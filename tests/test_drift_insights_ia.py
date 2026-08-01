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

# The primary masthead. Four families and two actions — the whole navigation.
FAMILIES = ("Our Firm", "Coordination", "Insights", "For Professionals")

# The whole masthead, in order. This tuple IS the specification.
#
# 2026-08-01: organised BY READER rather than by artifact, cutting twenty destinations to thirteen.
# Fees enters (it was among the strongest pages on the site and reachable from exactly one other
# page); Coordination sheds the four instruments to Insights → Tools & References; the two
# near-homonyms whose labels inverted their filenames merge into "How Coordination Works", which
# points at coordination-framework.html — the page that actually enumerates the seven systems.
#
# TWO APPROVED ENTRIES ARE DELIBERATELY ABSENT. "Fiduciary Standard" (Our Firm) and "Your First 90
# Days" (Coordination) are in the signed-off mockup but are NOT in this tuple, because
# fiduciary.html and first-90-days.html are still the shared placeholder stub. The mockup describes
# the end state; "no placeholders ship" governs what ships today, and an entry with nothing behind
# it is the exact defect this file exists to prevent. Each returns to its family in the same commit
# that writes its page — the rule Decision Memos already followed.
MASTHEAD = (
    ("Our Firm", (
        ("Our Story", "principles.html"),
        ("Leadership", "leadership.html"),
        ("Fees", "fees.html"),
    )),
    ("Coordination", (
        ("How Coordination Works", "coordination-framework.html"),
        ("A Household, Coordinated", "household-example.html"),
        ("The Coordination Review", "coordination-review.html"),
    )),
    ("Insights", (
        ("Research", "research.html"),
        ("Commentary", "commentary.html"),
        ("The Driftwood Review", "driftwood-review.html"),
        # One entry, not three. Decision Memos / Tools / Library were three rows pointing at three
        # scroll positions on one page. This lands on the section that enumerates the instruments.
        ("Tools & References", "insights.html#decision-tools"),
    )),
    ("For Professionals", (
        ("For CPAs", "partners.html"),
        ("For Estate Attorneys", "estate-attorneys.html"),
        ("Making a Referral", "referral.html"),
    )),
)

# The pages that must never be advertised while they remain stubs, and the family each would join.
UNLINKED_PLACEHOLDERS = (("fiduciary.html", "Our Firm"), ("first-90-days.html", "Coordination"))

# Inside Insights, in this order — the slice of MASTHEAD the rest of this file leans on.
INSIGHTS_CHILDREN = dict(MASTHEAD)["Insights"]

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
    """Every source page carrying the shared Phase-2 masthead."""
    return sorted(p for p in WEB.glob("*.html")
                  if 'class="dwnav dwnav--phase2"' in p.read_text(encoding="utf-8"))


def _is_noindex(text: str) -> bool:
    """Read the actual robots meta tag, not the word. Prose about a page's history — including the
    comments explaining why insights.html stopped being a noindex stub — must not trip this."""
    m = re.search(r'<meta[^>]+name="robots"[^>]*>', text)
    return bool(m) and "noindex" in m.group(0)


def _panel(text: str, family: str) -> str:
    """The dropdown panel markup for one family on one page."""
    m = re.search(
        r'>%s<span class="caret"[^>]*></span></button><div class="dwnav-panel">(.*?)</div>'
        % re.escape(family), text, re.S)
    return m.group(1) if m else ""


def _entries(panel: str):
    """(label, href) for each row of a panel, with the label un-escaped.

    Labels are authored as plain text in phase2_nav.FAMILIES and escaped once at emit time, so
    "Tools & References" ships as "Tools &amp; References". The specification tuples above stay
    readable; the comparison unescapes rather than encoding markup into the spec."""
    return [(html.unescape(lbl), href)
            for href, lbl in re.findall(r'<a href="([^"]+)"[^>]*>([^<]+)</a>', panel)]


# ── the masthead is the same everywhere ───────────────────────────────────────────────────────

def test_every_page_carries_the_same_four_families():
    """A masthead that differs page to page is the symptom of hand-edited nav. It is generated by
    scripts/phase2_nav.py precisely so it cannot drift."""
    pages = _nav_pages()
    assert len(pages) >= 45, f"only {len(pages)} pages carry the masthead"
    for p in pages:
        t = p.read_text(encoding="utf-8")
        for fam in FAMILIES:
            assert f'>{fam}<span class="caret"' in t, f"{p.name} is missing the {fam!r} family"


def test_the_research_family_was_renamed_to_insights_everywhere():
    """'Insights & Research' named a subset. 'Research' is one division inside Insights; it cannot
    also name the set that contains it."""
    for p in _nav_pages():
        t = p.read_text(encoding="utf-8")
        nav = re.search(r"<nav class=\"dwnav dwnav--phase2\".*?</nav>", t, re.S)
        assert nav, f"{p.name}: no masthead"
        assert "Insights &amp; Research" not in nav.group(0), f"{p.name} still says Insights & Research"


def test_articles_is_gone_from_the_navigation():
    """It named a FORMAT, not a subject — and it pointed at insights.html, which redirected back to
    research.html, another entry in the same menu. The URL still exists; the menu entry does not."""
    for p in _nav_pages():
        nav = re.search(r"<nav class=\"dwnav dwnav--phase2\".*?</nav>",
                        p.read_text(encoding="utf-8"), re.S).group(0)
        assert ">Articles<" not in nav, f"{p.name} still lists Articles in the nav"


def test_insights_holds_exactly_the_agreed_divisions_in_order():
    for p in _nav_pages():
        panel = _panel(p.read_text(encoding="utf-8"), "Insights")
        assert panel, f"{p.name}: no Insights panel"
        assert _entries(panel) == list(INSIGHTS_CHILDREN), \
            f"{p.name}: Insights panel is {_entries(panel)}"


@pytest.mark.parametrize("family,children", MASTHEAD)
def test_every_family_holds_exactly_the_agreed_entries_in_order(family, children):
    """The whole masthead is pinned, not just Insights.

    The 2026-08-01 restructure moved entries BETWEEN families (the four instruments left
    Coordination for Insights), which a per-family check on one family cannot see: an entry deleted
    here and re-added there passes any test that only counts one drawer."""
    for p in _nav_pages():
        panel = _panel(p.read_text(encoding="utf-8"), family)
        assert panel, f"{p.name}: no {family!r} panel"
        assert _entries(panel) == list(children), f"{p.name}: {family} panel is {_entries(panel)}"


@pytest.mark.parametrize("page,family", UNLINKED_PLACEHOLDERS)
def test_the_remaining_placeholders_are_not_advertised(page, family):
    """An absent page costs nothing; an empty one costs the reader's confidence in everything else.

    fiduciary.html and first-90-days.html are still the shared stub, whose tell is an eyebrow that
    just repeats the headline over one sentence fragment. They are approved menu entries in the
    mockup and they will return, but not while there is nothing behind them. This fails the day
    someone adds the row back without writing the page — and from the other side too: once the page
    is written, delete its line from UNLINKED_PLACEHOLDERS and add it to MASTHEAD in one commit.
    """
    src = WEB / page
    assert src.exists(), f"{page} must keep building even while unlinked"
    body = src.read_text(encoding="utf-8")
    eyebrow = re.search(r'<div class="eyebrow">([^<]+)</div>', body)
    heading = re.search(r"<h1>([^<]+)</h1>", body)
    assert eyebrow and heading and eyebrow.group(1).strip() == heading.group(1).strip(), (
        f"{page} no longer reads as the placeholder stub — if it has been written, move it out of "
        "UNLINKED_PLACEHOLDERS and into MASTHEAD"
    )
    for p in _nav_pages():
        panel = _panel(p.read_text(encoding="utf-8"), family)
        assert page not in panel, f"{p.name} advertises the unfinished {page} in {family}"


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
        body = re.sub(r"<nav class=\"dwnav dwnav--phase2\".*?</nav>", "",
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


def test_the_masthead_carries_no_more_than_the_agreed_families():
    """Guards against a sixth family quietly appearing. Adding one is a deliberate edit to FAMILIES
    above, not a change to fifty pages."""
    for p in _nav_pages():
        nav = re.search(r"<nav class=\"dwnav dwnav--phase2\".*?</nav>",
                        p.read_text(encoding="utf-8"), re.S).group(0)
        n = nav.count('class="dwnav-trigger"')
        assert n == len(FAMILIES), f"{p.name} has {n} families, expected {len(FAMILIES)}"


# ── every menu entry resolves ─────────────────────────────────────────────────────────────────

_ALL_ENTRIES = [(fam, lbl, href) for fam, kids in MASTHEAD for lbl, href in kids]


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
    """Twenty destinations became thirteen partly because two rows pointed at near-identical pages.
    One destination, one row: a reader choosing between two entries should never land in the same
    place, and should never have to guess which of two labels means which of two files."""
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
    """The landing page keeps all six divisions; the masthead now names four of them.

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
    nav_re = re.compile(r'<nav class="dwnav dwnav--phase2".*?</nav>', re.S)
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

def test_the_nav_wraps_its_families_in_the_mobile_disclosure_hook():
    """The bug that shipped: build_nav() never emitted .dwnav-links.

    That one missing element broke the masthead on every viewport under 1200px, and nothing caught
    it because every other nav test asserts on families and hrefs, which were all present and
    correct. The failure was structural:

      * dw-context.js's disclosure enhancer does `nav.querySelector(".dwnav-links")` and returns
        early when it is missing, so the hamburger was never injected and .dwnav--menu — the class
        every mobile rule in driftwood.css is scoped to — was never added.
      * .dwnav-panel is display:none by default, revealed only by .dwnav-drop--open (desktop only;
        open() is a no-op below 1200px) or .dwnav--menu.dwnav--open. With neither reachable, all
        four family triggers were dead buttons on a phone and ~20 destinations had no route.

    The CSS had always styled .dwnav-links at both breakpoints. Only the generator disagreed.
    """
    nav = _phase2_nav()
    markup = nav.build_nav("leakage.html")
    assert 'class="dwnav-links"' in markup, "the masthead has no mobile disclosure hook"

    # Every family must sit INSIDE the wrapper — that is what the enhancer toggles.
    wrapper = re.search(r'<div class="dwnav-links">(.*?)</div>\s*<span class="dwnav-sep"', markup, re.S)
    assert wrapper, "the .dwnav-links wrapper is not closed before the separator"
    assert wrapper.group(1).count('class="dwnav-drop') == len(nav.FAMILIES), \
        "not every nav family sits inside .dwnav-links"

    # Client Access and the CTA must stay OUTSIDE it: the mobile rules target them separately.
    tail = markup[markup.index('<span class="dwnav-sep"'):]
    assert 'class="dwnav-access"' in tail and 'class="dwnav-cta"' in tail

    # And it has to survive into the built pages, not just the generator.
    for page in ("leakage.html", "score.html", "insights.html"):
        assert 'class="dwnav-links"' in (DOCS / page).read_text(encoding="utf-8"), \
            f"docs/{page} ships a masthead with no mobile disclosure hook"


def test_the_collapsed_mobile_masthead_hides_the_index():
    """The follow-up bug, and the assertion the first fix was missing.

    Emitting .dwnav-links got the hamburger injected, but the index stayed on screen beside it: the
    generic `.dwnav--menu .dwnav-links{display:none}` collapse rule is overridden by
    `.dwnav--phase2 .dwnav-links{display:flex}`, which is declared unconditionally further down the
    stylesheet — identical specificity, later in the cascade. The result was the worst of both
    states: four family headers AND a hamburger, with the headers inert, because opening a panel
    needs .dwnav--open and only the hamburger sets it.

    The first fix passed its own checks because they measured nav HEIGHT (still one row, 85px) and
    the presence of the toggle. Neither notices that the families never went away. This asserts the
    collapse itself.

    A stylesheet test rather than a rendered one: the repo has no browser harness in CI, and the
    failure is a pure cascade question that reads honestly in the CSS text.
    """
    css = (WEB / "driftwood.css").read_text(encoding="utf-8")

    def in_mobile_media_query(selector: str) -> bool:
        """The rule must live under max-width:1199px — unconditionally it would break desktop.
        There are several such blocks, so anchor on the nearest @media above the selector."""
        i = css.find(selector)
        if i == -1:
            return False
        opened = css.rfind("@media", 0, i)
        return opened != -1 and "max-width:1199px" in css[opened:css.find("{", opened)]

    collapse = ".dwnav--phase2.dwnav--menu .dwnav-links{ display:none; }"
    reveal = ".dwnav--phase2.dwnav--menu.dwnav--open .dwnav-links{"
    assert in_mobile_media_query(collapse), (
        "the collapsed mobile masthead does not hide the index — the four family headers will "
        "render next to the hamburger, and they do nothing when tapped"
    )
    assert in_mobile_media_query(reveal), "nothing re-shows the index when the menu opens"
    # Both selectors must out-specify `.dwnav--phase2 .dwnav-links` (two classes) so they win on
    # specificity rather than on source order, which is what broke the generic rule.
    for sel in (".dwnav--phase2.dwnav--menu .dwnav-links",
                ".dwnav--phase2.dwnav--menu.dwnav--open .dwnav-links"):
        classes = sel.count(".")          # every class token starts with a dot; there are no ids
        assert classes >= 3, (
            f"{sel} carries {classes} classes and cannot out-specify the two-class "
            ".dwnav--phase2 .dwnav-links, so it would depend on source order"
        )
