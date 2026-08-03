#!/usr/bin/env python3
"""Phase 2: install the canonical dropdown nav across every source page.

Builds a single .dwnav--phase2 masthead (Our Firm / Coordination / Insights / For Professionals
+ Client Access + Request a Coordination Review) and injects it into every non-redirect source
page, marking the current page + its family. Also creates the sub-pages that do not yet exist so
no dropdown link 404s.

Run from repo root: python3 scripts/phase2_nav.py
"""
import re, glob, os, sys

SRC = "src/drift/web"

# Same token sync_docs.py substitutes firm_anchor_html() into. Declared here because this script
# is what puts it on the page; sync_docs.py is what fills it in.
FIRM_ANCHOR_TOKEN = "<!--FIRM_ANCHOR-->"


def _esc(label):
    """Menu labels are authored as plain text and escaped once, here.

    Only "Tools & References" needs it today, but a raw ampersand in an attribute-free text node is
    the kind of thing that stays valid right up until a label gains an angle bracket. Escaping at
    emit time keeps FAMILIES readable as a specification rather than as markup.
    """
    return label.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# (family label, [(sub-label, href, src-page-key), ...])
#
# ── 2026-08-01: reorganised BY READER, not by artifact ────────────────────────────────────────
# Twenty destinations became thirteen. The design council read the site as three arriving readers
# (a prospect, a referring CPA, an estate attorney) and found the masthead was a directory of the
# file system: it listed what the firm had made, in the order it had been made, and left the two
# best documents on the site (Fees, the CPA page) either unlinked or buried.
#
# Three changes carry the whole restructure:
#   * Fees enters Our Firm. It is among the three best pages on the site and was reachable from
#     exactly one other page.
#   * Coordination drops from eight entries to three. It had become the drawer everything went in:
#     a framework, a near-homonym of that framework, four tools, and the booking page.
#   * The four instruments (Assessment, Diagnostic, Lab, Atlas) move under Insights → Tools &
#     References, where a reader already expects instruments to live. They are not the product;
#     the Coordination Review is, and it keeps its own row plus the standing CTA.
#
# ── the five placeholders, and why only three of them are linked ───────────────────────────────
# The council's HIGH-priority call was to unlink five unfinished pages — Leadership, Fiduciary
# Standard, Your First 90 Days, Estate Attorneys, Referral Process — on the principle that "an
# absent page costs nothing, an empty one costs the reader's confidence in everything else."
# Three of those five have since been written into finished pages (leadership.html,
# estate-attorneys.html, referral.html) and are linked here.
#
# fiduciary.html and first-90-days.html have NOT been written. They are still the shared stub
# template — an eyebrow repeating the headline over a single sentence fragment — so they do not
# appear below, even though the approved mockup's "proposed" column lists them. The mockup
# describes the eventual end state; the standing rule ("no placeholders ship") governs what ships
# today. Both pages still build and still resolve by URL; they are simply not advertised. They
# join their family the day they are written, and not before — the same rule that kept Decision
# Memos out of the menu until a memo existed.
FAMILIES = [
    ("Our Firm", [
        ("Our Story", "principles.html", "principles.html"),
        ("Leadership", "leadership.html", "leadership.html"),
        # Fiduciary Standard belongs here and is deliberately withheld: fiduciary.html is a stub.
        ("Fees", "fees.html", "fees.html"),
    ]),
    # The two near-homonyms were merged into one entry, and on 2026-08-01 the merge finished: the
    # surviving FILE flipped. coordination-framework.html was 10KB of definitional list plus a CTA;
    # coordination.html is 49KB carrying the actual argument (the tumour-board opening, the worked
    # $8M estate, the method note) and ~30 inbound body links from the case studies, the registers,
    # and the homepage essay chain. Keeping the thin page as the destination meant the menu's one
    # Coordination door opened onto the weaker of the two.
    #
    # So coordination.html takes the name, the seven definitions moved into it as a reference band,
    # and coordination-framework.html became a canonical + refresh redirect — the same pattern
    # about.html uses into principles.html. One page, one name: the nav label and the <title> both
    # read "How Coordination Works" while the h1 stays as written, because a headline is not a page
    # name.
    ("Coordination", [
        ("How Coordination Works", "coordination.html", "coordination.html"),
        # Your First 90 Days belongs here and is deliberately withheld: first-90-days.html is a stub.
        ("A Household, Coordinated", "household-example.html", "household-example.html"),
        ("The Coordination Review", "coordination-review.html", "coordination-review.html"),
    ]),
    # "Insights", not "Insights & Research" (2026-07-31). The family is named for what it will hold
    # in three to five years, not what it happens to hold today: papers, commentary, a quarterly
    # publication, decision memos, and a growing shelf of interactive tools. "Research" is one of
    # those things and cannot name the set.
    #
    # "Articles" was dropped outright. It named a FORMAT, not a subject, and formats do not deserve
    # navigation — it also pointed at insights.html, which was a redirect stub back to research.html,
    # so the menu carried an entry that round-tripped the reader to a sibling entry.
    #
    # Decision Memos / Decision Tools / Decision Library were three menu rows pointing at three
    # sections of one landing page. They collapse into "Tools & References" (2026-08-01, the agreed
    # label — NOT "Decision Library and Tools"), which lands on #decision-tools, the section that
    # enumerates the instruments; Memos and Library are the next two sections down the same page.
    # One entry, one page, no menu row that is really a scroll position.
    ("Insights", [
        ("Research", "research.html", "research.html"),
        ("Commentary", "commentary.html", "commentary.html"),
        ("The Driftwood Review", "driftwood-review.html", "driftwood-review.html"),
        ("Tools & References", "insights.html#decision-tools", "insights.html"),
    ]),
    # "For Professionals", and every child addressed to the reader rather than describing the
    # artifact: a CPA scanning a masthead is looking for themselves, not for a noun.
    ("For Professionals", [
        ("For CPAs", "partners.html", "partners.html"),
        ("For Estate Attorneys", "estate-attorneys.html", "estate-attorneys.html"),
        ("Making a Referral", "referral.html", "referral.html"),
    ]),
]

# page file -> (family_label, sub_href) that should read as current.
#
# A sub_href that matches no entry in FAMILIES lights the FAMILY only — which is the correct read
# for a page that legitimately has no menu row of its own (an unlinked stub, a merged sibling, a
# deep essay). The reader still learns where in the site they are standing.
CURRENT = {
    "principles.html": ("Our Firm", "principles.html"),
    "leadership.html": ("Our Firm", "leadership.html"),
    "fees.html": ("Our Firm", "fees.html"),
    # Unlinked stub: family only, so anyone arriving from a bookmark or a body link is still oriented.
    "fiduciary.html": ("Our Firm", "fiduciary.html"),
    "coordination.html": ("Coordination", "coordination.html"),
    "household-example.html": ("Coordination", "household-example.html"),
    "coordination-review.html": ("Coordination", "coordination-review.html"),
    # Merged out of the menu (see FAMILIES) but still very much a Coordination page.
    "coordination.html": ("Coordination", "coordination.html"),
    "the-practice.html": ("Coordination", "the-practice.html"),
    # Unlinked stub: family only.
    "first-90-days.html": ("Coordination", "first-90-days.html"),
    "research.html": ("Insights", "research.html"),
    "insights.html": ("Insights", "insights.html"),
    "commentary.html": ("Insights", "commentary.html"),
    # A deep essay: lights the family, no menu row of its own.
    "count-the-pairs.html": ("Insights", "count-the-pairs.html"),
    # Same rule. It is filed under Research, so the Research row is what lights up.
    "the-interval-problem.html": ("Insights", "research.html"),
    # A short note rather than a paper, so it lights Commentary.
    "the-shortest-line.html": ("Insights", "commentary.html"),
    "articles.html": ("Insights", "articles.html"),
    "driftwood-review.html": ("Insights", "driftwood-review.html"),
    "decision-memo-domicile.html": ("Insights", "insights.html"),
    "ic-memo.html": ("Insights", "insights.html"),
    # The four instruments. They moved out of Coordination on 2026-08-01: a tool is evidence, not
    # the engagement, and putting them beside "The Coordination Review" made the free artifact and
    # the product look like siblings. They mark Insights → Tools & References, which is the row
    # that names the shelf they sit on.
    "score.html": ("Insights", "insights.html"),
    "leakage.html": ("Insights", "insights.html"),
    "taxlab.html": ("Insights", "insights.html"),
    "statemap.html": ("Insights", "insights.html"),
    "concentration.html": ("Insights", "insights.html"),
    # Decision Library — the worked decisions. Same rule: the family lights up, the Tools &
    # References row lights up, and the reader can see where in the site they are standing.
    "case-business-sale.html": ("Insights", "insights.html"),
    "case-vacation-home.html": ("Insights", "insights.html"),
    "case-inheritance.html": ("Insights", "insights.html"),
    "case-moving-states.html": ("Insights", "insights.html"),
    "case-stock-options.html": ("Insights", "insights.html"),
    "case-rmds.html": ("Insights", "insights.html"),
    "case-widowed.html": ("Insights", "insights.html"),
    "case-charitable-giving.html": ("Insights", "insights.html"),
    "partners.html": ("For Professionals", "partners.html"),
    "estate-attorneys.html": ("For Professionals", "estate-attorneys.html"),
    "referral.html": ("For Professionals", "referral.html"),
    "cpa-collab.html": ("For Professionals", "cpa-collab.html"),
}

BRAND = ('<a class="brand" href="index.html" aria-label="Driftwood Wealth, home">'
         '<svg class="brand-mark" viewBox="6 13 90 74" fill="none" stroke="currentColor" '
         'stroke-linecap="square" stroke-linejoin="miter" aria-hidden="true">'
         '<polyline points="10,18 24.35,18 62,50" stroke-width="4.6"></polyline>'
         '<polyline points="10,34 43.18,34 62,50" stroke-width="4.6"></polyline>'
         '<line x1="10" y1="50" x2="62" y2="50" stroke-width="4.6"></line>'
         '<polyline points="10,66 43.18,66 62,50" stroke-width="4.6"></polyline>'
         '<polyline points="10,82 24.35,82 62,50" stroke-width="4.6"></polyline>'
         '<line x1="62" y1="50" x2="90" y2="50" stroke-width="7"></line></svg>'
         '<span class="brand-rule" aria-hidden="true"></span>'
         '<span class="brand-word">Driftwood Wealth</span></a>')

def build_nav(page_file):
    cur = CURRENT.get(page_file)
    fam_cur, sub_cur = cur if cur else (None, None)
    parts = [BRAND]
    families = []
    for fam_label, items in FAMILIES:
        is_current = (fam_label == fam_cur)
        cls = "dwnav-drop" + (" dwnav-drop--current" if is_current else "")
        links = []
        for label, href, key in items:
            attrs = ' href="%s"' % href
            if key == sub_cur:
                attrs += ' aria-current="page"'
            links.append('<a%s>%s</a>' % (attrs, _esc(label)))
        panel = '<div class="dwnav-panel">%s</div>' % "".join(links)
        trigger = ('<button type="button" class="dwnav-trigger" aria-haspopup="true" '
                   'aria-expanded="false">%s<span class="caret" aria-hidden="true"></span></button>'
                   % _esc(fam_label))
        families.append('<div class="%s">%s%s</div>' % (cls, trigger, panel))
    # The families MUST be wrapped in .dwnav-links. This is not cosmetic markup — it is the hook the
    # entire mobile masthead hangs from, and omitting it broke the nav on every phone and tablet:
    #
    #   * dw-context.js's disclosure enhancer does `nav.querySelector(".dwnav-links")` and returns
    #     early when it is absent, so the hamburger was never injected and .dwnav--menu was never
    #     added — which is what activates every mobile rule in driftwood.css.
    #   * .dwnav-panel is display:none by default. It is revealed by .dwnav-drop--open (desktop
    #     only — open() is a no-op below 1200px) or by .dwnav--menu.dwnav--open. With neither
    #     reachable, all four family triggers were dead buttons under 1200px and roughly twenty
    #     destinations had no route to them at all.
    #
    # The CSS has always expected this element (it styles .dwnav-links at both breakpoints); only
    # the generator failed to emit it. Keep the separator, Client Access, and the CTA OUTSIDE it —
    # the mobile rules target those three separately.
    parts.append('<div class="dwnav-links">%s</div>' % "".join(families))
    parts.append('<span class="dwnav-sep" aria-hidden="true"></span>')
    parts.append('<a class="dwnav-access" href="private.html">Client Access</a>')
    parts.append('<a class="dwnav-cta" href="coordination-review.html">Request a Coordination Review <span class="cta-arrow" aria-hidden="true">&rarr;</span></a>')
    return '<nav class="dwnav dwnav--phase2" aria-label="Driftwood Wealth">\n      %s\n    </nav>' % "\n      ".join(parts)

NAV_RE = re.compile(r'<nav\b[^>]*>.*?</nav>', re.S)

# ---- the journey rail (Layer 3) ----
#
# The rail says WHERE AM I in the engagement. It is not the recommendation engine, which says WHAT
# SHOULD I DO NEXT and lives in dw-context.js — two different questions that were previously
# answered by the same hardcoded list of four steps.
#
# Three steps, not six. The middle is deliberately NOT a sequence: the four analyses are parallel,
# and which one a household should run is decided per-visitor by the recommendation engine. A
# six-step linear rail would assert a funnel the information architecture has just denied, and it
# wraps badly on a phone.
#
# Emitted from here rather than hand-written into each page for the same reason the masthead is:
# it previously existed as four near-identical copies, and adding the Assessment and the
# Concentrated Position Lab would have made six copies to keep in sync by hand.
JOURNEY = {
    # page                       (step, middle label,                middle href)
    "score.html":               (1, "Choose your analysis",         "insights.html#decision-tools"),
    "leakage.html":             (2, "Tax Diagnostic",               "leakage.html"),
    "statemap.html":            (2, "State Tax Atlas",              "statemap.html"),
    "taxlab.html":              (2, "After-Tax Lab",                "taxlab.html"),
    "concentration.html":       (2, "Concentrated Position Lab",    "concentration.html"),
    # coordination-review.html carried step 3 and no longer does (2026-08-01). It is the destination,
    # not a waypoint: a reader who lands here has the highest intent on the site, and the rail greeted
    # them by naming two steps they had skipped and framing a considered engagement as the end of a
    # funnel. Nothing else on the page depends on it. Removing the entry is what removes the rail —
    # install_rail() strips any rail it finds on a page that is not listed here.
}

# Two closing divs, not three: the rail is .journey-rail > .jr-in, and .jr-in's children (<ol>, the
# CTA anchor) contribute no divs of their own. Matching three swallowed ~5KB of the page beyond it.
RAIL_RE = re.compile(r'\s*<div class="journey-rail".*?</div>\s*</div>', re.S)


def build_rail(page_file):
    """The three-step spine. Every class here already exists in driftwood.css."""
    spec = JOURNEY.get(page_file)
    if not spec:
        return None
    step, mid_label, mid_href = spec
    steps = [(1, "Coordination Assessment", "score.html"),
             (2, mid_label, mid_href),
             (3, "Coordination Review", "coordination-review.html")]
    items = []
    for n, label, href in steps:
        cur = ' aria-current="step"' if n == step else ""
        items.append('<li%s><span class="num">%d</span><a href="%s">%s</a></li>' % (cur, n, href, label))
        if n != 3:
            items.append('<li class="sep" aria-hidden="true">&rarr;</li>')
    return (
        '\n    <div class="journey-rail" data-step="%d" aria-label="Your path through the engagement">'
        '\n      <div class="jr-in">'
        '\n        <span class="jr-k">Your path</span>'
        '\n        <ol>%s</ol>'
        '\n        <a class="jr-cta" href="coordination-review.html">The product &rarr;</a>'
        '\n      </div>'
        '\n    </div>' % (step, "".join(items))
    )


def install_rail(s, page_file):
    """Idempotent: replace an existing rail, else insert one right after the masthead."""
    rail = build_rail(page_file)
    if rail is None:
        # Not merely "leave it alone": a page dropped from JOURNEY must lose the rail it was built
        # with, or the removal only takes effect on pages that never had one.
        return RAIL_RE.sub("", s, count=1)
    if RAIL_RE.search(s):
        return RAIL_RE.sub(lambda _: rail, s, count=1)
    m = re.search(r'</nav>\s*(<div id="dw-household"[^>]*></div>)?', s)
    if not m:
        return s
    return s[:m.end()] + rail + s[m.end():]

# A page that opens its content with <div class="wrap"> but has no <nav> never had a masthead to
# replace, so the original "no nav -> skip" rule silently left it out of the sweep forever. Six pages
# were in that state, including "The Seven Systems" and "Household Example" — both linked FROM the
# Coordination dropdown, so a visitor who followed the menu landed somewhere with no way back.
WRAP_OPEN_RE = re.compile(r'(<div class="wrap"[^>]*>)')


FOOT_RE = re.compile(r'(\n\s*)(<div class="foot"[ >])')


def install_anchor(s):
    """Put the canonical firm strip above every page's disclosure block.

    The strip carries the firm name, the descriptor, the city, the phone, and the email, rendered
    once from site.py. It existed before this, but only ten of sixty-five pages carried the
    <!--FIRM_ANCHOR--> token that sync_docs.py substitutes it into — and the pages missing it were
    disproportionately the ones a professional actually lands on, which meant the reader most likely
    to want to pick up a phone was on a page with no number on it.

    Idempotent by construction: the token is inserted only where a .foot exists and no token is
    already present, so re-running never stacks a second strip.
    """
    if FIRM_ANCHOR_TOKEN in s:
        return s
    m = FOOT_RE.search(s)
    if not m:
        return s
    return s[:m.start()] + m.group(1) + FIRM_ANCHOR_TOKEN + m.group(1) + m.group(2) + s[m.end():]


def _tidy(rest):
    """Drop the blank lines the removed masthead left behind.

    Removing <nav> takes the element but not the newlines that surrounded it, and the re-insert then
    adds its own — so every run grew each page by one blank line. The script is meant to be run
    whenever the IA changes, which made "how many times has this been run?" visible in the diff of
    51 files. Normalizing here makes install() genuinely idempotent: run it twice, get one result.
    """
    return rest.lstrip("\n")


def install(page):
    s = open(page, encoding="utf-8").read()
    if 'http-equiv="refresh"' in s:
        return False                                   # redirect stub: no chrome by design
    name = os.path.basename(page)
    if NAV_RE.search(s):
        # Lift the masthead to the TOP of .wrap. On many pages it sat inside .frame > .inner, i.e.
        # inside the narrow reading shell — so the nav itself was 920–1080px wide depending on the
        # page while the homepage's was 1300px. Moving between pages visibly resized the masthead,
        # which is the one element a visitor sees on every screen. Content columns stay narrow;
        # the frame and the nav on it do not.
        stripped = NAV_RE.sub("", s, count=1)
        m = WRAP_OPEN_RE.search(stripped)
        if m:
            new = stripped[:m.end()] + "\n" + build_nav(name) + _tidy(stripped[m.end():])
        else:
            new = NAV_RE.sub(lambda mm: build_nav(name), s, count=1)
    else:
        m = WRAP_OPEN_RE.search(s)
        if not m:
            return False                               # nothing to anchor to
        new = s[:m.end()] + "\n" + build_nav(name) + _tidy(s[m.end():])
    new = install_rail(new, name)
    new = install_anchor(new)
    if new != s:
        open(page, "w", encoding="utf-8").write(new)
        return True
    return False

# ---- stub sub-pages ----
#
# create-if-missing only: every file below already exists, so make_stubs() is a no-op today. The
# dict is kept as the safety net that stops a deleted file from breaking sync_docs.py's copy-through
# (which reads each name unconditionally).
#
# Note that being in STUBS no longer implies being in the menu. fiduciary.html and first-90-days.html
# are generated, built, and reachable by URL, but unlinked from the masthead until they are written —
# see the FAMILIES header. Writing one of them means replacing the stub AND adding its row back to
# its family, in the same commit.
STUBS = {
    "leadership.html": ("Leadership", "The people and the standard behind the practice",
        "Driftwood is the private-wealth practice of Alec Messino, who conducts every Coordination Review personally. This page introduces the practice's leadership and the fiduciary standard it is held to."),
    "fiduciary.html": ("Fiduciary Standard", "Fee-based, fiduciary, and accountable to one client",
        "Driftwood is a fee-based fiduciary: it is compensated to coordinate your decisions, not to sell a product, and it is held to a standard of acting in your interest. Securities and advisory services are offered through Park Avenue Securities LLC (PAS), member FINRA/SIPC."),
    "six-systems.html": ("Six Systems", "The systems a coordinated life has to keep in one register",
        "Every financial life rests on the same set of systems — investments, taxes, cash flow, estate, protection, and the family's purpose. The Coordination Review reads them as one network, not six separate accounts."),
    "first-90-days.html": ("Your First 90 Days", "What the opening engagement actually does",
        "The first ninety days turn a scattered financial life into a coordinated one: the systems are mapped, the gaps are named, the Opportunity Register opens, and a 90-day plan sets the first owned decisions in motion."),
    "commentary.html": ("Commentary", "Short notes on coordination, tax, and the moving parts",
        "Occasional commentary on the decisions that quietly connect a household's systems — what changed, what it moved, and what a coordinated read would have caught earlier."),
    "estate-attorneys.html": ("Estate Attorneys", "For the attorneys who draft the documents",
        "Driftwood coordinates with estate attorneys rather than replacing them: the Coordination Review surfaces the decisions the documents depend on, and keeps them in one register the attorney can work from."),
    "referral.html": ("Referral Process", "How a referral reaches the right desk",
        "For CPAs and attorneys who recognize a coordination gap in a client's life: how a referral works, what the client receives, and how the introducing advisor stays informed."),
}

STUB_TMPL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{title}, Driftwood Wealth</title>
<meta name="description" content="{desc}" />
<link rel="canonical" href="https://driftwoodwealth.com/{name}" />
<link rel="stylesheet" href="driftwood.css">
<script src="dw-context.js"></script>
<link rel="icon" href="favicon.svg" />
<style>
  :root{{ --bg:#f1efe9; --soft:#f7f5f0; --line:#d8d3c6; --line2:#e9e5db; --frame-line:#c3bcab; --ghost-line:#b8b2a4;
    --ink:#1e2833; --body:#3d4650; --dim:#5c6470; --muted:#6b6e6a; --accent-strike:#2c5878; --accent-strike-soft:#a9c2d6;
    --navy:#1a2330; --on-dark:#e7ecf2; }}
  *{{box-sizing:border-box}}
  body{{margin:0;background:var(--bg);color:var(--body);font:16.5px/1.62 var(--sans);
    -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}}
  .wrap{{max-width:1060px;margin:36px auto;padding:0 20px 60px}}
  .frame{{background:var(--bg);overflow:hidden}}
  .doc{{padding:46px 44px 8px;max-width:760px}}
  .eyebrow{{font-family:var(--sans);font-weight:700;font-size:11px;letter-spacing:.2em;text-transform:uppercase;
    color:var(--accent-strike);margin-bottom:16px}}
  h1{{font-family:var(--sans);font-weight:700;font-size:clamp(32px,3vw+16px,46px);line-height:1.06;letter-spacing:-.022em;
    color:var(--ink);margin:0 0 18px;max-width:20ch}}
  .lede{{font-family:var(--serif);font-size:19px;line-height:1.55;color:var(--dim);margin:0;max-width:62ch}}
  .door{{margin:30px 44px 8px;padding:30px 34px;background:var(--navy);color:var(--on-dark);border-radius:0}}
  .door .dh{{font-family:var(--sans);font-weight:700;font-size:24px;letter-spacing:-.02em;color:#f1ede3;margin:0 0 10px}}
  .door .ds{{font-family:var(--sans);font-size:14px;line-height:1.55;color:var(--accent-strike-soft);margin:0 0 20px;max-width:56ch}}
  .door a.book{{display:inline-block;text-decoration:none;font-family:var(--sans);font-size:15px;font-weight:700;
    padding:14px 28px;background:var(--accent-strike);color:#f1ede3}}
  .foot{{padding:30px 44px;font-size:11px;line-height:1.6;color:var(--muted);border-top:1px solid var(--line)}}
</style>
</head>
<body>
<div class="wrap"><div class="frame">
{NAV}
    <div class="doc">
      <div class="eyebrow">{eyebrow}</div>
      <h1>{title}</h1>
      <p class="lede">{lede}</p>
    </div>
    <div class="door">
      <div class="dh">Schedule a Coordination Review.</div>
      <div class="ds">The guided engagement: Tax Diagnostic, State Tax Atlas, and After-Tax Lab are
        supporting evidence. The Review is the product.</div>
      <a class="book" href="coordination-review.html">Request a Coordination Review &rarr;</a>
    </div>
    <div class="foot">
      Educational, not investment, tax, or legal advice. Driftwood Wealth is the private-wealth practice of
      Alec Messino. Securities products and advisory services offered through Park Avenue Securities LLC (PAS),
      member FINRA, SIPC. Alec Messino is a Registered Representative and Financial Advisor of PAS. All figures illustrative, not a recommendation.
      <a href="privacy.html">Privacy</a> · <a href="terms.html">Terms</a>.
    </div>
</div></div>
</body>
</html>
"""

def make_stubs():
    created = []
    for name, (title, lede, desc) in STUBS.items():
        path = os.path.join(SRC, name)
        if os.path.exists(path):
            continue
        html = STUB_TMPL.format(NAV=build_nav(name), eyebrow=title, title=title, lede=lede, desc=desc, name=name)
        open(path, "w", encoding="utf-8").write(html)
        created.append(name)
    return created

if __name__ == "__main__":
    installed = []
    for page in sorted(glob.glob(os.path.join(SRC, "*.html"))):
        if install(page):
            installed.append(os.path.basename(page))
    created = make_stubs()
    print("installed nav on %d pages" % len(installed))
    print("created %d stub pages: %s" % (len(created), ", ".join(created)))
