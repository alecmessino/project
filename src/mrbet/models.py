"""Core data structures shared across the engine.

These are plain dataclasses (no validation) used at runtime. Config loading and
validation lives in `config.py` (pydantic). Keeping runtime objects as light
dataclasses keeps the hot path cheap and the math modules dependency-free.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Period(str, Enum):
    """Which slice of the game a market settles on."""

    FULL = "full"
    H1 = "h1"
    Q1 = "q1"
    Q2 = "q2"
    Q3 = "q3"
    Q4 = "q4"

    @property
    def length_minutes(self) -> float:
        """Regulation length of this period in minutes."""
        return {
            Period.FULL: 48.0,
            Period.H1: 24.0,
            Period.Q1: 12.0,
            Period.Q2: 12.0,
            Period.Q3: 12.0,
            Period.Q4: 12.0,
        }[self]

    @property
    def kind(self) -> str:
        """Coarse category used to pick min-minutes-remaining thresholds."""
        if self is Period.FULL:
            return "full"
        if self is Period.H1:
            return "half"
        return "quarter"


class Side(str, Enum):
    """Which side of a total a signal recommends."""

    OVER = "over"
    UNDER = "under"


class MarketType(str, Enum):
    GAME_TOTAL = "game_total"
    TEAM_TOTAL = "team_total"


@dataclass
class GameState:
    """A snapshot of live game progress.

    `points` is the total points scored within the relevant period so far. For a
    team-total market it is that team's points; for a game total it is both teams
    combined. `minutes_elapsed` / `minutes_remaining` are within the period.
    """

    period: Period
    minutes_elapsed: float
    minutes_remaining: float
    home_score: int
    away_score: int

    @property
    def total_score(self) -> int:
        return self.home_score + self.away_score


@dataclass
class MarketLine:
    """A live (or pregame) line for one over/under market."""

    market_type: MarketType
    period: Period
    line: float
    over_odds: int      # American odds
    under_odds: int     # American odds
    # For team totals only: which team ("OKC"/"SAS"); None for game totals.
    team: Optional[str] = None
    # Which sportsbook this quote came from (e.g. "bovada", or the consensus pick).
    book: Optional[str] = None


@dataclass
class Baseline:
    """The pregame anchor a live line is compared against."""

    market_type: MarketType
    period: Period
    line: float
    over_odds: int
    under_odds: int
    team: Optional[str] = None

    def key(self) -> str:
        t = self.team or "game"
        return f"{self.market_type.value}:{self.period.value}:{t}"


@dataclass
class Evaluation:
    """The full model output for one (baseline, live line, game state) triple."""

    baseline: Baseline
    live: MarketLine
    state: GameState
    side: Side                 # the side mean reversion favors
    fair_final: float          # projected final total for the period
    pct_move: float            # signed: (live - pregame)/pregame
    edge_pts: float            # signed in favor of `side`
    prob: float                # model probability the chosen side wins
    implied_prob: float        # book's vig-included implied prob for that side
    ev: float                  # expected value per $1 staked
    kelly_stake: float         # recommended stake in $ (fractional, capped)

    @property
    def offered_odds(self) -> int:
        return self.live.over_odds if self.side is Side.OVER else self.live.under_odds


@dataclass
class Signal:
    """An Evaluation that crossed all trigger thresholds — i.e. worth alerting."""

    evaluation: Evaluation
    strong: bool
    reasons: list[str] = field(default_factory=list)

    @property
    def dedupe_key(self) -> str:
        e = self.evaluation
        return f"{e.baseline.key()}:{e.side.value}"
