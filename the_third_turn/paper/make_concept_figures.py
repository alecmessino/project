#!/usr/bin/env python3
"""Conceptual (schematic) figures for the paper — illustrative, not data plots.

Rendered in the same visual system as the data figures (figstyle: Okabe-Ito
palette, white-edged boxes, recessive arrows, axis off):

    concept_laboratory.png   — equities vs. live baseball: why baseball is a clean lab
    concept_encompassing.png — the encompassing test as an information Venn + a wall

They carry the paper's committed numbers as annotations (feature R^2 0.279,
gain -0.017, error R^2 -0.037) so nothing here can drift from the results.

    python the_third_turn/paper/make_concept_figures.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import figstyle as fs  # noqa: E402

FIGDIR = HERE / "figures"
FIGDIR.mkdir(exist_ok=True)

BLUE, ORANGE, GREEN, RED = fs.PALETTE[0], fs.PALETTE[1], fs.PALETTE[2], fs.PALETTE[3]
BRICK = "#B4553B"


def _box(ax, x, y, w, h, fc, ec=None, r=0.09, lw=1.4, z=3):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0.02,rounding_size={r}",
                                facecolor=fc, edgecolor=ec or "white", linewidth=lw, zorder=z))


def _arrow(ax, x0, y0, x1, y1, color=None, lw=1.8, style="-|>", cs=None, z=2):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle=style, mutation_scale=14,
                                 color=color or fs.MUTED, linewidth=lw, zorder=z,
                                 shrinkA=0, shrinkB=0, connectionstyle=cs))


# ─────────────────────────────────────────────────────────────────────────────
# Concept 1 — equities vs. live baseball (the clean laboratory, by contrast)
# ─────────────────────────────────────────────────────────────────────────────
def laboratory():
    fs.setup()
    fig, (axE, axB) = plt.subplots(1, 2, figsize=(10.8, 4.9),
                                   gridspec_kw={"width_ratios": [1.0, 1.1]})
    for ax in (axE, axB):
        ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")

    # ---- equities: a price wandering around a never-realized fundamental band ----
    axE.set_title("Equities market", fontsize=10.8, pad=6)
    rng = np.random.default_rng(7)
    t = np.linspace(0.7, 9.3, 220)
    p = np.cumsum(rng.normal(0, 0.13, t.size)); p = 5.7 + (p - p.mean())
    axE.fill_between(t, 4.7, 6.7, color=RED, alpha=0.10, zorder=1)
    axE.plot(t, np.full_like(t, 5.7), color=RED, lw=1.2, ls=(0, (2, 3)), alpha=0.75, zorder=2)
    axE.text(5.0, 7.15, "fundamental value?  a fuzzy band, never realized",
             ha="center", va="center", color=RED, fontsize=7.9)
    axE.plot(t, p, color=fs.INK, lw=1.6, zorder=3, solid_capstyle="round")
    axE.annotate("", xy=(9.7, 2.1), xytext=(0.4, 2.1),
                 arrowprops=dict(arrowstyle="-|>", color=fs.MUTED, lw=1.3))
    axE.text(9.7, 1.72, "time, indefinite horizon", ha="right", va="top", color=fs.MUTED, fontsize=7.8)
    axE.text(5.0, 0.85, "price wanders  ·  payoffs need discounting", ha="center", va="center",
             color=fs.MUTED, fontsize=8.1)
    axE.text(5.0, 0.35, "no clean per-event value  ·  no terminal truth", ha="center", va="center",
             color=fs.MUTED, fontsize=8.1)

    # ---- live baseball: discrete valued events resolving to a terminal ground truth ----
    axB.set_title("Live baseball market", fontsize=10.8, pad=6)
    yb = 5.7
    axB.plot([1.25, 8.55], [yb, yb], color=fs.MUTED, lw=2.0, solid_capstyle="round", zorder=1)
    axB.plot([1.25], [yb], marker="o", ms=13, color=BLUE, markeredgecolor="white",
             markeredgewidth=1.6, zorder=3)
    axB.text(1.25, yb + 0.72, "first pitch", ha="center", va="bottom", color=fs.INK,
             fontsize=8.2, fontweight="bold")
    axB.text(1.25, yb - 0.72, "pregame line", ha="center", va="top", color=fs.MUTED, fontsize=7.4)
    axB.plot([8.55], [yb], marker="s", ms=15, color=fs.INK, markeredgecolor="white",
             markeredgewidth=1.6, zorder=3)
    axB.text(8.55, yb + 0.72, "final out", ha="center", va="bottom", color=fs.INK,
             fontsize=8.2, fontweight="bold")
    axB.text(8.55, yb - 0.72, "settles", ha="center", va="top", color=fs.MUTED, fontsize=7.4)
    for x, name, dre in [(3.0, "1B", "+0.47"), (4.35, "HR", "+1.4"),
                         (5.7, "K", "−0.26"), (7.05, "2B", "+0.78")]:
        axB.plot([x, x], [yb - 0.16, yb + 0.16], color=BLUE, lw=2.0, zorder=2)
        axB.plot([x], [yb], marker="o", ms=6, color=BLUE, markeredgecolor="white",
                 markeredgewidth=1.1, zorder=3)
        axB.text(x, yb + 0.30, name, ha="center", va="bottom", color=fs.INK, fontsize=7.6)
        axB.text(x, yb - 0.30, dre, ha="center", va="top", color=fs.MUTED, fontsize=6.9)
    axB.text(4.9, 8.7, "each play has a known run value (RE24 / linear weights);",
             ha="center", va="center", color=fs.MUTED, fontsize=8.1)
    axB.text(4.9, 8.25, "the live total reprices about once a minute", ha="center", va="center",
             color=fs.MUTED, fontsize=8.1)
    axB.text(4.9, 3.05, "resolves to the final total = ground truth  Y", ha="center", va="center",
             color=fs.INK, fontsize=8.6, fontweight="bold")
    axB.text(4.9, 2.55, "an absolute answer, within hours", ha="center", va="center",
             color=fs.MUTED, fontsize=7.9)

    fig.suptitle("Why baseball is a clean laboratory for market efficiency",
                 fontsize=11.4, fontweight="bold", y=1.03)
    fig.savefig(FIGDIR / "concept_laboratory.png", bbox_inches="tight")
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Concept 2 — the encompassing test: an information Venn + a wall
# ─────────────────────────────────────────────────────────────────────────────
def _brick_wall(ax, x, y0, y1, w=0.5):
    ax.add_patch(plt.Rectangle((x, y0), w, y1 - y0, facecolor=BRICK, edgecolor="none", zorder=4))
    rows = np.arange(y0, y1 + 0.001, 0.34)
    for i in range(len(rows) - 1):
        ax.plot([x, x + w], [rows[i], rows[i]], color="white", lw=0.9, zorder=5)
        xm = x + (w / 2 if i % 2 else 0)
        if x < xm < x + w:
            ax.plot([xm, xm], [rows[i], rows[i + 1]], color="white", lw=0.9, zorder=5)
    ax.plot([x + w, x + w], [y0, y1], color="white", lw=0.9, zorder=5)


def encompassing():
    fs.setup()
    fig, ax = plt.subplots(figsize=(9.4, 5.2))
    ax.set_xlim(0, 10); ax.set_ylim(0, 6.6); ax.axis("off")

    # information Venn: X entirely inside B
    ax.add_patch(Circle((2.55, 4.05), 2.05, facecolor=BLUE, alpha=0.13,
                        edgecolor=BLUE, linewidth=2.0, zorder=2))
    ax.text(2.55, 5.62, "Market forecast  B", ha="center", va="center", color=BLUE,
            fontsize=10.2, fontweight="bold")
    ax.add_patch(Circle((2.4, 3.5), 0.95, facecolor=ORANGE, alpha=0.9,
                        edgecolor="white", linewidth=1.6, zorder=3))
    ax.text(2.4, 3.5, "X", ha="center", va="center", color="white", fontsize=12.5,
            fontweight="bold", zorder=4)
    ax.text(2.55, 1.72, "the market's forecast already reflects\nthe information in X",
            ha="center", va="center", color=fs.MUTED, fontsize=8.0, style="italic")
    ax.text(2.55, 0.9, "X = TTO · velocity · bullpen · weather · park", ha="center", va="center",
            color=fs.INK, fontsize=7.8)

    # target 1: outcome Y — X reaches it
    _box(ax, 7.55, 4.55, 2.2, 1.15, GREEN)
    ax.text(8.65, 5.28, "Outcome  Y", ha="center", va="center", color="white",
            fontsize=10, fontweight="bold")
    ax.text(8.65, 4.9, "remaining runs", ha="center", va="center", color="white", fontsize=7.8)
    _arrow(ax, 3.35, 4.35, 7.5, 5.12, color=GREEN, lw=2.2, cs="arc3,rad=-0.12")
    ax.text(5.5, 5.42, "predicts runs   R² = 0.279", ha="center", va="center", color=fs.INK,
            fontsize=8.7, fontweight="bold", bbox=dict(facecolor="white", edgecolor="none",
            alpha=0.85, boxstyle="round,pad=0.15"))
    ax.text(6.62, 5.0, "✓", ha="center", va="center", color=fs.PASS, fontsize=13, fontweight="bold")

    # target 2: market error Y-B — X collides with a wall
    _box(ax, 7.55, 1.05, 2.2, 1.2, fs.INK)
    ax.text(8.65, 1.82, "Market error", ha="center", va="center", color="white",
            fontsize=9.6, fontweight="bold")
    ax.text(8.65, 1.42, "Y − B", ha="center", va="center", color="white", fontsize=9.0,
            family="DejaVu Sans Mono")
    _brick_wall(ax, 5.95, 0.85, 3.05)
    _arrow(ax, 3.3, 3.35, 5.85, 2.35, color=ORANGE, lw=2.2, cs="arc3,rad=0.10")
    ax.text(5.02, 1.62, "✗", ha="center", va="center", color=fs.FAIL, fontsize=15, fontweight="bold")
    ax.text(6.55, 3.42, "R² = −0.037", ha="center", va="center", color=BRICK, fontsize=9.0,
            fontweight="bold")
    ax.text(7.15, 0.62, "the market's forecast already exhausts the information in X",
            ha="center", va="center", color=fs.MUTED, fontsize=7.8, style="italic")

    ax.text(0.15, 0.3, "adding X to B:  ΔR² = −0.017", ha="left", va="center", color=fs.FAIL,
            fontsize=8.8, fontweight="bold")
    ax.set_title("The encompassing test: X predicts the outcome, but not the market's error",
                 fontsize=11, pad=8)
    fig.savefig(FIGDIR / "concept_encompassing.png", bbox_inches="tight")
    plt.close(fig)


def vig_hurdle():
    """Appendix C: the break-even (vig) hurdle in win-rate space."""
    fs.setup()
    fig, ax = plt.subplots(figsize=(8.8, 4.0))
    ax.set_xlim(48, 58); ax.set_ylim(-0.55, 1.45); ax.axis("off")
    y = 0.45
    ax.add_patch(plt.Rectangle((48.3, y - 0.14), 52.38 - 48.3, 0.28, facecolor=RED, alpha=0.10, zorder=1))
    ax.add_patch(plt.Rectangle((52.38, y - 0.14), 57.5 - 52.38, 0.28, facecolor=GREEN, alpha=0.12, zorder=1))
    ax.annotate("", xy=(57.75, y), xytext=(48.1, y),
                arrowprops=dict(arrowstyle="-|>", color=fs.MUTED, lw=1.6), zorder=2)
    ax.text(50.35, y + 0.075, "loss", ha="center", va="center", color=RED, fontsize=8.2, alpha=0.75)
    ax.text(55.0, y + 0.075, "profit", ha="center", va="center", color=fs.PASS, fontsize=8.2, alpha=0.9)
    for xv, lab, sub, col in [(50.0, "50%", "fair coin", fs.MUTED),
                              (52.38, "52.38%", "break-even vs −110 vig", fs.INK),
                              (55.0, "55%", "a marginal edge", fs.PASS)]:
        ax.plot([xv, xv], [y - 0.17, y + 0.17], color=col, lw=2.4, zorder=3)
        ax.text(xv, y + 0.24, lab, ha="center", va="bottom", fontsize=9.6, fontweight="bold", color=col)
        ax.text(xv, y - 0.24, sub, ha="center", va="top", fontsize=7.7, color=fs.MUTED)
    ax.annotate("", xy=(52.38, y + 0.66), xytext=(50.0, y + 0.66),
                arrowprops=dict(arrowstyle="<|-|>", color=RED, lw=1.3))
    ax.text(51.19, y + 0.72, "the vig: 2.38 points to clear just to break even",
            ha="center", va="bottom", color=RED, fontsize=8.2, fontweight="bold")
    ax.annotate("public information leaves you here\n(the market's error is unpredictable, R² = −0.037)",
                xy=(50.0, y - 0.17), xytext=(50.0, y - 0.62), ha="center", va="top", fontsize=8.0,
                color=fs.INK, arrowprops=dict(arrowstyle="-|>", color=fs.INK, lw=1.2))
    ax.set_title("The vig hurdle: profitability requires beating 52.4%, not 50%", fontsize=11, pad=14)
    fig.savefig(FIGDIR / "appendix_vig.png", bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    laboratory()
    encompassing()
    vig_hurdle()
    print("wrote: concept_laboratory.png, concept_encompassing.png, appendix_vig.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
