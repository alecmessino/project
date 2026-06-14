"""Self-healing trigger: ensure the live tracker is running whenever a game is live.

Every tick (frequent cron) it asks Bovada whether any NBA/WNBA game is live. For a
live game it locates a matching config — and if NONE exists, it AUTO-GENERATES one
from the discovered Bovada metadata (event id, total, spread, league) so the tracker
can attach to ANY live game without a hand-made config. Pre-built configs always win
(hand-tuning preserved). It then commits the new config and dispatches
`live_game_tracker.yml` (unless a tracker run is already active). Because it
re-checks every few minutes it both catches the tip (even if cron ticks slip) and
RESTARTS the tracker if it dies mid-game.

Env (provided by the workflow):
  GITHUB_TOKEN        read workflow runs + dispatch (needs actions:write)
  GITHUB_REPOSITORY   "owner/repo"
  TRACKER_WORKFLOW    workflow file to dispatch (default live_game_tracker.yml)
  TRACKER_REF         git ref to run on (default master)
  TRACKER_MAX_MINUTES passed through to the tracker (default 210)
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
API = "https://api.github.com"
LEAGUES = ("nba",)          # basketball leagues the sentinel watches (WNBA removed)


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


def _detect_live():
    """Across leagues, return (config_relpath, detail, created) for a live game —
    auto-generating a config from Bovada metadata when none exists. None if nothing
    is live. board_update.ensure_live_config does the discovery + config-gen so the
    Bovada/line/league logic lives in one place."""
    import board_update as bu
    for league in LEAGUES:
        try:
            res = bu.ensure_live_config(league)
        except Exception as e:           # never let one league's hiccup kill the run
            print(f"[{league}] detect failed: {type(e).__name__}: {e}")
            continue
        if res:
            rel, detail, created = res
            print(f"[{league}] LIVE → {rel}  ({detail}){' [auto]' if created else ''}")
            return rel, detail, created
        print(f"[{league}] nothing live")
    return None


def _commit_config(rel: str) -> None:
    """Commit + push a newly auto-generated config so the tracker's checkout sees it."""
    subprocess.run(["git", "config", "user.name", "github-actions[bot]"], cwd=ROOT, check=False)
    subprocess.run(["git", "config", "user.email",
                    "github-actions[bot]@users.noreply.github.com"], cwd=ROOT, check=False)
    subprocess.run(["git", "add", "config/games/"], cwd=ROOT, check=False)
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode == 0:
        return
    subprocess.run(["git", "commit", "-m",
                    f"chore: auto-generate live config {rel} [skip ci]"], cwd=ROOT, check=False)
    for _ in range(4):
        if subprocess.run(["git", "push"], cwd=ROOT).returncode == 0:
            print(f"pushed auto-generated {rel}")
            return
        subprocess.run(["git", "pull", "--rebase", "--no-edit"], cwd=ROOT, check=False)
    print(f"WARNING: could not push {rel} — tracker may not see it")


def tick(token: str, repo: str, wf: str, ref: str, max_minutes: str) -> int:
    """One detect→dispatch pass. Reused by both the 10-min cron (`main`) and the
    long-running watchdog (`sentinel_watch.py`), so the Bovada/dispatch logic lives
    in exactly one place. Returns 0 on success (live game covered or nothing live)."""
    found = _detect_live()
    if not found:
        print("no live game right now — nothing to do.")
        return 0
    rel, detail, created = found

    # Already covered? Skip if a tracker run is queued or in progress.
    try:
        _, runs = _gh("GET", f"/repos/{repo}/actions/workflows/{wf}/runs?per_page=20", token)
        active = [r for r in runs.get("workflow_runs", [])
                  if r.get("status") in ("queued", "in_progress", "waiting", "requested")]
        if active:
            print(f"tracker already active ({active[0]['status']}, run {active[0]['id']}) — leaving it.")
            return 0
    except Exception as e:
        print(f"run-status check failed ({e}); will attempt dispatch anyway.")

    # Push the freshly auto-generated config BEFORE dispatch so the tracker's
    # checkout of `ref` includes it.
    if created:
        _commit_config(rel)

    print(f"GAME LIVE ({detail}) and no tracker running → dispatching {wf} for {rel}")
    try:
        status, _ = _gh("POST", f"/repos/{repo}/actions/workflows/{wf}/dispatches", token,
                        {"ref": ref, "inputs": {"game": rel, "max_minutes": max_minutes}})
        print(f"dispatch status {status} ✓ (tracker starting for {rel})")
        return 0
    except urllib.error.HTTPError as e:
        print(f"dispatch failed: HTTP {e.code} {e.read().decode()[:300]}")
        return 1


def main() -> int:
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    wf = os.environ.get("TRACKER_WORKFLOW", "live_game_tracker.yml")
    ref = os.environ.get("TRACKER_REF", "master")
    max_minutes = os.environ.get("TRACKER_MAX_MINUTES", "210")
    if not (token and repo):
        print("GITHUB_TOKEN / GITHUB_REPOSITORY missing — cannot run sentinel")
        return 1
    return tick(token, repo, wf, ref, max_minutes)


if __name__ == "__main__":
    raise SystemExit(main())
