#!/usr/bin/env python3
"""Harvest LIVE total-line trajectories from Odds Papi historical odds.

The decisive dataset for the market-relative trigger: per game, the full path of
the balanced main total (Pinnacle) from first pitch to final. Feeds
``calibrate_decay.py`` (empirical E[live line | situation]) and the first honest
backtest against real live lines.

Budget-capped like the closing-line fetcher (free plan = 250 req/month total).
One request per game; resumable (games already in the output are skipped).

    ODDS_PAPI_KEY=… python the_third_turn/harvest_trajectories.py \
        --start 2026-06-15 --end 2026-06-30 --max-requests 60
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from odds_papi_history import Budget, _api, _parse_ts, load_fixtures, load_markets_map  # noqa: E402
from shared_piping.envload import load_env  # noqa: E402
from shared_piping.mlb_schedule import match_game_pk, pair_date_map  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / "data" / "trajectories.jsonl"


def extract_trajectory(hist: dict, mmap: dict[int, dict]) -> list[dict]:
    """All (ts, line) points where a handicap's Over/Under were both freshly priced.

    For each snapshot moment we take the handicap whose two sides are most balanced
    (the main line). Implementation: bucket snapshots to the minute, then per bucket
    pick the balanced active handicap.
    """
    books = (hist.get("data", hist) or {}).get("bookmakers", {})
    per_min: dict[str, dict[float, dict]] = {}
    for bv in books.values():
        for mid, mkt in bv.get("markets", {}).items():
            info = mmap.get(int(mid))
            if not info:
                continue
            for oid, ov in mkt.get("outcomes", {}).items():
                side = "o" if int(oid) == info["over"] else (
                    "u" if int(oid) == info["under"] else None)
                if side is None:
                    continue
                for snaps in ov.get("players", {}).values():
                    for s in snaps:
                        ts, price = s.get("createdAt"), s.get("price")
                        if not ts or not price:
                            continue
                        minute = ts[:16]
                        per_min.setdefault(minute, {}).setdefault(info["hc"], {})[side] = float(price)
    points = []
    for minute in sorted(per_min):
        best = None
        for hc, pr in per_min[minute].items():
            if "o" in pr and "u" in pr:
                imb = abs(1.0 / pr["o"] - 1.0 / pr["u"])
                if best is None or imb < best[0]:
                    best = (imb, hc, pr["o"], pr["u"])
        if best:
            points.append({"ts": minute, "line": best[1],
                           "over_dec": best[2], "under_dec": best[3]})
    return points


def existing_game_pks(path: Path) -> set[int]:
    if not path.exists():
        return set()
    out = set()
    for line in path.read_text().splitlines():
        try:
            out.add(int(json.loads(line)["game_pk"]))
        except (ValueError, KeyError):
            continue
    return out


def main(argv=None) -> int:
    load_env()
    ap = argparse.ArgumentParser(description="Harvest live total-line trajectories")
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--max-requests", type=int, default=60)
    ap.add_argument("--books", default="pinnacle")
    args = ap.parse_args(argv)

    key = os.environ.get("ODDS_PAPI_KEY")
    if not key:
        print("ERROR: ODDS_PAPI_KEY not set.", file=sys.stderr)
        return 2

    budget = Budget(args.max_requests)
    mmap = load_markets_map(key, budget)
    fixtures = load_fixtures(key, budget)
    sched = pair_date_map(args.start, args.end)
    done = existing_game_pks(OUT)

    targets = [f for f in fixtures
               if args.start <= str(f.get("startTime", ""))[:10] <= args.end
               and str(f.get("statusName", "")).lower() == "finished"]
    print(f"{len(targets)} finished fixtures in range; {len(done)} already harvested")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with OUT.open("a") as fh:
        for f in targets:
            gp = match_game_pk(sched, f.get("participant1Name", ""),
                               f.get("participant2Name", ""), f.get("startTime", ""))
            if gp is None or gp in done:
                continue
            if budget.used >= args.max_requests:
                print("[budget] cap reached — stopping.")
                break
            try:
                hist = _api(f"/v4/historical-odds?fixtureId={f['fixtureId']}"
                            f"&bookmakers={args.books}", key, budget)
            except Exception as exc:  # noqa: BLE001
                print(f"  {f['fixtureId']} failed: {exc}", file=sys.stderr)
                continue
            points = extract_trajectory(hist, mmap)
            if len(points) < 10:
                continue
            fh.write(json.dumps({
                "game_pk": gp, "fixture_id": f["fixtureId"],
                "start_time": f["startTime"],
                "team1": f.get("participant1Name"), "team2": f.get("participant2Name"),
                "points": points}) + "\n")
            fh.flush()
            done.add(gp)
            written += 1
            print(f"  ✓ {gp} {f.get('participant2Name','?')} @ {f.get('participant1Name','?')} "
                  f"— {len(points)} line points")
    print(f"Harvested {written} trajectories → {OUT} "
          f"({budget.used}/{args.max_requests} requests used)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
