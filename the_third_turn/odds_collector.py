#!/usr/bin/env python3
"""Collect REAL pregame MLB totals from The Odds API (forward-looking).

The free Odds API tier does NOT allow historical retro-fill, but the CURRENT-odds
endpoint (1 credit/call) returns pregame totals for upcoming games across US books.
Run this pregame (e.g. daily via cron) to accumulate real closing-ish lines into
``data/closing_lines.csv``; ``simulate_execution.py --totals-csv`` then computes TRUE
hit rates on games once they complete (and appear in Statcast).

Consensus total = median Over point across books, sanity-filtered to a plausible MLB
range so a stray alt/team-total line can't poison the median. Each event is matched to
its MLB ``game_pk`` via the free stats API schedule. Resumable: existing game_pks are
skipped. Cheap and budget-guarded.

    ODDS_API_KEY=… python the_third_turn/odds_collector.py            # 1 credit
    ODDS_API_KEY=… python the_third_turn/odds_collector.py --max-credits 3
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import statistics
import sys
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from shared_piping.envload import load_env  # noqa: E402
from shared_piping.headers import rotating_headers  # noqa: E402
from shared_piping.mlb_schedule import match_game_pk, pair_date_map  # noqa: E402
from shared_piping.team_map import resolve  # noqa: E402

HERE = Path(__file__).resolve().parent
DEFAULT_OUT = HERE / "data" / "closing_lines.csv"
ODDS_URL = ("https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
            "?apiKey={key}&regions=us&markets=totals&oddsFormat=american")
SCHEDULE_URL = ("https://statsapi.mlb.com/api/v1/schedule?sportId=1"
                "&startDate={start}&endDate={end}")
PLAUSIBLE_MIN, PLAUSIBLE_MAX = 5.5, 14.5   # MLB game totals live here; filter garbage


def _get(url: str) -> tuple[object, dict]:
    req = urllib.request.Request(url, headers=rotating_headers())
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read()), dict(r.headers)


def consensus_total(event: dict, min_books: int) -> tuple[float | None, int]:
    """Median Over point across US books, sanity-filtered; (total, n_books)."""
    pts = []
    for b in event.get("bookmakers", []):
        for m in b.get("markets", []):
            if m.get("key") != "totals":
                continue
            for o in m.get("outcomes", []):
                if o.get("name") == "Over" and o.get("point") is not None:
                    p = float(o["point"])
                    if PLAUSIBLE_MIN <= p <= PLAUSIBLE_MAX:
                        pts.append(p)
    if len(pts) < min_books:
        return None, len(pts)
    return round(statistics.median(pts) * 2) / 2.0, len(pts)


# game_pk matching is date-aware (shared_piping.mlb_schedule) — a team-pair-only
# lookup mislabels consecutive-day series games with an adjacent game's pk.


def load_existing(path: Path) -> set[int]:
    if not path.exists():
        return set()
    with path.open() as fh:
        return {int(r["game_pk"]) for r in csv.DictReader(fh) if r.get("game_pk")}


def main(argv=None) -> int:
    load_env()
    ap = argparse.ArgumentParser(description="Collect real pregame MLB totals (forward)")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--min-books", type=int, default=2)
    ap.add_argument("--max-credits", type=int, default=5, help="hard stop (this uses 1/call)")
    args = ap.parse_args(argv)

    key = os.environ.get("ODDS_API_KEY")
    if not key:
        print("ERROR: ODDS_API_KEY not set (env or .env).", file=sys.stderr)
        return 2

    try:
        events, hdrs = _get(ODDS_URL.format(key=key))
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR fetching odds: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    if not isinstance(events, list):
        print(f"Unexpected response: {str(events)[:200]}", file=sys.stderr)
        return 1

    dates = set()
    parsed = []
    for e in events:
        total, n = consensus_total(e, args.min_books)
        ct = e.get("commence_time", "")
        if total is None or not ct:
            continue
        dates.add(ct[:10])
        parsed.append((e.get("away_team"), e.get("home_team"), total, n, ct))

    sched = pair_date_map(min(dates), max(dates)) if dates else {}
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    existing = load_existing(out_path)

    written = 0
    new_file = not out_path.exists()
    with out_path.open("a", newline="") as fh:
        w = csv.writer(fh)
        if new_file:
            w.writerow(["game_pk", "pregame_total", "n_books", "commence_time", "source"])
        for away, home, total, n, ct in parsed:
            gp = match_game_pk(sched, away or "", home or "", ct)
            if gp is None or gp in existing:
                continue
            w.writerow([gp, total, n, ct, "theoddsapi"])
            existing.add(gp)
            written += 1

    used = hdrs.get("x-requests-used", "?")
    remaining = hdrs.get("x-requests-remaining", "?")
    print(f"Collected {written} new real line(s) from {len(parsed)} upcoming game(s) "
          f"→ {out_path}")
    print(f"Odds API credits: used={used}, remaining={remaining}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
