#!/usr/bin/env python3
"""Vector 3 — live team totals vs full-game totals, plus the velocity mechanism.

Two honest tests (we have no historical team-total LINES, so no faked P&L):

  A. MECHANISM — does the targeted starter's tier / TTO velocity drop actually predict
     the runs the facing team scores? If a Back-tier starter shedding velocity by the
     3rd time through reliably gets hit, that's the physical edge, cleanly isolated.

  B. SIGNAL-TO-NOISE — the core Vector 3 claim: a full-game Over pollutes our variable
     with the OTHER pitcher's line. Does conditioning on "facing a vulnerable starter"
     move the facing team's runs by a bigger effect size (Cohen's d) than it moves the
     full-game total? If yes, the team total is the sharper instrument and it's worth
     capturing live team-total lines going forward.

    python the_third_turn/v3_team_velocity.py
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402

from features import CACHE, build  # noqa: E402

console = Console()
VULN = {"Mid", "Back"}


def cohen_d(a, b):
    if len(a) < 2 or len(b) < 2:
        return None
    sa, sb = statistics.pstdev(a), statistics.pstdev(b)
    pooled = (((len(a) - 1) * sa**2 + (len(b) - 1) * sb**2) / (len(a) + len(b) - 2)) ** 0.5 or 1.0
    return (statistics.mean(a) - statistics.mean(b)) / pooled


def main() -> int:
    cache = build()
    units, games = [], []
    for r in cache.values():
        if r.get("final") is None:
            continue
        games.append(r)
        for facing_runs, sk in ((r["final_away"], r["away_faces"]),
                                (r["final_home"], r["home_faces"])):
            units.append({"tier": sk["tier"], "vdrop": sk["vel_drop_13"],
                          "ra": sk["runs_allowed"], "exit": sk["exit_inning"],
                          "runs": facing_runs})

    console.rule(f"[bold]Vector 3 · {len(games)} games · {len(units)} (team vs starter) units")

    # ---- A. MECHANISM: facing-team runs by velocity-drop bucket ----
    t = Table(title="A. Does the starter's TTO velocity drop predict the facing team's runs?")
    for c in ("velo drop TTO1→3", "units", "avg facing runs", "avg ER off starter", "% starter KO'd ≤5th"):
        t.add_column(c, justify="left" if c.startswith("velo") else "right")
    buckets = [("< 0 (gained)", -99, 0), ("0–1 mph", 0, 1), ("1–2 mph", 1, 2),
               ("2–3 mph", 2, 3), ("3+ mph", 3, 99)]
    for label, lo, hi in buckets:
        sub = [u for u in units if u["vdrop"] is not None and lo <= u["vdrop"] < hi]
        if not sub:
            t.add_row(label, "0", "—", "—", "—"); continue
        ko = sum(1 for u in sub if u["exit"] is not None and u["exit"] <= 5) / len(sub)
        t.add_row(label, str(len(sub)), f"{statistics.mean(u['runs'] for u in sub):.2f}",
                  f"{statistics.mean(u['ra'] for u in sub):.2f}", f"{100*ko:.0f}%")
    console.print(t)

    # by tier, for reference
    t2 = Table(title="…and by starter tier")
    for c in ("tier", "units", "avg facing runs", "avg velo drop"):
        t2.add_column(c, justify="left" if c == "tier" else "right")
    for tier in ("Ace", "Mid", "Back", "Unknown"):
        sub = [u for u in units if u["tier"] == tier]
        vs = [u["vdrop"] for u in sub if u["vdrop"] is not None]
        if sub:
            t2.add_row(tier, str(len(sub)), f"{statistics.mean(u['runs'] for u in sub):.2f}",
                       f"{statistics.mean(vs):+.2f}" if vs else "—")
    console.print(t2)

    # ---- B. SIGNAL-TO-NOISE: team total vs full-game total ----
    # effect of "facing a vulnerable starter (Mid/Back + >=1mph drop)" on the two targets
    def vulnerable(sk):
        return sk["tier"] in VULN and (sk["vel_drop_13"] or 0) >= 1.0

    team_hit = [u["runs"] for u in units if u["tier"] in VULN and (u["vdrop"] or 0) >= 1.0]
    team_non = [u["runs"] for u in units if not (u["tier"] in VULN and (u["vdrop"] or 0) >= 1.0)]
    game_hit = [g["final"] for g in games if vulnerable(g["away_faces"]) or vulnerable(g["home_faces"])]
    game_non = [g["final"] for g in games if not (vulnerable(g["away_faces"]) or vulnerable(g["home_faces"]))]

    t3 = Table(title="B. Signal-to-noise: which total does 'vulnerable starter' move more?")
    for c in ("target", "n vuln", "mean vuln", "n rest", "mean rest", "Δ mean", "Cohen's d"):
        t3.add_column(c, justify="left" if c == "target" else "right")
    for name, hit, non in (("TEAM total (facing team runs)", team_hit, team_non),
                           ("FULL-GAME total", game_hit, game_non)):
        d = cohen_d(hit, non)
        t3.add_row(name, str(len(hit)), f"{statistics.mean(hit):.2f}", str(len(non)),
                   f"{statistics.mean(non):.2f}", f"{statistics.mean(hit)-statistics.mean(non):+.2f}",
                   f"{d:+.2f}" if d is not None else "—")
    console.print(t3)
    console.print("\n[dim]A: if avg facing runs climbs monotonically with velocity drop, the mechanism "
                  "is real. B: a bigger |Cohen's d| for the TEAM total means isolating it strips the "
                  "opposing-pitcher noise — justifying live team-total capture. No P&L here: real "
                  "team-total lines don't exist in our history (game_line/2 would bias the vuln side up).[/]")

    (Path(CACHE).parent / "v3_team_velocity.json").write_text(json.dumps({
        "mechanism_by_vdrop": [{"band": b[0], "n": len([u for u in units if u["vdrop"] is not None and b[1] <= u["vdrop"] < b[2]]),
                                "avg_runs": round(statistics.mean([u["runs"] for u in units if u["vdrop"] is not None and b[1] <= u["vdrop"] < b[2]]), 2)
                                if [u for u in units if u["vdrop"] is not None and b[1] <= u["vdrop"] < b[2]] else None} for b in buckets],
        "d_team": cohen_d(team_hit, team_non), "d_game": cohen_d(game_hit, game_non)},
        indent=2, default=lambda x: x))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
