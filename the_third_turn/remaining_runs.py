#!/usr/bin/env python3
"""Expected remaining team runs — the model side of the calibration residual (no velocity).

At the start of each half-inning (clean base-out state) we snapshot the game state and
the runs the BATTING team scores from that point to the end. We then fit E[remaining |
state] on literature-supported predictors — game progress (innings remaining), continuous
times-through-order, pitch count, starter-still-in, opposing tier, bullpen quality, score
differential — and test whether the FATIGUE terms (TTO, pitch count, starter-in) add
predictive power over a progress+tier+bullpen+score baseline, out-of-sample.

If fatigue carries incremental, calibrated signal, this is the model side of
`residual = model_remaining − market_implied_remaining` for the live engine. (Base-out/
RE24 is constant at inning start, so it's a per-PA v2 enrichment.)

    python the_third_turn/remaining_runs.py
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

from calibrate_decay import FEED, _get  # noqa: E402
from config import EngineSettings  # noqa: E402
from shared_piping.team_map import resolve  # noqa: E402

console = Console()
HERE = Path(__file__).resolve().parent
TRAJ = HERE / "data" / "trajectories.jsonl"
CACHE = HERE / "output" / "remaining_snapshots.json"
LEAGUE_PEN = 4.3


def game_snapshots(feed, tiers, bullpen):
    gd, ld = feed.get("gameData", {}), feed.get("liveData", {})
    away = resolve(gd.get("teams", {}).get("away", {}).get("name", "")) or "?"
    home = resolve(gd.get("teams", {}).get("home", {}).get("name", "")) or "?"
    box = ld.get("boxscore", {}).get("teams", {})
    starter = {s: (box.get(s, {}).get("pitchers", []) or [None])[0] for s in ("away", "home")}
    bfaced: dict = defaultdict(int)     # batters faced by each pitcher
    pitches: dict = defaultdict(int)    # pitches thrown by each pitcher
    runs = {"away": 0, "home": 0}
    snaps, seen = [], set()
    plays = ld.get("plays", {}).get("allPlays", [])
    # final team runs
    fa = fh = 0
    for p in plays:
        r = p.get("result", {})
        if r.get("awayScore") is not None:
            fa, fh = r["awayScore"], r["homeScore"]
    final = {"away": fa, "home": fh}

    for play in plays:
        about, match, res = play.get("about", {}), play.get("matchup", {}), play.get("result", {})
        if res.get("type") != "atBat" or not match.get("batter"):
            continue
        inning = int(about.get("inning") or 0)
        is_top = bool(about.get("isTopInning"))
        bat = "away" if is_top else "home"
        pit = "home" if is_top else "away"
        pid = (match.get("pitcher") or {}).get("id")
        key = (inning, is_top)
        if key not in seen and inning <= 9:               # snapshot BEFORE this half's first PA
            seen.add(key)
            snaps.append({
                "inn_remaining": max(9 - inning + 1, 1),
                "tto": bfaced[pid] // 9 + 1,               # continuous times-through-order
                "pitches": float(pitches[pid]),
                "starter_on": 1.0 if pid == starter[pit] else 0.0,
                "back": 1.0 if tiers.get(str(starter[pit])) == "Back" else 0.0,
                "mid": 1.0 if tiers.get(str(starter[pit])) == "Mid" else 0.0,
                "pen": float(bullpen.get(pit_team(pit, away, home), LEAGUE_PEN)),
                "score_diff": float(runs[bat] - runs[pit]),
                "remaining": float(final[bat] - runs[bat]),
            })
        bfaced[pid] += 1
        pitches[pid] += len(play.get("playEvents", []) or [1])
        aw, hm = res.get("awayScore"), res.get("homeScore")
        if aw is not None:
            runs["away"], runs["home"] = aw, hm
    return snaps


def pit_team(side, away, home):
    return home if side == "home" else away


def build(refresh=False):
    if CACHE.exists() and not refresh:
        return json.loads(CACHE.read_text())
    games = [json.loads(l) for l in TRAJ.read_text().splitlines() if l.strip()]
    s = EngineSettings()
    tiers, bullpen = s.load_starter_tiers(), s.load_bullpen_quality()
    out = []
    for g in games:
        try:
            feed = _get(FEED.format(pk=g["game_pk"]))
        except Exception:  # noqa: BLE001
            continue
        for snap in game_snapshots(feed, tiers, bullpen):
            snap["game"] = g["game_pk"]
            out.append(snap)
    CACHE.write_text(json.dumps(out))
    return out


BASE = ["inn_remaining", "back", "mid", "pen", "score_diff"]
FATIGUE = ["tto", "pitches", "starter_on"]


def design(rows, cols, mean, std):
    X = np.ones((len(rows), len(cols) + 1))
    for j, c in enumerate(cols, 1):
        v = np.array([r[c] for r in rows], float)
        X[:, j] = (v - mean[c]) / std[c] if c in ("inn_remaining", "pen", "score_diff", "tto", "pitches") else v
    return X


def logo(rows, cols, l2=1.0):
    y = np.array([r["remaining"] for r in rows])
    mean = {c: float(np.mean([r[c] for r in rows])) for c in cols}
    std = {c: float(np.std([r[c] for r in rows]) or 1.0) for c in cols}
    pred = np.full(len(rows), np.nan)
    by_game = defaultdict(list)
    for i, r in enumerate(rows):
        by_game[r["game"]].append(i)
    for g, idx in by_game.items():
        tr = [i for i in range(len(rows)) if rows[i]["game"] != g]
        X = design([rows[i] for i in tr], cols, mean, std)
        R = l2 * np.eye(X.shape[1]); R[0, 0] = 0
        beta = np.linalg.solve(X.T @ X + R, X.T @ y[tr])
        pred[idx] = np.clip(design([rows[i] for i in idx], cols, mean, std) @ beta, 0, None)
    return y, pred


def mae(y, p):
    return float(np.mean(np.abs(y - p)))


def main() -> int:
    rows = build()
    console.rule(f"[bold]Expected remaining team runs · {len(rows)} half-inning snapshots "
                 f"· {len({r['game'] for r in rows})} games")
    console.print(f"[dim]mean remaining = {np.mean([r['remaining'] for r in rows]):.2f}. Leave-one-game-out. "
                  f"Does pitcher FATIGUE (TTO, pitch count, starter-in) beat a progress+tier+bullpen+score "
                  f"baseline at predicting rest-of-game team runs?[/]\n")

    y, p_base = logo(rows, BASE)
    _, p_full = logo(rows, BASE + FATIGUE)
    naive = np.full(len(y), y.mean())

    t = Table(title="Out-of-sample fit (MAE ↓, lower = better)")
    for c in ("model", "MAE", "R² vs naive"):
        t.add_column(c, justify="left" if c == "model" else "right")
    def r2(p):
        return 1 - np.sum((y - p) ** 2) / np.sum((y - y.mean()) ** 2)
    t.add_row("naive (grand mean)", f"{mae(y,naive):.3f}", "0.000")
    t.add_row("baseline: progress+tier+pen+score", f"{mae(y,p_base):.3f}", f"{r2(p_base):.3f}")
    t.add_row("+ fatigue (TTO, pitches, starter-in)", f"{mae(y,p_full):.3f}", f"{r2(p_full):.3f}")
    console.print(t)

    rt = Table(title="Calibration — predicted vs realized remaining runs (full model)")
    for c in ("pred bucket", "n", "avg pred", "avg realized"):
        rt.add_column(c, justify="left" if c == "pred bucket" else "right")
    edges = [0, 1, 2, 3, 4, 20]
    for lo, hi in zip(edges, edges[1:]):
        m = (p_full >= lo) & (p_full < hi)
        if m.sum():
            rt.add_row(f"{lo}-{hi}", str(int(m.sum())), f"{p_full[m].mean():.2f}", f"{y[m].mean():.2f}")
    console.print(rt)
    console.print(f"\n[dim]MAE improvement from fatigue = {mae(y,p_base)-mae(y,p_full):+.3f} runs. If ~0, "
                  f"fatigue adds nothing over game progress + tier + bullpen — meaning the model side of the "
                  f"residual should NOT lean on it either. If clearly negative (better), fatigue is real signal.[/]")

    (HERE / "output" / "remaining_runs.json").write_text(json.dumps({
        "n": len(rows), "mae_base": round(mae(y, p_base), 3), "mae_full": round(mae(y, p_full), 3),
        "r2_base": round(float(r2(p_base)), 3), "r2_full": round(float(r2(p_full)), 3)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
