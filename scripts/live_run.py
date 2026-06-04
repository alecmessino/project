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


def _commit_push(paths: list[str], msg: str) -> None:
    """Stage `paths`, commit if anything changed, push with rebase+retry.

    Concurrent bot workflows (board/midnight) also push to master, which would
    reject our push as non-fast-forward — so we rebase our commit on top and retry
    rather than let live updates get permanently blocked.
    """
    subprocess.run(["git", "add", *paths], cwd=ROOT, check=False)
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode == 0:
        return  # nothing changed
    subprocess.run(["git", "commit", "-m", msg], cwd=ROOT, check=False)
    for _ in range(5):
        if subprocess.run(["git", "push"], cwd=ROOT).returncode == 0:
            return
        subprocess.run(["git", "pull", "--rebase", "--no-edit"], cwd=ROOT, check=False)
        time.sleep(2)
    print(f"push still failing after retries ({msg})", flush=True)


def git_sync() -> None:
    # live_market_state.json is the file the dashboard streams (every ~20s); state.json
    # is kept as a legacy alias. Push both so the hot stream stays current.
    _commit_push(["docs/live_market_state.json", "docs/state.json",
                  "docs/forward.json", "docs/odds_history.json"],
                 "chore: live loop state [skip ci]")


def grade_and_sync() -> None:
    """Post-final: settle the forward ledger (W/L + CLV) and push it.

    grade_forward.py is idempotent and safe before the game is final (it no-ops
    until ESPN reports the box score). ESPN's summary can lag the final whistle by
    a minute, so retry a few times until no pending bets remain, then push the
    graded forward.json plus the YAML finals block the grader patches in.
    """
    import json as _json
    fpath = ROOT / "docs" / "forward.json"
    for attempt in range(4):
        subprocess.run([sys.executable, str(ROOT / "scripts" / "grade_forward.py")],
                       cwd=ROOT, check=False)
        try:
            led = _json.loads(fpath.read_text()).get("ledger", {})
            if not any(b.get("outcome") in ("pending", None, "") for b in led.values()):
                break
        except Exception:
            pass
        if attempt < 3:
            print(f"grade: finals not ready, retry in 30s ({attempt + 1}/4)", flush=True)
            time.sleep(30)
    _commit_push(["docs/forward.json", "config/games/"],
                 "chore: final grade — settle forward bets + CLV [skip ci]")


def _game_team_tags() -> tuple[str | None, str | None]:
    """(away, home) team nicknames from MRBET_GAME, lowercased — game-agnostic."""
    cfg = os.environ.get("MRBET_GAME", "")
    try:
        import yaml
        ev = (yaml.safe_load(pathlib.Path(cfg).read_text()) or {}).get("event", {})
        return ev["away"].split()[-1].lower(), ev["home"].split()[-1].lower()
    except Exception:
        return None, None


def espn_is_final() -> bool:
    """Authoritative final check from ESPN (state == 'post') for THIS game.

    Matches the configured game by team nickname (e.g. 'knicks'/'spurs') instead of
    a hardcoded matchup, so the loop exits cleanly for any game we track.
    """
    away_tag, home_tag = _game_team_tags()
    if not (away_tag and home_tag):
        return False
    try:
        d = json.loads(urllib.request.urlopen(ESPN, timeout=10).read())
        for e in d.get("events", []):
            comps = (e.get("competitions") or [{}])[0].get("competitors", [])
            names = " ".join(c.get("team", {}).get("displayName", "") for c in comps)
            hay = f"{e.get('shortName','')} {e.get('name','')} {names}".lower()
            if away_tag in hay and home_tag in hay:
                return e.get("status", {}).get("type", {}).get("state") == "post"
    except Exception:
        return False
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
                  f"{h.get('away','away')} {h.get('away_score')} "
                  f"{h.get('home','home')} {h.get('home_score')} "
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
    print("live_run done — grading forward bets.", flush=True)
    grade_and_sync()   # settle W/L + CLV the moment the game is final


if __name__ == "__main__":
    main()
