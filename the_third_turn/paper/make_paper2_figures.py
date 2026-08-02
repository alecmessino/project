#!/usr/bin/env python3
"""Paper 2 conceptual figures.

Each figure teaches ONE concept, and a reader flipping through the figures alone should
follow the paper's central argument. Paper 1's figures explained why the statistical test
answered the question; these explain why the question is hard to answer at all.

Visual system shared by every figure here:
  - soft tinted fills with a saturated stroke, never flat saturated blocks
  - generous internal padding; labels in Liberation Sans with tracked small-caps eyebrows
  - hairline rules, softened ink, annotation on leader lines
  - colour vocabulary: green identified, orange bounded, red fails, grey unknowable
  - GD-17: no axis carries a quantity that has not been estimated or derived

    python3 the_third_turn/paper/make_paper2_figures.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import figstyle as fs  # noqa: E402

FIG = HERE / "figures"

# ---------------------------------------------------------------- visual system
BLUE, ORANGE, GREEN, RED = fs.PALETTE[0], fs.PALETTE[1], fs.PALETTE[2], fs.PALETTE[3]
INK   = "#1F2933"     # softened ink with a faint cool bias, never pure black
MUTED = "#7B8794"
HAIR  = "#E1E5EA"
FOG   = "#EEF1F4"     # the unobservable ground
CARD  = "#FFFFFF"
IDENTIFIED, BOUNDED, FAILED = GREEN, ORANGE, RED
FONT = "Liberation Sans"


def _init():
    fs.setup()
    matplotlib.rcParams.update({
        "font.family": FONT, "text.color": INK,
        "figure.facecolor": "white", "savefig.facecolor": "white",
        "axes.grid": False, "figure.constrained_layout.use": False,
    })


def canvas(w, h, top=0.92):
    fig, ax = plt.subplots(figsize=(w, h))
    fig.subplots_adjust(top=top, bottom=0.04, left=0.02, right=0.98)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    return fig, ax


def eyebrow(ax, x, y, s, color=MUTED, size=8.4, ha="left"):
    ax.text(x, y, " ".join(s.upper()), ha=ha, va="center", fontsize=size,
            color=color, fontweight="bold", zorder=9)


def title(fig, s, sub=None, y=0.985):
    fig.text(0.5, y, s, ha="center", va="top", fontsize=13.2, color=INK, fontweight="bold")
    if sub:
        fig.text(0.5, y - 0.058, sub, ha="center", va="top", fontsize=9.6, color=MUTED)


def note(fig, s, y=0.0, size=9.3):
    fig.text(0.5, y, s, ha="center", va="top", fontsize=size, color=INK, linespacing=1.62)


def card(ax, x, y, w, h, fc=CARD, ec=HAIR, lw=1.1, r=0.016, z=2):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle=f"round,pad=0.004,rounding_size={r}",
                                fc=fc, ec=ec, lw=lw, zorder=z))


def tinted(ax, x, y, w, h, color, z=3, r=0.012, lw=1.5, alpha=0.13):
    """Soft fill plus saturated stroke: the workhorse shape of this system."""
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle=f"round,pad=0.003,rounding_size={r}",
                                fc=color, ec="none", zorder=z, alpha=alpha))
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle=f"round,pad=0.003,rounding_size={r}",
                                fc="none", ec=color, lw=lw, zorder=z + 1))


def arrow(ax, p, q, color=INK, lw=1.5, style="-|>", ls="-", z=6, ms=12, alpha=1.0):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=ms, lw=lw,
                                 color=color, zorder=z, linestyle=ls, alpha=alpha))


def leader(ax, xy, xytext, s, color=MUTED, size=8.6, ha="left"):
    ax.annotate(s, xy=xy, xytext=xytext, fontsize=size, color=color, ha=ha, va="center",
                zorder=9, linespacing=1.45, fontweight="bold",
                arrowprops=dict(arrowstyle="-", color=color, lw=0.8, alpha=0.7,
                                shrinkA=2, shrinkB=4))


def chip(ax, x, y, s, color, size=8.4):
    ax.text(x, y, s.upper(), ha="center", va="center", fontsize=size, color="white",
            fontweight="bold", zorder=9,
            bbox=dict(boxstyle="round,pad=0.42", fc=color, ec="none"))


# ------------------------------------------------------------------- FIG 1
def fig_boundary():
    fig, ax = canvas(9.4, 6.0)
    rows = [("Game event",       0.790, True,  "recorded by the state feed"),
            ("Bookmaker prices", 0.618, False, "when the book decided to move"),
            ("Feed publishes",   0.466, False, "when that decision became visible"),
            ("We sample",        0.294, True,  "our fixed polling interval"),
            ("Row in the panel", 0.142, True,  "the timestamp we actually hold")]

    card(ax, 0.055, 0.438, 0.895, 0.262, fc=FOG, ec=HAIR, lw=1.2, r=0.02, z=1)
    ax.text(0.087, 0.569, "UNOBSERVED", rotation=90, ha="center", va="center",
            fontsize=9.0, color=MUTED, fontweight="bold", zorder=8)

    h = 0.108
    for lab, y, seen, sub in rows:
        c = IDENTIFIED if seen else FAILED
        card(ax, 0.155, y, 0.60, h, fc=CARD, ec=HAIR, lw=1.2, z=4)
        ax.add_patch(Rectangle((0.157, y + 0.009), 0.0075, h - 0.018,
                               fc=c, ec="none", zorder=6))
        ax.text(0.188, y + h / 2 + 0.019, lab, fontsize=10.6, color=INK,
                fontweight="bold", va="center", zorder=6)
        ax.text(0.188, y + h / 2 - 0.024, sub, fontsize=8.5, color=MUTED,
                va="center", zorder=6)
        ax.text(0.660, y + h / 2, "observed" if seen else "hidden", fontsize=9.2,
                color=c, va="center", fontweight="bold", zorder=6)

    for a, b, hidden in [(0.790, 0.726, False), (0.618, 0.574, True),
                         (0.466, 0.402, True), (0.294, 0.250, False)]:
        arrow(ax, (0.455, a), (0.455, b), lw=1.4,
              color=MUTED if hidden else INK,
              ls=(0, (2.5, 2)) if hidden else "-", alpha=0.9 if hidden else 1)

    leader(ax, (0.757, 0.542), (0.828, 0.542),
           "the two stages\nthe question\nis about", color=FAILED, size=8.8)

    ax.text(0.5, 0.048, "The only two stages we cannot see are the only two we need.",
            ha="center", fontsize=11.4, color=INK, fontweight="bold")
    ax.text(0.5, 0.000, "Markets reveal prices. They do not reveal how those prices came to be.",
            ha="center", fontsize=9.8, color=MUTED, style="italic")
    title(fig, "The boundary of observation")
    fig.savefig(FIG / "p2_boundary.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


# ------------------------------------------------------------------- FIG 2
def fig_race():
    fig, ax = canvas(10.2, 5.0)
    card(ax, 0.172, 0.200, 0.548, 0.645, fc=FOG, ec=HAIR, lw=1.2, r=0.02, z=1)
    ax.text(0.446, 0.800, "N O T   O B S E R V A B L E", ha="center", fontsize=9.4,
            color=MUTED, fontweight="bold", zorder=8)

    ax.plot([0.113, 0.113], [0.182, 0.792], color=GREEN, lw=2.6, zorder=5,
            solid_capstyle="round")
    eyebrow(ax, 0.113, 0.845, "run scores", color=GREEN, size=9.4, ha="center")

    for y, lab, c, xe in [(0.698, "Book A decides to re-price", BLUE, 0.300),
                          (0.576, "Book A's feed publishes", MUTED, 0.437),
                          (0.453, "Book B decides to re-price", ORANGE, 0.520),
                          (0.331, "Book B's feed publishes", MUTED, 0.652)]:
        ax.plot([0.113, xe], [y, y], color=c, lw=1.7, zorder=5, solid_capstyle="round")
        ax.plot([xe], [y], "o", ms=6.4, color=c, zorder=6,
                markeredgecolor="white", markeredgewidth=1.2)
        ax.text(xe + 0.016, y, lab, fontsize=8.9, color=c, va="center", zorder=6)

    ax.plot([0.793, 0.793], [0.182, 0.792], color=INK, lw=2.2, zorder=5,
            solid_capstyle="round")
    eyebrow(ax, 0.793, 0.845, "we look", color=INK, size=9.4, ha="center")
    ax.text(0.793, 0.150, "every 31 s", ha="center", fontsize=8.5, color=MUTED)

    for y, c in [(0.643, BLUE), (0.396, ORANGE)]:
        ax.plot([0.722, 0.780], [y, y], color=c, lw=1.2, ls=(0, (2, 2)), zorder=5, alpha=.8)
        ax.plot([0.793], [y], "o", ms=7.6, color=INK, zorder=7,
                markeredgecolor="white", markeredgewidth=1.4)
        ax.text(0.818, y, "one timestamp", fontsize=8.9, color=INK, va="center")

    ax.text(0.5, 0.082, "Four internal events. Two recorded numbers.",
            ha="center", fontsize=11.4, color=INK, fontweight="bold")
    ax.text(0.5, 0.026,
            "The interval we can measure is a sum of intervals we cannot measure separately.",
            ha="center", fontsize=9.6, color=MUTED)
    title(fig, "The information race, and how little of it we see")
    fig.savefig(FIG / "p2_race.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


# ------------------------------------------------------------------- FIG 3
def fig_why_paper1():
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.9))
    for ax in axes:
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    ax = axes[0]
    eyebrow(ax, 0.5, 0.950, "paper 1", color=INK, size=10.2, ha="center")
    ax.text(0.5, 0.884, "does the variable beat the price?", ha="center",
            fontsize=9.2, color=MUTED)
    for lab, y in [("Public variable", 0.655), ("Market price", 0.400), ("Outcome", 0.145)]:
        tinted(ax, 0.20, y, 0.60, 0.135, GREEN, alpha=0.10, lw=1.3)
        ax.text(0.50, y + 0.0675, lab, ha="center", va="center", fontsize=10.4,
                color=INK, fontweight="bold", zorder=6)
    for a, b in [(0.655, 0.545), (0.400, 0.290)]:
        arrow(ax, (0.5, a), (0.5, b), lw=1.8)
    leader(ax, (0.802, 0.4675), (0.882, 0.4675), "every node\nobservable",
           color=IDENTIFIED, size=8.8)

    ax = axes[1]
    eyebrow(ax, 0.5, 0.950, "paper 2", color=INK, size=10.2, ha="center")
    ax.text(0.5, 0.884, "how did the price get there?", ha="center",
            fontsize=9.2, color=MUTED)
    for lab, y, hidden in [("Game event", 0.730, False), ("Book pricing", 0.515, True),
                           ("Feed publication", 0.300, True), ("What we record", 0.085, False)]:
        if hidden:
            card(ax, 0.20, y, 0.60, 0.125, fc=FOG, ec=HAIR, lw=1.1, z=3)
            ax.text(0.50, y + 0.0625, lab, ha="center", va="center", fontsize=10.2,
                    color=MUTED, zorder=6)
            ax.text(0.828, y + 0.0625, "hidden", fontsize=8.6, color=FAILED,
                    va="center", fontweight="bold", zorder=6)
        else:
            tinted(ax, 0.20, y, 0.60, 0.125, GREEN, alpha=0.10, lw=1.3)
            ax.text(0.50, y + 0.0625, lab, ha="center", va="center", fontsize=10.4,
                    color=INK, fontweight="bold", zorder=6)
    for a, b in [(0.730, 0.645), (0.515, 0.430), (0.300, 0.215)]:
        arrow(ax, (0.5, a), (0.5, b), lw=1.4, color=MUTED, ls=(0, (2.5, 2)))

    title(fig, "Why Paper 1 never had to face this", y=1.025)
    note(fig,
         "Paper 1 compared two endpoints and could stay agnostic about the machinery between them.\n"
         "Paper 2's question is the machinery, and half its stages are invisible.", y=0.020)
    fig.savefig(FIG / "p2_why_paper1.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


# ------------------------------------------------------------------- FIG 4 (centerpiece)
def fig_three_worlds():
    fig, axes = plt.subplots(1, 3, figsize=(15.0, 5.6))
    X0, BH = 0.105, 0.105
    yA, yB = 0.605, 0.455
    worlds = [("World A", "A prices faster; plumbing matches",
               0.20, 0.44, 0.26, 0.26, "the lag is real", GREEN),
              ("World B", "identical pricing; B's feed is slower",
               0.28, 0.28, 0.18, 0.42, "the lag is plumbing", RED),
              ("World C", "both differ, and partly cancel",
               0.24, 0.38, 0.22, 0.32, "the lag is a blend", ORANGE)]

    for ax, (name, sub, pA, pB, fA, fB, verdict, vc) in zip(axes, worlds):
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
        card(ax, 0.02, 0.045, 0.96, 0.905, fc=CARD, ec=HAIR, lw=1.3, r=0.022, z=1)
        chip(ax, 0.148, 0.885, name, INK)
        ax.text(0.575, 0.885, sub, ha="center", va="center", fontsize=8.8, color=MUTED)
        ax.plot([0.05, 0.95], [0.815, 0.815], color=HAIR, lw=1.0, zorder=2)

        endA, endB = X0 + pA + fA, X0 + pB + fB
        for xe in (endA, endB):
            ax.add_patch(Rectangle((xe - 0.004, 0.175), 0.008, 0.560,
                                   fc=INK, ec="none", alpha=0.07, zorder=2))
            ax.plot([xe, xe], [0.175, 0.735], color=INK, lw=1.0,
                    ls=(0, (2.5, 2.5)), alpha=0.5, zorder=3)

        eyebrow(ax, 0.05, 0.762, "the mechanism", color=MUTED, size=7.6)
        for lab, c, y, pr, fd in [("A", BLUE, yA, pA, fA), ("B", ORANGE, yB, pB, fB)]:
            ax.text(0.058, y + BH / 2, lab, fontsize=10.6, color=c,
                    fontweight="bold", va="center", ha="center", zorder=8)
            tinted(ax, X0, y, pr, BH, c, alpha=0.28, lw=1.6, r=0.010)
            tinted(ax, X0 + pr, y, fd, BH, MUTED, alpha=0.15, lw=1.1, r=0.010)
            ax.add_patch(FancyBboxPatch((X0 + pr, y), fd, BH,
                                        boxstyle="round,pad=0.003,rounding_size=0.010",
                                        fc="none", ec=MUTED, lw=0.0, hatch="////",
                                        alpha=0.55, zorder=5))
            if pr > 0.17:
                ax.text(X0 + pr / 2, y + BH / 2, "pricing", ha="center", va="center",
                        fontsize=8.2, color=c, fontweight="bold", zorder=7)
            if fd > 0.155:
                ax.text(X0 + pr + fd / 2, y + BH / 2, "feed", ha="center", va="center",
                        fontsize=8.2, color=MUTED, zorder=7)

        lo, hi = min(endA, endB), max(endA, endB)
        ax.annotate("", xy=(hi, 0.365), xytext=(lo, 0.365),
                    arrowprops=dict(arrowstyle="<|-|>", color=INK, lw=1.6,
                                    mutation_scale=11))
        ax.text((lo + hi) / 2, 0.318, "observed", ha="center", fontsize=8.8,
                color=INK, fontweight="bold")

        # what actually lands on disk: identical in all three panels
        ax.plot([0.05, 0.95], [0.258, 0.258], color=HAIR, lw=1.0, zorder=2)
        eyebrow(ax, 0.05, 0.225, "what reaches disk", color=MUTED, size=7.6)
        for xe in (endA, endB):
            ax.plot([xe], [0.163], "|", ms=15, mew=2.8, color=INK, zorder=6)
        ax.text(0.50, 0.112, "identical in every panel", ha="center", fontsize=8.2,
                color=MUTED, style="italic")
        ax.text(0.50, 0.070, verdict, ha="center", va="center", fontsize=9.6,
                color=vc, fontweight="bold", zorder=8,
                bbox=dict(boxstyle="round,pad=0.40", fc=vc, ec="none", alpha=0.12))

    fig.subplots_adjust(top=0.90, bottom=0.03, left=0.012, right=0.988, wspace=0.10)
    title(fig, "Three different markets. One identical dataset.", y=0.995)
    note(fig,
         "The bars differ in every panel; the two recorded timestamps do not. Read the strip along "
         "the bottom of each panel:\nwhat reaches disk is the same in all three, so no statistic "
         "computed from it can tell these worlds apart.", y=0.028)
    fig.savefig(FIG / "p2_three_worlds.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


# ------------------------------------------------------------------- FIG 5
def fig_anchoring():
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.3))
    for ax, t in zip(axes, ["Timing one book against the other",
                            "Timing each book against the game"]):
        ax.set_xlim(0, 10); ax.set_ylim(0, 1); ax.set_yticks([])
        ax.set_xlabel("time (minutes)", fontsize=9, color=MUTED, labelpad=6)
        ax.tick_params(colors=MUTED, labelsize=8.4)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.spines["bottom"].set_color(HAIR)
        ax.text(5.0, 1.13, t, ha="center", fontsize=10.4, color=INK, fontweight="bold")
        ax.axvspan(1.90, 2.10, color=GREEN, alpha=0.22, zorder=1)
        ax.plot([2, 2], [0.02, 0.92], color=GREEN, lw=3.4, zorder=3, solid_capstyle="round")
        ax.text(2.0, 0.955, "event", ha="center", fontsize=8.8, color=GREEN, fontweight="bold")

    ax = axes[0]
    fast = [2.4, 2.9, 3.4, 3.9, 4.4, 4.9, 5.4, 5.9, 6.4, 6.9, 7.4]
    ax.plot(fast, [0.63] * len(fast), "o", color=BLUE, ms=5.6, zorder=5,
            markeredgecolor="white", markeredgewidth=1.0)
    ax.plot([3.6, 7.2], [0.31, 0.31], "o", color=ORANGE, ms=8.0, zorder=5,
            markeredgecolor="white", markeredgewidth=1.1)
    ax.text(0.16, 0.72, "re-prices often", fontsize=8.6, color=BLUE, fontweight="bold")
    ax.text(0.16, 0.40, "re-prices rarely", fontsize=8.6, color=ORANGE, fontweight="bold")
    ax.annotate("", xy=(3.6, 0.47), xytext=(2.4, 0.47),
                arrowprops=dict(arrowstyle="<|-|>", color=RED, lw=1.5, mutation_scale=10))
    ax.text(3.0, 0.522, "apparent lead", fontsize=8.6, color=RED, ha="center",
            fontweight="bold")
    ax.text(5.4, 0.105, "the denser book arrives first by construction",
            fontsize=8.6, color=RED, ha="center", style="italic")

    ax = axes[1]
    for xe, y, c, lab in [(3.3, 0.63, BLUE, r"$\lambda_A$"),
                          (4.6, 0.31, ORANGE, r"$\lambda_B$")]:
        ax.annotate("", xy=(xe, y), xytext=(2.0, y),
                    arrowprops=dict(arrowstyle="<|-|>", color=c, lw=1.5, mutation_scale=10))
        ax.plot([xe], [y], "o", color=c, ms=8.6, zorder=5,
                markeredgecolor="white", markeredgewidth=1.1)
        ax.text((2.0 + xe) / 2, y + 0.085, lab, fontsize=11.5, color=c, ha="center")
    ax.text(5.4, 0.105, "each book measured against a clock neither controls",
            fontsize=8.6, color=GREEN, ha="center", style="italic")

    title(fig, "Why the estimand is anchored to the event", y=1.055)
    fig.savefig(FIG / "p2_anchoring.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


# ------------------------------------------------------------------- FIG 6
def fig_ladder():
    fig, ax = canvas(9.6, 6.2)
    rungs = [("Observed timestamps", "we hold these", IDENTIFIED, "have"),
             ("A common event clock", "event and quote times comparable", IDENTIFIED, "auditable"),
             ("One well defined price series", "the extraction rule is a free parameter",
              BOUNDED, "bounded"),
             ("Feed latency known or common mode", "not measurable from a public endpoint",
              FAILED, "open"),
             ("Pricing latency identified", "the quantity we actually want", FAILED, "blocked")]

    h, gap, y = 0.130, 0.041, 0.790
    for i, (lab, sub, c, tag) in enumerate(rungs):
        tinted(ax, 0.095, y, 0.660, h, c, alpha=0.09, lw=1.3, r=0.014)
        ax.add_patch(Rectangle((0.098, y + 0.010), 0.008, h - 0.020,
                               fc=c, ec="none", zorder=6))
        ax.text(0.128, y + h / 2 + 0.023, lab, fontsize=10.4, color=INK,
                va="center", fontweight="bold", zorder=7)
        ax.text(0.128, y + h / 2 - 0.026, sub, fontsize=8.5, color=MUTED,
                va="center", zorder=7)
        ax.text(0.878, y + h / 2, tag.upper(), fontsize=8.5, color=c, ha="center",
                va="center", fontweight="bold", zorder=7)
        if i < len(rungs) - 1:
            arrow(ax, (0.425, y), (0.425, y - gap + 0.005), lw=1.3, color=MUTED, ms=10)
        y -= (h + gap)

    leader(ax, (0.757, 0.255), (0.830, 0.150),
           "this rung decides\nthe paper", color=FAILED, size=8.8)

    for c, lab, yy in [(IDENTIFIED, "identifiable", 0.048),
                       (BOUNDED, "bounded only", 0.014),
                       (FAILED, "not identifiable here", -0.020)]:
        ax.add_patch(Rectangle((0.095, yy), 0.020, 0.020, fc=c, ec="none", alpha=0.85))
        ax.text(0.127, yy + 0.010, lab, fontsize=8.6, color=MUTED, va="center")

    title(fig, "The identification ladder", "each rung requires the one above it")
    fig.savefig(FIG / "p2_ladder.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


# ------------------------------------------------------------------- FIG 7
def fig_decision_tree():
    fig, ax = canvas(10.4, 6.0)

    def diamond(cx, cy, w, h, label):
        ax.add_patch(Polygon([[cx, cy + h], [cx + w, cy], [cx, cy - h], [cx - w, cy]],
                             closed=True, fc=CARD, ec=INK, lw=1.3, zorder=4,
                             joinstyle="round"))
        ax.text(cx, cy, label, ha="center", va="center", fontsize=8.8, color=INK,
                fontweight="bold", zorder=6, linespacing=1.5)

    tinted(ax, 0.355, 0.858, 0.29, 0.095, INK, alpha=0.05, lw=1.2)
    ax.text(0.50, 0.9055, "Observed lag", ha="center", va="center", fontsize=10.4,
            color=INK, fontweight="bold", zorder=7)

    diamond(0.50, 0.718, 0.150, 0.074, "common\nevent clock?")
    arrow(ax, (0.50, 0.858), (0.50, 0.796), lw=1.5)
    diamond(0.50, 0.520, 0.162, 0.074, "feed latency known\nor common mode?")
    arrow(ax, (0.50, 0.644), (0.50, 0.598), lw=1.5)
    ax.text(0.524, 0.622, "yes", fontsize=8.4, color=IDENTIFIED, fontweight="bold")
    diamond(0.50, 0.322, 0.155, 0.072, "price series\nwell defined?")
    arrow(ax, (0.50, 0.446), (0.50, 0.398), lw=1.5)
    ax.text(0.524, 0.424, "yes", fontsize=8.4, color=IDENTIFIED, fontweight="bold")
    arrow(ax, (0.50, 0.250), (0.50, 0.198), lw=1.5)
    ax.text(0.524, 0.226, "yes", fontsize=8.4, color=IDENTIFIED, fontweight="bold")

    def outcome(x, y, w, tag, label, c):
        tinted(ax, x, y, w, 0.105, c, alpha=0.11, lw=2.4)
        ax.text(x + w / 2, y + 0.068, tag, ha="center", va="center", fontsize=9.6,
                color=c, fontweight="bold", zorder=7)
        ax.text(x + w / 2, y + 0.032, label, ha="center", va="center", fontsize=8.5,
                color=MUTED, zorder=7)

    outcome(0.335, 0.088, 0.33, "OUTCOME A", "pricing latency identified", IDENTIFIED)
    arrow(ax, (0.345, 0.322), (0.224, 0.322), lw=1.4, color=BOUNDED)
    ax.text(0.285, 0.346, "no", fontsize=8.4, color=BOUNDED, ha="center", fontweight="bold")
    outcome(0.022, 0.270, 0.20, "OUTCOME B", "bounds only", BOUNDED)
    arrow(ax, (0.662, 0.520), (0.782, 0.520), lw=1.4, color=FAILED)
    ax.text(0.722, 0.544, "no", fontsize=8.4, color=FAILED, ha="center", fontweight="bold")
    outcome(0.780, 0.468, 0.20, "OUTCOME C", "not identifiable", FAILED)
    arrow(ax, (0.350, 0.718), (0.224, 0.718), lw=1.4, color=FAILED)
    ax.text(0.287, 0.742, "no", fontsize=8.4, color=FAILED, ha="center", fontweight="bold")
    ax.text(0.112, 0.718, "audit first", ha="center", va="center", fontsize=8.8,
            color=FAILED, fontweight="bold")

    ax.text(0.5, 0.024, "All three outcomes are publishable. C is a contribution, not a failure.",
            ha="center", fontsize=10.6, color=INK, fontweight="bold")
    title(fig, "The identification decision, walked through")
    fig.savefig(FIG / "p2_decision_tree.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


# ------------------------------------------------------------------- FIG 8
def fig_resolution():
    fig, ax = plt.subplots(figsize=(11.0, 4.6))
    ax.set_xlim(-4, 100); ax.set_ylim(0, 1); ax.axis("off")
    evs = [(2, "pitch", 0), (11, "ball", 0), (19, "pitch", 0), (26, "strike", 0),
           (34, "pitch", 0), (43, "single", 1), (52, "pitch", 0), (58, "ball", 0),
           (66, "pitch", 0), (73, "RUN", 2), (84, "pitch", 0), (91, "out", 1)]

    eyebrow(ax, -3, 0.900, "what happens in the game", color=MUTED)
    ax.plot([-1, 96], [0.755, 0.755], color=HAIR, lw=1.1, zorder=2)
    for x, lab, big in evs:
        c = GREEN if big == 2 else (BLUE if big == 1 else MUTED)
        ax.plot([x], [0.755], "o", ms=9.5 if big == 2 else (6.6 if big else 4.0),
                color=c, zorder=5, markeredgecolor="white",
                markeredgewidth=1.2 if big else 0.8)
        if big:
            ax.text(x, 0.828, lab, ha="center", fontsize=8.4 if big == 2 else 8.0,
                    color=c, fontweight="bold" if big == 2 else "normal")
        ax.plot([x, x], [0.732, 0.518], color=MUTED, lw=0.7, ls=(0, (1.6, 2)),
                alpha=0.5, zorder=2)

    eyebrow(ax, -3, 0.580, "what the instrument samples", color=MUTED)
    for i, x0 in enumerate([0, 31, 62]):
        w = min(31, 100 - x0)
        ax.add_patch(Rectangle((x0, 0.358), w, 0.155,
                               fc=(BLUE if i % 2 == 0 else ORANGE), alpha=0.11,
                               ec="white", lw=2.0, zorder=3))
        ax.text(x0 + w / 2, 0.462, f"poll window {i+1}", ha="center", va="center",
                fontsize=8.4, color=INK, zorder=6)
        ax.text(x0 + w / 2, 0.408, "31 s", ha="center", va="center",
                fontsize=7.8, color=MUTED, zorder=6)

    eyebrow(ax, -3, 0.242, "what we record", color=MUTED)
    for x0 in [0, 31, 62]:
        n = sum(1 for x, _, _ in evs if x0 <= x < x0 + 31)
        cx = min(x0 + 31, 96)
        ax.plot([cx, cx], [0.358, 0.202], color=INK, lw=0.9, ls=":", zorder=3)
        ax.add_patch(Polygon([[cx - 5, 0.182], [cx + 5, 0.182], [cx, 0.132]],
                             closed=True, fc=INK, ec="none", zorder=6))
        ax.text(cx, 0.080, f"{n} events collapse\ninto 1 observation", ha="center",
                fontsize=8.0, color=RED, linespacing=1.45, fontweight="bold")

    title(fig, "The resolution ceiling", "the game is finer than the instrument")
    note(fig,
         "A book that re-priced two seconds after the run and one that took twenty five are "
         "recorded identically.\nNo claim below the window is supportable, and the paper makes none.",
         y=0.040)
    fig.savefig(FIG / "p2_resolution.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


# ------------------------------------------------------------------- FIG 9
def fig_windows():
    fig, ax = canvas(10.0, 5.8)
    caps = ["Sharp benchmark book", "Two books at once", "Pitch-level measurement",
            "Weather and park", "Live market status", "Cross-book comparison",
            "Sub-minute timing"]
    june = [1, 0, 1, 1, 0, 0, 0]
    july = [0, 1, 0, 0, 1, 1, 0]

    x1, x2, w, hh = 0.475, 0.712, 0.183, 0.088
    for x, lab, c in [(x1, "june", BLUE), (x2, "july", ORANGE)]:
        eyebrow(ax, x + w / 2, 0.922, lab, color=c, size=9.6, ha="center")
        ax.text(x + w / 2, 0.874, "instrument", ha="center", fontsize=8.6, color=MUTED)

    y = 0.758
    for cap, a, b in zip(caps, june, july):
        ax.text(0.438, y + hh / 2, cap, fontsize=9.6, color=INK, ha="right", va="center")
        for x, v, c in [(x1, a, BLUE), (x2, b, ORANGE)]:
            if v:
                tinted(ax, x, y, w, hh, c, alpha=0.20, lw=1.5, r=0.010)
                ax.text(x + w / 2, y + hh / 2, "sees it", ha="center", va="center",
                        fontsize=8.6, color=c, fontweight="bold", zorder=7)
            else:
                card(ax, x, y, w, hh, fc=CARD, ec=HAIR, lw=1.1, r=0.010, z=3)
                ax.text(x + w / 2, y + hh / 2, "blind", ha="center", va="center",
                        fontsize=8.6, color=MUTED, zorder=7)
        y -= (hh + 0.016)

    ax.text(0.5, 0.070, "Neither instrument is better. They are blind in different places.",
            ha="center", fontsize=11.2, color=INK, fontweight="bold")
    ax.text(0.5, 0.016,
            "This is why a result from one could never confirm or contradict a result from the other.",
            ha="center", fontsize=9.5, color=MUTED)
    title(fig, "What each instrument can see")
    fig.savefig(FIG / "p2_windows.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


# ------------------------------------------------------------------- FIG 10
def fig_bridge():
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 5.0))
    for ax in axes:
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    ax = axes[0]
    eyebrow(ax, 0.5, 0.950, "paper 1", color=INK, size=10.2, ha="center")
    ax.text(0.5, 0.886, "information in prices", ha="center", fontsize=9.4,
            color=MUTED, style="italic")
    for lab, y, done in [("Public information", 0.672, False), ("Market", 0.428, False),
                         ("No increment", 0.184, True)]:
        tinted(ax, 0.20, y, 0.60, 0.130, GREEN, alpha=0.18 if done else 0.08,
               lw=1.7 if done else 1.2)
        ax.text(0.50, y + 0.065, lab, ha="center", va="center", fontsize=10.4,
                color=IDENTIFIED if done else INK, fontweight="bold", zorder=6)
    for a, b in [(0.672, 0.566), (0.428, 0.322)]:
        arrow(ax, (0.5, a), (0.5, b), lw=1.8)
    ax.text(0.5, 0.100, "answered", ha="center", fontsize=10, color=IDENTIFIED,
            fontweight="bold")

    ax = axes[1]
    eyebrow(ax, 0.5, 0.950, "paper 2", color=INK, size=10.2, ha="center")
    ax.text(0.5, 0.886, "formation of prices", ha="center", fontsize=9.4,
            color=MUTED, style="italic")
    tinted(ax, 0.22, 0.708, 0.56, 0.090, GREEN, alpha=0.08, lw=1.2)
    ax.text(0.5, 0.753, "Game event", ha="center", va="center", fontsize=10.2,
            color=INK, fontweight="bold", zorder=6)
    card(ax, 0.22, 0.518, 0.56, 0.100, fc=FOG, ec=HAIR, lw=1.1, z=3)
    ax.text(0.5, 0.568, "Hidden market process", ha="center", va="center",
            fontsize=10.2, color=MUTED, zorder=6)
    tinted(ax, 0.22, 0.338, 0.56, 0.090, GREEN, alpha=0.08, lw=1.2)
    ax.text(0.5, 0.383, "Observed timestamp", ha="center", va="center",
            fontsize=10.2, color=INK, fontweight="bold", zorder=6)
    tinted(ax, 0.15, 0.124, 0.70, 0.132, ORANGE, alpha=0.13, lw=1.7)
    ax.text(0.5, 0.219, "Identification depends", ha="center", va="center",
            fontsize=10.4, color=BOUNDED, fontweight="bold", zorder=6)
    ax.text(0.5, 0.166, "on assumptions", ha="center", va="center",
            fontsize=10.4, color=BOUNDED, fontweight="bold", zorder=6)
    for a, b in [(0.708, 0.626), (0.518, 0.434), (0.338, 0.264)]:
        arrow(ax, (0.5, a), (0.5, b), lw=1.4, color=MUTED, ls=(0, (2.5, 2)))

    title(fig, "From efficiency to identification", y=1.03)
    note(fig,
         "Paper 1 asked whether prices contain public information. Paper 2 asks whether prices\n"
         "reveal how that information entered the market.", y=0.018)
    fig.savefig(FIG / "p2_bridge.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    _init()
    for f in (fig_boundary, fig_race, fig_why_paper1, fig_three_worlds, fig_anchoring,
              fig_ladder, fig_decision_tree, fig_resolution, fig_windows, fig_bridge):
        f()
    print("wrote 10 figures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
