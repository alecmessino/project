"""Self-perpetuating sentinel — the reliability fix for GitHub's flaky cron.

GitHub's scheduled workflows are best-effort: the `*/10` sentinel cron has been
firing only ~hourly and routinely goes silent for 2h+, which is how NBA Finals G5
tipped (00:30 UTC) inside a dead window and was never auto-tracked. Relying on the
scheduler to land on a tip-off is the wrong foundation.

This runs ONE long-lived job (inside a single Actions run, which lasts up to ~6h)
that calls the sentinel detect→dispatch logic every WATCH_INTERVAL seconds. Cron
cadence no longer matters — coverage is continuous for the life of the run. Near the
Actions timeout it RE-ARMS itself (dispatches its own workflow) as long as a game is
live or tips within REARM_WINDOW_HOURS, so during a game day it stays up
back-to-back; only in the dead overnight hours does it exit and let the (now merely
"start once") bootstrap cron relaunch it. No external pinger, no PAT — just the
workflow's own GITHUB_TOKEN.

Env (from the workflow):
  GITHUB_TOKEN / GITHUB_REPOSITORY        auth + "owner/repo"
  TRACKER_WORKFLOW / TRACKER_REF / TRACKER_MAX_MINUTES   passed to each tick
  SELF_WORKFLOW          this watchdog's workflow file (default sentinel_watch.yml)
  WATCH_INTERVAL         seconds between detect passes (default 180)
  WATCH_MAX_MINUTES      run length before re-arm (default 330 = 5.5h; GH cap is 360)
  REARM_WINDOW_HOURS     re-arm if a game tips within this many hours (default 6)
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import game_sentinel as gs  # reuse the single source of detect→dispatch truth

LEAGUES = ("nba",)   # WNBA removed — sentinel/watchdog track NBA only


def _scoreboard(league: str) -> dict:
    url = (f"https://site.api.espn.com/apis/site/v2/sports/basketball/"
           f"{league}/scoreboard")
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read())


def _has_activity(window_hours: float) -> bool:
    """True if any watched-league game is live now OR tips within `window_hours`.

    Drives the re-arm decision: while the slate is active (or imminent) we keep a
    watchdog alive continuously; once the day is truly over we let it exit."""
    now = datetime.now(timezone.utc)
    for league in LEAGUES:
        try:
            d = _scoreboard(league)
        except Exception as e:
            print(f"[{league}] activity check failed: {type(e).__name__}: {e}")
            continue
        for e in d.get("events", []):
            state = e.get("status", {}).get("type", {}).get("state")
            if state == "in":
                print(f"[{league}] live now: {e.get('shortName','')} → stay up")
                return True
            if state == "pre":
                try:
                    tip = datetime.strptime(e.get("date", ""), "%Y-%m-%dT%H:%MZ")
                    tip = tip.replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
                hrs = (tip - now).total_seconds() / 3600.0
                if 0 <= hrs <= window_hours:
                    print(f"[{league}] {e.get('shortName','')} tips in {hrs:.1f}h → stay up")
                    return True
    return False


def _rearm(token: str, repo: str, self_wf: str, ref: str) -> None:
    body = json.dumps({"ref": ref}).encode()
    req = urllib.request.Request(
        f"{gs.API}/repos/{repo}/actions/workflows/{self_wf}/dispatches",
        data=body, method="POST", headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        })
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            print(f"re-armed watchdog (dispatch {self_wf} → {r.status})")
    except urllib.error.HTTPError as e:
        print(f"re-arm failed: HTTP {e.code} {e.read().decode()[:200]}")


def main() -> int:
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not (token and repo):
        print("GITHUB_TOKEN / GITHUB_REPOSITORY missing — cannot run watchdog")
        return 1
    wf = os.environ.get("TRACKER_WORKFLOW", "live_game_tracker.yml")
    ref = os.environ.get("TRACKER_REF", "master")
    max_minutes = os.environ.get("TRACKER_MAX_MINUTES", "210")
    self_wf = os.environ.get("SELF_WORKFLOW", "sentinel_watch.yml")
    interval = int(os.environ.get("WATCH_INTERVAL", "180"))
    run_minutes = int(os.environ.get("WATCH_MAX_MINUTES", "330"))
    rearm_window = float(os.environ.get("REARM_WINDOW_HOURS", "6"))

    deadline = time.time() + run_minutes * 60
    print(f"sentinel_watch start: interval={interval}s run={run_minutes}m "
          f"rearm_window={rearm_window}h repo={repo}", flush=True)
    while time.time() < deadline:
        try:
            gs.tick(token, repo, wf, ref, max_minutes)
        except Exception as e:  # never let one bad pass kill the watchdog
            print(f"tick error: {type(e).__name__}: {e}", flush=True)
        # Sleep in short steps so we exit promptly at the deadline.
        stop = min(deadline, time.time() + interval)
        while time.time() < stop:
            time.sleep(min(15, stop - time.time()))

    # End of this run's life — hand off to a fresh run if the slate is still active.
    if _has_activity(rearm_window):
        _rearm(token, repo, self_wf, ref)
    else:
        print("no live/upcoming games within window — exiting; bootstrap cron will relaunch.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
