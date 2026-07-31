#!/usr/bin/env python3
"""Phase 2: install the canonical dropdown nav across every source page.

Builds a single .dwnav--phase2 masthead (Our Firm / Coordination / Insights & Research /
Professionals + Client Access + Request a Coordination Review) and injects it into every
non-redirect source page, marking the current page + its family. Also creates the seven
sub-pages that do not yet exist so no dropdown link 404s.

Run from repo root: python3 scripts/phase2_nav.py
"""
import re, glob, os, sys

SRC = "src/drift/web"

# (family label, [(sub-label, href, src-page-key), ...])
FAMILIES = [
    ("Our Firm", [
        ("Our Story", "principles.html", "principles.html"),
        ("Leadership", "leadership.html", "leadership.html"),
        ("Fiduciary Standard", "fiduciary.html", "fiduciary.html"),
    ]),
    ("Coordination", [
        ("The Coordination Framework", "coordination.html", "coordination.html"),
        ("The Seven Systems", "coordination-framework.html", "coordination-framework.html"),
        ("Your First 90 Days", "first-90-days.html", "first-90-days.html"),
        ("Household Example", "household-example.html", "household-example.html"),
        # The Coordination Assessment is the front of the funnel and had NO menu entry anywhere on
        # the site — reachable only from four body links, so the one tool designed to be run first
        # was the hardest to find. It sits above the Diagnostic because that is the order the
        # journey rail walks. The two tools below keep their entries: they carry a link on every
        # page, and which ordering converts better is a measured question (OPERATIONS.md), not a
        # layout preference to settle by deletion.
        ("Coordination Assessment", "score.html", "score.html"),
        ("Tax Diagnostic", "leakage.html", "leakage.html"),
        ("After-Tax Lab", "taxlab.html", "taxlab.html"),
        ("Schedule a Coordination Review", "coordination-review.html", "coordination-review.html"),
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
    # Decision Tools and Decision Library are sections of the Insights landing page rather than
    # separate stubs: each is currently a list of links, and two thin pages would be worse than two
    # well-populated sections. They graduate to their own pages when they outgrow it (OPERATIONS.md).
    ("Insights", [
        ("Research", "research.html", "research.html"),
        ("Commentary", "commentary.html", "commentary.html"),
        ("The Driftwood Review", "driftwood-review.html", "driftwood-review.html"),
        # Reserved since 2026-07-31, entering the menu now that a memo exists — the rule was
        # that the category ships in the same commit as its first entry, never before it.
        ("Decision Memos", "insights.html#decision-memos", "insights.html"),
        ("Decision Tools", "insights.html#decision-tools", "insights.html"),
        ("Decision Library", "insights.html#decision-library", "insights.html"),
    ]),
    ("Professionals", [
        ("CPA Collaboration", "partners.html", "partners.html"),
        ("Estate Attorneys", "estate-attorneys.html", "estate-attorneys.html"),
        ("Referral Process", "referral.html", "referral.html"),
    ]),
]

# page file -> (family_label, sub_href) that should read as current
CURRENT = {
    "principles.html": ("Our Firm", "principles.html"),
    "leadership.html": ("Our Firm", "leadership.html"),
    "fiduciary.html": ("Our Firm", "fiduciary.html"),
    "coordination.html": ("Coordination", "coordination.html"),
    "coordination-framework.html": ("Coordination", "coordination-framework.html"),
    "six-systems.html": ("Coordination", "coordination-framework.html"),
    "first-90-days.html": ("Coordination", "first-90-days.html"),
    "the-practice.html": ("Coordination", "the-practice.html"),
    "score.html": ("Coordination", "score.html"),
    "leakage.html": ("Coordination", "leakage.html"),
    "taxlab.html": ("Coordination", "taxlab.html"),
    "coordination-review.html": ("Coordination", "coordination-review.html"),
    "research.html": ("Insights", "research.html"),
    "insights.html": ("Insights", "insights.html"),
    "commentary.html": ("Insights", "commentary.html"),
    "driftwood-review.html": ("Insights", "driftwood-review.html"),
    "decision-memo-domicile.html": ("Insights", "insights.html"),
    "ic-memo.html": ("Insights", "insights.html"),
    # Decision Tools — these have no menu entry of their own (the menu names the category, the
    # landing page enumerates the tools), so they mark the Insights family and the category row.
    "statemap.html": ("Insights", "insights.html"),
    "concentration.html": ("Insights", "insights.html"),
    # Decision Library — the worked decisions. Same rule: the family lights up, the category row
    # lights up, and the reader can see where in the site they are standing.
    "case-business-sale.html": ("Insights", "insights.html"),
    "case-vacation-home.html": ("Insights", "insights.html"),
    "case-inheritance.html": ("Insights", "insights.html"),
    "case-moving-states.html": ("Insights", "insights.html"),
    "case-stock-options.html": ("Insights", "insights.html"),
    "case-rmds.html": ("Insights", "insights.html"),
    "case-widowed.html": ("Insights", "insights.html"),
    "case-charitable-giving.html": ("Insights", "insights.html"),
    "partners.html": ("Professionals", "partners.html"),
    "estate-attorneys.html": ("Professionals", "estate-attorneys.html"),
    "referral.html": ("Professionals", "referral.html"),
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
    for fam_label, items in FAMILIES:
        is_current = (fam_label == fam_cur)
        cls = "dwnav-drop" + (" dwnav-drop--current" if is_current else "")
        links = []
        for label, href, key in items:
            attrs = ' href="%s"' % href
            if key == sub_cur:
                attrs += ' aria-current="page"'
            links.append('<a%s>%s</a>' % (attrs, label))
        panel = '<div class="dwnav-panel">%s</div>' % "".join(links)
        trigger = ('<button type="button" class="dwnav-trigger" aria-haspopup="true" '
                   'aria-expanded="false">%s<span class="caret" aria-hidden="true"></span></button>' % fam_label)
        parts.append('<div class="%s">%s%s</div>' % (cls, trigger, panel))
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
    "coordination-review.html": (3, "Choose your analysis",         "insights.html#decision-tools"),
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
        return s
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
    if new != s:
        open(page, "w", encoding="utf-8").write(new)
        return True
    return False

# ---- 7 stub sub-pages ----
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
<title>{title}</title>
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
  .note{{font-family:var(--sans);font-size:13.5px;line-height:1.6;color:var(--muted);margin:28px 44px 0;max-width:64ch}}
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
    <div class="note">This page is part of the Driftwood Coordination framework. The full experience —
      the systems read together, the findings written down, and an owner against every gap — is the
      Coordination Review.</div>
    <div class="door">
      <div class="dh">Schedule a Coordination Review.</div>
      <div class="ds">The guided engagement: Tax Diagnostic, State Tax Atlas, and After-Tax Lab are
        supporting evidence. The Review is the product.</div>
      <a class="book" href="coordination-review.html">Request a Coordination Review &rarr;</a>
    </div>
    <div class="foot">
      Educational, not investment, tax, or legal advice. Driftwood Wealth is the private-wealth practice of
      Alec Messino. Securities products and advisory services offered through Park Avenue Securities LLC (PAS),
      member FINRA, SIPC. Alec Messino is a Registered Representative and Financial Advisor of PAS and a
      Financial Representative of Guardian. All figures illustrative, not a recommendation.
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
