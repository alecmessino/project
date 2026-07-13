"""Per-state SEO landing pages — the organic-search front door to the funnel.

Each of the 50 states + DC gets its own **server-side-rendered** page (content baked into the HTML,
not JS-rendered like the interactive exhibits) so search engines index the state's real tax facts.
These are reference pages — they answer "how does this state tax investors?" — and the Driftwood
modeling is demoted to a quiet secondary section, not the hero. The content is assembled entirely from
existing sources of truth — `statemap._state_record` and `leakage.STATE_ALPHA` — so a state page can
never disagree with the map or the diagnostic.

Every page carries: a keyword title/H1/meta, canonical + Open Graph, FAQPage + BreadcrumbList +
FinancialService JSON-LD, the seven factual tax dimensions, a secondary "what careful tax management
can change" section (the illustrative before/after impact), a link into the personalized diagnostic
(`leakage.html?state=XX`), related-state internal links, and the full RIA + hypothetical-performance
disclosure. Output is flat `<slug>-tax.html` at the docs root so all asset paths (driftwood.css, og/,
favicon) resolve exactly like the other pages.

    drift states --out-dir docs        # writes <slug>-tax.html for every state + states.html index
"""

from __future__ import annotations

import html
import json
import re
import time
from pathlib import Path

from .leakage import (STATE_ALPHA, STATE_NAMES, build_leakage,
                      coordination_opportunity_per_m, fmt_usd, fmt_usd_compact)
from .statemap import DIMENSIONS, _state_record, AS_OF_LAW, LAST_REVIEWED, _CHANGELOG, CURRENT_EDITION
from . import reasoning

# Single source of truth for the public base URL lives in drift.site (re-exported here for callers
# and tests); flip it with scripts/set_domain.py when the custom domain goes live.
from .site import BASE_URL, BOOKING_URL, firm_anchor_html

# One-click booking from any flagship (Launch Standard: deep-page CTAs go straight to the scheduler,
# not back through the homepage contact section).
MEETING_URL = BOOKING_URL

# The 50 states + DC get a landing page (territories are edge cases; "—"/"NYC" are pseudo-keys).
STATE_PAGE_CODES = sorted(
    c for c in STATE_ALPHA if c not in ("—", "NYC") and c in STATE_NAMES and len(c) == 2
)

_DIM_LABEL = {d["key"]: d["label"] for d in DIMENSIONS}
# alpha is rendered as the hero, not a plain card; the seven factual dimensions each get a card.
_DIM_ORDER = ["cg", "marriage", "estate", "muni", "qsbs", "loss", "stepup"]


def slug_for(code: str) -> str:
    """SEO-friendly flat filename stem, e.g. 'CA' -> 'california-tax', 'DC' -> 'washington-dc-tax'."""
    name = STATE_NAMES.get(code, code)
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") + "-tax"


def page_path(code: str) -> str:
    """The flat legacy slug, kept as a permanent redirect alias: 'CA' -> 'california-tax.html'."""
    return f"{slug_for(code)}.html"


# ── Editioned publication URLs (§15.3) ────────────────────────────────────────────────────────────
# The Atlas is an editioned publication: /atlas/2026/{state}/ is the canonical, citable home for each
# state page; the flat *-tax.html slugs live on as permanent redirect aliases. Editioned pages sit
# three directories deep, so they carry absolute links (BASE_URL) rather than the root-relative links
# the flat pages used.
def state_slug(code: str) -> str:
    """The editioned URL slug (no '-tax'): 'CA' -> 'california', 'DC' -> 'washington-dc'."""
    return re.sub(r"[^a-z0-9]+", "-", STATE_NAMES.get(code, code).lower()).strip("-")


def atlas_path(code: str, edition: str = CURRENT_EDITION) -> str:
    """Editioned directory path (no domain): 'atlas/2026/california'."""
    return f"atlas/{edition}/{state_slug(code)}"


def atlas_url(code: str, edition: str = CURRENT_EDITION) -> str:
    """Canonical editioned URL, trailing slash: '{BASE_URL}/atlas/2026/california/'."""
    return f"{BASE_URL}/{atlas_path(code, edition)}/"


def edition_url(edition: str = CURRENT_EDITION) -> str:
    """The edition index (the states directory): '{BASE_URL}/atlas/2026/'."""
    return f"{BASE_URL}/atlas/{edition}/"


_ABS = f"{BASE_URL}/"  # absolute-link base for the nested editioned pages


# ── related-state internal linking: two high-tax, two no-tax, so every page links into the cluster ──
_HIGH_TAX = ["CA", "NY", "NJ", "OR", "MN", "HI"]
_NO_TAX = ["TX", "FL", "WA", "TN", "NV", "NH"]


def _related(code: str) -> list[tuple[str, str]]:
    picks: list[str] = []
    for pool in (_HIGH_TAX, _NO_TAX):
        for c in pool:
            if c != code and c in STATE_PAGE_CODES and c not in picks:
                picks.append(c)
                break
    # round out to 4 with the next distinct entries
    for pool in (_HIGH_TAX, _NO_TAX):
        for c in pool:
            if len(picks) >= 4:
                break
            if c != code and c in STATE_PAGE_CODES and c not in picks:
                picks.append(c)
    return [(c, STATE_NAMES[c]) for c in picks[:4]]


# ── Hand-authored, factual per-state context ──────────────────────────────────────────────────────
# The no-income-tax states (AK/FL/NV/NH/SD/TN/TX/WY) are IDENTICAL on every regime dimension — even the
# new muni/QSBS/loss ones — so the dataset alone can't give their pages distinct body copy (a real SEO
# duplicate-content risk). This is a genuinely unique, verifiable 1–2 sentence nugget per state
# (relocation drivers, homestead/asset-protection, trust-jurisdiction notes) — no invented law, and the
# "not advice" framing is preserved by the page's global disclosure. Every no-tax state MUST be covered.
_STATE_CONTEXT = {
    "AK": ("Alaska levies no state income tax and no statewide sales tax, and is the only no-income-tax "
           "state that also pays residents an annual Permanent Fund Dividend. It offers an elective "
           "community-property trust, so a couple can opt in to a full basis step-up at the first death."),
    "FL": ("Florida has no state income tax and a constitutional bar against one, which — paired with an "
           "unlimited-value homestead creditor exemption and tenancy-by-the-entireties protection for "
           "married couples — makes it a leading inbound-migration state for retirees and high earners."),
    "NV": ("Nevada has no state income tax and no corporate income tax, and is a well-known "
           "asset-protection venue for its self-settled spendthrift (Nevada Asset Protection) trusts. "
           "It is also a community-property state, so community assets get a full step-up at the first death."),
    "NH": ("New Hampshire taxes neither wages nor capital gains, and its former Interest & Dividends tax "
           "was fully repealed effective 2025 — so investment income is now untaxed at the state level. "
           "There is no general sales tax either."),
    "SD": ("South Dakota has no state income tax and is a premier trust jurisdiction: it allows perpetual "
           "(dynasty) trusts, imposes no state tax on trust income, and offers strong privacy — which is "
           "why a large volume of out-of-state trust assets is administered there."),
    "TN": ("Tennessee has no state income tax on wages, and its Hall tax on interest and dividends was "
           "fully repealed effective 2021 — so investment income is now untaxed at the state level. It "
           "leans instead on one of the higher combined sales-tax rates in the country."),
    "TX": ("Texas has no state income tax, constitutionally restricted, and pairs a strong homestead "
           "exemption with a community-property regime — so community assets receive a full basis step-up "
           "at the first spouse's death. Property and sales taxes carry more of the state's revenue."),
    "WY": ("Wyoming has no state income tax and no corporate income tax, and is a highly regarded trust "
           "and LLC jurisdiction — perpetual-trust statutes, strong privacy, and robust asset-protection "
           "law draw significant out-of-state planning."),
    # A few higher-traffic states with a genuinely distinctive regime note (not required for dedup):
    "CA": ("California applies the nation's highest top marginal rate and taxes capital gains as ordinary "
           "income, with no preferential long-term rate. It is a community-property state (full step-up at "
           "the first death) but is decoupled from the federal §1202 QSBS exclusion."),
    "WA": ("Washington has no tax on wages but, since 2022, levies a 7% (plus a 2.9% surcharge) excise on "
           "long-term capital gains above an annual threshold — the newest and most unusual regime in the "
           "country. Because that excise falls on long-term gains only, while short-term gains go untaxed, "
           "careful tax management — which works largely by turning short-term gains into long-term — helps "
           "less here than almost anywhere: Washington is the rare state where the usual playbook partly "
           "reverses. It is a community-property state, so community assets get a full step-up."),
    "NY": ("New York stacks a high state rate with a New York City surcharge for city residents, and its "
           "estate tax has a notorious 'cliff': clear the exemption by more than 5% and the entire estate — "
           "not just the excess — becomes taxable."),
    "MA": ("Massachusetts applies a flat 5% rate plus a 4% surtax on income over ~$1.1 million, and has "
           "one of the lowest state estate-tax exemptions (~$2 million), so estate exposure reaches well "
           "into the merely-affluent."),
}


def _state_context(code: str) -> str:
    return _STATE_CONTEXT.get(code, "")


def _faq(code: str, name: str, rec: dict) -> list[dict]:
    """Factual Q&A drawn from the dataset — unique per state, eligible for FAQ rich snippets."""
    faq = []
    cg = rec.get("cg")
    if cg:
        faq.append({"q": f"How are capital gains taxed in {name}?", "a": cg["note"]})
    est = rec.get("estate")
    if est:
        faq.append({"q": f"Does {name} have a state estate or inheritance tax?", "a": est["note"]})
    mar = rec.get("marriage")
    if mar:
        faq.append({"q": f"Is there a marriage penalty in {name}?", "a": mar["note"]})
    muni = rec.get("muni")
    if muni:
        faq.append({"q": f"How does {name} tax municipal-bond interest?", "a": muni["note"]})
    qsbs = rec.get("qsbs")
    if qsbs:
        faq.append({"q": f"Does {name} follow the federal QSBS (§1202) exclusion?", "a": qsbs["note"]})
    loss = rec.get("loss")
    if loss:
        faq.append({"q": f"What happens to a capital loss you carry forward in {name}?", "a": loss["note"]})
    a = rec.get("alpha")
    if a:
        faq.append({"q": f"How much is careful tax coordination worth in {name}?",
                    "a": a["note"]})
    return faq


def build_state_pages() -> dict:
    """{code: page-data} for every landing page, assembled once from the shared map dataset."""
    leak = build_leakage()
    out = {}
    for code in STATE_PAGE_CODES:
        rec = _state_record(code)
        name = STATE_NAMES[code]
        out[code] = {
            "code": code, "name": name, "slug": slug_for(code),
            "rec": rec, "alpha": rec.get("alpha"),
            "levers": leak["levers"],
            "faq": _faq(code, name, rec),
            "related": _related(code),
            "context": _state_context(code),
            "reasoning": reasoning.build_reasoning(code, rec),  # impact / framework / considerations / actions
        }
    return out


# ── rendering (server-side) ──────────────────────────────────────────────────────────────────────
def _esc(s: str) -> str:
    return html.escape(str(s), quote=True)


NAV = (
    '<nav class="dwnav" aria-label="Driftwood Capital">\n'
    '  <a class="brand" href="index.html" aria-label="Driftwood Capital — home">'
    '<svg class="brand-mark" viewBox="0 0 46 30" fill="none" stroke="currentColor" stroke-linecap="butt" aria-hidden="true">'
    '<path d="M1.5 1 H4.5 L27 15" stroke-width="2.4"/>'
    '<path d="M1.5 8 H8 L27 15" stroke-width="2.4"/>'
    '<path d="M1.5 15 H27" stroke-width="2.4"/>'
    '<path d="M1.5 22 H8 L27 15" stroke-width="2.4"/>'
    '<path d="M1.5 29 H4.5 L27 15" stroke-width="2.4"/>'
    '<path d="M27 15 H44.5" stroke-width="3.4"/></svg>'
    '<span class="brand-rule" aria-hidden="true"></span>'
    '<span class="brand-word">Driftwood Capital</span></a>\n'
    '  <div class="dwnav-links">\n'
    '    <span class="dwnav-group"><span class="dwnav-label">Understand</span>\n'
    '      <a href="about.html">Our Story</a>\n'
    '      <a href="principles.html">Philosophy</a>\n'
    '      <a href="inside.html">Operating&nbsp;System</a>\n'
    '      <a href="thesis.html">How We Invest</a>\n'
    '      <a href="howitworks.html">How It Works</a>\n'
    '      <a href="insights.html">Insights</a>\n'
    '      <a href="ledger.html">Research</a>\n'
    '    </span>\n'
    '    <span class="dwnav-group"><span class="dwnav-label">Discover</span>\n'
    '      <a href="leakage.html">Tax&nbsp;Diagnostic</a>\n'
    '      <a href="taxlab.html">After-Tax&nbsp;Review</a>\n'
    '      <a href="statemap.html" aria-current="page">State&nbsp;Tax&nbsp;Atlas</a>\n'
    '    </span>\n'
    '  </div>\n'
    '  <a class="dwnav-cta" href="index.html#conversation">Schedule a Coordination Review</a>\n'
    '</nav>'
)

# The same nav with root-relative hrefs rewritten to absolute (BASE_URL), for the nested editioned
# pages where a root-relative 'about.html' would otherwise resolve under /atlas/2026/{state}/.
NAV_ABS = re.sub(r'href="(?!https?:|#|/)([^"]*)"', lambda m: f'href="{_ABS}{m.group(1)}"', NAV)


# ── The narrative process spine ─────────────────────────────────────────────────────────────────
# Not a nav breadcrumb (where you are in the tree) but a PROCESS breadcrumb (where you are in the
# coordination journey): Environment → Compare → Plan → Coordinate → Review. It reinforces that the
# visitor is moving through one operating system, not browsing pages. Stages map 1:1 to the flagship
# products; the active stage is highlighted and Review always lands on a conversation.
_PROCESS_STAGES = [
    ("environment", "Environment", lambda ed: edition_url(ed)),           # the Atlas
    ("compare", "Compare", lambda ed: f"{edition_url(ed)}compare/"),      # the Comparison
    ("plan", "Plan", lambda ed: f"{edition_url(ed)}crossing/"),           # the Crossing Brief
    ("coordinate", "Coordinate", lambda ed: f"{edition_url(ed)}household/"),  # the Household Record
    ("review", "Review", lambda ed: MEETING_URL),                         # a conversation
]


def _process_bar(active: str, edition: str = CURRENT_EDITION) -> str:
    """The progressive process spine for the flagship pages; `active` is one of the stage keys."""
    parts = []
    for i, (key, label, urlfn) in enumerate(_PROCESS_STAGES):
        if i:
            parts.append('<i aria-hidden="true">→</i>')
        cur = ' aria-current="step"' if key == active else ""
        cls = "on" if key == active else ""
        parts.append(f'<a class="{cls}" href="{urlfn(edition)}"{cur}>{label}</a>')
    return f'<nav class="procbar" aria-label="Where you are in the coordination process">{"".join(parts)}</nav>'


PLAUSIBLE = (
    '<!-- Privacy-first analytics (Plausible) -->\n'
    '<script async src="https://plausible.io/js/pa-K0dJ5ljpih0ZZ-zv5pSeB.js"></script>\n'
    '<script>\n'
    '  window.plausible=window.plausible||function(){(plausible.q=plausible.q||[]).push(arguments)},'
    'plausible.init=plausible.init||function(i){plausible.o=i||{}};\n'
    '  plausible.init()\n'
    '</script>'
)

DISCLOSURE = (
    '<div class="disc">'
    '<b>Illustrative / hypothetical — not a real track record and not advice.</b> The tax-management '
    'impact figure is a hypothetical, after-tax result from the <b>retroactive application</b> of a '
    'tax-management model to ~30 years of proxy-spliced market data on a single illustrative path; '
    '<b>no client capital was invested</b>, and hypothetical performance <b>does not guarantee future '
    'results</b>. Intended for sophisticated investors; it may not be relevant to your situation, and '
    'your actual figure depends on your own holdings, basis, and bracket. State tax facts reflect tax '
    'year 2025 and can change — confirm with a tax advisor. Driftwood Capital is a '
    '<b>registered investment adviser</b>; <b>Form ADV</b> and <b>Form CRS</b> are available at '
    '<a href="https://adviserinfo.sec.gov/">adviserinfo.sec.gov</a>.'
    '</div>'
)


def _meta_description(name: str, rec: dict) -> str:
    cg = rec.get("cg")
    a = rec.get("alpha")
    rate = f" Top effective long-term rate {cg['tag']}." if (cg and cg["tag"] not in ("0%", "")) else ""
    if cg and cg["tag"] == "0%":
        rate = " No state tax on capital gains."
    impact = (f" Estimated after-tax coordination opportunity ~{fmt_usd(coordination_opportunity_per_m(a['value']))}"
              f"/yr per $1M of taxable assets in our illustrative modeling.") if a else ""
    return (f"How {name} taxes investors: capital gains, estate and inheritance tax, the marriage "
            f"penalty, municipal-bond interest, QSBS, and basis step-up.{rate}{impact} A state tax "
            f"reference. Illustrative, not advice.")[:300]


def _src_line(d: dict) -> str:
    """Citation-aware provenance for a dimension card, making the evidence hierarchy visible: a verified
    statute renders 'Prove it' with the primary source; an as-yet-uncited fact is labeled honestly as a
    summary — never dressed as a citation it doesn't have."""
    cites = d.get("citation")
    if cites:
        links = " · ".join(
            f'<a href="{_esc(c["url"])}" target="_blank" rel="noopener">{_esc(c["label"])}</a>' for c in cites)
        return f'<div class="dsrc"><b>Statute:</b> {links}</div>'
    return (f'<div class="dsrc"><b>Summary of state law</b> — primary-source citation in progress. '
            f'{_esc(d.get("source", ""))}</div>')


def _dim_cards(rec: dict) -> str:
    cards = []
    for key in _DIM_ORDER:
        d = rec.get(key)
        if not d:
            continue
        tag = f'<span class="dtag">{_esc(d["tag"])}</span>' if d.get("tag") else ""
        cards.append(
            f'<div class="dcard"><div class="dh">{_esc(_DIM_LABEL[key])}{tag}</div>'
            f'<p>{_esc(d["note"])}</p>'
            f'{_src_line(d)}</div>'
        )
    return "\n".join(cards)


def _provenance_block() -> str:
    """The 'as of / last reviewed' stamp + a short 'what changed' log — the freshness signals a citable
    reference lives on. State-agnostic: every page carries the currency of the whole Atlas."""
    items = "\n".join(f'<li><b>{_esc(d)}</b> — {_esc(t)}</li>' for d, t in _CHANGELOG)
    return (
        f'<p class="asofline">State law reflects <b>{_esc(AS_OF_LAW)}</b>; last reviewed '
        f'<b>{_esc(LAST_REVIEWED)}</b>. Every classification is a summary of state law; where a '
        f'primary-source citation has been verified, it is linked on the card.</p>'
        f'<details class="chlog"><summary>What changed</summary><ul>{items}</ul></details>'
    )


def _impact_block(name: str, a: dict | None) -> str:
    """The demoted (secondary-section) illustrative figure — reference, not hero. Public-facing, it
    now leads with the *coordination opportunity* in dollars-per-$1M rather than a return percentage;
    the modeled +X.X%/yr and the before/after kept-rate stay as the underlying methodology (and satisfy
    the source-of-truth numbers the state-page tests require)."""
    if not a:
        return ""
    before, after, alpha = a["before"], a["after"], a["value"]
    usd = coordination_opportunity_per_m(alpha)
    kept_before = max(2, min(96, round(before / max(after, 0.1) * 100)))
    return (
        f'<div class="hero">'
        f'<div class="big">~{fmt_usd(usd)}<span class="u">/yr per $1M taxable</span></div>'
        f'<div class="hlab">Estimated after-tax coordination opportunity in {_esc(name)}<br>'
        f'<span class="hsub">what running the portfolio against {_esc(name)}\'s rules can be worth — about '
        f'+{alpha:.1f}%/yr modeled, as a tax-managed book keeps ~{after:.1f}%/yr after tax vs ~{before:.1f}%/yr '
        f'for a concentrated, naive one; illustrative, over ~30 years, scales with the portfolio</span></div>'
        f'<div class="hbar" aria-hidden="true">'
        f'<span class="kept" style="width:{kept_before}%"></span></div>'
        f'</div>'
    )


def _faq_html(faq: list[dict]) -> str:
    if not faq:
        return ""
    items = "\n".join(
        f'<details class="faq"><summary>{_esc(f["q"])}</summary><p>{_esc(f["a"])}</p></details>'
        for f in faq
    )
    return f'<div class="sec"><div class="sh">Frequently asked — {len(faq)} on {{}}</div>{items}</div>'


def _jsonld(name: str, code: str, rec: dict, faq: list[dict], edition: str = CURRENT_EDITION) -> str:
    url = atlas_url(code, edition)  # the editioned canonical
    blocks = [
        {"@context": "https://schema.org", "@type": "FinancialService",
         "name": f"Driftwood Capital — {name} tax-aware investing", "legalName": "Driftwood Capital",
         "url": url, "areaServed": {"@type": "State", "name": name}, "feeBasis": "Fee-only",
         "description": f"Tax-aware investment management for {name} investors — asset location, "
                        f"tax-loss harvesting, and lot protection. Illustrative modeling, not advice."},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Driftwood Capital", "item": f"{BASE_URL}/index.html"},
            {"@type": "ListItem", "position": 2, "name": "The State Atlas", "item": edition_url(edition)},
            {"@type": "ListItem", "position": 3, "name": name, "item": url}]},
    ]
    if faq:
        blocks.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": f["q"],
             "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in faq]})
    return "\n".join(f'<script type="application/ld+json">\n{json.dumps(b)}\n</script>' for b in blocks)


_HEAD_CSS = """
  :root{--bg:#f1efe9;--soft:#f7f5f0;--line:#d8d3c6;--line2:#e9e5db;--chrome:#ece6da;
    --ink:#1d242d;--body:#3a414b;--dim:#5f5d68;--muted:#6f675b;
    --brass:#2c5878;--gold:#a9c2d6;--teal:#15463a;--teal2:#15806a;--neg:#9b4439;--navy:#1a2330;}
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--body);font:14.5px/1.6 var(--serif);
    -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
  .sheet{max-width:1040px;margin:30px auto;padding:0 20px 50px}
  .frame{background:var(--bg);border:1px solid #d9d2c4;border-radius:0;overflow:hidden;
    box-shadow:0 1px 2px rgba(20,18,12,.04),0 30px 70px -36px rgba(20,18,12,.46)}
  .bcrumb{padding:12px 40px 0;font-size:11.5px;color:var(--muted)}
  .bcrumb a{color:var(--brass);text-decoration:none} .bcrumb a:hover{text-decoration:underline}
  /* The narrative process spine — where you are in the coordination journey (not the page tree). */
  .procbar{display:flex;flex-wrap:wrap;align-items:center;gap:5px 9px;padding:13px 40px 2px;
    font-family:var(--sans);font-size:10px;font-weight:700;letter-spacing:.14em;text-transform:uppercase}
  .procbar a{color:var(--muted);text-decoration:none;padding:2px 0}
  .procbar a.on{color:var(--accent-strike);box-shadow:inset 0 -2px 0 var(--accent-strike)}
  .procbar a:hover{color:var(--ink)}
  .procbar i{color:var(--ghost-line);font-weight:400}
  @media(max-width:600px){.procbar{padding-left:18px;padding-right:18px;font-size:9px;letter-spacing:.1em}}
  .hd{padding:22px 40px 6px}
  .eyebrow{font-family:var(--sans);font-weight:700;font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--accent-strike);margin-bottom:10px}
  h1{font-family:var(--sans);font-weight:700;font-size:clamp(28px, 2.4vw + 19px, 36px);line-height:1.05;letter-spacing:-.02em;color:var(--ink);margin:0 0 10px}
  .lede{font-size:15px;color:var(--dim);margin:0;max-width:76ch}
  .context{font-size:14px;line-height:1.65;color:var(--body);margin:14px 0 0;max-width:76ch;
    border-left:3px solid var(--gold);padding:2px 0 2px 16px}
  .hero{margin:18px 40px 4px;padding:18px 24px;background:var(--navy);border-radius:0;display:flex;
    align-items:center;gap:20px;flex-wrap:wrap}
  .hero .big{font-variant-numeric:tabular-nums;font-size:44px;font-weight:700;color:#f1ede3;letter-spacing:-.02em;line-height:1}
  .hero .big .u{font-size:18px;color:var(--gold);margin-left:2px}
  .hero .hlab{font-size:13px;color:#dfe4ea;font-weight:500;flex:1;min-width:220px}
  .hero .hsub{font-weight:400;color:#9aa3ae;font-size:12px}
  .hero .hbar{width:100%;height:8px;border-radius:0;background:var(--neg);overflow:hidden}
  .hero .hbar .kept{display:block;height:100%;background:var(--teal2)}
  .grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;padding:18px 40px 6px}
  @media(max-width:760px){.grid{grid-template-columns:1fr}}
  .dcard{border:1px solid var(--line);border-left:3px solid var(--brass);border-radius:0;padding:14px 16px;background:#fff}
  .dcard .dh{font-family:var(--sans);font-weight:500;font-size:14.5px;color:var(--ink);margin-bottom:5px;display:flex;align-items:center;gap:8px}
  .dcard .dtag{font-size:10.5px;font-weight:700;color:var(--brass);border:1px solid var(--gold);border-radius:0;padding:2px 8px}
  .dcard p{margin:0;font-size:12.5px;color:var(--body);line-height:1.5}
  .dcard .dsrc{font-size:10px;color:var(--muted);margin-top:8px}
  .dcard .dsrc a{color:var(--teal2)}
  .asofline{font-size:11.5px;color:var(--muted);margin:16px 40px 0;line-height:1.55}
  .asofline b{color:var(--dim)}
  .mnote{font-size:11.5px;color:var(--muted);margin:10px 0 0;line-height:1.55;max-width:70ch}
  .chlog{margin:8px 40px 0;font-size:11.5px;color:var(--muted)}
  .chlog summary{cursor:pointer;color:var(--teal2);font-weight:500;width:max-content}
  .chlog ul{margin:8px 0 0;padding-left:18px;line-height:1.55} .chlog li{margin:3px 0}
  .chlog b{color:var(--dim)}
  .sec{padding:14px 40px 4px}
  .sec .sh{font-weight:500;font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin-bottom:12px}
  .levers{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
  @media(max-width:760px){.levers{grid-template-columns:1fr}}
  .lv{border:1px solid var(--line);border-left:3px solid var(--teal2);border-radius:0;padding:13px 15px;background:var(--soft)}
  .lv .n{font-weight:500;font-size:13px;color:var(--ink)} .lv .d{font-size:12px;color:var(--body);line-height:1.45;margin-top:4px}
  /* Reasoning chain (§16): Decision Framework signals, considerations, action register. Quiet — the
     level is a dot meter, not an alarm colour; hierarchy comes from weight and rule, not hue. */
  .fw{display:grid;gap:10px}
  .fsig{border:1px solid var(--line);border-left:3px solid var(--brass);background:#fff;padding:12px 15px}
  .fsig .fh{display:flex;align-items:baseline;justify-content:space-between;gap:12px}
  .fsig .fl{font-family:var(--sans);font-weight:500;font-size:13.5px;color:var(--ink)}
  .fsig .fm{display:inline-flex;gap:3px;align-items:center;flex-shrink:0}
  .fsig .fm i{width:6px;height:6px;border-radius:50%;background:var(--line);display:inline-block}
  .fsig .fm i.on{background:var(--brass)}
  .fsig p{margin:5px 0 0;font-size:12.5px;color:var(--body);line-height:1.5}
  .fsig.lv-severe{border-left-color:var(--neg)} .fsig.lv-severe .fm i.on{background:var(--neg)}
  .fsig.lv-none{border-left-color:var(--line)} .fsig.lv-none .fm i.on{background:var(--muted)}
  .considx{list-style:none;margin:0;padding:0;display:grid;gap:10px}
  .considx li{border:1px solid var(--line);border-left:3px solid var(--teal2);background:var(--soft);padding:12px 15px}
  .considx .ca{font-family:var(--sans);font-weight:500;font-size:13px;color:var(--ink)}
  .considx .cw{font-size:11px;color:var(--brass);font-weight:500}
  .considx p{margin:4px 0 0;font-size:12px;color:var(--body);line-height:1.45}
  .actreg{margin:0;padding:0;list-style:none;counter-reset:act;display:grid;gap:9px}
  .actreg li{display:flex;gap:12px;align-items:baseline;font-size:12.5px;color:var(--body);line-height:1.5}
  .actreg li::before{counter-increment:act;content:counter(act);font-family:var(--sans);font-weight:700;
    font-size:11px;color:var(--brass);min-width:15px}
  .actreg .ao{font-family:var(--sans);font-size:9.5px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;
    color:var(--muted);white-space:nowrap;min-width:96px;display:inline-block}
  @media(max-width:600px){.actreg .ao{min-width:0;display:block;margin-bottom:1px}}
  details.faq{border-bottom:1px solid var(--line2);padding:10px 0}
  details.faq summary{font-weight:500;font-size:13.5px;color:var(--ink);cursor:pointer}
  details.faq p{margin:8px 0 2px;font-size:12.5px;color:var(--body)}
  .cta{margin:20px 40px 4px;padding:20px 24px;background:var(--soft);border:1px solid var(--line);border-radius:0;
    display:flex;align-items:center;gap:18px;flex-wrap:wrap}
  .cta .ctxt{flex:1;min-width:240px} .cta .ch{font-weight:500;font-size:18px;color:var(--ink);margin-bottom:3px}
  .cta .cd{font-size:12.5px;color:var(--dim)}
  .cta a{text-decoration:none;border-radius:0;font-size:14px;font-weight:500;white-space:nowrap;padding:12px 20px}
  .cta a.primary{background:var(--teal);color:#f1ede3} .cta a.ghost{border:1px solid var(--frame-line);color:var(--ink);font-weight:500}
  .rel{padding:6px 40px 4px;font-size:12.5px;color:var(--dim)} .rel a{color:var(--teal2);text-decoration:none;font-weight:500}
  .capture{margin:12px 40px 4px}
  .capform{display:flex;gap:8px;flex-wrap:wrap}
  .capform input[type=email]{flex:1;min-width:220px;padding:11px 14px;border:1px solid var(--line);border-radius:0;font:inherit;font-size:14px;background:#fff}
  .capform button{background:var(--brass);color:#fff;border:0;border-radius:0;font:inherit;font-weight:500;font-size:14px;padding:11px 18px;cursor:pointer}
  .capform button:disabled{opacity:.6;cursor:default}
  .capnote{font-size:11.5px;color:var(--dim);margin-top:8px} .capnote a{color:var(--teal2)}
  .capok{background:var(--soft);border:1px solid var(--line);border-left:3px solid var(--teal2);border-radius:0;padding:14px 16px;font-size:13.5px;color:var(--teal);font-weight:500}
  .vh{position:absolute!important;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);border:0}
  .disc{margin:16px 40px 6px;font-size:10.5px;line-height:1.55;color:var(--muted);border-top:1px solid var(--line);padding-top:12px}
  .disc a{color:var(--teal2)}
  /* Trailing colophon under the firm-anchor — a light one-line provenance note, deliberately NOT
     the .foot disclosure treatment (the real disclosure is the .disc block above the anchor). Named
     apart from .foot so the shared body .foot rule doesn't impose the heavy disclosure spacing. */
  .colophon{margin:14px 40px 26px;color:var(--muted);font-size:11px;line-height:1.6}
  /* Phones: pull the generous 40px editorial gutters in to a comfortable 18px so the prose column
     isn't pinched, consistent with the other exhibits. */
  @media(max-width:600px){
    .bcrumb,.hd,.grid,.sec,.rel{padding-left:18px;padding-right:18px}
    .hero,.cta,.capture,.disc,.colophon,.asofline,.chlog{margin-left:18px;margin-right:18px}
  }
  @media print{body{background:#fff}.sheet{margin:0;max-width:none}.frame{border:0;box-shadow:none}.cta,.capture,.dwnav{display:none}}
"""

# Web3Forms lead-capture (public key — safe in client code; mirrors taxlab.html CONFIG).
_FORM_EP = "https://api.web3forms.com/submit"
_FORM_KEY = "cf6b1c2d-9971-4256-9ff9-72d6918c84e6"
_FORM_HP = "botcheck"
_CONTACT = "hello@driftwoodplanning.com"


def _capture(code: str, name: str, alpha, rate: str) -> str:
    """An inline email capture so a state page converts in place — no click-through required. Posts to
    Web3Forms tagged with the state + a lead-quality flag; honest manual-follow-up copy (no auto-report
    promise). Falls back to a mailto on failure."""
    a = f"{alpha:.1f}" if alpha is not None else ""
    nm = _esc(name)
    return f"""    <div class="capture" id="capture">
      <form class="capform" id="capform" novalidate>
        <label class="vh" for="capemail">Your email address</label>
        <input type="email" id="capemail" placeholder="you@email.com" required autocomplete="email" aria-label="Your email address" />
        <input type="text" id="caphp" name="{_FORM_HP}" class="vh" tabindex="-1" autocomplete="off" aria-hidden="true" />
        <button type="submit" id="capsend">Email me {nm}'s brief →</button>
      </form>
      <div class="capnote" id="capnote">A one-page, {nm}-specific after-tax breakdown — we'll follow up by email, usually within a business day. We never share your address.</div>
    </div>
    <script>
    (function(){{
      var f=document.getElementById("capform"); if(!f) return;
      var qp=new URLSearchParams(location.search);
      f.addEventListener("submit",function(ev){{
        ev.preventDefault();
        var el=document.getElementById("capemail"), email=(el.value||"").trim();
        if(!/^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test(email)){{ if(el.reportValidity)el.reportValidity(); return; }}
        var btn=document.getElementById("capsend"); btn.disabled=true; btn.textContent="Sending…";
        var p={{email:email, access_key:"{_FORM_KEY}", from_name:"Driftwood",
          _subject:"New {nm} state-page lead", state:"{code}", state_name:"{nm}",
          tax_impact_pct:"{a}", top_lt_rate:"{_esc(rate)}", source:"state_page",
          lead_quality:({a or 0}>=4.5?"high":"standard")}};
        ["utm_source","utm_medium","utm_campaign","utm_term","utm_content"].forEach(function(k){{var v=qp.get(k); if(v)p[k]=v;}});
        p["{_FORM_HP}"]=(document.getElementById("caphp").value||"");
        fetch("{_FORM_EP}",{{method:"POST",headers:{{"Content-Type":"application/json",Accept:"application/json"}},body:JSON.stringify(p)}})
          .then(function(r){{ if(!r.ok) throw 0;
            document.getElementById("capture").innerHTML='<div class="capok" role="status" aria-live="polite">Thanks — we\\'ll email your {nm} after-tax breakdown, usually within a business day.</div>';
            if(window.plausible) plausible("lead_submitted",{{props:{{source:"state_page",state:"{code}"}}}}); }})
          .catch(function(){{ btn.disabled=false; btn.textContent="Email me {nm}'s brief →";
            document.getElementById("capnote").innerHTML='Sorry — that didn\\'t send. Email us at <a href="mailto:{_CONTACT}">{_CONTACT}</a>.'; }});
      }});
    }})();
    </script>"""


def _summary(name: str, rec: dict) -> str:
    """A one-sentence synthesis of the state's tax profile across the dimensions — gives each page a
    distinct body paragraph (not just a swapped name) and explains unusual regimes (e.g. WA's excise)."""
    cg, est, su = rec.get("cg"), rec.get("estate"), rec.get("stepup")
    income = ""
    if cg:
        if cg["regime"] == "notax":
            income = f"{name} levies no state income tax on capital gains"
        elif cg["regime"] == "lt_only":
            income = f"{name} taxes only long-term gains, via a {cg['tag']} excise gross of short-term losses"
        else:
            income = f"{name} taxes long-term gains at a top effective {cg['tag']}"
    death = {"none": "no state death tax", "estate": "a state estate tax",
             "inheritance": "a state inheritance tax", "both": "both an estate and an inheritance tax"
             }.get((est or {}).get("regime"), "")
    step = {"community": "community-property step-up (a full basis step-up at the first death)",
            "optin": "an elective community-property trust for a full step-up",
            "udcprda": "UDCPRDA treatment of imported community property",
            "common": "common-law step-up (only half of jointly-held property)"
            }.get((su or {}).get("regime"), "")
    bits = [b for b in (income, death, step) if b]
    return ("; ".join(bits) + ".") if bits else ""


_LEVEL_DOTS = {"none": 0, "low": 1, "moderate": 2, "high": 3, "severe": 4}


def _reasoning_html(r: dict, name: str) -> str:
    """Render the reasoning chain (§16) from the composable primitives: the Decision Framework (the
    centrepiece), the planning considerations it opens, and the sequenced action register. The
    objects come from drift.reasoning — this only renders them."""
    sigs = []
    for s in r["framework"]:
        n = _LEVEL_DOTS.get(s["level"], 0)
        dots = "".join(f'<i class="{"on" if i < n else ""}"></i>' for i in range(4))
        cls = f' lv-{s["level"]}' if s["level"] in ("severe", "none") else ""
        sigs.append(
            f'<div class="fsig{cls}"><div class="fh"><span class="fl">{_esc(s["title"])}</span>'
            f'<span class="fm" role="img" aria-label="{_esc(s["level"])} — {_esc(s["question"])}">{dots}</span></div>'
            f'<p>{_esc(s["reading"])}</p></div>')
    framework = (
        f'<div class="sec"><div class="sh">How to think about {_esc(name)}</div>'
        f'<p class="lede" style="margin-bottom:14px">Five lenses turn {_esc(name)}\'s tax environment into a '
        f'household decision — the same lenses every state is read through, so any two states weigh on '
        f'identical terms.</p><div class="fw">{chr(10).join(sigs)}</div></div>')
    coordination = ""
    if r["coordination"]:
        items = "\n".join(
            f'<li><span class="ca">{_esc(c["title"])}</span> <span class="cw">· with your {_esc(c["coordinate_with"])}</span>'
            f'<p>{_esc(c["rationale"])}</p></li>' for c in r["coordination"])
        coordination = (f'<div class="sec"><div class="sh">Coordination priorities for {_esc(name)} households</div>'
                        f'<ul class="considx">{items}</ul></div>')
    actions = ""
    if r["actions"]:
        items = "\n".join(
            f'<li><span class="ao">{_esc(a["owner"])}</span><span>{_esc(a["step"])}</span></li>' for a in r["actions"])
        actions = (f'<div class="sec"><div class="sh">What should happen next</div>'
                   f'<ol class="actreg">{items}</ol></div>')
    return framework + coordination + actions


def render_state_html(data: dict, edition: str = CURRENT_EDITION) -> str:
    code, name, slug = data["code"], data["name"], data["slug"]
    rec, a, faq = data["rec"], data["alpha"], data["faq"]
    title = f"{name} Capital Gains & Estate Tax — Tax-Leakage Diagnostic | Driftwood"
    desc = _meta_description(name, rec)
    url = atlas_url(code, edition)   # editioned canonical (the page lives at /atlas/{edition}/{slug}/)
    og = f"{BASE_URL}/og/states/{code.lower()}.png"
    levers = "\n".join(
        f'<div class="lv"><div class="n">{_esc(l["name"])}</div><div class="d">{_esc(l["desc"])}</div></div>'
        for l in data["levers"])
    faq_html = _faq_html(faq).replace("{}", _esc(name)) if faq else ""
    related = " · ".join(   # sibling editioned pages
        f'<a href="{atlas_url(c, edition)}">{_esc(nm)}</a>' for c, nm in data["related"])
    rate = (rec.get("cg") or {}).get("tag", "")
    capture = _capture(code, name, (a or {}).get("value"), rate)
    lede = (f"Every state taxes investors differently. Here is how {name} treats capital gains at the top "
            f"rate, the marriage penalty, estate and inheritance tax at death, municipal-bond interest, "
            f"the §1202 QSBS exclusion, and a harvested loss — a plain reference to the state's tax code.")
    summary = _summary(name, rec)
    summary_p = f'<p class="lede" style="margin-top:10px">{_esc(summary)}</p>' if summary else ""
    context = data.get("context", "")
    context_p = (f'<p class="context">{_esc(context)}</p>') if context else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
{PLAUSIBLE}
<title>{_esc(title)}</title>
<meta name="description" content="{_esc(desc)}" />
<link rel="canonical" href="{url}" />
<link rel="icon" href="{_ABS}favicon.svg" />
<link rel="icon" type="image/png" sizes="32x32" href="{_ABS}favicon-32.png" />
<link rel="apple-touch-icon" sizes="180x180" href="{_ABS}apple-touch-icon.png" />
<link rel="mask-icon" href="{_ABS}mask-icon.svg" color="#1a2330" />
<meta name="theme-color" content="#f1efe9" media="(prefers-color-scheme: light)" />
<meta name="theme-color" content="#1a2330" media="(prefers-color-scheme: dark)" />
<meta property="og:type" content="website" />
<meta property="og:site_name" content="Driftwood Capital" />
<meta property="og:title" content="{_esc(title)}" />
<meta property="og:description" content="{_esc(desc)}" />
<meta property="og:url" content="{url}" />
<meta property="og:image" content="{og}" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{_esc(title)}" />
<meta name="twitter:description" content="{_esc(desc)}" />
<meta name="twitter:image" content="{og}" />
{_jsonld(name, code, rec, faq, edition)}
<link rel="stylesheet" href="{_ABS}driftwood.css">
<script src="{_ABS}dw-context.js"></script>
<style>{_HEAD_CSS}</style>
</head>
<body>
<div class="sheet">
  <div class="frame">
    {NAV_ABS}
    {_process_bar("environment", edition)}
    <div class="hd">
      <div class="eyebrow">The State Atlas · {_esc(name)}</div>
      <h1>How {_esc(name)} taxes investors.</h1>
      <p class="lede">{_esc(lede)}</p>
      {summary_p}
      {context_p}
    </div>
    <div class="grid">
      {_dim_cards(rec)}
    </div>
    {faq_html}
    <div class="sec"><div class="sh">What careful tax management can change</div>
      <p class="lede" style="margin:2px 0 14px">Tax law is only half the picture. How a portfolio is
        built and run — where each holding sits, how losses are used, how gains are timed — decides how
        much of {_esc(name)}'s tax code you actually pay. An illustrative estimate for a portfolio here:</p>
      {_impact_block(name, a)}
      <p class="mnote">How this is modeled: a single 30-year proxy-spliced path (1996–2026), comparing a
        concentrated, high-turnover book with a tax-managed one — illustrative and coarse; treat it as
        directional, not a precise figure.</p>
      <div class="levers">{levers}</div></div>
    {_reasoning_html(data.get("reasoning") or {"framework": [], "considerations": [], "actions": []}, name)}
    <div class="cta">
      <div class="ctxt">
        <div class="ch">See the figure on your own {_esc(name)} portfolio.</div>
        <div class="cd">The personalized diagnostic computes your after-tax, asset-location, and harvesting picture — by bracket and holdings.</div>
      </div>
      <a class="primary" href="{_ABS}leakage.html?state={code}">Run my {_esc(name)} diagnostic →</a>
      <a class="ghost" href="{MEETING_URL}">Schedule a Coordination Review</a>
    </div>
{capture}
    <div class="rel">Onward: <a href="{edition_url(edition)}compare/">weigh {_esc(name)} against another state →</a> · <a href="{edition_url(edition)}crossing/">plan a move →</a> · <a href="{edition_url(edition)}household/">build a coordination record →</a><br><span style="color:var(--muted)">Nearby regimes: {related} · <a href="{edition_url(edition)}">all 50 states + DC →</a></span></div>
    {_provenance_block()}
    {DISCLOSURE}
    {firm_anchor_html()}
    <div class="colophon">Driftwood. State tax law reflects {_esc(AS_OF_LAW)}; last reviewed {_esc(LAST_REVIEWED)}.</div>
  </div>
</div>
</body>
</html>
"""


def render_states_index(pages: dict, edition: str = CURRENT_EDITION) -> str:
    """The edition index (/atlas/{edition}/): a crawlable directory of every state page, sorted, with
    each state's rate + illustrative alpha, linking to the editioned canonical pages."""
    rows = []
    for code in sorted(pages, key=lambda c: STATE_NAMES[c]):
        d = pages[code]
        a = d["alpha"]
        cg = d["rec"].get("cg")
        rate = _esc(cg["tag"]) if cg else "—"
        alpha = f'~{fmt_usd_compact(coordination_opportunity_per_m(a["value"]))}/$1M' if a else "—"
        rows.append(f'<tr><td><a href="{atlas_url(code, edition)}">{_esc(d["name"])}</a></td>'
                    f'<td>{rate}</td><td class="al">{alpha}</td></tr>')
    body = "\n".join(rows)
    url = edition_url(edition)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
{PLAUSIBLE}
<title>State Capital Gains & Estate Tax — all 50 states + DC | Driftwood</title>
<meta name="description" content="How every state taxes investors — top long-term capital-gains rate, estate and inheritance tax, munis, QSBS, and basis step-up for all 50 states and DC. A state tax reference. Illustrative, not advice." />
<link rel="canonical" href="{url}" />
<link rel="icon" href="{_ABS}favicon.svg" />
<link rel="icon" type="image/png" sizes="32x32" href="{_ABS}favicon-32.png" />
<link rel="apple-touch-icon" sizes="180x180" href="{_ABS}apple-touch-icon.png" />
<link rel="mask-icon" href="{_ABS}mask-icon.svg" color="#1a2330" />
<meta name="theme-color" content="#f1efe9" media="(prefers-color-scheme: light)" />
<meta name="theme-color" content="#1a2330" media="(prefers-color-scheme: dark)" />
<meta property="og:type" content="website" />
<meta property="og:site_name" content="Driftwood Capital" />
<meta property="og:title" content="State Capital Gains & Estate Tax — Driftwood Capital" />
<meta property="og:description" content="A tax reference for all 50 states + DC: top long-term capital-gains rate and how each state taxes investors." />
<meta property="og:url" content="{url}" />
<meta property="og:image" content="{BASE_URL}/og/statemap.png" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="State Tax Reference — Driftwood Capital" />
<meta name="twitter:description" content="How every state taxes investors — capital gains, estate, and more." />
<meta name="twitter:image" content="{BASE_URL}/og/statemap.png" />
<link rel="stylesheet" href="{_ABS}driftwood.css">
<script src="{_ABS}dw-context.js"></script>
<style>{_HEAD_CSS}
  table.st{{width:calc(100% - 80px);margin:6px 40px 0;border-collapse:collapse;font-size:13.5px}}
  table.st th,table.st td{{padding:8px 10px;border-bottom:1px solid var(--line2);text-align:right}}
  table.st th:first-child,table.st td:first-child{{text-align:left}}
  table.st thead th{{font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}}
  table.st td.al{{font-weight:700;color:var(--teal);font-variant-numeric:tabular-nums}}
  table.st a{{color:var(--ink);text-decoration:none;font-weight:500}} table.st a:hover{{color:var(--teal2)}}
  @media(max-width:760px){{table.st{{width:100%;margin:6px 0 0}}}}
</style>
</head>
<body>
<div class="sheet">
  <div class="frame">
    {NAV_ABS}
    {_process_bar("environment", edition)}
    <div class="hd">
      <div class="eyebrow">The State Atlas · state tax reference</div>
      <h1>How every state taxes investors.</h1>
      <p class="lede">Pick your state for its capital-gains, estate, marriage, and basis-step-up profile —
        and an illustrative estimate of the after-tax coordination opportunity its rules create.</p>
    </div>
    <table class="st">
      <thead><tr><th scope="col">State</th><th scope="col">Top LT rate</th><th scope="col">Coordination Opportunity</th></tr></thead>
      <tbody>{body}</tbody>
    </table>
    <div class="cta">
      <div class="ctxt">
        <div class="ch">A state is where coordination begins, not ends.</div>
        <div class="cd">Weigh two environments, plan a move between them, and see how it all becomes one household's standing record.</div>
      </div>
      <a class="primary" href="{edition_url(edition)}compare/">Compare how coordination changes across states →</a>
      <a class="ghost" href="{MEETING_URL}">Schedule a Coordination Review</a>
    </div>
    <div class="rel">Onward: <a href="{edition_url(edition)}crossing/">plan a move between states →</a> · <a href="{edition_url(edition)}household/">build a coordination record →</a></div>
    {_provenance_block()}
    {DISCLOSURE}
    {firm_anchor_html()}
    <div class="colophon">Driftwood. State tax law reflects {_esc(AS_OF_LAW)}; last reviewed {_esc(LAST_REVIEWED)}.</div>
  </div>
</div>
</body>
</html>
"""


def render_redirect(target: str, title: str) -> str:
    """A static permanent-redirect stub (GitHub Pages serves no true 301s): an instant meta-refresh —
    which search engines treat as a permanent redirect — reinforced by rel=canonical so the flat URL's
    SEO equity consolidates onto the editioned canonical. A visible link covers no-JS and humans."""
    return (f'<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8" />\n'
            f'<title>{_esc(title)}</title>\n'
            f'<link rel="canonical" href="{target}" />\n'
            f'<meta http-equiv="refresh" content="0; url={target}" />\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1" />\n'
            f'</head>\n<body>\n'
            f'<p>This page has permanently moved to <a href="{target}">{target}</a>.</p>\n'
            f'</body>\n</html>\n')


def export_state_pages(out_dir: str | Path = "docs", edition: str = CURRENT_EDITION) -> list[str]:
    """Publish the editioned Atlas: the canonical /atlas/{edition}/{state}/ pages + the edition index,
    with the flat *-tax.html and states.html slugs kept as permanent redirect aliases, and /atlas/
    redirecting to the current edition. Returns the list of written paths (relative to out_dir)."""
    out_dir = Path(out_dir)
    pages = build_state_pages()
    written = []
    for code, data in pages.items():
        # The canonical editioned page at /atlas/{edition}/{slug}/index.html.
        d = out_dir / atlas_path(code, edition)
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(render_state_html(data, edition))
        written.append(f"{atlas_path(code, edition)}/index.html")
        # The flat legacy slug lives on as a permanent redirect to the editioned canonical.
        (out_dir / page_path(code)).write_text(
            render_redirect(atlas_url(code, edition), f"{data['name']} tax — moved to {edition} edition"))
        written.append(page_path(code))
    # The edition index, and the flat states.html as its permanent redirect alias.
    edir = out_dir / "atlas" / edition
    edir.mkdir(parents=True, exist_ok=True)
    (edir / "index.html").write_text(render_states_index(pages, edition))
    written.append(f"atlas/{edition}/index.html")
    (out_dir / "states.html").write_text(
        render_redirect(edition_url(edition), "State tax reference — moved"))
    written.append("states.html")
    # /atlas/ always resolves to the current edition.
    (out_dir / "atlas" / "index.html").write_text(
        render_redirect(edition_url(edition), "The State Tax Atlas"))
    written.append("atlas/index.html")
    return written


# Core (non-state) pages that also belong in the sitemap, with priorities.
_CORE_SITEMAP = [
    ("index.html", "1.0", "weekly"), ("insights.html", "0.9", "weekly"),
    ("every-portfolio-has-two-returns.html", "0.8", "monthly"),
    ("principles.html", "0.9", "monthly"),
    ("about.html", "0.9", "monthly"),
    ("taxlab.html", "0.9", "weekly"),
    ("leakage.html", "0.9", "monthly"), ("statemap.html", "0.8", "monthly"),
    ("concentration.html", "0.8", "monthly"),
    ("states.html", "0.8", "monthly"), ("thesis.html", "0.7", "monthly"),
    ("ledger.html", "0.5", "weekly"), ("tearsheet.html", "0.5", "weekly"),
    ("equities.html", "0.4", "weekly"), ("equities_case_studies.html", "0.4", "weekly"),
]


def render_sitemap(edition: str = CURRENT_EDITION, extra: list[tuple[str, str, str]] = ()) -> str:
    # The sitemap lists CANONICAL URLs only — the editioned pages and the edition index — never the
    # flat redirect aliases (which would be duplicate content). states.html → the edition index.
    # `extra` lets a caller (the CLI) append other canonical Atlas surfaces (e.g. the Comparison
    # instrument index + featured corridors) without statepage importing those modules.
    core = [(loc, pr, cf) for (loc, pr, cf) in _CORE_SITEMAP if loc != "states.html"]
    core.append((f"atlas/{edition}/", "0.8", "monthly"))
    state_urls = [(f"{atlas_path(c, edition)}/", "0.7", "monthly") for c in STATE_PAGE_CODES]
    body = "\n".join(
        f"  <url><loc>{BASE_URL}/{loc}</loc><changefreq>{cf}</changefreq><priority>{pr}</priority></url>"
        for loc, pr, cf in (core + state_urls + list(extra)))
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            "<!-- Driftwood — generated by drift states (src/drift/statepage.py). -->\n"
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{body}\n</urlset>\n")


def export_sitemap(out_dir: str | Path = "docs", extra: list[tuple[str, str, str]] = ()) -> Path:
    p = Path(out_dir) / "sitemap.xml"
    p.write_text(render_sitemap(extra=extra))
    return p
