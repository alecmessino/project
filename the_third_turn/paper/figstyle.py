"""Shared publication figure style — one coherent visual system for the paper.

Okabe-Ito categorical palette (CVD-safe, validator-passed), reserved status colors,
recessive axes, consistent typography. Import and call `setup()` before plotting;
use PALETTE for categorical series and PASS/FAIL only for status marks.
"""

from __future__ import annotations

import numpy as np

# Okabe-Ito — colorblind-safe scientific standard (validated for CVD separation)
PALETTE = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#56B4E9", "#CC79A7"]
INK, MUTED, GRID = "#222222", "#666666", "#DDDDDD"
PASS, FAIL, NA = "#1B7837", "#B2182B", "#999999"   # reserved status (with symbols, never color-alone)
NEUTRAL = "#8C8C8C"                                 # for near-zero / not-significant bars


def setup():
    import matplotlib as mpl
    mpl.rcParams.update({
        "figure.dpi": 200, "savefig.dpi": 200, "figure.facecolor": "white",
        "savefig.facecolor": "white", "font.family": "DejaVu Sans", "font.size": 10,
        "axes.titlesize": 12, "axes.titleweight": "bold", "axes.labelsize": 10,
        "axes.edgecolor": MUTED, "axes.labelcolor": INK, "text.color": INK,
        "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False,
        "axes.spines.right": False, "axes.grid": True, "grid.color": GRID,
        "grid.linewidth": 0.6, "axes.axisbelow": True, "legend.frameon": False,
        "figure.constrained_layout.use": True,
    })


def boot_ci(fn, n, reps=2000, seed=0):
    """Bootstrap 95% CI of a statistic fn(idx) over n items (resample with replacement)."""
    rng = np.random.default_rng(seed)
    vals = [fn(rng.integers(0, n, n)) for _ in range(reps)]
    vals = [v for v in vals if v == v]
    return (np.percentile(vals, 2.5), np.percentile(vals, 97.5)) if vals else (np.nan, np.nan)
