"""Synthesize the live line a book would post, from a real score timeline.

The bettor's model (`reversion.py`) reverts remaining scoring toward the pregame
rate with weight `beta`. A book, by contrast, *chases recent pace*: we model its
live line with the same blend but a low reversion weight `book_beta` (0 = pure
pace-chasing, 1 = the line never moves off the pregame rate). The gap between the
two is exactly the edge the system claims to exploit.

This is the one modeled piece of the backtest; outcomes are graded against ESPN's
real finals. Because results are sensitive to `book_beta`, the sweep treats it as
an explicit axis rather than a fixed assumption.
"""

from __future__ import annotations

from typing import Optional

from .config import EventMeta, GameConfig, OverUnder
from .espn import GameHistory
from .models import GameState, MarketLine, MarketType, Period
from .odds.base import Snapshot

STD_ODDS = -110  # modeled books hold price at -110 and move the line


def game_config_from_history(hist: GameHistory, h1_share: float = 0.5) -> GameConfig:
    """Build an in-memory GameConfig (pregame baselines) from ESPN history."""
    teams = hist.pregame_team_totals()
    return GameConfig(
        event=EventMeta(
            id=hist.event_id, away=hist.away_name, home=hist.home_name,
            away_key=hist.away, home_key=hist.home,
        ),
        totals={
            "full": OverUnder(line=hist.pregame_total, over=STD_ODDS, under=STD_ODDS),
            "h1": OverUnder(line=round(hist.pregame_total * h1_share, 1),
                            over=STD_ODDS, under=STD_ODDS),
        },
        team_totals={
            hist.away: OverUnder(line=round(teams[hist.away], 1), over=STD_ODDS, under=STD_ODDS),
            hist.home: OverUnder(line=round(teams[hist.home], 1), over=STD_ODDS, under=STD_ODDS),
        },
        finals=hist.finals,
    )


def _book_line(pregame_total: float, length: float, points: float,
               elapsed: float, remaining: float, book_beta: float,
               min_elapsed: float) -> float:
    """The live total a pace-chasing book posts for this market."""
    pregame_rate = pregame_total / length
    pace = points / elapsed if elapsed >= min_elapsed and elapsed > 0 else pregame_rate
    blended = book_beta * pregame_rate + (1.0 - book_beta) * pace
    return round((points + remaining * blended) * 2) / 2.0  # snap to nearest 0.5


def synth_snapshots(
    hist: GameHistory,
    cfg: GameConfig,
    book_beta: float = 0.2,
    sample_minutes: float = 1.0,
    min_elapsed: float = 5.0,
    markets: Optional[list[str]] = None,
) -> list[Snapshot]:
    """One snapshot per sampled game-minute, each carrying modeled live lines."""
    markets = markets or ["total_full", "total_h1", "team_total"]
    want_full = "total_full" in markets
    want_h1 = "total_h1" in markets
    want_team = "team_total" in markets

    full_pre = cfg.totals["full"].line
    h1_pre = cfg.totals["h1"].line
    team_pre = {t: ou.line for t, ou in cfg.team_totals.items()}

    snaps: list[Snapshot] = []
    next_sample = sample_minutes
    for tp in hist.timeline:
        e = tp.minutes_elapsed
        if e <= 0 or (e < next_sample and e < 48.0):
            continue
        next_sample = e + sample_minutes
        lines: list[MarketLine] = []

        if want_full:
            lines.append(MarketLine(
                MarketType.GAME_TOTAL, Period.FULL,
                _book_line(full_pre, 48.0, tp.total, e, 48.0 - e, book_beta, min_elapsed),
                STD_ODDS, STD_ODDS, book="modeled"))
        if want_h1 and e < 24.0:
            lines.append(MarketLine(
                MarketType.GAME_TOTAL, Period.H1,
                _book_line(h1_pre, 24.0, tp.total, e, 24.0 - e, book_beta, min_elapsed),
                STD_ODDS, STD_ODDS, book="modeled"))
        if want_team:
            for team, pre in team_pre.items():
                pts = tp.home_score if team == hist.home else tp.away_score
                lines.append(MarketLine(
                    MarketType.TEAM_TOTAL, Period.FULL,
                    _book_line(pre, 48.0, pts, e, 48.0 - e, book_beta, min_elapsed),
                    STD_ODDS, STD_ODDS, team=team, book="modeled"))

        if lines:
            snaps.append(Snapshot(
                state=GameState(
                    period=Period.FULL, minutes_elapsed=e, minutes_remaining=48.0 - e,
                    home_score=tp.home_score, away_score=tp.away_score),
                lines=lines, meta={"source": "synthetic", "book_beta": book_beta}))
    return snaps
