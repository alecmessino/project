"""Discover a whole league's Bovada slate and write docs/board.json.

No per-game YAML needed — this enumerates every game Bovada lists for the league
and extracts the pre-game Total / Spread / Moneyline so the dashboard can show
tonight's full board the moment it loads (before any tip-off). Re-run on a cron
or before tip:

    python scripts/board_update.py --league wnba
    python scripts/board_update.py --league nba
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mrbet.bovada_feed import (   # noqa: E402
    BovadaProvider, _american, _handicap, board_events, event_from_bovada,
)

OUT = ROOT / "docs" / "board.json"


def _game_markets(raw: dict):
    """Pull pre-game Total / Spread / Moneyline (period G) from a raw event."""
    total = spread = None
    ml_home = ml_away = None
    home_name = next((c.get("name", "") for c in raw.get("competitors", []) if c.get("home")), "")
    for dg in raw.get("displayGroups", []):
        for m in dg.get("markets", []):
            if (m.get("period", {}) or {}).get("abbreviation") != "G":
                continue
            key = m.get("key")
            outs = m.get("outcomes", [])
            if key == "2W-OU":
                over = next((o for o in outs if o.get("description", "").lower() == "over"), None)
                if over:
                    total = _handicap(over.get("price", {}))
            elif key == "2W-HCAP":
                ho = next((o for o in outs
                           if home_name.split()[-1].lower() in o.get("description", "").lower()), None)
                if ho:
                    spread = _handicap(ho.get("price", {}))
            elif key == "2W-12":
                for o in outs:
                    is_home = home_name.split()[-1].lower() in o.get("description", "").lower()
                    price = _american(o.get("price", {}))
                    if is_home:
                        ml_home = price
                    else:
                        ml_away = price
    return total, spread, ml_home, ml_away


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Write docs/board.json for a league's slate")
    ap.add_argument("--league", default="wnba")
    args = ap.parse_args(argv)

    events = board_events(args.league)
    games = []
    for raw in events:
        ev = event_from_bovada(raw)
        p = BovadaProvider(ev, league=args.league, max_polls=1)
        stage = p._classify_stage(raw)
        total, spread, ml_home, ml_away = _game_markets(raw)
        tip_ms = raw.get("startTime")
        tip = (time.strftime("%-I:%M %p", time.localtime(tip_ms / 1000))
               if isinstance(tip_ms, (int, float)) else "—")
        games.append({
            "matchup": f"{ev.away} @ {ev.home}",
            "away": ev.away, "home": ev.home,
            "away_key": ev.away_key, "home_key": ev.home_key,
            "tip": tip, "stage": stage,
            "total": total,
            "spread": (f"{ev.home_key} {spread:+g}" if spread is not None else None),
            "ml_away": ml_away, "ml_home": ml_home,
        })

    payload = {
        "league": args.league.upper(),
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "count": len(games),
        "games": games,
    }
    OUT.write_text(json.dumps(payload, indent=2))
    print(f"wrote {OUT} — {len(games)} {args.league.upper()} games")
    for g in games:
        print(f"  {g['stage']:5} {g['matchup']:42} tot {g['total']} | {g['spread']} | "
              f"ML {g['ml_away']}/{g['ml_home']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
