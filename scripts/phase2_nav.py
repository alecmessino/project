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


# The masthead specification and renderer moved to src/drift/nav.py on 2026-08-09 so the
# generated Atlas pages could stop carrying a second, frozen copy of it. This script still owns
# the INJECTION (which pages get a nav, the journey rail, stub creation); drift.nav owns WHAT the
# nav is. Change a row there, then re-run this, then scripts/sync_docs.py.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from drift.nav import FAMILIES, CURRENT, BRAND, build_nav, _esc  # noqa: E402,F401

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
