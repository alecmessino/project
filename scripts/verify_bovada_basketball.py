"""League-agnostic Bovada verification — enumerate a whole slate and confirm the
auto-detection + pace-clock mapping transition pre -> live correctly.

Liveness/clock come from Bovada's SCORES endpoint (the coupon omits the in-play
clock). Use --retry-minutes to poll until a game actually tips:

    python scripts/verify_bovada_basketball.py --league wnba --retry-minutes 10

Exit: 0 = PASS (>=1 game live with a correctly-mapped clock), 1 = pending
(nothing live yet — kept retrying until the window closed), 2 = a live game's
clock mapping was wrong (real bug — send the output).
"""

from __future__ import annotations

import argparse
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mrbet.bovada_feed import (   # noqa: E402
    LEAGUES, BovadaProvider, board_events, event_from_bovada,
)


def run_check(league: str) -> int:
    """One pass over the slate. 0 = a game live+mapped, 1 = pending, 2 = bad mapping."""
    cfg = LEAGUES[league]
    print(f"VERIFY · {league.upper()} slate  "
          f"({cfg['regulation_min']:.0f}-min reg, {cfg['quarter_min']:.0f}-min quarters) "
          f"· {time.strftime('%H:%M:%S')}")

    events = board_events(league)
    if not events:
        print("  no events on the board yet (not posted, idle, or fetch blocked).")
        return 1

    live_ok = bad = pending = 0
    for raw in events:
        ev = event_from_bovada(raw)
        p = BovadaProvider(ev, league=league, max_polls=1)
        p._raw_event = raw
        head = f"{ev.away_key} @ {ev.home_key}".ljust(14)
        st = p._fetch_state()                      # scores-based; None unless truly live
        if st is not None:
            ok = (0 <= st.minutes_elapsed <= cfg["regulation_min"]
                  and abs(st.minutes_elapsed + st.minutes_remaining - cfg["regulation_min"]) < 0.05)
            if ok:
                live_ok += 1
                print(f"  ✅ {head} LIVE {p._clock} | elapsed "
                      f"{st.minutes_elapsed:.1f}/{cfg['regulation_min']:.0f}m | "
                      f"{ev.away_key} {st.away_score}-{st.home_score} {ev.home_key}")
            else:
                bad += 1
                print(f"  ✗ {head} LIVE but clock maps WRONG "
                      f"(elapsed {st.minutes_elapsed} + rem {st.minutes_remaining} "
                      f"!= {cfg['regulation_min']})")
        elif p._stage == "final":
            print(f"  🏁 {head} FINAL")
        else:
            pending += 1
            print(f"  ⏸  {head} not live yet")

    print(f"  -> {len(events)} games · {live_ok} live-verified · {pending} pending · {bad} bad")
    if bad:
        return 2
    return 0 if live_ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Verify Bovada pre->live for a basketball league")
    ap.add_argument("--league", default="wnba", choices=sorted(LEAGUES))
    ap.add_argument("--retry-minutes", type=float, default=0.0,
                    help="keep polling (every 60s) up to this many minutes for a live game")
    args = ap.parse_args(argv)

    deadline = time.time() + args.retry_minutes * 60.0
    attempt = 0
    while True:
        attempt += 1
        code = run_check(args.league)
        if code == 0:
            print("\nPASS ✅  a game is live and its clock maps correctly.")
            return 0
        if code == 2:
            print("\nFAIL ❌  a live game's clock mapping is wrong — send this output.")
            return 2
        if time.time() >= deadline:
            print(f"\n{'PENDING ⏳' if args.retry_minutes else 'NOT LIVE YET ⏳'}  "
                  f"no game live with a clock after {attempt} attempt(s). "
                  "Re-run nearer tip-off." )
            return 1
        print(f"  …retry {attempt} — waiting 60s for a tip "
              f"(~{(deadline - time.time())/60:.0f} min left)\n", flush=True)
        time.sleep(60)


if __name__ == "__main__":
    raise SystemExit(main())
