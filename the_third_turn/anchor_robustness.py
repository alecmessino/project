#!/usr/bin/env python3
"""Is the TTOP gate's backtested edge REAL or threshold noise?

The shipped honest backtest (``calibrate_decay.py``) anchors the model's fair value
on each game's OPENING trajectory point and reports ~56% / +EV. That result turns
out to be fragile: the opening and the pre-first-pitch CLOSING line are near
identical in value (median difference 0), yet swapping one for the other flips the
backtest from +EV to −EV. This script explains why.

It replays the SAME shipped engine over the SAME games under two pregame anchors
(opening vs. closing) and partitions the fires:

  * COMMON      — fire under BOTH anchors (the edge the gate is *confident* about)
  * OPENING-ONLY / CLOSING-ONLY — marginal fires that only clear the required-edge
    bar under one anchor (a ~0.2-run wobble in the fair, right at the threshold)

If the COMMON fires don't beat breakeven, the headline edge lives entirely in the
marginal fires — i.e. it's threshold noise, not signal.

    python the_third_turn/anchor_robustness.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402

from calibrate_decay import FEED, _get, line_lookup, state_timeline  # noqa: E402
from config import Constraints, EngineSettings  # noqa: E402
from investigate_line_edge import BREAKEVEN, WIN_PAYOUT, wilson_interval  # noqa: E402
from replay_today import replay_game  # noqa: E402

console = Console()
HERE = Path(__file__).resolve().parent
TRAJ = HERE / "data" / "trajectories.jsonl"


def closing_line(points: list[dict], start_time: str) -> float:
    cut = (start_time or "")[:16]
    pre = [p["line"] for p in points if p["ts"] <= cut] if cut else []
    return pre[-1] if pre else points[0]["line"]


def fire_set(games, anchor_fn, c, bullpen, tiers) -> dict:
    """(game_pk, live_line) -> (final, over_win, push) for every non-WATCH fire."""
    out = {}
    for g in games:
        try:
            feed = _get(FEED.format(pk=g["game_pk"]))
        except Exception:  # noqa: BLE001
            continue
        _tl, final = state_timeline(feed)
        fn = line_lookup(g["points"])
        for t in replay_game(feed, c, bullpen, tiers, anchor_fn(g), line_fn=fn):
            if t.trigger_type == "WATCH":
                continue
            out[(g["game_pk"], t.live_total)] = (final, final > t.live_total,
                                                 final == t.live_total)
    return out


def _row(tbl, name, keys, src):
    dec = [src[k] for k in keys if not src[k][2]]      # exclude pushes
    n, w = len(dec), sum(1 for _f, win, _p in dec if win)
    if not n:
        tbl.add_row(name, "0", "—", "—", "—")
        return {"segment": name, "n": 0}
    hit = w / n
    lo, hi = wilson_interval(w, n)
    units = w * WIN_PAYOUT - (n - w)
    color = "[green]" if hit > BREAKEVEN else "[red]"
    tbl.add_row(name, str(n), f"{color}{100*hit:.1f}%[/]",
                f"{100*lo:.0f}–{100*hi:.0f}%", f"{units:+.2f}")
    return {"segment": name, "n": n, "wins": w, "hit_pct": round(100 * hit, 1),
            "units": round(units, 2)}


def main() -> int:
    if not TRAJ.exists():
        console.print("[red]No trajectories — run harvest_trajectories.py first.[/]")
        return 1
    games = [json.loads(l) for l in TRAJ.read_text().splitlines() if l.strip()]
    c = Constraints(use_decay_ratio=True, market_shrink_beta=0.75)   # shipped
    s = EngineSettings()
    bullpen, tiers = s.load_bullpen_quality(), s.load_starter_tiers()
    console.rule(f"[bold]Anchor robustness · {len(games)} games · shipped engine")

    op = fire_set(games, lambda g: g["points"][0]["line"], c, bullpen, tiers)
    cl = fire_set(games, lambda g: closing_line(g["points"], g.get("start_time", "")),
                  c, bullpen, tiers)
    common = set(op) & set(cl)
    open_only, close_only = set(op) - set(cl), set(cl) - set(op)

    tbl = Table(title=f"Fires by anchor-robustness (breakeven {100*BREAKEVEN:.1f}%)")
    for col in ("fire segment", "n", "Over hit %", "Wilson 95% CI", "units @ -110"):
        tbl.add_column(col, justify="left" if col == "fire segment" else "right")
    rows = [
        _row(tbl, "COMMON (both anchors)", common, op),
        _row(tbl, "OPENING-only (marginal)", open_only, op),
        _row(tbl, "CLOSING-only (marginal)", close_only, cl),
    ]
    console.print(tbl)
    console.print("[dim]If COMMON < breakeven while a marginal segment carries the +EV, "
                  "the 'edge' is threshold noise, not signal.[/]")
    (HERE / "output" / "anchor_robustness.json").write_text(
        json.dumps({"common": len(common), "opening_only": len(open_only),
                    "closing_only": len(close_only), "segments": rows}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
