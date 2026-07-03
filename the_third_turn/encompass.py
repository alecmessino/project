#!/usr/bin/env python3
"""Project G — forecast encompassing: does the sportsbook already contain our features?

At each half-inning snapshot of each game:
    Y = final total − runs so far        (actual remaining game runs)
    B = live game total − runs so far    (market-implied remaining runs)
    X = candidate features               (velocity, tier, bullpen, TTO, pitch count,
                                          weather, park, inning)
So  Y − B = final − live line = the MARKET'S FORECAST ERROR.

Three models (leave-one-game-out): Y~B, Y~X, Y~B+X. If Y~B+X ≈ Y~B, the book encompasses
our features (they're redundant). The sharpest single test is regressing the book error
(Y − B) on X: if X predicts the error, the book underweights X — the start of an edge.

    python the_third_turn/encompass.py
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402

from calibrate_decay import FEED, _get, line_lookup  # noqa: E402
from config import EngineSettings  # noqa: E402
from features import parse_weather, park_factor  # noqa: E402

console = Console()
HERE = Path(__file__).resolve().parent
TRAJ = HERE / "data" / "trajectories.jsonl"
CACHE = HERE / "output" / "encompass_cache.json"
FEATS = ["vdrop", "back", "mid", "pen", "tto", "pc", "temp", "wind", "park", "inning"]


def snapshots(feed, points, tiers, bullpen):
    gd, ld = feed.get("gameData", {}), feed.get("liveData", {})
    box = ld.get("boxscore", {}).get("teams", {})
    starter = {s: (box.get(s, {}).get("pitchers", []) or [None])[0] for s in ("away", "home")}
    fn = line_lookup(points)
    wx, pf = parse_weather(gd), park_factor(gd)
    away = (gd.get("teams", {}).get("away", {}) or {})
    teamname = {"away": away.get("abbreviation")}
    pen = {"away": bullpen.get((gd.get("teams", {}).get("away", {}) or {}).get("abbreviation")),
           "home": bullpen.get((gd.get("teams", {}).get("home", {}) or {}).get("abbreviation"))}

    bf, pit, speeds = defaultdict(int), defaultdict(int), defaultdict(list)
    total = 0
    fa = fh = 0
    plays = ld.get("plays", {}).get("allPlays", [])
    for p in plays:
        r = p.get("result", {})
        if r.get("awayScore") is not None:
            fa, fh = r["awayScore"], r["homeScore"]
    final = fa + fh

    out, seen = [], set()
    for play in plays:
        about, match, res = play.get("about", {}), play.get("matchup", {}), play.get("result", {})
        if res.get("type") != "atBat" or not match.get("batter"):
            continue
        inning, is_top = int(about.get("inning") or 0), bool(about.get("isTopInning"))
        pit_side = "home" if is_top else "away"
        pid = (match.get("pitcher") or {}).get("id")
        key = (inning, is_top)
        line = fn(about.get("startTime") or "")
        if key not in seen and inning <= 8 and line is not None:
            seen.add(key)
            sp = speeds.get(pid, [])
            vdrop = (sum(sp[:15]) / 15 - sum(sp[-10:]) / min(10, len(sp))) if len(sp) >= 18 else 0.0
            tier = tiers.get(str(starter[pit_side]))
            out.append({
                "Y": float(final - total), "B": float(line - total),
                "vdrop": round(vdrop, 2), "back": 1.0 if tier == "Back" else 0.0,
                "mid": 1.0 if tier == "Mid" else 0.0, "pen": float(pen[pit_side] or 4.3),
                "tto": float(bf[pid] // 9 + 1), "pc": float(pit[pid]),
                "temp": float(wx["temp"] or 72), "wind": float(wx["wind_signed"]),
                "park": float(pf), "inning": float(inning),
            })
        # advance state
        bf[pid] += 1
        for e in play.get("playEvents", []):
            s = (e.get("pitchData") or {}).get("startSpeed")
            if s:
                speeds[pid].append(s)
        pit[pid] = pit[pid] + len(play.get("playEvents", []) or [1])
        aw, hm = res.get("awayScore"), res.get("homeScore")
        if aw is not None:
            total = aw + hm
    for o in out:
        o["game"] = int(gd.get("game", {}).get("pk") or feed.get("gamePk") or 0)
    return out


def build(refresh=False):
    if CACHE.exists() and not refresh:
        return json.loads(CACHE.read_text())
    games = [json.loads(l) for l in TRAJ.read_text().splitlines() if l.strip()]
    s = EngineSettings()
    tiers, bullpen = s.load_starter_tiers(), s.load_bullpen_quality()
    rows = []
    for g in games:
        try:
            feed = _get(FEED.format(pk=g["game_pk"]))
        except Exception:  # noqa: BLE001
            continue
        rows += snapshots(feed, g["points"], tiers, bullpen)
    CACHE.write_text(json.dumps(rows))
    return rows


def logo_lin(rows, cols, target="Y", l2=1.0):
    y = np.array([r[target] for r in rows])
    cont = [c for c in cols if c not in ("back", "mid")]
    mean = {c: float(np.mean([r[c] for r in rows])) for c in cont}
    std = {c: float(np.std([r[c] for r in rows]) or 1.0) for c in cont}

    def design(rs):
        X = np.ones((len(rs), len(cols) + 1))
        for j, c in enumerate(cols, 1):
            v = np.array([r[c] for r in rs], float)
            X[:, j] = (v - mean[c]) / std[c] if c in cont else v
        return X
    pred = np.full(len(rows), np.nan)
    by_game = defaultdict(list)
    for i, r in enumerate(rows):
        by_game[r["game"]].append(i)
    for g, idx in by_game.items():
        tr = [i for i in range(len(rows)) if rows[i]["game"] != g]
        X = design([rows[i] for i in tr])
        R = l2 * np.eye(X.shape[1]); R[0, 0] = 0
        beta = np.linalg.solve(X.T @ X + R, X.T @ y[tr])
        pred[idx] = design([rows[i] for i in idx]) @ beta
    return y, pred, mean, std


def r2(y, p):
    return 1 - np.sum((y - p) ** 2) / np.sum((y - y.mean()) ** 2)


def main() -> int:
    rows = build()
    console.rule(f"[bold]Project G · forecast encompassing · {len(rows)} snapshots "
                 f"· {len({r['game'] for r in rows})} games")
    y = np.array([r["Y"] for r in rows])
    B = np.array([r["B"] for r in rows])
    console.print(f"[dim]Y=actual remaining runs (mean {y.mean():.2f}); B=market-implied remaining. "
                  f"Market alone: R²(Y~B)... does adding our features beat it?[/]\n")

    _, p_b, _, _ = logo_lin(rows, ["B"])
    _, p_x, _, _ = logo_lin(rows, FEATS)
    _, p_bx, _, _ = logo_lin(rows, ["B"] + FEATS)
    t = Table(title="Three forecasts (leave-one-game-out)")
    for c in ("model", "MAE ↓", "R² ↑"):
        t.add_column(c, justify="left" if c == "model" else "right")
    for name, p in (("M1: market only  (Y ~ B)", p_b), ("M2: our features (Y ~ X)", p_x),
                    ("M3: market + features (Y ~ B+X)", p_bx)):
        t.add_row(name, f"{np.mean(np.abs(y-p)):.3f}", f"{r2(y,p):.3f}")
    console.print(t)
    gain = r2(y, p_bx) - r2(y, p_b)
    console.print(f"[bold]Encompassing gain: R²(M3) − R²(M1) = {gain:+.4f}[/]  "
                  f"({'features add nothing → book encompasses them' if gain < 0.005 else 'features add signal beyond the market'})")

    # the sharp test: does anything predict the book error (Y - B)?
    err_rows = [dict(r, ERR=r["Y"] - r["B"]) for r in rows]
    _, p_err, mean, std = logo_lin(err_rows, FEATS, target="ERR")
    e = np.array([r["ERR"] for r in err_rows])
    console.print(f"\n[bold]Book error (Y−B):[/] mean {e.mean():+.2f}, sd {e.std():.2f} · "
                  f"features predict it with OOS R² = [bold]{r2(e,p_err):+.3f}[/] "
                  f"({'≈0 → nothing predicts the error' if r2(e,p_err) < 0.01 else 'predictable → candidate edge'})")
    # standardized coefficients of ERR ~ X on the full sample (which features tug the error)
    cont = [c for c in FEATS if c not in ("back", "mid")]
    X = np.ones((len(err_rows), len(FEATS) + 1))
    for j, c in enumerate(FEATS, 1):
        v = np.array([r[c] for r in err_rows], float)
        X[:, j] = (v - mean[c]) / std[c] if c in cont else v
    beta = np.linalg.solve(X.T @ X + np.eye(X.shape[1]), X.T @ e)
    ct = Table(title="Which features tug the book error? (standardized β on Y−B)")
    for c in ("feature", "β"):
        ct.add_column(c, justify="left" if c == "feature" else "right")
    for f, b in sorted(zip(FEATS, beta[1:]), key=lambda kv: -abs(kv[1])):
        ct.add_row(f, f"{b:+.3f}")
    console.print(ct)

    # E+ : per-feature incremental value beyond the market (Y ~ B+Xi vs Y ~ B).
    # Tests each feature against B individually, so two proxies for the same state can't
    # hide each other (the multivariate G test's blind spot).
    base = r2(y, p_b)
    it = Table(title="E+ · each feature's incremental R² beyond the market (Y~B+Xi − Y~B)")
    for c in ("feature", "ΔR² (out-of-sample)"):
        it.add_column(c, justify="left" if c == "feature" else "right")
    incs = []
    for f in FEATS:
        _, pf_, _, _ = logo_lin(rows, ["B", f])
        incs.append((f, r2(y, pf_) - base))
    for f, dd in sorted(incs, key=lambda kv: -kv[1]):
        flag = " [green]← adds signal[/]" if dd > 0.003 else ""
        it.add_row(f, f"{dd:+.4f}{flag}")
    console.print(it)
    console.print("[dim]All ΔR² ≤ 0 ⇒ every feature is individually encompassed by the market too.[/]")

    (HERE / "output" / "encompass.json").write_text(json.dumps({
        "incremental": {f: round(float(d), 4) for f, d in incs},
        "n": len(rows), "r2_market": round(float(r2(y, p_b)), 3),
        "r2_features": round(float(r2(y, p_x)), 3), "r2_both": round(float(r2(y, p_bx)), 3),
        "encompass_gain": round(float(gain), 4), "err_r2": round(float(r2(e, p_err)), 3),
        "err_mean": round(float(e.mean()), 3)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
