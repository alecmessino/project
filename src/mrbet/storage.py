"""Persist every evaluation + signal to SQLite for later backtesting / tuning.

Logging *all* evaluations (not just flagged ones) is deliberate: it's the raw
material for checking whether the reversion rule actually beats the closing line.
"""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Optional

from .models import Evaluation, Signal

_SCHEMA = """
CREATE TABLE IF NOT EXISTS observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    event_id TEXT,
    market_type TEXT,
    period TEXT,
    team TEXT,
    pregame_line REAL,
    live_line REAL,
    over_odds INTEGER,
    under_odds INTEGER,
    side TEXT,
    fair_final REAL,
    pct_move REAL,
    edge_pts REAL,
    prob REAL,
    implied_prob REAL,
    ev REAL,
    kelly_stake REAL,
    minutes_remaining REAL,
    home_score INTEGER,
    away_score INTEGER,
    flagged INTEGER DEFAULT 0,
    strong INTEGER DEFAULT 0
);
"""


class Storage:
    def __init__(self, path: str | Path = "data/runtime/mrbet.sqlite", event_id: str = ""):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.event_id = event_id
        self.conn = sqlite3.connect(str(self.path))
        self.conn.execute(_SCHEMA)
        self.conn.commit()

    def log(self, ev: Evaluation, signal: Optional[Signal] = None) -> None:
        b = ev.baseline
        self.conn.execute(
            """INSERT INTO observations
               (ts, event_id, market_type, period, team, pregame_line, live_line,
                over_odds, under_odds, side, fair_final, pct_move, edge_pts, prob,
                implied_prob, ev, kelly_stake, minutes_remaining, home_score,
                away_score, flagged, strong)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                time.time(), self.event_id, b.market_type.value, b.period.value,
                b.team, b.line, ev.live.line, ev.live.over_odds, ev.live.under_odds,
                ev.side.value, ev.fair_final, ev.pct_move, ev.edge_pts, ev.prob,
                ev.implied_prob, ev.ev, ev.kelly_stake, ev.state.minutes_remaining,
                ev.state.home_score, ev.state.away_score,
                1 if signal else 0, 1 if (signal and signal.strong) else 0,
            ),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
