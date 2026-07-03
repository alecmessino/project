#!/usr/bin/env python3
"""Daily maintenance probe — is the V3 sample ripe, and are the streams healthy?

Reads the banked panels (committed by the 24/7 Actions runner) and reports:
  * COVERAGE — distinct live (game, date) captured in the team-total panel. Nearly every
    game has a Mid/Back starter reaching his TTO cliff, so live-games-captured ≈ cliff
    events. Ripe for a first directional V3 read at ~50; robust at ~100.
  * HEALTH — row counts + most-recent timestamp per stream, and malformed-line count, so
    a stalled or corrupted stream is caught early.

Exit code 0 always; the scheduled check parses the RIPE/HEALTH verdict lines.

    python the_third_turn/ripeness_check.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "output"
FIRST_LOOK = 50
ROBUST = 100
STREAMS = ("ledger.jsonl", "book_panel.jsonl", "team_total_panel.jsonl")


def _rows(path: Path):
    rows, bad = [], 0
    if not path.exists():
        return rows, bad
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            bad += 1
    return rows, bad


def main() -> int:
    tt, tt_bad = _rows(OUT / "team_total_panel.jsonl")
    live = {(r.get("ts", "")[:10], r.get("game")) for r in tt if r.get("live")}
    n = len(live)
    ripe = n >= FIRST_LOOK
    print(f"COVERAGE: {n} distinct live game-days captured "
          f"(first-look {FIRST_LOOK}, robust {ROBUST})")
    print(f"RIPE: {'YES' if ripe else 'no'} "
          f"({'ready for a first V3 read' if ripe else f'{FIRST_LOOK - n} more to go'})")

    print("HEALTH:")
    stale = []
    for s in STREAMS:
        rows, bad = _rows(OUT / s)
        last = max((r.get("ts", "") for r in rows), default="—")
        flag = " [MALFORMED]" if bad else ""
        print(f"  {s}: {len(rows)} rows, last {last}{flag}")
        if bad:
            stale.append(f"{s} has {bad} malformed rows")
    # freshness: team-total panel shouldn't be empty if the runner is up
    if not tt:
        stale.append("team_total_panel.jsonl empty — runner may be down")
    print(f"HEALTH_OK: {'no — ' + '; '.join(stale) if stale else 'yes'}")
    print(f"CHECKED_AT: {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
