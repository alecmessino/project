"""The house mark — a great blue heron, *Standing, Alert*, cut as an engraving.

This is not a logo. The wordmark is Driftwood's identity; the heron is a house mark, which is a
different instrument: it earns its meaning from scarcity and from being *the same object* every
time it appears. So there is exactly one master here, and every future application — hero
frontispiece, AWOR cover, a flagship essay, an embossed folder — reuses this file rather than a
variant of it. A second heron would destroy the only property that makes the first one worth
having.

THE TECHNIQUE, AND THE ONE THING NOT TO GET WRONG. This is an intaglio plate, and an intaglio
plate does not rotate its lay to follow the animal. **Family A runs at a constant +26° across the
entire figure** — neck, torso, wing plane, tail, bill, legs, all of it. Form is described *only*
by continuous variation in stroke weight along those parallel runs, never by stroke direction.
The temptation to bend the hatch around the neck is the single most common way this technique is
faked, and bending it is what makes the result read as illustration-with-texture rather than as
an engraving. Family B crosses at −68° (94° from A, deliberately not orthogonal, so the shadows
never resolve into a printed screen) and Family C at +82° deepens the darkest passages.

Every mark is a **filled ribbon**: a closed variable-width shape, `fill` only, `stroke="none"`.
Nothing here is an SVG stroked line, because `stroke-width` is constant along a path and the whole
technique depends on width swelling and dying along a single burin pass.

**There is no outline anywhere.** No closed contour follows the silhouette; the bird's edge exists
solely as hatch endpoints terminating against an invisible `<clipPath>`. Where the hatch is dense
the edge reads crisp; where the weight has fallen under the visibility floor the edge genuinely
disappears and the eye closes the form. One hairline contour would collapse the whole effect —
and it is also why the mark survives being embossed, where a contour would not.

Geometry, angles, spacings, thresholds and the shading model follow the technical specification
for the plate; the coordinate system is its native 1100 × 1500, art bounding box 147→873 by
216→1362. The right margin is deliberately 80px wider than the left: that is forward space in
front of the bill, and centring the bird weakens the pose.

PURE MODULE (see CLAUDE.md): no I/O, no filesystem, no clock, no global RNG. `_Seq` is the same
local LCG the plate library uses, so the master is byte-identical on every machine and every
Python build. The SVG is a committed asset; a generator that drifted would rewrite the house mark
in every future diff, and a house mark that changes is not a house mark.

Write it with ``python3 scripts/build_heron.py``.
"""
from __future__ import annotations

import math

# One ink, the same one the survey plates are cut in. 100% opaque everywhere: all apparent grey is
# stroke coverage at the pixel level, never transparency. Consumers that want it neutral apply
# `filter:grayscale(1)` at the point of use.
INK = "#1E2833"
PAPER = "#F4F1EA"

# Native mark canvas. Art bounding box x 147→873, y 216→1362 (726 × 1146).
W, H = 1100.0, 1500.0
ART = (147.0, 216.0, 873.0, 1362.0)


class _Seq:
    """A local linear-congruential sequence.

    Deliberately not `random`: the master is a committed static asset. Seeding the stdlib
    generator would leave the output hostage to a future change in CPython's algorithm, and a
    regenerated mark that differs by a hair would rewrite the file for no reason.
    """

    __slots__ = ("s",)

    def __init__(self, seed: int) -> None:
        self.s = (seed * 2654435761 + 1) & 0x7FFFFFFF

    def unit(self) -> float:
        self.s = (1103515245 * self.s + 12345) & 0x7FFFFFFF
        return self.s / 0x7FFFFFFF

    def span(self, lo: float, hi: float) -> float:
        return lo + (hi - lo) * self.unit()


# ---------------------------------------------------------------------------------------------
# geometry
# ---------------------------------------------------------------------------------------------

def _catmull(anchors, closed: bool = True, steps: int = 16):
    """A smooth curve through `anchors` (uniform Catmull-Rom)."""
    pts = list(anchors)
    n = len(pts)
    out = []
    for i in (range(n) if closed else range(n - 1)):
        p0 = pts[(i - 1) % n] if closed else pts[max(i - 1, 0)]
        p1, p2 = pts[i % n], pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if closed else pts[min(i + 2, n - 1)]
        for k in range(steps):
            t = k / steps
            t2, t3 = t * t, t * t * t
            out.append((
                0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t
                       + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                       + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3),
                0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t
                       + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                       + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3),
            ))
    return out


def _ribbon(centre, half_widths):
    """A closed polygon offset ±h along the path normal. Neck, legs, toes and contours are all
    built this way: a centreline plus a width law, never a stroked line."""
    left, right = [], []
    n = len(centre)
    for i, (x, y) in enumerate(centre):
        ax, ay = centre[max(i - 1, 0)]
        bx, by = centre[min(i + 1, n - 1)]
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        h = half_widths[i]
        left.append((x + nx * h, y + ny * h))
        right.append((x - nx * h, y - ny * h))
    return left + right[::-1]


def _lerp_widths(nodes_w, steps):
    """Widths resampled to match a Catmull-Rom resample of the same node list."""
    out = []
    for i in range(len(nodes_w) - 1):
        for k in range(steps):
            t = k / steps
            out.append(nodes_w[i] + (nodes_w[i + 1] - nodes_w[i]) * t)
    out.append(nodes_w[-1])
    return out


# ── 1.1 Neck ──────────────────────────────────────────────────────────────────────────────────
# Not a dramatic S. A shallow, near-rigid forward lean with one soft inflection — 74px of lateral
# travel against 350px of vertical. Held upright under tension, not coiled; the restraint is the
# character. The base overlaps the torso so the union gives a continuous shoulder with no seam.
_NECK_NODES = [(378, 266), (388, 326), (406, 414), (430, 516), (452, 616)]
_NECK_W = [56, 62, 72, 86, 108]

# ── 1.2 Head and beak ─────────────────────────────────────────────────────────────────────────
# Resolved into canvas coordinates (local frame rotated −8° about (378, 262)). The head mass is
# barely wider than the neck it sits on (0.89×) — the silhouette must read as one continuous
# tapering line from shoulder to bill tip, broken only by the crest plume. A head that reads as a
# distinct bulb turns the mark into a generic wading bird.
_HEAD = [
    (415.9, 272.8),   # lower rear / neck junction
    (351.4, 273.8),   # throat
    (260.6, 274.5),   # lower mandible base
    (141.5, 275.0),   # BILL TIP
    (248.8, 247.8),   # upper mandible
    (314.7, 228.5),   # forehead
    (365.4, 215.3),   # crown
    (411.2, 225.0),   # rear of skull
    (472.3, 228.6),   # crest plume tip
    (417.4, 240.3),   # crest plume base
]

# ── 1.3 Body ──────────────────────────────────────────────────────────────────────────────────
# The three-stage topline is a defining feature: flat across the front 40%, then 10.4° down, then
# steepening to ~31° into the tail. A single continuous curve from shoulder to tail reads as a
# goose. The flat front section is what gives the bird its level, poised carriage.
_TORSO = [
    (468, 558), (508, 578), (566, 600), (640, 610), (716, 624), (792, 652),
    (846, 694), (872, 728), (798, 738), (722, 770), (638, 808), (554, 820),
    (484, 804), (438, 758), (414, 690), (406, 618), (428, 578),
]

# ── 1.4 Legs, feet ────────────────────────────────────────────────────────────────────────────
# Shallow double bend, bowing ~8px outward at the joint; the two legs bow in opposite directions,
# which is what stops them reading as one unit.
_LEG_NEAR = [(586, 806), (578, 950), (572, 1094), (584, 1232), (592, 1318)]
_LEG_FAR = [(654, 802), (672, 946), (680, 1090), (668, 1226), (662, 1312)]
_LEG_W = [18, 15, 13, 12, 11]

# Three toes per foot from a shared origin, 9 → 3px. The lightest elements in the drawing: a
# suggestion of contact, not anatomy.
_TOES = [
    [(592, 1318), (544, 1330), (486, 1338)],
    [(592, 1318), (556, 1348), (508, 1364)],
    [(592, 1318), (636, 1332), (674, 1342)],
    [(662, 1312), (614, 1324), (556, 1332)],
    [(662, 1312), (626, 1342), (578, 1358)],
    [(662, 1312), (706, 1326), (744, 1336)],
]
_TOE_W = [9, 5.5, 3]

# ── Drawn contours ────────────────────────────────────────────────────────────────────────────
# The only deliberately drawn lines in the whole image. WING and SCAP run parallel ~22px apart at
# about 24° — within 2° of the primary lay — so the folded wing edge reads as a slightly heavier
# member of the same stroke family rather than as an applied outline. Unclipped, so they overrun
# the silhouette very slightly, the way a burin does.
_CONTOURS = [
    ([(566, 618), (648, 648), (730, 686), (800, 722), (854, 746)], [4.0, 3.4, 2.8, 2.2, 1.6]),
    ([(560, 640), (630, 676), (700, 714), (762, 748)], [2.6, 2.1, 1.6, 1.2]),
    ([(317.0, 230.2), (341.9, 220.6), (366.2, 221.2)], [2.4, 1.8, 1.3]),
]

# ── 2.6 Eye ───────────────────────────────────────────────────────────────────────────────────
# A single solid filled disc — the only fully saturated element in the drawing, sitting in the
# lightest zone. That contrast is what lets a 10px dot hold the whole composition.
_EYE = (341.3, 230.8, 5.0)

# ── 2.1 The three stroke families ─────────────────────────────────────────────────────────────
# angle°, spacing, w_max, threshold, gamma, wave amplitude, wavelength
_FAMILIES = (
    ("A", 26.0, 8.2, 5.2, 1.00, 1.27, 1.7, 205.0),
    ("B", -68.0, 10.0, 3.9, 0.68, 1.45, 1.2, 185.0),
    ("C", 82.0, 12.5, 3.1, 0.46, 1.60, 0.0, 1.0),
)

_SAMPLE = 2.2      # centreline sampling step
_FLOOR = 0.06      # visibility floor: below this the run simply stops
_TAPER = 6         # samples tapered to 15% at each end (≈13px)
_TIP = 0.15


# ---------------------------------------------------------------------------------------------
# the silhouette, as a raster field
# ---------------------------------------------------------------------------------------------

class _Mask:
    """The union of every region, scan-converted once, plus its distance-to-edge.

    Both are needed at every one of several hundred thousand stroke samples, and a point-in-
    polygon test against the union is far too expensive to run that often. The distance also
    feeds the shading model, which inflates the flat silhouette into a rounded height field.
    """

    __slots__ = ("x0", "y0", "step", "nx", "ny", "mask", "dist")

    def __init__(self, polys, step: float = 1.5, pad: float = 4.0):
        xs = [p[0] for poly in polys for p in poly]
        ys = [p[1] for poly in polys for p in poly]
        self.x0, self.y0, self.step = min(xs) - pad, min(ys) - pad, step
        self.nx = int((max(xs) + pad - self.x0) / step) + 2
        self.ny = int((max(ys) + pad - self.y0) / step) + 2
        self.mask = [bytearray(self.nx) for _ in range(self.ny)]
        for poly in polys:
            self._fill(poly)
        self.dist = self._chamfer()

    def _fill(self, poly):
        n = len(poly)
        ylo = min(p[1] for p in poly)
        yhi = max(p[1] for p in poly)
        j0 = max(0, int((ylo - self.y0) / self.step))
        j1 = min(self.ny - 1, int((yhi - self.y0) / self.step) + 1)
        for j in range(j0, j1 + 1):
            y = self.y0 + j * self.step
            hits = []
            k = n - 1
            for i in range(n):
                xi, yi = poly[i]
                xk, yk = poly[k]
                if (yi > y) != (yk > y):
                    hits.append(xi + (y - yi) * (xk - xi) / (yk - yi))
                k = i
            hits.sort()
            row = self.mask[j]
            for m in range(0, len(hits) - 1, 2):
                a = max(0, int(math.ceil((hits[m] - self.x0) / self.step)))
                b = min(self.nx - 1, int((hits[m + 1] - self.x0) / self.step))
                for i in range(a, b + 1):
                    row[i] = 1

    def _chamfer(self):
        s2 = math.sqrt(2.0)
        big = 1e9
        d = [[0.0 if not self.mask[j][i] else big for i in range(self.nx)]
             for j in range(self.ny)]
        for j in range(self.ny):
            row, prev = d[j], d[j - 1] if j else None
            for i in range(self.nx):
                if row[i] == 0.0:
                    continue
                v = row[i]
                if prev is not None:
                    v = min(v, prev[i] + 1.0)
                    if i:
                        v = min(v, prev[i - 1] + s2)
                    if i + 1 < self.nx:
                        v = min(v, prev[i + 1] + s2)
                if i:
                    v = min(v, row[i - 1] + 1.0)
                row[i] = v
        for j in range(self.ny - 1, -1, -1):
            row = d[j]
            nxt = d[j + 1] if j + 1 < self.ny else None
            for i in range(self.nx - 1, -1, -1):
                if row[i] == 0.0:
                    continue
                v = row[i]
                if nxt is not None:
                    v = min(v, nxt[i] + 1.0)
                    if i:
                        v = min(v, nxt[i - 1] + s2)
                    if i + 1 < self.nx:
                        v = min(v, nxt[i + 1] + s2)
                if i + 1 < self.nx:
                    v = min(v, row[i + 1] + 1.0)
                row[i] = v
        return [[v * self.step for v in row] for row in d]

    def _ij(self, x: float, y: float):
        return int((x - self.x0) / self.step + 0.5), int((y - self.y0) / self.step + 0.5)

    def inside(self, x: float, y: float) -> bool:
        i, j = self._ij(x, y)
        return 0 <= i < self.nx and 0 <= j < self.ny and bool(self.mask[j][i])

    def edge(self, x: float, y: float) -> float:
        i, j = self._ij(x, y)
        if 0 <= i < self.nx and 0 <= j < self.ny:
            return self.dist[j][i]
        return 0.0


# ---------------------------------------------------------------------------------------------
# 2.3 the shading model
# ---------------------------------------------------------------------------------------------

_ROLLOFF = 74.0
_AMBIENT = 0.27
_RELIEF = 2.7
_LIGHT = (-0.58, -0.72, 0.38)

# §2.3 — the plate's measured zone coverage, in per cent of ink over silhouette area. This table
# is the tonal architecture and it is the thing the acceptance checks measure, so it drives the
# weight law directly; the lighting model below modulates *within* a zone rather than setting its
# level. Stated plainly: darkest at the lower breast and under the folded wing; the neck a lighter
# passage than the torso, which is what makes it read as a separate cylinder; the head the
# lightest large form in the drawing at a quarter the density of the body, which draws the eye
# upward without using contrast or an outline.
_ZONES = (
    (250, 262, 10.0),   # bill, mid
    (330, 250, 10.0),   # head
    (392, 320, 36.9),   # neck, upper
    (430, 520, 41.8),   # neck, lower
    (500, 590, 39.0),   # shoulder
    (640, 620, 34.0),   # upper back — the lit passage, strokes fragment here
    (760, 660, 40.0),   # wing plane
    (836, 722, 33.7),   # rear / tail
    (560, 690, 40.0),   # lower body
    (610, 770, 57.0),   # the shadow under the folded wing — peak of the plate
    (470, 760, 48.0),   # lower breast
    (700, 760, 44.0),   # belly, rear
    (760, 730, 40.0),
)
# Coverage and weight are not the same quantity, so the table above is mapped onto the weight
# law's `shade` through one calibrated curve, fitted once against the rendered plate so the
# measured coverages land on §5.3–5.5. The compression matters: in the dark passages Families B
# and C switch on and stack, so coverage rises faster than weight does.
_P, _K = 0.67, 1.00

# The legs are given their weight directly rather than through that curve. A ribbon 11–18px wide
# crossed by an 8.2px lay is only ever cut by short runs, and a short run is mostly taper — so it
# takes a much deeper weight to reach the same 10.7% coverage the body reaches easily. This is the
# "beaded, ladder-like" texture the plate has, and it is why the legs read as thin, broken and
# slightly beaded rather than as solid tapered bars.
_LEG_DARK = 0.31
_TOE_DARK = 0.15


def _zone_tone(x: float, y: float, legs, toes) -> float:
    """Target ink darkness at a point, from the plate's zone table, blended smoothly.

    Inverse-cube weighting keeps each anchor local, so the neck does not bleed its lighter value
    into the breast and the legs do not pull tone out of the belly above them.
    """
    if toes(x, y):
        return _TOE_DARK
    if legs(x, y):
        return _LEG_DARK
    num = den = 0.0
    for ax, ay, cov in _ZONES:
        d2 = (x - ax) ** 2 + (y - ay) ** 2 + 700.0
        w = 1.0 / (d2 * math.sqrt(d2))
        num += cov * w
        den += w
    return (num / den / 100.0) ** _P * _K


def _shade_fn(mask: _Mask, legs, toes):
    """`shade ∈ [0,1]`, 1 = fully lit, 0 = deep shadow.

    Two terms. The zone table sets the *level* — how dark this passage of the plate is. The
    lighting model sets the *modelling within* it: the flat silhouette is inflated into a rounded
    height field by its own distance-to-edge, lit from upper-left and slightly forward, so every
    top-left facing surface lightens and every under surface deepens. One light for the whole
    bird — which is exactly why a single constant +26° lay can describe every part of it.
    """
    lx, ly, lz = _LIGHT
    L = math.sqrt(lx * lx + ly * ly + lz * lz)
    lx, ly, lz = lx / L, ly / L, lz / L

    def height(x, y):
        t = min(1.0, mask.edge(x, y) / _ROLLOFF)
        return math.sqrt(max(0.0, 1.0 - (1.0 - t) ** 2))

    def shade(x: float, y: float) -> float:
        h = 2.0
        zx = (height(x + h, y) - height(x - h, y)) / (2.0 * h)
        zy = (height(x, y + h) - height(x, y - h)) / (2.0 * h)
        nx, ny, nz = -_RELIEF * zx, -_RELIEF * zy, 1.0
        n = math.sqrt(nx * nx + ny * ny + 1.0)
        lam = max(0.0, (nx * lx + ny * ly + nz * lz) / n)
        lit = _AMBIENT + (1.0 - _AMBIENT) * lam        # 0.27 dark .. 1.0 full light
        model = 1.62 - 0.92 * lit                      # 0.70 on a lit face .. 1.37 underneath
        dark = _zone_tone(x, y, legs, toes) * model
        return max(0.0, min(1.0, 1.0 - dark))

    return shade


# ---------------------------------------------------------------------------------------------
# 2.2 / 4.4 stroke generation
# ---------------------------------------------------------------------------------------------

def _hatch(mask: _Mask, shade, angle: float, spacing: float, w_max: float,
           thresh: float, gamma: float, amp: float, wave: float, seq: _Seq,
           weight_scale=None):
    """One family of parallel runs across the whole figure.

    The angle never varies. A run traverses the full chord of whatever it crosses and breaks only
    where it leaves the silhouette or where its computed weight falls under the visibility floor —
    which is what makes strokes dissolve into dashes and then vanish on the lit upper-left
    surfaces while the same line continues at full weight once it re-enters shadow. Collinear
    fragments are deliberate: they are what let the eye reconstruct one continuous burin pass.
    """
    th = math.radians(angle)
    ux, uy = math.cos(th), math.sin(th)
    nx, ny = -math.sin(th), math.cos(th)
    ax, ay, bx, by = ART
    cx, cy = (ax + bx) / 2.0, (ay + by) / 2.0
    reach = math.hypot(bx - ax, by - ay) / 2.0 + spacing
    lines = int(reach / spacing) + 2
    steps = int(2.0 * reach / _SAMPLE) + 2
    out = []
    for i in range(-lines, lines + 1):
        off = i * spacing
        phase = seq.span(0.0, math.tau)
        sx, sy = cx + nx * off - ux * reach, cy + ny * off - uy * reach
        run_p, run_w = [], []
        for k in range(steps):
            d = k * _SAMPLE
            px, py = sx + ux * d, sy + uy * d
            if amp:
                s = amp * math.sin(d / wave * math.tau + phase)
                px, py = px + nx * s, py + ny * s
            w = 0.0
            if mask.inside(px, py):
                q = (thresh - shade(px, py)) / thresh
                if q > 0.0:
                    w = w_max * (q if q < 1.0 else 1.0) ** gamma
                    if weight_scale is not None:
                        w *= weight_scale(px, py)
            if w >= _FLOOR:
                run_p.append((px, py))
                run_w.append(w)
            else:
                if len(run_p) >= 2:
                    out.append((run_p, run_w))
                run_p, run_w = [], []
        # Two samples is the shortest mark the plate keeps. Three would drop the fragments at the
        # bill tip and along the top of the back, where the form is carried by stroke endpoints
        # alone — exactly the passages the technique depends on.
        if len(run_p) >= 2:
            out.append((run_p, run_w))
    return [(p, _taper(w)) for p, w in out]


def _taper(ws):
    """No blunt terminations anywhere in the drawing: every run dies to 15% of its local width
    over its final ~13px at both ends."""
    n = len(ws)
    # Short runs — the two or three samples that cross a leg, or a fragment left on a lit surface —
    # must not be tapered out of existence, or the legs vanish and the fragments stop reading as
    # collinear pieces of one pass. Cap the taper at a third of the run.
    m = max(1, min(_TAPER, n // 3))
    out = list(ws)
    for k in range(m):
        f = _TIP + (1.0 - _TIP) * (k / m)
        out[k] *= f
        out[n - 1 - k] *= f
    return out


def _stipple(mask: _Mask, shade, seq: _Seq, count: int):
    """Carries the mid-tones and the transitions. Without it the cross-hatch reads as a hard-edged
    screen wherever Family B switches on at its threshold.

    The spec's 0.5–1.7px figure is taken as dot *size*, not radius: a 1.7px-radius dot is 3.4px
    across, wider than the median stroke, and at the spec'd count of 11,000 it buries the hatch —
    stipple alone measured 57% coverage in the lower body against a 49% target for the whole
    plate. Read as diameter, the count holds and the coverages land.
    """
    x0, y0 = mask.x0, mask.y0
    x1, y1 = x0 + mask.nx * mask.step, y0 + mask.ny * mask.step
    pts = []
    tries = 0
    while len(pts) < count and tries < count * 30:
        tries += 1
        x, y = seq.span(x0, x1), seq.span(y0, y1)
        if not mask.inside(x, y):
            continue
        s = shade(x, y)
        if s >= 0.85:
            continue
        t = min(1.0, (0.85 - s) / (0.85 - 0.32))
        if seq.unit() > t:
            continue
        pts.append((x, y, 0.14 + 0.34 * t))
    return pts


# ---------------------------------------------------------------------------------------------
# the plate
# ---------------------------------------------------------------------------------------------

def _regions():
    """Every closed region of the silhouette. Used for the clip path and for the mask — and never
    painted, in either role."""
    neck = _ribbon(_catmull(_NECK_NODES, closed=False, steps=16),
                   [w / 2 for w in _lerp_widths(_NECK_W, 16)])
    torso = _catmull(_TORSO, closed=True, steps=16)
    legs = [_ribbon(_catmull(nodes, closed=False, steps=14),
                    [w / 2 for w in _lerp_widths(_LEG_W, 14)])
            for nodes in (_LEG_NEAR, _LEG_FAR)]
    toes = [_ribbon(_catmull(t, closed=False, steps=10),
                    [w / 2 for w in _lerp_widths(_TOE_W, 10)]) for t in _TOES]
    return {"neck": neck, "torso": torso, "head": list(_HEAD), "legs": legs, "toes": toes}


def build():
    """Cut the master."""
    seq = _Seq(20260803)
    reg = _regions()
    polys = [reg["neck"], reg["torso"], reg["head"]] + reg["legs"] + reg["toes"]
    mask = _Mask(polys, step=1.5)
    leg_mask = _Mask(reg["legs"], step=1.2, pad=2.0)
    toe_mask = _Mask(reg["toes"], step=1.0, pad=2.0)
    shade = _shade_fn(mask, leg_mask.inside, toe_mask.inside)

    # §6.3 — the clearest available improvement on the source: lighten the far leg so it sits
    # back in space instead of competing with the near one for the same plane.
    far = _Mask([reg["legs"][1]], step=1.2, pad=2.0)
    near = _Mask([reg["legs"][0]], step=1.2, pad=2.0)


    def depth(x, y):
        return 0.83 if (far.inside(x, y) and not near.inside(x, y)) else 1.0

    families = {}
    for name, angle, spacing, w_max, thresh, gamma, amp, wave in _FAMILIES:
        families[name] = _hatch(mask, shade, angle, spacing, w_max, thresh, gamma,
                                amp, wave, seq, weight_scale=depth)

    return {
        "regions": polys,
        "A": families["A"], "B": families["B"], "C": families["C"],
        "stipple": _stipple(mask, shade, seq, 11000),
        # _ribbon takes half-widths; the spec's contour figures are full widths.
        "contours": [_ribbon(_catmull(c, closed=False, steps=14),
                             [w / 2.0 for w in _lerp_widths(ws, 14)])
                     for c, ws in _CONTOURS],
        "eye": _EYE,
    }


# ---------------------------------------------------------------------------------------------
# 4.3 emission — every mark is a closed filled ribbon
# ---------------------------------------------------------------------------------------------

def _ribbon_d(pts, half) -> str:
    """M P₀+h₀N … Pₙ+hₙN, back along Pₙ−hₙN … P₀−h₀N, Z. Coordinates quantised to 1dp: well
    below perceptual threshold at 726px of art width, and roughly half the file size."""
    n = len(pts)
    fwd, back = [], []
    for i in range(n):
        x, y = pts[i]
        ax, ay = pts[max(i - 1, 0)]
        bx, by = pts[min(i + 1, n - 1)]
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy) or 1.0
        ox, oy = -dy / L * half[i] * 0.5, dx / L * half[i] * 0.5   # half[] is full width
        fwd.append((x + ox, y + oy))
        back.append((x - ox, y - oy))
    pieces = [f"M{fwd[0][0]:.1f} {fwd[0][1]:.1f}"]
    px, py = fwd[0]
    for x, y in fwd[1:] + back[::-1]:
        pieces.append(f"l{x - px:.1f} {y - py:.1f}")
        px, py = x, y
    pieces.append("Z")
    return "".join(pieces)


def _poly_d(poly) -> str:
    px, py = poly[0]
    out = [f"M{px:.1f} {py:.1f}"]
    for x, y in poly[1:]:
        out.append(f"l{x - px:.1f} {y - py:.1f}")
        px, py = x, y
    out.append("Z")
    return "".join(out)


def _family_d(runs) -> str:
    return "".join(_ribbon_d(p, w) for p, w in runs)


def render_svg(plate=None, paper: bool = False) -> str:
    """The master file. One ink, filled ribbons only, no outlines, no stamp.

    `paper` is off by default: the master composites onto whatever surface uses it (the hero's
    limestone, an embossed cover), and a painted background rectangle would punch a light box out
    of that surface. Pass `paper=True` for a standalone two-colour plate.
    """
    plate = plate or build()
    clip = "".join(f'<path d="{_poly_d(p)}"/>' for p in plate["regions"])
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}"/>'
                   for x, y, r in plate["stipple"])
    bg = f'<rect width="{W:.0f}" height="{H:.0f}" fill="{PAPER}"/>' if paper else ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" '
        f'preserveAspectRatio="xMidYMid meet" shape-rendering="geometricPrecision" role="img" '
        f'aria-label="Engraving of a great blue heron standing alert, facing left">'
        f'{bg}'
        f'<defs><clipPath id="dw-heron-sil" clipPathUnits="userSpaceOnUse">{clip}</clipPath></defs>'
        f'<g id="mark" fill="{INK}" stroke="none" fill-rule="nonzero">'
        f'<g id="tone" clip-path="url(#dw-heron-sil)">'
        f'<path id="hatch-primary" d="{_family_d(plate["A"])}"/>'
        f'<path id="hatch-cross" d="{_family_d(plate["B"])}"/>'
        f'<path id="hatch-deep" d="{_family_d(plate["C"])}"/>'
        f'<g id="stipple">{dots}</g>'
        f'</g>'
        f'<g id="contours">'
        + "".join(f'<path d="{_poly_d(c)}"/>' for c in plate["contours"]) +
        f'</g>'
        f'<circle id="eye" cx="{plate["eye"][0]:.1f}" cy="{plate["eye"][1]:.1f}" '
        f'r="{plate["eye"][2]:.1f}"/>'
        f'</g></svg>'
    )
