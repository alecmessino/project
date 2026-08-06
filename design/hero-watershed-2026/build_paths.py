#!/usr/bin/env python3
"""Generate the cubic-bezier path data used by the three hero variants.

WHY A GENERATOR. The first pass at this drawing was hand-placed control points, and it produced a
blob: smooth, plausible, and not recognisably a watershed. The basin's silhouette is doing real
work — it is the thing that makes five abstract curves read as a river system rather than a
flourish — so its proportion has to be right rather than merely pleasant.

So the geometry comes from coordinates, not from taste:

  1. Each feature is a short list of (lat, lon) landmarks — the basin divide, and the five rivers.
     Deliberately short. Twelve landmarks per river, not two hundred: the brief asks for precise
     circuitry that evokes flow, not a survey. Simplification happens here, in the landmark list,
     where it can be reasoned about — never later as jitter smoothed out of a traced outline.

  2. One equirectangular projection, with the latitude scale held at 1.31x the longitude scale
     (the true ratio of a degree of latitude to a degree of longitude at 40°N), so the basin is
     not silently stretched. The basin's own bounding box is fitted to the canvas — not the
     United States', because no coastline is drawn and nothing outside the basin exists.

  3. CENTRIPETAL Catmull-Rom (alpha = 0.5) through the projected points, converted to cubic
     beziers exactly. The output is genuine cubic bezier path data with C1 continuity by
     construction: the curve passes through every landmark, and the tangent at each landmark is
     shared by the segments either side of it.

     Centripetal, not uniform, and the difference is the whole reason this file exists. Uniform
     Catmull-Rom overshoots wherever the landmark spacing changes sharply — it put a loop in the
     Missouri's bend above Great Falls and threw a hook past the delta, because both are near
     reversals between unevenly spaced points. Centripetal parameterisation is provably cusp- and
     self-intersection-free, so the delta comes to a point instead of curling past itself.

The output is pasted into the variant HTML. Re-run after changing a landmark:

    python3 design/hero-watershed-2026/build_paths.py
"""

# ── the canvas ────────────────────────────────────────────────────────────────────────────────
VIEW_W, VIEW_H = 1200, 700
BOX = (200, 70, 1006, 660)          # where the basin's bounding box lands: x0, y0, x1, y1
LAT_OVER_LON = 1.31                 # 111 km / 85 km at 40°N — the aspect the map is held to

# ── the divide ────────────────────────────────────────────────────────────────────────────────
# Clockwise from the north-west corner of the Missouri headwaters. North and east edges follow the
# Great Lakes divide, the east follows the Appalachian crest, the west the Continental Divide.
BASIN = [
    (48.2, -113.6),   # MT, the north-west corner of the basin
    (49.0, -110.0),   # the Canadian line, Montana
    (49.0, -104.0),   # the Canadian line, North Dakota
    (48.6,  -99.0),   # ND — south of the Souris
    (47.2,  -96.6),   # MN — the divide with the Red River of the North
    (47.6,  -94.5),   # MN — above Itasca
    (47.3,  -92.0),   # MN — the Lake Superior divide
    (46.0,  -89.5),   # WI / Upper Peninsula
    (44.0,  -88.4),   # WI — the Fox / Wisconsin portage
    (42.2,  -87.9),   # IL — hard against Lake Michigan
    (41.4,  -85.5),   # IN — south of the lake
    (41.2,  -83.0),   # OH — south of Lake Erie
    (41.5,  -80.5),   # OH / PA
    (42.0,  -78.2),   # PA — the north-east tip of the Ohio basin
    (40.2,  -78.0),   # PA — the Appalachian crest turns south
    (39.0,  -79.3),   # WV
    (37.4,  -81.0),   # VA / WV
    (36.2,  -82.2),   # TN / NC
    (35.0,  -83.8),   # NC / GA
    (34.2,  -85.5),   # GA / AL
    (33.0,  -86.6),   # AL
    (31.5,  -88.0),   # AL / MS
    (30.2,  -89.5),   # the Gulf coast
    (29.1,  -89.3),   # the delta
    (30.0,  -91.5),   # LA
    (31.2,  -94.0),   # TX / LA
    (32.5,  -98.0),   # TX
    (34.5, -101.5),   # the Texas panhandle
    (35.5, -104.0),   # NM
    (36.8, -105.5),   # NM / CO — the Sangre de Cristo
    (38.8, -106.5),   # CO — the Continental Divide
    (40.5, -107.5),   # CO / WY
    (42.5, -109.5),   # WY
    (44.5, -111.5),   # MT / ID
    (46.5, -113.0),   # MT
]

# ── the rivers ────────────────────────────────────────────────────────────────────────────────
# Headwater first, confluence last. The last landmark of a tributary is the first-shared point
# with the stem, so confluences are exact rather than approximate.
CONF_ILLINOIS = (38.97, -90.60)   # Grafton
CONF_MISSOURI = (38.82, -90.12)   # above St. Louis
CONF_OHIO     = (37.00, -89.17)   # Cairo
CONF_ARKANSAS = (33.95, -91.07)   # Napoleon
BDOTE         = (44.89, -93.18)   # the Minnesota / Mississippi confluence

MISSISSIPPI = [
    (47.20, -95.20),  # Lake Itasca
    (45.60, -94.30),
    BDOTE,            # Bdóte — the Minnesota arrives
    (44.75, -92.80),  # Prescott — the St Croix arrives
    (43.80, -91.25),  # La Crosse
    (43.05, -91.14),  # Prairie du Chien — the Wisconsin arrives
    (42.50, -90.66),  # Dubuque
    (41.50, -90.57),  # Rock Island — the Rock and the Iowa arrive
    (40.40, -91.38),  # Quincy
    CONF_ILLINOIS,
    CONF_MISSOURI,
    (37.95, -89.85),  # Chester
    CONF_OHIO,
    (35.15, -90.05),  # Memphis
    CONF_ARKANSAS,
    (32.35, -90.88),  # Vicksburg
    (31.10, -91.60),  # below Natchez
    (30.45, -91.19),  # Baton Rouge
    (29.95, -90.07),  # New Orleans
    (29.15, -89.25),  # the delta
]

MISSOURI = [
    (45.95, -111.55),  # Three Forks
    (47.20, -111.20),  # Great Falls
    (47.95, -107.50),  # the Fort Peck reach — carries the northward hook into an arc
    (48.00, -103.80),  # Williston
    (46.85, -100.85),  # Bismarck
    (44.37, -100.35),  # Pierre
    (42.85,  -97.35),  # Yankton
    (41.26,  -95.93),  # Omaha
    (39.10,  -94.60),  # Kansas City
    (38.58,  -92.17),  # Jefferson City
    CONF_MISSOURI,
]

OHIO = [
    (40.44, -80.00),  # Pittsburgh
    (40.06, -80.72),  # Wheeling
    (38.85, -82.13),  # Point Pleasant — the Kanawha arrives
    (39.10, -84.50),  # Cincinnati
    (38.25, -85.76),  # Louisville
    (37.97, -87.57),  # Evansville
    (37.08, -88.60),  # Paducah
    CONF_OHIO,
]

ARKANSAS = [
    (38.44, -106.30),  # the Sawatch headwaters
    (38.27, -104.60),  # Pueblo
    (37.75, -100.02),  # Dodge City
    (37.69,  -97.34),  # Wichita
    (36.15,  -95.99),  # Tulsa
    (35.39,  -94.40),  # Fort Smith
    (34.75,  -92.29),  # Little Rock
    CONF_ARKANSAS,
]

ILLINOIS = [
    (41.70, -88.10),  # the Chicago portage
    (41.35, -88.84),  # Ottawa
    (40.69, -89.59),  # Peoria
    (40.00, -90.42),  # Beardstown
    CONF_ILLINOIS,
]

MINNESOTA = [
    (45.30, -96.45),  # Big Stone Lake
    (44.55, -95.60),  # Granite Falls
    (44.16, -94.00),  # Mankato — the great bend
    (44.55, -93.70),  # Belle Plaine
    (44.79, -93.52),  # Shakopee
    BDOTE,
]
# ── the outer tier ────────────────────────────────────────────────────────────────────────────
# The capillaries. These exist because the drawing has three tiers, not two: the hover hierarchy
# resolves outer → mid → stem, and a network with nothing outside its four majors has no outer to
# resolve away. Each ends on a landmark its parent already owns, so every junction is exact rather
# than nearly — a capillary that stops two units short of its river is the one thing at this
# weight the eye does catch.
OUTER = {
    "YELLOWSTONE": [(44.50, -110.40), (45.60, -108.55), (46.40, -105.85), (47.60, -104.20),
                    (48.00, -103.80)],                                    # → Missouri, Williston
    "PLATTE":      [(41.10, -102.90), (40.70, -99.10), (41.00, -96.90), (41.26, -95.93)],
    "KANSAS":      [(39.05, -97.65), (39.07, -95.70), (39.10, -94.60)],   # → Missouri, KC
    "WISCONSIN":   [(45.80, -89.60), (44.30, -89.75), (43.35, -89.90), (43.05, -91.14)],
    "DES_MOINES":  [(43.30, -95.15), (42.10, -94.20), (41.30, -93.10), (40.40, -91.38)],
    "TENNESSEE":   [(35.95, -84.00), (35.05, -85.30), (34.75, -87.65), (36.00, -88.10),
                    (37.08, -88.60)],                                     # → Ohio, Paducah
    "CUMBERLAND":  [(36.85, -84.20), (36.16, -86.78), (36.60, -87.85), (37.08, -88.60)],
    "WABASH":      [(40.75, -85.15), (40.42, -86.90), (38.68, -87.75), (37.97, -87.57)],
    "CANADIAN":    [(35.55, -104.30), (35.45, -99.40), (35.35, -96.30), (35.39, -94.40)],
    "RED":         [(34.90, -100.30), (33.75, -96.60), (33.10, -93.90), (31.85, -92.60),
                    (31.10, -91.60)],                                     # → Mississippi
    "MILK":        [(48.90, -112.00), (48.75, -109.70), (48.40, -107.90), (47.95, -107.50)],
    "NIOBRARA":    [(42.80, -104.00), (42.85, -100.60), (42.75, -98.60), (42.85, -97.35)],
    "JAMES":       [(46.90, -98.55), (45.40, -98.45), (43.90, -98.05), (42.85, -97.35)],
    "OSAGE":       [(37.85, -94.40), (38.05, -93.30), (38.35, -92.60), (38.58, -92.17)],
    "ST_CROIX":    [(46.30, -92.45), (45.55, -92.70), (45.05, -92.75), (44.75, -92.80)],
    "ROCK":        [(43.55, -89.00), (42.55, -89.35), (41.80, -90.15), (41.50, -90.57)],
    "IOWA_CEDAR":  [(43.20, -93.40), (42.30, -92.30), (41.65, -91.53), (41.50, -90.57)],
    "KANAWHA":     [(37.75, -81.15), (38.05, -81.10), (38.35, -81.63), (38.85, -82.13)],
    "GREEN":       [(37.15, -85.35), (37.20, -86.45), (37.65, -87.30), (37.97, -87.57)],
    "WHITE":       [(36.30, -92.95), (35.55, -91.90), (34.70, -91.35), (33.95, -91.07)],
    "YAZOO":       [(34.00, -90.35), (33.20, -90.45), (32.70, -90.65), (32.35, -90.88)],
    "CIMARRON":    [(36.90, -102.60), (36.85, -99.40), (36.45, -97.30), (36.15, -95.99)],
    "OUACHITA":    [(34.55, -93.55), (33.60, -92.10), (32.50, -92.10), (31.85, -92.60)],
}

# Generated, and used as an outer capillary in Variant I. Bdóte itself — the Minnesota meeting the
# Mississippi — is where Variant II started, and at hero scale it fails: the whole Minnesota is
# ~110px long and its great bend at Mankato reads as a kink rather than a meander, in the one
# variant whose entire subject is two legible waters. Variant II therefore draws the Bdóte FIGURE
# (two waters arriving, one leaving, one node) at the basin's own great confluence above St Louis,
# where both arms are long enough to be read. Kept here because the decision is worth being able
# to revisit, and because a longer-form application — a folio spread, a print — could carry it.

# Variant II's two arms and its single channel. Split at the Missouri's mouth; each side is
# splined independently, so each gets its own natural tangent at the junction.
_M_SPLIT = MISSISSIPPI.index(CONF_MISSOURI)
UPPER_MISSISSIPPI = MISSISSIPPI[:_M_SPLIT + 1]
LOWER_MISSISSIPPI = MISSISSIPPI[_M_SPLIT:]


# ── projection ────────────────────────────────────────────────────────────────────────────────

def _fit():
    """Solve one scale and offset that lands the basin's bbox inside BOX at the true aspect."""
    lats = [p[0] for p in BASIN]
    lons = [p[1] for p in BASIN]
    lon0, lon1, lat0, lat1 = min(lons), max(lons), min(lats), max(lats)
    x0, y0, x1, y1 = BOX
    s = min((x1 - x0) / (lon1 - lon0), (y1 - y0) / ((lat1 - lat0) * LAT_OVER_LON))
    w, h = (lon1 - lon0) * s, (lat1 - lat0) * s * LAT_OVER_LON
    return s, x0 + ((x1 - x0) - w) / 2 - lon0 * s, y0 + ((y1 - y0) - h) / 2 + lat1 * s * LAT_OVER_LON


_S, _XO, _YO = _fit()


def project(pt):
    lat, lon = pt
    return (lon * _S + _XO, _YO - lat * _S * LAT_OVER_LON)


# ── Catmull-Rom → cubic bezier ────────────────────────────────────────────────────────────────

def _f(v):
    """Trim to one decimal, and drop the decimal when it is zero — shorter path data reads better."""
    r = round(v, 1)
    return str(int(r)) if r == int(r) else str(r)


ALPHA = 0.5   # 0 = uniform, 0.5 = centripetal, 1 = chordal


def _knot(a, b):
    return (((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5) ** ALPHA


def spline(points, closed=False, projected=False):
    """Centripetal Catmull-Rom through `points`, emitted as exact cubic beziers.

    `projected=True` takes canvas coordinates directly — used by Variant III's channel, which is
    constructed on the canvas rather than derived from geography.
    """
    p = list(points) if projected else [project(q) for q in points]
    n = len(p)
    if closed:
        ext = [p[-1]] + p + [p[0], p[1]]
    else:
        # Reflect the ends rather than duplicating them: a duplicated endpoint has zero knot
        # spacing, which the centripetal weights divide by.
        ext = [(2 * p[0][0] - p[1][0], 2 * p[0][1] - p[1][1])] + p + \
              [(2 * p[-1][0] - p[-2][0], 2 * p[-1][1] - p[-2][1])]
    d = [f"M {_f(p[0][0])} {_f(p[0][1])}"]
    for i in range(n if closed else n - 1):
        p0, p1, p2, p3 = ext[i], ext[i + 1], ext[i + 2], ext[i + 3]
        t1, t2, t3 = _knot(p0, p1), _knot(p1, p2), _knot(p2, p3)
        if t1 == 0 or t2 == 0 or t3 == 0:            # coincident landmarks: fall back to a line
            c1, c2 = p1, p2
        else:
            c1 = tuple((t1 * t1 * p2[k] - t2 * t2 * p0[k]
                        + (2 * t1 * t1 + 3 * t1 * t2 + t2 * t2) * p1[k]) / (3 * t1 * (t1 + t2))
                       for k in (0, 1))
            c2 = tuple((t3 * t3 * p1[k] - t2 * t2 * p3[k]
                        + (2 * t3 * t3 + 3 * t3 * t2 + t2 * t2) * p2[k]) / (3 * t3 * (t3 + t2))
                       for k in (0, 1))
        d.append(f"C {_f(c1[0])} {_f(c1[1])} {_f(c2[0])} {_f(c2[1])} {_f(p2[0])} {_f(p2[1])}")
    return " ".join(d) + (" Z" if closed else "")


def wrap(d, width=104, indent=" " * 14):
    out, line = [], ""
    for tok in d.split(" C "):
        piece = tok if not out and not line else "C " + tok
        if line and len(line) + len(piece) + 1 > width:
            out.append(line)
            line = piece
        else:
            line = (line + " " + piece).strip()
    out.append(line)
    return ("\n" + indent).join(out)


# ── Variant III: five congruent tributaries on the real channel ───────────────────────────────
# The five are ONE curve, in a local frame measured from the join: u runs back upstream, v runs
# sideways. It is placed five times, at five equal arc-length intervals along the drawn channel,
# each time rotated into that point's tangent frame and mirrored on alternating sides. So all five
# are congruent — same length, same curvature, same 34.5° approach to the channel — while the
# channel they lock into stays the real river. That is the balance the variant claims: the
# tributaries are identical and evenly spaced *along the channel*, which is the only spacing that
# means anything on a curve.
#            u = upstream reach          v = lateral reach
# Lateral 190 against upstream 84: a tributary has to arrive ACROSS the channel to read as an
# arrival. The first version of this template reached further upstream than sideways and the five
# came out running alongside the river instead of into it.
TEMPLATE = [(84, 190), (66, 150), (56, 112), (46, 76), (36, 40), (24, 18), (0, 0)]
#           start       ── first cubic ──        mid       ── second cubic ──       the join
# The mid point's incoming and outgoing controls are exact reflections ((56,112) about (46,76)
# gives (36,40)), so the template is C1-continuous before it is placed anywhere.

SIDES = [+1, -1, +1, -1, +1]          # alternating banks, starting west

# THE CHANNEL IS CONSTRUCTED, NOT GEOGRAPHIC — the one place these three variants part company.
# Hanging the five congruent tributaries on the real Mississippi was tried and abandoned: the real
# channel turns hard between the Illinois and the Arkansas, and rotating the template into those
# swinging tangent frames threw the west-bank arrivals across one another. A figure whose claim is
# perfect balance cannot be built on a curve that keeps changing its mind.
#
# So Variant III descends a channel of its own — near-straight, drifting steadily east because
# every join adds from a different side — pinned at both ends to the real drawing: it begins at
# Itasca's projected position and ends at the projected delta, inside the real silhouette. The
# five nodes sit 60 units apart in y, in the basin's wide belly, which is the only band where five
# arrivals of equal reach all have room to exist inside the watershed.
CHANNEL_XY = [
    (617, 123),   # Itasca, as projected
    (632, 230),
    (648, 334),   # node 1
    (662, 394),   # node 2
    (676, 454),   # node 3
    (692, 514),   # node 4
    (708, 574),   # node 5
    (722, 620),   # holds node 5's tangent in line with the other four before the delta turn
    (751, 658),   # the delta, as projected
]
NODES_XY = CHANNEL_XY[2:7]
SYSTEMS = ["INVESTMENTS", "TAXES", "LIQUIDITY", "ESTATE", "RISK & LIABILITY"]


def _flatten(d, steps=60):
    """Walk a cubic path string into a dense polyline plus cumulative arc length."""
    tok = d.replace("M", " ").replace("C", " ").replace("Z", " ").split()
    nums = [float(t) for t in tok]
    pts = [(nums[0], nums[1])]
    poly = [pts[0]]
    i = 2
    while i + 5 < len(nums) + 1 and i + 5 <= len(nums):
        p0 = poly[-1]
        c1, c2, p3 = (nums[i], nums[i + 1]), (nums[i + 2], nums[i + 3]), (nums[i + 4], nums[i + 5])
        for k in range(1, steps + 1):
            t = k / steps
            m = 1 - t
            poly.append((m ** 3 * p0[0] + 3 * m * m * t * c1[0] + 3 * m * t * t * c2[0] + t ** 3 * p3[0],
                         m ** 3 * p0[1] + 3 * m * m * t * c1[1] + 3 * m * t * t * c2[1] + t ** 3 * p3[1]))
        i += 6
    cum = [0.0]
    for a, b in zip(poly, poly[1:]):
        cum.append(cum[-1] + ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5)
    return poly, cum


def frame_at(d, f):
    """Point and unit downstream tangent at arc-length fraction `f` of path `d`."""
    poly, cum = _flatten(d)
    target = cum[-1] * f
    i = max(1, min(range(1, len(cum)), key=lambda k: abs(cum[k] - target)))
    p = poly[i]
    a, b = poly[max(0, i - 3)], poly[min(len(poly) - 1, i + 3)]
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = (dx * dx + dy * dy) ** 0.5
    return p, (dx / n, dy / n), cum[-1]


def tributary(point, tangent, side, scale=1.0):
    """Place TEMPLATE in the tangent frame at `point`, mirrored onto `side`, at `scale`."""
    (px, py), (tx, ty) = point, tangent
    out = []
    for u, v in TEMPLATE:
        u, v = u * scale, v * scale
        out.append((px - u * tx + v * side * -ty, py - u * ty + v * side * tx))
    return ("M {} {} C {} {} {} {} {} {} C {} {} {} {} {} {}"
            .format(*[_f(c) for pt in out for c in pt]))


def frame_on(d, f):
    """Point and unit tangent at arc-length fraction `f` of an arbitrary path string."""
    poly, cum = _flatten(d)
    target = cum[-1] * f
    i = max(1, min(range(1, len(cum)), key=lambda k: abs(cum[k] - target)))
    a, b = poly[max(0, i - 3)], poly[min(len(poly) - 1, i + 3)]
    n = ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
    return poly[i], ((b[0] - a[0]) / n, (b[1] - a[1]) / n)


FEEDER_SCALE = 0.5   # each of Variant III's five carries one feeder, the same curve at half size


# ── emitting the SVG bodies ───────────────────────────────────────────────────────────────────
# The variants carry their geometry inline — they have to be self-contained — but nobody should be
# hand-copying thirty `d` attributes between a generator and three files. So the generator writes
# them, between the GEOM:BEGIN / GEOM:END markers, and the committed HTML is the finished article
# either way. Nothing outside those markers is touched, so the prose above them is safe to edit.
#
# TIMING IS EMITTED WITH THE GEOMETRY, for the same reason. The draw is one 12s linear loop:
# stroke-dasharray "1 1" over pathLength 1, stroke-dashoffset 2 → 0. At offset o the drawn portion
# is [0, 1-o], so a point at fraction f of a vector is reached at t = 6 + 6f seconds, and the
# cycle closes seamlessly — the line erases from its head and redraws from its head, with no snap
# at the loop point. Each confluence therefore knows, arithmetically, when the water gets to it;
# every node below carries its own --d, measured, not guessed.
CYCLE = 12.0
TRACE_DASH = 0.16      # the lit segment, as a fraction of any vector's length


def trace_time(f, phase=0.0):
    """When the travelling front is at fraction `f` of a vector carrying `phase`."""
    return (CYCLE * (f - TRACE_DASH) + phase) % CYCLE


# Phase leads. Negative delays ADVANCE a vector in the cycle rather than postponing it, so nothing
# waits for its first turn and the wave is already in motion at t=0.
PHASE = {"outer": -2.4, "mid": -1.2, "stem": 0.0}          # variants I and II
MID_STAGGER = [-1.8, -1.5, -1.2, -0.9]                     # variant I: the four majors, in order
IND = " " * 6


def _grp(cls, d, phase, node=None, hover_r=16, comment=None, mask="", node_t=None):
    """A mid-tier vector: proximity zone, the line, its glow, and a confluence that only exists
    while it is firing."""
    out = []
    if comment:
        out.append(f'{IND}<!-- {comment} -->')
    out.append(f'{IND}<g class="trib {cls}">')
    out.append(f'{IND}  <path class="hit" d="{d}"/>')
    out.append(f'{IND}  <path class="flow"{mask} pathLength="1" d="{d}"/>')
    out.append(f'{IND}  <path class="trace"{mask} pathLength="1" style="--t:{phase:.2f}s" d="{d}"/>')
    out.append(f'{IND}  <path class="glow"{mask} pathLength="1" d="{d}"/>')
    if node:
        out.append(f'{IND}  <circle class="node node--hover" cx="{_f(node[0])}" '
                   f'cy="{_f(node[1])}" r="{hover_r}"/>')
    out.append(f'{IND}</g>')
    return "\n".join(out)


def _basin():
    return (f'{IND}<!-- THE FIELD — the divide, as 35 landmarks: the Continental Divide down the\n'
            f'{IND}     west, the Great Lakes divide across the north and east, the Appalachian\n'
            f'{IND}     crest down to the Gulf. Fill only; an outline here would be a border. -->\n'
            f'{IND}<g class="basin">\n{IND}  <path class="basin-fill" d="'
            + wrap(spline(BASIN, True), 96, IND + "    ") + '"/>\n' + IND + '</g>')


def _node_delay(stem_d, point, phase):
    """When the drawing front reaches `point` on `stem_d`, in this cycle's clock."""
    poly, cum = _flatten(stem_d)
    j = min(range(len(poly)), key=lambda k: (poly[k][0] - point[0]) ** 2 + (poly[k][1] - point[1]) ** 2)
    f = cum[j] / cum[-1]
    return f, 6.0 + 6.0 * f + phase


def emit_v1():
    stem_d = spline(MISSISSIPPI)
    out = [_basin(), "",
           f'{IND}<!-- THE OUTER TIER — the capillaries. Line only: no proximity zone and no glow,',
           f'{IND}     because a hairline this fine is not something anyone aims at, and the hover',
           f'{IND}     hierarchy resolves it away rather than toward. -->',
           f'{IND}<g class="outer">']
    for name, pts in list(OUTER.items()) + [("MINNESOTA", MINNESOTA)]:
        d = spline(pts)
        out.append(f'{IND}  <path class="flow" pathLength="1" d="{d}"/>'
                   f'  <!-- {name.replace("_", " ").title()} -->')
        out.append(f'{IND}  <path class="trace" pathLength="1" '
                   f'style="--t:{PHASE["outer"]:.2f}s" d="{d}"/>')
    out.append(f'{IND}</g>')
    out.append("")
    out.append(f'{IND}<!-- THE FOUR MAJORS, north to south. Each ends on a landmark the stem itself')
    out.append(f'{IND}     owns, so every junction is exact rather than nearly. -->')
    mids = [("t-illinois", ILLINOIS, CONF_ILLINOIS, 15, "ILLINOIS — the Chicago portage to Grafton"),
            ("t-missouri", MISSOURI, CONF_MISSOURI, 18, "MISSOURI — Three Forks to St Louis, the long north-west arm"),
            ("t-ohio", OHIO, CONF_OHIO, 18, "OHIO — Pittsburgh to Cairo, the largest addition of volume"),
            ("t-arkansas", ARKANSAS, CONF_ARKANSAS, 17, "ARKANSAS — the Sawatch headwaters to Napoleon")]
    for (cls, pts, conf, r, note), ph in zip(mids, MID_STAGGER):
        out.append(_grp(cls, spline(pts), ph, project(conf), r, note))
    out.append("")
    out.append(f'{IND}<!-- THE STEM — Itasca to the delta, through all four junctions. The only')
    out.append(f'{IND}     vector illuminated at rest, and the only one that breathes. -->')
    out.append(f'{IND}<g class="stemwrap">\n{IND}  <path class="hit" d="{stem_d}"/>\n'
               f'{IND}  <path class="stem" pathLength="1" d="'
               + wrap(stem_d, 96, IND + "      ") + f'"/>\n'
               f'{IND}  <path class="trace trace--stem" pathLength="1" style="--t:0s" d="{stem_d}"/>'
               f'\n{IND}</g>')
    out.append("")
    out.append(f'{IND}<!-- The confluences. Each fires as its own tributary lands; --d is measured')
    out.append(f'{IND}     off the drawn geometry, not chosen. -->')
    for (cls, _pts, conf, r, _n), ph in zip(mids, MID_STAGGER):
        pt = project(conf)
        out.append(f'{IND}<circle class="node node--load" style="--d:{trace_time(1.0, ph):.2f}s" '
                   f'cx="{_f(pt[0])}" cy="{_f(pt[1])}" r="{r}"/>  <!-- {cls[2:]} -->')
    return "\n".join(out), None


def emit_v2():
    out = [_basin(), "",
           f'{IND}<!-- THE TWO WATERS — the upper Mississippi from Itasca, the Missouri from Three',
           f'{IND}     Forks, arriving from opposite quarters of the basin. -->',
           _grp("t-upper", spline(UPPER_MISSISSIPPI), PHASE["mid"], project(CONF_MISSOURI), 21,
                "THE FIRST WATER — the upper Mississippi"),
           _grp("t-missouri", spline(MISSOURI), PHASE["mid"], project(CONF_MISSOURI), 21,
                "THE SECOND WATER — the Missouri"),
           "",
           f'{IND}<!-- WHAT LEAVES. Drawn last in the cycle because it does not exist until the two',
           f'{IND}     arrive; the only illuminated vector, and the only one that breathes. -->',
           f'{IND}<g class="stemwrap">\n{IND}  <path class="hit" d="{spline(LOWER_MISSISSIPPI)}"/>\n'
           f'{IND}  <path class="stem" pathLength="1" d="'
           + wrap(spline(LOWER_MISSISSIPPI), 96, IND + "      ") + f'"/>\n'
           f'{IND}  <path class="trace trace--stem" pathLength="1" style="--t:0s" '
           f'd="{spline(LOWER_MISSISSIPPI)}"/>\n{IND}</g>',
           "",
           f'{IND}<!-- The confluence: one pulse, at the moment both arms have finished and the',
           f'{IND}     channel begins. Nothing is left behind. -->']
    p = project(CONF_MISSOURI)
    out.append(f'{IND}<circle class="node node--load" '
               f'style="--d:{trace_time(1.0, PHASE["mid"]):.2f}s" '
               f'cx="{_f(p[0])}" cy="{_f(p[1])}" r="21"/>')
    return "\n".join(out)


def emit_v3():
    channel = spline(CHANNEL_XY, projected=True)
    poly, cum = _flatten(channel)

    # Where each node sits along the channel, and therefore when the channel's own front reaches
    # it. Because the five nodes are equally spaced along the channel by construction and the
    # front moves at constant velocity, these five times come out equally spaced on their own —
    # the sequence is the geometry's, not a set of numbers chosen to look even.
    node_f, node_t = [], []
    for node in NODES_XY:
        j = min(range(len(poly)), key=lambda k: (poly[k][0] - node[0]) ** 2 + (poly[k][1] - node[1]) ** 2)
        node_f.append(cum[j] / cum[-1])
        node_t.append(trace_time(cum[j] / cum[-1], 0.0))

    # Each arrival is phased so its front lands at its join exactly as the channel's front arrives
    # there; each feeder leads its own parent by 1.2s. Nothing here is a chosen delay — every value
    # is derived from where the node fell on the channel.
    trib_phase = [(t - trace_time(1.0, 0.0)) % CYCLE - CYCLE for t in node_t]
    feeder_phase = [ph - 1.2 for ph in trib_phase]

    trib_ds, feeders = [], []
    for node, side in zip(NODES_XY, SIDES):
        j = min(range(len(poly)), key=lambda k: (poly[k][0] - node[0]) ** 2 + (poly[k][1] - node[1]) ** 2)
        a, b = poly[max(0, j - 4)], poly[min(len(poly) - 1, j + 4)]
        n = ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
        tan = ((b[0] - a[0]) / n, (b[1] - a[1]) / n)
        d = tributary(node, tan, side)
        trib_ds.append(d)
        fp, ft = frame_on(d, 0.5)
        feeders.append(tributary(fp, ft, side, FEEDER_SCALE))

    out = [_basin(), "",
           f'{IND}<!-- THE OUTER TIER — one feeder per arrival, the same template at half size,',
           f'{IND}     placed halfway along its parent in its parent\'s own frame. Congruent among',
           f'{IND}     themselves, exactly as the five are congruent among themselves. -->',
           f'{IND}<g class="outer">']
    for i, d in enumerate(feeders, start=1):
        out.append(f'{IND}  <path class="flow" mask="url(#field)" pathLength="1" d="{d}"/>'
                   f'  <!-- feeds {i} -->')
        out.append(f'{IND}  <path class="trace" mask="url(#field)" pathLength="1" '
                   f'style="--t:{feeder_phase[i - 1]:.2f}s" d="{d}"/>')
    out.append(f'{IND}</g>')
    out.append("")
    out.append(f'{IND}<!-- ── THE FIVE. One template, five placements; node coordinates lie on the')
    out.append(f'{IND}     channel by construction. Names are structural only — nothing renders a')
    out.append(f'{IND}     word, here or anywhere on the plate. ── -->')
    for i, (d, node, sysname, side, ph) in enumerate(
            zip(trib_ds, NODES_XY, SYSTEMS, SIDES, trib_phase), start=1):
        out.append(_grp(f"t-{i}", d, ph, node, 16,
                        f"{i} · {sysname} — {'west' if side > 0 else 'east'} bank",
                        mask=' mask="url(#field)"'))
    out.append("")
    out.append(f'{IND}<!-- THE CHANNEL. Itasca to the delta, through all five nodes, drifting east')
    out.append(f'{IND}     as it descends because each join adds from a different side. -->')
    out.append(f'{IND}<g class="stemwrap">\n{IND}  <path class="hit" d="{channel}"/>\n'
               f'{IND}  <path class="stem" pathLength="1" d="'
               + wrap(channel, 96, IND + "      ") + f'"/>\n'
               f'{IND}  <path class="trace trace--stem" pathLength="1" style="--t:0s" d="{channel}"/>'
               f'\n{IND}</g>')
    out.append("")
    out.append(f'{IND}<!-- The five confluences, fired in order as the channel\'s front reaches each.')
    out.append(f'{IND}     Every --d below is measured off the drawn channel. -->')
    for i, (node, t, f) in enumerate(zip(NODES_XY, node_t, node_f), start=1):
        out.append(f'{IND}<circle class="node node--load" style="--d:{t:.2f}s" '
                   f'cx="{node[0]}" cy="{node[1]}" r="16"/>  <!-- {i} · f={f:.3f} -->')
    return "\n".join(out), node_t


MARK_OPEN, MARK_CLOSE = "<!--GEOM:BEGIN-->", "<!--GEOM:END-->"


def inject():
    import re as _re
    v1 = emit_v1()[0]
    bodies = {"variant-1-basin.html": v1,
              "variant-2-bdote.html": emit_v2(),
              "variant-3-panch-prayag.html": emit_v3()[0],
              "hero-watershed.html": v1}
    here = __import__("pathlib").Path(__file__).resolve().parent
    # The live homepage takes the same emitted geometry as the prototype it came from, from the
    # same run — so the two can never quietly drift apart.
    bodies[str(here.parents[1] / "src" / "drift" / "web" / "hub.html")] = bodies["hero-watershed.html"]
    for name, body in bodies.items():
        p = __import__("pathlib").Path(name) if "/" in name else here / name
        html = p.read_text(encoding="utf-8")
        pat = _re.compile(_re.escape(MARK_OPEN) + r".*?" + _re.escape(MARK_CLOSE), _re.DOTALL)
        if not pat.search(html):
            print(f"!! {name}: no <!--GEOM--> markers")
            return 1
        html = pat.sub(lambda _m: MARK_OPEN + "\n" + body + "\n" + IND + MARK_CLOSE, html)
        html = html.replace("__BASIN__", spline(BASIN, True))
        p.write_text(html, encoding="utf-8")
        print(f"   injected geometry -> {name}")
    return 0


if __name__ == "__main__":
    import sys as _sys
    if "--inject" in _sys.argv:
        raise SystemExit(inject())
    print(f"# projection: scale={_S:.4f} px/deg-lon, aspect={LAT_OVER_LON}, viewBox 0 0 {VIEW_W} {VIEW_H}\n")
    for name, pts, closed in [
        ("BASIN", BASIN, True),
        ("MISSISSIPPI", MISSISSIPPI, False),
        ("MISSOURI", MISSOURI, False),
        ("OHIO", OHIO, False),
        ("ARKANSAS", ARKANSAS, False),
        ("ILLINOIS", ILLINOIS, False),
    ]:
        print(f"── {name} " + "─" * (60 - len(name)))
        print(wrap(spline(pts, closed)))
        print()

    print("── OUTER TIER " + "─" * 57)
    for name, pts in list(OUTER.items()) + [("MINNESOTA", MINNESOTA)]:
        print(f"   {name}")
        print("     " + wrap(spline(pts), indent=" " * 5))
    print()
    for name, pts in [("UPPER_MISSISSIPPI (variant II arm)", UPPER_MISSISSIPPI),
                      ("LOWER_MISSISSIPPI (variant II channel)", LOWER_MISSISSIPPI)]:
        print(f"── {name} " + "─" * max(2, 60 - len(name)))
        print(wrap(spline(pts)))
        print()

    print("── confluence coordinates " + "─" * 45)
    for label, pt in [("illinois", CONF_ILLINOIS), ("missouri", CONF_MISSOURI),
                      ("ohio", CONF_OHIO), ("arkansas", CONF_ARKANSAS), ("bdote", BDOTE)]:
        x, y = project(pt)
        print(f"   {label:<10} cx=\"{_f(x)}\" cy=\"{_f(y)}\"")

    print("\n── VARIANT III: the constructed channel " + "─" * 32)
    channel = spline(CHANNEL_XY, projected=True)
    print(wrap(channel))
    print("\n── VARIANT III: five congruent tributaries " + "─" * 29)
    poly, cum = _flatten(channel)
    for i, (node, s, sysname) in enumerate(zip(NODES_XY, SIDES, SYSTEMS), start=1):
        # tangent from the channel polyline at the vertex nearest this node
        j = min(range(len(poly)), key=lambda k: (poly[k][0] - node[0]) ** 2 + (poly[k][1] - node[1]) ** 2)
        a, b = poly[max(0, j - 4)], poly[min(len(poly) - 1, j + 4)]
        n = ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
        tan = ((b[0] - a[0]) / n, (b[1] - a[1]) / n)
        print(f"   {i} · {sysname:<17} node cx=\"{node[0]}\" cy=\"{node[1]}\"  "
              f"{'west' if s > 0 else 'east'}  tangent {tan[0]:+.3f},{tan[1]:+.3f}")
        trib = tributary(node, tan, s)
        print(f"       mid   {trib}")
        fp, ft = frame_on(trib, 0.5)
        print(f"       outer {tributary(fp, ft, s, FEEDER_SCALE)}")
