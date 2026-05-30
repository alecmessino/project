#!/usr/bin/env python3
"""Pull REAL historical in-play odds snapshots into the batch-backtest `marks` format.

This is the legitimate way to populate live lines for past games: The Odds API's
*historical* endpoint (`/v4/historical/sports/{sport}/odds`) returns the odds
snapshot at (or just before) a given timestamp. We hit it once per cadence mark
and emit the `lines` block that `tests/data/*_batch.json` expects.

REQUIREMENTS / HONEST CAVEATS
-----------------------------
- Paid plan only. Historical access is a paid feature of The Odds API; each
  snapshot costs ~10 credits per region per market. Budget accordingly.
- In-play period markets (totals_h1, totals_q*) only exist in the archive from
  2023-05-03 onward; coverage for a specific live moment can be sparse.
- Game-minute → wall-clock is NOT linear (timeouts, breaks, reviews). We map it
  with a tunable `--stretch` factor (real minutes per game minute, default 2.4);
  treat the resulting lines as the nearest archived snapshot, not exact.
- Scores per mark are NOT provided by the odds endpoint. Fill `away_score` /
  `home_score` from the box score (or pair with src/mrbet/espn.py) before
  running the backtest — they are emitted as null here.

The key is read from the environment only (ODDS_API_KEY / THE_ODDS_API_KEY via
.env or GitHub Secrets). It is never printed.

USAGE
-----
    python scripts/fetch_historical_odds.py \
        --event-id sas_okc_2026-05-18 \
        --commence 2026-05-19T01:30:00Z \
        --markets totals,totals_h1,team_totals \
        --book bovada > /tmp/g1_marks.json

Then paste the printed `marks` array into the matching game block in the batch
file and remove that game's `_status: incomplete` flag.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys

import requests

# Reuse the package's env loader + constants so behaviour matches the live path.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from mrbet.envload import load_env, has_odds_key  # noqa: E402
from mrbet.cadence import timeout_marks            # noqa: E402

ODDS_BASE = "https://api.the-odds-api.com/v4"
SPORT = "basketball_nba"


def _snapshot_at(api_key: str, when: dt.datetime, markets: str, region: str) -> dict:
    """One historical snapshot. Returns the parsed JSON (or {} on failure)."""
    url = f"{ODDS_BASE}/historical/sports/{SPORT}/odds"
    params = {
        "apiKey": api_key,                       # from env only — never logged
        "regions": region,
        "markets": markets,
        "oddsFormat": "american",
        "date": when.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    try:
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as exc:
        # Never echo params (they carry the key); report status only.
        print(f"[warn] snapshot at {params['date']} failed: {exc}", file=sys.stderr)
        return {}


def _lines_from_snapshot(snap: dict, book: str) -> dict:
    """Flatten a snapshot's bookmaker markets into our `lines` dict."""
    data = snap.get("data") or {}
    events = data if isinstance(data, list) else data.get("data", [])
    out: dict = {}
    for ev in events or []:
        for bk in ev.get("bookmakers", []):
            if bk.get("key") != book:
                continue
            for mk in bk.get("markets", []):
                key = mk.get("key")
                outcomes = mk.get("outcomes", [])
                over = next((o for o in outcomes if o.get("name") == "Over"), None)
                if not over:
                    continue
                under = next((o for o in outcomes if o.get("name") == "Under"), None)
                json_key = {"totals": "game_total", "totals_h1": "total_h1"}.get(key, key)
                out[json_key] = {
                    "line": over.get("point"),
                    "over": int(over.get("price", -110)),
                    "under": int(under.get("price", -110)) if under else -110,
                }
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--event-id", required=True, help="batch event_id (label only)")
    ap.add_argument("--commence", required=True,
                    help="game tip-off in UTC ISO8601, e.g. 2026-05-19T01:30:00Z")
    ap.add_argument("--markets", default="totals,totals_h1,team_totals",
                    help="comma-separated Odds API market keys")
    ap.add_argument("--book", default="bovada", help="bookmaker key to extract")
    ap.add_argument("--region", default="us")
    ap.add_argument("--stretch", type=float, default=2.4,
                    help="real minutes per game minute (stoppage factor)")
    args = ap.parse_args()

    load_env()
    if not has_odds_key():
        print("ERROR: no ODDS_API_KEY in environment (.env or GitHub Secrets). "
              "Historical odds require a paid plan.", file=sys.stderr)
        return 2
    api_key = os.environ["ODDS_API_KEY"]

    tip = dt.datetime.strptime(args.commence, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=dt.timezone.utc)

    marks = []
    for mark in timeout_marks():
        when = tip + dt.timedelta(minutes=mark * args.stretch)
        lines = _lines_from_snapshot(
            _snapshot_at(api_key, when, args.markets, args.region), args.book)
        if not lines:
            print(f"[warn] no {args.book} lines at game-min {mark} "
                  f"({when:%H:%M}Z) — skipping", file=sys.stderr)
            continue
        marks.append({
            "minutes_elapsed": mark,
            "away_score": None, "home_score": None,   # fill from box score
            "lines": lines,
        })

    json.dump({"event_id": args.event_id, "marks": marks}, sys.stdout, indent=2)
    print(file=sys.stdout)
    print(f"[ok] {len(marks)} marks fetched for {args.event_id}. "
          "Fill in away_score/home_score from the box score, then paste `marks` "
          "into the batch file and drop its _status flag.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
