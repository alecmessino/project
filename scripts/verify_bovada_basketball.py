"""League-agnostic Bovada verification — enumerate a whole slate and check that
the auto-detection + pace-clock mapping transition pre -> live correctly.

Built for tonight's 6 WNBA games (4x10min = 40-min regulation, NOT the NBA's 48):

    python scripts/verify_bovada_basketball.py --league wnba

Run it pre-game (expect every game PRE), then again after tips to watch games flip
to LIVE and confirm the elapsed/remaining clock maps with the right league length.
"""

from __future__ import annotations

import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mrbet.bovada_feed import (   # noqa: E402
    LEAGUES, BovadaProvider, board_events, event_from_bovada,
)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Verify Bovada pre->live for a basketball league")
    ap.add_argument("--league", default="wnba", choices=sorted(LEAGUES), help="nba or wnba")
    args = ap.parse_args(argv)
    cfg = LEAGUES[args.league]

    print(f"VERIFY · {args.league.upper()} slate  "
          f"({cfg['regulation_min']:.0f}-min reg, {cfg['quarter_min']:.0f}-min quarters)\n")

    events = board_events(args.league)
    if not events:
        print("FAIL ❌  no events on the board (not posted, league idle, or host geo-blocked).")
        return 2

    live_ok = pre_ok = 0
    for raw in events:
        ev = event_from_bovada(raw)
        p = BovadaProvider(ev, league=args.league, max_polls=1)
        p._raw_event = raw                      # wrap this specific discovered game
        stage = p.detect_mode(raw)
        head = f"{ev.away_key} @ {ev.home_key}  {ev.away} @ {ev.home}".ljust(46)

        if stage == "live":
            st = p._fetch_state()
            if st is None:
                print(f"  ⏳ {head} LIVE (clock not exposed yet — awaiting clock)")
                continue
            # Sanity: elapsed within the league's regulation, remaining = reg - elapsed.
            ok = (0 < st.minutes_elapsed <= cfg["regulation_min"]
                  and abs(st.minutes_elapsed + st.minutes_remaining - cfg["regulation_min"]) < 0.05)
            live_ok += ok
            mark = "✅" if ok else "✗"
            print(f"  {mark} {head} LIVE  {p._clock} | "
                  f"elapsed {st.minutes_elapsed:.1f}/{cfg['regulation_min']:.0f}m "
                  f"| score {ev.away_key} {st.away_score}-{st.home_score} {ev.home_key}")
        elif stage == "final":
            print(f"  🏁 {head} FINAL")
        else:
            pre_ok += 1
            print(f"  ⏸  {head} PRE (status={raw.get('status')}, live_flag={raw.get('live')})")

    total = len(events)
    print(f"\n{total} games · {pre_ok} pre · {live_ok} live-verified")
    if any(event_from_bovada(r) and BovadaProvider(event_from_bovada(r), league=args.league)
           ._classify_stage(r) == "live" for r in events) and live_ok == 0:
        print("FAIL ❌  a game looks live but the clock didn't map — send me this output.")
        return 2
    print("PASS ✅  detection + clock mapping consistent for this poll.")
    print("   (Re-run after tip-off to watch PRE -> LIVE and confirm live clocks.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
