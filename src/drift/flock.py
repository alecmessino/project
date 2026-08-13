"""The hero flock — a distant scatter of birds, generated, for the ``?hero=flock`` control arm.

WHAT THIS IS, AND WHAT IT IS EMPHATICALLY NOT. This is **not** a house mark and must never become
one. The house mark is a single great blue heron, *Standing, Alert* (:mod:`drift.heron`), and its
whole instrument is scarcity: one bird, one master, reserved for enduring statements, currently on
no web page at all. The flock is the opposite object by construction — many birds, none of them
individually legible, none of them a heron, carrying no identity and no argument. It is
**atmosphere**, and it is here to be judged as atmosphere.

That distinction is load-bearing, so it is enforced rather than asserted: see
``tests/test_drift_flock.py``, which holds the flock to being plural and small. The failure mode
is not that someone draws a bad bird — it is that one bird slowly gets bigger and better placed
until the page has grown a second mark and the heron's rarity has been spent by a file that never
claimed to be a mark at all.

WHY GENERATED RATHER THAN SHIPPED AS FOOTAGE. The source was 45s of gulls over a flat sky. Shipped
as video that is ~400 KB, an autoplay policy, a poster frame and a reduced-motion branch, spent on
birds that occupy 0.57% of the frame and land at 5–10px in this slot — you cannot see what you
paid for. Traced and regenerated it is ~20 KB of vector, scales without artefacts, needs no
network branch, and is drawn in the site's own ink rather than photographed in someone else's
light. The site already works this way: `heron.py` and the hero watershed are both drawings the
repo generates, not assets it licenses.

THE POSES ARE REAL. :data:`_POSES` are eight silhouettes traced out of the footage frame by frame
(threshold, connected components, Moore boundary walk, Douglas-Peucker), normalised to unit
wingspan about their own centre. They are not drawn from imagination and not clip art, which is
the only reason the flock reads as birds at eight pixels — the wing sweep is a real wing's.
Composition, depth, heading and timing are generated here; the shapes are observed.

DEPTH IS THE ONLY HIERARCHY, AND IT BORROWS THE WATERSHED'S. Four tiers, and the same pairing the
watershed plate uses: nearer is both larger and darker (palette #5d7e96 → #2c5878). One flat ink
at one size reads as a field of specks; tying weight to depth of colour is what makes it read as
air with distance in it. The rhyme with the watershed is deliberate — if this ever shares a page
with that plate it should look like the same weather.

PURE MODULE (see CLAUDE.md): no I/O, no filesystem, no clock, no global RNG. :class:`_Seq` is the
same local LCG `heron.py` and the plate library use, so the asset is byte-identical on every
machine and every Python build — a generator that drifted would rewrite the file in every diff.

Write it with ``python3 scripts/build_flock.py``.
"""
from __future__ import annotations

import math

# The hero's right-hand void, in the watershed's own viewBox units, so the control arm can swap
# one plate for the other without touching a single positioning rule.
W, H = 680.0, 626.0

# The watershed's four tiers, near to far reversed: t1 is the most distant bird and the palest,
# t4 the nearest and the darkest. Same ramp, same reason — bigger is darker.
TIERS = ("#5d7e96", "#486e8a", "#386280", "#2c5878")

# Wingspan in viewBox units per tier. The footage's median bird was 14px across a 960px frame
# (1.46% of the width); at 680 units that is ~10, which is where the middle tiers sit. Nothing
# here is allowed to grow into a subject — see FLOCK_MAX_SPAN and the test that guards it.
_SPANS = ((7.0, 11.0), (10.0, 15.0), (13.5, 20.0), (17.0, 26.0))

# The hard ceiling on any one bird, as a fraction of the plate width. This is the governance
# number, not a taste number: above it a bird stops being weather and starts being a subject, and
# a subject in this slot is a second house mark by another name.
FLOCK_MAX_SPAN = 0.055

# Default population. Plural by a wide margin — the flock's entire meaning is that no individual
# in it is the point.
FLOCK_COUNT = 38
FLOCK_MIN_COUNT = 12


class _Seq:
    """A local linear-congruential sequence.

    Deliberately not `random`, for the same reason the house mark does not use it: the output is a
    committed static asset, and seeding the stdlib generator would leave it hostage to a future
    change in CPython's algorithm.
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
# the traced pose library
# ---------------------------------------------------------------------------------------------
# Eight silhouettes lifted from the footage, normalised to unit wingspan about their own centre.
# Wing positions vary from a full glide (flat) to a deep downstroke; nothing in the library is
# thrashing, because a flock of frantic birds is a different photograph and a different mood.
# Rejected during tracing: anything deeper than 1.15× its span (a merged pair, or a bird banking
# hard enough to read as a blot rather than a bird).

_POSES = (
    ((+0.5000, -0.1300), (+0.4700, -0.1100), (+0.2100, -0.1000), (+0.1200, -0.0600),
     (+0.1000, -0.0200), (+0.1900, +0.0100), (+0.1900, +0.0300), (+0.1600, +0.0500),
     (+0.0400, +0.0600), (-0.0700, +0.0000), (-0.1400, +0.0000), (-0.4100, +0.1400),
     (-0.4800, +0.1700), (-0.5000, +0.1600), (-0.3800, +0.0300), (-0.3000, -0.0300),
     (-0.2400, -0.0500), (+0.0100, -0.0900), (+0.1800, -0.1700)),
    ((+0.5000, -0.4554), (+0.4821, -0.3482), (+0.1964, +0.0982), (+0.2143, +0.1518),
     (+0.3929, +0.1518), (+0.3393, +0.2589), (+0.2500, +0.2946), (-0.0179, +0.2589),
     (-0.4464, +0.4554), (-0.5000, +0.4375), (-0.5000, +0.4018), (-0.3571, +0.2768),
     (-0.2679, +0.2411), (-0.1786, +0.1161), (-0.0179, +0.0804), (+0.1250, -0.1518)),
    ((+0.4815, -0.1759), (+0.5000, -0.1389), (+0.3704, -0.1944), (-0.0556, -0.1759),
     (-0.1296, -0.1389), (-0.2407, -0.0093), (-0.4444, +0.3611), (-0.4815, +0.3796),
     (-0.5000, +0.3426), (-0.4259, -0.0833), (-0.3519, -0.1944), (-0.2407, -0.2500),
     (-0.3148, -0.2870), (-0.2778, -0.3426), (+0.1481, -0.3796)),
    ((+0.5000, -0.5222), (+0.2778, -0.1222), (+0.1889, -0.0333), (+0.2333, +0.0111),
     (+0.4111, +0.0111), (+0.3889, +0.1444), (+0.3000, +0.1889), (+0.0111, +0.1667),
     (-0.3000, +0.4333), (-0.5000, +0.5222), (-0.3889, +0.2778), (-0.1889, +0.1000),
     (-0.1667, +0.0111), (-0.0556, -0.0111), (+0.0333, -0.1000), (+0.1222, -0.3000),
     (+0.4333, -0.5222)),
    ((+0.5000, +0.0088), (+0.4474, +0.0263), (+0.3947, -0.0088), (+0.3070, -0.0088),
     (+0.2193, +0.0439), (+0.0614, +0.0614), (-0.1491, +0.0614), (-0.2719, +0.0088),
     (-0.3772, +0.1667), (-0.4474, +0.1667), (-0.5000, +0.0614), (-0.5000, -0.0789),
     (-0.4123, -0.1491), (-0.0614, -0.1316), (-0.0088, -0.1667), (+0.1491, -0.1667),
     (+0.2368, -0.1491)),
    ((+0.5000, -0.1827), (+0.4615, -0.1442), (+0.1346, -0.1250), (+0.0000, +0.0481),
     (+0.0192, +0.1058), (+0.1731, +0.0865), (+0.1731, +0.1442), (+0.0769, +0.2212),
     (-0.1731, +0.2212), (-0.3462, +0.1250), (-0.3846, +0.1250), (-0.4615, +0.2212),
     (-0.5000, +0.1442), (-0.4808, -0.0673), (-0.4038, -0.0673), (-0.1923, +0.0288),
     (-0.0385, -0.2019), (+0.4231, -0.2212)),
    ((+0.5000, -0.5233), (+0.4767, -0.4535), (+0.2907, -0.3837), (+0.1744, -0.2674),
     (+0.0581, -0.0349), (+0.2907, -0.0349), (+0.3140, +0.0116), (+0.2209, +0.1279),
     (-0.1977, +0.1512), (-0.2907, +0.2442), (-0.3837, +0.5233), (-0.4302, +0.5233),
     (-0.5000, +0.2907), (-0.4535, +0.1512), (-0.1047, -0.1047), (-0.0814, -0.2442),
     (+0.0116, -0.3605), (+0.1279, -0.4302)),
    ((+0.5000, -0.4000), (+0.4800, -0.3400), (+0.3200, -0.2600), (+0.2000, -0.1200),
     (+0.3800, +0.0000), (+0.3600, +0.0400), (-0.1000, +0.1400), (-0.3600, +0.3600),
     (-0.5000, +0.4000), (-0.3000, +0.1200), (-0.3400, +0.0600), (-0.2800, +0.0000),
     (-0.1800, +0.0200), (+0.1000, -0.2400)),
)


# ---------------------------------------------------------------------------------------------
# composition
# ---------------------------------------------------------------------------------------------
# Birds are drawn around a few loose centres rather than sprinkled uniformly. Uniform scatter is
# the tell of a generated flock: real birds working the same air arrive in clumps with holes
# between them, and an even field reads as confetti no matter how good the silhouettes are.
_CENTRES = ((0.30, 0.34), (0.62, 0.52), (0.44, 0.72))


def _place(seq: _Seq):
    """One position, clustered on a centre, with the density thinning toward the lower edge."""
    cx, cy = _CENTRES[int(seq.unit() * len(_CENTRES)) % len(_CENTRES)]
    # Gaussian-ish falloff from two uniforms: tight cores, long tails, no library needed.
    r = 0.30 * (seq.unit() + seq.unit() + seq.unit() - 1.5)
    a = seq.span(0.0, math.tau)
    x = cx + r * math.cos(a) * 1.35
    y = cy + r * math.sin(a)
    return x, y


class Bird:
    """One placed silhouette. A dataclass in spirit; __slots__ because there are a few dozen."""

    __slots__ = ("x", "y", "span", "pose", "flip", "tier", "rot", "delay")

    def __init__(self, x, y, span, pose, flip, tier, rot, delay):
        self.x, self.y, self.span, self.pose = x, y, span, pose
        self.flip, self.tier, self.rot, self.delay = flip, tier, rot, delay


def build(seed: int = 20260813, count: int = FLOCK_COUNT) -> list:
    """The flock, as placed birds. Deterministic in `seed`; nothing here reads a clock."""
    seq = _Seq(seed)
    birds = []
    for _ in range(count):
        x, y = _place(seq)
        # Reject anything that would hang off the plate: the flock is composed inside the frame,
        # not cropped by it. Retry rather than clamp — clamping stacks birds on the edges.
        for _ in range(24):
            if 0.03 <= x <= 0.97 and 0.04 <= y <= 0.96:
                break
            x, y = _place(seq)
        # Depth is drawn with a bias toward the far tiers: a flock with as many near birds as far
        # ones has no depth, it has two sizes.
        u = seq.unit()
        tier = 0 if u < 0.42 else 1 if u < 0.72 else 2 if u < 0.91 else 3
        lo, hi = _SPANS[tier]
        birds.append(Bird(
            x=x * W, y=y * H,
            span=seq.span(lo, hi),
            pose=int(seq.unit() * len(_POSES)) % len(_POSES),
            # A flock has a heading. Most birds face the same way; a minority do not, because a
            # flock in which every bird agrees is a formation, and this is not one.
            flip=seq.unit() < 0.22,
            tier=tier,
            rot=seq.span(-14.0, 14.0),
            # Far birds settle first, near birds last, so depth accumulates toward the viewer.
            delay=round(0.12 * tier + seq.span(0.0, 0.55), 2),
        ))
    return birds


# ---------------------------------------------------------------------------------------------
# rendering
# ---------------------------------------------------------------------------------------------

def _path(pose, span: float) -> str:
    pts = _POSES[pose]
    d = "".join(
        ("M" if i == 0 else "L") + f"{x * span:.2f} {y * span:.2f}"
        for i, (x, y) in enumerate(pts)
    )
    return d + "Z"


def _css() -> str:
    """One pass, then nothing — the doctrine the hero slot and the house mark both run under.

    The flock composes itself once, far tier inward, and stops. It does not loop, drift, breathe
    or answer the cursor: a slot that keeps moving asks to be watched, and this one is weather
    behind a headline.

    Longhand animation properties only, never the `animation` shorthand. Every delay here is a
    per-element inline style, and the shorthand carries an `animation-delay:0` with it that would
    flatten the entry into a single frame the moment one delay moved into the stylesheet. That is
    the same rule, and the same reason, as the watershed's paths.
    """
    return (
        "@keyframes flkin{from{opacity:0;translate:var(--dx) var(--dy)}"
        "to{opacity:1;translate:0 0}}"
        ".b{opacity:0;animation-name:flkin;animation-timing-function:cubic-bezier(.32,0,.24,1);"
        "animation-fill-mode:both;animation-duration:1.5s}"
        # Entry offset scales with depth: near birds travel further, which is parallax, and it is
        # what stops the settle reading as one sheet of stickers sliding in together.
        ".t1{--dx:5px;--dy:-2px}.t2{--dx:8px;--dy:-3px}"
        ".t3{--dx:12px;--dy:-5px}.t4{--dx:17px;--dy:-7px}"
        # The finished frame is the drawing; only the arrival is motion, so reduced motion keeps
        # every bird and simply starts them home.
        "@media(prefers-reduced-motion:reduce){"
        ".b{animation-name:none;opacity:1;translate:none}}"
    )


def render_svg(birds=None, seed: int = 20260813, count: int = FLOCK_COUNT) -> str:
    """The deployed asset. Self-contained: it is loaded through an ``<img>``, so it inherits no
    custom property and no stylesheet from the page and has to carry its own ink."""
    birds = build(seed, count) if birds is None else birds
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" '
        f'preserveAspectRatio="xMaxYMid meet" role="img" '
        f'aria-label="A distant scatter of birds over open sky">',
        f"<style>{_css()}</style>",
    ]
    for tier in range(4):
        group = [b for b in birds if b.tier == tier]
        if not group:
            continue
        out.append(f'<g fill="{TIERS[tier]}" class="t{tier + 1}">')
        for b in group:
            sx = -1 if b.flip else 1
            out.append(
                f'<path class="b" style="animation-delay:{b.delay:.2f}s" '
                f'transform="translate({b.x:.1f} {b.y:.1f}) rotate({b.rot:.1f}) '
                f'scale({sx} 1)" d="{_path(b.pose, b.span)}"/>'
            )
        out.append("</g>")
    out.append("</svg>")
    return "".join(out)
