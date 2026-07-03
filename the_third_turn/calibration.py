#!/usr/bin/env python3
"""Calibration engine core — measure market error, not win rate.

The framework (your Project 7): model P(outcome) vs sportsbook implied P(outcome) vs
realized frequency. Residual = model − implied; reliability curves bucket implied
probability and compare to observed frequency, conditioned on game state.

This file provides:
  A. MARKET side — implied_over()/implied_mean() from a banked Pinnacle team-run
     distribution row (ready for the live team_total_panel).
  B. DIAGNOSTICS — reliability_curve(), ece(), brier(), auc().
  C. A historical validation of the MODEL side (steps 1-2): is a velocity/TTOP model
     of P(team scores over K) calibrated, and does velocity add over a tier-only
     baseline? Leave-one-GAME-out. Also illustrates the residual in the high-velocity-
     drop state — where a tier-pricing market would be miscalibrated if it ignores velocity.

    python the_third_turn/calibration.py
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402

console = Console()


def fit_logistic(X, y, l2=1.0, iters=60):
    """Ridge logistic via numpy IRLS (inlined to avoid cross-module fragility)."""
    beta = np.zeros(X.shape[1])
    R = l2 * np.eye(X.shape[1])
    R[0, 0] = 0.0
    for _ in range(iters):
        p = 1 / (1 + np.exp(-np.clip(X @ beta, -30, 30)))
        W = p * (1 - p) + 1e-6
        grad = X.T @ (y - p) - R @ beta
        H = (X.T * W) @ X + R
        try:
            beta = beta + np.linalg.solve(H, grad)
        except np.linalg.LinAlgError:
            break
    return beta
HERE = Path(__file__).resolve().parent
FEAT = HERE / "output" / "features_cache.json"
OPEN_CENTROID = 8.5


# ---------- A. MARKET side (from a Pinnacle team-run distribution) ----------
def implied_over(probs: dict, line: float) -> float:
    """P(team runs > line) from a de-vigged run distribution ('0'..'7','8+')."""
    def val(k):
        return OPEN_CENTROID if k.endswith("+") else float(k)
    return sum(p for k, p in probs.items() if val(k) > line)


def implied_mean(probs: dict) -> float:
    def val(k):
        return OPEN_CENTROID if k.endswith("+") else float(k)
    return sum(val(k) * p for k, p in probs.items())


# ---------- B. Diagnostics ----------
def brier(preds, ys):
    return float(np.mean((np.array(preds) - np.array(ys)) ** 2))


def auc(preds, ys):
    preds, ys = np.array(preds), np.array(ys)
    pos, neg = preds[ys == 1], preds[ys == 0]
    if not len(pos) or not len(neg):
        return float("nan")
    return float(np.mean([np.mean(p > neg) + 0.5 * np.mean(p == neg) for p in pos]))


def reliability_curve(preds, ys, edges=(0, .3, .4, .5, .6, .7, 1.01)):
    preds, ys = np.array(preds), np.array(ys)
    rows = []
    for lo, hi in zip(edges, edges[1:]):
        m = (preds >= lo) & (preds < hi)
        if m.sum() == 0:
            continue
        rows.append((f"{lo:.2f}-{hi:.2f}", int(m.sum()),
                     float(preds[m].mean()), float(ys[m].mean())))
    return rows


def ece(preds, ys, edges=(0, .3, .4, .5, .6, .7, 1.01)):
    preds, ys = np.array(preds), np.array(ys)
    tot = 0.0
    for lo, hi in zip(edges, edges[1:]):
        m = (preds >= lo) & (preds < hi)
        if m.sum():
            tot += (m.sum() / len(preds)) * abs(preds[m].mean() - ys[m].mean())
    return float(tot)


# ---------- C. Historical model calibration (steps 1-2) ----------
def units():
    feat = json.loads(FEAT.read_text())
    out = []
    for r in feat.values():
        if r.get("final") is None:
            continue
        for runs, sk in ((r["final_away"], r["away_faces"]), (r["final_home"], r["home_faces"])):
            if sk["vel_drop_13"] is None:
                continue
            out.append({"runs": runs, "vd": float(sk["vel_drop_13"]),
                        "back": 1.0 if sk["tier"] == "Back" else 0.0,
                        "mid": 1.0 if sk["tier"] == "Mid" else 0.0})
    return out


def design(rows, cols, mean, std):
    X = np.ones((len(rows), len(cols) + 1))
    for j, c in enumerate(cols, 1):
        v = np.array([r[c] for r in rows])
        X[:, j] = (v - mean[c]) / std[c] if c == "vd" else v
    return X


def logo_oos(rows, cols, K):
    """Leave-one-game-out P(team runs > K). Games are pairs of consecutive units."""
    y = np.array([1.0 if r["runs"] > K else 0.0 for r in rows])
    mean = {"vd": float(np.mean([r["vd"] for r in rows]))}
    std = {"vd": float(np.std([r["vd"] for r in rows]) or 1.0)}
    oos = np.full(len(rows), np.nan)
    games = [(i, i + 1) for i in range(0, len(rows) - 1, 2)]
    for te in games:
        tr = [i for i in range(len(rows)) if i not in te]
        beta = fit_logistic(design([rows[i] for i in tr], cols, mean, std), y[tr], l2=1.0)
        Xte = design([rows[i] for i in te], cols, mean, std)
        oos[list(te)] = 1 / (1 + np.exp(-np.clip(Xte @ beta, -30, 30)))
    return y, oos


def main() -> int:
    rows = units()
    K = 4.5
    y = np.array([1.0 if r["runs"] > K else 0.0 for r in rows])
    console.rule(f"[bold]Calibration engine · model P(team scores >{K}) · {len(rows)} team-units")
    console.print(f"[dim]base rate over {K} = {100*y.mean():.0f}%. Leave-one-game-out. "
                  f"This validates the MODEL side; the market side plugs in the banked "
                  f"Pinnacle implied prob once live snapshots + outcomes accumulate.[/]\n")

    _, p_full = logo_oos(rows, ["vd", "back", "mid"], K)
    _, p_base = logo_oos(rows, ["back", "mid"], K)   # tier-only "market proxy"

    t = Table(title="Discrimination + calibration (out-of-sample)")
    for c in ("model", "Brier ↓", "AUC ↑", "ECE ↓"):
        t.add_column(c, justify="left" if c == "model" else "right")
    t.add_row("tier only (market proxy)", f"{brier(p_base,y):.3f}", f"{auc(p_base,y):.3f}", f"{ece(p_base,y):.3f}")
    t.add_row("tier + velocity drop", f"{brier(p_full,y):.3f}", f"{auc(p_full,y):.3f}", f"{ece(p_full,y):.3f}")
    console.print(t)

    rt = Table(title="Reliability — model P(over) vs observed frequency (tier+velocity)")
    for c in ("implied bucket", "n", "avg pred", "observed"):
        rt.add_column(c, justify="left" if c == "implied bucket" else "right")
    for lab, n, pred, obs in reliability_curve(p_full, y):
        flag = " [green]↑[/]" if obs - pred > 0.06 else (" [red]↓[/]" if pred - obs > 0.06 else "")
        rt.add_row(lab, str(n), f"{100*pred:.0f}%", f"{100*obs:.0f}%{flag}")
    console.print(rt)

    # residual illustration: where does velocity move the model away from a tier-only market?
    big = np.array([r["vd"] >= 2.0 for r in rows])
    console.print(f"\n[bold]Residual in the ≥2.0 mph velocity-drop state (n={int(big.sum())}):[/] "
                  f"tier-only market P={100*p_base[big].mean():.0f}% · model P={100*p_full[big].mean():.0f}% "
                  f"· realized={100*y[big].mean():.0f}% → residual "
                  f"[bold]{100*(y[big].mean()-p_base[big].mean()):+.0f} pts[/] vs a tier-pricing market")
    console.print("[dim]That residual is the calibration-engine output: if the live market prices like the "
                  "tier-only proxy (ignores velocity), it under-rates the Over in the velocity-cliff state by "
                  "~that much. The live Pinnacle distribution replaces the proxy to test if it ACTUALLY does.[/]")

    (HERE / "output" / "calibration.json").write_text(json.dumps({
        "n": len(rows), "K": K, "base_rate": round(float(y.mean()), 3),
        "brier_tier": round(brier(p_base, y), 3), "brier_full": round(brier(p_full, y), 3),
        "auc_tier": round(auc(p_base, y), 3), "auc_full": round(auc(p_full, y), 3),
        "ece_full": round(ece(p_full, y), 3),
        "residual_bigdrop_pts": round(float(100 * (y[big].mean() - p_base[big].mean())), 1)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
