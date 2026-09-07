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
on exactly one page; they now assert it appears on NONE, which is the same rule — the mark goes
where Driftwood makes an enduring statement, and today no web page is one. The day it returns to a
page, that page has to earn it, and this file should be edited deliberately to say so.
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


def test_the_house_mark_appears_on_no_page_at_all():
    """This is the rule the mark's meaning is made of, in its current form. It is not a decorative
    asset that pages may reach for; it appears where Driftwood makes an enduring statement, and as
    of 2026-08-06 no web page is one. Every page is a deliberate absence, not an oversight — and a
    reappearance should be a considered edit to this test, never a quiet import."""
    strays = []
    for root in (WEB, DOCS):
        for page in _pages(root):
            if "heron-engraving" in page.read_text(encoding="utf-8"):
                strays.append(f"{root.name}/{page.name}")
    assert not strays, f"the house mark has returned to: {strays} — rarity is the whole instrument"


def test_the_master_is_not_a_deployed_asset():
    """It lives in design/, not under web/img/ and not in docs/. Left in the web tree it would be
    copied into every build by sync_docs.py and would sooner or later be reached for by a page that
    just wanted texture, which is exactly the failure the scarcity rule exists to prevent."""
    assert MASTER.exists(), "the house-mark master is missing"
    assert not (WEB / "img" / "heron-engraving.svg").exists(), \
        "the master is back in the web tree, where it will be deployed and eventually reused"
    assert not (DOCS / "img" / "heron-engraving.svg").exists(), \
        "a stale copy of the mark is still being shipped in docs/"



def test_the_homepage_carries_only_the_supplied_heron():
    import hashlib
    t = HUB.read_text(encoding="utf-8")
    assert t.count('src="img/heron-plate.svg"') == 1
    assert '<svg class="ws"' not in t
    supplied = WEB / "img/heron-plate.svg"
    assert hashlib.sha256(supplied.read_bytes()).hexdigest() == "3a7bf75ade532043c6da5d52d7851f9a90154cd671edf7b5d445d4d2b09c04de"
    assert supplied.read_bytes() == (DOCS / "img/heron-plate.svg").read_bytes()
    for page in WEB.glob("*.html"):
        if page.name != "hub.html":
            assert "heron-plate.svg" not in page.read_text()


def test_the_heron_has_its_own_responsive_column():
    t = HUB.read_text(encoding="utf-8")
    assert 'class="heron-col"' in t
    css = (WEB / "driftwood.css").read_text()
    assert '.dw-home .heron-col{max-width:480px;}' in css
    assert 'grid-row:auto!important' in css
    assert 'alt=""' in re.search(r'<img[^>]*heron-plate.svg[^>]*>', t).group(0)
