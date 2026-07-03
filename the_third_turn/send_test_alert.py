#!/usr/bin/env python3
"""Post one synthetic embed to confirm the Discord webhook + formatting land.

    DISCORD_WEBHOOK_URL=… python the_third_turn/send_test_alert.py
    # or put it in the_third_turn/.env
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import aiohttp  # noqa: E402

from shared_piping.envload import load_env  # noqa: E402
from shared_piping.notify import DiscordNotifier  # noqa: E402
from shared_piping.run_expectancy import RunEnvAnchor  # noqa: E402
from live_engine import Trigger  # noqa: E402
from sources.base import LiveGameState, Quote  # noqa: E402


def _demo_trigger() -> Trigger:
    s = LiveGameState(game_pk=1, away="CWS", home="ATL", inning=6, half="top", away_score=2,
                      home_score=1, pitcher_id=99, pitcher_name="Test Starter (demo)",
                      pitch_count=82, batting_slot_due=2, times_through_order=3, status="Live",
                      outs=0, starter_tier="Back", data_age_seconds=14.0)
    anchor = RunEnvAnchor(expected_final=8.6, base_remaining=4.2, situational=0.4,
                          frac_remaining=0.44, park=1.0)
    return Trigger("CONFIRM", "TTO3-Mid/Back", s.game_key, s,
                   Quote(book="fanduel", home="ATL", away="CWS", line=7.5),
                   9.0, 7.5, anchor, 4.6, ["demo alert"])


async def _main() -> int:
    load_env()
    notifier = DiscordNotifier()
    if not notifier.enabled:
        print("DISCORD_WEBHOOK_URL not set (env or .env) — nothing to send.")
        return 2
    async with aiohttp.ClientSession() as session:
        ok = await notifier.post(session, _demo_trigger())
    print("✅ test embed posted to Discord." if ok else "❌ Discord post failed (see error above).")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
