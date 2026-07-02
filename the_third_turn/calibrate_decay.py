#!/usr/bin/env python3
"""Calibrate the market's live-line decay + run the FIRST honest backtest.

Uses harvested Pinnacle trajectories (``data/trajectories.jsonl``) joined to MLB
play-by-play (free statsapi) to answer two questions:

1. **Decay curve** — where does the market's live total actually sit, conditional
   on game situation? Measured as ``ratio = (live_line − runs) / (pregame × frac_
   remaining)``, bucketed by game progress × revealed pace (cold/normal/hot). This
   is the empirical "situation-justified drop" the user's framing calls for; the
   model's RE24 fair implicitly assumes ratio ≈ 1 everywhere.

2. **Honest backtest** — replay the exact engine rules over each game's PAs with
   the ACTUAL live line at each moment (not the pregame stand-in), and score fires
   vs finals under: (a) the z-gate alone, (b) z-gate + β-shrinkage.

    python the_third_turn/calibrate_decay.py
"""

from __future__ import annotations

import bisect
import json
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402

from config import Constraints, EngineSettings  # noqa: E402
from replay_today import replay_game  # noqa: E402
from shared_piping.decay import PACE_BAND, bucket_of  # noqa: E402
from shared_piping.run_expectancy import fraction_remaining  # noqa: E402

console = Console()
HERE = Path(__file__).resolve().parent
TRAJ = HERE / "data" / "trajectories.jsonl"
OUT = HERE / "output"
FEED = "https://statsapi.mlb.com/api/v1.1/game/{pk}/feed/live"


def _get(url):
    return json.loads(urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": "the-third-turn/1.0"}),
        timeout=30).read())


def line_lookup(points: list[dict]):
    """ts -> most recent line at/before ts (None if >10 min stale or pre-first-point)."""
    keys = [p["ts"] for p in points]

    def fn(ts: str):
        if not ts:
            return None
        i = bisect.bisect_right(keys, ts[:16]) - 1
        if i < 0:
            return None
        # reject if the freshest point is >10 minutes old (market suspended/closed)
        if keys[i][:16] < ts[:16] and (int(ts[11:13]) * 60 + int(ts[14:16])) - \
                (int(keys[i][11:13]) * 60 + int(keys[i][14:16])) > 10:
            return None
        return points[i]["line"]
    return fn


def state_timeline(feed: dict):
    """[(ts, inning, half, outs, runs)] per completed play, plus final total."""
    plays = feed.get("liveData", {}).get("plays", {}).get("allPlays", [])
    tl = []
    away = home = 0
    for p in plays:
        about, res = p.get("about", {}), p.get("result", {})
        ts = about.get("endTime") or about.get("startTime")
        if not ts:
            continue
        away = int(res.get("awayScore") or away)
        home = int(res.get("homeScore") or home)
        tl.append((ts, int(about.get("inning") or 0),
                   "top" if about.get("isTopInning") else "bottom",
                   int(p.get("count", {}).get("outs") or 0), away + home))
    return tl, away + home


def main() -> int:
    if not TRAJ.exists():
        console.print("[red]No trajectories — run harvest_trajectories.py first.[/]")
        return 1
    games = [json.loads(l) for l in TRAJ.read_text().splitlines() if l.strip()]
    console.rule(f"[bold]Decay calibration + honest backtest · {len(games)} games")

    settings = EngineSettings()
    bullpen, tiers = settings.load_bullpen_quality(), settings.load_starter_tiers()

    # ---- part 1: empirical decay surface -----------------------------------
    # ratio buckets: progress (early/mid/late) × revealed pace (cold/normal/hot)
    buckets: dict[tuple, list[float]] = defaultdict(list)
    # ---- part 2: honest replays --------------------------------------------
    variants = {
        "OLD fair (ratio=1), β=1.0": Constraints(use_decay_ratio=False, market_shrink_beta=1.0),
        "decay fair, β=1.0": Constraints(use_decay_ratio=True, market_shrink_beta=1.0),
        "decay fair, β=0.75 (ship)": Constraints(use_decay_ratio=True, market_shrink_beta=0.75),
        "decay fair, β=0.4 (old choke)": Constraints(use_decay_ratio=True, market_shrink_beta=0.4),
    }
    fires: dict[str, list] = {k: [] for k in variants}

    processed = 0
    for g in games:
        try:
            feed = _get(FEED.format(pk=g["game_pk"]))
        except Exception:  # noqa: BLE001
            continue
        tl, final_total = state_timeline(feed)
        if not tl:
            continue
        pts = g["points"]
        pregame = pts[0]["line"]
        fn = line_lookup(pts)

        # decay surface samples (every ~5th play to decorrelate)
        for ts, inning, half, outs, runs in tl[::5]:
            line = fn(ts)
            if line is None or inning < 2 or inning > 8:
                continue
            frac = fraction_remaining(inning, half, outs)
            naive_remaining = pregame * frac
            if naive_remaining < 1.5:
                continue
            prog, pace = bucket_of(pregame, inning, half, outs, runs)  # shared binning
            buckets[(prog, pace)].append((line - runs) / naive_remaining)

        # honest replay per variant — β affects the market-verified gate; the
        # trajectory line IS the market, so tag the quote book accordingly by
        # gating with the same required-edge inflation used live.
        for name, c in variants.items():
            fired = replay_game(feed, c, bullpen, tiers, pregame, line_fn=fn)
            for t in fired:
                if t.trigger_type == "WATCH":
                    continue
                fires[name].append({
                    "game_pk": g["game_pk"], "rule": t.rule_name, "type": t.trigger_type,
                    "line": t.live_total, "fair": t.anchor.expected_final,
                    "edge": round(t.edge, 2), "final": final_total,
                    "win": final_total > t.live_total})
        processed += 1

    # ---- report: decay surface ---------------------------------------------
    import statistics
    table = Table(title="Market live-line decay: (line−runs)/(pregame×frac_remaining)")
    for col in ("progress", "pace", "n", "median ratio", "p25", "p75"):
        table.add_column(col, justify="right" if col not in ("progress", "pace") else "left")
    surface = {}
    for (prog, pace) in sorted(buckets):
        vals = sorted(buckets[(prog, pace)])
        if len(vals) < 20:
            continue
        med = statistics.median(vals)
        surface[f"{prog}|{pace}"] = {"median": round(med, 3), "n": len(vals),
                                     "p25": round(vals[len(vals)//4], 3),
                                     "p75": round(vals[3*len(vals)//4], 3)}
        table.add_row(prog, pace, str(len(vals)), f"{med:.3f}",
                      f"{vals[len(vals)//4]:.3f}", f"{vals[3*len(vals)//4]:.3f}")
    console.print(table)
    (OUT / "decay_surface.json").write_text(json.dumps(surface, indent=2))

    # ---- report: honest backtest -------------------------------------------
    bt = Table(title=f"HONEST backtest vs REAL live lines ({processed} games)")
    for col in ("variant", "fires", "wins", "hit %", "units @ -110"):
        bt.add_column(col, justify="right" if col != "variant" else "left")
    summary = {}
    for name, rows in fires.items():
        n = len(rows)
        w = sum(1 for r in rows if r["win"])
        hr = 100 * w / n if n else float("nan")
        units = w * (100 / 110) - (n - w)
        summary[name] = {"fires": n, "wins": w, "hit_pct": round(hr, 1),
                         "units": round(units, 2)}
        bt.add_row(name, str(n), str(w), f"{hr:.1f}%" if n else "—", f"{units:+.2f}")
    console.print(bt)
    (OUT / "honest_backtest.json").write_text(json.dumps(
        {"summary": summary, "fires": fires}, indent=2, default=str))
    console.print(f"[green]Wrote {OUT/'decay_surface.json'} and {OUT/'honest_backtest.json'}[/]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
