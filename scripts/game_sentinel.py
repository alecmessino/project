"""Self-healing trigger: ensure the live tracker is running whenever our game is live.

GitHub's `schedule:` cron is unreliable (it skipped tonight's tip entirely). This
sentinel runs on a FREQUENT cron — every tick it asks ESPN whether a game we have
a config for is in progress, and if so and no tracker run is active, it dispatches
`live_game_tracker.yml`. Because it re-checks every few minutes it (a) catches the
tip even if some cron ticks are skipped, and (b) RESTARTS the tracker automatically
if it ever dies mid-game. Redundant with the direct schedule — belt and suspenders.

Env (provided by the workflow):
  GITHUB_TOKEN        to read workflow runs + dispatch (needs actions:write)
  GITHUB_REPOSITORY   "owner/repo"
  TRACKER_WORKFLOW    workflow file to dispatch (default live_game_tracker.yml)
  TRACKER_REF         git ref to run on (default master)
  TRACKER_MAX_MINUTES passed through to the tracker (default 210)
"""

from __future__ import annotations

import glob
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
ESPN = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
API = "https://api.github.com"


def _gh(method: str, path: str, token: str, body: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=20) as r:
        raw = r.read()
        return r.status, (json.loads(raw) if raw else {})


def _nba_configs():
    """(away_tag, home_tag, commence_epoch, config_relpath) for every NBA config."""
    import time as _t
    from datetime import datetime
    import yaml
    out = []
    for p in glob.glob(str(ROOT / "config" / "games" / "*.yaml")):
        try:
            ev = (yaml.safe_load(pathlib.Path(p).read_text()) or {}).get("event", {})
        except Exception:
            continue
        if str(ev.get("league", "")).upper() != "NBA":
            continue
        away = str(ev.get("away", "")).split()[-1].lower()
        home = str(ev.get("home", "")).split()[-1].lower()
        if not (away and home):
            continue
        epoch = 0.0
        ct = str(ev.get("commence_time", "") or "")
        for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"):
            try:
                epoch = datetime.strptime(ct.replace("Z", "+0000"), fmt).timestamp()
                break
            except ValueError:
                continue
        out.append((away, home, epoch, str(pathlib.Path(p).relative_to(ROOT))))
    return out


def _live_game(configs):
    """Return (config_relpath, detail) for a live ESPN game; if several same-matchup
    configs match, pick the one whose tip-off is nearest now (correct series game)."""
    import time as _t
    try:
        d = json.loads(urllib.request.urlopen(ESPN, timeout=15).read())
    except Exception as e:
        print(f"ESPN fetch failed: {e}")
        return None, None
    now = _t.time()
    candidates = []
    for e in d.get("events", []):
        comps = (e.get("competitions") or [{}])[0].get("competitors", [])
        names = " ".join(c.get("team", {}).get("displayName", "") for c in comps)
        hay = f"{e.get('shortName','')} {e.get('name','')} {names}".lower()
        state = e.get("status", {}).get("type", {}).get("state")
        detail = e.get("status", {}).get("type", {}).get("detail", "")
        for away, home, epoch, rel in configs:
            if away in hay and home in hay:
                print(f"matched {rel}: ESPN '{e.get('shortName')}' state={state} ({detail})")
                if state == "in":
                    candidates.append((abs((epoch or now) - now), rel, detail))
    if not candidates:
        return None, None
    candidates.sort()                       # nearest tip-off first
    return candidates[0][1], candidates[0][2]


def main() -> int:
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    wf = os.environ.get("TRACKER_WORKFLOW", "live_game_tracker.yml")
    ref = os.environ.get("TRACKER_REF", "master")
    max_minutes = os.environ.get("TRACKER_MAX_MINUTES", "210")
    if not (token and repo):
        print("GITHUB_TOKEN / GITHUB_REPOSITORY missing — cannot run sentinel")
        return 1

    configs = _nba_configs()
    print(f"watching {len(configs)} NBA config(s)")
    rel, detail = _live_game(configs)
    if not rel:
        print("no tracked game is live right now — nothing to do.")
        return 0

    # Already covered? Skip if a tracker run is queued or in progress.
    try:
        _, runs = _gh("GET", f"/repos/{repo}/actions/workflows/{wf}/runs"
                              "?per_page=20", token)
        active = [r for r in runs.get("workflow_runs", [])
                  if r.get("status") in ("queued", "in_progress", "waiting", "requested")]
        if active:
            print(f"tracker already active ({active[0]['status']}, run {active[0]['id']}) — leaving it.")
            return 0
    except Exception as e:
        print(f"run-status check failed ({e}); will attempt dispatch anyway.")

    # Game is live and nothing is running — start the tracker.
    print(f"GAME LIVE ({detail}) and no tracker running → dispatching {wf} for {rel}")
    try:
        status, _ = _gh("POST", f"/repos/{repo}/actions/workflows/{wf}/dispatches", token,
                        {"ref": ref, "inputs": {"game": rel, "max_minutes": max_minutes}})
        print(f"dispatch status {status} ✓ (tracker starting for {rel})")
        return 0
    except urllib.error.HTTPError as e:
        print(f"dispatch failed: HTTP {e.code} {e.read().decode()[:300]}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
