"""Grade logged signals against actual results — the "does it have edge?" check.

Reads the observations SQLite written by `storage.py` and scores every flagged
bet two ways:

- **Result grading** (needs final scores): did the bet win/lose/push, and what was
  the realized profit / ROI at the stored odds and stake? Also reports calibration
  (predicted win prob vs realized win rate) and model EV vs realized ROI.
- **Closing-line value** (needs only the log): compares the line we flagged against
  the last line observed for that market (a proxy for the closing number). Beating
  the close is the most robust evidence of edge and needs no final score.

Finals can come from a `--results` YAML/JSON or a `results:` block in the game YAML:

    finals:
      game: { full: 224, h1: 110, q1: 55 }
      team: { OKC: 112, SAS: 112 }
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .probability import american_to_profit

_FETCH = """
SELECT ts, event_id, market_type, period, team, pregame_line, live_line,
       over_odds, under_odds, side, prob, ev, kelly_stake, flagged
FROM observations
{where}
ORDER BY ts ASC
"""


@dataclass
class GradedBet:
    market_type: str
    period: str
    team: Optional[str]
    side: str
    line: float
    odds: int
    stake: float
    pred_prob: float
    model_ev: float
    # filled by result grading
    actual: Optional[float] = None
    outcome: Optional[str] = None      # "win" | "loss" | "push" | "ungraded"
    profit: float = 0.0
    # closing-line value
    closing_line: Optional[float] = None
    clv_pts: Optional[float] = None


@dataclass
class Summary:
    bets: int = 0
    wins: int = 0
    losses: int = 0
    pushes: int = 0
    staked: float = 0.0
    profit: float = 0.0
    avg_model_ev: float = 0.0
    avg_pred_prob: float = 0.0
    clv_graded: int = 0
    clv_beat: int = 0
    avg_clv_pts: float = 0.0
    graded: list[GradedBet] = field(default_factory=list)

    @property
    def roi(self) -> float:
        return self.profit / self.staked if self.staked else 0.0

    @property
    def win_rate(self) -> float:
        decided = self.wins + self.losses
        return self.wins / decided if decided else 0.0

    @property
    def clv_beat_rate(self) -> float:
        return self.clv_beat / self.clv_graded if self.clv_graded else 0.0


def _market_key(market_type: str, period: str, team: Optional[str]) -> str:
    return f"{market_type}:{period}:{team or 'game'}"


def _actual_final(finals: dict, market_type: str, period: str, team: Optional[str]) -> Optional[float]:
    try:
        if market_type == "team_total":
            return float(finals["team"][team])
        return float(finals["game"][period])
    except (KeyError, TypeError, ValueError):
        return None


def closing_lines(db_path: str | Path, event_id: Optional[str] = None) -> dict[str, float]:
    """Last observed live line per market key (proxy for the closing number)."""
    where = "WHERE event_id = ?" if event_id else ""
    args = (event_id,) if event_id else ()
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(_FETCH.format(where=where), args).fetchall()
    conn.close()
    out: dict[str, float] = {}
    for r in rows:  # ascending ts -> last write wins
        out[_market_key(r["market_type"], r["period"], r["team"])] = r["live_line"]
    return out


def grade(
    db_path: str | Path,
    finals: Optional[dict] = None,
    event_id: Optional[str] = None,
    flagged_only: bool = True,
) -> Summary:
    where_clauses = []
    args: list = []
    if event_id:
        where_clauses.append("event_id = ?")
        args.append(event_id)
    if flagged_only:
        where_clauses.append("flagged = 1")
    where = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(_FETCH.format(where=where), tuple(args)).fetchall()
    conn.close()

    closes = closing_lines(db_path, event_id)
    summary = Summary()

    for r in rows:
        side = r["side"]
        odds = r["over_odds"] if side == "over" else r["under_odds"]
        bet = GradedBet(
            market_type=r["market_type"], period=r["period"], team=r["team"],
            side=side, line=r["live_line"], odds=odds, stake=r["kelly_stake"],
            pred_prob=r["prob"], model_ev=r["ev"],
        )

        # closing-line value (independent of finals)
        close = closes.get(_market_key(r["market_type"], r["period"], r["team"]))
        if close is not None:
            bet.closing_line = close
            bet.clv_pts = (close - bet.line) if side == "over" else (bet.line - close)
            summary.clv_graded += 1
            summary.avg_clv_pts += bet.clv_pts
            if bet.clv_pts > 0:
                summary.clv_beat += 1

        # result grading (needs finals)
        actual = _actual_final(finals or {}, r["market_type"], r["period"], r["team"])
        if actual is None:
            bet.outcome = "ungraded"
        else:
            bet.actual = actual
            if abs(actual - bet.line) < 1e-9:
                bet.outcome, bet.profit = "push", 0.0
                summary.pushes += 1
            else:
                won = actual > bet.line if side == "over" else actual < bet.line
                if won:
                    bet.outcome = "win"
                    bet.profit = bet.stake * american_to_profit(odds)
                    summary.wins += 1
                else:
                    bet.outcome = "loss"
                    bet.profit = -bet.stake
                    summary.losses += 1
            summary.staked += bet.stake
            summary.profit += bet.profit

        summary.bets += 1
        summary.avg_model_ev += bet.model_ev
        summary.avg_pred_prob += bet.pred_prob
        summary.graded.append(bet)

    if summary.bets:
        summary.avg_model_ev /= summary.bets
        summary.avg_pred_prob /= summary.bets
    if summary.clv_graded:
        summary.avg_clv_pts /= summary.clv_graded
    return summary


def load_finals(results_path: Optional[str], game_cfg=None) -> Optional[dict]:
    """Resolve finals from a results file, else a `finals:` block on the game cfg."""
    if results_path:
        import yaml

        data = yaml.safe_load(Path(results_path).read_text()) or {}
        return data.get("finals", data)
    if game_cfg is not None:
        finals = getattr(game_cfg, "finals", None)
        if finals:
            return finals
    return None
