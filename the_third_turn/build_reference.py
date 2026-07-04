#!/usr/bin/env python3
"""Build reference tables the live engine loads (Revision 2, Fixes #1 and #4).

From the MLB Stats API season pitching leaders (reachable; FanGraphs/xFIP are not):
  * config/bullpen_quality.json  — {team_key: bullpen_RA9}  (relievers = gamesStarted 0)
  * config/starter_tiers.json    — {pitcher_id: "Ace"|"Mid"|"Back"} by season WHIP

RA/9 (runs, not earned) is the bullpen-quality metric — consistent with Fix #2's
run-environment framing. Tiers let the engine flag ace-vs-back-of-rotation Overs.

    python the_third_turn/build_reference.py --seasons 2025
    python the_third_turn/build_reference.py --seasons 2024 2025 2026
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from shared_piping.headers import rotating_headers  # noqa: E402
from shared_piping.team_map import resolve  # noqa: E402

HERE = Path(__file__).resolve().parent
CONFIG = HERE / "config"
STATS_URL = ("https://statsapi.mlb.com/api/v1/stats?stats=season&group=pitching"
             "&season={season}&sportId=1&gameType=R&playerPool=all&limit=1500&offset={offset}")

# season-WHIP tier cutoffs (<= Ace, <= Mid, else Back).
ACE_WHIP, MID_WHIP = 1.10, 1.30
STARTER_MIN_GS = 5   # only tier regular starters


def _ip_to_float(ip) -> float:
    try:
        whole, _, frac = str(ip).partition(".")
        return float(whole or 0) + (float(frac[:1] or 0) / 3.0)
    except (TypeError, ValueError):
        return 0.0


def _iter_splits(seasons):
    for season in seasons:
        offset = 0
        while True:
            url = STATS_URL.format(season=season, offset=offset)
            req = urllib.request.Request(url, headers=rotating_headers())
            try:
                data = json.loads(urllib.request.urlopen(req, timeout=30).read())
            except Exception as exc:  # noqa: BLE001
                print(f"[build_reference] {season}@{offset} failed: {exc}", file=sys.stderr)
                break
            splits = data.get("stats", [{}])[0].get("splits", [])
            if not splits:
                break
            yield from splits
            if len(splits) < 1500:
                break
            offset += 1500


def build(seasons: list[int]) -> tuple[dict, dict]:
    bullpen = defaultdict(lambda: {"R": 0.0, "IP": 0.0})
    starters = defaultdict(lambda: {"H": 0.0, "BB": 0.0, "IP": 0.0, "GS": 0})
    for sp in _iter_splits(seasons):
        st = sp.get("stat", {})
        ip = _ip_to_float(st.get("inningsPitched"))
        if ip <= 0:
            continue
        gs = int(st.get("gamesStarted", 0) or 0)
        if gs == 0:  # reliever -> bullpen aggregate for its team
            team_key = resolve(sp.get("team", {}).get("name", ""))
            if team_key:
                bullpen[team_key]["R"] += float(st.get("runs", 0) or 0)
                bullpen[team_key]["IP"] += ip
        else:        # starter -> accumulate season WHIP inputs
            pid = sp.get("player", {}).get("id")
            if pid is not None:
                s = starters[int(pid)]
                s["H"] += float(st.get("hits", 0) or 0)
                s["BB"] += float(st.get("baseOnBalls", 0) or 0)
                s["IP"] += ip
                s["GS"] += gs

    bullpen_quality = {t: round(9.0 * v["R"] / v["IP"], 3)
                       for t, v in bullpen.items() if v["IP"] > 0}

    tiers = {}
    for pid, s in starters.items():
        if s["GS"] < STARTER_MIN_GS or s["IP"] <= 0:
            continue
        whip = (s["H"] + s["BB"]) / s["IP"]
        tiers[str(pid)] = ("Ace" if whip <= ACE_WHIP else
                           "Mid" if whip <= MID_WHIP else "Back")
    return bullpen_quality, tiers


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Build engine reference tables")
    ap.add_argument("--seasons", type=int, nargs="+", default=[2025])
    args = ap.parse_args(argv)

    bullpen_quality, tiers = build(args.seasons)
    CONFIG.mkdir(parents=True, exist_ok=True)
    (CONFIG / "bullpen_quality.json").write_text(json.dumps(bullpen_quality, indent=2, sort_keys=True))
    (CONFIG / "starter_tiers.json").write_text(json.dumps(tiers, indent=2, sort_keys=True))

    from collections import Counter
    dist = Counter(tiers.values())
    print(f"bullpen_quality: {len(bullpen_quality)} teams "
          f"(best {min(bullpen_quality.values()):.2f} / worst {max(bullpen_quality.values()):.2f} RA9)")
    print(f"starter_tiers: {len(tiers)} starters {dict(dist)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
