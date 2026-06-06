"""Auto-grade the forward-capture ledger once ESPN reports a completed game.

Safe to run on every 5-minute cron cycle — exits 0 with no writes if the
game has not yet finished. Once ESPN marks the game completed:
  1. Fetches quarter + team final scores from the ESPN summary endpoint (free).
  2. Re-grades every pending bet in docs/forward.json against those actuals.
  3. Appends a `finals:` block to the game YAML so manual re-runs and the
     live poll loop both carry the final score without re-hitting ESPN.

Usage:
  python scripts/grade_forward.py
  MRBET_GAME=config/games/sas_okc_2026-05-30.yaml python scripts/grade_forward.py
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mrbet.config import GameConfig
from mrbet.espn import ESPNClient
from mrbet.envload import load_env
from mrbet import forward as fwd

load_env()

GAME_YAML = pathlib.Path(os.environ.get(
    "MRBET_GAME", ROOT / "config" / "games" / "sas_okc_2026-05-30.yaml"))
FORWARD_JSON = ROOT / "docs" / "forward.json"

game = GameConfig.load(GAME_YAML)

# --- already graded via the YAML finals block in a prior run? ---
if game.finals:
    finals_from_yaml = game.finals
    print(f"Using finals from {GAME_YAML.name}: "
          f"total={finals_from_yaml.get('game', {}).get('full')}")
    finals = finals_from_yaml
    espn_fetch_needed = False
else:
    espn_fetch_needed = True
    finals = None

if espn_fetch_needed:
    # ESPN files a game under its US-Eastern calendar date. commence_time may be in
    # UTC (e.g. "2026-06-04T00:30:00+0000" = 8:30 PM ET on 6/3), so convert to ET
    # and also try +/-1 day to be safe around the date boundary.
    from datetime import datetime, timedelta
    try:
        from zoneinfo import ZoneInfo
        _ET = ZoneInfo("America/New_York")
    except Exception:
        _ET = None

    ct = game.event.commence_time or ""
    dt = None
    for _fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"):
        try:
            dt = datetime.strptime(ct.replace("Z", "+0000"), _fmt)
            break
        except ValueError:
            continue
    if dt is None:
        print(f"Cannot derive game date from commence_time={ct!r} — skipping")
        sys.exit(0)
    base = (dt.astimezone(_ET).date() if (dt.tzinfo and _ET) else dt.date())
    candidates = [(base + timedelta(days=d)).strftime("%Y%m%d") for d in (0, -1, 1)]

    client = ESPNClient(use_cache=False, league=str(getattr(game.event, "league", "nba")))
    found = None
    for game_date in candidates:
        found = client.find_completed_game(game_date, game.event.home, game.event.away)
        if found:
            break
    if not found:
        print(f"Game {game.event.id} not yet complete on ESPN "
              f"(tried dates {candidates}) — skipping grade")
        sys.exit(0)

    espn_id, sname = found
    print(f"Completed: {sname} (ESPN ID {espn_id})")

    fetched = client.fetch_finals(espn_id)
    if not fetched:
        print("ESPN summary did not return finals — skipping grade")
        sys.exit(0)

    away_abbr, home_abbr, esp_finals = fetched

    # Map ESPN abbreviations (e.g. "SA") -> game YAML keys (e.g. "SAS").
    # The away/home position is authoritative; abbreviation spelling may differ.
    away_pts = esp_finals["team"].get(away_abbr)
    home_pts = esp_finals["team"].get(home_abbr)
    if away_pts is None or home_pts is None:
        print(f"Unexpected team keys in ESPN finals: {list(esp_finals['team'])} "
              f"(expected {away_abbr}/{home_abbr}) — skipping grade")
        sys.exit(0)

    finals = {
        "game": esp_finals["game"],
        "team": {
            game.event.away_key: away_pts,
            game.event.home_key: home_pts,
        },
    }

total = finals["game"]["full"]
a_pts = finals["team"][game.event.away_key]
h_pts = finals["team"][game.event.home_key]
print(f"Final: {game.event.away_key} {a_pts} – {h_pts} {game.event.home_key}  "
      f"(combined {total})")

# --- grade pending bets ---
if not FORWARD_JSON.exists():
    print("No docs/forward.json yet — nothing to grade")
    sys.exit(0)

existing = json.loads(FORWARD_JSON.read_text())
ledger = existing.get("ledger", {})
scope = existing.get("scope", {})

if not ledger:
    print("Ledger is empty (no bets captured yet) — nothing to grade")
    sys.exit(0)

graded = 0
for k, entry in ledger.items():
    if entry.get("outcome") not in ("pending", None, ""):
        continue
    parts = k.split(":", 3)
    if len(parts) != 4:
        continue
    market_type, period, team_or_game, side = parts
    team = None if team_or_game == "game" else team_or_game
    actual = fwd._actual_final(finals, market_type, period, team)
    if actual is not None:
        outcome, profit = fwd._grade(side, entry["entry_line"], actual,
                                     entry["entry_odds"])
        entry["outcome"] = outcome
        entry["profit"] = round(profit, 3)
        graded += 1
        print(f"  {k}: line {entry['entry_line']} vs actual {actual} "
              f"→ {outcome} ({profit:+.3f}u)")

scope["finals"] = finals
scope["graded_ts"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

fwd.dump(FORWARD_JSON, ledger, scope=scope)
s = fwd.summarize(ledger)
print(f"\nGraded {graded} bet(s). "
      f"Record: {s['wins']}-{s['losses']}-{s['pushes']} "
      f"({s['pending']} still pending). Written → {FORWARD_JSON}")

# --- patch game YAML with finals for future runs ---
if espn_fetch_needed:
    yaml_text = GAME_YAML.read_text()
    if "finals:" not in yaml_text:
        g = finals["game"]
        t = finals["team"]
        block = (
            f"\nfinals:\n"
            f"  game:\n"
            f"    full: {g['full']}\n"
            f"    h1:   {g['h1']}\n"
            f"    q1:   {g['q1']}\n"
            f"    q2:   {g['q2']}\n"
            f"    q3:   {g['q3']}\n"
            f"    q4:   {g['q4']}\n"
            f"  team:\n"
            f"    {game.event.away_key}: {t[game.event.away_key]}\n"
            f"    {game.event.home_key}: {t[game.event.home_key]}\n"
        )
        GAME_YAML.write_text(yaml_text.rstrip() + "\n" + block)
        print(f"Patched {GAME_YAML.name} with finals block")
