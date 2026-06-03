"""Long-running live loop for a single game — the reliable runner.

Designed to run INSIDE one GitHub Actions job (those run up to ~6h), so live
coverage no longer depends on the throttled 5-minute cron or on any interactive
session staying alive. Every LIVE_CYCLE_SECONDS it:

  1. runs one poller cycle (scripts/gh_pages_update.py) — free ESPN clock check,
     a paid odds fetch only at an uncaptured cadence mark, reversion + edge alerts,
  2. commits & pushes the refreshed docs/ state so the dashboard stays live,
  3. stops when ESPN reports the game final (or LIVE_MAX_MINUTES elapses).

Env:
  MRBET_GAME           game YAML (passed through to the poller)
  LIVE_CYCLE_SECONDS   seconds between cycles (default 75)
  LIVE_MAX_MINUTES     hard stop (default 300 = 5h, covers OT)
  ODDS_API_KEY / DISCORD_WEBHOOK_URL / ... from the workflow secrets
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
STATE = ROOT / "docs" / "state.json"
CYCLE = int(os.environ.get("LIVE_CYCLE_SECONDS", "75"))
MAX_MINUTES = int(os.environ.get("LIVE_MAX_MINUTES", "300"))
ESPN = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"


def run_cycle() -> None:
    subprocess.run([sys.executable, str(ROOT / "scripts" / "gh_pages_update.py")],
                   cwd=ROOT, check=False)


def git_sync() -> None:
    # live_market_state.json is the file the dashboard streams (every ~20s); state.json
    # is kept as a legacy alias. Push both so the hot stream stays current.
    subprocess.run(["git", "add", "docs/live_market_state.json", "docs/state.json",
                    "docs/forward.json", "docs/odds_history.json"], cwd=ROOT, check=False)
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode != 0:
        subprocess.run(["git", "commit", "-m", "chore: live loop state [skip ci]"],
                       cwd=ROOT, check=False)
        subprocess.run(["git", "push"], cwd=ROOT, check=False)


def espn_is_final() -> bool:
    """Authoritative final check straight from ESPN (state == 'post')."""
    try:
        d = json.loads(urllib.request.urlopen(ESPN, timeout=10).read())
        ev = next(e for e in d["events"]
                  if "OKC" in e.get("shortName", "") and "SA" in e.get("shortName", ""))
        return ev["status"]["type"]["state"] == "post"
    except Exception:
        return False


def main() -> None:
    deadline = time.time() + MAX_MINUTES * 60
    print(f"live_run start: cycle={CYCLE}s max={MAX_MINUTES}m game={os.environ.get('MRBET_GAME')}",
          flush=True)
    final_streak = 0
    while time.time() < deadline:
        try:
            run_cycle()
            git_sync()
            h = json.loads(STATE.read_text()).get("header", {})
            print(f"[{time.strftime('%H:%M:%S')}] {h.get('clock')} "
                  f"SA {h.get('away_score')} OKC {h.get('home_score')} "
                  f"rem {h.get('minutes_remaining')}", flush=True)
        except Exception as e:  # never let one bad cycle kill the loop
            print(f"cycle error: {type(e).__name__}: {e}", flush=True)

        # Two consecutive ESPN 'post' reads → game truly over, exit.
        if espn_is_final():
            final_streak += 1
            if final_streak >= 2:
                print("ESPN reports final — exiting live loop.", flush=True)
                break
        else:
            final_streak = 0
        time.sleep(CYCLE)
    print("live_run done.", flush=True)


if __name__ == "__main__":
    main()
