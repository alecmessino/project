#!/usr/bin/env python3
"""Gradient replacement for the binary required-edge gate — fluid, not a glass ceiling.

Instead of firing iff ``live_line < fair − required_edge`` (a hard threshold where a
0.2-run wobble reshuffles the fires), fit a simple, interpretable logistic model of
``P(final Over the live line)`` on the CLIFF-context observations and ask the real
question: does a SOFT threshold on that probability isolate a genuinely +EV subset
out-of-sample?

Features are deliberately few (n≈560, small): drop size, TTO3-vs-TTO2, inning,
Back-tier, bullpen RA/9. Fitted with numpy IRLS + ridge. Every probability is honest
out-of-sample via LEAVE-ONE-GAME-OUT cross-validation (games, not rows, because a
game's half-innings share one final). Reuses the cliff tagging from
conditional_drop_reversion.walk_game.

    python the_third_turn/gradient_signal.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402

from calibrate_decay import FEED, _get  # noqa: E402
from conditional_drop_reversion import walk_game  # noqa: E402
from config import Constraints, EngineSettings  # noqa: E402
from investigate_line_edge import BREAKEVEN, WIN_PAYOUT, wilson_interval  # noqa: E402

console = Console()
HERE = Path(__file__).resolve().parent
TRAJ = HERE / "data" / "trajectories.jsonl"
CACHE = HERE / "output" / "gradient_cache.json"
LEAGUE_PEN_RA9 = 4.3
FEATURES = ["drop", "tto3", "inning", "back_tier", "pen_ra9"]
CONTINUOUS = {"drop", "inning", "pen_ra9"}


def build_rows(games, rules, elite, bullpen, tiers, refresh):
    cache = {} if refresh or not CACHE.exists() else json.loads(CACHE.read_text())
    rows = []
    for g in games:
        key = str(g["game_pk"])
        if key in cache:
            ctx = cache[key]
        else:
            try:
                feed = _get(FEED.format(pk=g["game_pk"]))
            except Exception:  # noqa: BLE001
                continue
            ctx = walk_game(feed, g["points"], g.get("start_time", ""),
                            rules, elite, bullpen, tiers)["context"]
            cache[key] = ctx
        for o in ctx:
            if o["push"]:
                continue
            rows.append({
                "game": int(g["game_pk"]), "drop": float(o["drop"]),
                "tto3": 1.0 if "TTO3" in (o.get("rule") or "") else 0.0,
                "inning": float(o["inning"]),
                "back_tier": 1.0 if o.get("tier") == "Back" else 0.0,
                "pen_ra9": float(o.get("pen_ra9") or LEAGUE_PEN_RA9),
                "y": 1.0 if o["win"] else 0.0,
            })
    CACHE.write_text(json.dumps(cache))
    return rows


def design(rows, mean, std):
    """Intercept + standardized-continuous / binary features."""
    X = np.ones((len(rows), len(FEATURES) + 1))
    for j, f in enumerate(FEATURES, start=1):
        col = np.array([r[f] for r in rows], dtype=float)
        if f in CONTINUOUS:
            col = (col - mean[f]) / std[f]
        X[:, j] = col
    y = np.array([r["y"] for r in rows], dtype=float)
    return X, y


def fit_logistic(X, y, l2=1.0, iters=60):
    d = X.shape[1]
    beta = np.zeros(d)
    R = l2 * np.eye(d)
    R[0, 0] = 0.0                                  # never penalize the intercept
    for _ in range(iters):
        p = 1.0 / (1.0 + np.exp(-np.clip(X @ beta, -30, 30)))
        W = p * (1 - p) + 1e-6
        grad = X.T @ (y - p) - R @ beta
        H = (X.T * W) @ X + R                       # −Hessian (pos. def.)
        try:
            beta = beta + np.linalg.solve(H, grad)
        except np.linalg.LinAlgError:
            break
    return beta


def moments(rows):
    mean, std = {}, {}
    for f in CONTINUOUS:
        col = np.array([r[f] for r in rows], dtype=float)
        mean[f], std[f] = float(col.mean()), float(col.std() or 1.0)
    return mean, std


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Gradient signal prototype")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--l2", type=float, default=1.0)
    args = ap.parse_args(argv)
    if not TRAJ.exists():
        console.print("[red]No trajectories.[/]")
        return 1
    games = [json.loads(l) for l in TRAJ.read_text().splitlines() if l.strip()]
    c = Constraints(use_decay_ratio=True, market_shrink_beta=0.75)
    s = EngineSettings()
    rows = build_rows(games, c.rules, c.bullpen_elite_ra9,
                      s.load_bullpen_quality(), s.load_starter_tiers(), args.refresh)
    console.rule(f"[bold]Gradient signal · {len(rows)} cliff-context obs · "
                 f"{len({r['game'] for r in rows})} games")
    base = np.mean([r["y"] for r in rows])
    console.print(f"[dim]Base Over rate (fire on every cliff) = {100*base:.1f}%  "
                  f"(breakeven {100*BREAKEVEN:.1f}%)[/]\n")

    # ---- interpretable full-sample coefficients (standardized) ----
    m, sd = moments(rows)
    Xf, yf = design(rows, m, sd)
    beta_full = fit_logistic(Xf, yf, l2=args.l2)
    ct = Table(title="Logistic coefficients (standardized; sign = pushes Over ↑/↓)")
    for col in ("feature", "coef", "reads as"):
        ct.add_column(col, justify="left" if col != "coef" else "right")
    reads = {"drop": "bigger drop", "tto3": "3rd time through (vs 2nd)",
             "inning": "later inning", "back_tier": "Back-end starter",
             "pen_ra9": "weaker bullpen"}
    ct.add_row("(intercept)", f"{beta_full[0]:+.3f}", "")
    for j, f in enumerate(FEATURES, start=1):
        arrow = "→ Over more likely" if beta_full[j] > 0 else "→ Over less likely"
        ct.add_row(f, f"{beta_full[j]:+.3f}", f"{reads[f]} {arrow}")
    console.print(ct)

    # ---- honest OOS probabilities via leave-one-GAME-out ----
    game_ids = sorted({r["game"] for r in rows})
    oos = np.full(len(rows), np.nan)
    idx_by_game = {g: [i for i, r in enumerate(rows) if r["game"] == g] for g in game_ids}
    for g in game_ids:
        te = idx_by_game[g]
        tr = [i for i in range(len(rows)) if rows[i]["game"] != g]
        m_tr, sd_tr = moments([rows[i] for i in tr])
        Xtr, ytr = design([rows[i] for i in tr], m_tr, sd_tr)
        beta = fit_logistic(Xtr, ytr, l2=args.l2)
        Xte, _ = design([rows[i] for i in te], m_tr, sd_tr)
        oos[te] = 1.0 / (1.0 + np.exp(-np.clip(Xte @ beta, -30, 30)))
    y = np.array([r["y"] for r in rows])

    # ---- does a soft threshold isolate a +EV subset? (OOS) ----
    st = Table(title="OOS threshold sweep — select fires where model P(Over) ≥ τ")
    for col in ("P(Over) ≥ τ", "fires", "Over hit %", "Wilson 95% CI", "units @ -110"):
        st.add_column(col, justify="left" if col.startswith("P(") else "right")
    sweep = []
    for tau in (0.50, BREAKEVEN, 0.55, 0.58, 0.60):
        sel = oos >= tau
        n = int(sel.sum())
        w = int(y[sel].sum())
        if n == 0:
            st.add_row(f"{tau:.3f}", "0", "—", "—", "—")
            continue
        hit = w / n
        lo, hi = wilson_interval(w, n)
        units = w * WIN_PAYOUT - (n - w)
        color = "[green]" if lo > BREAKEVEN else ("[yellow]" if hit > BREAKEVEN else "[red]")
        st.add_row(f"{tau:.3f}", str(n), f"{color}{100*hit:.1f}%[/]",
                   f"{100*lo:.0f}–{100*hi:.0f}%", f"{units:+.2f}")
        sweep.append({"tau": round(tau, 3), "fires": n, "wins": w,
                      "hit_pct": round(100 * hit, 1), "ci_low": round(100 * lo, 1),
                      "ci_high": round(100 * hi, 1), "units": round(units, 2)})
    console.print(st)
    console.print("[dim]Green = CI lower bound clears breakeven (real edge); yellow = point "
                  "estimate clears but CI doesn't; red = below breakeven.[/]")

    (HERE / "output" / "gradient_signal.json").write_text(json.dumps({
        "n_obs": len(rows), "base_over_pct": round(100 * base, 1),
        "coefficients": {f: round(float(beta_full[j]), 3)
                         for j, f in enumerate(["intercept"] + FEATURES)},
        "oos_sweep": sweep}, indent=2))
    console.print(f"\n[green]Wrote output/gradient_signal.json[/]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
