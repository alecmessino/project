"""Cadence-aware forward-capture poller -> docs/state.json + docs/forward.json.

Runs as the 5-minute GitHub Actions cron. Every run it checks the FREE ESPN
clock; it spends a (paid) Odds API fetch ONLY when the game clock has crossed an
uncaptured 9-point cadence mark (Q1-Q3 timeouts + breaks: 6,9,12,18,21,24,30,33,
36). Captured marks persist across runs in docs/forward.json, so the whole game
costs ~9 odds calls. Between marks it just refreshes the clock/score for free.

Active game: MRBET_GAME env (default sas_okc_2026-05-30.yaml). Key from the
ODDS_API_KEY secret (CI) or .env (local).
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mrbet import forward as fwd
from mrbet.cadence import timeout_marks
from mrbet.config import GameConfig, Settings
from mrbet.engine import Engine
from mrbet.envload import load_env
from mrbet.odds.theodds import TheOddsProvider
from mrbet.web.server import DashboardState

load_env()

GAME_YAML = pathlib.Path(os.environ.get(
    "MRBET_GAME", ROOT / "config" / "games" / "sas_okc_2026-05-30.yaml"))
STATE_JSON = ROOT / "docs" / "state.json"
FORWARD_JSON = ROOT / "docs" / "forward.json"
MARKS = timeout_marks()   # [6,9,12,18,21,24,30,33,36]

settings = Settings.load(ROOT / "config" / "settings.yaml")
game = GameConfig.load(GAME_YAML)
matchup = f"{game.event.away_key} @ {game.event.home_key}"

# Restore prior dashboard state + forward ledger + captured marks.
prev_state = json.loads(STATE_JSON.read_text()) if STATE_JSON.exists() else {}
prev_fwd = json.loads(FORWARD_JSON.read_text()) if FORWARD_JSON.exists() else {}
ledger = prev_fwd.get("ledger", {})
captured = set(prev_fwd.get("scope", {}).get("captured_marks", []))
finals = getattr(game, "finals", None) or None

state = DashboardState(game)
state.signals = prev_state.get("signals", [])

provider = TheOddsProvider(
    event=game.event, markets=settings.engine.markets, poll_interval=0,
    books=settings.engine.books, region=settings.engine.region,
    fallback_consensus=settings.engine.fallback_consensus, max_polls=1,
)

espn = provider._fetch_state()            # FREE clock/score
captured_now = None

if espn is None:
    # Game not live yet (or finished/not found) — refresh header, spend nothing.
    state.header.update({
        "status": "waiting", "updated": time.strftime("%H:%M:%S"),
        "error": "game not live on ESPN scoreboard (pre-tip or finished)",
    })
    state.rows = []   # no live markets before tip / after final
else:
    elapsed = espn.minutes_elapsed
    # Earliest uncaptured mark the clock has reached (one capture per run).
    due = next((m for m in MARKS if m <= elapsed and m not in captured), None)
    if due is not None:
        lines = provider._fetch_lines()    # PAID — only at a cadence mark
        from mrbet.odds.base import Snapshot
        snap = Snapshot(state=espn, lines=lines, meta={
            "credits_remaining": provider.credits_remaining(),
            "clock": provider._clock, "cadence_mark": due})
        results = engine = Engine(settings, game, provider=None).process_snapshot(snap)
        state.update(snap, results)
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        for r in results:
            if r.signal:
                state.add_signal(r.signal)
            fwd.merge_signal(ledger, r.evaluation, ts, matchup, finals)
        captured.add(due)
        captured_now = due
        print(f"captured cadence mark m{due:.0f} "
              f"(credits remaining: {provider.credits_remaining()})")
    else:
        # Between marks — free clock refresh, keep prior rows.
        state.header.update({
            "status": "live", "period": espn.period.value,
            "clock": provider._clock, "away_score": espn.away_score,
            "home_score": espn.home_score,
            "minutes_remaining": round(espn.minutes_remaining, 1),
            "minutes_elapsed": round(espn.minutes_elapsed, 1),
            "updated": time.strftime("%H:%M:%S"),
        })
        state.rows = prev_state.get("rows", [])
        print(f"between marks at {elapsed:.1f}m elapsed — no odds call (captured: {sorted(captured)})")

STATE_JSON.write_bytes(state.to_json())
fwd.dump(FORWARD_JSON, ledger, scope={
    "matchup": matchup, "game": game.event.id,
    "cadence": "9-point timeout", "marks": MARKS,
    "captured_marks": sorted(captured),
})
print(f"Wrote {STATE_JSON} ({len(state.rows)} rows) and {FORWARD_JSON} "
      f"({len(ledger)} bets, {len(captured)}/{len(MARKS)} marks captured)"
      + (f" [+m{captured_now:.0f}]" if captured_now is not None else ""))
