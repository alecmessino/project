"""Orchestration: stream snapshots -> evaluate every market -> flag -> notify/log."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .config import GameConfig, Settings
from .models import Evaluation, GameState, MarketLine, MarketType, Period, Signal
from .notify import Notifier
from .odds.base import OddsProvider, Snapshot
from .storage import Storage
from .triggers import evaluate_market, to_signal


@dataclass
class Result:
    evaluation: Evaluation
    signal: Optional[Signal]


def derive_state(snap_state: GameState, target: Period) -> Optional[GameState]:
    """Build the GameState relevant to `target` from a snapshot's state.

    Replay/manual snapshots already carry the target period and are returned
    as-is. For a live full-game snapshot we derive the in-period clock; periods
    that have already closed (or whose per-period scoring can't be inferred from
    a cumulative score) return None and are skipped.
    """
    if snap_state.period == target:
        return snap_state
    if snap_state.period != Period.FULL:
        return None

    elapsed_full = snap_state.minutes_elapsed
    if target in (Period.FULL,):
        return snap_state
    # Half length = regulation/2, derived from the live clock so it is league-correct
    # (NBA 24, WNBA 20) rather than a hardcoded NBA half.
    regulation = snap_state.minutes_elapsed + snap_state.minutes_remaining
    half_len = (regulation / 2.0) if regulation > 0 else 24.0
    if target == Period.H1:
        if elapsed_full >= half_len:
            return None  # first half already over
        return GameState(
            period=Period.H1,
            minutes_elapsed=elapsed_full,
            minutes_remaining=half_len - elapsed_full,
            home_score=snap_state.home_score,
            away_score=snap_state.away_score,
        )
    if target == Period.H2:
        # 2nd half: need the settled H1-final to split the cumulative score.
        if elapsed_full < half_len:
            return None  # 2nd half hasn't started
        if snap_state.h1_home is None or snap_state.h1_away is None:
            return None  # H1-final not known yet — can't derive H2 scoring
        h2_elapsed = elapsed_full - half_len
        return GameState(
            period=Period.H2,
            minutes_elapsed=h2_elapsed,
            minutes_remaining=max(0.0, half_len - h2_elapsed),
            home_score=snap_state.home_score - snap_state.h1_home,
            away_score=snap_state.away_score - snap_state.h1_away,
        )
    # Quarter markets need per-quarter scoring, which a cumulative score can't
    # provide; only the replay/manual path (period match above) handles them.
    return None


def market_key(line: MarketLine) -> str:
    """Settings-vocabulary key for a market line: 'team_total' or 'total_<period>'
    (e.g. total_full, total_h1, total_q1) — used to filter tracked markets per league."""
    if line.market_type == MarketType.TEAM_TOTAL:
        return "team_total"
    return f"total_{line.period.value}"


def points_for(state: GameState, line: MarketLine, cfg: GameConfig) -> float:
    """Points scored so far relevant to this market within its period."""
    if line.market_type == MarketType.TEAM_TOTAL:
        if line.team == cfg.event.home_key:
            return float(state.home_score)
        if line.team == cfg.event.away_key:
            return float(state.away_score)
        return 0.0
    return float(state.total_score)


class Engine:
    def __init__(
        self,
        settings: Settings,
        game: GameConfig,
        provider: OddsProvider,
        notifier: Optional[Notifier] = None,
        storage: Optional[Storage] = None,
    ):
        self.settings = settings
        self.game = game
        self.provider = provider
        self.notifier = notifier
        self.storage = storage
        self._baseline_index = {b.key(): b for b in game.baselines()}

    def process_snapshot(self, snap: Snapshot) -> list[Result]:
        results: list[Result] = []
        league = getattr(self.game.event, "league", None)
        allowed = set(self.settings.engine.markets_for(league))
        for line in snap.lines:
            if market_key(line) not in allowed:
                continue   # market not tracked for this league (e.g. WNBA team totals)
            baseline = self._baseline_for(line)
            if baseline is None:
                continue
            state = derive_state(snap.state, line.period)
            if state is None:
                continue
            pts = points_for(state, line, self.game)
            ev = evaluate_market(baseline, line, state, pts, self.settings,
                                 league=getattr(self.game.event, "league", None))
            sig = to_signal(ev, self.settings)
            results.append(Result(evaluation=ev, signal=sig))
        return results

    def run(self, on_result=None) -> None:
        """Consume the provider stream end to end."""
        for snap in self.provider.snapshots():
            credits = snap.meta.get("credits_remaining")
            if credits is not None and credits < self.settings.engine.min_api_credits:
                print(f"[warn] API credits low: {credits}")
            for res in self.process_snapshot(snap):
                if self.storage:
                    self.storage.log(res.evaluation, res.signal)
                if res.signal and self.notifier:
                    self.notifier.maybe_notify(res.signal)
                if on_result:
                    on_result(res)

    def _baseline_for(self, line: MarketLine):
        team = line.team
        key = f"{line.market_type.value}:{line.period.value}:{team or 'game'}"
        return self._baseline_index.get(key)
