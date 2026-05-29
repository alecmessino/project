"""Efficient threshold sweep: grade every evaluation once, then test many
threshold combinations as cheap filters over the pre-graded rows.

For one (model_beta, book_beta) pair we run the engine over each game's
synthesized snapshots a single time, attaching the *real* graded outcome to
every market evaluation. A threshold combination is then just: filter rows that
clear all gates, keep the first crossing per (game, market, side), and
aggregate. So an N-cell grid costs ~one engine pass, not N.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Iterable, Optional

from .config import GameConfig, Settings
from .engine import Engine
from .espn import GameHistory
from .linemodel import synth_snapshots
from .models import Period
from .probability import american_to_profit


@dataclass
class Record:
    """One graded market evaluation at one snapshot (outcome is real)."""
    game_id: str
    market: str            # e.g. "game_total:full:game"
    period_kind: str       # full | half | quarter
    side: str              # over | under
    minute: float          # full-game minute the eval was observed
    minutes_remaining: float
    pct_move: float        # signed (live-pre)/pre
    abs_move: float        # |pct_move|
    edge_pts: float        # signed in favor of side
    ev: float
    prob: float
    line: float
    odds: int
    # real outcome at this line:
    outcome: str           # win | loss | push
    profit_1u: float       # flat 1-unit profit


@dataclass
class Combo:
    pct_move: float
    edge_pts: float
    ev: float
    min_minutes_full: float

    def label(self) -> str:
        return (f"move≥{self.pct_move:.0%} edge≥{self.edge_pts:.1f} "
                f"ev≥{self.ev:+.0%} min≥{self.min_minutes_full:.0f}m")


@dataclass
class SweepRow:
    combo: Combo
    bets: int = 0
    wins: int = 0
    losses: int = 0
    pushes: int = 0
    profit: float = 0.0
    avg_ev: float = 0.0
    avg_prob: float = 0.0
    win_rate: float = 0.0
    roi: float = 0.0
    by_period: dict = field(default_factory=dict)   # kind -> (bets, profit)
    by_side: dict = field(default_factory=dict)


_MIN_MIN = {"full": "min_minutes_full", "half": None, "quarter": None}


def _period_kind(period: str) -> str:
    if period == "full":
        return "full"
    if period == "h1":
        return "half"
    return "quarter"


def build_records(
    games: list[tuple[GameHistory, GameConfig]],
    settings: Settings,
    book_beta: float,
    sample_minutes: float = 1.0,
    markets: Optional[list[str]] = None,
) -> list[Record]:
    """Run the engine once per game and grade every evaluation against finals."""
    recs: list[Record] = []
    for hist, cfg in games:
        finals = hist.finals
        engine = Engine(settings, cfg, provider=None)
        for snap in synth_snapshots(hist, cfg, book_beta=book_beta,
                                    sample_minutes=sample_minutes, markets=markets):
            for r in engine.process_snapshot(snap):
                e = r.evaluation
                b = e.baseline
                actual = _actual_final(finals, b.market_type.value, b.period.value, b.team)
                if actual is None:
                    continue
                outcome, profit = _grade(e.side.value, e.live.line, actual, e.offered_odds)
                recs.append(Record(
                    game_id=hist.event_id,
                    market=b.key(),
                    period_kind=_period_kind(b.period.value),
                    side=e.side.value,
                    minute=round(e.state.minutes_elapsed, 1),
                    minutes_remaining=e.state.minutes_remaining,
                    pct_move=e.pct_move, abs_move=abs(e.pct_move),
                    edge_pts=e.edge_pts, ev=e.ev, prob=e.prob,
                    line=e.live.line, odds=e.offered_odds,
                    outcome=outcome, profit_1u=profit,
                ))
    return recs


def _actual_final(finals, market_type, period, team):
    try:
        if market_type == "team_total":
            return float(finals["team"][team])
        return float(finals["game"][period])
    except (KeyError, TypeError, ValueError):
        return None


def _grade(side: str, line: float, actual: float, odds: int) -> tuple[str, float]:
    if abs(actual - line) < 1e-9:
        return "push", 0.0
    won = actual > line if side == "over" else actual < line
    return ("win", american_to_profit(odds)) if won else ("loss", -1.0)


def _passes(rec: Record, c: Combo) -> bool:
    if rec.abs_move < c.pct_move:
        return False
    if rec.edge_pts < c.edge_pts:
        return False
    if rec.ev < c.ev:
        return False
    # min-minutes gate keyed by period kind (full uses the swept value;
    # half/quarter scale down proportionally, mirroring the live config ratio).
    floor = c.min_minutes_full
    if rec.period_kind == "half":
        floor = c.min_minutes_full * (4.0 / 6.0)
    elif rec.period_kind == "quarter":
        floor = c.min_minutes_full * (3.0 / 6.0)
    return rec.minutes_remaining >= floor


def evaluate_combo(records: list[Record], c: Combo) -> SweepRow:
    """First-crossing bet per (game, market, side); aggregate the real outcomes."""
    row = SweepRow(combo=c)
    seen: set = set()
    for rec in records:               # records are in time order within each game
        if not _passes(rec, c):
            continue
        key = (rec.game_id, rec.market, rec.side)
        if key in seen:
            continue
        seen.add(key)
        row.bets += 1
        row.profit += rec.profit_1u
        row.avg_ev += rec.ev
        row.avg_prob += rec.prob
        if rec.outcome == "win":
            row.wins += 1
        elif rec.outcome == "loss":
            row.losses += 1
        else:
            row.pushes += 1
        bp = row.by_period.setdefault(rec.period_kind, [0, 0.0])
        bp[0] += 1; bp[1] += rec.profit_1u
        bs = row.by_side.setdefault(rec.side, [0, 0.0])
        bs[0] += 1; bs[1] += rec.profit_1u
    if row.bets:
        row.avg_ev /= row.bets
        row.avg_prob /= row.bets
        decided = row.wins + row.losses
        row.win_rate = row.wins / decided if decided else 0.0
        row.roi = row.profit / row.bets
    return row


def default_grid() -> list[Combo]:
    moves = [0.06, 0.08, 0.10, 0.12, 0.15]
    edges = [2.0, 3.0, 4.0, 5.0]
    evs = [0.0, 0.02, 0.05]
    mins = [4.0, 6.0, 8.0]
    return [Combo(m, e, v, t) for m, e, v, t in itertools.product(moves, edges, evs, mins)]


def sweep(records: list[Record], grid: Optional[Iterable[Combo]] = None,
          min_bets: int = 1) -> list[SweepRow]:
    """Evaluate every combo; return rows sorted by ROI then sample size."""
    grid = list(grid or default_grid())
    rows = [evaluate_combo(records, c) for c in grid]
    rows = [r for r in rows if r.bets >= min_bets]
    rows.sort(key=lambda r: (r.roi, r.bets), reverse=True)
    return rows
