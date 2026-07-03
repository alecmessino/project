#!/usr/bin/env python3
"""Project 3 — distribution / tail calibration of Pinnacle team-run distributions.

Books price MEANS well; tails are harder. For each banked Pinnacle per-team run
distribution, once the game is FINAL we compute where the realized team runs fell (PIT)
and compare implied P(k runs) to realized frequency — focusing on the tails (0, 1, 8+).
A calibrated book ⇒ uniform PIT (mean ~0.5) and implied ≈ realized per bucket; systematic
deviation (e.g. an under-priced high tail) is a distribution-calibration error and does
NOT require any velocity signal.

    python the_third_turn/tail_calibration.py
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402

from calibrate_decay import _get  # noqa: E402
from shared_piping.team_map import resolve  # noqa: E402

console = Console()
PANEL = Path(__file__).resolve().parent / "output" / "team_total_panel.jsonl"
BUCKETS = ["0", "1", "2", "3", "4", "5", "6", "7", "8+"]


def realized(dates):
    """game_key -> {team_key: final runs} for FINAL games on the given dates."""
    out = {}
    for d in sorted(dates):
        try:
            sched = _get(f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={d}")
        except Exception:  # noqa: BLE001
            continue
        for dd in sched.get("dates", []):
            for g in dd.get("games", []):
                if g.get("status", {}).get("abstractGameState") != "Final":
                    continue
                aw = resolve(g["teams"]["away"]["team"]["name"])
                hm = resolve(g["teams"]["home"]["team"]["name"])
                ar, hr = g["teams"]["away"].get("score"), g["teams"]["home"].get("score")
                if aw and hm and ar is not None and hr is not None:
                    out[f"{aw}@{hm}"] = {aw: ar, hm: hr}
    return out


def bucket_of(runs):
    return str(runs) if runs < 8 else "8+"


def pit(probs, runs):
    """Probability integral transform (mid-PIT) of realized runs under the distribution."""
    below = sum(p for k, p in probs.items() if (8.5 if k.endswith("+") else float(k)) < runs)
    at = probs.get(bucket_of(runs), 0.0)
    return below + 0.5 * at


def main() -> int:
    if not PANEL.exists():
        console.print("[yellow]No team_total_panel yet.[/]")
        return 0
    rows = [json.loads(l) for l in PANEL.read_text().splitlines() if l.strip()]
    # latest distribution per (game, team)
    latest = {}
    for r in rows:
        latest[(r["game"], r["team"])] = r
    fin = realized({r["ts"][:10] for r in rows})

    graded = []
    for (game, team), r in latest.items():
        if game in fin and team in fin[game]:
            graded.append((r, fin[game][team]))
    console.rule(f"[bold]Project 3 · pregame tail calibration · {len(graded)} graded team-obs "
                 f"({len(fin)} final games banked)")
    if not graded:
        console.print("[dim]No banked distributions have a FINAL game yet — accumulates as games "
                      "complete. (Live in-play distributions will bank once the fresh runner catches "
                      "games in progress.)[/]")
        return 0

    pits = [pit(r["probs"], runs) for r, runs in graded]
    console.print(f"[dim]mean PIT = {sum(pits)/len(pits):.2f} (0.50 = calibrated; <0.5 book runs HIGH, "
                  f">0.5 book runs LOW). n={len(pits)}.[/]\n")

    t = Table(title="Implied vs realized per run bucket (tail focus)")
    for c in ("runs", "implied P", "realized freq", "Δ"):
        t.add_column(c, justify="left" if c == "runs" else "right")
    for b in BUCKETS:
        imp = sum(r["probs"].get(b, 0.0) for r, _ in graded) / len(graded)
        rea = sum(1 for _, runs in graded if bucket_of(runs) == b) / len(graded)
        flag = " [green]↑[/]" if rea - imp > 0.04 else (" [red]↓[/]" if imp - rea > 0.04 else "")
        t.add_row(b, f"{100*imp:.0f}%", f"{100*rea:.0f}%{flag}", f"{100*(rea-imp):+.0f}{flag}")
    console.print(t)
    console.print("[dim]↑ = realized more often than the book implied (under-priced bucket). Tiny n — "
                  "directional only; the point is the harness runs and grows nightly.[/]")

    (Path(PANEL).parent / "tail_calibration.json").write_text(json.dumps({
        "n": len(graded), "mean_pit": round(sum(pits) / len(pits), 3),
        "buckets": {b: {"implied": round(sum(r["probs"].get(b, 0.0) for r, _ in graded) / len(graded), 3),
                        "realized": round(sum(1 for _, runs in graded if bucket_of(runs) == b) / len(graded), 3)}
                    for b in BUCKETS}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
