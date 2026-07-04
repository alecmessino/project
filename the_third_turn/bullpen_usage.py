#!/usr/bin/env python3
"""V4 — trailing-3-day bullpen workload from statsapi (the fatigue fetch job).

For each game's two teams we pull the club's ACTUAL prior games (not just the ones in
our sample) and sum each reliever's pitches per day, so we can later ask: when a
Mid/Back starter is chased at his TTO cliff, does the facing team score more if the
opposing pen is already gassed?

We store the RAW per-arm/per-day pitch counts (not a hardcoded "exhausted" flag) so the
analysis can sweep the threshold, plus convenient team aggregates. "Top-4 high-leverage
arms" is a Phase-2 refinement (needs season leverage) — this phase captures total-pen
workload, arms used, and yesterday's heavy arms, which need no season data.

    python the_third_turn/bullpen_usage.py --sample   # one team, verify the pipeline
    python the_third_turn/bullpen_usage.py            # build the full cache (~1.3k calls)
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from calibrate_decay import _get  # noqa: E402
from shared_piping.team_map import resolve  # noqa: E402

HERE = Path(__file__).resolve().parent
FEATURES = HERE / "output" / "features_cache.json"
CACHE = HERE / "output" / "bullpen_cache.json"
STATS = "https://statsapi.mlb.com/api/v1"
WINDOW = 3
HEAVY_1D = 30     # pitches yesterday that mark a "worked" arm (analysis sweeps this)
HEAVY_3D = 45     # cumulative pitches over the window that mark a leaned-on arm


def team_id_map() -> dict:
    teams = _get(f"{STATS}/teams?sportId=1").get("teams", [])
    m = {}
    for t in teams:
        k = resolve(t.get("name", "")) or resolve(t.get("teamName", ""))
        if k:
            m[k] = t["id"]
    return m


def _boxscore(pk, memo):
    if pk not in memo:
        memo[pk] = _get(f"{STATS}/game/{pk}/boxscore")
    return memo[pk]


def prior_usage(team_id: int, game_date: str, memo: dict) -> dict:
    """Trailing-WINDOW reliever workload for one team before `game_date`."""
    d = date.fromisoformat(game_date)
    s, e = (d - timedelta(days=WINDOW)).isoformat(), (d - timedelta(days=1)).isoformat()
    sched = _get(f"{STATS}/schedule?sportId=1&teamId={team_id}&startDate={s}&endDate={e}")
    per_arm: dict = {}                 # pid -> {"name":.., "by_day":{date:pitches}}
    games = 0
    for dd in sched.get("dates", []):
        gd = dd.get("date")
        for gm in dd.get("games", []):
            if gm.get("status", {}).get("abstractGameState") != "Final":
                continue
            pk = gm.get("gamePk")
            try:
                bs = _boxscore(pk, memo)
            except Exception:  # noqa: BLE001
                continue
            side = next((sd for sd in ("away", "home")
                         if bs.get("teams", {}).get(sd, {}).get("team", {}).get("id") == team_id), None)
            if side is None:
                continue
            games += 1
            t = bs["teams"][side]
            pitchers = t.get("pitchers", [])
            for i, pid in enumerate(pitchers):
                if i == 0:                       # starter — not a bullpen arm
                    continue
                pl = t.get("players", {}).get(f"ID{pid}", {})
                pitches = (pl.get("stats", {}).get("pitching", {}) or {}).get("numberOfPitches") or 0
                a = per_arm.setdefault(pid, {"name": pl.get("person", {}).get("fullName", str(pid)),
                                             "by_day": {}})
                a["by_day"][gd] = a["by_day"].get(gd, 0) + pitches

    yday = (d - timedelta(days=1)).isoformat()
    pen_3d = sum(sum(a["by_day"].values()) for a in per_arm.values())
    pen_1d = sum(a["by_day"].get(yday, 0) for a in per_arm.values())
    gassed_1d = sum(1 for a in per_arm.values() if a["by_day"].get(yday, 0) >= HEAVY_1D)
    heavy_3d = sum(1 for a in per_arm.values() if sum(a["by_day"].values()) >= HEAVY_3D)
    return {"games": games, "arms_used": len(per_arm), "pen_pitches_3d": pen_3d,
            "pen_pitches_1d": pen_1d, "gassed_1d": gassed_1d, "heavy_3d": heavy_3d,
            "per_arm": {str(p): a for p, a in per_arm.items()}}


def build(sample=False) -> dict:
    feat = json.loads(FEATURES.read_text())
    ids = team_id_map()
    cache = {} if not CACHE.exists() else json.loads(CACHE.read_text())
    memo: dict = {}
    games = list(feat.values())
    if sample:
        games = games[:1]
    done = 0
    for g in games:
        for side, team_key in (("away", g["away"]), ("home", g["home"])):
            tid = ids.get(team_key)
            if tid is None:
                continue
            ck = f"{g['game_pk']}:{side}"
            if ck in cache and not sample:
                continue
            try:
                cache[ck] = {"team": team_key, "date": g["date"], **prior_usage(tid, g["date"], memo)}
            except Exception as e:  # noqa: BLE001
                cache[ck] = {"team": team_key, "date": g["date"], "error": str(e)}
        done += 1
        if done % 20 == 0:
            print(f"  {done}/{len(games)} games…", flush=True)
            CACHE.write_text(json.dumps(cache))
    CACHE.write_text(json.dumps(cache))
    return cache


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", action="store_true")
    args = ap.parse_args(argv)
    cache = build(sample=args.sample)
    if args.sample:
        for k, v in cache.items():
            print(f"\n{k}  team={v.get('team')} date={v.get('date')}")
            print(json.dumps({kk: vv for kk, vv in v.items() if kk != "per_arm"}, indent=2))
            for pid, a in list(v.get("per_arm", {}).items())[:6]:
                print(f"   {a['name']}: {a['by_day']}")
    else:
        ok = [v for v in cache.values() if "error" not in v]
        print(f"built {len(cache)} team-game rows ({len(ok)} ok). "
              f"mean pen_pitches_3d={sum(v['pen_pitches_3d'] for v in ok)/max(len(ok),1):.0f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
