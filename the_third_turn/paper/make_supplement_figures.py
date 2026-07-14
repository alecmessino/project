#!/usr/bin/env python3
"""Supplementary / companion figures (talks, repo, social) — NOT part of the frozen paper.

    supp_line_movement.png  — one game's live total tracking the runs it scores (real, from
                              the committed encompass_cache: live total = B + runs-so-far)
    supp_weather_diamond.png — the run-environment: how weather and park move fly-ball carry,
                              the physics the market already prices (and, in our data, over-adjusts)

    python the_third_turn/paper/make_supplement_figures.py
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Polygon, Wedge, Circle, FancyBboxPatch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import figstyle as fs  # noqa: E402

OUT = HERE.parent / "output"
FIGDIR = HERE / "figures"
FIGDIR.mkdir(exist_ok=True)
GRASS, DIRT = "#D7E8D0", "#E7D7B4"


# ─────────────────────────────────────────────────────────────────────────────
# Line movement: the market's live total tracking the runs actually scored
# ─────────────────────────────────────────────────────────────────────────────
def line_movement(game_pk=823541):
    rows = json.load(open(OUT / "encompass_cache.json"))
    snaps = sorted([r for r in rows if r["game"] == game_pk], key=lambda r: r["inning"])
    final = snaps[0]["Y"]                                  # Y at the first snapshot ~= final total
    x = list(range(len(snaps)))
    innings = [int(s["inning"]) for s in snaps]
    runs = [final - s["Y"] for s in snaps]                 # cumulative runs scored
    live = [s["B"] + (final - s["Y"]) for s in snaps]      # market forecast of the FINAL total
    pregame = live[0]
    burst = max(range(1, len(runs)), key=lambda i: runs[i] - runs[i - 1])

    fs.setup()
    fig, ax = plt.subplots(figsize=(8.8, 4.9))
    ax.fill_between(x, runs, live, color=fs.PALETTE[0], alpha=0.09, zorder=1)
    ax.axhline(pregame, color=fs.MUTED, lw=1.0, ls=":")
    ax.text(x[-1] + 0.1, pregame, f"pregame total {pregame:.1f}", va="center", ha="left",
            fontsize=7.8, color=fs.MUTED)
    ax.plot(x, live, color=fs.PALETTE[0], lw=2.3, marker="o", ms=4.5, zorder=3,
            label="market's live total  (forecast of final)")
    ax.plot(x, runs, color=fs.PALETTE[3], lw=2.3, marker="s", ms=4.5, zorder=3,
            label="runs actually scored")
    ax.annotate(f"{int(runs[burst] - runs[burst - 1])} runs score →\nthe market lifts its total",
                xy=(x[burst], live[burst]), xytext=(x[burst] - 3.4, live[burst] + 3.2),
                fontsize=8.2, color=fs.INK, ha="left", va="bottom",
                bbox=dict(facecolor="white", edgecolor="none", alpha=0.8, boxstyle="round,pad=0.15"),
                arrowprops=dict(arrowstyle="-|>", color=fs.MUTED, lw=1.2))
    ax.annotate("gap = runs the market\nstill expects (its live over/under)",
                xy=((x[3] + x[4]) / 2, (live[3] + runs[3]) / 2), xytext=(x[3] + 0.3, runs[3] - 4.2),
                fontsize=7.8, color=fs.PALETTE[0], ha="left", va="top",
                arrowprops=dict(arrowstyle="-|>", color=fs.PALETTE[0], lw=1.0))
    ax.plot([x[-1]], [live[-1]], marker="*", ms=15, color=fs.INK, zorder=4)
    ax.text(x[-1], live[-1] + 0.7, "final: line = score", ha="center", va="bottom",
            fontsize=8.0, color=fs.INK, fontweight="bold")
    step = max(1, len(x) // 8)
    ax.set_xticks(x[::step]); ax.set_xticklabels([f"inn {innings[i]}" for i in x[::step]], fontsize=8.2)
    ax.set_ylabel("runs")
    ax.set_ylim(-0.5, max(live) + 4.2)
    ax.legend(loc="upper left", fontsize=8.6)
    ax.set_title("Line movement over a game: the live total chases the runs, and meets them at the end",
                 fontsize=11, pad=10)
    fig.savefig(FIGDIR / "supp_line_movement.png", bbox_inches="tight")
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# The run environment: weather + park physics the market already prices
# ─────────────────────────────────────────────────────────────────────────────
def weather_diamond():
    fs.setup()
    fig, ax = plt.subplots(figsize=(9.2, 6.4))
    ax.set_xlim(-9, 9); ax.set_ylim(-1.6, 11.2); ax.axis("off"); ax.set_aspect("equal")

    # field: grass wedge (foul lines at 45 and 135 deg) + dirt infield diamond
    ax.add_patch(Wedge((0, 0), 7.6, 45, 135, facecolor=GRASS, edgecolor="none", zorder=1))
    ax.add_patch(Wedge((0, 0), 7.6, 45, 135, width=0.12, facecolor=fs.MUTED, edgecolor="none", zorder=2))  # fence
    for a in (45, 135):  # foul lines
        r = np.deg2rad(a)
        ax.plot([0, 7.55 * np.cos(r)], [0, 7.55 * np.sin(r)], color="white", lw=1.6, zorder=2)
    dia = [(0, 0), (2.3, 2.3), (0, 4.6), (-2.3, 2.3)]
    ax.add_patch(Polygon(dia, closed=True, facecolor=DIRT, edgecolor="white", lw=1.6, zorder=3))
    for (bx, by) in dia[1:]:
        ax.add_patch(plt.Rectangle((bx - 0.16, by - 0.16), 0.32, 0.32, facecolor="white",
                                   edgecolor=fs.MUTED, lw=0.8, zorder=4))
    ax.add_patch(plt.Polygon([(-0.16, -0.02), (0.16, -0.02), (0.16, 0.14), (0, 0.28), (-0.16, 0.14)],
                             closed=True, facecolor="white", edgecolor=fs.MUTED, lw=0.8, zorder=4))  # home
    ax.add_patch(Circle((0, 2.3), 0.28, facecolor=DIRT, edgecolor="white", lw=1.2, zorder=4))  # mound

    # wind arrow, out to center
    ax.add_patch(FancyArrowPatch((0, 0.9), (0, 6.7), arrowstyle="-|>", mutation_scale=22,
                                 color=fs.PALETTE[0], lw=3.0, zorder=5, alpha=0.85))
    ax.text(0.35, 5.9, "WIND OUT", rotation=90, va="center", ha="left", color=fs.PALETTE[0],
            fontsize=10, fontweight="bold")
    ax.text(-0.4, 5.9, "10 · 20 · 30 mph", rotation=90, va="center", ha="right", color=fs.PALETTE[0],
            fontsize=7.8)

    def chip(x, y, title, body, col=fs.INK):
        ax.add_patch(FancyBboxPatch((x, y), 4.5, 1.5, boxstyle="round,pad=0.05,rounding_size=0.12",
                                    facecolor="#F6F6F4", edgecolor=fs.GRID, lw=1.0, zorder=6))
        ax.text(x + 0.22, y + 1.16, title, ha="left", va="center", color=col, fontsize=9.2,
                fontweight="bold", zorder=7)
        ax.text(x + 0.22, y + 0.5, body, ha="left", va="center", color=fs.MUTED, fontsize=7.7,
                zorder=7)

    chip(-8.7, 8.9, "Temperature", "warm air is thinner →\nball carries ~+2.5 ft per +10°F", fs.PALETTE[3])
    chip(4.2, 8.9, "Humidity", "humid air is LESS dense →\nslightly more carry (counter-intuitive)", fs.PALETTE[0])
    chip(-8.7, 0.1, "Wind to center", "out: more carry, more runs\nin: knocks fly balls down", fs.PALETTE[0])
    chip(4.2, 0.1, "Park factor", "100 = neutral · 112 = hitter\n120+ ≈ Coors (altitude, thin air)", fs.PALETTE[2])

    ax.text(0, 10.75, "The run environment: the physics the market already prices",
            ha="center", va="center", fontsize=12, fontweight="bold", color=fs.INK)
    ax.text(0, -1.15,
            "Fly-ball carry ≈ f(air density): temperature, altitude, barometric pressure, humidity, wind.  "
            "Denser air = less carry = fewer runs.",
            ha="center", va="center", fontsize=8.2, color=fs.INK,
            bbox=dict(facecolor="#F1F1EE", edgecolor=fs.GRID, boxstyle="round,pad=0.4"))
    fig.savefig(FIGDIR / "supp_weather_diamond.png", bbox_inches="tight")
    plt.close(fig)


def _wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return (max(0.0, c - h), min(1.0, c + h))


def weather_runs():
    """Real sample: runs rise with hitter weather, but the over never reliably beats break-even."""
    rows = json.load(open(OUT / "encompass_cache.json"))
    byg = defaultdict(list)
    for r in rows:
        byg[r["game"]].append(r)
    G = []
    for _, s in byg.items():
        s = sorted(s, key=lambda r: r["inning"])
        G.append(dict(final=s[0]["Y"], pre=s[0]["B"], temp=s[0]["temp"], wind=s[0]["wind"]))
    buckets = [
        ("wind in\n(≤ −4)", [g for g in G if g["wind"] <= -4]),
        ("calm", [g for g in G if -4 < g["wind"] < 4]),
        ("wind out\n(≥ +4)", [g for g in G if g["wind"] >= 4]),
        ("cooler\n(< 75°)", [g for g in G if g["temp"] < 75]),
        ("warm\n(75–84°)", [g for g in G if 75 <= g["temp"] < 85]),
        ("hot\n(≥ 85°)", [g for g in G if g["temp"] >= 85]),
    ]
    labels = [b[0] for b in buckets]
    runs = [sum(g["final"] for g in gm) / len(gm) for _, gm in buckets]
    ns = [len(gm) for _, gm in buckets]
    hit, lo, hi = [], [], []
    for _, gm in buckets:
        dec = [g for g in gm if g["final"] != g["pre"]]
        k, n = sum(1 for g in dec if g["final"] > g["pre"]), len(dec)
        hit.append(100 * k / n); a, b = _wilson(k, n); lo.append(100 * a); hi.append(100 * b)
    cols = [fs.PALETTE[0]] * 3 + [fs.PALETTE[3]] * 3

    fs.setup()
    fig, (axA, axR) = plt.subplots(1, 2, figsize=(10.8, 4.8))
    x = np.arange(6)

    axA.bar(x, runs, color=cols, width=0.72, zorder=3)
    for xi, r, n in zip(x, runs, ns):
        axA.text(xi, r + 0.12, f"{r:.1f}", ha="center", va="bottom", fontsize=8.4, fontweight="bold")
        axA.text(xi, 0.35, f"n={n}", ha="center", va="bottom", color="white", fontsize=7.4, fontweight="bold", zorder=4)
    axA.set_ylabel("mean runs scored per game")
    axA.set_ylim(0, max(runs) + 1.4)
    axA.set_xticks(x); axA.set_xticklabels(labels, fontsize=7.7)
    axA.set_title("Runs rise with hitter-friendly weather", fontsize=10.6, pad=8)

    axR.bar(x, hit, color=cols, width=0.72, alpha=0.85, zorder=3)
    axR.errorbar(x, hit, yerr=[[h - l for h, l in zip(hit, lo)], [u - h for h, u in zip(hit, hi)]],
                 fmt="none", ecolor=fs.INK, elinewidth=1.3, capsize=4, zorder=4)
    axR.axhline(50, color=fs.MUTED, lw=1.1, ls="--")
    axR.axhline(52.38, color=fs.FAIL, lw=1.3, ls="--")
    axR.text(5.55, 50, "coin flip", va="center", ha="left", fontsize=7.4, color=fs.MUTED)
    axR.text(5.55, 52.6, "break-even", va="bottom", ha="left", fontsize=7.4, color=fs.FAIL)
    axR.set_ylabel("over hit-rate (%)")
    axR.set_ylim(28, 76)
    axR.set_xticks(x); axR.set_xticklabels(labels, fontsize=7.7)
    axR.set_title("...but the over never reliably clears break-even", fontsize=10.6, pad=8)

    fig.suptitle("Weather moves runs; it does not move the price enough to beat it",
                 fontsize=11.6, fontweight="bold", y=1.10)
    fig.savefig(FIGDIR / "supp_weather_runs.png", bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    line_movement()
    weather_diamond()
    weather_runs()
    print("wrote: supp_line_movement.png, supp_weather_diamond.png, supp_weather_runs.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
