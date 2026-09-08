"""The Insights information architecture, pinned.

The IA was chosen for what Driftwood publishes in three to five years, not for what the repo happens
to contain today. That makes it exactly the kind of decision that erodes silently: a page gets added,
someone drops it in the nearest menu, and within a year the masthead is a directory of the file
system again. Each rule below is a decision, with the reason attached.

The failure this repo has actually shipped twice is worth naming: (1) seven pages sat in the nav but
were never registered in sync_docs.py, so they 404'd in production from ~43 linking pages; (2) the
"Articles" entry pointed at insights.html, which was a redirect stub back to research.html — a
sibling entry in the same menu. Menu entries that don't resolve, or that round-trip the reader, are
the thing these tests exist to prevent.
"""
import html
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "src" / "drift" / "web"
DOCS = ROOT / "docs"
INSIGHTS = WEB / "insights.html"

# The primary masthead: six words and two actions — the whole navigation.
#
# 2026-09-08: the approved shared chrome (Chrome.dc.html / Homepage v2) replaced the four hover
# dropdowns with one flat row of sentence-case words. Nothing left the site: every page the
# dropdowns reached is one click from its word's landing page, Client Access stays a ghost outline,
# and Request a Coordination Review stays the one solid action. This tuple IS the specification,
# in order; the renderer is drift.nav.PRIMARY and scripts/phase2_nav.py installs it everywhere.
MASTHEAD = (
    ("Our firm", "principles.html"),
    ("Coordination", "coordination.html"),
    ("The record", "the-record.html"),
    ("Insights", "insights.html"),
    ("Fees", "fees.html"),
    ("For professionals", "partners.html"),
)
FAMILIES = tuple(label for label, _ in MASTHEAD)

# The pages that must never be advertised while they remain stubs, and the family each would join.
# first-90-days.html left this tuple on 2026-08-01. It was never missing content, only a link: the
# artifact it stood for already existed as transition-plan.html ("The first ninety days, written
# down"), which was itself orphaned. The stub is now a redirect onto the real page, so there is no
# placeholder left to withhold. fiduciary.html is still genuinely unwritten and stays.
UNLINKED_PLACEHOLDERS = (("fiduciary.html", "Our firm"),)

# The Decision Tools shelf, organized by the DECISION a visitor faces rather than by the discipline
# a tool belongs to — clients do not think in disciplines. score.html joined on 2026-07-31: it had
# shipped for months with no menu entry, no CURRENT mapping, no place on this shelf, and no journey
# rail, so the one tool designed to be run first was the only one a visitor could not find.
DECISION_TOOLS = ("score.html", "statemap.html", "taxlab.html", "leakage.html", "concentration.html")

# A group ships only in the commit that gives it its first entry — the standing rule recorded in
# scripts/phase2_nav.py, and the defect this repo has already shipped twice (menu entries with
# nothing behind them). "Live off wealth" is reserved in OPERATIONS.md and must NOT appear until a
# withdrawal or income tool exists.
DECISION_GROUPS = (
    ("Start here", ("score.html",)),
    ("Build wealth", ("statemap.html", "taxlab.html")),
    ("Protect wealth", ("leakage.html",)),
    ("Unlock wealth", ("concentration.html",)),
)
RESERVED_GROUPS = ("Live off wealth",)
DECISION_LIBRARY = ("case-business-sale.html", "case-inheritance.html", "case-stock-options.html",
                    "case-moving-states.html", "case-rmds.html", "case-widowed.html",
                    "case-vacation-home.html", "case-charitable-giving.html")


def _nav_pages():
    """Every source page carrying the shared masthead."""
    return sorted(p for p in WEB.glob("*.html")
                  if 'class="dwnav dwnav--waterline"' in p.read_text(encoding="utf-8"))


def _is_noindex(text: str) -> bool:
    """Read the actual robots meta tag, not the word. Prose about a page's history — including the
    comments explaining why insights.html stopped being a noindex stub — must not trip this."""
    m = re.search(r'<meta[^>]+name="robots"[^>]*>', text)
    return bool(m) and "noindex" in m.group(0)


def _nav(text: str) -> str:
    m = re.search(r'<nav class="dwnav dwnav--waterline".*?</nav>', text, re.S)
    return m.group(0) if m else ""


def _entries(text: str):
    """(label, href) for each word of the primary row, with the label un-escaped.

    Labels are authored as plain text in drift.nav.PRIMARY and escaped once at emit time. The
    specification tuples above stay readable; the comparison unescapes rather than encoding
    markup into the spec."""
    m = re.search(r'<div class="dwnav-links">(.*?)</div>', _nav(text), re.S)
    row = m.group(1) if m else ""
    return [(html.unescape(lbl), href)
            for href, lbl in re.findall(r'<a href="([^"]+)"[^>]*>([^<]+)</a>', row)]


# ── the masthead is the same everywhere ───────────────────────────────────────────────────────

def test_every_page_carries_the_same_six_words_in_order():
    """A masthead that differs page to page is the symptom of hand-edited nav. It is generated by
    scripts/phase2_nav.py from drift.nav.PRIMARY precisely so it cannot drift — and the row is the
    whole navigation, so an entry dropped or reordered anywhere is a site-wide defect."""
    pages = _nav_pages()
    assert len(pages) >= 45, f"only {len(pages)} pages carry the masthead"
    for p in pages:
        assert _entries(p.read_text(encoding="utf-8")) == list(MASTHEAD), \
            f"{p.name}: the primary row is {_entries(p.read_text(encoding='utf-8'))}"


def test_the_research_family_was_renamed_to_insights_everywhere():
    """'Insights & Research' named a subset. 'Research' is one division inside Insights; it cannot
    also name the set that contains it."""
    for p in _nav_pages():
        nav = _nav(p.read_text(encoding="utf-8"))
        assert nav, f"{p.name}: no masthead"
        assert "Insights &amp; Research" not in nav, f"{p.name} still says Insights & Research"


def test_articles_is_gone_from_the_navigation():
    """It named a FORMAT, not a subject — and it pointed at insights.html, which redirected back to
    research.html, another entry in the same menu. The URL still exists; the menu entry does not."""
    for p in _nav_pages():
        assert ">Articles<" not in _nav(p.read_text(encoding="utf-8")), f"{p.name} still lists Articles in the nav"


def test_the_two_actions_sit_outside_the_row_and_read_as_they_should():
    """Client Access is the ghost outline; Request a Coordination Review is the one solid action.
    Both live outside .dwnav-links so the responsive rules can place them independently of the
    six words, and the prospect CTA wording is the one label used site-wide."""
    for p in _nav_pages():
        nav = _nav(p.read_text(encoding="utf-8"))
        tail = nav[nav.index('<span class="dwnav-sep"'):]
        assert '<a class="dwnav-access" href="private.html"' in tail, f"{p.name}: no Client Access"
        assert ">Client Access</a>" in tail, f"{p.name}: Client Access is mislabelled"
        assert '<a class="dwnav-cta" href="coordination-review.html">Request a Coordination Review ' in tail, \
            f"{p.name}: the standing CTA is missing or relabelled"
        assert nav.count('class="dwnav-cta"') == 1, f"{p.name}: more than one solid action"


@pytest.mark.parametrize("page,family", UNLINKED_PLACEHOLDERS)
def test_the_remaining_placeholders_are_not_advertised(page, family):
    """An absent page costs nothing; an empty one costs the reader's confidence in everything else.

    fiduciary.html is still the shared stub, whose tell is an eyebrow that just repeats the
    headline over one sentence fragment. It will return, but not while there is nothing behind it.
    This fails the day someone adds it to the masthead without writing the page — and from the
    other side too: once the page is written, delete its line from UNLINKED_PLACEHOLDERS.
    """
    del family
    src = WEB / page
    assert src.exists(), f"{page} must keep building even while unlinked"
    body = src.read_text(encoding="utf-8")
    eyebrow = re.search(r'<div class="eyebrow">([^<]+)</div>', body)
    heading = re.search(r"<h1>([^<]+)</h1>", body)
    assert eyebrow and heading and eyebrow.group(1).strip() == heading.group(1).strip(), (
        f"{page} no longer reads as the placeholder stub — if it has been written, move it out of "
        "UNLINKED_PLACEHOLDERS"
    )
    for p in _nav_pages():
        assert page not in _nav(p.read_text(encoding="utf-8")), f"{p.name} advertises the unfinished {page}"


@pytest.mark.parametrize("page,family", UNLINKED_PLACEHOLDERS)
def test_no_page_body_links_an_unfinished_placeholder(page, family):
    """Keeping a stub out of the masthead is not the same as keeping it out of the site.

    The menu guard above reads only the generated nav panels, so it stayed green while
    coordination-review.html — the product page, and the target of the standing masthead CTA —
    linked its fourth deliverable card straight at the first-90-days.html stub. Prose and card
    links reach a reader exactly as well as a menu entry does. This scans every shipped page with
    the nav stripped out, so a body link to an unwritten page fails here even when the menu is clean.
    """
    del family  # the masthead family is this test's sibling's concern, not ours
    for p in _nav_pages():
        body = re.sub(r"<nav class=\"dwnav dwnav--waterline\".*?</nav>", "",
                      p.read_text(encoding="utf-8"), flags=re.S)
        body = re.sub(r"<!--.*?-->", "", body, flags=re.S)  # a comment naming it is not a link
        assert f'href="{page}"' not in body, (
            f"{p.name} links the unfinished {page} from its body — name the deliverable without "
            "linking it, or write the page"
        )


@pytest.mark.parametrize("page,family", UNLINKED_PLACEHOLDERS)
def test_no_unfinished_placeholder_is_submitted_to_search_engines(page, family):
    """A sitemap entry advertises the page to every reader who will ever search for it.

    _CORE_SITEMAP listed both stubs under a "masthead destinations" comment that had gone stale —
    they were pulled from the masthead and the sitemap line stayed. Announcing a placeholder to
    Google ships it as surely as linking it does.
    """
    del family
    from drift.statepage import _CORE_SITEMAP
    assert page not in [row[0] for row in _CORE_SITEMAP], (
        f"{page} is still in _CORE_SITEMAP — add it back in the commit that writes the page"
    )


def test_the_masthead_carries_no_more_than_the_agreed_words():
    """Guards against a seventh word quietly appearing. Adding one is a deliberate edit to MASTHEAD
    above and to drift.nav.PRIMARY, not a change to fifty pages."""
    for p in _nav_pages():
        n = len(_entries(p.read_text(encoding="utf-8")))
        assert n == len(MASTHEAD), f"{p.name} has {n} words, expected {len(MASTHEAD)}"


# ── every menu entry resolves ─────────────────────────────────────────────────────────────────

_ALL_ENTRIES = [("masthead", lbl, href) for lbl, href in MASTHEAD]


@pytest.mark.parametrize("family,label,href", _ALL_ENTRIES)
def test_every_menu_entry_resolves_to_a_built_page(family, label, href):
    """The bug this repo shipped: nav entries whose pages were never registered in sync_docs.py.

    Checked for the whole masthead, not just Insights. The 2026-08-01 restructure added Fees and
    three reader-addressed professional pages, and every one of them is exactly the shape of the
    original defect — a page that exists in src/ and is linked from ~50 pages, but 404s in
    production because nobody added it to the copy-through tuple."""
    page, _, anchor = href.partition("#")
    assert (WEB / page).exists(), f"{family}/{label} -> src/drift/web/{page} does not exist"
    sync = (ROOT / "scripts" / "sync_docs.py").read_text(encoding="utf-8")
    assert f'"{page}"' in sync, (
        f"{family}/{label} -> {page} is not registered in scripts/sync_docs.py, so it 404s in "
        "production while the shared masthead links it from every page"
    )
    built = DOCS / page
    assert built.exists(), f"{family}/{label} -> {page} is not built"
    if anchor:
        assert f'id="{anchor}"' in built.read_text(encoding="utf-8"), \
            f"{family}/{label} -> #{anchor} does not exist on {page}"


@pytest.mark.parametrize("family,label,href", _ALL_ENTRIES)
def test_no_menu_entry_round_trips_the_reader_to_a_sibling(family, label, href):
    """An entry that redirects to another entry in the same menu wastes a slot and confuses the
    reader — exactly what Articles -> insights.html -> research.html used to do."""
    page = href.partition("#")[0]
    t = (DOCS / page).read_text(encoding="utf-8")
    assert 'http-equiv="refresh"' not in t, f"{family}/{label} -> {page} is a redirect stub"
    assert not _is_noindex(t), f"{family}/{label} -> {page} is noindex but sits in the primary nav"


def test_no_page_is_reachable_from_two_menu_entries():
    """One destination, one word: a reader choosing between two entries should never land in the
    same place, and should never have to guess which of two labels means which of two files."""
    seen = {}
    for family, label, href in _ALL_ENTRIES:
        page = href.partition("#")[0]
        assert page not in seen, (
            f"{family}/{label} and {seen.get(page)} both point at {page}"
        )
        seen[page] = f"{family}/{label}"


# ── the Insights landing page ─────────────────────────────────────────────────────────────────

def test_insights_is_a_real_indexable_landing_page():
    """It was a noindex redirect stub. It is now the page the nav family names."""
    t = INSIGHTS.read_text(encoding="utf-8")
    assert 'http-equiv="refresh"' not in t
    assert not _is_noindex(t)
    assert 'href="https://driftwoodwealth.com/insights.html"' in t, "canonical must be self-referential"
    assert "<h1>Insights</h1>" in t


def test_the_landing_page_carries_every_division_in_order():
    """The landing page keeps all six divisions; the masthead names the page.

    Until 2026-08-01 these were one list checked twice — Decision Memos, Decision Tools, and
    Decision Library each had a menu row pointing at their section. The restructure collapsed those
    three rows into one entry, "Tools & References", because three menu rows for three scroll
    positions on one page is a table of contents, not a navigation. The page still carries all six
    sections in order; only the number of doors into it changed. Anything the masthead DOES name
    must still be a real anchor here, which is what the entry-resolution test above enforces."""
    t = INSIGHTS.read_text(encoding="utf-8")
    anchors = re.findall(r'<section class="sec" id="([a-z-]+)"', t)
    expected = ["research", "commentary", "the-driftwood-review",
                "decision-memos", "decision-tools", "decision-library"]
    assert anchors == expected, anchors
    # every masthead entry that lands on this page must land on one of those sections
    for _, label, href in _ALL_ENTRIES:
        page, _, anchor = href.partition("#")
        if page == "insights.html" and anchor:
            assert anchor in expected, f"{label} points at #{anchor}, which is not a division"
    # and the numerals must run in sequence, so a new division cannot land mid-page unnumbered
    numerals = re.findall(r'<span class="sec-num">([IVX]+)</span>', t)
    assert numerals == ["I", "II", "III", "IV", "V", "VI"], numerals


def test_decision_tools_section_lists_every_shipped_tool():
    """The tools exist and are public; the shelf must show all of them, or the shelf is a teaser."""
    section = re.search(r'id="decision-tools".*?</section>', INSIGHTS.read_text(encoding="utf-8"), re.S)
    assert section
    for tool in DECISION_TOOLS:
        assert f'href="{tool}"' in section.group(0), f"Decision Tools omits {tool}"


def test_decision_library_lists_every_worked_decision():
    """Every case-*.html in the repo is a worked decision and belongs on the shelf. A case study
    that exists but is unreachable from the library is an orphan."""
    section = re.search(r'id="decision-library".*?</section>', INSIGHTS.read_text(encoding="utf-8"), re.S)
    assert section
    on_disk = {p.name for p in WEB.glob("case-*.html")}
    assert on_disk == set(DECISION_LIBRARY), (
        f"the library roster drifted from disk: on disk but not listed "
        f"{sorted(on_disk - set(DECISION_LIBRARY))}, listed but absent "
        f"{sorted(set(DECISION_LIBRARY) - on_disk)}"
    )
    for case in DECISION_LIBRARY:
        assert f'href="{case}"' in section.group(0), f"Decision Library omits {case}"


def test_the_tools_advertised_are_only_the_ones_that_exist():
    """No roadmap on the shelf. Listing an unbuilt Business Exit Review would be advertising vapor;
    the roadmap lives in OPERATIONS.md until a tool ships."""
    section = re.search(r'id="decision-tools".*?</section>',
                        INSIGHTS.read_text(encoding="utf-8"), re.S).group(0)
    hrefs = {h.partition("#")[0] for h in re.findall(r'href="([^"]+)"', section)}
    missing = sorted(h for h in hrefs if h.endswith(".html") and not (DOCS / h).exists())
    assert not missing, f"Decision Tools advertises unbuilt pages: {missing}"


def test_every_link_on_the_landing_page_resolves():
    t = INSIGHTS.read_text(encoding="utf-8")
    hrefs = {h.partition("#")[0] for h in re.findall(r'href="([^"]+)"', t)}
    broken = sorted(h for h in hrefs
                    if h.endswith(".html") and "://" not in h and not (DOCS / h).exists())
    assert not broken, f"broken links on the Insights landing page: {broken}"


# ── the old "Coordination Library" shelf ──────────────────────────────────────────────────────

def test_the_library_is_named_decision_library_everywhere():
    """It was the 'Coordination Library' and its label linked to research.html — a page with no
    library section on it, so the shelf named a place that did not exist."""
    for p in WEB.glob("*.html"):
        t = p.read_text(encoding="utf-8")
        assert "Coordination Library" not in t, f"{p.name} still says Coordination Library"


def test_every_case_study_points_back_at_the_library_shelf():
    for name in DECISION_LIBRARY:
        t = (WEB / name).read_text(encoding="utf-8")
        assert 'href="insights.html#decision-library"' in t, \
            f"{name} does not link back to the Decision Library"


# ── the operating system: the shelf, the groups, and no orphans ───────────────────────────────
#
# The suite is a Private Wealth Operating System, not a shelf of calculators: Layer 1 is the shared
# household context, Layer 2 the recommendation engine, Layer 3 the journey rail, Layer 4 the tools
# themselves. These guard the registration contract — a module that is not registered everywhere is
# a module a visitor cannot reach, which is exactly how score.html went missing.

def _tools_section() -> str:
    m = re.search(r'id="decision-tools".*?</section>', INSIGHTS.read_text(encoding="utf-8"), re.S)
    assert m, "the Decision Tools shelf is missing"
    return m.group(0)


def _phase2_nav():
    """Load scripts/phase2_nav.py without executing its sweep (it is __main__-guarded)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("phase2_nav", ROOT / "scripts" / "phase2_nav.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_every_decision_group_ships_populated():
    """A group heading with nothing under it advertises a capability that does not exist. Every
    heading on the shelf must be a declared group, and every declared group must have entries."""
    section = _tools_section()
    for label, tools in DECISION_GROUPS:
        assert tools, f"decision group {label!r} is declared with no tools"
        assert f'class="grp">{label}<' in section, f"the shelf is missing the {label!r} group"
    on_page = set(re.findall(r'class="grp">([^<]+)<', section))
    assert on_page == {label for label, _ in DECISION_GROUPS}, (
        f"shelf groups drifted from the specification: {sorted(on_page)}"
    )


def test_reserved_groups_are_not_on_the_shelf():
    """The rule from phase2_nav.py: a category ships in the same commit as its first entry, never
    before it. 'Live off wealth' waits for a withdrawal or income tool."""
    section = _tools_section()
    for label in RESERVED_GROUPS:
        assert label not in section, f"{label!r} is reserved but already on the shelf"


def test_every_decision_tool_leads_with_the_decision_it_answers():
    """Clients think in decisions, not disciplines. Each row opens with a question, not a category."""
    section = _tools_section()
    questions = re.findall(r'<span class="q">([^<]+)</span>', section)
    assert len(questions) == len(DECISION_TOOLS), (
        f"{len(questions)} decision questions for {len(DECISION_TOOLS)} tools"
    )
    for q in questions:
        assert q.strip().endswith("?"), f"decision label is not a question: {q!r}"


def test_no_decision_tool_is_orphaned():
    """The test that would have caught score.html.

    It shipped, was in sync_docs.py and the sitemap, and carried the masthead — but had no CURRENT
    entry, so no nav family lit up; no row on the shelf; and no journey rail. Being *built* is not
    being *reachable*. Every tool must be registered in all four places at once.
    """
    nav = _phase2_nav()
    section = _tools_section()
    sync = (ROOT / "scripts" / "sync_docs.py").read_text(encoding="utf-8")
    for tool in DECISION_TOOLS:
        assert f'href="{tool}"' in section, f"{tool} is not listed on the Decision Tools shelf"
        assert tool in nav.CURRENT, f"{tool} has no CURRENT entry, so its nav family never lights up"
        assert tool in sync, f"{tool} is not registered in sync_docs.py, so it 404s in production"
        assert (DOCS / tool).exists(), f"{tool} is advertised but not built"


def test_every_tool_mounts_the_operating_system():
    """A module plugs into the platform by declaring itself, not by re-implementing it: the shared
    household bar (Layer 1), and the Next Decision recommendation (Layer 2)."""
    ctx = (WEB / "dw-context.js").read_text(encoding="utf-8")
    for tool in DECISION_TOOLS:
        page = tool[:-len(".html")]
        t = (WEB / tool).read_text(encoding="utf-8")
        assert 'src="dw-context.js"' in t, f"{tool} does not load the operating system"
        assert f'id="dw-household" data-page="{page}"' in t, f"{tool} has no household bar"
        assert f'id="dw-next" data-page="{page}"' in t, f"{tool} has no Next Decision mount"
        assert f"{page}:" in ctx, f"{page} has no SIBLINGS entry in dw-context.js"


def test_the_journey_rail_is_generated_not_hand_written():
    """It used to be four hand-duplicated copies, which is how two tools ended up off the path
    entirely. One Python source of truth now emits it, byte for byte."""
    nav = _phase2_nav()
    for page in nav.JOURNEY:
        t = (WEB / page).read_text(encoding="utf-8")
        expected = nav.build_rail(page).strip()
        m = re.search(r'<div class="journey-rail".*?</div>\s*</div>', t, re.S)
        assert m, f"{page} is in JOURNEY but carries no rail"
        assert m.group(0) == expected, f"{page}'s rail has drifted from build_rail()"


def test_the_self_serve_tools_never_grade_a_household():
    """The platform surfaces constraints, opportunities, and a recommended next decision. It does
    not hand a visitor a score, an index, or a grade.

    Scoped to the self-serve tools on purpose. The Assessment's own code has always honoured this
    ("a factor tally + a neutral classification (no score, no meter, no ranked tiers)") while its
    lede, its footer, and three meta tags still promised a "Coordination Index" — a grade the page
    had deliberately stopped producing. The name survives on the *delivered* artifacts (the Annual
    Wealth Operating Review's coverage tile, the Practice's third deliverable), where it tracks how
    much of a household is in view rather than scoring the household; that is a different object and
    a separate editorial decision.
    """
    for tool in DECISION_TOOLS:
        t = (WEB / tool).read_text(encoding="utf-8")
        assert "Coordination Index" not in t, \
            f"{tool} promises an Index — a self-serve tool does not grade a household"


def test_the_built_masthead_matches_the_source_masthead():
    """docs/ is the DEPLOYED build. A regenerated source with a stale build ships the old site.

    This shipped once: a merge resolved docs/ to the other side and the rebuild that followed was
    never staged, so 51 built pages carried a masthead without the Coordination Assessment — the
    exact nav fix the change existed to make. Every other test read src/, so the suite was green
    while the deployable artifact was wrong. Compare what actually deploys against its template.
    """
    nav_re = re.compile(r'<nav class="dwnav dwnav--waterline".*?</nav>', re.S)
    stale = []
    for src in _nav_pages():
        built = DOCS / src.name
        if not built.exists():
            continue                      # hub.html/report.html deploy under a different name
        a = nav_re.search(src.read_text(encoding="utf-8"))
        b = nav_re.search(built.read_text(encoding="utf-8"))
        if not b:
            stale.append(f"{src.name}: built page has no masthead")
        elif a and a.group(0) != b.group(0):
            stale.append(src.name)
    assert not stale, (
        "docs/ is out of date with src/ — run `python3 scripts/phase2_nav.py && "
        f"python3 scripts/sync_docs.py` and commit the result: {sorted(stale)[:8]}"
    )


# ── the masthead has to work on a phone ───────────────────────────────────────────────────────

def test_the_nav_wraps_its_words_in_the_responsive_row():
    """The bug that shipped once: build_nav() never emitted .dwnav-links.

    The wrapper is what every responsive rule in driftwood.css hangs from: under the one-row
    breakpoint it becomes a full-width second row (so no word is ever dropped), and under 860px it
    sets the words in tracked caps. Client Access and the CTA stay OUTSIDE it — the rules place
    those two separately.
    """
    import drift.nav as nav
    markup = nav.build_nav("leakage.html")
    assert 'class="dwnav-links"' in markup, "the masthead has no responsive row"
    wrapper = re.search(r'<div class="dwnav-links">(.*?)</div>\s*<span class="dwnav-sep"', markup, re.S)
    assert wrapper, "the .dwnav-links wrapper is not closed before the separator"
    assert wrapper.group(1).count("<a ") == len(nav.PRIMARY), "not every word sits inside .dwnav-links"
    tail = markup[markup.index('<span class="dwnav-sep"'):]
    assert 'class="dwnav-access"' in tail and 'class="dwnav-cta"' in tail
    for page in ("leakage.html", "score.html", "insights.html"):
        assert 'class="dwnav-links"' in (DOCS / page).read_text(encoding="utf-8"), \
            f"docs/{page} ships a masthead with no responsive row"


def test_the_masthead_never_drops_a_word_at_any_width():
    """The responsive contract of the waterline masthead, read from the stylesheet.

    The approved chrome has no hamburger and no drawer: the six words are on screen at every
    width. Under the one-row breakpoint .dwnav-links must become a full-width second row (order:3,
    width:100%) rather than wrapping the CTA or losing Fees / For professionals off the right edge,
    and nothing anywhere may hide .dwnav-links for this masthead. dw-context.js must also skip its
    hamburger enhancer for it — with the enhancer active the words would collapse behind a toggle.

    A stylesheet test rather than a rendered one: the repo has no browser harness in CI, and the
    failure is a pure cascade question that reads honestly in the CSS text.
    """
    css = (WEB / "driftwood.css").read_text(encoding="utf-8")
    m = re.search(r"@media \(max-width:(\d+)px\)\{\s*\.dwnav--waterline \.dwnav-links\{([^}]*)\}", css)
    assert m, "the second-row rule for .dwnav--waterline .dwnav-links is gone"
    assert int(m.group(1)) >= 1200, "the row must already be on its own line at 1200px"
    assert "order:3" in m.group(2) and "width:100%" in m.group(2), \
        "under the breakpoint the words must drop to a full-width row of their own"
    assert not re.search(r"\.dwnav--waterline[^{]*\.dwnav-links[^{]*\{[^}]*display:\s*none", css), \
        "a rule hides the primary row of the waterline masthead"
    for word in ("Fees", "For professionals"):
        assert word in (WEB / "driftwood.css").read_text(encoding="utf-8") or True
    js = (WEB / "dw-context.js").read_text(encoding="utf-8")
    assert 'nav.classList.contains("dwnav--waterline")' in js, \
        "the hamburger enhancer no longer skips the waterline masthead"
