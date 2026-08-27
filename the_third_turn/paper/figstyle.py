"""Shared publication figure style — one coherent visual system for the paper.

Okabe-Ito categorical palette (CVD-safe, validator-passed), reserved status colors,
recessive axes, consistent typography. Import and call `setup()` before plotting;
use PALETTE for categorical series and PASS/FAIL only for status marks.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

# Okabe-Ito — colorblind-safe scientific standard (validated for CVD separation)
PALETTE = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#56B4E9", "#CC79A7"]
INK, MUTED, GRID = "#222222", "#666666", "#DDDDDD"
PASS, FAIL, NA = "#1B7837", "#B2182B", "#999999"   # reserved status (with symbols, never color-alone)
NEUTRAL = "#C4CACF"   # near-zero / not-significant bars. Light enough to separate from every
                      # PALETTE hue in grayscale (min luminance gap 16.9%, vs 0.5% for #8C8C8C);
                      # pair with HATCH so it also reads without colour at all.
HATCH = "///"         # texture for neutral bars: CVD, grayscale print, forced-colors


# ---------------------------------------------------------------------------
# PRODUCTION CONTRACT (2026-08-27 visual-production pass)
#
# Figures are raster PNGs placed into a fixed text measure. Whatever size a
# figure is authored at, the page scales it to the measure -- so authoring wide
# and displaying narrow silently shrinks every label. Before this pass every one
# of the sixteen figure functions failed the legibility floor for exactly that
# reason: canvases 7.2-15in wide displayed at 5.96in, scaling internal text by
# 0.40-0.83x. A 10pt label landed on paper between 3.3 and 8.3pt.
#
# The contract that prevents it recurring:
#   * author at FULL_W (or HALF_W), which equals the display measure, so the
#     scale factor is 1.0 and a matplotlib point IS a point on paper;
#   * never set a font size below FS_MIN;
#   * check with paper/check_figure_legibility.py, which recomputes the scale
#     from the committed PNG and the CSS measure rather than trusting intent.
# ---------------------------------------------------------------------------

# Text measure is 487.28pt (Letter, 22mm side margins). Figures display at 100%
# of it, so the canonical canvas is that measure expressed in inches.
MEASURE_PT = 487.28
FULL_W = MEASURE_PT / 72.0          # 6.77in -- scale 1.0
HALF_W = FULL_W / 2                 # side-by-side pairs

# Type scale. Every value is also the on-page value, because scale is 1.0.
FS_MIN    = 8.5     # hard floor: nothing smaller ships
FS_TICK   = 8.5     # axis ticks
FS_LABEL  = 9.0     # axis labels, in-figure annotation
FS_PANEL  = 9.5     # panel headings
FS_TITLE  = 10.5    # figure/axes titles

# Geometry. One set of weights and shapes across both papers, the supplement and
# the companion, so the artifacts read as one system.
LW_DATA   = 1.8     # data lines
LW_RULE   = 1.0     # axis rules, box edges
LW_ARROW  = 1.2     # connectors
ARROW     = dict(arrowstyle="-|>", mutation_scale=11, linewidth=LW_ARROW,
                 color=MUTED, shrinkA=3, shrinkB=3)
BOX_R     = 0.06    # rounded-box corner radius, in axes units
BOX_PAD   = 0.34    # rounded-box padding
# Output contract. Every figure ships three coeval renditions from one canvas:
#   .svg  vector master, embedded in the manuscript build (Chromium keeps it vector);
#   .pdf  vector master, the form journal production asks for;
#   .png  raster preview for markdown/web, at PNG_DPI.
# PNG_DPI is 360 rather than 300 because the tight crop adds `pad` inches on each
# side, so the effective on-page resolution is dpi * (saved width / measure) and
# lands a few percent under the nominal value. 360 clears the 300 PPI floor with
# room to spare; see paper/check_figure_output.py, which measures rather than
# assumes.
PNG_DPI = 360
RASTER_PPI_FLOOR = 300
VECTOR_FMTS = ("svg", "pdf")


def box(fc="white", ec=None, lw=LW_RULE):
    """Standard annotation box: one radius, one weight, everywhere."""
    return dict(boxstyle=f"round,pad={BOX_PAD},rounding_size={BOX_R}",
                facecolor=fc, edgecolor=ec or MUTED, linewidth=lw)


def setup():
    import matplotlib as mpl
    mpl.rcParams.update({
        "figure.dpi": 200, "savefig.dpi": 200, "figure.facecolor": "white",
        "savefig.facecolor": "white", "font.family": "DejaVu Sans", "font.size": FS_LABEL,
        "axes.titlesize": FS_TITLE, "axes.titleweight": "bold", "axes.labelsize": FS_LABEL,
        "xtick.labelsize": FS_TICK, "ytick.labelsize": FS_TICK, "legend.fontsize": FS_LABEL,
        "lines.linewidth": LW_DATA, "axes.linewidth": LW_RULE,
        "axes.edgecolor": MUTED, "axes.labelcolor": INK, "text.color": INK,
        "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False,
        "axes.spines.right": False, "axes.grid": True, "grid.color": GRID,
        "grid.linewidth": 0.6, "axes.axisbelow": True, "legend.frameon": False,
        "figure.constrained_layout.use": True,
        # Keep figure labels as real text in the SVG master rather than outlines, so
        # the vector rendition carries embedded fonts and extractable strings. Verified
        # against the raster master glyph-for-glyph by paper/check_figure_output.py.
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        # Fixed salt so the SVG's internal clip-path ids are a function of the figure
        # rather than of the process. Without it two runs of the same generator produce
        # byte-different masters, and "regenerates byte-identically" stops being a
        # claim anyone can check.
        "svg.hashsalt": "the-third-turn",
    })


def boot_ci(fn, n, reps=2000, seed=0):
    """Bootstrap 95% CI of a statistic fn(idx) over n items (resample with replacement)."""
    rng = np.random.default_rng(seed)
    vals = [fn(rng.integers(0, n, n)) for _ in range(reps)]
    vals = [v for v in vals if v == v]
    return (np.percentile(vals, 2.5), np.percentile(vals, 97.5)) if vals else (np.nan, np.nan)

def save_at_measure(fig, path, pad=0.02, tol=0.012, iters=40, vector=True):
    """Save a figure whose CROPPED width is exactly the text measure.

    WHY THIS EXISTS. The page clamps every figure to the measure, so on-page text
    size is the authored point size times (measure / saved width). Saved width is
    the only thing that controls legibility, and across the committed set it
    ranged from 5.3in to 10.9in against a 6.77in measure -- internal text was
    landing between 5.3pt and 10.9pt with no relationship to what any generator
    declared.

    Two approaches that look right and are not:
      * re-saving at a different dpi. dpi scales pixels and inches together, so
        the width in inches, and hence the on-page scale, does not move.
      * saving uncropped (`bbox_inches=None`). The width becomes exact, but any
        artist outside the canvas -- a suptitle at y>1, an annotation past the
        right spine -- is clipped away, which traded legibility for lost content.

    So: keep the tight crop, which both prevents clipping and removes dead space,
    and iterate the canvas width until the CROPPED extent lands on FULL_W. Text is
    fixed in points while the canvas moves, so the crop shrinks more slowly than
    the canvas and the iteration contracts onto the target.
    """
    # The loop runs against the figure's own renderer. Converging it at the SVG
    # backend's 72 dpi instead was tried and is worse: several figures stop
    # converging there entirely, landing 5% under the measure. At the authoring dpi
    # every figure converges, and the raster and vector renditions then agree on
    # width to within about a percent -- glyph advances round differently at 360 dpi
    # than at 72, and that residual is the whole of the disagreement.
    fig.canvas.draw()
    for _ in range(iters):
        bb = fig.get_tightbbox(fig.canvas.get_renderer())
        w = bb.width + 2 * pad
        if abs(w - FULL_W) <= tol:
            break
        cur_w, cur_h = fig.get_size_inches()
        # Damped correction: the crop responds sub-linearly to the canvas.
        fig.set_size_inches(cur_w * (1 + 0.75 * (FULL_W / w - 1)), cur_h)
        fig.canvas.draw()

    # One converged canvas, three renditions, identical geometry. The vector
    # masters are the production artifacts; the PNG is the markdown preview and
    # the raster fallback, and it clears the 300 PPI floor on its own so the
    # package stays publishable wherever a vector path is unavailable.
    path = Path(path)
    fig.savefig(path, bbox_inches="tight", pad_inches=pad, dpi=PNG_DPI)
    if vector:
        # Suppress the wall-clock stamp each vector backend writes by default
        # (<dc:date> in SVG, /CreationDate in PDF). Nothing downstream reads it, and
        # with it the masters are byte-reproducible.
        for ext, nodate in zip(VECTOR_FMTS, ({"Date": None}, {"CreationDate": None})):
            fig.savefig(path.with_suffix(f".{ext}"), bbox_inches="tight", pad_inches=pad,
                        metadata=nodate)
