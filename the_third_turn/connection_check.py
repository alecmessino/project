#!/usr/bin/env python3
"""Ping every live endpoint once and verify we get a usable JSON payload.

Confirms the "piping" works before running the daemon: for each source it prints
HTTP status, latency, payload size, and a sample of parsed data (game/quote count
+ one example), then exits non-zero if any REQUIRED source failed or 403'd.

DraftKings is intentionally absent — it 403s this datacenter IP regardless of
User-Agent (an edge/IP block UA rotation can't defeat); FanDuel replaces it.

    python the_third_turn/connection_check.py
"""

from __future__ import annotations

import asyncio
import sys
from datetime import date
from pathlib import Path

# Make sibling packages importable when run as a script from any cwd.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import aiohttp  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402

from sources.base import SourceResult  # noqa: E402
from sources.bovada import BovadaSource  # noqa: E402
from sources.fanduel import FanDuelSource  # noqa: E402
from sources.mlb_statsapi import MLBStatsSource  # noqa: E402
from sources.pinnacle import PinnacleSource  # noqa: E402

console = Console()

# Which sources must succeed for the daemon to be viable. Pinnacle is a bonus.
REQUIRED = {"mlb_statsapi", "fanduel", "bovada"}


def _sample(res: SourceResult) -> str:
    if res.states:
        s = res.states[0]
        return (f"{len(res.states)} live game(s); e.g. {s.away}@{s.home} "
                f"inn {s.inning} {s.half}, {s.pitcher_name or '?'} "
                f"PC={s.pitch_count} slot={s.batting_slot_due} TTO={s.times_through_order}")
    if res.quotes:
        q = res.quotes[0]
        return (f"{len(res.quotes)} quote(s); e.g. {q.away}@{q.home} "
                f"O/U {q.line} ({q.over_odds}/{q.under_odds})")
    return "connected, but no games/quotes parsed right now"


async def main() -> int:
    today = date.today().isoformat()
    sources = [
        MLBStatsSource(date=today, live_only=False),
        FanDuelSource(),
        BovadaSource(),
        PinnacleSource(),
    ]
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(*(s.fetch(session) for s in sources))

    table = Table(title=f"The Third Turn · connection check ({today})")
    for col in ("Source", "OK", "HTTP", "Latency", "Bytes", "Sample / error"):
        table.add_column(col, overflow="fold")

    failures = []
    for res in results:
        ok_mark = "[green]✓[/]" if res.ok else "[red]✗[/]"
        detail = _sample(res) if res.ok else f"[red]{res.error}[/]"
        table.add_row(
            res.name, ok_mark,
            str(res.http_status or "-"),
            f"{res.latency_ms:.0f} ms" if res.latency_ms else "-",
            f"{res.payload_bytes:,}" if res.payload_bytes else "-",
            detail,
        )
        if res.name in REQUIRED and not res.ok:
            failures.append(res.name)

    console.print(table)
    if failures:
        console.print(f"[red]FAILED required source(s): {', '.join(failures)}[/]")
        return 1
    console.print("[green]All required sources returned a usable JSON payload (no 403).[/]")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
