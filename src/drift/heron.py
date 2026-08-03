"""The house mark — a great blue heron, *Standing, Alert*, cut as an engraving.

This is not a logo. The wordmark is Driftwood's identity; the heron is a house mark, which is a
different instrument: it earns its meaning from scarcity and from being *the same object* every
time it appears. So there is exactly one master here, and every future application — hero
frontispiece, AWOR cover, a flagship essay, an embossed folder — reuses this file rather than a
variant of it. A second heron would destroy the only property that makes the first one worth
having.

WHY GENERATED, AND WHY THE ENGRAVING VOCABULARY. The pose reads before the bird does: neck
extended, head composed, weight settled, nothing in motion. Observation before action — the same
claim the rest of the site makes in words. It is drawn the way the survey plates are drawn,
because the site already has a hand: single ink (#1E2833), hatch and stipple, **no outlines**.
The silhouette is not stroked anywhere; the bird's edge is simply where the tone stops. That is
what makes it read as atmosphere first and as a heron second, which is the whole objective — and
it is also why it survives being embossed, where an outline would not.

THE HATCH FOLLOWS THE FORM, AND THAT IS THE WHOLE TECHNIQUE. The first cut of this mark laid down
straight scan-lines in two fixed directions and broke them into short dashes. It was a *field* of
marks: isotropic, one stroke weight, the same character everywhere, and the silhouette read as the
hard edge of that field. An engraver does the opposite — long continuous burin passes that travel
with the anatomy, thinning and breaking where the light is, with true cross-hatching reserved for
the shadow. So the primary families here are **streamlines through a flow field** (:func:`_flow`)
built from the bird's own armatures: the bill's axis, the neck's S, the body's sweep to the tail,
the wing's feather direction. Lines are integrated through that field, spaced evenly by the
Jobard–Lefebvre rule, then inked as *runs* — long where the tone is deep, breaking up into nicks
and finally into nothing where it is light. Cross-hatch families cross the flow only where the
shadow can carry them, and stroke weight is bucketed by tone rather than fixed. Tone falls off
into the perimeter so the edge dissolves instead of being cut out.

PURE MODULE (see CLAUDE.md): no I/O, no filesystem, no clock, no global RNG. `_Seq` is the same
local LCG the plate library uses, so the master is byte-identical on every machine and every
Python build. The SVG is a committed asset; a generator that drifted would rewrite the house mark
in every future diff, and a house mark that changes is not a house mark.

Write it with ``python3 scripts/build_heron.py``.
"""
from __future__ import annotations

import math

# One ink, the same one the survey plates are cut in. Consumers that want it neutral apply
# `filter:grayscale(1)` at the point of use; the master stays a single ink.
INK = "#1E2833"

# Portrait plate, sized so the bird fills it with a hair of air. Placement, crop and padding are
# decisions for the page that uses the mark, not properties of the mark.
W, H = 900.0, 1400.0


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
# geometry helpers
# ---------------------------------------------------------------------------------------------

def _catmull(anchors, closed: bool = True, steps: int = 14):
    """A smooth curve through `anchors` (uniform Catmull-Rom).

    Anchors are the anatomy; the spline is what keeps the outline off a drafting compass. Repeat
    an anchor to hold a cusp there — the bill's tip and the primaries are points, not curves.
    """
    pts = list(anchors)
    n = len(pts)
    out = []
    rng = range(n) if closed else range(n - 1)
    for i in rng:
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


def _dist_to(poly, x: float, y: float) -> float:
    """Shortest distance from (x, y) to an open polyline. Used to shade off anatomy lines."""
    best = 1e9
    for i in range(len(poly) - 1):
        ax, ay = poly[i]
        bx, by = poly[i + 1]
        dx, dy = bx - ax, by - ay
        L = dx * dx + dy * dy
        t = 0.0 if L == 0 else max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / L))
        px, py = ax + t * dx - x, ay + t * dy - y
        d = px * px + py * py
        if d < best:
            best = d
    return math.sqrt(best)


def _tangent(poly, x: float, y: float):
    """The unit tangent of the segment of `poly` nearest (x, y), and the distance to it.

    All the armatures are drawn head-to-tail in the same sense, so their tangents can be blended
    without cancelling each other — this is what lets the flow field turn smoothly out of the neck
    and into the body instead of tearing at the shoulder.
    """
    best, bt = 1e18, (1.0, 0.0)
    for i in range(len(poly) - 1):
        ax, ay = poly[i]
        bx, by = poly[i + 1]
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / L2))
        px, py = ax + t * dx - x, ay + t * dy - y
        d = px * px + py * py
        if d < best:
            L = math.sqrt(L2) or 1.0
            best, bt = d, (dx / L, dy / L)
    return bt, math.sqrt(best)


def _band(d: float, width: float) -> float:
    """A soft falloff, 1 on the line and 0 well off it. Every tonal cue in the mark is one of
    these; nothing in an engraving has a hard edge except the edge of the plate."""
    t = d / width
    return math.exp(-t * t)


def _ramp(a: float, b: float, v: float) -> float:
    """Smoothstep from a to b."""
    t = max(0.0, min(1.0, (v - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


def _thick(centre, half_widths):
    """A closed polygon around a centreline with a per-node half-width. The legs."""
    left, right = [], []
    n = len(centre)
    for i, (x, y) in enumerate(centre):
        ax, ay = centre[max(i - 1, 0)]
        bx, by = centre[min(i + 1, n - 1)]
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        w = half_widths[i]
        left.append((x + nx * w, y + ny * w))
        right.append((x - nx * w, y - ny * w))
    return left + right[::-1]


def _widths(nodes, widths, steps):
    """Half-widths for a Catmull-Rom resample of `nodes` — linear between the node values."""
    out = []
    for i in range(len(nodes) - 1):
        for k in range(steps):
            t = k / steps
            out.append(widths[i] + (widths[i + 1] - widths[i]) * t)
    out.append(widths[-1])
    return out


class _Field:
    """A region, rasterised once: inside-ness and distance to the edge.

    Both are needed thousands of times — for every integration step of every streamline, and for
    every tone sample — and a point-in-polygon test against a six-hundred-point outline is far too
    expensive to run that often. Scan-convert the outline once, then chamfer the mask to get the
    edge distance, and both questions become a table lookup. The edge distance is what lets the
    tone fall away into the perimeter instead of stopping dead at it.
    """

    __slots__ = ("x0", "y0", "step", "nx", "ny", "mask", "dist")

    def __init__(self, poly, step: float = 2.5, pad: float = 6.0):
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        self.x0, self.y0, self.step = min(xs) - pad, min(ys) - pad, step
        self.nx = int((max(xs) + pad - self.x0) / step) + 2
        self.ny = int((max(ys) + pad - self.y0) / step) + 2
        self.mask = [bytearray(self.nx) for _ in range(self.ny)]
        n = len(poly)
        for j in range(self.ny):
            y = self.y0 + j * step
            xs_hit = []
            k = n - 1
            for i in range(n):
                xi, yi = poly[i]
                xk, yk = poly[k]
                if (yi > y) != (yk > y):
                    xs_hit.append(xi + (y - yi) * (xk - xi) / (yk - yi))
                k = i
            xs_hit.sort()
            row = self.mask[j]
            for m in range(0, len(xs_hit) - 1, 2):
                a = max(0, int(math.ceil((xs_hit[m] - self.x0) / step)))
                b = min(self.nx - 1, int((xs_hit[m + 1] - self.x0) / step))
                for i in range(a, b + 1):
                    row[i] = 1
        # Chamfer distance transform, two passes. Cheap, and well inside a pixel of exact here.
        big = 1e9
        d = [[0.0 if not self.mask[j][i] else big for i in range(self.nx)] for j in range(self.ny)]
        s2 = math.sqrt(2.0)
        for j in range(self.ny):
            for i in range(self.nx):
                if d[j][i] == 0.0:
                    continue
                v = d[j][i]
                if j:
                    v = min(v, d[j - 1][i] + 1.0)
                    if i:
                        v = min(v, d[j - 1][i - 1] + s2)
                    if i + 1 < self.nx:
                        v = min(v, d[j - 1][i + 1] + s2)
                if i:
                    v = min(v, d[j][i - 1] + 1.0)
                d[j][i] = v
        for j in range(self.ny - 1, -1, -1):
            for i in range(self.nx - 1, -1, -1):
                if d[j][i] == 0.0:
                    continue
                v = d[j][i]
                if j + 1 < self.ny:
                    v = min(v, d[j + 1][i] + 1.0)
                    if i:
                        v = min(v, d[j + 1][i - 1] + s2)
                    if i + 1 < self.nx:
                        v = min(v, d[j + 1][i + 1] + s2)
                if i + 1 < self.nx:
                    v = min(v, d[j][i + 1] + 1.0)
                d[j][i] = v
        self.dist = [[v * step for v in row] for row in d]

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

    def seed(self):
        """Any point well inside — the first streamline has to start somewhere."""
        best, bp = -1.0, (self.x0, self.y0)
        for j in range(0, self.ny, 3):
            for i in range(0, self.nx, 3):
                if self.dist[j][i] > best:
                    best, bp = self.dist[j][i], (self.x0 + i * self.step, self.y0 + j * self.step)
        return bp


# ---------------------------------------------------------------------------------------------
# the anatomy — Standing, Alert; facing left, into the page
# ---------------------------------------------------------------------------------------------
# Proportions are a great blue heron's, held to the approved pose: weight settled on both legs,
# neck extended but unstruck, head level and watchful. Nothing here is stylised into a mascot —
# the bird has to survive being looked at by someone who knows the bird. The mass sits low: a
# deep body over structural legs, not a light body on stilts.

_SIL = _catmull([
    (50, 112), (50, 112),                                   # dagger tip (cusp)
    (96, 100), (190, 80), (252, 62),                        # culmen, up to the forehead
    (268, 52), (298, 46), (334, 52), (368, 66), (392, 86),   # crown and nape
    (384, 112), (368, 134), (352, 156),                     # nape into the back of the neck
    (354, 196), (362, 236), (374, 272), (388, 296),
    (410, 340), (436, 384), (468, 420), (496, 438),         # neck, into the shoulder
    (548, 452), (614, 474), (678, 504), (740, 546),         # the back
    (796, 592), (842, 630), (872, 660), (872, 660),         # primaries, past the tail (cusp)
    (838, 692), (778, 720), (708, 738), (626, 748),         # under the tail
    (544, 750), (466, 738), (404, 716), (366, 682),         # the belly
    (346, 638), (344, 600), (352, 562), (358, 528),         # the breast
    (350, 486), (336, 428), (316, 370), (300, 314),         # the front of the neck
    (288, 262), (284, 210), (290, 160),
    (298, 144), (286, 130), (270, 118), (252, 108),         # jaw, to the gape
    (190, 108), (96, 110),                                  # lower mandible, back to the tip
], steps=10)

# The bill is cut denser and tighter than the plumage — it is not feathers, and it should not be
# drawn like feathers. Its own region, its own pitch, its own tone.
_BEAK = _catmull([
    (50, 112), (50, 112), (96, 100), (190, 80), (252, 62),
    (252, 108), (252, 108), (190, 108), (96, 110),
], steps=10)

# The folded wing: everything below the covert line. It carries its own flow, running back toward
# the primaries, which is what gives the flank its direction.
_WING = _catmull([
    (406, 540), (520, 568), (640, 596), (760, 624), (824, 644),
    (872, 660), (872, 660), (838, 692), (778, 720), (708, 738),
    (626, 748), (544, 750), (466, 738), (404, 716), (370, 688),
    (374, 628), (384, 578),
], steps=10)

# Tonal armatures. The bird's form is carried entirely by where these run.
_BACK_LINE = [(500, 462), (552, 478), (616, 500), (680, 530), (742, 570), (800, 610), (846, 648)]
_COVERT_LINE = [(406, 540), (520, 568), (640, 596), (760, 624), (824, 644)]
_BREAST_LINE = [(356, 540), (362, 590), (378, 648), (406, 690), (456, 724)]
_NECK_FRONT = [(290, 160), (284, 210), (288, 262), (300, 314), (316, 370),
               (336, 428), (350, 486), (358, 528), (352, 566), (346, 610)]
_CROWN_LINE = [(258, 58), (296, 48), (338, 54), (376, 74)]
_CULMEN = [(50, 112), (96, 100), (190, 80), (252, 62)]
_EYE = (272, 76)

# Flow armatures — the burin's direction, not the tone's. Every one runs bill-to-tail so their
# tangents blend instead of fighting.
_BEAK_AXIS = [(58, 108), (140, 94), (210, 82), (272, 70)]
_NECK_AXIS = [(300, 150), (302, 212), (312, 272), (332, 332), (358, 392), (392, 442),
              (432, 480), (472, 504)]
_BODY_AXIS = [(368, 622), (452, 608), (562, 600), (664, 608), (764, 628), (860, 654)]
_WING_FLOW = [(418, 572), (532, 598), (652, 626), (752, 652), (854, 670)]

_LEG_A = [(520, 742), (514, 900), (506, 1090), (499, 1250), (497, 1332)]
_LEG_B = [(612, 742), (602, 900), (590, 1090), (580, 1250), (576, 1332)]
_LEG_A_W = [12.0, 9.0, 7.5, 6.4, 5.8]
_LEG_B_W = [11.4, 8.6, 7.1, 6.1, 5.5]

# Toes and plumes are drawn as broken runs, not shapes: at this weight a toe is a line of marks.
_TOES = [
    [(497, 1332), (461, 1344), (431, 1352), (409, 1357)],
    [(497, 1332), (466, 1352), (443, 1363)],
    [(497, 1332), (519, 1340), (547, 1345)],
    [(576, 1332), (540, 1345), (514, 1353)],
    [(576, 1332), (552, 1354), (532, 1364)],
    [(576, 1332), (622, 1340), (676, 1344), (712, 1345)],
]
_CREST = [
    [(352, 62), (382, 72), (404, 80)],
    [(356, 76), (378, 84), (392, 90)],
]
# The primaries. Long single strands over the wing, taken past the tone the way an engraver ends a
# plate: a few decisive passes that state the feather direction the hatch only implies.
_STRANDS = [
    [(470, 570), (580, 598), (690, 626), (790, 652), (866, 664)],
    [(486, 610), (596, 634), (706, 656), (800, 674), (862, 676)],
    [(506, 652), (616, 672), (716, 686), (802, 694)],
    [(560, 692), (660, 706), (748, 714), (818, 714)],
]


def _tone_fn(field: _Field):
    """Ink density at a point, 0 (paper) to 1 (solid). The whole bird is in this function.

    Light falls from above and slightly behind, the way it does on a bird standing in open water
    under a flat sky: the back and the covert line catch it, the breast and the underbelly sit in
    it, the front of the neck holds a dark margin that is what actually reads as "neck" at a
    glance. The last term is the one that matters most at hero opacity — tone thins into the
    perimeter, so the silhouette dissolves at its edge instead of reading as a cut-out.
    """
    ex, ey = _EYE

    def tone(x: float, y: float) -> float:
        v = 0.84
        v -= 0.13 * _band(_dist_to(_BACK_LINE, x, y), 22.0)      # light along the back
        v -= 0.10 * _band(_dist_to(_COVERT_LINE, x, y), 10.0)    # the covert streak
        v += 0.20 * _band(_dist_to(_NECK_FRONT, x, y), 14.0)     # dark margin down the throat
        v += 0.15 * _band(_dist_to(_BREAST_LINE, x, y), 26.0)    # the breast carries the weight
        v += 0.19 * _ramp(672.0, 744.0, y)                       # weight under the belly
        v += 0.20 * _band(_dist_to(_CROWN_LINE, x, y), 15.0)     # the crown stripe
        # Low-frequency mottle. Perfectly even tone is printing, not engraving.
        v += 0.07 * math.sin(x * 0.031 + y * 0.017) * math.sin(y * 0.024 - x * 0.009)
        # Into the perimeter. The edge is where the tone runs out, not where a line stops.
        v *= 0.62 + 0.38 * _ramp(0.5, 9.0, field.edge(x, y))
        if math.hypot(x - ex, y - ey) < 13.0:                    # the eye keeps its paper
            v *= 0.10
        return max(0.0, min(0.97, v))

    return tone


def _beak_tone_fn(field: _Field):
    """The bill is the one part of the bird that is not plumage, and it is cut like it: dense
    passes running the length of the dagger, with a lit edge along the culmen so the top of the
    bill separates from the sky rather than being drawn against it."""
    def tone(x: float, y: float) -> float:
        v = 0.93 - 0.22 * _band(_dist_to(_CULMEN, x, y), 6.0)
        v += 0.05 * math.sin(x * 0.06 + y * 0.03)
        v *= 0.30 + 0.70 * _ramp(0.4, 5.0, field.edge(x, y))
        return max(0.0, min(0.97, v))

    return tone


def _flow(x: float, y: float):
    """The burin's direction at a point — the tangent of whichever armature owns this part of the
    bird, blended by inverse square distance so the field turns rather than tears."""
    sx = sy = w = 0.0
    for arm, weight in ((_BEAK_AXIS, 1.0), (_NECK_AXIS, 1.0), (_BODY_AXIS, 1.0), (_WING_FLOW, 0.9)):
        (tx, ty), d = _tangent(arm, x, y)
        k = weight / (d * d + 260.0)
        sx += tx * k
        sy += ty * k
        w += k
    L = math.hypot(sx, sy) or 1.0
    return sx / L, sy / L


def _leg_flow(axis):
    def f(x, y):
        (tx, ty), _ = _tangent(axis, x, y)
        return tx, ty
    return f


# ---------------------------------------------------------------------------------------------
# the engraver's marks
# ---------------------------------------------------------------------------------------------

def _streams(field: _Field, flow, d_sep: float, step: float = 2.6,
             test: float = 0.58, max_pts: int = 620, cap: int = 1400):
    """Evenly-spaced streamlines through the flow field, clipped to the region.

    Jobard–Lefebvre: integrate one line, then sow new seeds a separation-distance off it on both
    sides, and keep going until nothing new will fit. The result is what a plate actually looks
    like — long passes that hold their spacing as they travel with the form, rather than a grid
    laid over it.
    """
    cell = d_sep
    grid: dict = {}

    def near(px, py, r):
        i0, j0 = int(px // cell), int(py // cell)
        rr = r * r
        for i in range(i0 - 1, i0 + 2):
            for j in range(j0 - 1, j0 + 2):
                for qx, qy in grid.get((i, j), ()):
                    if (qx - px) ** 2 + (qy - py) ** 2 < rr:
                        return True
        return False

    def march(px, py, sign):
        pts = [(px, py)]
        for _ in range(max_pts):
            dx, dy = flow(px, py)
            mx, my = px + sign * dx * step * 0.5, py + sign * dy * step * 0.5
            dx, dy = flow(mx, my)
            qx, qy = px + sign * dx * step, py + sign * dy * step
            if not field.inside(qx, qy) or near(qx, qy, d_sep * test):
                break
            pts.append((qx, qy))
            px, py = qx, qy
        return pts

    lines = []
    queue = [field.seed()]
    head = 0
    gap = max(1, int(round(d_sep / step)))
    while head < len(queue) and len(lines) < cap:
        sx, sy = queue[head]
        head += 1
        if not field.inside(sx, sy) or near(sx, sy, d_sep * 0.92):
            continue
        fwd = march(sx, sy, 1)
        bwd = march(sx, sy, -1)
        line = bwd[:0:-1] + fwd
        if len(line) < 3:
            continue
        for px, py in line:
            grid.setdefault((int(px // cell), int(py // cell)), []).append((px, py))
        lines.append(line)
        for i in range(0, len(line), gap):
            px, py = line[i]
            dx, dy = flow(px, py)
            queue.append((px - dy * d_sep, py + dx * d_sep))
            queue.append((px + dy * d_sep, py - dx * d_sep))
    return lines


def _ink(lines, seq: _Seq, tone, gain: float = 1.0, hold: float = 0.34, gape: float = 0.5,
         floor: float = 0.05, wander: float = 0.4):
    """Turn streamlines into burin passes.

    The line does not fade — it *runs* while the tone will carry it and breaks up when it will
    not. Two probabilities do all the work: how likely a stroke is to continue (rises steeply with
    tone, so shadow gets long unbroken passes) and how long the gap is once it stops. At the light
    end the same machinery leaves nothing but nicks, which is exactly how the form thins out into
    the paper. Returns (points, mean-tone) runs so the caller can bucket them by weight.
    """
    out = []
    for line in lines:
        n = len(line)
        i = 0
        while i < n - 1:
            x, y = line[i]
            v = min(0.97, tone(x, y) * gain)
            if v <= floor or seq.unit() > v ** 0.62:
                i += 1
                continue
            run, acc, cnt = [], 0.0, 0
            while i < n:
                x, y = line[i]
                v = min(0.97, tone(x, y) * gain)
                o = seq.span(-wander, wander)
                if run:                                    # jitter across the pass, not along it
                    px, py = run[-1]
                    dx, dy = x - px, y - py
                    L = math.hypot(dx, dy) or 1.0
                    run.append((x - dy / L * o, y + dx / L * o))
                else:
                    run.append((x, y))
                acc += v
                cnt += 1
                i += 1
                if v <= floor or seq.unit() > v ** hold:
                    break
            if len(run) > 1:
                out.append((run, acc / cnt))
            # the gap: short nicks in the shadow, long silences in the light
            v = min(0.97, tone(*line[min(i, n - 1)]) * gain)
            skip = 1
            while i + skip < n and seq.unit() < (1.0 - v) ** gape:
                skip += 1
            i += skip
    return out


def _simplify(pts, tol: float = 0.38):
    """Drop points a straight-enough pass does not need. The streamlines are smooth, so this is
    most of the file size for none of the drawing."""
    if len(pts) < 3:
        return pts
    out = [pts[0]]
    ax, ay = pts[0]
    for i in range(1, len(pts) - 1):
        bx, by = pts[i + 1]
        px, py = pts[i]
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy)
        dev = abs((px - ax) * dy - (py - ay) * dx) / L if L else 0.0
        if dev > tol:
            out.append((px, py))
            ax, ay = px, py
    out.append(pts[-1])
    return out


def _stipple(field: _Field, seq: _Seq, tone, count: int, gain: float = 1.0, bias: float = 1.0):
    """A stipple field. Rejection-sampled against the tone, so it thickens exactly where the hatch
    thickens and the two never argue about where the form is."""
    x0, y0 = field.x0, field.y0
    x1 = x0 + field.nx * field.step
    y1 = y0 + field.ny * field.step
    pts = []
    for _ in range(count):
        x = seq.span(x0, x1)
        y = seq.span(y0, y1)
        if not field.inside(x, y):
            continue
        v = tone(x, y) * gain
        if seq.unit() < v ** bias:
            pts.append((x, y))
    return pts


def _run(path, seq: _Seq, tone, step: float = 5.2, gain: float = 1.0,
         jitter: float = 0.8, samples: int = 26):
    """Broken marks laid along an open path — toes, crest plumes, primary strands."""
    pts = _catmull(path, closed=False, steps=samples)
    out = []
    carry = seq.span(0.0, step)
    for i in range(len(pts) - 1):
        ax, ay = pts[i]
        bx, by = pts[i + 1]
        L = math.hypot(bx - ax, by - ay)
        if L < 1e-6:
            continue
        ux, uy = (bx - ax) / L, (by - ay) / L
        u = 0.0
        while u < L:
            if carry <= 0:
                px, py = ax + ux * u, ay + uy * u
                v = min(0.97, tone(px, py) * gain)
                if seq.unit() < v:
                    ln = step * (0.35 + 0.75 * v) * seq.span(0.7, 1.25)
                    o = seq.span(-jitter, jitter)
                    out.append((px - uy * o, py + ux * o, ux * ln, uy * ln))
                carry = step * seq.span(0.8, 1.25)
            adv = min(carry, L - u)
            carry -= adv
            u += adv
    return out


def _cross(flow, turn: float):
    """A flow rotated off the form's direction — the cross-hatch families."""
    c, s = math.cos(turn), math.sin(turn)

    def f(x, y):
        dx, dy = flow(x, y)
        return dx * c - dy * s, dx * s + dy * c
    return f


def _shadow(tone, floor: float, gain: float = 1.0):
    """Tone re-based so a family only bites where the shadow can carry it. True cross-hatching is
    a shadow technique; laid over the whole form it is what turns an engraving into a basket."""
    span = max(1e-6, 1.0 - floor)

    def f(x, y):
        return max(0.0, (tone(x, y) - floor) / span) * gain
    return f


# ---------------------------------------------------------------------------------------------
# the plate
# ---------------------------------------------------------------------------------------------

def build():
    """Cut the master. Returns groups of marks ready for :func:`render_svg`."""
    seq = _Seq(20260803)
    body = _Field(_SIL, step=2.5)
    beak = _Field(_BEAK, step=1.4, pad=3.0)
    wing = _Field(_WING, step=3.0)
    tone = _tone_fn(body)
    beak_tone = _beak_tone_fn(beak)

    def leg_tone_fn(field):
        def f(x, y):
            v = 0.86 + 0.10 * math.sin(y * 0.033) - 0.10 * _ramp(1190.0, 1340.0, y)
            return max(0.0, min(0.97, v * (0.34 + 0.66 * _ramp(0.3, 4.4, field.edge(x, y)))))
        return f

    # ── the primary passes: long, form-following, one family that owns the whole bird ──
    runs = _ink(_streams(body, _cross(_flow, math.radians(23)), 4.6), seq, tone, hold=0.26)
    # ── cross-hatch, in the shadow only, off the flow by ~70° and ~35° ──
    runs += _ink(_streams(body, _cross(_flow, math.radians(-42)), 7.0), seq,
                 _shadow(tone, 0.48), hold=0.36, gape=0.42, wander=0.3)
    runs += _ink(_streams(body, _cross(_flow, math.radians(78)), 9.6), seq,
                 _shadow(tone, 0.66), hold=0.45, gape=0.4, wander=0.3)
    # ── the wing's own direction, laid over the flank ──
    runs += _ink(_streams(wing, _cross(_flow, math.radians(-10)), 7.4), seq,
                 _shadow(tone, 0.34, 0.9), hold=0.36, gape=0.45, wander=0.35)
    # ── the bill: tighter pitch, denser tone, its own axis ──
    beak_flow = _leg_flow(_BEAK_AXIS)
    runs += _ink(_streams(beak, beak_flow, 2.9, step=2.0, max_pts=260), seq, beak_tone,
                 hold=0.22, gape=0.55, wander=0.16)
    runs += _ink(_streams(beak, _cross(beak_flow, math.radians(74)), 5.0, step=1.4, max_pts=60),
                 seq, _shadow(beak_tone, 0.60), hold=0.5, gape=0.4, wander=0.14)

    # ── the legs: structural, not stick-like. Long passes down the bone, cross ticks across it ──
    legs = []
    for axis, ws in ((_LEG_A, _LEG_A_W), (_LEG_B, _LEG_B_W)):
        poly = _thick(_catmull(axis, closed=False, steps=18), _widths(axis, ws, 18))
        fld = _Field(poly, step=1.2, pad=3.0)
        lt = leg_tone_fn(fld)
        flow = _leg_flow(_catmull(axis, closed=False, steps=8))
        legs += _ink(_streams(fld, flow, 2.9, step=2.4, max_pts=500), seq, lt,
                     hold=0.24, gape=0.5, wander=0.18)
        legs += _ink(_streams(fld, _cross(flow, math.radians(78)), 3.6, step=1.1, max_pts=40),
                     seq, _shadow(lt, 0.45), hold=0.5, gape=0.4, wander=0.14)

    feet = []
    for s in _TOES:
        feet += _run(s, seq, lambda x, y: 0.92, step=3.0, jitter=0.45)

    strands = []
    for s in _STRANDS:
        strands += _run(s, seq, tone, step=6.4, gain=0.9, jitter=0.7)
    for s in _CREST:
        strands += _run(s, seq, lambda x, y: 0.7, step=2.6, jitter=0.4)
    dots = _stipple(body, seq, tone, 30000, gain=0.55, bias=1.8)
    dots += _stipple(wing, seq, tone, 5000, gain=0.42, bias=2.0)
    # The eye is a stipple cluster, not a drawn dot: a filled circle is the one high-contrast
    # discrete element on a plate that has no other, and at hero opacity it reads as a punched
    # hole. Cut it out of the same field as everything else and it sits *in* the engraving.
    ex, ey = _EYE
    eye = []
    for _ in range(240):
        a = seq.span(0.0, math.tau)
        r = 5.4 * math.sqrt(seq.unit())
        if seq.unit() < 1.0 - 0.55 * (r / 5.4) ** 2:
            eye.append((ex + math.cos(a) * r, ey + math.sin(a) * r * 0.86))

    return {"runs": runs, "legs": legs, "strands": strands, "feet": feet,
            "dots": dots, "eye": eye}


# Stroke weight follows tone. A single width across the whole bird is a plotter's mark, not an
# engraver's: the burin cuts deeper in the shadow and the line is wider for it.
_WEIGHTS = ((0.46, 0.80), (0.68, 1.02), (1.01, 1.28))


def _bucket(runs):
    out = [[] for _ in _WEIGHTS]
    for pts, v in runs:
        for k, (hi, _) in enumerate(_WEIGHTS):
            if v <= hi or k == len(_WEIGHTS) - 1:
                out[k].append(pts)
                break
    return out


def _pass(pts) -> str:
    pts = _simplify(pts)
    d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    px, py = pts[0]
    for x, y in pts[1:]:
        d += f"l{x - px:.1f} {y - py:.1f}"
        px, py = x, y
    return d


def _marks(marks) -> str:
    return "".join(f"M{x:.1f} {y:.1f}l{dx:.1f} {dy:.1f}" for x, y, dx, dy in marks)


def _points(pts) -> str:
    return "".join(f"M{x:.1f} {y:.1f}h0" for x, y in pts)


def _body(plate) -> str:
    parts = [f'<g fill="none" stroke="{INK}" stroke-linecap="round">']
    for key, scale in (("runs", 1.0), ("legs", 0.94)):
        for group, (_, w) in zip(_bucket(plate[key]), _WEIGHTS):
            if group:
                parts.append(f'<path stroke-width="{w * scale:.2f}" '
                             f'd="{"".join(_pass(p) for p in group)}"/>')
    parts.append(f'<path stroke-width="1.25" d="{_marks(plate["strands"])}"/>')
    parts.append(f'<path stroke-width="1.55" d="{_marks(plate["feet"])}"/>')
    parts.append(f'<path stroke-width="1.4" d="{_points(plate["dots"])}"/>')
    parts.append(f'<path stroke-width="1.7" d="{_points(plate["eye"])}"/>')
    parts.append("</g>")
    return "".join(parts)


def render_svg(plate=None) -> str:
    """The master file. One ink, no outlines, no title block, no stamp."""
    plate = plate or build()
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" '
        f'preserveAspectRatio="xMidYMid meet" role="img" '
        f'aria-label="Engraving of a great blue heron standing alert, facing left">'
        f"{_body(plate)}</svg>"
    )
