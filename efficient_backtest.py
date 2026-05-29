"""Credit-efficient historical NBA totals backtest against The Odds API.

Strategy for conserving the 500-credit/month free budget:
  * query a SINGLE event's odds endpoint, never the whole league-day;
  * sample only 9 game-clock stoppages (Q1-Q3 timeouts + quarter breaks);
  * map each game-clock minute to a real-world wall-clock timestamp with a
    ~2.2x broadcast-stretch multiplier from tip-off;
  * read `x-requests-remaining` after every call and abort before overspending;
  * detect the free-plan paywall (HTTP 401 HISTORICAL_UNAVAILABLE...) up front
    so a probe costs 0 credits.

Historical odds cost 10 credits per market x region per snapshot, so a full
9-mark single-market single-region run is ~90 credits. The script prints the
projected cost and refuses to start if the budget can't cover it.

Usage:
    python efficient_backtest.py --event-id <id> --tip-off 2026-05-31T01:00:00Z \
        [--opening 212.5] [--market totals] [--region us] [--budget 200]

The key is read from THE_ODDS_API_KEY (see .env, which is gitignored).
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
from datetime import datetime, timedelta, timezone

import requests

BASE = "https://api.the-odds-api.com/v4"
SPORT = "basketball_nba"
OUT = pathlib.Path("backtest_results.json")

# Game-clock minutes elapsed at the 9 Q1-Q3 stoppages.
GAME_CLOCK_MARKS = [
    ("Q1 timeout 1", 6), ("Q1 timeout 2", 9), ("End of Q1", 12),
    ("Q2 timeout 1", 18), ("Q2 timeout 2", 21), ("Halftime", 24),
    ("Q3 timeout 1", 30), ("Q3 timeout 2", 33), ("End of Q3", 36),
]
BROADCAST_STRETCH = 2.2   # real wall-clock minutes per game-clock minute from tip
CREDITS_PER_CALL = 10     # historical: 10 x markets x regions (we use 1 x 1)


def load_key() -> str:
    key = os.environ.get("THE_ODDS_API_KEY")
    if not key:
        env = pathlib.Path(".env")
        if env.exists():
            for line in env.read_text().splitlines():
                if line.strip().startswith("THE_ODDS_API_KEY="):
                    key = line.split("=", 1)[1].strip()
                    break
    if not key:
        sys.exit("THE_ODDS_API_KEY not set (env or .env).")
    return key


def mark_timestamps(tip_off_iso: str) -> list[tuple[str, int, str]]:
    """(label, game_minute, real_wall_clock_ISO) for each of the 9 marks."""
    tip = datetime.fromisoformat(tip_off_iso.replace("Z", "+00:00")).astimezone(timezone.utc)
    out = []
    for label, gmin in GAME_CLOCK_MARKS:
        real = tip + timedelta(minutes=gmin * BROADCAST_STRETCH)
        out.append((label, gmin, real.strftime("%Y-%m-%dT%H:%M:%SZ")))
    return out


def fetch_snapshot(key: str, event_id: str, ts: str, market: str, region: str):
    """Return (parsed_or_None, credits_remaining, error_or_None)."""
    url = f"{BASE}/historical/sports/{SPORT}/events/{event_id}/odds"
    params = {"apiKey": key, "date": ts, "regions": region,
              "markets": market, "oddsFormat": "american"}
    try:
        r = requests.get(url, params=params, timeout=25)
    except requests.RequestException as e:
        return None, None, f"network: {e}"
    remaining = r.headers.get("x-requests-remaining")
    remaining = int(remaining) if remaining and remaining.isdigit() else None
    if r.status_code == 401:
        try:
            return None, remaining, r.json().get("error_code", "unauthorized")
        except ValueError:
            return None, remaining, "unauthorized"
    if r.status_code != 200:
        return None, remaining, f"http {r.status_code}"
    return r.json(), remaining, None


def extract_total(payload: dict, market: str) -> tuple[float | None, int | None, str | None]:
    """Pull the totals line/over-odds from the first book that quotes it."""
    data = payload.get("data", payload)
    for bk in data.get("bookmakers", []):
        for mkt in bk.get("markets", []):
            if mkt.get("key") != market:
                continue
            over = next((o for o in mkt.get("outcomes", []) if o.get("name") == "Over"), None)
            if over and over.get("point") is not None:
                return float(over["point"]), over.get("price"), bk.get("key")
    return None, None, None


def run(event_id, tip_off, opening, market, region, budget, key):
    marks = mark_timestamps(tip_off)
    projected = len(marks) * CREDITS_PER_CALL
    print(f"event {event_id} · tip {tip_off} · {len(marks)} marks · "
          f"projected cost ~{projected} credits (market={market}, region={region})")

    # Probe once (cheap on 401) before committing the budget.
    _, remaining, err = fetch_snapshot(key, event_id, marks[0][2], market, region)
    if err in ("HISTORICAL_UNAVAILABLE_ON_FREE_USAGE_PLAN", "unauthorized"):
        result = {"event_id": event_id, "status": "blocked", "error": err,
                  "note": "Historical odds require a PAID Odds API plan. "
                          "Free tier blocks /v4/historical. Upgrade, or use free "
                          "forward-capture (timeout cadence) for real lines.",
                  "credits_remaining": remaining,
                  "planned_marks": [{"label": l, "game_minute": g, "timestamp": t}
                                    for l, g, t in marks]}
        OUT.write_text(json.dumps(result, indent=2))
        print(f"\n⚠ historical unavailable on this plan ({err}); 0 credits charged.")
        print(f"  wrote {OUT} with the planned cadence (ready for a paid key).")
        return result
    if remaining is not None and remaining < projected:
        sys.exit(f"insufficient credits: {remaining} < projected {projected}. Aborting.")

    rows, open_line = [], opening
    for label, gmin, ts in marks:
        payload, remaining, err = fetch_snapshot(key, event_id, ts, market, region)
        if err:
            rows.append({"label": label, "game_minute": gmin, "timestamp": ts, "error": err})
            continue
        line, price, book = extract_total(payload, market)
        if open_line is None and line is not None:
            open_line = line  # first observed snapshot anchors the "opening" line
        rows.append({
            "label": label, "game_minute": gmin, "timestamp": ts,
            "line": line, "over_price": price, "book": book,
            "shift_vs_open": (round(line - open_line, 1) if line is not None and open_line else None),
            "credits_remaining": remaining,
        })
        if remaining is not None and remaining < CREDITS_PER_CALL:
            print(f"  stopping early — credits low ({remaining}).")
            break

    result = {"event_id": event_id, "tip_off": tip_off, "market": market,
              "region": region, "opening_line": open_line, "status": "ok",
              "credits_remaining": remaining, "samples": rows}
    OUT.write_text(json.dumps(result, indent=2))
    print(f"\nwrote {OUT}: opening {open_line}, {len(rows)} marks sampled.")
    for r in rows:
        if "line" in r:
            print(f"  {r['label']:14s} m{r['game_minute']:>2}  {r['timestamp']}  "
                  f"line={r['line']}  shift={r['shift_vs_open']}")
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--event-id", required=True)
    ap.add_argument("--tip-off", required=True, help="ISO UTC, e.g. 2026-05-31T01:00:00Z")
    ap.add_argument("--opening", type=float, default=None, help="Opening total (else first snapshot)")
    ap.add_argument("--market", default="totals")
    ap.add_argument("--region", default="us")
    ap.add_argument("--budget", type=int, default=200, help="Max credits willing to spend")
    args = ap.parse_args()
    run(args.event_id, args.tip_off, args.opening, args.market, args.region,
        args.budget, load_key())


if __name__ == "__main__":
    main()
