"""Where the survey vocabulary is allowed — and where it must not creep.

The stipple/contour survey language is the strongest thing in Driftwood's visual identity, which is
exactly why it spreads: it looks good on everything, so it ends up on everything, and then it means
nothing. Two instances were removed on 2026-07-31 and this file stops them coming back.

ALLOWED
  - publications and articles: the Review's per-card plate fragments, where the plate is *content*
    (the structure of the plate matches the subject of the piece)
  - page furniture: hero and footer plates

NOT ALLOWED
  - behind a diagram that carries a claim. The homepage lattice had an engraving under it at 5%
    opacity as "ground texture"; it was noise a reader had to subtract before the seven nodes and
    the structural six resolved, and it masked the ghosted situational edges entirely.
  - on wayfinding and directory pages. The Insights landing had a plate band under every section
    head and an art panel beside the Review. A directory is a page someone uses to *find* something.

The distinction is not "is it pretty" but "is the plate carrying meaning, or filling space".
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "src" / "drift" / "web"
DOCS = ROOT / "docs"

# Pages whose job is wayfinding or argument, not publication. No plates.
PLATE_FREE_PAGES = ("insights.html",)


def _plate_refs(text: str):
    """Every reference to survey artwork, by any route: <img>, CSS url(), or a <use> of the library."""
    return (re.findall(r'img/plates/[a-z]+\.svg', text)
            + re.findall(r'[a-z-]*(?:survey-plate|confluence-plate)[a-z-]*\.(?:svg|png)', text)
            + re.findall(r'<use href="#pl-[a-z]+"', text))


def test_the_insights_directory_carries_no_survey_artwork():
    """A directory is carried by type, rule and space. Plates on it are decoration on wayfinding."""
    for name in PLATE_FREE_PAGES:
        refs = _plate_refs((WEB / name).read_text(encoding="utf-8"))
        assert not refs, f"{name} has survey artwork back on it: {sorted(set(refs))}"


def test_no_plate_sits_behind_the_homepage_lattice():
    """The lattice is the site's central argument — seven systems, six structural edges. Anything
    behind it competes with that, and the 5%-opacity engraving that used to be there also hid the
    situational edges the two-tier weighting exists to show."""
    t = (WEB / "hub.html").read_text(encoding="utf-8")
    stage = re.search(r"\.sysstage\{[^}]*\}(?:\s*/\*.*?\*/)?\s*\.sysstage\{[^}]*\}", t, re.S)
    # the specific regression: a ::before/::after backdrop on the lattice stage
    assert not re.search(r"\.sysstage::(?:before|after)\s*\{[^}]*(?:background|url\()", t, re.S), \
        "a backdrop image is back behind the lattice"
    assert "confluence-plate" not in t, "the lattice engraving reference is back"


def test_the_orphaned_backdrop_asset_is_gone():
    """It was 907 KB, referenced by nothing, and copied into docs/ on every build."""
    assert not (WEB / "img" / "confluence-plate.png").exists()
    assert not (DOCS / "img" / "confluence-plate.png").exists()


def test_the_review_keeps_its_plate_fragments():
    """The rule is scope, not abstinence. On the Review the plate IS the content — each card's plate
    is chosen because its structure matches the article's subject — so it stays."""
    t = (WEB / "driftwood-review.html").read_text(encoding="utf-8")
    uses = re.findall(r'<use href="#pl-([a-z]+)"', t)
    assert len(uses) >= 8, f"the Review lost its canonical plate fragments (found {len(uses)})"
    assert "<!--PLATE_LIBRARY-->" in t


def test_the_homepage_keeps_its_footer_plate():
    """Page furniture is explicitly in scope — the argument is about diagrams and directories, and
    the footer band is furniture.

    The *hero* plate is the one exception, and it was never removed on the "decoration vs content"
    argument this file makes. It has now held three things: the generic hydrographic plate, then
    the house mark (2026-08-03), then the hero watershed (2026-08-06). Each replacement moved the
    slot further from furniture and closer to argument — the watershed is the firm's claim about
    coordination drawn rather than stated, which is why it displaced a mark whose job was
    atmosphere. The rule this file guards is unchanged: the survey vocabulary still may not creep
    into diagrams or directories.
    """
    t = (WEB / "hub.html").read_text(encoding="utf-8")
    assert "survey-plate-footer.svg" in t, "the footer plate is page furniture and should remain"
    assert 'class="ws"' in t, "the hero lost the watershed"


def test_every_plate_reference_that_remains_resolves_to_a_real_asset():
    """A dangling plate reference renders as a broken image on a page that is otherwise all restraint."""
    missing = []
    for page in sorted(DOCS.glob("*.html")):
        for ref in re.findall(r'src="(img/(?:plates/)?[^"]+\.(?:svg|png|jpg))"',
                              page.read_text(encoding="utf-8")):
            if not (DOCS / ref).exists():
                missing.append(f"{page.name} -> {ref}")
    assert not missing, f"broken artwork references: {missing}"
