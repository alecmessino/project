#!/usr/bin/env python3
"""Conceptual (schematic) figures for the paper — illustrative, not data plots.

Two intuition figures rendered in the same visual system as the data figures
(figstyle: Okabe-Ito palette, white-edged boxes, recessive arrows, axis off):

    concept_encompassing.png  — the forecast-encompassing test (B vs B+X)
    concept_laboratory.png    — baseball as a clean market-efficiency laboratory

They carry the paper's committed numbers as annotations (0.304 / 0.279 / 0.287,
gain -0.017, error R^2 -0.037) so nothing here can drift from the results.

    python the_third_turn/paper/make_concept_figures.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import figstyle as fs  # noqa: E402

FIGDIR = HERE / "figures"
FIGDIR.mkdir(exist_ok=True)

BLUE, ORANGE, GREEN = fs.PALETTE[0], fs.PALETTE[1], fs.PALETTE[2]


def _box(ax, x, y, w, h, fc, ec=None, r=0.06, lw=1.4):
    ax.add_patch(FancyBboxPatch((x, y), w, h, mutation_scale=1,
                                boxstyle=f"round,pad=0.02,rounding_size={r}",
                                facecolor=fc, edgecolor=ec or "white", linewidth=lw, zorder=3))


def _arrow(ax, x0, y0, x1, y1, color=None, lw=1.7, style="-|>"):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle=style,
                                 mutation_scale=14, color=color or fs.MUTED,
                                 linewidth=lw, zorder=2, shrinkA=0, shrinkB=0))


# ─────────────────────────────────────────────────────────────────────────────
# Concept 1 — the forecast-encompassing test
# ─────────────────────────────────────────────────────────────────────────────
def encompassing():
    fs.setup()
    fig, ax = plt.subplots(figsize=(9.0, 5.0))
    ax.set_xlim(0, 10); ax.set_ylim(0, 6); ax.axis("off")

    # inputs
    _box(ax, 0.25, 3.55, 2.5, 1.05, BLUE)
    ax.text(1.5, 4.19, "Market forecast  B", ha="center", va="center", color="white",
            fontsize=10.5, fontweight="bold")
    ax.text(1.5, 3.83, "the live line, already public", ha="center", va="center",
            color="white", fontsize=8.1)
    _box(ax, 0.25, 1.55, 2.5, 1.05, ORANGE)
    ax.text(1.5, 2.19, "Public features  X", ha="center", va="center", color="white",
            fontsize=10.5, fontweight="bold")
    ax.text(1.5, 1.83, "TTO · velocity · bullpen · weather · park", ha="center",
            va="center", color="white", fontsize=7.6)

    # nested comparison
    _box(ax, 3.5, 1.2, 3.15, 3.75, "#F4F4F2", ec=fs.GRID)
    ax.text(5.075, 4.62, "Nested out-of-sample test", ha="center", va="center",
            color=fs.INK, fontsize=9.6, fontweight="bold")
    rows = [("Y  ~  B", "R² = 0.304", "market alone", BLUE),
            ("Y  ~  X", "R² = 0.279", "features predict runs", ORANGE),
            ("Y  ~  B + X", "R² = 0.287", "both together", fs.MUTED)]
    for i, (lhs, r2, note, col) in enumerate(rows):
        y = 4.02 - i * 0.62
        ax.add_patch(plt.Rectangle((3.72, y - 0.11), 0.12, 0.22, facecolor=col,
                                   edgecolor="none", zorder=4))
        ax.text(3.98, y, lhs, ha="left", va="center", color=fs.INK, fontsize=9.4,
                fontweight="bold", family="DejaVu Sans Mono")
        ax.text(6.5, y, r2, ha="right", va="center", color=fs.INK, fontsize=9.2,
                family="DejaVu Sans Mono")
        ax.text(3.98, y - 0.235, note, ha="left", va="center", color=fs.MUTED, fontsize=7.3)
    ax.plot([3.72, 6.5], [2.06, 2.06], color=fs.GRID, lw=1.0)
    ax.text(5.075, 1.62, "adding X to B:   ΔR² = −0.017", ha="center", va="center",
            color=fs.FAIL, fontsize=9.5, fontweight="bold")

    # verdict + sharpest test
    _box(ax, 7.35, 3.35, 2.5, 1.6, fs.INK)
    ax.text(8.6, 4.42, "B encompasses X", ha="center", va="center", color="white",
            fontsize=10.6, fontweight="bold")
    ax.text(8.6, 3.9, "the information is\nalready in the price", ha="center", va="center",
            color="white", fontsize=8.3)
    _box(ax, 7.35, 1.2, 2.5, 1.75, "#F4F4F2", ec=fs.GRID)
    ax.text(8.6, 2.62, "Sharpest test", ha="center", va="center", color=fs.INK,
            fontsize=8.8, fontweight="bold")
    ax.text(8.6, 1.98, "regress the market's error\n(Y − B) on X:\nOOS R² = −0.037,\nnot predictable",
            ha="center", va="center", color=fs.MUTED, fontsize=8.0)

    _arrow(ax, 2.8, 3.0, 3.45, 3.0)          # inputs -> test
    _arrow(ax, 6.7, 4.0, 7.3, 4.15)          # test -> verdict
    _arrow(ax, 6.7, 1.9, 7.3, 2.05)          # test -> sharpest

    # bottom strip: the three questions
    ax.text(0.25, 0.62, "Three distinct questions:", ha="left", va="center",
            color=fs.INK, fontsize=8.8, fontweight="bold")
    for x, lab, mark, mc in [(3.05, "predict the outcome", "✓", fs.PASS),
                             (5.35, "improve on the market", "✗", fs.FAIL),
                             (7.95, "turn a profit", "✗", fs.FAIL)]:
        ax.text(x, 0.62, mark, ha="left", va="center", color=mc, fontsize=11,
                fontweight="bold")
        ax.text(x + 0.28, 0.62, lab, ha="left", va="center", color=fs.MUTED, fontsize=8.4)

    ax.set_title("Forecast encompassing: a variable must improve the market's forecast, "
                 "not merely predict the outcome", fontsize=11, pad=10)
    fig.savefig(FIGDIR / "concept_encompassing.png", bbox_inches="tight")
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Concept 2 — baseball as a clean laboratory
# ─────────────────────────────────────────────────────────────────────────────
def laboratory():
    fs.setup()
    fig, ax = plt.subplots(figsize=(9.4, 4.8))
    ax.set_xlim(0, 10); ax.set_ylim(0, 5); ax.axis("off")

    yline = 3.35
    ax.plot([1.15, 8.85], [yline, yline], color=fs.MUTED, lw=2.0, zorder=1,
            solid_capstyle="round")

    # endpoints
    _box(ax, 0.2, 2.95, 1.15, 0.95, BLUE)
    ax.text(0.775, 3.55, "First pitch", ha="center", va="center", color="white",
            fontsize=8.8, fontweight="bold")
    ax.text(0.775, 3.2, "pregame line", ha="center", va="center", color="white", fontsize=7.2)
    _box(ax, 8.65, 2.95, 1.2, 0.95, fs.INK)
    ax.text(9.25, 3.55, "Final out", ha="center", va="center", color="white",
            fontsize=8.8, fontweight="bold")
    ax.text(9.25, 3.2, "bet settles", ha="center", va="center", color="white", fontsize=7.2)

    # in-game events on the timeline
    events = [(2.35, "single", "+0.47"), (3.55, "walk", "+0.32"), (4.75, "home run", "+1.4"),
              (5.95, "strikeout", "−0.26"), (7.15, "double", "+0.78")]
    for x, name, dre in events:
        ax.plot([x, x], [yline - 0.16, yline + 0.16], color=fs.PALETTE[0], lw=2.0, zorder=2)
        ax.plot([x], [yline], marker="o", ms=6, color=fs.PALETTE[0], zorder=3,
                markeredgecolor="white", markeredgewidth=1.2)
        ax.text(x, yline + 0.34, name, ha="center", va="bottom", color=fs.INK, fontsize=7.6)
        ax.text(x, yline - 0.34, f"ΔRE {dre}", ha="center", va="top", color=fs.MUTED, fontsize=7.0)

    ax.annotate("each play has a known run value (RE24 / linear weights);\n"
                "the live total reprices about once a minute",
                xy=(4.75, yline + 0.62), xytext=(4.75, 4.55), ha="center", va="center",
                color=fs.MUTED, fontsize=8.2,
                arrowprops=dict(arrowstyle="-", color=fs.GRID, lw=1.0))
    ax.annotate("realized runs  Y = ground truth", xy=(9.25, 2.9), xytext=(7.55, 2.25),
                ha="center", va="center", color=fs.INK, fontsize=8.4, fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color=fs.MUTED, lw=1.3))

    # property chips
    chips = [("Terminal payoff", "no discounting"),
             ("Valued events", "RE24 · linear weights"),
             ("High-frequency price", "a public forecast/min"),
             ("No liquidity constraint", "clean scoring")]
    cw, gap = 2.12, 0.18
    x0 = (10 - (cw * 4 + gap * 3)) / 2
    for i, (t, s) in enumerate(chips):
        x = x0 + i * (cw + gap)
        _box(ax, x, 0.85, cw, 0.92, "#F4F4F2", ec=fs.GRID)
        ax.text(x + cw / 2, 1.42, t, ha="center", va="center", color=fs.INK,
                fontsize=8.5, fontweight="bold")
        ax.text(x + cw / 2, 1.08, s, ha="center", va="center", color=fs.MUTED, fontsize=7.4)

    ax.text(5.0, 0.32, "In equities the fundamental value is never realized; here the game ends "
            "and the runs are counted.", ha="center", va="center", color=fs.MUTED,
            fontsize=8.0, style="italic")

    ax.set_title("Baseball as a clean laboratory: valued events, a high-frequency public price, "
                 "and a terminal ground truth", fontsize=10.6, pad=8)
    fig.savefig(FIGDIR / "concept_laboratory.png", bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    encompassing()
    laboratory()
    print("wrote: concept_encompassing.png, concept_laboratory.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
