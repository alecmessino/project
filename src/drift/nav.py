"""The canonical Driftwood masthead, in one place.

The site had TWO mastheads. `scripts/phase2_nav.py` injected the real one (`.dwnav--phase2`, four
families, Client Access, the standing CTA) into every source page under `src/drift/web/`; the 51
editioned Atlas pages, the Comparison, the Crossing Brief and the Household Record carried a
second, hand-written `NAV` constant inside `statepage.py` that had frozen at the phase-1 design.
By 2026-08-09 that copy advertised a family ("The Method") that no longer exists, a row ("How It
Works") pointing at a redirect stub, and a product name ("After-Tax Review") the rest of the site
had renamed. No guard could see it, because every nav test reads the source templates under
`src/drift/web/` and the Atlas pages are generated.

That mattered little while the Atlas was two clicks deep. It matters now that the Atlas is a
masthead row of its own and the destination we are actively promoting, so the generator and the
injector both point here and there is one masthead again.

FAMILIES is the specification. Read it, and the comments in it, before changing a row.
"""

from __future__ import annotations

import re

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
    # ── 2026-08-14: the Coordination Atlas joins this family, not Insights ────────────────────
    # It is one workspace over three routes — the state brief, the household inventory, and the
    # scope a review would examine — sharing a single household context across all three. That
    # makes it a Coordination artifact by function: an Insights row would file it beside the
    # reference material it happens to read from, which is the smaller half of what it does.
    #
    # It does NOT displace "The State Tax Atlas" (statemap.html), which remains the published
    # 8-dimension reference and keeps its own Insights row. Two different objects: one is the
    # reference, the other is the surface a household reads it through.
    ("Coordination", [
        ("How Coordination Works", "coordination.html", "coordination.html"),
        # Your First 90 Days belongs here and is deliberately withheld: first-90-days.html is a stub.
        ("A Household, Coordinated", "household-example.html", "household-example.html"),
        ("The Coordination Atlas", "coordination-atlas.html", "coordination-atlas.html"),
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
    #
    # ── 2026-08-09: the Atlas comes back out of the shelf, deliberately ───────────────────────────
    # On 2026-08-01 the four instruments were moved INTO "Tools & References" on the reasoning that
    # "a tool is evidence, not the engagement". That reasoning still holds for the Assessment, the
    # Diagnostic and the Lab, and all three stay on the shelf.
    #
    # The Atlas is now a different kind of object from its three shelfmates, and the promotion is a
    # judgement that the 2026-08-01 rule no longer describes it rather than a reversal of the rule:
    #   * It is 51 editioned, statute-cited, server-rendered pages plus three derived instruments
    #     (Comparison, Crossing Brief, Household Record), not one calculator.
    #   * It is the firm's centre-of-influence surface. A CPA or an estate attorney is the primary
    #     reader, and it is the one artifact they can put in front of a client unchanged.
    #   * It carries the per-state collision block, which is where the coordination argument stops
    #     being a claim about the firm and becomes a fact about the reader's own state.
    # Nothing else moves. Three rows on the shelf, one row of its own.
    ("Insights", [
        ("Research", "research.html", "research.html"),
        ("Commentary", "commentary.html", "commentary.html"),
        ("The Driftwood Review", "driftwood-review.html", "driftwood-review.html"),
        ("The State Tax Atlas", "statemap.html", "statemap.html"),
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
    "coordination-atlas.html": ("Coordination", "coordination-atlas.html"),
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
    # The Atlas has its own row as of 2026-08-09 (see FAMILIES), so it lights that row rather than
    # the shelf it used to sit on.
    "statemap.html": ("Insights", "statemap.html"),
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



def render(page_file: str | None = None, abs_base: str | None = None) -> str:
    """The masthead for `page_file`, marking its family and its row as current.

    `abs_base` rewrites root-relative hrefs to absolute, for the editioned pages that sit three
    directories deep and would otherwise resolve `about.html` under /atlas/2026/<state>/.
    """
    nav = build_nav(page_file or "")
    if abs_base:
        nav = re.sub(r'href="(?!https?:|#|/)([^"]*)"', lambda m: f'href="{abs_base}{m.group(1)}"', nav)
    return nav
