"""Append-only JSONL ledger of every fired signal (Revision 3).

Records ALL trigger types — CONFIRM, ARM, and the console-only WATCH — with a
``trigger_type`` tag so post-season hit-rate analysis needs no manual tracking.
Used by both ``live_engine`` (real time) and ``simulate_execution`` (historical),
so the row schema is identical (the sim adds outcome fields via ``extra``).

Reads the trigger via duck typing to avoid importing ``live_engine``.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from shared_piping.notify import pull_risk_label


def build_row(trigger, *, bullpen_elite_ra9: float, ts: Optional[str] = None,
              extra: Optional[dict] = None) -> dict:
    """Flat, analysis-friendly dict for one fired signal."""
    s = trigger.state
    row = {
        "ts": ts or datetime.now(timezone.utc).isoformat(),
        "trigger_type": trigger.trigger_type,      # CONFIRM | ARM | WATCH
        "rule_name": trigger.rule_name,
        "game_key": trigger.game_key,
        "game_pk": getattr(s, "game_pk", None),
        "away": s.away, "home": s.home,
        "away_score": s.away_score, "home_score": s.home_score,
        "inning": s.inning, "half": s.half, "outs": s.outs,
        "pitcher": s.pitcher_name, "starter_tier": s.starter_tier,
        "pitch_count": s.pitch_count,
        "tto": s.times_through_order, "slot": s.batting_slot_due,
        "live_total": trigger.live_total, "pregame_total": trigger.pregame_total,
        "fair": round(trigger.anchor.expected_final, 2), "edge": round(trigger.edge, 2),
        "bullpen_ra9": trigger.bullpen_ra9,
        "pull_risk": pull_risk_label(trigger.bullpen_ra9, bullpen_elite_ra9).split(" ")[0],
        "data_age_s": s.data_age_seconds,
        "book": getattr(trigger.quote, "book", None),
    }
    if extra:
        row.update(extra)
    return row


class Ledger:
    """Opens the JSONL file lazily and appends one line per recorded signal."""

    def __init__(self, path: str | Path, bullpen_elite_ra9: float = 3.80):
        self.path = Path(path)
        self.bullpen_elite_ra9 = bullpen_elite_ra9
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, trigger, *, ts: Optional[str] = None,
               extra: Optional[dict] = None) -> dict:
        row = build_row(trigger, bullpen_elite_ra9=self.bullpen_elite_ra9, ts=ts, extra=extra)
        with self.path.open("a") as fh:
            fh.write(json.dumps(row) + "\n")
        return row
