#!/usr/bin/env python3
"""Sweep the trigger's line-edge threshold: absolute runs vs % of line vs z-normalized.

Answers "should we gate on % edge instead of absolute runs?" empirically. Reads a
simulation ledger produced with ``simulate_execution.py --edge-floor -99`` (every
state-matched window recorded with its raw edge, no gate) and evaluates, for each
threshold family and cutoff:

    fires · fires/game-day · hit rate (Over) · ROI/unit at -110

Families (edge = fair - line):
    runs : edge >= t                      (current behavior, t in runs)
    pct  : edge / line >= t               (scales with the run environment)
    z    : edge / sqrt(line) >= t         (scales with outcome σ — value ∝ Φ(edge/σ),
                                           σ ~ sqrt(expected runs))

    python the_third_turn/sweep_edge_thresholds.py
    python the_third_turn/sweep_edge_thresholds.py --ledger output/simulation_ledger.jsonl
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402

console = Console()
HERE = Path(__file__).resolve().parent
OUT = HERE / "output"

BREAKEVEN = 0.5238   # -110 both sides
FAMILIES = {
    "runs": ([0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0], lambda e, line: e),
    "pct":  ([0.0, 0.03, 0.05, 0.07, 0.10, 0.15], lambda e, line: e / line if line else 0.0),
    "z":    ([0.0, 0.10, 0.15, 0.20, 0.25, 0.35], lambda e, line: e / math.sqrt(line) if line > 0 else 0.0),
}


def load(path: Path) -> pd.DataFrame:
    rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    df = pd.DataFrame(rows)
    df = df[df["trigger_type"].isin(["CONFIRM", "ARM"])]          # tto rules only
    df = df[df["outcome"].isin(["Over", "Under"])].copy()          # decided games
    df["edge"] = pd.to_numeric(df["edge"], errors="coerce")
    df["live_total"] = pd.to_numeric(df["live_total"], errors="coerce")
    return df.dropna(subset=["edge", "live_total"])


def roi_per_unit(hit_rate: float) -> float:
    """Profit per 1u staked at -110: win +0.909, lose -1."""
    return hit_rate * (100 / 110) - (1 - hit_rate)


def sweep(df: pd.DataFrame, n_game_days: int) -> pd.DataFrame:
    rows = []
    for fam, (cuts, metric) in FAMILIES.items():
        vals = df.apply(lambda r: metric(r["edge"], r["live_total"]), axis=1)
        for t in cuts:
            sub = df[vals >= t]
            if len(sub) < 30:
                continue
            hr = float((sub["outcome"] == "Over").mean())
            rows.append({
                "family": fam, "threshold": t, "fires": len(sub),
                "fires_per_day": round(len(sub) / n_game_days, 2) if n_game_days else 0,
                "hit_rate_%": round(hr * 100, 1),
                "roi_per_unit_%": round(roi_per_unit(hr) * 100, 1),
            })
    return pd.DataFrame(rows)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Edge-threshold sweep (runs vs pct vs z)")
    ap.add_argument("--ledger", default=str(OUT / "simulation_ledger.jsonl"))
    args = ap.parse_args(argv)

    df = load(Path(args.ledger))
    if df.empty:
        console.print("[red]No decided CONFIRM/ARM rows in the ledger — run "
                      "simulate_execution.py --edge-floor -99 first.[/]")
        return 1
    n_days = df["ts"].astype(str).str[:10].nunique()
    console.rule(f"[bold]Edge-threshold sweep · {len(df)} decided fires · {n_days} game-days")

    rep = sweep(df, n_days)
    rep.to_csv(OUT / "edge_threshold_sweep.csv", index=False)

    table = Table(title="Hit rate & ROI by edge-gate family (−110 breakeven = 52.4%)")
    for col in rep.columns:
        table.add_column(str(col), justify="right" if col != "family" else "left")
    prev_fam = None
    for _, r in rep.iterrows():
        if prev_fam and r["family"] != prev_fam:
            table.add_section()
        prev_fam = r["family"]
        table.add_row(r["family"], f'{r["threshold"]:g}', str(r["fires"]),
                      f'{r["fires_per_day"]:g}', f'{r["hit_rate_%"]}', f'{r["roi_per_unit_%"]}')
    console.print(table)

    # headline: best ROI per family at meaningful volume (>= 1 fire/day)
    console.rule("[bold]Best cut per family (volume ≥ 1 fire/day)")
    for fam in FAMILIES:
        sub = rep[(rep["family"] == fam) & (rep["fires_per_day"] >= 1.0)]
        if len(sub):
            best = sub.loc[sub["roi_per_unit_%"].idxmax()]
            console.print(f"  {fam:5} ≥ {best['threshold']:g} → {best['hit_rate_%']}% hit, "
                          f"ROI {best['roi_per_unit_%']}%/u on {best['fires']} fires "
                          f"({best['fires_per_day']}/day)")
    console.print(f"[green]Wrote {OUT/'edge_threshold_sweep.csv'}[/]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
