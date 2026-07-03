#!/usr/bin/env python3
"""Drop-reversion CONDITIONED on the TTOP cliff — fix the ruler, keep the map.

The context-free drop analysis (investigate_line_edge.py, Section B) conflates two
very different drops:

  * CLOCK drops — the live total drifts down simply because outs accumulate without
    runs. Buying the Over into pure time-decay is trivially −EV.
  * CLIFF drops — the total drops WHILE a vulnerable Mid/Back starter is reaching his
    TTO2/TTO3 time-through-order cliff against the top of the order. This is the
    system's actual thesis.

Averaging them together washes out the signal. This script separates them. It walks
each game's play-by-play (same state reconstruction as replay_today.replay_game),
tags every half-inning as:

  * CONTEXT  — a shipped TTO2/TTO3 CONFIRM state is live (exact tto, top-order slot,
    min inning, starter still on the mound, Mid/Back tier, non-elite bullpen)
  * CONTROL  — an in-window half-inning (inning ≥ 3) with no active cliff

then measures the Over vs the REAL live line, bucketed by drop size — with NO edge
gate (a fluid gradient, not the binary required-edge filter). If CONTEXT drops beat
breakeven and beat CONTROL at the same drop size, the cliff — not the clock — is
carrying a real edge, and the fix is to gate on a gradient rather than shelve it.

    python the_third_turn/conditional_drop_reversion.py
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402

from calibrate_decay import FEED, _get, line_lookup, state_timeline  # noqa: E402
from config import Constraints, EngineSettings  # noqa: E402
from investigate_line_edge import (  # noqa: E402
    BREAKEVEN, DROP_BUCKETS, WIN_PAYOUT, bucket_label, closing_line,
    roi_per_unit, wilson_interval,
)
from shared_piping.team_map import resolve  # noqa: E402

console = Console()
HERE = Path(__file__).resolve().parent
TRAJ = HERE / "data" / "trajectories.jsonl"
CACHE = HERE / "output" / "conditional_cache.json"


def active_cliff(rules, elite, tto, slot, inning, starter_on, tier, pen_ra9):
    """Return the matching TTO rule name if this state is an active CONFIRM cliff."""
    for r in rules:
        if getattr(r, "kind", "tto") == "watch":
            continue
        if (tto == r.times_through_order and slot in r.top_of_order_slots
                and inning >= r.min_inning and starter_on
                and tier in r.starter_tier_filter
                and (pen_ra9 is None or pen_ra9 >= elite)):
            return r.name
    return None


def walk_game(feed, points, start_time, rules, elite, bullpen, tiers) -> dict:
    """One decorrelated observation per half-inning, split CONTEXT vs CONTROL."""
    gd, ld = feed.get("gameData", {}), feed.get("liveData", {})
    away = resolve(gd.get("teams", {}).get("away", {}).get("name", "")) or "?"
    home = resolve(gd.get("teams", {}).get("home", {}).get("name", "")) or "?"
    box = ld.get("boxscore", {}).get("teams", {})
    order = {"away": box.get("away", {}).get("battingOrder", []) or [],
             "home": box.get("home", {}).get("battingOrder", []) or []}
    starter = {s: (box.get(s, {}).get("pitchers", []) or [None])[0] for s in ("away", "home")}

    _tl, final = state_timeline(feed)
    fn = line_lookup(points)
    closing = closing_line(points, start_time)

    faced: dict[tuple, int] = defaultdict(int)
    running_outs = 0
    cur_half = None
    # per half-inning: {"line":.., "active_rule":.. or None}; first active PA wins
    half_rows: dict[tuple, dict] = {}

    for play in ld.get("plays", {}).get("allPlays", []):
        about, match, res = play.get("about", {}), play.get("matchup", {}), play.get("result", {})
        if res.get("type") != "atBat" or not match.get("batter"):
            continue
        is_top = bool(about.get("isTopInning"))
        half = "top" if is_top else "bottom"
        inning = int(about.get("inning") or 0)
        if (inning, half) != cur_half:
            running_outs = 0
            cur_half = (inning, half)

        pitching_side = "home" if is_top else "away"
        batting_side = "away" if is_top else "home"
        pitcher_id = (match.get("pitcher") or {}).get("id")
        batter_id = (match.get("batter") or {}).get("id")
        sid = starter[pitching_side]
        faced[(pitcher_id, batter_id)] += 1
        tto = faced[(pitcher_id, batter_id)]
        slot = order[batting_side].index(batter_id) + 1 if batter_id in order[batting_side] else None
        tier = tiers.get(str(sid), "Unknown")
        starter_on = pitcher_id == sid
        pen_ra9 = bullpen.get(home if is_top else away)

        line = fn(about.get("startTime") or "")
        if line is not None and inning >= 3:
            rule = active_cliff(rules, elite, tto, slot, inning, starter_on, tier, pen_ra9)
            key = (inning, half)
            slot_row = half_rows.get(key)
            if slot_row is None:
                half_rows[key] = {"line": line, "active_rule": rule}
            elif rule and not slot_row["active_rule"]:
                slot_row["line"], slot_row["active_rule"] = line, rule  # upgrade to context

        running_outs = int(play.get("count", {}).get("outs") or running_outs)

    context, control = [], []
    for (inning, half), row in half_rows.items():
        obs = {"inning": inning, "drop": round(closing - row["line"], 2),
               "line": row["line"], "win": final > row["line"], "push": final == row["line"]}
        if row["active_rule"]:
            obs["rule"] = row["active_rule"]
            context.append(obs)
        else:
            control.append(obs)
    return {"final": final, "context": context, "control": control}


# --------------------------------- reporting ---------------------------------
def _seg(obs):
    dec = [o for o in obs if not o["push"]]
    n, w = len(dec), sum(1 for o in dec if o["win"])
    return n, w


def bucket_table(title: str, obs: list[dict]) -> list[dict]:
    t = Table(title=title)
    for col in ("drop bucket (runs)", "n", "Over hit %", "Wilson 95% CI", "ROI/u @ -110"):
        t.add_column(col, justify="left" if col.startswith("drop") else "right")
    rows = []
    for label, _lo, _hi in DROP_BUCKETS:
        n, w = _seg([o for o in obs if bucket_label(o["drop"]) == label])
        if not n:
            t.add_row(label, "0", "—", "—", "—")
            rows.append({"bucket": label, "n": 0})
            continue
        hit = w / n
        lo, hi = wilson_interval(w, n)
        color = "[green]" if hit > BREAKEVEN else "[red]"
        t.add_row(label, str(n), f"{color}{100*hit:.1f}%[/]",
                  f"{100*lo:.0f}–{100*hi:.0f}%", f"{roi_per_unit(hit):+.3f}")
        rows.append({"bucket": label, "n": n, "wins": w, "hit_pct": round(100 * hit, 1),
                     "ci_low": round(100 * lo, 1), "ci_high": round(100 * hi, 1),
                     "roi_u": round(roi_per_unit(hit), 3)})
    console.print(t)
    return rows


def headline(name: str, obs: list[dict]):
    n, w = _seg(obs)
    if not n:
        console.print(f"[dim]{name}: no observations[/]")
        return {"n": 0}
    hit = w / n
    lo, hi = wilson_interval(w, n)
    units = w * WIN_PAYOUT - (n - w)
    color = "green" if hit > BREAKEVEN else "red"
    console.print(f"[bold]{name}[/]: n={n}  Over [{color}]{100*hit:.1f}%[/] "
                  f"(CI {100*lo:.0f}–{100*hi:.0f}%)  units {units:+.2f}")
    return {"n": n, "wins": w, "hit_pct": round(100 * hit, 1),
            "ci_low": round(100 * lo, 1), "ci_high": round(100 * hi, 1),
            "units": round(units, 2)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Conditional (TTOP) drop-reversion")
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args(argv)
    if not TRAJ.exists():
        console.print("[red]No trajectories.[/]")
        return 1
    games = [json.loads(l) for l in TRAJ.read_text().splitlines() if l.strip()]
    c = Constraints(use_decay_ratio=True, market_shrink_beta=0.75)
    rules, elite = c.rules, c.bullpen_elite_ra9
    s = EngineSettings()
    bullpen, tiers = s.load_bullpen_quality(), s.load_starter_tiers()
    cache = {} if args.refresh or not CACHE.exists() else json.loads(CACHE.read_text())

    console.rule(f"[bold]Conditional drop-reversion · {len(games)} games")
    context, control = [], []
    for g in games:
        key = str(g["game_pk"])
        if key in cache:
            d = cache[key]
        else:
            try:
                feed = _get(FEED.format(pk=g["game_pk"]))
            except Exception:  # noqa: BLE001
                continue
            d = walk_game(feed, g["points"], g.get("start_time", ""),
                          rules, elite, bullpen, tiers)
            cache[key] = d
        context.extend(d["context"])
        control.extend(d["control"])
    CACHE.write_text(json.dumps(cache))

    console.print(f"\n[dim]Breakeven -110 = {100*BREAKEVEN:.1f}%. CONTEXT = active TTO2/TTO3 "
                  f"cliff; CONTROL = in-window half-innings with no cliff.[/]\n")
    h_ctx = headline("CONTEXT (cliff active)", context)
    h_ctl = headline("CONTROL (clock only)  ", control)
    tto2 = [o for o in context if "TTO2" in o.get("rule", "")]
    tto3 = [o for o in context if "TTO3" in o.get("rule", "")]
    headline("  · CONTEXT TTO2", tto2)
    headline("  · CONTEXT TTO3", tto3)

    console.print()
    ctx_b = bucket_table("CONTEXT — Over vs live line by drop size (cliff active)", context)
    ctl_b = bucket_table("CONTROL — Over vs live line by drop size (no cliff)", control)

    # lift = context Over% − control Over%, per bucket
    lift = Table(title="LIFT — does the cliff beat the clock at the same drop? (CONTEXT − CONTROL)")
    for col in ("drop bucket", "CONTEXT n / hit%", "CONTROL n / hit%", "lift (pts)"):
        lift.add_column(col, justify="left" if col == "drop bucket" else "right")
    cb = {r["bucket"]: r for r in ctx_b}
    lb = {r["bucket"]: r for r in ctl_b}
    for label, _lo, _hi in DROP_BUCKETS:
        a, b = cb.get(label, {}), lb.get(label, {})
        if not a.get("n") and not b.get("n"):
            continue
        ah, bh = a.get("hit_pct"), b.get("hit_pct")
        delta = f"{ah - bh:+.1f}" if ah is not None and bh is not None else "—"
        color = "[green]" if ah is not None and bh is not None and ah > bh else ""
        lift.add_row(label, f"{a.get('n',0)} / {ah if ah is not None else '—'}%",
                     f"{b.get('n',0)} / {bh if bh is not None else '—'}%",
                     f"{color}{delta}[/]" if color else delta)
    console.print(lift)

    (HERE / "output" / "conditional_drop_reversion.json").write_text(json.dumps(
        {"context": h_ctx, "control": h_ctl,
         "context_by_bucket": ctx_b, "control_by_bucket": ctl_b,
         "context_tto2": len(tto2), "context_tto3": len(tto3)}, indent=2))
    console.print(f"\n[green]Wrote output/conditional_drop_reversion.json[/]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
