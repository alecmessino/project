"""The Canonical Survey Library is a closed vocabulary. These tests keep it closed.

The library's whole value is that it is fixed: ten plates, reused across every issue, each one
structurally what its name says. That value decays the moment someone adds an eleventh plate for a
one-off article, or quietly re-tunes `gradient` until it stops tightening, or lets a plate carry a
number. Each of those is a silent failure — the page still renders, it just stops meaning anything.
So each is pinned here.
"""
import math
import re
from pathlib import Path

import pytest

from drift import plates
from drift.plates import CANON, NAMES, W, H, build, build_all, render_svg, render_symbols

PLATE_DIR = Path(__file__).resolve().parents[1] / "src" / "drift" / "web" / "img" / "plates"


# ── the library is closed ─────────────────────────────────────────────────────────────────────

def test_the_library_is_exactly_ten_plates():
    """Ten, no more. An eleventh plate is a new word in a vocabulary meant to be memorised."""
    assert len(CANON) == 10
    assert len(NAMES) == len(set(NAMES)) == 10


def test_every_plate_builds_and_declares_its_structure():
    for name, numeral, structure in CANON:
        p = build(name)
        assert p.name == name and p.numeral == numeral and p.structure == structure
        assert p.contours, f"{name} drew nothing"
        assert any(p.tiers), f"{name} has no sounding field"


def test_an_unknown_plate_is_refused_by_name():
    """Fail loudly rather than silently rendering an empty box in a published issue."""
    with pytest.raises(KeyError, match="canonical survey library"):
        build("escarpment")


def test_every_plate_stays_inside_its_canvas():
    """A plate that overruns its viewBox gets silently cropped by `slice` and the structure the
    reader is supposed to recognise disappears."""
    for p in build_all():
        for tier in p.tiers:
            for x, y in tier:
                assert -1 <= x <= W + 1 and -1 <= y <= H + 1, f"{p.name}: sounding off-canvas"


# ── determinism: these are committed assets ───────────────────────────────────────────────────

def test_generation_is_deterministic():
    """Same input, same bytes. The plates are committed files; a generator that drifted would
    rewrite ten assets on every unrelated build."""
    assert render_svg(build("delta")) == render_svg(build("delta"))
    once, twice = build_all(), build_all()
    for a, b in zip(once, twice):
        assert a.contours == b.contours and a.tiers == b.tiers


def test_committed_files_match_the_generator():
    """`scripts/build_plates.py` output is checked in. If plates.py changed and the files were not
    rebuilt, docs/ ships one library and the module describes another."""
    missing = [n for n in NAMES if not (PLATE_DIR / f"{n}.svg").exists()]
    assert not missing, f"never built: {missing} — run python3 scripts/build_plates.py"
    stale = [p.name for p in build_all()
             if (PLATE_DIR / f"{p.name}.svg").read_text(encoding="utf-8") != render_svg(p)]
    assert not stale, f"stale plate files: {stale} — run python3 scripts/build_plates.py"


def test_plates_are_not_a_random_field():
    """Two different plates must not coincidentally produce the same geometry — that would mean the
    'structure' claim is decoration and the seed is doing all the work."""
    seen = {}
    for p in build_all():
        key = str(p.contours)
        assert key not in seen, f"{p.name} is geometrically identical to {seen[key]}"
        seen[key] = p.name


# ── the prohibitions: clean artwork, no invented data ─────────────────────────────────────────

def test_plates_carry_no_archival_stamps_or_text():
    """No 'Plate I', no 'Sheet 01', no title block, no legend — no text at all. The catalogue
    numeral is an internal identifier and must never reach the artwork."""
    for p in build_all():
        svg = render_svg(p)
        assert "<text" not in svg, f"{p.name}: artwork carries type"
        assert "<tspan" not in svg
        assert not re.search(r"\b(Plate|Sheet|Fig\.?|Figure)\b", svg), f"{p.name}: archival stamp"
        # the numeral may appear only inside the aria-label's structure phrase, never as a stamp
        assert f">{p.numeral}<" not in svg


def test_plates_encode_no_measurement():
    """These are not charts. No axis, no tick label, no scale bar, no units — nothing a reader
    could mistake for data. (FIGURE_PROVENANCE.md: an unfalsifiable quantitative claim on a public
    page is the failure mode this whole discipline exists to prevent.)"""
    for p in build_all():
        svg = render_svg(p)
        for banned in ("%", "$", "axis", "scale", "legend", "data-value"):
            assert banned not in svg, f"{p.name}: {banned!r} implies the plate carries a figure"


def test_the_palette_is_the_master_plates_monochrome():
    """One ink, lifted from survey-plate-hero.svg. Research is specified as uncompromising
    monochrome, and colour is separately budgeted site-wide — a plate must not spend any of it."""
    for p in build_all():
        svg = render_svg(p)
        colours = set(re.findall(r"#[0-9A-Fa-f]{3,6}", svg))
        assert colours == {plates.INK}, f"{p.name} introduced colour: {colours - {plates.INK}}"


# ── each plate is structurally what it claims ─────────────────────────────────────────────────

def _xs_of_vertical_family(plate):
    """Mean x of each contour, sorted — for plates whose structure is read across the page."""
    return sorted(sum(x for x, _ in c) / len(c) for c in plate.contours)


def test_gradient_actually_tightens():
    """The plate means 'rate escalation'. If its spacing is uniform it is `contour` with a
    different caption, which is exactly the failure caught in review."""
    xs = _xs_of_vertical_family(build("gradient"))
    gaps = [b - a for a, b in zip(xs, xs[1:])]
    assert len(gaps) >= 8
    # monotonically collapsing, and dramatically so end-to-end
    assert gaps[0] > gaps[-1] * 8, f"first gap {gaps[0]:.1f} vs last {gaps[-1]:.1f} — not steep"
    assert sum(b <= a * 1.02 for a, b in zip(gaps, gaps[1:])) >= len(gaps) - 2


def test_contour_is_uniform_and_gradient_is_not():
    """The pair only carries meaning as a contrast: systematic exposure vs escalating friction."""
    ys = sorted(sum(y for _, y in c) / len(c) for c in build("contour").contours)
    gaps = [b - a for a, b in zip(ys, ys[1:])]
    assert max(gaps) - min(gaps) < 0.5, f"'uniform tracking lines' are not uniform: {gaps}"


def test_boundary_never_crosses_its_own_line():
    """'Abrupt terminal hairlines' — two families that stop dead. A contour continuing across the
    boundary would say the jurisdictions are continuous, the opposite of the plate's meaning."""
    p = build("boundary")
    vertical = [c for c in p.contours if len(c) == 2 and abs(c[0][0] - c[1][0]) < 0.01]
    assert len(vertical) == 1, "the boundary line itself is missing"
    bx = vertical[0][0][0]
    for c in p.contours:
        if c is vertical[0]:
            continue
        xs = [x for x, _ in c]
        assert min(xs) >= bx - 0.01 or max(xs) <= bx + 0.01, "a contour crosses the boundary"


def test_divide_contours_terminate_at_the_ridge_and_mirror_across_it():
    """A divide separates flow. Its two families must meet AT the crest and lean opposite ways —
    negating one family instead of mirroring it produced a single comb running straight through
    the ridge, which reads as one catchment, not two."""
    p = build("divide")
    crest = p.contours[0]
    (ax, ay), (bx, by) = crest[0], crest[-1]
    arms = p.contours[1:]
    assert len(arms) >= 40

    def side(px, py):                       # sign of the cross product = which side of the crest
        return (bx - ax) * (py - ay) - (by - ay) * (px - ax)

    north = [a for a in arms if side(*a[-1]) < 0]
    south = [a for a in arms if side(*a[-1]) > 0]
    assert north and south, "the ridge does not separate two families"
    assert abs(len(north) - len(south)) <= 1

    def heading(arm):
        dx, dy = arm[-1][0] - arm[0][0], arm[-1][1] - arm[0][1]
        return math.atan2(dy, dx)

    # every arm starts on the crest …
    for arm in arms:
        assert abs(side(*arm[0])) < 1e-6, "an arm does not start on the ridge"
    # … and the two families genuinely point apart
    spread = abs(heading(north[0]) - heading(south[0]))
    assert math.radians(60) < spread < math.radians(300), f"families not mirrored ({spread:.2f} rad)"


def test_basin_and_watershed_are_closed_but_confluence_and_delta_are_not():
    """Enclosed structures (pools, catchments) close; flow structures (streams, distributaries)
    do not. Getting this backwards inverts what the plate says about the money."""
    for name in ("basin", "watershed"):
        p = build(name)
        assert all(c[0] == c[-1] or math.dist(c[0], c[-1]) < 1.0 for c in p.contours), \
            f"{name} must enclose"
    for name in ("confluence", "delta", "current", "tributary"):
        p = build(name)
        assert any(math.dist(c[0], c[-1]) > 20.0 for c in p.contours), f"{name} must not enclose"


def test_delta_disperses_and_confluence_converges():
    """Mirror-image claims — generational outflow vs systems coordination. The vertical spread of
    the endpoints has to move the opposite way for each."""
    def spread(pts):
        ys = [y for _, y in pts]
        return max(ys) - min(ys)

    d = build("delta")
    assert spread([c[0] for c in d.contours]) < spread([c[-1] for c in d.contours]), \
        "delta must end wider than it starts"

    c = build("confluence")
    lower = [x for x in c.contours if math.dist(x[0], x[-1]) > 20.0]
    assert spread([p[0] for p in lower]) > spread([p[-1] for p in lower]), \
        "confluence must end narrower than it starts"


# ── rendering contract ────────────────────────────────────────────────────────────────────────

def test_density_is_gated_on_inherited_custom_properties():
    """The three disciplines are served by ONE library. That only works because custom properties
    cross the <use> shadow boundary — so the tiers must stay gated on them, never baked in."""
    svg = render_svg(build("contour"))
    assert "var(--pl-s2,1)" in svg and "var(--pl-s3,1)" in svg
    assert "var(--pl-ink,.5)" in svg and "var(--pl-sound,.34)" in svg
    assert 'class="pl-s1"' in svg and 'class="pl-s2"' in svg and 'class="pl-s3"' in svg


def test_symbol_library_exposes_every_plate_once():
    lib = render_symbols()
    for name in NAMES:
        assert lib.count(f'id="pl-{name}"') == 1, f"#pl-{name} missing or duplicated"
    assert lib.count("<symbol") == 10
    assert 'aria-hidden="true"' in lib


def test_simplification_stays_sub_pixel():
    """Polylines are decimated to keep the inlined library small. That is only safe if the error
    is invisible — otherwise the plates quietly lose the features the tests above check for."""
    for p in build_all():
        for c in p.contours:
            simple = plates._simplify(c)
            assert len(simple) >= 2
            assert simple[0] == c[0] and simple[-1] == c[-1], "endpoints must be preserved"
            kept = set(simple)
            for pt in c:
                if pt in kept:
                    continue
                # every dropped point must lie within tolerance of the retained polyline
                best = min(_point_seg_dist(pt, a, b) for a, b in zip(simple, simple[1:]))
                assert best <= plates.SIMPLIFY_TOL + 1e-6, f"{p.name}: dropped point off by {best}"


def _point_seg_dist(p, a, b):
    (px, py), (ax, ay), (bx, by) = p, a, b
    dx, dy = bx - ax, by - ay
    if dx == dy == 0:
        return math.dist(p, a)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.dist(p, (ax + t * dx, ay + t * dy))
