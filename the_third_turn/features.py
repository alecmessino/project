#!/usr/bin/env python3
"""One-pass game feature builder — the shared substrate for every research vector.

Walks each game's play-by-play + line trajectory ONCE and emits a rich, cached record
so the vector backtests (alt-line skew, early-runs anchoring, team totals, bullpen
fatigue) are each a thin slice-and-grade on top instead of re-deriving state five times.

Per game it captures:
  * pregame close / final game total / per-team finals
  * the live line+price series (line, over_dec, under_dec) straight from the trajectory
  * the live total at the end of each inning 1..8
  * runs per half-inning, and 1st-inning runs tagged by CAUSE (hit / walk-hbp / error)
  * per side: starter tier, avg pitch velocity by time-through-order (TTO1/2/3) and the
    TTO1→TTO3 velocity drop, runs allowed while the starter was on, and exit inning

    python the_third_turn/features.py            # build/refresh the cache
    python the_third_turn/features.py --sample   # print one record + sanity stats
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from calibrate_decay import FEED, _get, line_lookup, state_timeline  # noqa: E402
from config import Constraints, EngineSettings  # noqa: E402
from investigate_line_edge import closing_line  # noqa: E402
from shared_piping.team_map import resolve  # noqa: E402

HERE = Path(__file__).resolve().parent
TRAJ = HERE / "data" / "trajectories.jsonl"
CACHE = HERE / "output" / "features_cache.json"

HIT = {"single", "double", "triple", "home_run"}
FREE = {"walk", "hit_by_pitch"}
ERR = {"field_error"}


def extract(feed, points, start_time, tiers) -> dict:
    gd, ld = feed.get("gameData", {}), feed.get("liveData", {})
    away = resolve(gd.get("teams", {}).get("away", {}).get("name", "")) or "?"
    home = resolve(gd.get("teams", {}).get("home", {}).get("name", "")) or "?"
    box = ld.get("boxscore", {}).get("teams", {})
    starter = {s: (box.get(s, {}).get("pitchers", []) or [None])[0] for s in ("away", "home")}

    fn = line_lookup(points)
    closing = closing_line(points, start_time)
    _tl, final = state_timeline(feed)

    faced: dict[tuple, int] = defaultdict(int)
    vel: dict[tuple, list] = defaultdict(lambda: [0.0, 0])   # (side, tto) -> [sum, n]
    runs_half: dict[tuple, int] = defaultdict(int)
    cause1 = {"hit": 0, "walk": 0, "error": 0, "other": 0}
    runs_vs_starter = {"away": 0, "home": 0}
    exit_inning = {"away": None, "home": None}
    line_by_inn: dict[int, float] = {}
    prev = 0
    last_aw = last_hm = 0

    for play in ld.get("plays", {}).get("allPlays", []):
        about, match, res = play.get("about", {}), play.get("matchup", {}), play.get("result", {})
        inning = int(about.get("inning") or 0)
        is_top = bool(about.get("isTopInning"))
        half = "top" if is_top else "bottom"
        pside = "home" if is_top else "away"          # the pitching (defending) side
        line = fn(about.get("startTime") or "")
        if line is not None and inning >= 2 and inning not in line_by_inn:
            line_by_inn[inning - 1] = line             # live total at the END of (inning-1)

        pitcher_id = (match.get("pitcher") or {}).get("id")
        batter_id = (match.get("batter") or {}).get("id")
        starter_on = pitcher_id == starter[pside]
        if not starter_on and pitcher_id and exit_inning[pside] is None:
            exit_inning[pside] = inning

        if res.get("type") == "atBat" and match.get("batter"):
            faced[(pitcher_id, batter_id)] += 1
            tto = min(faced[(pitcher_id, batter_id)], 3)
            if starter_on:
                for e in play.get("playEvents", []):
                    sp = (e.get("pitchData") or {}).get("startSpeed")
                    if sp:
                        vel[(pside, tto)][0] += sp
                        vel[(pside, tto)][1] += 1

        aw, hm = res.get("awayScore"), res.get("homeScore")
        if aw is not None and hm is not None:
            last_aw, last_hm = aw, hm
            d = (aw + hm) - prev
            prev = aw + hm
            if d > 0:
                runs_half[(inning, half)] += d
                if starter_on:
                    runs_vs_starter[pside] += d
                if inning == 1:
                    et = res.get("eventType", "")
                    b = ("hit" if et in HIT else "walk" if et in FREE
                         else "error" if et in ERR else "other")
                    cause1[b] += d

    def side_rec(s):
        vt = {t: (vel[(s, t)][0] / vel[(s, t)][1] if vel[(s, t)][1] else None) for t in (1, 2, 3)}
        drop = (vt[1] - vt[3]) if (vt[1] and vt[3]) else None
        return {"tier": tiers.get(str(starter[s]), "Unknown"), "starter_id": starter[s],
                "vel_tto": vt, "vel_drop_13": round(drop, 2) if drop is not None else None,
                "runs_allowed": runs_vs_starter[s], "exit_inning": exit_inning[s]}

    r1 = runs_half.get((1, "top"), 0) + runs_half.get((1, "bottom"), 0)
    return {
        "closing": closing, "final": final, "final_away": last_aw, "final_home": last_hm,
        "away": away, "home": home,
        "line_by_inn": {str(k): v for k, v in line_by_inn.items()},
        "first_inning_runs": r1, "cause1": cause1,
        "runs_half": {f"{i}:{h}": n for (i, h), n in runs_half.items()},
        # the batting side faces the OTHER side's starter:
        "away_faces": side_rec("home"), "home_faces": side_rec("away"),
        "points": points,          # keep the price/line series for the skew vector
    }


def build(refresh=False) -> dict:
    games = [json.loads(l) for l in TRAJ.read_text().splitlines() if l.strip()]
    tiers = EngineSettings().load_starter_tiers()
    cache = {} if refresh or not CACHE.exists() else json.loads(CACHE.read_text())
    for g in games:
        key = str(g["game_pk"])
        if key in cache:
            continue
        try:
            feed = _get(FEED.format(pk=g["game_pk"]))
        except Exception:  # noqa: BLE001
            continue
        rec = extract(feed, g["points"], g.get("start_time", ""), tiers)
        rec["game_pk"] = g["game_pk"]
        rec["date"] = (g.get("start_time", "") or "")[:10]
        cache[key] = rec
    CACHE.write_text(json.dumps(cache))
    return cache


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--sample", action="store_true")
    args = ap.parse_args(argv)
    cache = build(refresh=args.refresh)
    recs = [r for r in cache.values() if r.get("final") is not None]
    print(f"built {len(cache)} game records ({len(recs)} with finals)")
    if args.sample and recs:
        r = recs[0]
        print("\nSAMPLE record (trimmed):")
        show = {k: v for k, v in r.items() if k != "points"}
        print(json.dumps(show, indent=2)[:1400])
        fr = [r["first_inning_runs"] for r in recs]
        drops = [r["away_faces"]["vel_drop_13"] for r in recs if r["away_faces"]["vel_drop_13"] is not None]
        drops += [r["home_faces"]["vel_drop_13"] for r in recs if r["home_faces"]["vel_drop_13"] is not None]
        big1st = sum(1 for x in fr if x >= 2)
        print(f"\nSANITY:")
        print(f"  1st-inning runs: mean {statistics.mean(fr):.2f}, "
              f"games with 2+ = {big1st}/{len(fr)}")
        print(f"  starter velocity TTO1->TTO3 drop (mph): n={len(drops)}, "
              f"mean {statistics.mean(drops):+.2f}, "
              f"median {statistics.median(drops):+.2f}" if drops else "  no velocity data")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
