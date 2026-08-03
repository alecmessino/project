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

Tone is built the way an engraver builds it: two hatch families crossing at roughly sixty
degrees, a third family following the wing's feather flow, and a stipple field. Density is
modulated by :func:`_tone` — lighter along the back and the wing's leading edge, heavier under
the belly and down the front of the neck — so the form is carried by tone alone.

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
    an anchor to hold a cusp there — the beak tip and the primaries are points, not curves.
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


def _inside(poly, x: float, y: float) -> bool:
    """Even-odd point-in-polygon."""
    hit = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            hit = not hit
        j = i
    return hit


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
    """A closed polygon around a centreline with a per-node half-width. Legs and plumes."""
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


# ---------------------------------------------------------------------------------------------
# the anatomy — Standing, Alert; facing left, into the page
# ---------------------------------------------------------------------------------------------
# Proportions are a great blue heron's, held to the approved pose: weight settled on both legs,
# neck extended but unstruck, head level and watchful. Nothing here is stylised into a mascot —
# the bird has to survive being looked at by someone who knows the bird.

_SIL = _catmull([
    (50, 120), (50, 120),                                  # dagger tip (cusp)
    (88, 110), (186, 86), (243, 69),                       # culmen, up to the forehead
    (258, 60), (285, 55), (318, 62), (345, 74), (362, 90),  # crown and nape
    (352, 112), (338, 132), (326, 152),                    # nape into the back of the neck
    (330, 190), (340, 230), (352, 262), (365, 284),
    (388, 330), (415, 375), (450, 420), (481, 440),        # neck, into the shoulder
    (533, 455), (600, 474), (665, 500), (730, 536),        # the back
    (792, 576), (838, 612), (866, 648), (866, 648),        # primaries, past the tail (cusp)
    (830, 676), (768, 696), (700, 705), (620, 707),        # under the tail
    (542, 704), (466, 692), (404, 674), (364, 646),        # the belly
    (344, 608), (342, 574), (350, 540), (355, 508),        # the breast
    (348, 470), (335, 410), (315, 355), (295, 300),        # the front of the neck
    (280, 250), (276, 200), (282, 152),
    (288, 138), (276, 126), (260, 116), (243, 108),        # jaw, to the gape
    (185, 114), (90, 120),                                 # lower mandible, back to the tip
], steps=10)

# The beak is hatched along its own axis, so it is cut as its own region. The shared edge at the
# gape is an anatomical line, not a seam.
_BEAK = _catmull([
    (50, 120), (50, 120), (88, 110), (186, 86), (243, 69),
    (243, 108), (243, 108), (185, 114), (90, 120),
], steps=10)

# The folded wing: everything below the covert line. It carries a third hatch family running back
# toward the primaries, which is what gives the flank its direction.
_WING = _catmull([
    (398, 496), (500, 524), (620, 550), (740, 578), (804, 598),
    (866, 648), (866, 648), (830, 676), (768, 696), (700, 705),
    (620, 707), (542, 704), (466, 692), (404, 674), (368, 648),
    (372, 592), (382, 540),
], steps=10)

# Tonal armatures. The bird's form is carried entirely by where these run.
_BACK_LINE = [(490, 464), (540, 479), (604, 498), (668, 524), (730, 560), (790, 598), (834, 634)]
_COVERT_LINE = [(398, 496), (500, 524), (620, 550), (740, 578), (804, 598)]
_BREAST_LINE = [(352, 516), (358, 566), (372, 620), (398, 658), (446, 682)]
_NECK_FRONT = [(282, 152), (276, 200), (280, 250), (295, 300), (315, 355),
               (335, 410), (348, 470), (355, 510), (350, 555), (344, 600)]
_CROWN_LINE = [(250, 68), (288, 60), (326, 65), (356, 86)]
_CULMEN = [(50, 120), (88, 110), (186, 86), (243, 69)]
_EYE = (258, 78)

_LEG_A = [(507, 690), (501, 890), (494, 1086), (488, 1250), (486, 1332)]
_LEG_B = [(600, 690), (590, 890), (578, 1086), (568, 1250), (564, 1332)]
_LEG_A_W = [11.0, 8.2, 6.8, 5.8, 5.2]
_LEG_B_W = [10.4, 7.8, 6.4, 5.5, 5.0]

# Toes and plumes are drawn as broken runs, not shapes: at this weight a toe is a line of marks.
_TOES = [
    [(486, 1332), (450, 1344), (420, 1352), (398, 1357)],
    [(486, 1332), (455, 1352), (432, 1363)],
    [(486, 1332), (508, 1340), (536, 1345)],
    [(564, 1332), (528, 1345), (502, 1353)],
    [(564, 1332), (540, 1354), (520, 1364)],
    [(564, 1332), (610, 1340), (664, 1344), (700, 1345)],
]
_CREST = [
    [(332, 66), (366, 78), (394, 88), (408, 93)],
    [(338, 80), (364, 90), (382, 97)],
]
# Long scapular and primary strands. An engraver draws a handful of these and lets them carry the
# feather direction the hatch only implies.
_STRANDS = [
    [(470, 484), (560, 516), (660, 552), (762, 590), (846, 632)],
    [(455, 516), (560, 548), (670, 584), (774, 620), (856, 652)],
    [(470, 560), (580, 590), (690, 618), (786, 646), (854, 664)],
    [(500, 602), (600, 628), (700, 650), (794, 668), (846, 672)],
    [(520, 644), (620, 662), (710, 674), (790, 682)],
    [(430, 468), (520, 490), (620, 516), (700, 542)],
]


def _tone(x: float, y: float) -> float:
    """Ink density at a point, 0 (paper) to 1 (solid). The whole bird is in this function.

    Light falls from above and slightly behind, the way it does on a bird standing in open water
    under a flat sky: the back and the covert line catch it, the breast and the underbelly sit in
    it, the front of the neck holds a dark margin that is what actually reads as "neck" at a
    glance.
    """
    v = 0.72
    v -= 0.19 * _band(_dist_to(_BACK_LINE, x, y), 24.0)      # light along the back
    v -= 0.15 * _band(_dist_to(_COVERT_LINE, x, y), 12.0)    # the covert streak
    v += 0.20 * _band(_dist_to(_NECK_FRONT, x, y), 14.0)     # dark margin down the throat
    v += 0.14 * _band(_dist_to(_BREAST_LINE, x, y), 26.0)    # the breast carries the weight
    v += 0.18 * _ramp(636.0, 702.0, y)                       # weight under the belly
    v += 0.20 * _band(_dist_to(_CROWN_LINE, x, y), 15.0)     # the crown stripe
    # Low-frequency mottle. Perfectly even tone is printing, not engraving.
    v += 0.07 * math.sin(x * 0.031 + y * 0.017) * math.sin(y * 0.024 - x * 0.009)
    ex, ey = _EYE
    if math.hypot(x - ex, y - ey) < 12.0:                    # the eye keeps its paper
        v = 0.02
    return max(0.05, min(0.97, v))


def _beak_tone(x: float, y: float) -> float:
    """The bill is the one part of the bird that is not plumage, and it is cut like it: near-solid
    hatch running the length of the dagger, with a lit edge along the culmen so the top of the
    bill separates from the sky rather than being drawn against it."""
    v = 0.90 - 0.20 * _band(_dist_to(_CULMEN, x, y), 6.5)
    v += 0.05 * math.sin(x * 0.06 + y * 0.03)
    return max(0.18, min(0.97, v))


# ---------------------------------------------------------------------------------------------
# the engraver's marks
# ---------------------------------------------------------------------------------------------

def _spans(poly, angle: float, spacing: float, phase: float = 0.0,
           seq: "_Seq | None" = None, wobble: float = 0.0):
    """Scan `poly` with parallel lines at `angle` and return the inside runs, in world space.

    Analytic rather than an SVG clip-path: the mark has to survive being rasterised by a print
    RIP, a laser, and a die — all of which are happier with real geometry than with a clip.

    `wobble` varies the line pitch. Two families at a fixed pitch cross into a visible weave, and
    a weave is a texture the eye resolves as *pattern*; a hand's pitch never quite repeats, and
    that irregularity is what keeps the tone reading as tone.
    """
    c, s = math.cos(-angle), math.sin(-angle)
    rot = [(x * c - y * s, x * s + y * c) for x, y in poly]
    ic, is_ = math.cos(angle), math.sin(angle)
    lo = min(p[1] for p in rot)
    hi = max(p[1] for p in rot)
    runs = []
    t = lo + phase * spacing
    while t <= hi:
        xs = []
        n = len(rot)
        j = n - 1
        for i in range(n):
            xi, yi = rot[i]
            xj, yj = rot[j]
            if (yi > t) != (yj > t):
                xs.append(xi + (t - yi) * (xj - xi) / (yj - yi))
            j = i
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            a, b = xs[k], xs[k + 1]
            if b - a > 1.2:
                runs.append(((a * ic - t * is_, a * is_ + t * ic),
                             (b * ic - t * is_, b * is_ + t * ic)))
        t += spacing * (1.0 + wobble * (seq.unit() - 0.5)) if (seq and wobble) else spacing
    return runs


def _cut(runs, seq: _Seq, tone, gain: float = 1.0, step: float = 6.4,
         bite: float = 1.0, jitter: float = 0.35, floor: float = 0.12):
    """Walk each run and lay strokes down it, in proportion to local tone.

    Both the *chance* of a stroke and its *length* follow the tone, which is how a burin actually
    lightens: the line does not fade, it breaks up and shortens. At full tone consecutive strokes
    close up into a continuous cut, which is the difference between an engraving and a scribble.
    Nothing here draws a contour — that would be an outline, and the mark has none.
    """
    out = []
    for (ax, ay), (bx, by) in runs:
        dx, dy = bx - ax, by - ay
        L = math.hypot(dx, dy)
        if L < 1.2:
            continue
        ux, uy = dx / L, dy / L
        nx, ny = -uy, ux
        u = seq.span(0.0, step)
        while u < L:
            px, py = ax + ux * u, ay + uy * u
            v = tone(px, py) * gain
            if v > floor and seq.unit() < v:
                ln = min(step * bite * (0.55 + 0.55 * v) * seq.span(0.85, 1.15), L - u)
                if ln > 0.7:
                    o = seq.span(-jitter, jitter)
                    out.append((px + nx * o, py + ny * o, ux * ln, uy * ln))
            u += step * seq.span(0.9, 1.12)
    return out


def _stipple(poly, seq: _Seq, tone, count: int, gain: float = 1.0, bias: float = 1.0):
    """A stipple field over a region. Rejection-sampled against the tone, so it thickens exactly
    where the hatch thickens and the two never argue about where the form is."""
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    pts = []
    for _ in range(count):
        x = seq.span(x0, x1)
        y = seq.span(y0, y1)
        if not _inside(poly, x, y):
            continue
        v = tone(x, y) * gain
        if seq.unit() < v ** bias:
            pts.append((x, y))
    return pts


def _run(path, seq: _Seq, tone, step: float = 5.2, gain: float = 1.0,
         jitter: float = 0.8, samples: int = 26):
    """Broken marks laid along an open path — toes, crest plumes, feather strands."""
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
                    ln = step * (0.3 + 0.6 * v) * seq.span(0.7, 1.25)
                    o = seq.span(-jitter, jitter)
                    out.append((px - uy * o, py + ux * o, ux * ln, uy * ln))
                carry = step * seq.span(0.8, 1.25)
            adv = min(carry, L - u)
            carry -= adv
            u += adv
    return out


# ---------------------------------------------------------------------------------------------
# the plate
# ---------------------------------------------------------------------------------------------

def build():
    """Cut the master. Returns groups of marks ready for :func:`render_svg`."""
    seq = _Seq(20260803)

    def leg_tone(x, y):
        # Legs are darker than the plumage and shade unevenly down their length, which is what
        # stops them reading as two drawn lines.
        return min(0.96, 0.72 + 0.14 * math.sin(y * 0.035) - 0.07 * _ramp(1180.0, 1340.0, y))

    leg_a = _thick(_catmull(_LEG_A, closed=False, steps=18),
                   [w for w in _resample_w(_LEG_A, _LEG_A_W, 18)])
    leg_b = _thick(_catmull(_LEG_B, closed=False, steps=18),
                   [w for w in _resample_w(_LEG_B, _LEG_B_W, 18)])

    # Two crossing families over the whole bird, one following the wing, and a stipple field.
    hatch = []
    hatch += _cut(_spans(_SIL, math.radians(-6), 5.6, seq=seq, wobble=0.34), seq, _tone, step=6.6)
    hatch += _cut(_spans(_SIL, math.radians(62), 6.4, phase=0.37, seq=seq, wobble=0.34), seq,
                  _tone, gain=0.92, step=6.2)
    hatch += _cut(_spans(_SIL, math.radians(28), 11.0, phase=0.61, seq=seq, wobble=0.5), seq,
                  _tone, gain=0.42, step=7.4)
    hatch += _cut(_spans(_WING, math.radians(-24), 7.4, phase=0.18, seq=seq, wobble=0.3), seq,
                  _tone, gain=0.80, step=6.8)
    hatch += _cut(_spans(_BEAK, math.radians(9), 2.9), seq, _beak_tone, step=7.0, jitter=0.22)
    hatch += _cut(_spans(_BEAK, math.radians(78), 4.6, phase=0.5), seq, _beak_tone, gain=0.5,
                  step=4.6, jitter=0.2)

    legs = []
    legs += _cut(_spans(leg_a, math.radians(74), 3.0), seq, leg_tone, step=4.4, jitter=0.3)
    legs += _cut(_spans(leg_b, math.radians(74), 3.0, phase=0.4), seq, leg_tone, step=4.4,
                 jitter=0.3)
    legs += _cut(_spans(leg_a, math.radians(12), 3.4, phase=0.3), seq, leg_tone, gain=0.55,
                 step=5.0, jitter=0.25)
    legs += _cut(_spans(leg_b, math.radians(12), 3.4, phase=0.7), seq, leg_tone, gain=0.55,
                 step=5.0, jitter=0.25)

    strands = []
    for s in _STRANDS:
        strands += _run(s, seq, _tone, step=6.0, gain=0.85, jitter=0.9)
    for s in _CREST:
        strands += _run(s, seq, lambda x, y: 0.86, step=3.2, jitter=0.45)
    for s in _TOES:
        strands += _run(s, seq, lambda x, y: 0.8, step=3.2, jitter=0.5)

    dots = _stipple(_SIL, seq, _tone, 26000, gain=0.62, bias=1.6)
    dots += _stipple(_WING, seq, _tone, 6000, gain=0.5, bias=1.7)
    dots += _stipple(leg_a, seq, leg_tone, 2600, gain=0.5)
    dots += _stipple(leg_b, seq, leg_tone, 2600, gain=0.5)

    return {"hatch": hatch, "legs": legs, "strands": strands, "dots": dots, "eye": _EYE}


def _resample_w(nodes, widths, steps):
    """Half-widths for a Catmull-Rom resample of `nodes` — linear between the node values."""
    out = []
    n = len(nodes)
    for i in range(n - 1):
        for k in range(steps):
            t = k / steps
            out.append(widths[i] + (widths[i + 1] - widths[i]) * t)
    out.append(widths[-1])
    return out


def _marks(marks) -> str:
    return "".join(f"M{x:.1f} {y:.1f}l{dx:.1f} {dy:.1f}" for x, y, dx, dy in marks)


def _points(pts) -> str:
    return "".join(f"M{x:.1f} {y:.1f}h0" for x, y in pts)


def _body(plate) -> str:
    ex, ey = plate["eye"]
    return (
        f'<g fill="none" stroke="{INK}" stroke-linecap="round">'
        f'<path stroke-width="1.15" d="{_marks(plate["hatch"])}"/>'
        f'<path stroke-width="1.05" d="{_marks(plate["legs"])}"/>'
        f'<path stroke-width="1.3" d="{_marks(plate["strands"])}"/>'
        f'<path stroke-width="1.45" stroke-linecap="round" d="{_points(plate["dots"])}"/>'
        f'</g>'
        f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="5.2" fill="{INK}"/>'
    )


def render_svg(plate=None) -> str:
    """The master file. One ink, no outlines, no title block, no stamp."""
    plate = plate or build()
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" '
        f'preserveAspectRatio="xMidYMid meet" role="img" '
        f'aria-label="Engraving of a great blue heron standing alert, facing left">'
        f"{_body(plate)}</svg>"
    )
