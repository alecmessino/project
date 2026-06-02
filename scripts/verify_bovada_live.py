"""Tip-off verification — confirm Bovada is pulling LIVE clock + score correctly.

Run this once the game is actually in-play (a few minutes after tip). It fetches
Bovada live, maps the clock through the exact Pace-Tracker math, sanity-checks the
result, and prints a clear PASS / NOT-LIVE-YET / FAIL verdict — so you know whether
it's safe to flip the production runner to Bovada.

    python scripts/verify_bovada_live.py --game config/games/nyk_sas_2026-06-03.yaml
"""

from __future__ import annotations

import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mrbet.bovada_feed import BovadaProvider          # noqa: E402
from mrbet.config import GameConfig                   # noqa: E402
from mrbet.models import MarketType, Period           # noqa: E402
from mrbet.reversion import projected_final           # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Verify Bovada live clock/score at tip-off")
    ap.add_argument("--game", required=True, help="path to config/games/*.yaml")
    ap.add_argument("--beta", type=float, default=0.90, help="reversion beta (settings default)")
    args = ap.parse_args(argv)

    game = GameConfig.load(args.game)
    p = BovadaProvider(game.event, max_polls=1)
    print(f"VERIFY · {game.event.away} @ {game.event.home}  ({game.event.id})\n")

    ev = p._refresh()
    if ev is None:
        print("FAIL ❌  event not on Bovada's NBA board (not posted, or this host is geo-blocked).")
        return 2

    print(f"matched id={ev.get('id')}  live={ev.get('live')}  status={ev.get('status')}")
    state = p._fetch_state()
    if state is None:
        print("\nNOT LIVE YET ⏳  Bovada shows the game but no in-play clock.")
        print("   Pre-tip or just-tipped — wait ~2-3 min into Q1 and run again.")
        return 1

    # ---- live state pulled — sanity-check the clock/score mapping ---------- #
    checks = []
    checks.append(("clock string present", bool(p._clock)))
    checks.append(("elapsed in 0–48 min", 0.0 < state.minutes_elapsed <= 48.0))
    checks.append(("remaining = 48 − elapsed",
                   abs((state.minutes_elapsed + state.minutes_remaining) - 48.0) < 0.05))
    checks.append(("score non-negative", state.away_score >= 0 and state.home_score >= 0))
    checks.append(("some time elapsed (game underway)", state.minutes_elapsed > 0))

    print(f"\nLIVE READ:")
    print(f"  clock     : {p._clock}")
    print(f"  elapsed   : {state.minutes_elapsed:.2f} min   remaining: {state.minutes_remaining:.2f} min")
    print(f"  score     : {game.event.away_key} {state.away_score} — {state.home_score} {game.event.home_key}")

    # ---- prove the Pace Tracker produces a sane projection ----------------- #
    lines = p._fetch_lines()
    full = next((l for l in lines if l.market_type is MarketType.GAME_TOTAL
                 and l.period is Period.FULL), None)
    if full is not None:
        pre = game.totals["full"].line if hasattr(game.totals["full"], "line") else game.totals["full"]
        fair = projected_final(pre, state.total_score, state, beta=args.beta, min_minutes_elapsed=5.0)
        print(f"\nPACE TRACKER (β={args.beta}):")
        print(f"  pregame {pre} · live {full.line} · scored {state.total_score} "
              f"→ projected final {fair:.1f} (edge {fair - full.line:+.1f} vs live)")
        checks.append(("projection finite & sane (100–320)", 100 <= fair <= 320))
    else:
        print("\n  (no full-game total parsed yet — Bovada may not have re-posted it in-play)")

    print("\nCHECKS:")
    for name, ok in checks:
        print(f"  [{'✓' if ok else '✗'}] {name}")

    if all(ok for _, ok in checks):
        print("\nPASS ✅  Live clock + score map correctly. Safe to flip the runner to Bovada.")
        return 0
    print("\nFAIL ❌  One or more checks failed — DO NOT flip yet; send me this output.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
