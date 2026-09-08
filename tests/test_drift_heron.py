"""The house mark, and the rules that are the whole point of having one.

A house mark is not a logo, and almost everything that can go wrong with it is a governance
failure rather than a drawing failure: it gets a second version, it turns up in the nav "just
this once", someone brightens it until it competes with the headline, or the animation acquires
a loop. Each of those is cheap to do and permanently expensive — the mark's meaning comes from
being rare, identical, and quiet, and there is no way to earn that back once it is spent.

So the drawing is tested lightly (it is generated and deterministic; the eye is the reviewer) and
the *rules* are tested hard.

── 2026-08-06: THE MARK CAME OFF THE WEBSITE ────────────────────────────────────────────────────
The hero watershed replaced it on the homepage — see the top of hub.html. That was a slot decision,
not a demotion: the heron's job in that plate was atmosphere, and the watershed makes the firm's
actual argument (small waters joining into one channel that is larger below every join). Two
atmospheric marks in one hero would have made both quieter, so the mark left the site rather than
sharing the plate.

What did NOT change: the drawing, the pose, the technique, and the scarcity principle. The heron is
still the house mark, still one master, still reserved for enduring statements — an AWOR cover, a
flagship essay, a client folder, an embossed die. The master simply lives at design/house-mark/
now instead of under web/img/, because it is no longer a deployed asset and should not be shipped
to docs/ as though it were.

So the scarcity tests below inverted rather than disappeared. They used to assert the mark appears
on exactly one page; from 2026-08-06 they asserted it appears on NONE, which is the same rule.

── 2026-09-08: THE MARK CAME BACK, ON THE HOMEPAGE ONLY ─────────────────────────────────────────
The approved Homepage v2 (lock 1a) put the heron in the right column of the hero as a plate,
img/heron-plate.svg: the supplied engraving, one ink on limestone, bill toward the headline, feet on
the CTA baseline. The watershed left the slot rather than sharing it. The scarcity rule stands in
its original form again — one page, one master, never nav / footer / favicon / a repeating slot —
and the generated master at design/house-mark/ still ships nowhere; the plate is its only deployed
form. This file was edited deliberately to say so.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from drift import heron  # noqa: E402

WEB = ROOT / "src" / "drift" / "web"
DOCS = ROOT / "docs"
MASTER = ROOT / "design" / "house-mark" / "heron-engraving.svg"
HUB = WEB / "hub.html"


# ── the master ────────────────────────────────────────────────────────────────────────────────

def test_the_master_is_byte_identical_on_every_run():
    """A house mark that differs run to run is not a house mark — and a generator that drifts
    rewrites the committed asset in every future diff."""
    assert heron.render_svg() == heron.render_svg()


def test_the_committed_master_matches_the_generator():
    """The SVG is a committed static asset. If heron.py changed, `python3 scripts/build_heron.py`
    was the other half of the change."""
    assert MASTER.exists(), "the house-mark master is missing"
    assert MASTER.read_text(encoding="utf-8") == heron.render_svg(), (
        "src/drift/web/img/heron-engraving.svg is stale — run python3 scripts/build_heron.py"
    )


def test_the_engraving_is_hatch_and_stipple_only():
    """Engraved vocabulary, stated structurally: paths of open marks, one solid dot for the eye,
    and nothing else. A <rect>, a gradient, or a filter would be a different kind of picture."""
    svg = MASTER.read_text(encoding="utf-8")
    tags = set(re.findall(r"<([a-zA-Z][a-zA-Z0-9]*)", svg))
    assert tags <= {"svg", "g", "path", "circle"}, f"non-engraving elements in the master: {tags}"
    assert "gradient" not in svg and "filter" not in svg and "<image" not in svg


def test_the_engraving_carries_no_outline():
    """**No outlines** is the load-bearing rule of the whole mark: the bird's edge is where the
    tone stops, which is what makes it read as atmosphere before illustration — and what lets it
    survive being embossed, where a contour would not. Every subpath is an open mark; nothing
    closes, so nothing can be a silhouette."""
    svg = MASTER.read_text(encoding="utf-8")
    for d in re.findall(r' d="([^"]*)"', svg):
        assert "z" not in d.lower(), "a closed subpath appeared — the mark has grown an outline"
        # Every mark is a single move plus one short segment: M..l.. or M..h0 (a stipple dot).
        assert not re.search(r"[CcSsQqTtAa]", d), "curves are not the engraver's vocabulary here"


def test_the_engraving_is_one_ink():
    """Single ink tone. No editorial blue, no accent, no second colour anywhere — consumers that
    want it neutral apply grayscale at the point of use."""
    svg = MASTER.read_text(encoding="utf-8")
    colours = set(re.findall(r"#[0-9A-Fa-f]{3,8}", svg))
    assert colours == {heron.INK}, f"the master is no longer a single ink: {sorted(colours)}"


def test_the_bird_faces_left_into_the_page():
    """Standing, Alert, facing left — toward the headline. The bill is the leftmost thing on the
    plate and the eye sits well behind it; if that ever inverts, the pose has been redrawn."""
    bill_x = min(x for x, _ in heron._CULMEN)
    eye_x, _ = heron._EYE
    assert bill_x < eye_x, "the bird is no longer facing left"
    assert bill_x < 0.15 * heron.W, "the bill should reach the left edge of the plate"


def test_the_pose_is_standing_alert_on_two_legs():
    """Not striking, not in flight, not resting: both legs down and carrying weight, head above
    the body, nothing folded."""
    assert heron._LEG_A[-1][1] > 0.9 * heron.H and heron._LEG_B[-1][1] > 0.9 * heron.H, \
        "a leg has left the ground — this is no longer the standing pose"
    assert heron._EYE[1] < 0.2 * heron.H, "the head has dropped; the alert pose carries it high"


# ── scarcity: the mark is not a web asset ─────────────────────────────────────────────────────

def _pages(root: Path):
    return sorted(p for p in root.glob("*.html"))


def test_the_house_mark_appears_on_the_homepage_and_nowhere_else():
    """This is the rule the mark's meaning is made of. It is not a decorative asset that pages may
    reach for; it appears where Driftwood makes an enduring statement. As of 2026-09-08 exactly one
    web page is one: the homepage hero (Homepage v2 lock 1a), which carries the approved plate
    img/heron-plate.svg. The generated master (heron-engraving) still ships nowhere. Every other
    page is a deliberate absence — a second page has to earn it with an edit to this test."""
    strays, plates = [], []
    for root in (WEB, DOCS):
        for page in _pages(root):
            t = page.read_text(encoding="utf-8")
            if "heron-engraving" in t:
                strays.append(f"{root.name}/{page.name}")
            if "heron-plate" in t:
                plates.append(f"{root.name}/{page.name}")
    assert not strays, f"the master has returned to: {strays} — the plate is the only deployed form"
    assert sorted(plates) == ["docs/index.html", "web/hub.html"], \
        f"the plate must appear on the homepage only, found on: {plates} — rarity is the whole instrument"


def test_the_master_is_not_a_deployed_asset():
    """It lives in design/, not under web/img/ and not in docs/. Left in the web tree it would be
    copied into every build by sync_docs.py and would sooner or later be reached for by a page that
    just wanted texture, which is exactly the failure the scarcity rule exists to prevent."""
    assert MASTER.exists(), "the house-mark master is missing"
    assert not (WEB / "img" / "heron-engraving.svg").exists(), \
        "the master is back in the web tree, where it will be deployed and eventually reused"
    assert not (DOCS / "img" / "heron-engraving.svg").exists(), \
        "a stale copy of the mark is still being shipped in docs/"


def test_the_hero_carries_the_heron_plate_and_nothing_else_decorative():
    """2026-09-08: the mark returns to the homepage as the approved plate (img/heron-plate.svg,
    Homepage v2 lock 1a). It is decorative in the accessibility sense — inside an aria-hidden
    figure, never a link — and the watershed it replaces is gone entirely rather than sharing the
    plate: two atmospheric drawings in one hero would make both quieter."""
    t = HUB.read_text(encoding="utf-8")
    fig = re.search(r'<figure class="heron-col"[^>]*>(.*?)</figure>', t, re.S)
    assert fig, "the hero has lost the heron plate"
    assert 'aria-hidden="true"' in t[fig.start():fig.start() + 80], \
        "the plate is announcing itself to screen readers"
    assert 'src="img/heron-plate.svg"' in fig.group(1)
    before = t[: fig.start()]
    assert before.rfind("<a ") < before.rfind("</a>"), "the plate is inside a link"
    assert '<svg class="ws"' not in t, "the watershed is back beside the heron"
    assert "mask-image" not in t, "the plate is faded under the copy; it sits in its own column"


def test_the_plate_sits_in_its_own_column_and_never_under_the_copy():
    """Typography wins by geometry: the plate is the second column of the hero grid, spanning the
    headline, the aside and the action, so it can never be drawn under a word. Feet on the CTA
    baseline at desktop (align-self:end in a grid aligned to end), a 480px plate; below 900px it
    drops under the copy at 380px and keeps its balance rather than the baseline."""
    t = HUB.read_text(encoding="utf-8")
    col = re.search(r"\.heron-col\{([^}]*)\}", t)
    assert col, "the heron column has no rule"
    assert "grid-column:2" in col.group(1) and "align-self:end" in col.group(1)
    assert "max-width:480px" in col.group(1), "the desktop plate is no longer the approved 480px"
    assert re.search(r"\.hero-grid\{[^}]*grid-template-columns:minmax\(0,13fr\) minmax\(0,9fr\)", t), \
        "the hero lost its 13:9 copy/plate proportion"
    assert re.search(r"@media\(max-width:899px\)\{[^@]*\.heron-col\{[^}]*max-width:380px", t, re.S), \
        "the plate does not step down under the copy on narrow viewports"


def test_the_plate_is_the_supplied_asset_one_ink_on_limestone():
    """The approved plate, used verbatim: one ink (#1e2833) with limestone (#f1efe9) knockouts,
    no gradient, no raster, no text, no second colour. The file is shipped from web/img so
    sync_docs copies it through with the other plates."""
    plate = WEB / "img" / "heron-plate.svg"
    assert plate.exists() and (DOCS / "img" / "heron-plate.svg").exists()
    svg = plate.read_text(encoding="utf-8")
    colours = set(re.findall(r'(?:fill|stroke)="(#[0-9a-fA-F]{6})"', svg))
    assert colours == {"#1e2833", "#f1efe9"}, f"the plate is no longer ink on limestone: {sorted(colours)}"
    assert "<text" not in svg and "<image" not in svg and "gradient" not in svg.lower()
    assert 'viewBox="0 0 660 720"' in svg
