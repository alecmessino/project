#!/usr/bin/env python3
"""Paper 2 conceptual figures — the identification story, drawn.

These are DESIGN figures: they illustrate the estimand and the identification problem.
None of them plots an unconfirmed empirical result (GD-15/GD-16); the two that use data
use only promoted standing-knowledge facts about the instrument.

    python3 the_third_turn/paper/make_paper2_figures.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import figstyle as fs  # noqa: E402

FIG = HERE / "figures"
BLUE, ORANGE, GREEN, RED = fs.PALETTE[0], fs.PALETTE[1], fs.PALETTE[2], fs.PALETTE[3]
INK, MUTED, GRID = fs.INK, fs.MUTED, fs.GRID


def _box(ax, x, y, w, h, label, sub=None, fc="white", ec=INK, lw=1.4, fs_=9.5, z=3):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.02",
                                fc=fc, ec=ec, lw=lw, zorder=z))
    ax.text(x + w / 2, y + h / 2 + (0.035 if sub else 0), label, ha="center", va="center",
            fontsize=fs_, color=INK, zorder=z + 1, weight="bold")
    if sub:
        ax.text(x + w / 2, y + h / 2 - 0.045, sub, ha="center", va="center",
                fontsize=8.2, color=MUTED, zorder=z + 1)


def _arrow(ax, p, q, color=INK, lw=1.6, style="-|>", ls="-", z=4, rad=0.0):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=13, lw=lw,
                                 color=color, zorder=z, linestyle=ls,
                                 connectionstyle=f"arc3,rad={rad}"))


def fig_three_latencies():
    """The decomposition that governs the paper: three latencies, one observable."""
    fig, ax = plt.subplots(figsize=(10.4, 4.5))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    y = 0.52; h = 0.19; w = 0.165
    xs = [0.03, 0.27, 0.51, 0.78]
    _box(ax, xs[0], y, w, h, "Game event", "run scores at $t_E$", fc="#F4F7FA")
    _box(ax, xs[1], y, w, h, "Bookmaker", "revises price", fc="#F4F7FA")
    _box(ax, xs[2], y, w, h, "Feed", "publishes quote", fc="#F4F7FA")
    _box(ax, xs[3], y, w, h, "Our collector", "observes at 31 s", fc="#F4F7FA")

    for i in range(3):
        _arrow(ax, (xs[i] + w, y + h / 2), (xs[i + 1], y + h / 2), lw=1.8)

    labs = [("pricing latency", "$\\lambda^{\\mathrm{price}}$", BLUE),
            ("feed latency", "$\\lambda^{\\mathrm{feed}}$", ORANGE),
            ("observation latency", "$\\lambda^{\\mathrm{obs}}$", GREEN)]
    for i, (name, sym, c) in enumerate(labs):
        xm = (xs[i] + w + xs[i + 1]) / 2
        ax.text(xm, y + h + 0.155, sym, ha="center", va="center", fontsize=12, color=c, weight="bold")
        ax.text(xm, y + h + 0.085, name, ha="center", va="center", fontsize=8.4, color=c)
        ax.plot([xm, xm], [y + h + 0.045, y + h + 0.008], color=c, lw=0.9, zorder=2)

    # what we actually observe
    ax.add_patch(Rectangle((xs[0] + w / 2, 0.27), xs[3] + w / 2 - xs[0] - w / 2, 0.115,
                           fc="#FBEEE6", ec=ORANGE, lw=1.3, zorder=2))
    ax.text((xs[0] + xs[3] + w) / 2, 0.327,
            "what the data contain:  $\\Delta t \\;=\\; \\lambda^{\\mathrm{price}} + "
            "\\lambda^{\\mathrm{feed}} + \\lambda^{\\mathrm{obs}}$   (one number, three causes)",
            ha="center", va="center", fontsize=10.5, color=INK, zorder=5)

    ax.text(0.5, 0.155,
            "Only $\\lambda^{\\mathrm{price}}$ is economics. The other two are plumbing.",
            ha="center", fontsize=10.2, color=INK, weight="bold")
    ax.text(0.5, 0.065,
            "A single book cannot separate them. The paper asks under what conditions the\n"
            "difference between two books can, and reports honestly when it cannot.",
            ha="center", fontsize=9.2, color=MUTED, linespacing=1.5)

    ax.set_title("The three latencies between an event and an observed price change",
                 fontsize=12.5, color=INK, pad=12)
    fig.savefig(FIG / "p2_three_latencies.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def fig_identification():
    """Why differencing two books may (or may not) cancel the plumbing."""
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.4))

    X0, HB = 0.16, 0.085
    yA, yB = 0.60, 0.31

    def panel(ax, title, priceA, priceB, plumbA, plumbB, ok, note):
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
        ax.text(0.5, 0.95, title, ha="center", fontsize=10.5, color=INK, weight="bold")
        for bk, c, yy, pr, pl in [("Book A", BLUE, yA, priceA, plumbA),
                                  ("Book B", ORANGE, yB, priceB, plumbB)]:
            ax.text(0.02, yy + HB / 2, bk, fontsize=9.2, color=c, weight="bold", va="center")
            ax.add_patch(Rectangle((X0, yy), pr, HB, fc=c, ec="white", lw=1.2, zorder=3))
            ax.add_patch(Rectangle((X0 + pr, yy), pl, HB, fc=MUTED if ok else RED,
                                   ec="white", lw=1.2, alpha=0.30 if ok else 0.45, zorder=3))
            ax.plot([X0 + pr + pl, X0 + pr + pl], [yy - 0.03, yy + HB + 0.03],
                    color=INK, lw=1.0, ls=":", zorder=4)
        ax.text(X0 + 0.10, 0.80, "pricing", fontsize=8.4, color=INK, ha="center")
        ax.text(X0 + 0.42, 0.80, "plumbing (feed + observation)", fontsize=8.4,
                color=MUTED if ok else RED, ha="center")
        # observed totals bracket
        tA, tB = X0 + priceA + plumbA, X0 + priceB + plumbB
        ax.annotate("", xy=(tB, 0.205), xytext=(tA, 0.205),
                    arrowprops=dict(arrowstyle="<|-|>", color=GREEN if ok else RED, lw=1.6))
        ax.text((tA + tB) / 2, 0.155, "observed $\\Delta t$", ha="center", fontsize=8.8,
                color=GREEN if ok else RED, weight="bold")
        ax.text(0.5, 0.055, note, ha="center", fontsize=10.2,
                color=GREEN if ok else RED, weight="bold")

    # LEFT: plumbing equal -> observed gap == pricing gap
    panel(axes[0], "If plumbing is common-mode",
          0.20, 0.34, 0.30, 0.30, True,
          "observed $\\Delta t$ = the pricing gap  ✓")
    axes[0].annotate("", xy=(X0 + 0.34, 0.455), xytext=(X0 + 0.20, 0.455),
                     arrowprops=dict(arrowstyle="<|-|>", color=GREEN, lw=1.6))
    axes[0].text(X0 + 0.27, 0.485, "true pricing gap", ha="center", fontsize=8.8,
                 color=GREEN, weight="bold")

    # RIGHT: pricing equal, plumbing unequal -> observed gap is pure artifact
    panel(axes[1], "If plumbing differs by book",
          0.26, 0.26, 0.16, 0.42, False,
          "observed $\\Delta t$ is pure plumbing  ✗")
    axes[1].text(X0 + 0.13, 0.485, "pricing gap = 0", ha="center", fontsize=8.8,
                 color=INK, weight="bold")

    fig.subplots_adjust(top=0.80)
    fig.suptitle("The identification problem, in one picture",
                 fontsize=12.5, color=INK, y=1.06)
    fig.savefig(FIG / "p2_identification.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def fig_anchoring():
    """Why book-to-book timing fails and event-anchoring is required."""
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.2))

    # left: book-to-book (confounded by update frequency)
    ax = axes[0]
    ax.set_title("Book-to-book timing: confounded", fontsize=11, color=INK, pad=10)
    ax.set_xlim(0, 10); ax.set_ylim(0, 1); ax.set_yticks([]); ax.set_xlabel("time (minutes)")
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.axvline(2.0, color=GREEN, lw=2, zorder=2)
    ax.text(2.0, 0.94, "event", ha="center", fontsize=9, color=GREEN, weight="bold")
    fast = [2.4, 2.9, 3.4, 3.9, 4.4, 4.9, 5.4, 5.9, 6.4, 6.9, 7.4]
    slow = [3.6, 7.2]
    ax.plot(fast, [0.62] * len(fast), "o", color=BLUE, ms=6, zorder=4)
    ax.plot(slow, [0.32] * len(slow), "o", color=ORANGE, ms=8, zorder=4)
    ax.text(0.15, 0.62, "dense book", fontsize=9, color=BLUE, va="center", weight="bold")
    ax.text(0.15, 0.32, "sparse book", fontsize=9, color=ORANGE, va="center", weight="bold")
    ax.annotate("", xy=(3.6, 0.47), xytext=(2.4, 0.47),
                arrowprops=dict(arrowstyle="<|-|>", color=RED, lw=1.5))
    ax.text(3.0, 0.52, "'lead'", fontsize=9, color=RED, ha="center", weight="bold")
    ax.text(5.0, 0.13, "the dense book arrives first by construction",
            fontsize=8.8, color=RED, ha="center", style="italic")

    # right: event-anchored
    ax = axes[1]
    ax.set_title("Event-anchored: the estimand", fontsize=11, color=INK, pad=10)
    ax.set_xlim(0, 10); ax.set_ylim(0, 1); ax.set_yticks([]); ax.set_xlabel("time (minutes)")
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.axvline(2.0, color=GREEN, lw=2, zorder=2)
    ax.text(2.0, 0.94, "event $t_E$", ha="center", fontsize=9, color=GREEN, weight="bold")
    ax.plot([3.3], [0.62], "o", color=BLUE, ms=9, zorder=4)
    ax.plot([4.6], [0.32], "o", color=ORANGE, ms=9, zorder=4)
    ax.annotate("", xy=(3.3, 0.62), xytext=(2.0, 0.62),
                arrowprops=dict(arrowstyle="<|-|>", color=BLUE, lw=1.5))
    ax.annotate("", xy=(4.6, 0.32), xytext=(2.0, 0.32),
                arrowprops=dict(arrowstyle="<|-|>", color=ORANGE, lw=1.5))
    ax.text(2.65, 0.69, "$\\lambda_A$", fontsize=11, color=BLUE, ha="center")
    ax.text(3.3, 0.39, "$\\lambda_B$", fontsize=11, color=ORANGE, ha="center")
    ax.text(5.0, 0.13, "each book timed against the game, not each other",
            fontsize=8.8, color=GREEN, ha="center", style="italic")

    fig.subplots_adjust(top=0.80)
    fig.suptitle("Why the estimand is anchored to the event", fontsize=12.5, color=INK, y=1.06)
    fig.savefig(FIG / "p2_anchoring.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def fig_resolution():
    """The 31 s sampling floor: what the instrument can and cannot resolve."""
    fig, ax = plt.subplots(figsize=(9.6, 3.9))
    ax.set_xlim(0.5, 3000); ax.set_xscale("log")
    ax.set_ylim(0, 1); ax.set_yticks([])
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.axvspan(0.5, 31, color=RED, alpha=0.13, zorder=1)
    ax.axvspan(31, 3000, color=GREEN, alpha=0.10, zorder=1)
    ax.axvline(31, color=INK, lw=2, zorder=4)
    ax.text(31, 1.02, "31 s sampling floor", ha="center", fontsize=10, color=INK, weight="bold")
    ax.text(4.5, 0.60, "UNRESOLVABLE", ha="center", fontsize=11.5, color=RED, weight="bold")
    ax.text(4.5, 0.44, "sub-poll price formation\nHFT-scale latency", ha="center",
            fontsize=8.8, color=RED, linespacing=1.5)
    ax.text(300, 0.60, "RESOLVABLE", ha="center", fontsize=11.5, color=GREEN, weight="bold")
    ax.text(300, 0.44, "bookmaker reaction to game events\nmulti-second to minute scale",
            ha="center", fontsize=8.8, color=GREEN, linespacing=1.5)
    ax.set_xlabel("latency scale (seconds, log)", fontsize=10)
    ax.text(0.5, -0.34,
            "The instrument is honest about its own floor: any claim below 31 s is unsupportable "
            "with these data,\nand the paper makes none. The economically interesting scale for a "
            "bookmaker sits above it.",
            transform=ax.transAxes, ha="center", fontsize=9, color=MUTED, linespacing=1.5)
    ax.set_title("What this instrument can resolve", fontsize=12.5, color=INK, pad=16)
    fig.savefig(FIG / "p2_resolution.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    fs.setup()
    fig_three_latencies()
    fig_identification()
    fig_anchoring()
    fig_resolution()
    print("wrote: p2_three_latencies.png, p2_identification.png, p2_anchoring.png, p2_resolution.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
