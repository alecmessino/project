"""Core mean-reversion engine for live MLB totals.

Replaces the NBA project's continuous 48-minute clock with a discrete,
state-based baseball framework:

  state = (inning, half, outs, away_runs, home_runs)

Cadence marks fire at the conclusion of each half-inning — 18 marks for a
9-inning regulation game. Everything is anchored to the pregame Vegas run
line (e.g. 8.5), not basketball point totals; all text references are in
"runs", never "points".

This single module deliberately contains the dataclasses, math, and trigger
logic so the scaffold has one importable surface — matches the file layout
requested in the spec.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import erf, sqrt
from pathlib import Path
from typing import Optional

# A standard 9-inning game has 18 half-innings; the F5 segment has 10.
HALF_INNINGS_PER_GAME = 18
HALF_INNINGS_PER_F5 = 10
OUTS_PER_HALF_INNING = 3


# --------------------------------------------------------------------------- #
# Enums + dataclasses (the runtime objects)                                   #
# --------------------------------------------------------------------------- #
class Half(str, Enum):
    TOP = "top"
    BOTTOM = "bottom"


class Period(str, Enum):
    FULL = "full"
    F5 = "f5"


class MarketType(str, Enum):
    GAME_TOTAL = "game_total"   # full game OR F5 — period field distinguishes
    TEAM_TOTAL = "team_total"   # always full game


class Side(str, Enum):
    OVER = "over"
    UNDER = "under"


@dataclass
class GameState:
    """A snapshot of live game progress.

    `outs` counts the OPEN outs in the current half-inning (0, 1, or 2). A
    half-inning ends at the 3rd out and the next state advances `half` or
    `inning` — we never carry outs=3.
    """

    inning: int
    half: Half
    outs: int
    away_runs: int
    home_runs: int

    def half_innings_elapsed(self) -> float:
        """Completed half-innings + a fractional credit for outs in the current."""
        full = (self.inning - 1) * 2 + (0 if self.half is Half.TOP else 1)
        return full + self.outs / OUTS_PER_HALF_INNING

    def half_innings_remaining(self, period: Period = Period.FULL) -> float:
        target = HALF_INNINGS_PER_GAME if period is Period.FULL else HALF_INNINGS_PER_F5
        return max(0.0, target - self.half_innings_elapsed())

    def total_runs(self) -> int:
        return self.away_runs + self.home_runs

    def team_runs(self, team_role: str) -> int:
        """`team_role` is 'away' or 'home'."""
        return self.away_runs if team_role == "away" else self.home_runs


@dataclass
class MarketLine:
    """A live over/under quote for one market."""

    market_type: MarketType
    period: Period
    line: float
    over_odds: int
    under_odds: int
    team: Optional[str] = None   # e.g. "LAD" / "NYY" for team totals
    book: Optional[str] = None


@dataclass
class Baseline:
    """The pregame anchor — what live moves are measured against."""

    market_type: MarketType
    period: Period
    line: float
    over_odds: int
    under_odds: int
    team: Optional[str] = None

    def key(self) -> str:
        return f"{self.market_type.value}:{self.period.value}:{self.team or 'game'}"


@dataclass
class ModelParams:
    beta: float = 0.75
    sigma_full: float = 2.6
    sigma_f5: float = 1.7
    sigma_team: float = 1.8
    min_half_innings_elapsed: int = 2


@dataclass
class TriggerParams:
    pct_move_threshold: float = 0.12
    edge_runs_threshold: float = 2.5
    ev_threshold: float = 0.0
    ev_strong_threshold: float = 0.03
    min_half_innings_remaining: dict = field(
        default_factory=lambda: {"full": 4, "f5": 2})


@dataclass
class Evaluation:
    baseline: Baseline
    live: MarketLine
    state: GameState
    side: Side
    fair_final: float
    pct_move: float         # signed: (live - pregame) / pregame
    edge_runs: float        # signed in favor of `side` (always non-negative if the side is correct)
    prob: float             # model probability the chosen side wins
    implied_prob: float
    ev: float

    @property
    def offered_odds(self) -> int:
        return self.live.over_odds if self.side is Side.OVER else self.live.under_odds


@dataclass
class Signal:
    evaluation: Evaluation
    strong: bool
    reasons: list[str]


# --------------------------------------------------------------------------- #
# Pure math (no I/O — fully unit-testable)                                    #
# --------------------------------------------------------------------------- #
def _normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + erf(x / sqrt(2.0)))


def american_to_implied(odds: int) -> float:
    return (-odds) / ((-odds) + 100) if odds < 0 else 100 / (odds + 100)


def american_to_profit(odds: int) -> float:
    """Profit per $1 risked at the offered American odds."""
    return 100 / (-odds) if odds < 0 else odds / 100


def projected_final(
    pregame_total: float,
    runs_so_far: float,
    state: GameState,
    *,
    period: Period,
    model: ModelParams,
) -> float:
    """Mean-reversion projection of the final total for `period`.

    Blends the pregame per-half-inning rate with the observed live rate, weighted
    by β. Until `min_half_innings_elapsed` is reached, only pregame is trusted
    (avoids a single big frame whipsawing the line).
    """
    period_half_innings = (
        HALF_INNINGS_PER_GAME if period is Period.FULL else HALF_INNINGS_PER_F5
    )
    elapsed = min(state.half_innings_elapsed(), period_half_innings)
    remaining = max(0.0, period_half_innings - elapsed)
    if remaining == 0.0:
        return runs_so_far

    pregame_rate = pregame_total / period_half_innings
    if elapsed < model.min_half_innings_elapsed:
        pace_rate = pregame_rate
    else:
        pace_rate = runs_so_far / elapsed
    blended_rate = model.beta * pregame_rate + (1.0 - model.beta) * pace_rate
    return runs_so_far + blended_rate * remaining


def sigma_for(
    period: Period,
    market_type: MarketType,
    state: GameState,
    model: ModelParams,
) -> float:
    """Standard deviation of the FINAL run total, shrunk by share of game left."""
    if market_type is MarketType.TEAM_TOTAL:
        base, total = model.sigma_team, HALF_INNINGS_PER_GAME
    elif period is Period.F5:
        base, total = model.sigma_f5, HALF_INNINGS_PER_F5
    else:
        base, total = model.sigma_full, HALF_INNINGS_PER_GAME
    remaining = max(0.0, total - state.half_innings_elapsed())
    return base * sqrt(remaining / total) if total > 0 else 0.0


def prob_over(line: float, fair_final: float, sigma: float) -> float:
    if sigma <= 0:
        return 1.0 if fair_final > line else 0.0
    return 1.0 - _normal_cdf((line - fair_final) / sigma)


def expected_value(prob: float, odds: int) -> float:
    """EV per $1 risked (no-push approximation)."""
    return prob * american_to_profit(odds) - (1.0 - prob) * 1.0


# --------------------------------------------------------------------------- #
# Public API: evaluate -> Evaluation -> Signal                                #
# --------------------------------------------------------------------------- #
def evaluate_market(
    baseline: Baseline,
    live: MarketLine,
    state: GameState,
    runs_so_far: float,
    model: ModelParams,
) -> Evaluation:
    """Run the mean-reversion model for ONE market and price both sides."""
    fair = projected_final(
        baseline.line, runs_so_far, state, period=baseline.period, model=model)
    sigma = sigma_for(baseline.period, baseline.market_type, state, model)

    side = Side.OVER if fair >= live.line else Side.UNDER
    if side is Side.OVER:
        prob, odds, edge = prob_over(live.line, fair, sigma), live.over_odds, fair - live.line
    else:
        prob, odds, edge = (1.0 - prob_over(live.line, fair, sigma),
                            live.under_odds, live.line - fair)

    pct_move = (live.line - baseline.line) / baseline.line if baseline.line else 0.0
    return Evaluation(
        baseline=baseline, live=live, state=state, side=side, fair_final=fair,
        pct_move=pct_move, edge_runs=edge, prob=prob,
        implied_prob=american_to_implied(odds), ev=expected_value(prob, odds),
    )


def to_signal(ev: Evaluation, t: TriggerParams) -> Optional[Signal]:
    """Return a Signal if the Evaluation clears EVERY threshold, else None.

    The guard is deliberately conjunctive (same as the NBA engine): a big line
    move alone never fires. The model must agree (`edge_runs`), the wager must
    carry positive EV at the offered odds, and there must be enough game left
    for reversion to play out.
    """
    reasons: list[str] = []

    # 1. Line moved meaningfully, in the direction our side wants.
    move_helps = ev.pct_move <= 0 if ev.side is Side.OVER else ev.pct_move >= 0
    if not (move_helps and abs(ev.pct_move) >= t.pct_move_threshold):
        return None
    reasons.append(f"line moved {ev.pct_move*100:+.1f}% vs pregame")

    # 2. Model independently sees enough RUNS of edge.
    if ev.edge_runs < t.edge_runs_threshold:
        return None
    reasons.append(f"model edge {ev.edge_runs:+.2f} runs")

    # 3. Positive EV at the offered odds.
    if ev.ev < t.ev_threshold:
        return None
    reasons.append(f"EV {ev.ev*100:+.1f}% @ {ev.offered_odds:+d}")

    # 4. Enough half-innings remaining for reversion.
    period_key = ev.baseline.period.value
    min_remaining = (t.min_half_innings_remaining or {}).get(period_key, 0)
    period_total = (
        HALF_INNINGS_PER_GAME if ev.baseline.period is Period.FULL
        else HALF_INNINGS_PER_F5
    )
    remaining = max(0.0, period_total - ev.state.half_innings_elapsed())
    if remaining < min_remaining:
        return None
    reasons.append(f"{remaining:.0f} half-innings left")

    return Signal(evaluation=ev, strong=ev.ev >= t.ev_strong_threshold, reasons=reasons)


# --------------------------------------------------------------------------- #
# Tiny YAML loader so callers don't need pydantic for the scaffold            #
# --------------------------------------------------------------------------- #
def load_settings(path: str | Path = "settings.yaml") -> tuple[ModelParams, TriggerParams]:
    """Read settings.yaml -> (ModelParams, TriggerParams). PyYAML required."""
    import yaml  # local import keeps the module importable without the dep
    data = yaml.safe_load(Path(path).read_text()) or {}
    model = ModelParams(**(data.get("model") or {}))
    triggers = TriggerParams(**(data.get("triggers") or {}))
    return model, triggers
