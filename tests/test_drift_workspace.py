"""Guards for the Coordination Atlas workspace (src/drift/web/coordination-atlas.html).

One surface, four routes: #/atlas (the state brief, the comparison, a move), #/assessment (a ruled
two-column ledger), #/review (the scope a review would examine), and #/brief (three printable
documents for the household's CPA). The behaviour is exercised in tests/web/test_coordination_atlas.js,
which drives the real script against the real Atlas payload; what is pinned HERE is the design
contract — the things a later edit would quietly reintroduce because they are easy and they look
like progress.

Four of those prohibitions are worth naming, because each one was a real earlier iteration of this
surface and each was cut deliberately:

  * No 0–5 dot scale, friction score, complexity index, or any other ranking device. The Atlas is
    not a league table and the Assessment is not a credit rating; an ordering invented for a
    household is a claim the data does not support.
  * No archetype labels ("The Founder", "The Inheritor") as navigation or as a visual system. They
    read as a personality quiz, and they decide for a reader what their own situation is.
  * No "If you were moving here / if you were leaving" marketing blocks. The Atlas does not
    recommend a move; residency is proved by days, ties, and intent.
  * No surface diagram or radar on the Assessment. The inventory names the matters back in words.
"""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "src" / "drift" / "web"
DOCS = ROOT / "docs"
PAGE = WEB / "coordination-atlas.html"
BUILT = DOCS / "coordination-atlas.html"


@pytest.fixture(scope="module")
def src() -> str:
    return PAGE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def built() -> str:
    assert BUILT.exists(), "docs/coordination-atlas.html is not built — run `drift statemap`"
    return BUILT.read_text(encoding="utf-8")


# ── the workspace is one surface over four routes ─────────────────────────────────────────────

@pytest.mark.parametrize("route", ["atlas", "assessment", "review", "brief"])
def test_every_route_is_reachable_by_hash(src, route):
    assert f'"{route}"' in src, f"the #{route} route is gone"
    assert f'#/{route}' in src, f"nothing links to #/{route}"


def test_the_three_primary_routes_carry_a_visible_switcher(src):
    """The Atlas, the Assessment and the Review are one workspace, not three pages that happen to
    share a stylesheet. The route bar is what makes that legible."""
    for route in ("atlas", "assessment", "review"):
        assert f'data-route-link="{route}"' in src, f"the {route} route has no switch in the chrome"
    # #/brief is deliberately NOT a fourth tab: it is a document you go and print, reached from the
    # surface that produced it, not a place in the workspace.
    assert 'data-route-link="brief"' not in src


def test_the_atlas_leads_with_the_brief_and_offers_the_map_on_request(src):
    """The state brief is the centre of gravity. The map is available on request — it used to BE the
    page, which put a lookup device in front of the reading."""
    assert re.search(r"mapOpen:\s*false", src), \
        "the cartogram opens by default again, above the brief it is supposed to serve"
    assert "Map &amp; ladder" in src and "togglemap" in src, "the map can no longer be summoned or dismissed"
    assert re.search(r'tab:\s*"brief"', src), "the Atlas no longer opens on the state brief"


def test_the_household_is_carried_by_the_shared_platform_not_a_private_store(src):
    """A module declares itself to the operating system; it does not re-implement it. The household
    (state · inventory · portfolio) lives in dw-context.js so every other Driftwood tool sees it."""
    assert 'src="dw-context.js"' in src, "the workspace does not load the operating system"
    assert "window.dwTaxContext.save" in src, "the workspace does not write through the shared context"
    assert "dwTaxContext.subscribe" in src, "the workspace does not follow the shared household"
    # The workspace's own localStorage key may hold UI state only. If a household field appears in
    # it, two stores own the same value and they will diverge.
    m = re.search(r"localStorage\.setItem\(UI_KEY, JSON\.stringify\(\{(.*?)\}\)", src, re.S)
    assert m, "the workspace UI store has moved — re-check what it persists"
    for field in ("checked", "portfolio", "drivers"):
        assert field not in m.group(1), \
            f"{field!r} is a household field and must not be persisted in the workspace's own store"


def test_the_portfolio_is_parsed_in_exactly_one_place(src):
    """CLAUDE.md, after the 2026-07-26 leakage.html incident: a page that takes the same field from
    a URL param and from a control must not grow a second parser. The workspace hands the raw
    parameter to dwTaxContext.save(), which owns parsePortfolioLike() — so it must not parse one
    itself. tests/web/test_coordination_atlas.js proves both paths land on the same number."""
    assert "parsePortfolioLike" not in src, \
        "the workspace has its own copy of the portfolio parser — there must be one, in dw-context.js"
    assert not re.search(r"(?:parseFloat|parseInt|\+\s*)\(\s*(?:qs|q)\.get\(\"port\"", src), \
        "a portfolio parameter is being coerced locally instead of handed to dwTaxContext"
    assert 'patch.portfolio = port' in src, "the raw port parameter no longer reaches the shared parser"


# ── the softened impact figure ────────────────────────────────────────────────────────────────

def test_the_impact_figure_defaults_to_a_percentage_and_scales_on_request(src):
    """Dollars are a claim about a household we have not met. The figure is a share of taxable
    assets until the reader supplies a portfolio, and only then is it denominated."""
    assert "% of taxable assets" in src, "the softened default figure is gone"
    assert "set a portfolio size to read it in dollars" in src, "the invitation to scale is gone"
    assert "Scale this to your taxable portfolio" in src, "the progressive portfolio affordance is gone"
    assert "Illustrative coordination impact" in src


def test_the_impact_figure_is_labelled_as_modeling_wherever_it_appears(src):
    assert "illustrative" in src.lower()
    assert "30-year proxy-spliced path" in src, "the modeling basis is no longer stated"
    assert "not a precise ranking" in src


# ── the prohibitions ──────────────────────────────────────────────────────────────────────────

RANKING_DEVICES = (
    "friction score", "complexity index", "coordination index", "coordination score",
    "out of 5", "/5 dots", "★", "☆",
)


def test_no_ranking_device_anywhere_on_the_workspace(src):
    low = src.lower()
    found = [d for d in RANKING_DEVICES if d.lower() in low]
    assert not found, f"a ranking device reappeared on the workspace: {found}"


def test_the_atlas_says_in_words_that_it_is_not_a_ranking(src):
    assert "The Atlas is not a ranking." in src
    assert "a regime table, not a league table" in src.lower()


def test_the_assessment_does_not_grade_a_household(src):
    assert "No score, no grade" in src, "the Assessment's no-grade promise is gone"
    assert "An inventory, not a grade." in src
    # The earlier iteration's meter, and the segmented bar that drew it. The register names the
    # matters back in words instead; a count of checked boxes is fine, a picture of one is not.
    assert "Coordination surface" not in src, \
        "the coordination-surface meter is back — the Assessment is a ledger, not a diagram"
    assert "v.tally" not in src and "cw-tally" not in src, "the tally meter is back on the Assessment"
    assert "What this household is carrying" in src, \
        "the aside no longer names the matters back in words"


ARCHETYPES = ("The Founder", "The Inheritor", "The Operator", "The Executive", "archetype")


def test_no_archetype_labels_are_used_as_navigation_or_as_a_visual_system(src):
    found = [a for a in ARCHETYPES if a in src]
    assert not found, f"archetype labels reappeared: {found}"


def test_no_moving_here_marketing_blocks(src):
    low = src.lower()
    for phrase in ("if you were moving here", "if you were leaving",
                   "thinking of moving here", "why people move to"):
        assert phrase not in low, f"a relocation marketing block reappeared: {phrase!r}"
    # What replaces them: the move is read as a sequence, and the page declines to recommend one.
    assert "The Atlas does not recommend a move." in src
    assert "A move is a sequence, not a destination." in src


# ── the move brief ────────────────────────────────────────────────────────────────────────────

def test_the_move_reading_is_directional_and_only_shows_what_changes(src):
    assert "What changes at the line" in src
    assert "Only the regimes that differ." in src
    assert "Which side of the line" in src, "the sequencing section is gone from the move brief"
    assert "Unchanged at the line: " in src, "the move reading no longer says what agrees"
    assert "moveRows" in src and "a.regime === b.regime" in src, \
        "the move view no longer filters to the levers that actually differ"


# ── the printable CPA documents ───────────────────────────────────────────────────────────────

def test_three_printable_documents_exist_and_each_is_stamped(src):
    for fn in ("briefDocState", "briefDocCompare", "briefDocMove"):
        assert f"function {fn}(" in src, f"the {fn} document is gone"
    assert 'generatedLine' in src
    assert '"Brief generated "' in src, "the documents no longer stamp a generation date"
    # One stamp helper feeding one header, so a document cannot ship undated.
    assert src.count("function docHead(") == 1
    assert src.count("generatedLine()") >= 1


def test_every_printable_document_carries_the_full_disclosure(src):
    assert "var DISCLOSURE =" in src
    for phrase in ("Educational, not tax, legal, or investment advice.",
                   "no client capital was invested",
                   "does not guarantee future results",
                   "Park Avenue Securities"):
        assert phrase in src, f"the printable disclosure dropped: {phrase!r}"
    # Each of the three documents renders it; none may opt out.
    assert src.count("DISCLOSURE + '</div></div>'") == 3, \
        "a printable document no longer carries the disclosure block"


def test_the_documents_print_without_the_workspace_chrome(src):
    assert "@media print" in src
    assert "[data-noprint]{display:none !important}" in src
    for hook in ('class="cw-chrome" data-noprint', 'class="cw-briefbar" data-noprint'):
        assert hook in src, f"a chrome element is missing its print exclusion: {hook}"


def test_the_cpa_handoff_copies_a_link_that_carries_the_household(src):
    assert "Copy a link for your CPA" in src
    assert "navigator.clipboard" in src
    assert "function hashFor(" in src
    # The minted link has to carry every household field, or the CPA opens a different workspace.
    hash_for = re.search(r"function hashFor\(route\)\{(.*?)\n  \}", src, re.S).group(1)
    for field in ("state=", "drivers=", "port=", "pins=", "move="):
        assert field in hash_for, f"the copied link drops {field!r}"


# ── derived regime notes come from the data, and only where it supports them ──────────────────

DERIVED_NOTES = ("pte", "qsbs", "trailing", "situs", "cliff", "sourcing")


def test_every_derived_regime_note_reads_a_regime_already_in_the_dataset(src):
    ask = re.search(r"function askLine\(key, code\)\{(.*?)\n  \}", src, re.S)
    assert ask, "askLine() has moved — re-check what the derived notes are built from"
    body = ask.group(1)
    for key in DERIVED_NOTES:
        assert f'key === "{key}"' in body, f"the {key} regime note is gone"
    # Only these dimensions may be consulted; a new fact would mean modeling, not deriving.
    consulted = set(re.findall(r"st\.(\w+)", body))
    assert consulted <= {"cg", "estate", "qsbs"}, \
        f"a derived note reads a dimension outside the dataset's regimes: {consulted}"
    # An absent regime yields no sentence rather than a guess.
    assert 'return !qs ? ""' in body and 'return !es ? ""' in body, \
        "a derived note no longer degrades to silence when the data is absent"


def test_the_upgraded_inventory_carries_the_higher_intent_triggers(src):
    """The brief's requirement: still ten factors, but aimed at the households a Coordination Review
    is actually for."""
    factors = re.search(r"var FACTORS = \[(.*?)\n  \];", src, re.S).group(1)
    keys = re.findall(r'\{k:"([^"]+)"', factors)
    assert len(keys) == 10, f"the inventory is {len(keys)} factors, not 10"
    for k in ("qsbs-founder", "equity-comp", "relocation", "business"):
        assert k in keys, f"the {k!r} trigger is missing from the inventory"
    assert "§1202" in factors, "the QSBS trigger no longer names the section it turns on"
    assert "pays material state tax" in factors, "the business trigger lost its materiality qualifier"


def test_the_inventory_slugs_are_registered_with_the_shared_platform(src):
    """A slug the platform does not know is silently dropped by dw-context's cleanKeys(), which is
    how a checked box would vanish on the way to another tool."""
    ctx = (WEB / "dw-context.js").read_text(encoding="utf-8")
    declared = re.search(r"var DRIVER_KEYS = \[(.*?)\];", ctx, re.S).group(1)
    keys = re.findall(r'\{k:"([^"]+)"', re.search(r"var FACTORS = \[(.*?)\n  \];", src, re.S).group(1))
    missing = [k for k in keys if f'"{k}"' not in declared]
    assert not missing, f"inventory slugs unknown to dw-context.js DRIVER_KEYS: {missing}"


def test_retired_driver_slugs_still_resolve_forward(src):
    """A personalized link minted before the inventory was upgraded — or a bookmark, or a link from
    score.html — must restore the visitor's boxes rather than dropping them."""
    legacy = re.search(r"var LEGACY_DRIVERS = \{(.*?)\};", src, re.S)
    assert legacy, "the legacy driver map is gone; pre-upgrade links now lose their checked boxes"
    assert '"multi-state":"relocation"' in legacy.group(1).replace(" ", "")
    assert '"entities":"business"' in legacy.group(1).replace(" ", "")


# ── the Assessment → Review handoff ───────────────────────────────────────────────────────────

def test_the_review_scope_is_built_from_the_checked_inventory(src):
    assert "What this review would examine for your household" in src
    assert "Built from the " in src and "you checked and what " in src
    assert "Nothing here is a finding" in src, "the scope preview no longer disclaims itself"
    assert "Edit the inventory" in src, "there is no way back to the Assessment from the scope"
    # An empty inventory must ask for one rather than rendering an empty list.
    assert "there is nothing to name back" in src


def test_the_review_keeps_the_engagement_intact(src):
    """The Review route replaces nothing about the engagement: the deliverables, the sequence, the
    fit test, and the fee posture all still have to be on it."""
    for phrase in ("The Coordination Report", "The Opportunity Register", "The Wealth Operating Manual",
                   "Your 90-Day Plan", "The Decision Register"):
        assert phrase in src, f"the {phrase!r} deliverable is gone from the Review"
    assert "Warranted when" in src and "Not warranted when" in src
    assert "a defined engagement fee" in src


# ── the frozen design system ──────────────────────────────────────────────────────────────────

def test_the_workspace_uses_the_shared_stylesheet_and_its_tokens(src):
    assert '<link rel="stylesheet" href="driftwood.css">' in src
    for token in ("--accent-strike", "--ink", "--soft", "--frame-line", "--ghost-line", "--serif", "--sans"):
        assert token in src, f"the {token} design token is not used"


def test_surfaces_stay_square(src):
    """Squared corners are the house surface. A stray radius is how a sheet starts looking like a
    card from somewhere else."""
    bad = [m for m in re.findall(r"border-radius:\s*([^;}\"']+)", src)
           if m.strip() not in ("0", "0px", "50%", "var(--surface-radius)")]
    assert not bad, f"non-square surfaces on the workspace: {bad}"


# Class names the workspace shares with the site on purpose: the masthead, the page frame, and the
# footer band are the shared chrome and must keep inheriting driftwood.css.
_SHARED_CHROME = {"sheet", "frame", "foot", "firm-anchor"}


def test_no_workspace_class_silently_inherits_a_site_wide_rule(src):
    """driftwood.css owns a set of short, generic class names — `.stamp`, `.cta`, `.note`, `.tools`
    among them — as unscoped, site-wide rules. This shipped once: the printable brief's header used
    `class="stamp"` and inherited `.stamp{border:1px solid …}`, drawing a box around the edition
    block that nothing in this page's own stylesheet asked for, and `class="cta"` inherited a
    border-radius that rounded a corner the design system freezes square.

    A page-scoped rule (`.cw-doc .cw-stamp{…}`) wins on specificity for the properties it sets and
    silently accepts every property it does not. So the workspace prefixes its own class names
    rather than out-specifying the sheet, and this pins that.
    """
    css = (WEB / "driftwood.css").read_text(encoding="utf-8")
    style = re.search(r"<style>(.*?)</style>", src, re.S).group(1)
    markup = src.replace(style, "")

    used = set()
    for m in re.finditer(r'class=\\?"([a-zA-Z0-9 _-]+)\\?"', markup):
        used.update(m.group(1).split())

    site_wide = set()
    for m in re.finditer(r"(^|[},])\s*([^{}]+?)\{", css, re.M):
        for sel in m.group(2).split(","):
            hit = re.fullmatch(r"\.([a-zA-Z0-9_-]+)(?::[a-z-]+(?:\([^)]*\))?)?", sel.strip())
            if hit:
                site_wide.add(hit.group(1))

    clash = sorted((used & site_wide) - _SHARED_CHROME - {c for c in used if c.startswith("dwnav")})
    assert not clash, (
        f"workspace classes colliding with unscoped driftwood.css rules: {clash} — "
        "prefix them (cw-…) rather than relying on specificity"
    )


def test_the_workspace_carries_the_shared_masthead_and_frame(src):
    assert 'class="dwnav dwnav--phase2"' in src, "the workspace has no masthead"
    assert '<div class="sheet">' in src, "the workspace is not on the shared page frame"
    assert not re.search(r"\.sheet\{[^}]*max-width:\s*\d", src), "the workspace redeclares the frame width"


def test_the_workspace_does_not_ship_a_house_mark(src):
    """The heron is a governed house mark and is currently on no web page (OPERATIONS.md). A new
    surface is exactly where one gets reached for as texture."""
    low = src.read_text().lower() if hasattr(src, "read_text") else src.lower()
    assert "heron" not in low, "the house mark reached the workspace; see OPERATIONS.md"


# ── the built artifact ────────────────────────────────────────────────────────────────────────

def test_the_built_page_embeds_the_same_atlas_payload_as_the_state_tax_atlas(built):
    """One dataset. The workspace's state brief and statemap.html's dimension tabs must never be
    able to disagree about what a state's law is."""
    def payload(text):
        m = re.search(r"window\.__STATE__ = (.*?);\s*\n", text, re.S)
        assert m, "no embedded Atlas payload"
        return json.loads(m.group(1))

    ws = payload(built)
    sm = payload((DOCS / "statemap.html").read_text(encoding="utf-8"))
    assert ws == sm, "the workspace and the State Tax Atlas ship different Atlas data"
    assert len(ws["states"]) == 56 and len(ws["dimensions"]) == 8


def test_the_built_page_resolves_its_build_tokens(built):
    assert "<!--FIRM_ANCHOR-->" not in built, "the workspace shipped a raw build token"
    assert 'class="firm-anchor"' in built, "the firm identity strip is missing from the built page"


def test_the_built_page_is_indexable_and_canonical(built):
    assert 'rel="canonical" href="https://driftwoodwealth.com/coordination-atlas.html"' in built
    assert "noindex" not in built
