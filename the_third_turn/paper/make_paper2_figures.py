#!/usr/bin/env python3
"""Paper 2 conceptual figures — teach the identification problem before any equation.

Design philosophy carried over from Paper 1: each figure introduces a CONCEPT, and a
reader flipping through the figures alone should follow the paper's central argument.
Paper 1's figures explained why the statistical test answered the question; these
explain why the question is hard to answer at all.

None of these plots an unconfirmed empirical result (GD-15/GD-16).

    python3 the_third_turn/paper/make_paper2_figures.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import figstyle as fs  # noqa: E402

FIG = HERE / "figures"
BLUE, ORANGE, GREEN, RED = fs.PALETTE[0], fs.PALETTE[1], fs.PALETTE[2], fs.PALETTE[3]
SKY, PLUM = fs.PALETTE[4], fs.PALETTE[5]
INK, MUTED, GRID = fs.INK, fs.MUTED, fs.GRID
FOG = "#E8E8E8"


def box(ax, x, y, w, h, label, sub=None, fc="white", ec=INK, lw=1.4, tc=None, fsz=9.5, z=3):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.010,rounding_size=0.018",
                                fc=fc, ec=ec, lw=lw, zorder=z))
    ax.text(x + w / 2, y + h / 2 + (0.030 if sub else 0), label, ha="center", va="center",
            fontsize=fsz, color=tc or INK, zorder=z + 2, weight="bold")
    if sub:
        ax.text(x + w / 2, y + h / 2 - 0.042, sub, ha="center", va="center",
                fontsize=8.0, color=MUTED, zorder=z + 2)


def arrow(ax, p, q, color=INK, lw=1.6, style="-|>", ls="-", z=4, rad=0.0, ms=13):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=ms, lw=lw,
                                 color=color, zorder=z, linestyle=ls,
                                 connectionstyle=f"arc3,rad={rad}"))


# ----------------------------------------------------------------------------- FIG 1
def fig_information_race():
    """We observe only the last step of a process with several hidden stages."""
    fig, ax = plt.subplots(figsize=(10.6, 5.4))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    # the fog of unobservability
    ax.add_patch(Rectangle((0.185, 0.235), 0.545, 0.60, fc=FOG, ec=MUTED, lw=1.1,
                           ls=(0, (5, 3)), alpha=0.75, zorder=1))
    ax.text(0.4575, 0.795, "EVERYTHING IN HERE IS UNOBSERVABLE", ha="center", fontsize=9.6,
            color=MUTED, weight="bold", zorder=6)

    # event
    ax.plot([0.115, 0.115], [0.20, 0.90], color=GREEN, lw=2.6, zorder=5)
    ax.text(0.115, 0.925, "RUN SCORES", ha="center", fontsize=10.2, color=GREEN, weight="bold")
    ax.text(0.115, 0.163, "$t_E$", ha="center", fontsize=10.5, color=GREEN)

    rows = [
        (0.70, "Book A decides to re-price", BLUE, 0.30),
        (0.575, "Book A's feed publishes it", MUTED, 0.44),
        (0.45, "Book B decides to re-price", ORANGE, 0.52),
        (0.325, "Book B's feed publishes it", MUTED, 0.66),
    ]
    for yy, lab, c, xend in rows:
        arrow(ax, (0.115, yy), (xend, yy), color=c, lw=1.7, ms=12, z=5)
        ax.plot([xend], [yy], "o", ms=7, color=c, zorder=6)
        ax.text(xend + 0.018, yy, lab, fontsize=8.9, color=c, va="center", zorder=6)

    # what we actually see
    ax.plot([0.79, 0.79], [0.20, 0.90], color=INK, lw=2.2, zorder=5)
    ax.text(0.79, 0.925, "WE LOOK", ha="center", fontsize=10.2, color=INK, weight="bold")
    ax.text(0.79, 0.163, "poll at 31 s", ha="center", fontsize=8.6, color=MUTED)
    for yy, c in [(0.70, BLUE), (0.45, ORANGE)]:
        arrow(ax, (0.735, yy - 0.055), (0.785, yy - 0.055), color=c, lw=1.4, ls=(0, (2, 2)), ms=10)
    ax.plot([0.79, 0.79], [0.645, 0.395], "o", ms=8, color=INK, zorder=6)
    ax.text(0.815, 0.645, "one timestamp for A", fontsize=8.9, color=INK, va="center")
    ax.text(0.815, 0.395, "one timestamp for B", fontsize=8.9, color=INK, va="center")

    ax.text(0.5, 0.085,
            "Four internal events. Two recorded numbers.",
            ha="center", fontsize=11.2, color=INK, weight="bold")
    ax.text(0.5, 0.022,
            "The paper's problem is not measuring the gap. It is that the gap we can measure is a sum\n"
            "of things we cannot measure separately.",
            ha="center", fontsize=9.2, color=MUTED, linespacing=1.55)

    ax.set_title("The information race, and how little of it we see",
                 fontsize=13, color=INK, pad=14)
    fig.savefig(FIG / "p2_race.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


# ----------------------------------------------------------------------------- FIG 2
def fig_three_worlds():
    """THE figure: three different markets, one identical dataset."""
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.9))
    X0, HB, TOT = 0.11, 0.105, 0.72
    yA, yB = 0.60, 0.36

    worlds = [
        ("WORLD A", "A prices fast, feeds equal",
         0.20, 0.44, 0.28, 0.28, "the lag is real: A is quicker", GREEN),
        ("WORLD B", "identical pricing, B's feed is slow",
         0.28, 0.28, 0.20, 0.44, "the lag is pure plumbing", RED),
        ("WORLD C", "both differ, and offset",
         0.24, 0.38, 0.24, 0.34, "the lag mixes the two", ORANGE),
    ]
    for ax, (name, sub, pA, pB, fA, fB, verdict, vc) in zip(axes, worlds):
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
        ax.text(0.5, 0.95, name, ha="center", fontsize=12, color=INK, weight="bold")
        ax.text(0.5, 0.875, sub, ha="center", fontsize=8.8, color=MUTED)
        for bk, c, yy, pr, fd in [("A", BLUE, yA, pA, fA), ("B", ORANGE, yB, pB, fB)]:
            ax.text(0.035, yy + HB / 2, bk, fontsize=10, color=c, weight="bold", va="center")
            ax.add_patch(Rectangle((X0, yy), pr, HB, fc=c, ec="white", lw=1.2, zorder=3))
            ax.add_patch(Rectangle((X0 + pr, yy), fd, HB, fc=MUTED, ec="white", lw=1.2,
                                   alpha=0.38, zorder=3))
            ax.text(X0 + pr / 2, yy + HB / 2, "pricing", ha="center", va="center",
                    fontsize=7.4, color="white", weight="bold", zorder=5)
            ax.text(X0 + pr + fd / 2, yy + HB / 2, "feed", ha="center", va="center",
                    fontsize=7.4, color=INK, zorder=5)
        # identical observed endpoints, with guides so the eye sees they never move
        for yy, pr, fd in [(yA, pA, fA), (yB, pB, fB)]:
            xe = X0 + pr + fd
            ax.plot([xe, xe], [0.245, 0.775], color=INK, lw=1.0, ls=(0, (3, 3)),
                    alpha=0.55, zorder=2)
            ax.plot([xe], [yy + HB / 2], "|", ms=18, color=INK, mew=2.6, zorder=6)
        ax.annotate("", xy=(X0 + pB + fB, 0.265), xytext=(X0 + pA + fA, 0.265),
                    arrowprops=dict(arrowstyle="<|-|>", color=INK, lw=1.7))
        ax.text((X0 * 2 + pA + fA + pB + fB) / 2, 0.205, "observed lag",
                ha="center", fontsize=9, color=INK, weight="bold")
        ax.add_patch(Rectangle((0.06, 0.055), 0.88, 0.085, fc=vc, ec="none", alpha=0.13, zorder=2))
        ax.text(0.5, 0.0975, verdict, ha="center", va="center", fontsize=9.2,
                color=vc, weight="bold", zorder=4)

    fig.subplots_adjust(top=0.78)
    fig.suptitle("Three different markets. One identical dataset.",
                 fontsize=13.5, color=INK, y=1.045)
    fig.text(0.5, -0.045,
             "In every panel the two observed timestamps are the same, so the data are the same. "
             "The mechanisms are not.\nNo statistic computed from timestamps alone can tell these "
             "worlds apart. That is the identification problem.",
             ha="center", fontsize=9.6, color=INK, linespacing=1.6)
    fig.savefig(FIG / "p2_three_worlds.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


# ----------------------------------------------------------------------------- FIG 3
def fig_why_paper1_could_ignore():
    """Same visual language as Paper 1's opening figure; different question."""
    fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.8))
    for ax in axes:
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    ax = axes[0]
    ax.text(0.5, 0.95, "PAPER 1", ha="center", fontsize=12, color=INK, weight="bold")
    ax.text(0.5, 0.885, "does the variable beat the price?", ha="center", fontsize=9, color=MUTED)
    steps = [("Public variable", 0.66), ("Sharp market price", 0.40), ("Outcome", 0.14)]
    for lab, yy in steps:
        box(ax, 0.22, yy, 0.56, 0.145, lab, fc="#F2F7FA")
    for y0, y1 in [(0.66, 0.545), (0.40, 0.285)]:
        arrow(ax, (0.5, y0), (0.5, y1), lw=1.9)
    ax.text(0.845, 0.40, "every node\nobservable", fontsize=8.6, color=GREEN,
            ha="center", va="center", weight="bold", linespacing=1.5)

    ax = axes[1]
    ax.text(0.5, 0.95, "PAPER 2", ha="center", fontsize=12, color=INK, weight="bold")
    ax.text(0.5, 0.885, "how did the price get there?", ha="center", fontsize=9, color=MUTED)
    steps2 = [("Game event", 0.735, "white", INK, False),
              ("Book pricing", 0.515, FOG, MUTED, True),
              ("Feed publication", 0.295, FOG, MUTED, True),
              ("Collector observes", 0.075, "white", INK, False)]
    for lab, yy, fc, tc, hidden in steps2:
        box(ax, 0.22, yy, 0.56, 0.135, lab, fc=fc, ec=MUTED if hidden else INK,
            lw=1.1 if hidden else 1.4, tc=tc)
        if hidden:
            ax.text(0.845, yy + 0.0675, "hidden", fontsize=8.4, color=RED,
                    ha="center", va="center", weight="bold")
    for y0, y1 in [(0.735, 0.655), (0.515, 0.435), (0.295, 0.215)]:
        arrow(ax, (0.5, y0), (0.5, y1), lw=1.6, color=MUTED, ls=(0, (3, 2)))

    fig.subplots_adjust(top=0.84)
    fig.suptitle("Why Paper 1 never had to face this", fontsize=13.5, color=INK, y=1.03)
    fig.text(0.5, -0.05,
             "Paper 1 compared two endpoints and could stay agnostic about the machinery between them.\n"
             "Paper 2's question is the machinery, and two of its four stages are invisible.",
             ha="center", fontsize=9.6, color=INK, linespacing=1.6)
    fig.savefig(FIG / "p2_why_paper1.png", dpi=200, bbox_inches="tight")
    plt.close(fig)



# ----------------------------------------------------------------------------- FIG 3b
def fig_anchoring():
    """Why book-to-book timing fails and event-anchoring is required."""
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.3))
    for ax, title in zip(axes, ["Timing one book against the other: confounded",
                                "Timing each book against the game: the estimand"]):
        ax.set_xlim(0, 10); ax.set_ylim(0, 1); ax.set_yticks([])
        ax.set_xlabel("time (minutes)")
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.text(5.0, 1.10, title, ha="center", fontsize=10.4, color=INK, weight="bold")
        ax.axvline(2.0, color=GREEN, lw=2.2, zorder=2)

    ax = axes[0]
    ax.text(2.0, 0.93, "event", ha="center", fontsize=9, color=GREEN, weight="bold")
    fast = [2.4, 2.9, 3.4, 3.9, 4.4, 4.9, 5.4, 5.9, 6.4, 6.9, 7.4]
    ax.plot(fast, [0.62] * len(fast), "o", color=BLUE, ms=6, zorder=4)
    ax.plot([3.6, 7.2], [0.30, 0.30], "o", color=ORANGE, ms=8.5, zorder=4)
    ax.text(0.15, 0.70, "re-prices often", fontsize=8.6, color=BLUE, weight="bold")
    ax.text(0.15, 0.38, "re-prices rarely", fontsize=8.6, color=ORANGE, weight="bold")
    ax.annotate("", xy=(3.6, 0.46), xytext=(2.4, 0.46),
                arrowprops=dict(arrowstyle="<|-|>", color=RED, lw=1.6))
    ax.text(3.0, 0.51, "'lead'", fontsize=9, color=RED, ha="center", weight="bold")
    ax.text(5.2, 0.11, "the dense book reaches any price level first\nby construction, informed or not",
            fontsize=8.6, color=RED, ha="center", style="italic", linespacing=1.5)

    ax = axes[1]
    ax.text(2.0, 0.93, "event $t_E$", ha="center", fontsize=9, color=GREEN, weight="bold")
    ax.plot([3.3], [0.62], "o", color=BLUE, ms=9, zorder=4)
    ax.plot([4.6], [0.30], "o", color=ORANGE, ms=9, zorder=4)
    for xe, yy, c, lab in [(3.3, 0.62, BLUE, "$\\lambda_A$"), (4.6, 0.30, ORANGE, "$\\lambda_B$")]:
        ax.annotate("", xy=(xe, yy), xytext=(2.0, yy),
                    arrowprops=dict(arrowstyle="<|-|>", color=c, lw=1.6))
        ax.text((2.0 + xe) / 2, yy + 0.07, lab, fontsize=11, color=c, ha="center")
    ax.text(5.2, 0.11, "each book measured against a clock\nneither book controls",
            fontsize=8.6, color=GREEN, ha="center", style="italic", linespacing=1.5)

    fig.savefig(FIG / "p2_anchoring.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


# ----------------------------------------------------------------------------- FIG 4
def fig_identification_ladder():
    """Paper 1's elimination-ladder language, applied to identification requirements."""
    fig, ax = plt.subplots(figsize=(9.8, 6.1))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    rungs = [
        ("Observed timestamps", "we have these", GREEN, "HAVE"),
        ("A common event clock", "event and quote times comparable", GREEN, "AUDITABLE"),
        ("A single well-defined price series", "main-line rule fixed and tested", ORANGE, "BOUNDED"),
        ("Feed latency known or common-mode", "no way to measure it from outside", RED, "OPEN"),
        ("Pricing latency identified", "the quantity we actually want", RED, "BLOCKED"),
    ]
    h, gap = 0.135, 0.038
    y = 0.80
    for i, (lab, sub, c, tag) in enumerate(rungs):
        ax.add_patch(FancyBboxPatch((0.10, y), 0.66, h,
                                    boxstyle="round,pad=0.008,rounding_size=0.015",
                                    fc=c, ec=c, lw=1.4, alpha=0.16, zorder=3))
        ax.add_patch(Rectangle((0.10, y), 0.014, h, fc=c, ec="none", zorder=4))
        ax.text(0.145, y + h / 2 + 0.024, lab, fontsize=10.3, color=INK, va="center", weight="bold")
        ax.text(0.145, y + h / 2 - 0.030, sub, fontsize=8.4, color=MUTED, va="center")
        ax.text(0.885, y + h / 2, tag, fontsize=8.8, color=c, ha="center", va="center",
                weight="bold")
        if i < len(rungs) - 1:
            arrow(ax, (0.43, y), (0.43, y - gap + 0.004), lw=1.5, color=MUTED, ms=11)
        y -= (h + gap)

    for c, lab, yy in [(GREEN, "identifiable", 0.055), (ORANGE, "bounded only", 0.020),
                       (RED, "not identifiable with this instrument", -0.015)]:
        ax.add_patch(Rectangle((0.10, yy), 0.022, 0.022, fc=c, ec="none", alpha=0.8))
        ax.text(0.135, yy + 0.011, lab, fontsize=8.6, color=INK, va="center")

    ax.set_title("The identification ladder: each rung requires the one above it",
                 fontsize=13, color=INK, pad=16)
    fig.text(0.5, -0.075,
             "The ladder is climbed from the top. We hold the first two rungs; the third is a\n"
             "methodological choice we can fix; the fourth is not obtainable from public endpoints,\n"
             "and it is the one the fifth depends on.",
             ha="center", fontsize=9.4, color=INK, linespacing=1.6)
    fig.savefig(FIG / "p2_ladder.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


# ----------------------------------------------------------------------------- FIG 5
def fig_resolution_ceiling():
    """Draw the sampling window over real game granularity."""
    fig, ax = plt.subplots(figsize=(11.0, 4.4))
    ax.set_xlim(-2, 96); ax.set_ylim(0, 1); ax.axis("off")

    ax.plot([-1, 95], [0.70, 0.70], color=INK, lw=1.3, zorder=2)
    evs = [(2, "pitch"), (11, "ball"), (19, "pitch"), (26, "strike"), (34, "pitch"),
           (43, "single"), (52, "pitch"), (58, "ball"), (66, "pitch"), (73, "RUN"),
           (84, "pitch"), (91, "out")]
    for x, lab in evs:
        big = lab in ("RUN", "single", "out")
        c = GREEN if lab == "RUN" else (BLUE if big else MUTED)
        ax.plot([x], [0.70], "o", ms=10 if lab == "RUN" else (7 if big else 4.5),
                color=c, zorder=4)
        ax.text(x, 0.775, lab, ha="center", fontsize=8.0 if big else 7.2,
                color=c, weight="bold" if lab == "RUN" else "normal", rotation=0)
    ax.text(-1, 0.855, "what happens in the game", fontsize=9.4, color=INK, weight="bold")

    # the poll windows
    for i, x0 in enumerate([0, 31, 62]):
        ax.add_patch(Rectangle((x0, 0.36), 31, 0.16, fc=ORANGE, ec="white", lw=2.0,
                               alpha=0.28, zorder=3))
        ax.text(x0 + 15.5, 0.44, f"poll window {i+1}\n31 s", ha="center", va="center",
                fontsize=8.4, color=INK, linespacing=1.4, zorder=5)
    ax.text(-1, 0.565, "what our instrument samples", fontsize=9.4, color=ORANGE, weight="bold")

    ax.plot([31, 62, 93], [0.24, 0.24, 0.24], "v", ms=11, color=INK, zorder=5)
    ax.text(-1, 0.155, "what we record", fontsize=9.4, color=INK, weight="bold")
    for x in (31, 62, 93):
        ax.text(x, 0.175, "one\nquote", ha="center", fontsize=7.6, color=INK, linespacing=1.35)
        ax.plot([x, x], [0.36, 0.28], color=INK, lw=0.9, ls=":", zorder=3)

    ax.text(47, 0.055,
            "Everything inside a window collapses to a single observation. "
            "A book that re-priced 2 s after the run\nand one that re-priced 25 s after it are "
            "recorded identically. Sub-window claims are unsupportable.",
            ha="center", fontsize=9.3, color=INK, linespacing=1.6)
    ax.set_title("The resolution ceiling: the game is finer than the instrument",
                 fontsize=13, color=INK, pad=14)
    fig.savefig(FIG / "p2_resolution.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


# ----------------------------------------------------------------------------- FIG 6
def fig_instrument_windows():
    """Two instruments, two different windows onto the same market."""
    fig, ax = plt.subplots(figsize=(10.2, 5.6))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    caps = ["Sharp benchmark book", "Multiple books at once", "Pitch-level (Statcast)",
            "Weather and park", "Live market status", "Cross-book comparison",
            "Sub-minute timing"]
    june = [1, 0, 1, 1, 0, 0, 0]
    july = [0, 1, 0, 0, 1, 1, 0]

    x1, x2, w = 0.46, 0.70, 0.175
    ax.text(x1 + w / 2, 0.90, "JUNE\ninstrument", ha="center", fontsize=10.2, color=BLUE,
            weight="bold", linespacing=1.4)
    ax.text(x2 + w / 2, 0.90, "JULY\ninstrument", ha="center", fontsize=10.2, color=ORANGE,
            weight="bold", linespacing=1.4)

    y = 0.775
    hh = 0.088
    for cap, a, b in zip(caps, june, july):
        ax.text(0.42, y + hh / 2, cap, fontsize=9.3, color=INK, ha="right", va="center")
        for x, v, c in [(x1, a, BLUE), (x2, b, ORANGE)]:
            ax.add_patch(Rectangle((x, y), w, hh, fc=c if v else "white", ec=c if v else GRID,
                                   lw=1.3, alpha=0.85 if v else 1.0, zorder=3))
            ax.text(x + w / 2, y + hh / 2, "sees it" if v else "blind",
                    ha="center", va="center", fontsize=8.4,
                    color="white" if v else MUTED, weight="bold" if v else "normal", zorder=5)
        y -= (hh + 0.014)

    ax.text(0.5, 0.075,
            "Neither instrument is better. They are blind in different places.",
            ha="center", fontsize=11, color=INK, weight="bold")
    ax.text(0.5, 0.012,
            "This is why the July data cannot replicate the June study, and why a difference between\n"
            "them could never be attributed to the passage of time.",
            ha="center", fontsize=9.3, color=MUTED, linespacing=1.6)
    ax.set_title("What each instrument can see", fontsize=13, color=INK, pad=14)
    fig.savefig(FIG / "p2_windows.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


# ----------------------------------------------------------------------------- FIG 7
def fig_decision_tree():
    """Walk the reader through the identification decision, Third Turn Protocol style."""
    fig, ax = plt.subplots(figsize=(10.6, 6.0))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    box(ax, 0.355, 0.855, 0.29, 0.10, "Observed lag", fc="#F2F7FA")

    def diamond(cx, cy, w, h, label):
        ax.add_patch(Polygon([[cx, cy + h], [cx + w, cy], [cx, cy - h], [cx - w, cy]],
                             closed=True, fc="white", ec=INK, lw=1.4, zorder=3))
        ax.text(cx, cy, label, ha="center", va="center", fontsize=8.9, color=INK,
                weight="bold", zorder=5)

    diamond(0.50, 0.715, 0.145, 0.072, "common\nevent clock?")
    arrow(ax, (0.50, 0.855), (0.50, 0.792), lw=1.6)

    diamond(0.50, 0.520, 0.155, 0.072, "feed latency known\nor common-mode?")
    arrow(ax, (0.50, 0.643), (0.50, 0.597), lw=1.6)
    ax.text(0.525, 0.622, "yes", fontsize=8.4, color=GREEN, weight="bold")

    diamond(0.50, 0.325, 0.150, 0.070, "price series\nwell defined?")
    arrow(ax, (0.50, 0.448), (0.50, 0.400), lw=1.6)
    ax.text(0.525, 0.427, "yes", fontsize=8.4, color=GREEN, weight="bold")

    arrow(ax, (0.50, 0.255), (0.50, 0.205), lw=1.6)
    ax.text(0.525, 0.232, "yes", fontsize=8.4, color=GREEN, weight="bold")
    box(ax, 0.335, 0.095, 0.33, 0.105, "OUTCOME A", "pricing latency identified",
        fc="#E7F4EE", ec=GREEN, lw=1.7, tc=GREEN)

    # side exits
    arrow(ax, (0.345, 0.325), (0.215, 0.325), lw=1.5, color=ORANGE)
    ax.text(0.283, 0.348, "no", fontsize=8.4, color=ORANGE, weight="bold", ha="center")
    box(ax, 0.015, 0.270, 0.20, 0.105, "OUTCOME B", "bounds only", fc="#FBF1E6",
        ec=ORANGE, lw=1.7, tc=ORANGE)

    arrow(ax, (0.655, 0.520), (0.785, 0.520), lw=1.5, color=RED)
    ax.text(0.720, 0.543, "no", fontsize=8.4, color=RED, weight="bold", ha="center")
    box(ax, 0.785, 0.465, 0.20, 0.105, "OUTCOME C", "not identifiable", fc="#FBEAE6",
        ec=RED, lw=1.7, tc=RED)

    arrow(ax, (0.355, 0.715), (0.215, 0.715), lw=1.5, color=RED)
    ax.text(0.285, 0.738, "no", fontsize=8.4, color=RED, weight="bold", ha="center")
    ax.text(0.115, 0.715, "audit first\n(Section 5.6)", ha="center", va="center",
            fontsize=8.6, color=RED, linespacing=1.45)

    ax.text(0.5, 0.038,
            "All three outcomes are publishable. C is a contribution, not a failure.",
            ha="center", fontsize=10.6, color=INK, weight="bold")
    ax.set_title("The identification decision, walked through",
                 fontsize=13, color=INK, pad=14)
    fig.savefig(FIG / "p2_decision_tree.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    fs.setup()
    fig_information_race()
    fig_three_worlds()
    fig_why_paper1_could_ignore()
    fig_anchoring()
    fig_identification_ladder()
    fig_resolution_ceiling()
    fig_instrument_windows()
    fig_decision_tree()
    print("wrote 7: p2_race, p2_three_worlds, p2_why_paper1, p2_ladder, "
          "p2_resolution, p2_windows, p2_decision_tree")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
