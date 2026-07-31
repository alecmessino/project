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
    "leakage.html": ("Coordination", "leakage.html"),
    "taxlab.html": ("Coordination", "taxlab.html"),
    "coordination-review.html": ("Coordination", "coordination-review.html"),
    "research.html": ("Insights", "research.html"),
    "insights.html": ("Insights", "insights.html"),
    "commentary.html": ("Insights", "commentary.html"),
    "driftwood-review.html": ("Insights", "driftwood-review.html"),
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
    parts.append('<a class="dwnav-cta" href="coordination-review.html">Request a Coordination Review</a>')
    return '<nav class="dwnav dwnav--phase2" aria-label="Driftwood Wealth">\n      %s\n    </nav>' % "\n      ".join(parts)

NAV_RE = re.compile(r'<nav\b[^>]*>.*?</nav>', re.S)

def install(page):
    s = open(page, encoding="utf-8").read()
    if not NAV_RE.search(s):
        return False  # redirect stub or no nav
    name = os.path.basename(page)
    new = NAV_RE.sub(lambda m: build_nav(name), s, count=1)
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
