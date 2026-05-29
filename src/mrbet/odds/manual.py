"""Manual / replay provider.

Two modes:
- replay: read a JSON file of pre-recorded snapshots (used by `simulate`, tests,
  and demos). Yields them in order, then stops.
- interactive: prompt the operator for the current clock/score and the live lines
  seen on the sportsbook screen. Useful tonight if the API's in-play coverage lags.

JSON schema (replay):
{
  "event_id": "okc_sas_2026-05-28",
  "snapshots": [
    {
      "period": "full", "minutes_elapsed": 6.0, "minutes_remaining": 42.0,
      "home_score": 8, "away_score": 6,
      "lines": [
        {"market_type": "game_total", "period": "full", "line": 210.5,
         "over_odds": -110, "under_odds": -110},
        {"market_type": "team_total", "period": "full", "team": "OKC",
         "line": 102.5, "over_odds": -110, "under_odds": -115}
      ]
    }
  ]
}
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator, Optional

from ..models import GameState, MarketLine, MarketType, Period
from .base import Snapshot


def _parse_state(d: dict) -> GameState:
    return GameState(
        period=Period(d["period"]),
        minutes_elapsed=float(d["minutes_elapsed"]),
        minutes_remaining=float(d["minutes_remaining"]),
        home_score=int(d["home_score"]),
        away_score=int(d["away_score"]),
    )


def _parse_line(d: dict) -> MarketLine:
    return MarketLine(
        market_type=MarketType(d["market_type"]),
        period=Period(d.get("period", "full")),
        line=float(d["line"]),
        over_odds=int(d["over_odds"]),
        under_odds=int(d["under_odds"]),
        team=d.get("team"),
    )


def load_replay(path: str | Path) -> list[Snapshot]:
    data = json.loads(Path(path).read_text())
    snaps: list[Snapshot] = []
    for s in data.get("snapshots", []):
        state = _parse_state(s)
        lines = [_parse_line(x) for x in s.get("lines", [])]
        snaps.append(Snapshot(state=state, lines=lines, meta={"source": "replay"}))
    return snaps


class ManualProvider:
    """Provider backed by a replay file or interactive prompts."""

    def __init__(self, replay: Optional[str] = None, **_ignored):
        self.replay = replay

    def snapshots(self) -> Iterator[Snapshot]:
        if self.replay:
            yield from load_replay(self.replay)
        else:
            yield from self._interactive()

    def credits_remaining(self) -> Optional[int]:
        return None

    def _interactive(self) -> Iterator[Snapshot]:  # pragma: no cover - I/O loop
        print("Interactive manual entry. Ctrl-C to stop.\n")
        while True:
            try:
                period = Period(input("period [full/h1/q1..q4]: ").strip() or "full")
                elapsed = float(input("minutes elapsed in period: ").strip())
                remaining = period.length_minutes - elapsed
                away = int(input("away score: ").strip())
                home = int(input("home score: ").strip())
                state = GameState(period, elapsed, remaining, home, away)

                lines: list[MarketLine] = []
                print("Enter live lines (blank line to finish). "
                      "Format: <game|team:KEY> <line> <over_odds> <under_odds>")
                while True:
                    raw = input("  line> ").strip()
                    if not raw:
                        break
                    lines.append(_parse_interactive_line(raw, period))
                yield Snapshot(state=state, lines=lines, meta={"source": "manual"})
            except (KeyboardInterrupt, EOFError):
                print("\nstopping interactive entry.")
                return


def _parse_interactive_line(raw: str, period: Period) -> MarketLine:  # pragma: no cover
    parts = raw.split()
    tgt, line, over, under = parts[0], float(parts[1]), int(parts[2]), int(parts[3])
    if tgt.startswith("team:"):
        return MarketLine(MarketType.TEAM_TOTAL, period, line, over, under, team=tgt.split(":", 1)[1])
    return MarketLine(MarketType.GAME_TOTAL, period, line, over, under)
