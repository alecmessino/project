"""The Canonical Survey Library — ten structural plates for the Driftwood Review.

The Review's visual vocabulary is fixed, not per-issue. An article does not get a bespoke
illustration and it never gets an invented metric; it gets the one plate whose *structure*
matches its subject. Ten plates, reused forever, is what makes a run of issues read as a
continuing institutional record rather than a series of marketing emails.

Each plate is real geometry, not decoration-by-noise:

    confluence  intersecting vector streams        core systems coordination
    watershed   broad catchment boundaries         total household aggregation
    tributary   small streams feeding a channel    liquidity & cash-flow inputs
    gradient    rapidly tightening contours        tax-rate escalation / bracket friction
    basin       concentric enclosed depressions    asset pools / trapped corporate capital
    contour     uniform parallel tracking lines    factor exposure / systematic portfolios
    current     parallel directional vector paths  time-series momentum / trend
    boundary    abrupt terminal hairlines          state lines / jurisdictional domicile
    delta       multi-channel dispersion           generational transfer / estate outflows
    divide      ridge separating flow directions   risk mitigation / asset protection

So `gradient` genuinely tightens its spacing along the plate and `boundary` genuinely has two
non-matching contour families that stop dead at a line. A reader who learns the vocabulary can
read the plate; that is the whole point of fixing the library at ten.

WHY GENERATED RATHER THAN CUT FROM THE MASTER PLATES. The obvious move is to crop fragments out
of `img/survey-plate-hero.svg`. That was tried and rejected: the master plate is a single
hydrographic confluence, so every window cut from it *is* a confluence. Ten crops would give ten
pictures of the same structure wearing ten different names — the vocabulary would be a lie. These
are generated instead, but generated in the master plates' exact hand: the same ink (#1E2833),
the same sounding radii (0.75 / 0.85 / 1.3), the same stroke weights. Same surveyor, ten sites.

PURE MODULE (see CLAUDE.md): no I/O, no filesystem, no clock, no global RNG. `_Seq` is a local
LCG so a plate is byte-identical on every machine and every Python build — the SVGs are committed
assets, and a generator that drifts would show up as noise in every future diff.

Density is NOT baked in. Every plate emits all three sounding tiers and gates them on inherited
CSS custom properties (`--pl-s2`, `--pl-s3`, ...), because the publication type — research,
commentary, household — is a property of the *article*, not of the plate. Ten files serve all
three disciplines; see `driftwood-review.html`.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

# The surveyor's hand, lifted from src/drift/web/img/survey-plate-hero.svg so the generated
# library and the master plates are visibly the same instrument.
INK = "#1E2833"
SOUND_R = (0.75, 0.85, 1.3)      # tier 1, tier 2, tier 3 sounding radii
W, H = 480.0, 150.0              # fragment canvas: a wide band, sized for the card's plate zone

# The library, in order. The roman numeral is an internal catalogue index ONLY — it is never
# stamped on the artwork (the plates render clean; see test_plates_carry_no_archival_stamps).
CANON = (
    ("confluence", "I", "Intersecting vector streams"),
    ("watershed", "II", "Broad catchment boundaries"),
    ("tributary", "III", "Small streams feeding a channel"),
    ("gradient", "IV", "Rapidly tightening steep contours"),
    ("basin", "V", "Concentric enclosed depressions"),
    ("contour", "VI", "Uniform parallel tracking lines"),
    ("current", "VII", "Parallel directional vector paths"),
    ("boundary", "VIII", "Abrupt terminal hairlines"),
    ("delta", "IX", "Multi-channel dispersion systems"),
    ("divide", "X", "Ridge lines separating flow directions"),
)
NAMES = tuple(n for n, _, _ in CANON)


class _Seq:
    """A local linear-congruential sequence.

    Deliberately not `random`: these plates are committed static assets. Seeding the stdlib
    generator would still leave the output hostage to a future change in CPython's algorithm,
    and a regenerated library that differs by a pixel would rewrite ten files in a diff for no
    reason. This is fifteen lines and frozen forever.
    """

    __slots__ = ("s",)

    def __init__(self, seed: int) -> None:
        self.s = (seed * 2654435761 + 1) & 0x7FFFFFFF

    def unit(self) -> float:
        self.s = (1103515245 * self.s + 12345) & 0x7FFFFFFF
        return self.s / 0x7FFFFFFF

    def span(self, lo: float, hi: float) -> float:
        return lo + (hi - lo) * self.unit()


@dataclass
class Plate:
    """One canonical plate: named structure, its contour polylines, and its sounding field."""

    name: str
    numeral: str
    structure: str
    contours: list[list[tuple[float, float]]] = field(default_factory=list)
    # sounding points, split into the three density tiers
    tiers: tuple[list[tuple[float, float]], ...] = ((), (), ())


# ---------------------------------------------------------------------------------------------
# geometry helpers
# ---------------------------------------------------------------------------------------------

def _ease(t: float) -> float:
    """Smoothstep. Channels converge on a curve, not a corner."""
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _loop(cx: float, cy: float, rx: float, ry: float, lobes, steps: int = 96):
    """A closed, gently lobed ring — the shape a real catchment or depression traces.

    `lobes` is a sequence of (harmonic, amplitude) pairs; perfectly elliptical rings read as
    clip-art, so every closed plate carries a little harmonic irregularity.
    """
    pts = []
    for i in range(steps + 1):
        th = (i / steps) * math.tau
        k = 1.0
        for harm, amp in lobes:
            k += amp * math.sin(harm * th + harm * 0.7)
        pts.append((cx + rx * k * math.cos(th), cy + ry * k * math.sin(th)))
    return pts


def _sample(fn, x0: float, x1: float, steps: int = 60):
    """Trace y = fn(x) across [x0, x1]."""
    return [(x0 + (x1 - x0) * i / steps, fn(x0 + (x1 - x0) * i / steps)) for i in range(steps + 1)]


# ---------------------------------------------------------------------------------------------
# the ten structures
# ---------------------------------------------------------------------------------------------

def _confluence(rng: _Seq):
    """Two stream families converge into one trunk. The junction is the subject."""
    jx = 0.52 * W
    trunk = lambda x: 0.52 * H + 7.0 * math.sin(x / W * 2.2 + 0.3)
    out = []
    for k in range(-3, 4):
        o = k * 5.6
        out.append(_sample(lambda x, o=o: trunk(x) + o, 0.0, W, 72))          # upper -> trunk
        # the lower family exists only until the junction; past it there is one channel, not two
        out.append([
            (x, (0.86 * H + o * 0.7) * (1 - _ease(x / jx)) + (trunk(x) + o) * _ease(x / jx))
            for x in (jx * i / 48 for i in range(49))
        ])
    return out, 1.0


def _watershed(rng: _Seq):
    """Nested catchment boundaries: each ring encloses the last."""
    out = []
    for k in range(1, 6):
        out.append(_loop(0.5 * W, 0.5 * H, 26 + k * 37, 13 + k * 17,
                         ((3, 0.13), (5, 0.06), (2, 0.05))))
    return out, 0.85


def _tributary(rng: _Seq):
    """A main channel with small feeders joining it *downstream-ward*.

    Feeders must arrive tangentially, at a shallow angle pointing the way the trunk already
    flows — a stream that meets its channel head-on is a road crossing, not a tributary. The
    trunk carries banks; the feeders are single lines, because they are small.
    """
    chan = lambda x: 0.74 * H + 7.0 * math.sin(x / W * 2.6)
    out = [_sample(lambda x, o=o: chan(x) + o, 0.0, W, 72) for o in (-5.0, 5.0)]
    # Feeders must stay SMALL relative to the trunk — sized to reach the channel, not to rival it.
    for fx, reach, top in ((0.14, 0.11, 0.46), (0.27, 0.15, 0.30), (0.41, 0.10, 0.52),
                           (0.56, 0.17, 0.24), (0.72, 0.12, 0.44), (0.91, 0.16, 0.31)):
        jx, sx, ty = fx * W, (fx - reach) * W, top * H
        out.append([
            # x eases out early, y falls late: the feeder drops, then lays over and merges along
            # the trunk's own direction instead of striking it head-on
            (sx + (jx - sx) * (t ** 0.6), ty + (chan(jx) - 5.0 - ty) * (t ** 2.1))
            for t in (j / 30 for j in range(31))
        ])
    return out, 1.05


def _gradient(rng: _Seq):
    """Contour spacing collapses across the plate — the plate *is* the escalation.

    The interval is a geometric series solved to span the canvas: with ratio r over n intervals
    the first step is W(1-r)/(1-r^n). Anything less aggressive reads as evenly-spaced contour and
    the plate stops meaning bracket friction.
    """
    out, r, n = [], 0.82, 15
    step = W * (1 - r) / (1 - r ** n)
    x = 0.02 * W
    for _ in range(n):
        out.append([(x + 9.0 * math.sin(y / H * 2.1 + x / W), y)
                    for y in (H * j / 40 for j in range(41))])
        x += step
        step *= r
    return out, 1.15


def _basin(rng: _Seq):
    """Two enclosed depressions, rings tightening toward each low point."""
    out = []
    for cx, cy, sc in ((0.33 * W, 0.54 * H, 1.0), (0.71 * W, 0.44 * H, 0.74)):
        for k in range(1, 6):
            r = (k / 5.0) ** 1.45
            out.append(_loop(cx, cy, sc * (10 + r * 92), sc * (6 + r * 46),
                             ((3, 0.10), (4, 0.05))))
    return out, 0.9


def _contour(rng: _Seq):
    """Uniform spacing, uniform phase — a systematic field with nothing singular in it."""
    return [_sample(lambda x, y0=y0: y0 + 6.5 * math.sin(x / W * 2.4 + 0.2), 0.0, W, 64)
            for y0 in (H * (i + 0.5) / 9 for i in range(9))], 0.8


def _current(rng: _Seq):
    """Parallel directional paths, all running one way.

    Distinguished from `contour` by three things a reader can see without being told: the paths
    start at ragged, staggered x (a trend has an onset; a contour does not), they carry a common
    downstream drift, and their phase walks line to line so the family shears rather than nests.
    Without that, momentum and factor exposure render as the same picture.

    Card-scale legibility drove the final numbers. At the first pass this plate sat beside
    `contour` in the same row of the Review and the two were indistinguishable: twelve near-
    horizontal lines either way. Fewer lines (so the gaps register), a much wider spread of onsets,
    and a drift strong enough to survive the card's centre crop are what separate them.
    """
    out = []
    for i in range(9):
        y0 = H * (i + 0.5) / 9
        x0 = rng.span(0.02, 0.44) * W
        x1 = W * rng.span(0.84, 1.0)
        out.append(_sample(
            lambda x, y0=y0, i=i: y0 + 8.0 * math.sin(x / W * 1.5 + i * 0.55) - (x / W) ** 1.4 * 23.0,
            x0, x1, 52))
    return out, 0.9


def _boundary(rng: _Seq):
    """Two contour families that stop dead at a line and do not match across it."""
    bx = 0.46 * W
    out = [[(bx, 0.0), (bx, H)]]                                   # the line itself
    for i in range(7):                                             # west: shallow, wide-spaced
        y0 = H * (i + 0.5) / 7
        out.append(_sample(lambda x, y0=y0: y0 + 5.0 * math.sin(x / W * 1.8), 0.0, bx, 30))
    for i in range(12):                                            # east: steep, tight, unaligned
        y0 = H * (i + 0.5) / 12 - 4.0
        out.append(_sample(lambda x, y0=y0: y0 + 9.0 * math.sin(x / W * 3.4 + 1.1), bx, W, 34))
    return out, 1.0


def _delta(rng: _Seq):
    """One channel disperses into many, in stages. Nothing recombines.

    A single fan from one apex reads as a starburst. A real delta bifurcates repeatedly, so each
    branch splits again downstream — which is also the honest picture of generational transfer:
    the dispersion compounds, it does not happen once.
    """
    out = [[(0.0, 0.5 * H - 4.5), (0.26 * W, 0.5 * H - 3.4)],
           [(0.0, 0.5 * H + 4.5), (0.26 * W, 0.5 * H + 3.4)]]

    def branch(x0: float, y0: float, spread: float, depth: int) -> None:
        x1 = x0 + (W - x0) * (0.42 if depth else 0.62)
        for sign in (-1.0, 1.0):
            y1 = y0 + sign * spread
            out.append([
                (x0 + (x1 - x0) * t, y0 + (y1 - y0) * _ease(t) + 2.0 * math.sin(t * 3.4 + y0))
                for t in (j / 26 for j in range(27))
            ])
            if depth:
                branch(x1, y1, spread * 0.46, depth - 1)

    branch(0.26 * W, 0.5 * H, 0.235 * H, 2)
    return out, 1.0


def _divide(rng: _Seq):
    """A ridge, and two slopes whose contours fall away from it in OPPOSITE directions.

    The failure mode here is subtle and was caught in review: decaying one shared waveform on both
    sides produces eleven parallel undulating lines — i.e. `contour` again, which is the wrong
    plate. Inverting the phase of that horizontal family was tried next and still read as `contour`
    at card size. What works is a *diagonal* crest with the slope contours meeting it from both sides at
    mirrored angles: a herringbone can only be read one way. Every contour terminates ON the ridge,
    because a contour that crossed it would mean the two catchments drain together, which is the
    opposite of what this plate is for.
    """
    y0, y1 = 0.88 * H, 0.12 * H
    rx, ry = W, y1 - y0                                       # ridge direction
    rl = math.hypot(rx, ry)
    rx, ry = rx / rl, ry / rl
    nx, ny = -ry, rx                                          # unit normal, pointing south-east
    out = [[(0.0, y0), (W, y1)]]                              # the crest itself

    a = math.radians(70.0)   # near-perpendicular: the cartographic mark for a scarp, not a feather
    ca, sa = math.cos(a), math.sin(a)
    # MIRRORED about the crest, not negated. Negating gives south = -north, which is the same
    # straight line continued — the comb then runs *through* the ridge and the plate says the two
    # catchments drain together. Reflecting across the crest gives a chevron that meets at it.
    north = (rx * ca - nx * sa, ry * ca - ny * sa)
    south = (rx * ca + nx * sa, ry * ca + ny * sa)
    for i in range(24):
        t = (i + 0.5) / 24
        px, py = W * t, y0 + (y1 - y0) * t
        for dx, dy in (north, south):
            L = 62.0 + 26.0 * math.sin(i * 0.9)               # ragged edge, not a machined comb
            out.append([(px + dx * L * j / 12, py + dy * L * j / 12) for j in range(13)])
    return out, 0.8


_BUILDERS = {
    "confluence": _confluence, "watershed": _watershed, "tributary": _tributary,
    "gradient": _gradient, "basin": _basin, "contour": _contour, "current": _current,
    "boundary": _boundary, "delta": _delta, "divide": _divide,
}


# ---------------------------------------------------------------------------------------------
# sounding field
# ---------------------------------------------------------------------------------------------

def _soundings(contours, rng: _Seq, weight: float):
    """Scatter sounding points the way a survey actually carries them: dense along the traced
    structure, thinning into the open field. Points are split into three tiers so the publication
    type can thin the plate without changing its geometry."""
    tiers: tuple[list, list, list] = ([], [], [])

    # A FIXED budget, not a per-contour rate. Sampling at a rate-per-contour makes a plate's file
    # size scale with how many polylines its structure happens to need — `divide` draws 49 short
    # herringbone arms and `watershed` draws 5 long rings, so the naive version made divide three
    # times the weight for no more visible ink. Ten of these are inlined on one page; a plate's
    # cost has to track what it looks like, not how it was constructed.
    flat = [p for pts in contours for p in pts]
    budget = int(300 * weight)
    stride = max(1, len(flat) // budget) if budget else 1
    for i in range(0, len(flat), stride):
        x, y = flat[i]
        px, py = x + rng.span(-7.0, 7.0), y + rng.span(-6.0, 6.0)
        if not (0 <= px <= W and 0 <= py <= H):
            continue
        u = rng.unit()
        tiers[0 if u < 0.34 else (1 if u < 0.72 else 2)].append((px, py))
    for _ in range(int(90 * weight)):                      # open field, away from the structure
        u = rng.unit()
        tiers[1 if u < 0.55 else 2].append((rng.span(0, W), rng.span(0, H)))
    return tiers


def build(name: str) -> Plate:
    """Build one canonical plate by name. Deterministic: same name in, same geometry out."""
    if name not in _BUILDERS:
        raise KeyError(f"{name!r} is not in the canonical survey library: {', '.join(NAMES)}")
    numeral, structure = next((n, s) for k, n, s in CANON if k == name)
    rng = _Seq(NAMES.index(name) + 7)
    contours, weight = _BUILDERS[name](rng)
    return Plate(name=name, numeral=numeral, structure=structure, contours=contours,
                 tiers=_soundings(contours, rng, weight))


def build_all() -> list[Plate]:
    return [build(n) for n in NAMES]


# ---------------------------------------------------------------------------------------------
# rendering
# ---------------------------------------------------------------------------------------------

SIMPLIFY_TOL = 0.35   # px on the 480x150 canvas — below one device pixel at any size we render


def _simplify(points, tol: float = SIMPLIFY_TOL):
    """Ramer–Douglas–Peucker, with the closed-ring case handled.

    The builders sample every curve densely because that keeps the *geometry* readable — a
    generator that hand-tuned step counts per plate to save bytes would be unmaintainable. Instead
    the cost is removed here: a smooth arc collapses to a few points while a sharp feature (the
    delta's bifurcations, the boundary's terminations) keeps every vertex it needs. The tolerance
    is sub-pixel, so this is free visually and roughly halves the inlined library.

    CLOSED RINGS NEED THE SPLIT. `basin` and `watershed` are rings, so their first and last points
    coincide and plain RDP measures every vertex against a zero-length chord — which collapses a
    catchment boundary to a couple of segments and deforms it by several pixels. Splitting the ring
    at its farthest vertex first gives two well-formed arcs. (Caught by
    test_simplification_stays_sub_pixel, which measures the actual deviation rather than trusting
    the algorithm.)
    """
    if len(points) < 3:
        return list(points)
    if math.dist(points[0], points[-1]) < 1.0:
        far = max(range(1, len(points) - 1), key=lambda i: math.dist(points[0], points[i]))
        return _simplify(points[:far + 1], tol)[:-1] + _simplify(points[far:], tol)
    (ax, ay), (bx, by) = points[0], points[-1]
    dx, dy = bx - ax, by - ay
    norm = math.hypot(dx, dy)
    worst, idx = -1.0, 0
    for i in range(1, len(points) - 1):
        px, py = points[i]
        # distance from the chord; degenerate chord (closed loop) falls back to radial distance
        dist = (abs(dy * px - dx * py + bx * ay - by * ax) / norm if norm
                else math.hypot(px - ax, py - ay))
        if dist > worst:
            worst, idx = dist, i
    if worst <= tol:
        return [points[0], points[-1]]
    return _simplify(points[:idx + 1], tol)[:-1] + _simplify(points[idx:], tol)


def _d(points) -> str:
    points = _simplify(points)
    if not points:
        return ""
    head = f"M{points[0][0]:.1f} {points[0][1]:.1f}"
    return head + "".join(f"L{x:.1f} {y:.1f}" for x, y in points[1:])


def _body(plate: Plate) -> str:
    """The plate's inner markup: contours, then the three sounding tiers.

    Tiers 2 and 3 gate on inherited custom properties. Custom properties are the one thing that
    crosses a <use> shadow boundary, which is what lets ONE symbol library serve research,
    commentary, and household densities without emitting thirty files or duplicating geometry.
    """
    parts = [
        f'<g class="pl-c" fill="none" stroke="{INK}" stroke-width="var(--pl-w,1)" '
        f'stroke-opacity="var(--pl-ink,.5)" stroke-linecap="round">'
    ]
    parts += [f'<path d="{_d(c)}"/>' for c in plate.contours]
    parts.append("</g>")
    for idx, (tier, radius, gate) in enumerate(
            zip(plate.tiers, SOUND_R, ("1", "var(--pl-s2,1)", "var(--pl-s3,1)"))):
        if not tier:
            continue
        parts.append(
            f'<g class="pl-s{idx + 1}" fill="{INK}" '
            f'fill-opacity="calc({gate} * var(--pl-sound,.34))">'
        )
        # Integer coordinates: soundings are 0.75–1.3px dots on a 480×150 canvas, so a decimal
        # place is invisible and costs ~20% of the page weight across ten inlined plates.
        seen = set()
        for x, y in tier:
            key = (round(x), round(y))
            if key in seen:
                continue
            seen.add(key)
            parts.append(f'<circle cx="{key[0]}" cy="{key[1]}" r="{radius}"/>')
        parts.append("</g>")
    return "".join(parts)


def render_svg(plate: Plate) -> str:
    """A standalone plate file. Clean artwork: no numeral, no sheet stamp, no title block."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" '
        f'preserveAspectRatio="xMidYMid slice" role="img" '
        f'aria-label="Survey plate: {plate.structure.lower()}">'
        f"{_body(plate)}</svg>"
    )


def render_symbols(plates=None) -> str:
    """The whole library as one inline <symbol> set, for pages that need CSS-driven density."""
    plates = list(plates or build_all())
    syms = "".join(
        f'<symbol id="pl-{p.name}" viewBox="0 0 {W:.0f} {H:.0f}" '
        f'preserveAspectRatio="xMidYMid slice">{_body(p)}</symbol>'
        for p in plates
    )
    return (
        '<svg class="pl-lib" xmlns="http://www.w3.org/2000/svg" width="0" height="0" '
        f'aria-hidden="true" focusable="false" style="position:absolute">{syms}</svg>'
    )
