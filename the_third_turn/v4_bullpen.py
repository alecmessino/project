#!/usr/bin/env python3
"""V4 analysis — does a gassed bullpen amplify the velocity-cliff scoring window?

Historical preview (we bet nothing yet — no live team-total lines): join the trailing-
3-day bullpen workload to the game features and ask two things about the RELEVANT pen —
the OPPOSING team's, since that's who pitches to the team we care about:

  A. Baseline — do facing-team runs rise with the opposing pen's recent workload?
  B. The multiplier — among games where a Mid/Back starter is chased early (the TTO
     cliff fires), does the facing team score MORE when the pen behind him is already
     gassed vs rested? That interaction is the whole V4 thesis.

Facing-team runs stand in for the (not-yet-captured) team total. Small cells — CIs/counts
shown, thresholds picked by the data.

    python the_third_turn/v4_bullpen.py
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402

console = Console()
HERE = Path(__file__).resolve().parent
FEAT = HERE / "output" / "features_cache.json"
BULL = HERE / "output" / "bullpen_cache.json"
VULN = {"Mid", "Back"}


def units():
    feat = json.loads(FEAT.read_text())
    bull = json.loads(BULL.read_text())
    out = []
    for r in feat.values():
        if r.get("final") is None:
            continue
        pk = r["game_pk"]
        # away team scores vs the HOME pitching -> HOME pen fatigue is the relevant one
        for facing_runs, sk, pen_key in (
            (r["final_away"], r["away_faces"], f"{pk}:home"),
            (r["final_home"], r["home_faces"], f"{pk}:away"),
        ):
            pen = bull.get(pen_key)
            if not pen or "pen_pitches_3d" not in pen:
                continue
            out.append({"runs": facing_runs, "tier": sk["tier"], "vdrop": sk["vel_drop_13"],
                        "exit": sk["exit_inning"], "pen3d": pen["pen_pitches_3d"],
                        "gassed": pen["gassed_1d"], "heavy": pen["heavy_3d"]})
    return out


def summary(rows):
    if not rows:
        return "0", "—"
    return str(len(rows)), f"{statistics.mean(r['runs'] for r in rows):.2f}"


def main() -> int:
    rows = units()
    if not rows:
        console.print("[yellow]bullpen cache not ready yet — run bullpen_usage.py first.[/]")
        return 0
    pens = sorted(r["pen3d"] for r in rows)
    lo_c, hi_c = pens[len(pens) // 3], pens[2 * len(pens) // 3]      # data-driven terciles
    console.rule(f"[bold]V4 · bullpen fatigue × facing-team runs · {len(rows)} team-units")
    console.print(f"[dim]pen_pitches_3d terciles: low ≤{lo_c} · high >{hi_c}. "
                  f"'facing runs' = runs the team scored off the opposing starter+pen.[/]\n")

    # A. baseline: facing runs by opposing-pen workload tercile
    t = Table(title="A. Facing-team runs by OPPOSING bullpen's trailing-3d workload")
    for c in ("pen workload", "units", "avg facing runs"):
        t.add_column(c, justify="left" if c == "pen workload" else "right")
    t.add_row(f"low (≤{lo_c}p)", *summary([r for r in rows if r["pen3d"] <= lo_c]))
    t.add_row("mid", *summary([r for r in rows if lo_c < r["pen3d"] <= hi_c]))
    t.add_row(f"high (>{hi_c}p)", *summary([r for r in rows if r["pen3d"] > hi_c]))
    console.print(t)

    # B. the multiplier: cliff chased (Mid/Back + exit<=5) split by pen fatigue
    cliff = [r for r in rows if r["tier"] in VULN and r["exit"] is not None and r["exit"] <= 5]
    t2 = Table(title="B. Exhaustion multiplier — Mid/Back starter chased ≤5th, by pen state")
    for c in ("pen behind him", "units", "avg facing runs"):
        t2.add_column(c, justify="left" if c == "pen behind him" else "right")
    t2.add_row("rested (0 gassed arms)", *summary([r for r in cliff if r["gassed"] == 0]))
    t2.add_row("≥1 gassed arm (≥30p yest)", *summary([r for r in cliff if r["gassed"] >= 1]))
    t2.add_row(f"high workload (>{hi_c}p/3d)", *summary([r for r in cliff if r["pen3d"] > hi_c]))
    t2.add_row(f"low workload (≤{lo_c}p/3d)", *summary([r for r in cliff if r["pen3d"] <= lo_c]))
    console.print(t2)
    console.print("\n[dim]V4 thesis holds if 'chased + gassed/high-workload pen' scores meaningfully more "
                  "than 'chased + rested pen'. Watch the unit counts — cliff cells are thin.[/]")

    (HERE / "output" / "v4_bullpen.json").write_text(json.dumps({
        "n": len(rows), "cliff_n": len(cliff),
        "cliff_gassed": summary([r for r in cliff if r["gassed"] >= 1])[1],
        "cliff_rested": summary([r for r in cliff if r["gassed"] == 0])[1]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
