#!/usr/bin/env python3
"""Fetch REAL historical MLB closing totals from Odds Papi (https://oddspapi.io).

Unlike The Odds API free tier (no history), Odds Papi's free plan HAS historical odds
(since Jan 2026). Flow (fixture-based, strictly budget-capped — free plan = 250
requests total, 5s cooldown):

  1. cache /v4/markets  → marketId -> (handicap, Over id, Under id) for baseball totals
  2. cache /v4/fixtures?tournamentId=109 → fixtureId ↔ (team1, team2, startTime)
  3. per game: /v4/historical-odds?fixtureId=…&bookmakers=pinnacle,fanduel,draftkings
     → closing total = handicap of the BALANCED main line at the last snapshot BEFORE
       first pitch, median across the ≤3 books.

Each game is matched to its MLB game_pk via the free stats-API schedule (team pair +
date) and appended to data/closing_lines.csv (source=oddspapi), resumable. Feed the
result to `simulate_execution.py --totals-csv … --real-only` for TRUE hit rates.

    ODDS_PAPI_KEY=… python the_third_turn/odds_papi_history.py --start 2026-06-20 --end 2026-06-27
"""

from __future__ import annotations

import argparse
import csv
import gzip
import http.client
import json
import os
import statistics
import sys
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from shared_piping.envload import load_env  # noqa: E402
from shared_piping.team_map import resolve  # noqa: E402

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
OUT = DATA / "closing_lines.csv"
BASE = "https://api.oddspapi.io"
SPORT_BASEBALL, TOURNAMENT_MLB = 13, 109
MAIN_PERIODS = ("result", "fulltime")   # full-game total
COOLDOWN = 5.1                          # plan rate limit is 5000ms


class Budget:
    """Counts API requests and hard-stops at the cap (protects the 250 free quota)."""

    def __init__(self, cap: int):
        self.cap, self.used = cap, 0

    def spend(self) -> None:
        if self.used >= self.cap:
            raise RuntimeError(f"request budget ({self.cap}) exhausted")
        self.used += 1


def _api(path: str, key: str, budget: Budget):
    """GET + JSON. Requests gzip (historical payloads are 10-18MB raw) and retries once
    on a truncated read; counts one request against the budget regardless of retries."""
    budget.spend()
    sep = "&" if "?" in path else "?"
    url = f"{BASE}{path}{sep}apiKey={key}"
    headers = {"User-Agent": "the-third-turn/1.0", "Accept-Encoding": "gzip"}
    last = None
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=90) as r:
                raw = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
            time.sleep(COOLDOWN)
            return json.loads(raw)
        except (http.client.IncompleteRead, urllib.error.URLError, TimeoutError) as exc:
            last = exc
            time.sleep(COOLDOWN)
    raise last


# --------------------------------------------------------------------------- #
# Reference caches (fetched once, reused)                                      #
# --------------------------------------------------------------------------- #
def load_markets_map(key: str, budget: Budget, refresh: bool = False) -> dict[int, dict]:
    cache = DATA / "opapi_markets.json"
    if cache.exists() and not refresh:
        return {int(k): v for k, v in json.loads(cache.read_text()).items()}
    raw = _api("/v4/markets", key, budget)
    items = raw if isinstance(raw, list) else raw.get("data", [])
    out = {}
    for m in items:
        if (m.get("sportId") == SPORT_BASEBALL and m.get("marketType") == "totals"
                and m.get("period") in MAIN_PERIODS):
            outs = {o["outcomeName"].lower(): o["outcomeId"] for o in m.get("outcomes", [])}
            if "over" in outs and "under" in outs:
                out[int(m["marketId"])] = {"hc": float(m["handicap"]),
                                           "over": outs["over"], "under": outs["under"]}
    DATA.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(out))
    return out


def load_fixtures(key: str, budget: Budget, refresh: bool = False) -> list[dict]:
    cache = DATA / "opapi_fixtures.json"
    if cache.exists() and not refresh:
        return json.loads(cache.read_text())
    raw = _api(f"/v4/fixtures?tournamentId={TOURNAMENT_MLB}", key, budget)
    items = raw if isinstance(raw, list) else raw.get("data", [])
    DATA.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(items))
    return items


# --------------------------------------------------------------------------- #
# Closing-line extraction (pure — unit-tested)                                 #
# --------------------------------------------------------------------------- #
def _parse_ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _snaps(outcome: dict) -> list:
    for v in (outcome or {}).get("players", {}).values():
        if isinstance(v, list):
            return sorted(v, key=lambda s: s.get("createdAt", ""))
    return []


def _last_pre(snaps: list, start: datetime):
    pre = [s for s in snaps if s.get("createdAt") and s.get("price")
           and _parse_ts(s["createdAt"]) <= start]
    return pre[-1] if pre else None


def closing_total_for_book(markets: dict, mmap: dict[int, dict], start: datetime):
    """Handicap of the balanced main total at the last pre-first-pitch snapshot."""
    best = None
    for mid, mkt in markets.items():
        info = mmap.get(int(mid))
        if not info:
            continue
        outs = mkt.get("outcomes", {})
        o = _last_pre(_snaps(outs.get(str(info["over"]))), start)
        u = _last_pre(_snaps(outs.get(str(info["under"]))), start)
        if not o or not u:
            continue
        try:
            imbalance = abs(1.0 / float(o["price"]) - 1.0 / float(u["price"]))
        except (ZeroDivisionError, ValueError, TypeError):
            continue
        if best is None or imbalance < best[0]:
            best = (imbalance, info["hc"])
    return best[1] if best else None


def closing_total(hist: dict, mmap: dict[int, dict], start: datetime):
    """Median closing total across the returned books."""
    books = (hist.get("data", hist) or {}).get("bookmakers", {})
    lines = []
    for bv in books.values():
        line = closing_total_for_book(bv.get("markets", {}), mmap, start)
        if line is not None:
            lines.append(line)
    if not lines:
        return None, 0
    return round(statistics.median(lines) * 2) / 2.0, len(lines)


# --------------------------------------------------------------------------- #
# game_pk matching + orchestration                                            #
# --------------------------------------------------------------------------- #
# game_pk matching is date-aware via shared_piping.mlb_schedule: the ET schedule
# date is derived from the UTC commence time (a 01:41Z start is the PREVIOUS ET
# night's game), so consecutive-day series games can't be mislabeled.
from shared_piping.mlb_schedule import match_game_pk, pair_date_map  # noqa: E402


def load_existing(path: Path) -> set[int]:
    if not path.exists():
        return set()
    with path.open() as fh:
        return {int(r["game_pk"]) for r in csv.DictReader(fh) if r.get("game_pk")}


def main(argv=None) -> int:
    load_env()
    ap = argparse.ArgumentParser(description="Odds Papi historical MLB closing totals")
    ap.add_argument("--start", required=True, help="YYYY-MM-DD (>= 2026-01-01)")
    ap.add_argument("--end", required=True, help="YYYY-MM-DD")
    ap.add_argument("--max-requests", type=int, default=60, help="hard cap on API calls")
    ap.add_argument("--books", default="pinnacle",
                    help="comma-separated bookmaker slugs, max 3 (default: pinnacle, sharpest)")
    ap.add_argument("--refresh", action="store_true", help="refresh markets/fixtures caches")
    args = ap.parse_args(argv)

    key = os.environ.get("ODDS_PAPI_KEY")
    if not key:
        print("ERROR: ODDS_PAPI_KEY not set (env or .env).", file=sys.stderr)
        return 2

    budget = Budget(args.max_requests)
    try:
        mmap = load_markets_map(key, budget, args.refresh)
        fixtures = load_fixtures(key, budget, args.refresh)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR loading reference data: {exc}", file=sys.stderr)
        return 1
    print(f"reference: {len(mmap)} baseball totals markets, {len(fixtures)} fixtures cached")

    sched = pair_date_map(args.start, args.end)
    existing = load_existing(OUT)
    in_range = [f for f in fixtures
                if args.start <= str(f.get("startTime", ""))[:10] <= args.end]
    print(f"{len(in_range)} MLB fixtures in {args.start}..{args.end}; "
          f"budget {budget.used}/{args.max_requests} used so far")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    new_file = not OUT.exists()
    written = 0
    with OUT.open("a", newline="") as fh:
        w = csv.writer(fh)
        if new_file:
            w.writerow(["game_pk", "pregame_total", "n_books", "commence_time", "source"])
        for f in in_range:
            gp = match_game_pk(sched, f.get("participant1Name", ""),
                               f.get("participant2Name", ""), f.get("startTime", ""))
            if gp is None or gp in existing:
                continue
            if budget.used >= args.max_requests:
                print("[budget] request cap reached — stopping.")
                break
            try:
                hist = _api(f"/v4/historical-odds?fixtureId={f['fixtureId']}"
                            f"&bookmakers={args.books}", key, budget)
            except Exception as exc:  # noqa: BLE001
                print(f"  {f['fixtureId']} failed: {exc}", file=sys.stderr)
                continue
            total, n = closing_total(hist, mmap, _parse_ts(f["startTime"]))
            if total is None:
                continue
            w.writerow([gp, total, n, f["startTime"], "oddspapi"])
            fh.flush()
            existing.add(gp)
            written += 1

    print(f"Wrote {written} real closing line(s) → {OUT}")
    print(f"Odds Papi requests used this run: {budget.used}/{args.max_requests} "
          f"(free plan = 250 total).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
