"""One-shot engine run for GitHub Actions → docs/state.json.

Fetches a single live snapshot (Odds API + ESPN), runs the engine,
merges in any previously-accumulated signals, and writes docs/state.json.
GitHub Pages serves that file; the dashboard JS polls it.
"""

from __future__ import annotations

import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mrbet.config import GameConfig, Settings
from mrbet.engine import Engine
from mrbet.odds.theodds import TheOddsProvider
from mrbet.web.server import DashboardState

GAME_YAML = ROOT / "config" / "games" / "okc_sas_2026-05-28.yaml"
STATE_JSON = ROOT / "docs" / "state.json"

settings = Settings.load(ROOT / "config" / "settings.yaml")
game = GameConfig.load(GAME_YAML)

state = DashboardState(game)

# Carry forward previously-accumulated signals across runs.
if STATE_JSON.exists():
    try:
        prev = json.loads(STATE_JSON.read_text())
        state.signals = prev.get("signals", [])
    except Exception:
        pass

provider = TheOddsProvider(
    event=game.event,
    markets=settings.engine.markets,
    poll_interval=0,
    books=settings.engine.books,
    region=settings.engine.region,
    fallback_consensus=settings.engine.fallback_consensus,
    max_polls=1,
)

engine = Engine(settings, game, provider=None)

try:
    for snap in provider.snapshots():
        if snap.state is None:
            # ESPN didn't find the game; mark waiting and preserve signals.
            state.header.update({
                "status": "waiting",
                "updated": time.strftime("%H:%M:%S"),
                "error": "game not found on ESPN scoreboard",
            })
            break
        results = engine.process_snapshot(snap)
        state.update(snap, results)
        for r in results:
            if r.signal:
                state.add_signal(r.signal)
        credits = snap.meta.get("credits_remaining")
        if credits is not None:
            print(f"API credits remaining: {credits}")
except Exception as exc:
    state.header.update({
        "status": "error",
        "updated": time.strftime("%H:%M:%S"),
        "error": str(exc),
    })
    print(f"Error: {exc}", file=sys.stderr)

STATE_JSON.write_bytes(state.to_json())
print(f"Wrote {STATE_JSON}  ({len(state.signals)} signals, {len(state.rows)} rows)")
