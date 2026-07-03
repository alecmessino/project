#!/usr/bin/env python3
"""Investigate the line edge: efficiency null vs. dynamic drop-reversion.

Three questions, one read-only pass over the harvested trajectories + free MLB
play-by-play (no metered API):

  A. EFFICIENCY NULL — take the closing line right before each game and compare
     to the actual final total. If the market is efficient the residual is
     unbiased (mean ~0, Over ~50%): you cannot beat the closing number statically.

  B. DROP-REVERSION — the user's core thesis. At each mid-game half-inning, how
     far has the live total dropped below its pregame (closing) level, and does
     buying the Over at that dropped line beat the -110 breakeven (52.4%)? Bucket
     the hit rate by the size of the drop and see if the edge grows with it.

  C. OUR TTOP GATE — re-run the shipped engine (decay fair, beta=0.75) against the
     REAL live line at each moment (reusing ``replay_game``), attach a Wilson 95%
     interval so the small-sample caveat is explicit, and segment the gate's fires
     by the same drop buckets to see where on the reversion curve they land.

Reuses ``line_lookup`` / ``state_timeline`` (calibrate_decay) and ``replay_game``
(replay_today). Finals + derived per-game rows are cached to
``output/finals_cache.json`` so re-runs are cheap; pass ``--refresh`` to rebuild.

    python the_third_turn/investigate_line_edge.py
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402

from calibrate_decay import FEED, _get, line_lookup, state_timeline  # noqa: E402
from config import Constraints, EngineSettings  # noqa: E402
from replay_today import replay_game  # noqa: E402

console = Console()
HERE = Path(__file__).resolve().parent
TRAJ = HERE / "data" / "trajectories.jsonl"
CLOSING_CSV = HERE / "data" / "closing_lines.csv"
OUT = HERE / "output"
CACHE = OUT / "finals_cache.json"

BREAKEVEN = 110 / 210          # -110 no-vig breakeven = 0.5238
WIN_PAYOUT = 100 / 110         # units won on a -110 winner

# drop = pregame(closing) - live_line, in runs. Buckets are (low, high] with -inf/inf ends.
DROP_BUCKETS = [
    ("<= 0 (no drop / up)", -math.inf, 0.0),
    ("(0, 0.5]", 0.0, 0.5),
    ("(0.5, 1.0]", 0.5, 1.0),
    ("(1.0, 1.5]", 1.0, 1.5),
    ("(1.5, 2.0]", 1.5, 2.0),
    ("> 2.0", 2.0, math.inf),
]


def wilson_interval(wins: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score 95% CI for a binomial proportion (pushes excluded upstream)."""
    if n <= 0:
        return (float("nan"), float("nan"))
    p = wins / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    margin = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))


def bucket_label(drop: float) -> str:
    for label, lo, hi in DROP_BUCKETS:
        if lo < drop <= hi:
            return label
    return DROP_BUCKETS[0][0]  # drop == -inf guard (never hit in practice)


def roi_per_unit(hit: float) -> float:
    """EV per 1u staked at -110 given a decimal hit rate."""
    return hit * WIN_PAYOUT - (1 - hit)


def closing_line(points: list[dict], start_time: str) -> float:
    """The pregame line: last harvested point at/before first pitch (else the open)."""
    cut = (start_time or "")[:16]
    pre = [p["line"] for p in points if p["ts"] <= cut] if cut else []
    return pre[-1] if pre else points[0]["line"]


def half_inning_observations(points, timeline, final_total, closing) -> list[dict]:
    """One Over-vs-live-line observation per half-inning boundary (inning >= 3)."""
    fn = line_lookup(points)
    obs, seen = [], set()
    for ts, inning, half, _outs, _runs in timeline:
        key = (inning, half)
        if key in seen or inning < 3:
            continue
        seen.add(key)
        line = fn(ts)
        if line is None:
            continue
        obs.append({
            "inning": inning, "half": half, "line": line,
            "drop": round(closing - line, 2),
            "win": final_total > line, "push": final_total == line,
        })
    return obs


def per_game(feed, points, start_time, c, bullpen, tiers) -> dict:
    """All three sections' raw rows for one trajectory game."""
    timeline, final_total = state_timeline(feed)
    closing = closing_line(points, start_time)
    obs = half_inning_observations(points, timeline, final_total, closing)
    fn = line_lookup(points)
    fires = []
    for t in replay_game(feed, c, bullpen, tiers, closing, line_fn=fn):
        if t.trigger_type == "WATCH":
            continue
        fires.append({
            "rule": t.rule_name, "type": t.trigger_type,
            "line": t.live_total, "fair": round(t.anchor.expected_final, 2),
            "edge": round(t.edge, 2), "drop": round(closing - t.live_total, 2),
            "win": final_total > t.live_total, "push": final_total == t.live_total,
        })
    return {"final": final_total, "closing": closing, "obs": obs, "fires": fires}


# --------------------------------- reporting ---------------------------------
def section_a(records: list[dict]) -> dict:
    """records: [{game_pk, closing, final, source}]. Closing-line efficiency."""
    res = [r["final"] - r["closing"] for r in records]
    n = len(res)
    over = sum(1 for r in records if r["final"] > r["closing"])
    under = sum(1 for r in records if r["final"] < r["closing"])
    push = n - over - under
    within = {k: sum(1 for x in res if abs(x) <= k) / n for k in (1, 2, 3)}
    stats = {
        "n": n, "mean_residual": round(statistics.mean(res), 3),
        "median_residual": round(statistics.median(res), 3),
        "std_residual": round(statistics.pstdev(res), 3),
        "mae": round(statistics.mean(abs(x) for x in res), 3),
        "over": over, "under": under, "push": push,
        "over_pct": round(100 * over / n, 1),
        "within_1": round(100 * within[1], 1),
        "within_2": round(100 * within[2], 1),
        "within_3": round(100 * within[3], 1),
    }
    t = Table(title=f"A · Efficiency null — closing line vs. final ({n} games)")
    for col in ("metric", "value"):
        t.add_column(col, justify="left" if col == "metric" else "right")
    t.add_row("mean residual (final − closing)", f"{stats['mean_residual']:+.2f} runs")
    t.add_row("median residual", f"{stats['median_residual']:+.2f}")
    t.add_row("residual SD", f"{stats['std_residual']:.2f}")
    t.add_row("mean abs error", f"{stats['mae']:.2f}")
    t.add_row("Over / Under / Push", f"{over} / {under} / {push}")
    t.add_row("Over %", f"{stats['over_pct']:.1f}%   (efficient ⇒ ~50)")
    t.add_row("within ±1 / ±2 / ±3 runs",
              f"{stats['within_1']:.0f}% / {stats['within_2']:.0f}% / {stats['within_3']:.0f}%")
    console.print(t)
    return stats


def _bucket_table(title: str, obs: list[dict]) -> list[dict]:
    t = Table(title=title)
    for col in ("drop bucket (runs)", "n", "Over hit %", "Wilson 95% CI", "ROI/u @ -110"):
        t.add_column(col, justify="left" if col.startswith("drop") else "right")
    out = []
    for label, _lo, _hi in DROP_BUCKETS:
        sub = [o for o in obs if bucket_label(o["drop"]) == label]
        dec = [o for o in sub if not o["push"]]
        n = len(dec)
        w = sum(1 for o in dec if o["win"])
        if n == 0:
            t.add_row(label, "0", "—", "—", "—")
            out.append({"bucket": label, "n": 0, "wins": 0})
            continue
        hit = w / n
        lo, hi = wilson_interval(w, n)
        beat = "[green]" if hit > BREAKEVEN else "[red]"
        t.add_row(label, str(n), f"{beat}{100*hit:.1f}%[/]",
                  f"{100*lo:.0f}–{100*hi:.0f}%", f"{roi_per_unit(hit):+.3f}")
        out.append({"bucket": label, "n": n, "wins": w, "hit_pct": round(100 * hit, 1),
                    "ci_low": round(100 * lo, 1), "ci_high": round(100 * hi, 1),
                    "roi_u": round(roi_per_unit(hit), 3)})
    console.print(t)
    return out


def section_b(obs_all: list[dict]) -> dict:
    console.print(f"\n[dim]Breakeven at -110 = {100*BREAKEVEN:.1f}%. "
                  f"Green = beats breakeven.[/]")
    all_tbl = _bucket_table(
        f"B · Drop-reversion — Over vs. live line by drop size, inning ≥ 3 "
        f"({len(obs_all)} obs)", obs_all)
    late = [o for o in obs_all if o["inning"] >= 5]
    late_tbl = _bucket_table(
        f"B (late) · same, inning ≥ 5 — our gate's window ({len(late)} obs)", late)
    return {"inn_ge_3": all_tbl, "inn_ge_5": late_tbl}


def section_c(fires: list[dict]) -> dict:
    dec = [f for f in fires if not f["push"]]
    n, w = len(dec), sum(1 for f in dec if f["win"])
    hit = w / n if n else float("nan")
    lo, hi = wilson_interval(w, n)
    units = w * WIN_PAYOUT - (n - w)
    console.print()
    t = Table(title=f"C · Shipped TTOP gate vs. real live lines ({n} decided fires)")
    for col in ("metric", "value"):
        t.add_column(col, justify="left" if col == "metric" else "right")
    t.add_row("fires (decided / pushes)", f"{n} / {len(fires) - n}")
    t.add_row("wins", str(w))
    t.add_row("hit %", f"{100*hit:.1f}%" if n else "—")
    t.add_row("Wilson 95% CI", f"{100*lo:.0f}–{100*hi:.0f}%" if n else "—")
    t.add_row("units @ -110", f"{units:+.2f}")
    t.add_row("breakeven", f"{100*BREAKEVEN:.1f}%")
    console.print(t)

    seg = Table(title="C · gate fires segmented by drop bucket (where they sit on B)")
    for col in ("drop bucket", "fires", "Over hit %", "avg edge"):
        seg.add_column(col, justify="left" if col == "drop bucket" else "right")
    by_bucket = []
    for label, _lo, _hi in DROP_BUCKETS:
        sub = [f for f in dec if bucket_label(f["drop"]) == label]
        if not sub:
            continue
        ww = sum(1 for f in sub if f["win"])
        avg_edge = statistics.mean(f["edge"] for f in sub)
        seg.add_row(label, str(len(sub)), f"{100*ww/len(sub):.0f}%", f"{avg_edge:+.2f}")
        by_bucket.append({"bucket": label, "fires": len(sub), "wins": ww,
                          "hit_pct": round(100 * ww / len(sub), 1),
                          "avg_edge": round(avg_edge, 2)})
    console.print(seg)
    return {"n": n, "wins": w, "hit_pct": round(100 * hit, 1) if n else None,
            "ci_low": round(100 * lo, 1) if n else None,
            "ci_high": round(100 * hi, 1) if n else None,
            "units": round(units, 2), "by_bucket": by_bucket}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Line-edge investigation")
    ap.add_argument("--refresh", action="store_true", help="ignore the finals cache")
    args = ap.parse_args(argv)

    if not TRAJ.exists():
        console.print("[red]No trajectories — run harvest_trajectories.py first.[/]")
        return 1
    games = [json.loads(l) for l in TRAJ.read_text().splitlines() if l.strip()]
    csv_lines: dict[int, float] = {}
    if CLOSING_CSV.exists():
        with CLOSING_CSV.open() as fh:
            for r in csv.DictReader(fh):
                if r.get("game_pk"):
                    csv_lines[int(r["game_pk"])] = float(r["pregame_total"])

    c = Constraints(use_decay_ratio=True, market_shrink_beta=0.75)  # shipped variant
    settings = EngineSettings()
    bullpen, tiers = settings.load_bullpen_quality(), settings.load_starter_tiers()

    cache = {} if args.refresh or not CACHE.exists() else json.loads(CACHE.read_text())
    console.rule(f"[bold]Line-edge investigation · {len(games)} trajectory games · "
                 f"{len(csv_lines)} closing-line rows")

    a_records, obs_all, fires_all = [], [], []
    traj_pks = set()
    for g in games:
        pk = int(g["game_pk"])
        traj_pks.add(pk)
        key = str(pk)
        if key in cache and "obs" in cache[key]:
            d = cache[key]
        else:
            try:
                feed = _get(FEED.format(pk=pk))
            except Exception as exc:  # noqa: BLE001
                console.log(f"[yellow]{pk} fetch failed: {type(exc).__name__}[/]")
                continue
            d = per_game(feed, g["points"], g.get("start_time", ""), c, bullpen, tiers)
            cache[key] = d
        if not d.get("obs") and d.get("final") in (None, 0):
            continue
        a_records.append({"game_pk": pk, "closing": d["closing"],
                          "final": d["final"], "source": "traj"})
        obs_all.extend(d["obs"])
        fires_all.extend(d["fires"])

    # closing_lines.csv games not covered by a trajectory — Section A only
    for pk, total in csv_lines.items():
        if pk in traj_pks:
            continue
        key = f"csv{pk}"
        if key in cache:
            final = cache[key]["final"]
        else:
            try:
                _tl, final = state_timeline(_get(FEED.format(pk=pk)))
            except Exception:  # noqa: BLE001
                continue
            cache[key] = {"final": final}
        if not final:
            continue
        a_records.append({"game_pk": pk, "closing": total, "final": final, "source": "csv"})

    OUT.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache))

    a = section_a(a_records)
    b = section_b(obs_all)
    cc = section_c(fires_all)

    report = {"n_games": len(traj_pks), "n_efficiency_games": len(a_records),
              "n_obs": len(obs_all), "section_a": a, "section_b": b, "section_c": cc}
    (OUT / "line_edge_report.json").write_text(json.dumps(report, indent=2, default=str))
    console.print(f"\n[green]Wrote {OUT / 'line_edge_report.json'}[/]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
