"""The Driftwood Review is a *record*, and a record's credibility is its fixed structure.

Everything pinned here is something that would still render fine if it broke, and would quietly
destroy the thing the publication is for:

  - a reordered or dropped division makes it a newsletter with a masthead
  - a bespoke illustration makes the ten-plate vocabulary decorative instead of meaningful
  - a stray figure in a summary makes it a marketing page with a provenance problem
  - the homepage lattice tiled behind the cards turns a specific claim into wallpaper

None of those raise an exception in a browser. They only fail here.
"""
import re
from pathlib import Path

import pytest

from drift.plates import NAMES

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "src" / "drift" / "web"
DOCS = ROOT / "docs"
REVIEW = WEB / "driftwood-review.html"

# The running order. This tuple IS the specification — it is not derived from the page.
DIVISIONS = (
    ("lead-essay", "Lead Essay"),
    ("research-notes", "Research Notes"),
    ("tax-planning", "Tax &amp; Planning"),
    ("market-structure", "Market Structure"),
    ("practice-updates", "Practice Updates"),
    ("reading-list", "Reading List"),
    ("appendix", "Appendix"),
)
DISCIPLINES = ("research", "commentary", "household")

_CARD_RE = re.compile(r'<article class="card[^"]*"([^>]*)>(.*?)</article>', re.S)


def _src() -> str:
    return REVIEW.read_text(encoding="utf-8")


def _cards():
    """(attrs, inner html) for every card on the page."""
    return [(m.group(1), m.group(2)) for m in _CARD_RE.finditer(_src())]


# ── 1. the running order never changes ────────────────────────────────────────────────────────

def test_the_seven_divisions_exist_in_the_specified_order():
    """Seven divisions, this order, every issue. A quarter may have little to say under a heading;
    it may not move the heading."""
    t = _src()
    positions = []
    for anchor, title in DIVISIONS:
        marker = f'id="{anchor}"'
        assert marker in t, f"division {title!r} is missing"
        assert title in t, f"division heading {title!r} is missing"
        positions.append(t.index(marker))
    assert positions == sorted(positions), (
        "the running order drifted: "
        f"{[d[1] for d in sorted(zip(positions, DIVISIONS))]}"
    )


def test_the_running_order_index_matches_the_divisions():
    """The 'in this issue' nav is a promise about the page. Every entry must land somewhere."""
    t = _src()
    order = re.search(r'<nav class="order".*?</nav>', t, re.S)
    assert order, "the running-order index is missing"
    linked = re.findall(r'href="#([a-z-]+)"', order.group(0))
    assert linked == [a for a, _ in DIVISIONS]


def test_no_eighth_division_crept_in():
    """A new section is a change to the publication's structure and must be a deliberate edit to
    DIVISIONS above, not an addition to the page."""
    sections = re.findall(r'<section class="sec" id="([a-z-]+)"', _src())
    assert sections == [a for a, _ in DIVISIONS]


# ── 2. the card architecture ──────────────────────────────────────────────────────────────────

def test_every_card_has_exactly_the_four_elements_in_order():
    """Metadata, headline, summary, survey fragment. Nothing else — no tag chips, no read-time,
    no author badge, no engagement counter. The restraint IS the design."""
    for attrs, body in _cards():
        order = [m.group(1) for m in re.finditer(r'class="(meta|hd|sum|frag)"', body)]
        assert order == ["meta", "hd", "sum", "frag"], f"card element order is {order} in {attrs}"


def test_every_card_metadata_row_is_date_then_type():
    for attrs, body in _cards():
        meta = re.search(r'<div class="meta">(.*?)</div>', body, re.S)
        assert meta, f"card has no metadata row: {attrs}"
        assert re.search(r'<time datetime="\d{4}-\d{2}-\d{2}">', meta.group(1)), \
            f"metadata row needs a machine-readable date: {attrs}"
        assert '<span class="sl">//</span>' in meta.group(1), "metadata separator is '//'"


def test_no_summary_exceeds_twenty_five_words():
    """A cap that forces the summary to state the claim instead of trailing off into copy."""
    for attrs, body in _cards():
        sm = re.search(r'<p class="sum">(.*?)</p>', body, re.S)
        assert sm, f"card has no summary: {attrs}"
        words = re.sub(r"<[^>]+>", " ", sm.group(1)).split()
        assert len(words) <= 25, f"summary runs {len(words)} words: {' '.join(words)[:70]}…"


def test_the_fragment_zone_contains_artwork_and_never_type():
    """'NO TEXTBOOK BLINDERS': the plate zone carries no caption, no numeral, no sheet stamp."""
    for attrs, body in _cards():
        frag = re.search(r'<div class="frag">(.*?)</div>', body, re.S)
        assert frag, f"card has no survey fragment: {attrs}"
        inner = frag.group(1)
        assert "<use" in inner, f"fragment is not a canonical plate: {attrs}"
        assert "<text" not in inner and "<tspan" not in inner
        assert not re.sub(r"<[^>]+>", "", inner).strip(), "the fragment zone must carry no text"


# ── 3. the artwork is a closed library ────────────────────────────────────────────────────────

def test_every_card_uses_a_canonical_plate():
    """No bespoke art. If a piece needs a picture, it gets the plate whose structure matches it."""
    used = []
    for attrs, body in _cards():
        declared = re.search(r'data-plate="([a-z]+)"', attrs)
        assert declared, f"card declares no plate: {attrs}"
        assert declared.group(1) in NAMES, f"{declared.group(1)!r} is not in the library"
        ref = re.search(r'<use href="#pl-([a-z]+)"', body)
        assert ref, f"card renders no plate: {attrs}"
        assert ref.group(1) == declared.group(1), \
            f"card declares {declared.group(1)} but renders {ref.group(1)}"
        used.append(declared.group(1))
    assert used, "the issue has no cards"


def test_the_issue_exercises_the_whole_library():
    """Not a hard rule for every future issue, but true of the template issue — a vocabulary the
    reader never sees in full cannot be learned."""
    used = {re.search(r'data-plate="([a-z]+)"', a).group(1) for a, _ in _cards()}
    assert used == set(NAMES), f"never shown: {sorted(set(NAMES) - used)}"


def test_no_image_tags_or_external_art():
    """The plates are the art. A stock photograph or an uploaded illustration breaks the record."""
    t = _src()
    assert "<img" not in t, "the Review carries no raster art"
    assert not re.search(r'src="https?://', t), "no externally hosted asset"


# ── 4. the prohibitions ───────────────────────────────────────────────────────────────────────

def test_the_issue_publishes_no_dollar_or_percentage_figure():
    """The Review links to figures; it does not restate them. Any figure it printed would need its
    own FIGURE_PROVENANCE.md row, and a quarterly publication is exactly where an unsourced number
    would slip in unnoticed."""
    body = re.search(r"<main>(.*?)</main>", _src(), re.S)
    assert body, "the issue has no <main>"
    text = re.sub(r"<[^>]+>", " ", body.group(1))
    assert "$" not in text, "a dollar figure appeared in the issue body"
    assert "%" not in text, "a percentage appeared in the issue body"


def test_no_invented_telemetry_or_index():
    """No fake metrics, scores, indices, or simulated readouts — explicitly out of scope."""
    t = _src().lower()
    for banned in ("system elevation", "regional score", "index score", "telemetry",
                   "confidence score", "readout"):
        assert banned not in t, f"invented metric on the page: {banned!r}"


def test_the_homepage_lattice_does_not_bleed_into_the_review():
    """The seven-node lattice is a claim about one household's systems moving together. Tiled
    behind editorial cards it would become decoration and stop being an argument."""
    t = _src()
    for marker in ('class="net', "net--structural", "net--rim", 'class="sysstage', 'class="node',
                   "GOVERNANCE"):
        assert marker not in t, f"homepage lattice markup leaked onto the Review: {marker!r}"


def test_border_radius_is_zero_everywhere():
    t = _src()
    radii = set(re.findall(r"border-radius:\s*([^;}]+)", t))
    assert radii <= {"0"}, f"non-zero corner radius: {radii}"


# ── 5. the three disciplines ──────────────────────────────────────────────────────────────────

def test_all_three_disciplines_appear_and_every_card_declares_one():
    seen = set()
    for attrs, _ in _cards():
        d = re.search(r'data-type="([a-z]+)"', attrs)
        assert d, f"card declares no publication type: {attrs}"
        assert d.group(1) in DISCIPLINES, f"unknown discipline {d.group(1)!r}"
        seen.add(d.group(1))
    assert seen == set(DISCIPLINES), f"discipline never demonstrated: {set(DISCIPLINES) - seen}"


def test_each_discipline_sets_a_distinct_density():
    """The three types must actually render differently. Identical handles would mean the
    'editorial discipline' is a label with no visual consequence."""
    t = _src()
    handles = {}
    for d in DISCIPLINES:
        block = re.search(r'\.card\[data-type="%s"\]\{(.*?)\}' % d, t, re.S)
        assert block, f"no density handles for {d!r}"
        handles[d] = dict(re.findall(r"(--pl-[a-z0-9]+):\s*([^;]+)", block.group(1)))
        for required in ("--pl-ink", "--pl-sound", "--pl-w", "--pl-s2", "--pl-s3"):
            assert required in handles[d], f"{d} does not set {required}"
    assert len({tuple(sorted(v.items())) for v in handles.values()}) == 3, \
        "two disciplines render identically"


def test_density_falls_monotonically_from_research_to_household():
    """research dense -> commentary lighter -> household near-silent. The ordering is the point."""
    t = _src()
    ink = {}
    for d in DISCIPLINES:
        block = re.search(r'\.card\[data-type="%s"\]\{(.*?)\}' % d, t, re.S)
        ink[d] = float(re.search(r"--pl-ink:\s*([\d.]+)", block.group(1)).group(1))
    assert ink["research"] > ink["commentary"] > ink["household"], ink


def test_household_drops_both_optional_sounding_tiers():
    """'Tiny, isolated survey fragments … the visual language steps completely out of the way.'"""
    block = re.search(r'\.card\[data-type="household"\]\{(.*?)\}', _src(), re.S).group(1)
    assert re.search(r"--pl-s2:\s*0", block) and re.search(r"--pl-s3:\s*0", block)


def test_research_keeps_every_tier():
    block = re.search(r'\.card\[data-type="research"\]\{(.*?)\}', _src(), re.S).group(1)
    assert re.search(r"--pl-s2:\s*1", block) and re.search(r"--pl-s3:\s*1", block)


# ── 6. it actually ships ──────────────────────────────────────────────────────────────────────

def test_the_template_carries_the_build_tokens_not_a_baked_library():
    """The 170 KB plate library is injected at build time. Committing it into the template would
    bury the markup and make every regeneration an unreviewable diff."""
    t = _src()
    assert "<!--PLATE_LIBRARY-->" in t
    assert "<!--FIRM_ANCHOR-->" in t
    assert "<symbol" not in t, "the plate library was baked into the source template"


def test_the_built_page_has_the_library_expanded():
    built = DOCS / "driftwood-review.html"
    assert built.exists(), "driftwood-review.html is not registered in scripts/sync_docs.py"
    b = built.read_text(encoding="utf-8")
    assert "<!--PLATE_LIBRARY-->" not in b and "<!--FIRM_ANCHOR-->" not in b, "token left unexpanded"
    for name in NAMES:
        assert f'id="pl-{name}"' in b, f"#pl-{name} missing from the built page"
    assert "firm-anchor" in b


def test_the_standalone_plate_files_ship_too():
    """A page that does not need CSS-driven density can reference a plate with a plain <img>."""
    for name in NAMES:
        assert (DOCS / "img" / "plates" / f"{name}.svg").exists(), f"docs/img/plates/{name}.svg"


@pytest.mark.parametrize("anchor,_title", DIVISIONS)
def test_every_division_is_reachable_from_the_index(anchor, _title):
    assert f'href="#{anchor}"' in _src()


def test_every_internal_link_resolves_to_a_built_page():
    """The failure this repo has actually shipped before: a page in the nav that was never
    registered in sync_docs.py, 404ing in production from every page that linked it."""
    hrefs = {h.split("#")[0] for h in re.findall(r'href="([^"#][^"]*)"', _src())}
    # Absolute URLs are excluded on purpose: <link rel="canonical"> must stay absolute, and a
    # blanket absolute->relative rewrite has broken it in this repo before.
    internal = {h for h in hrefs if h.endswith(".html") and "://" not in h}
    broken = sorted(h for h in internal if not (DOCS / h).exists())
    assert not broken, f"links to unbuilt pages: {broken}"
    assert internal, "the issue links nowhere"
