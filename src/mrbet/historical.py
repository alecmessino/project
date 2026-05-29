"""Offline historical-odds source: run the engine against a JSON odds dump.

Plugs into the same pipeline as the live poller. The JSON file supplies
real or mock live lines at each cadence mark; ESPN scores + finals come
from the same file. Swap the source out for TheOddsApiHistoricalSource
(paid) without touching anything else.

JSON format
-----------
Single-game file::

    {
      "event_id": "sas_okc_2026-05-30",
      "marks": [
        { "minutes_elapsed": 6.0,
          "away_score": 9, "home_score": 10,
          "lines": {
            "game_total":     {"line": 168.0, "over": -115, "under": -105},
            "total_h1":       {"line":  83.0, "over": -115, "under": -105},
            "team_total_SAS": {"line":  80.5, "over": -110, "under": -110},
            "team_total_OKC": {"line":  87.5, "over": -110, "under": -110}
          }
        }, ...
      ],
      "finals": {
        "game": {"full": 209, "h1": 104, "q1": 42, "q2": 62, "q3": 61, "q4": 44},
        "team": {"SAS": 97, "OKC": 112}
      }
    }

Multi-game file: wrap in ``{"games": [ <game>, ... ]}``.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

from .cadence import timeout_marks
from .config import EventMeta, GameConfig, OverUnder, Settings
from .models import GameState, MarketLine, MarketType, Period
from .odds.base import Snapshot
from . import forward as fwd

# JSON line key -> (MarketType, Period, team=None)
_MARKET_MAP = {
    "game_total": (MarketType.GAME_TOTAL, Period.FULL, None),
    "total_h1":   (MarketType.GAME_TOTAL, Period.H1,   None),
    "total_q1":   (MarketType.GAME_TOTAL, Period.Q1,   None),
    "total_q2":   (MarketType.GAME_TOTAL, Period.Q2,   None),
    "total_q3":   (MarketType.GAME_TOTAL, Period.Q3,   None),
    "total_q4":   (MarketType.GAME_TOTAL, Period.Q4,   None),
}


def _parse_lines(lines_dict: dict) -> list[MarketLine]:
    out: list[MarketLine] = []
    for key, odds in lines_dict.items():
        if key in _MARKET_MAP:
            mtype, period, team = _MARKET_MAP[key]
            out.append(MarketLine(mtype, period, float(odds["line"]),
                                  int(odds["over"]), int(odds["under"])))
        elif key.startswith("team_total_"):
            team = key[len("team_total_"):]
            out.append(MarketLine(MarketType.TEAM_TOTAL, Period.FULL,
                                  float(odds["line"]), int(odds["over"]),
                                  int(odds["under"]), team=team))
    return out


def _game_config_from_dict(g: dict) -> GameConfig:
    """Build a GameConfig from a self-contained game dict (inline 'pregame' block).

    Required pregame keys: away_key, home_key, total.
    Optional: away_name, home_name, h1, team_total_<AWAY>, team_total_<HOME>.
    All odds default to -110/-110 (line-only datasets).
    """
    p        = g.get("pregame", {})
    away_key = p.get("away_key", "AWAY")
    home_key = p.get("home_key", "HOME")
    totals: dict = {}
    if "total" in p:
        totals["full"] = OverUnder(line=float(p["total"]), over=-110, under=-110)
    if "h1" in p:
        totals["h1"]   = OverUnder(line=float(p["h1"]),    over=-110, under=-110)
    team_totals: dict = {}
    for key in (away_key, home_key):
        val = p.get(f"team_total_{key}")
        if val is not None:
            team_totals[key] = OverUnder(line=float(val), over=-110, under=-110)
    return GameConfig(
        event=EventMeta(
            id=g["event_id"],
            away=p.get("away_name", away_key),
            home=p.get("home_name", home_key),
            away_key=away_key,
            home_key=home_key,
        ),
        totals=totals,
        team_totals=team_totals,
        finals=g.get("finals", {}),
    )


class JsonFileSource:
    """Historical odds from a structured JSON dump (real or mock).

    Marks are looked up by exact `minutes_elapsed` (±0.5 min tolerance).
    """

    def __init__(self, path: str | Path):
        data = json.loads(Path(path).read_text())
        self._games: dict[str, dict] = {}
        if "event_id" in data:
            self._games[data["event_id"]] = data
        for g in data.get("games", []):
            self._games[g["event_id"]] = g

    def game_ids(self) -> list[str]:
        return list(self._games.keys())

    def game_dicts(self) -> list[dict]:
        return list(self._games.values())

    def finals(self, event_id: str) -> Optional[dict]:
        return self._games.get(event_id, {}).get("finals") or None

    def lines_at(self, event_id: str, minutes_elapsed: float) -> list[MarketLine]:
        marks = self._games.get(event_id, {}).get("marks", [])
        m = next((m for m in marks
                  if abs(m["minutes_elapsed"] - minutes_elapsed) < 0.5), None)
        return _parse_lines(m["lines"]) if m else []

    def score_at(self, event_id: str, minutes_elapsed: float) -> Optional[tuple[int, int]]:
        """Return (away_score, home_score) from the mark closest to minutes_elapsed."""
        marks = [m for m in self._games.get(event_id, {}).get("marks", [])
                 if m["minutes_elapsed"] <= minutes_elapsed + 0.5]
        if not marks:
            return None
        m = min(marks, key=lambda x: abs(x["minutes_elapsed"] - minutes_elapsed))
        return m.get("away_score", 0), m.get("home_score", 0)


def run_cadence_backtest(
    source: JsonFileSource,
    game: GameConfig,
    settings: Settings,
) -> dict:
    """Run the 9-point cadence against *source* for *game*. Returns a graded ledger."""
    from .engine import Engine

    event_id = game.event.id
    finals = source.finals(event_id)
    matchup = f"{game.event.away_key} @ {game.event.home_key}"
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    ledger: dict = {}

    for mark in timeout_marks():
        scores = source.score_at(event_id, mark)
        if scores is None:
            continue
        away_score, home_score = scores
        state = GameState(
            period=Period.FULL,
            minutes_elapsed=mark,
            minutes_remaining=48.0 - mark,
            away_score=away_score,
            home_score=home_score,
        )
        lines = source.lines_at(event_id, mark)
        if not lines:
            continue
        snap = Snapshot(state=state, lines=lines,
                        meta={"source": "json_file", "mark": mark})
        for result in Engine(settings, game, provider=None).process_snapshot(snap):
            if result.signal:
                fwd.merge_signal(ledger, result.evaluation, ts, matchup, finals)

    return ledger
