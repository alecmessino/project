"""Per-state SEO landing pages — the organic-search front door to the funnel.

Each of the 50 states + DC gets its own **server-side-rendered** page (content baked into the HTML,
not JS-rendered like the interactive exhibits) so search engines index the state's real tax facts and
the illustrative Structural-Alpha number. The content is assembled entirely from existing sources of
truth — `statemap._state_record` (the 5-dimension dataset) and `leakage.STATE_ALPHA` — so a state page
can never disagree with the map or the diagnostic.

Every page carries: a keyword title/H1/meta, canonical + Open Graph, FAQPage + BreadcrumbList +
FinancialService JSON-LD, the five tax dimensions, the illustrative before/after alpha, a CTA into the
personalized diagnostic (`leakage.html?state=XX`) and booking, related-state internal links, and the
full RIA + hypothetical-performance disclosure. Output is flat `<slug>-tax.html` at the docs root so all
asset paths (driftwood.css, og/, favicon) resolve exactly like the other pages.

    drift states --out-dir docs        # writes <slug>-tax.html for every state + states.html index
"""

from __future__ import annotations

import html
import json
import re
import time
from pathlib import Path

from .leakage import STATE_ALPHA, STATE_NAMES, build_leakage
from .statemap import DIMENSIONS, _state_record

# Single source of truth for the public base URL lives in drift.site (re-exported here for callers
# and tests); flip it with scripts/set_domain.py when the custom domain goes live.
from .site import BASE_URL

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
    return f"{slug_for(code)}.html"


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
           "country. It is a community-property state, so community assets get a full step-up."),
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
        faq.append({"q": f"How much investment tax can tax-managed investing recover in {name}?",
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
        }
    return out


# ── rendering (server-side) ──────────────────────────────────────────────────────────────────────
def _esc(s: str) -> str:
    return html.escape(str(s), quote=True)


NAV = (
    '<nav class="dwnav" aria-label="Driftwood">\n'
    '  <a class="brand" href="index.html">Drift<span class="w">wood</span></a>\n'
    '  <div class="dwnav-links">\n'
    '    <a href="about.html">Our Story</a>\n'
    '    <a href="thesis.html">How We Invest</a>\n'
    '    <a href="taxlab.html?view=prospect">Tax&nbsp;Lab</a>\n'
    '    <a href="leakage.html">Tax&nbsp;Diagnostic</a>\n'
    '    <a href="statemap.html">State Tax Guide</a>\n'
    '    <a href="ledger.html">Research</a>\n'
    '  </div>\n'
    '</nav>'
)

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
    '<b>Illustrative / hypothetical — not a real track record and not advice.</b> The Structural Alpha '
    'figure is a hypothetical, after-tax result from the <b>retroactive application</b> of a '
    'tax-management model to ~30 years of proxy-spliced market data on a single illustrative path; '
    '<b>no client capital was invested</b>, and hypothetical performance <b>does not guarantee future '
    'results</b>. Intended for sophisticated investors; it may not be relevant to your situation, and '
    'your actual figure depends on your own holdings, basis, and bracket. State tax facts reflect tax '
    'year 2025 and can change — confirm with a tax advisor. Driftwood is a '
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
    alpha = (f" A tax-managed book of the same exposure recovers up to ~+{a['value']:.1f}%/yr after tax "
             f"in our illustrative modeling.") if a else ""
    return (f"{name} capital-gains, estate, marriage, and basis-step-up taxes — and where a "
            f"concentrated portfolio leaks return to tax.{rate}{alpha} Illustrative, not advice.")[:300]


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
            f'<div class="dsrc">{_esc(d.get("source", ""))}</div></div>'
        )
    return "\n".join(cards)


def _alpha_hero(name: str, a: dict | None) -> str:
    if not a:
        return ""
    before, after, alpha = a["before"], a["after"], a["value"]
    kept_before = max(2, min(96, round(before / max(after, 0.1) * 100)))
    return (
        f'<div class="hero">'
        f'<div class="big">+{alpha:.1f}<span class="u">%/yr</span></div>'
        f'<div class="hlab">Illustrative Structural&nbsp;Alpha (tax) recovered in {_esc(name)}<br>'
        f'<span class="hsub">the tax-managed book keeps ~{after:.1f}%/yr after tax vs ~{before:.1f}%/yr '
        f'for a concentrated, naive one — illustrative, over ~30 years, figures rounded to 0.1%/yr</span></div>'
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


def _jsonld(name: str, code: str, rec: dict, faq: list[dict]) -> str:
    url = f"{BASE_URL}/{page_path(code)}"
    blocks = [
        {"@context": "https://schema.org", "@type": "FinancialService",
         "name": f"Driftwood — {name} tax-aware investing", "legalName": "Driftwood",
         "url": url, "areaServed": {"@type": "State", "name": name}, "feeBasis": "Fee-only",
         "description": f"Tax-aware investment management for {name} investors — asset location, "
                        f"tax-loss harvesting, and lot protection. Illustrative modeling, not advice."},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Driftwood", "item": f"{BASE_URL}/index.html"},
            {"@type": "ListItem", "position": 2, "name": "State Tax Map", "item": f"{BASE_URL}/statemap.html"},
            {"@type": "ListItem", "position": 3, "name": name, "item": url}]},
    ]
    if faq:
        blocks.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": f["q"],
             "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in faq]})
    return "\n".join(f'<script type="application/ld+json">\n{json.dumps(b)}\n</script>' for b in blocks)


_HEAD_CSS = """
  :root{--bg:#f6f3ec;--soft:#fbf9f4;--line:#e3dccd;--line2:#f0ece2;--chrome:#ece6da;
    --ink:#1d242d;--body:#3a414b;--dim:#5f5d68;--muted:#6f675b;
    --brass:#a9853f;--gold:#c9b896;--teal:#15463a;--teal2:#15806a;--neg:#9b4439;--navy:#1a2330;}
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--body);font:14.5px/1.6 var(--serif);
    -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
  .sheet{max-width:1040px;margin:30px auto;padding:0 20px 50px}
  .frame{background:var(--bg);border:1px solid #d9d2c4;border-radius:12px;overflow:hidden;
    box-shadow:0 1px 2px rgba(20,18,12,.04),0 30px 70px -36px rgba(20,18,12,.46)}
  .bcrumb{padding:12px 40px 0;font-size:11.5px;color:var(--muted)}
  .bcrumb a{color:var(--brass);text-decoration:none} .bcrumb a:hover{text-decoration:underline}
  .hd{padding:22px 40px 6px}
  .eyebrow{font-weight:600;font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--brass);margin-bottom:10px}
  h1{font-family:var(--serif);font-weight:700;font-size:clamp(28px, 2.4vw + 19px, 36px);line-height:1.05;letter-spacing:-.02em;color:var(--ink);margin:0 0 10px}
  .lede{font-size:15px;color:#54545c;margin:0;max-width:76ch}
  .context{font-size:14px;line-height:1.65;color:var(--body);margin:14px 0 0;max-width:76ch;
    border-left:3px solid var(--gold);padding:2px 0 2px 16px}
  .hero{margin:18px 40px 4px;padding:18px 24px;background:var(--navy);border-radius:12px;display:flex;
    align-items:center;gap:20px;flex-wrap:wrap}
  .hero .big{font-variant-numeric:tabular-nums;font-size:44px;font-weight:700;color:#f1ede3;letter-spacing:-.02em;line-height:1}
  .hero .big .u{font-size:18px;color:var(--gold);margin-left:2px}
  .hero .hlab{font-size:13px;color:#dfe4ea;font-weight:600;flex:1;min-width:220px}
  .hero .hsub{font-weight:400;color:#9aa3ae;font-size:12px}
  .hero .hbar{width:100%;height:8px;border-radius:5px;background:var(--neg);overflow:hidden}
  .hero .hbar .kept{display:block;height:100%;background:var(--teal2)}
  .grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;padding:18px 40px 6px}
  @media(max-width:760px){.grid{grid-template-columns:1fr}}
  .dcard{border:1px solid var(--line);border-left:3px solid var(--brass);border-radius:8px;padding:14px 16px;background:#fff}
  .dcard .dh{font-family:var(--sans);font-weight:600;font-size:14.5px;color:var(--ink);margin-bottom:5px;display:flex;align-items:center;gap:8px}
  .dcard .dtag{font-size:10.5px;font-weight:700;color:var(--brass);border:1px solid var(--gold);border-radius:999px;padding:1px 8px}
  .dcard p{margin:0;font-size:12.5px;color:var(--body);line-height:1.5}
  .dcard .dsrc{font-size:10px;color:var(--muted);margin-top:8px}
  .sec{padding:14px 40px 4px}
  .sec .sh{font-weight:600;font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin-bottom:12px}
  .levers{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
  @media(max-width:760px){.levers{grid-template-columns:1fr}}
  .lv{border:1px solid var(--line);border-left:3px solid var(--teal2);border-radius:8px;padding:13px 15px;background:var(--soft)}
  .lv .n{font-weight:600;font-size:13px;color:var(--ink)} .lv .d{font-size:12px;color:var(--body);line-height:1.45;margin-top:4px}
  details.faq{border-bottom:1px solid var(--line2);padding:10px 0}
  details.faq summary{font-weight:600;font-size:13.5px;color:var(--ink);cursor:pointer}
  details.faq p{margin:8px 0 2px;font-size:12.5px;color:var(--body)}
  .cta{margin:20px 40px 4px;padding:20px 24px;background:var(--soft);border:1px solid var(--line);border-radius:12px;
    display:flex;align-items:center;gap:18px;flex-wrap:wrap}
  .cta .ctxt{flex:1;min-width:240px} .cta .ch{font-weight:600;font-size:18px;color:var(--ink);margin-bottom:3px}
  .cta .cd{font-size:12.5px;color:var(--dim)}
  .cta a{text-decoration:none;border-radius:8px;font-size:14px;font-weight:600;white-space:nowrap;padding:12px 20px}
  .cta a.primary{background:var(--teal);color:#f1ede3} .cta a.ghost{border:1px solid #cdc4b2;color:var(--ink);font-weight:500}
  .rel{padding:6px 40px 4px;font-size:12.5px;color:var(--dim)} .rel a{color:var(--teal2);text-decoration:none;font-weight:600}
  .capture{margin:12px 40px 4px}
  .capform{display:flex;gap:8px;flex-wrap:wrap}
  .capform input[type=email]{flex:1;min-width:220px;padding:11px 14px;border:1px solid var(--line);border-radius:8px;font:inherit;font-size:14px;background:#fff}
  .capform button{background:var(--brass);color:#fff;border:0;border-radius:8px;font:inherit;font-weight:600;font-size:14px;padding:11px 18px;cursor:pointer}
  .capform button:disabled{opacity:.6;cursor:default}
  .capnote{font-size:11.5px;color:var(--dim);margin-top:8px} .capnote a{color:var(--teal2)}
  .capok{background:#eef5f0;border:1px solid #cfe0d6;border-left:3px solid var(--teal2);border-radius:8px;padding:14px 16px;font-size:13.5px;color:#244c3f;font-weight:600}
  .vh{position:absolute!important;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);border:0}
  .disc{margin:16px 40px 6px;font-size:10.5px;line-height:1.55;color:var(--muted);border-top:1px solid var(--line);padding-top:12px}
  .disc a{color:var(--teal2)}
  .foot{margin:6px 40px 26px;color:var(--muted);font-size:11px}
  /* Phones: pull the generous 40px editorial gutters in to a comfortable 18px so the prose column
     isn't pinched, consistent with the other exhibits. */
  @media(max-width:600px){
    .bcrumb,.hd,.grid,.sec,.rel{padding-left:18px;padding-right:18px}
    .hero,.cta,.capture,.disc,.foot{margin-left:18px;margin-right:18px}
  }
  @media print{body{background:#fff}.sheet{margin:0;max-width:none}.frame{border:0;box-shadow:none}.cta,.capture,.dwnav{display:none}}
"""

# Web3Forms lead-capture (public key — safe in client code; mirrors taxlab.html CONFIG).
_FORM_EP = "https://api.web3forms.com/submit"
_FORM_KEY = "cf6b1c2d-9971-4256-9ff9-72d6918c84e6"
_FORM_HP = "botcheck"
_CONTACT = "alec.messino@gmail.com"


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
        <button type="submit" id="capsend">Email me {nm}'s 1-pager →</button>
      </form>
      <div class="capnote" id="capnote">A one-page, {nm}-specific tax-leakage breakdown — we'll follow up by email, usually within a business day. We never share your address.</div>
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
          structural_alpha_pct:"{a}", top_lt_rate:"{_esc(rate)}", source:"state_page",
          lead_quality:({a or 0}>=4.5?"high":"standard")}};
        ["utm_source","utm_medium","utm_campaign","utm_term","utm_content"].forEach(function(k){{var v=qp.get(k); if(v)p[k]=v;}});
        p["{_FORM_HP}"]=(document.getElementById("caphp").value||"");
        fetch("{_FORM_EP}",{{method:"POST",headers:{{"Content-Type":"application/json",Accept:"application/json"}},body:JSON.stringify(p)}})
          .then(function(r){{ if(!r.ok) throw 0;
            document.getElementById("capture").innerHTML='<div class="capok" role="status" aria-live="polite">Thanks — we\\'ll email your {nm} tax-leakage breakdown, usually within a business day.</div>';
            if(window.plausible) plausible("lead_submitted",{{props:{{source:"state_page",state:"{code}"}}}}); }})
          .catch(function(){{ btn.disabled=false; btn.textContent="Email me {nm}'s 1-pager →";
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


def render_state_html(data: dict) -> str:
    code, name, slug = data["code"], data["name"], data["slug"]
    rec, a, faq = data["rec"], data["alpha"], data["faq"]
    title = f"{name} Capital Gains & Estate Tax — Tax-Leakage Diagnostic | Driftwood"
    desc = _meta_description(name, rec)
    url = f"{BASE_URL}/{page_path(code)}"
    og = f"{BASE_URL}/og/states/{code.lower()}.png"
    levers = "\n".join(
        f'<div class="lv"><div class="n">{_esc(l["name"])}</div><div class="d">{_esc(l["desc"])}</div></div>'
        for l in data["levers"])
    faq_html = _faq_html(faq).replace("{}", _esc(name)) if faq else ""
    related = " · ".join(
        f'<a href="{page_path(c)}">{_esc(nm)}</a>' for c, nm in data["related"])
    rate = (rec.get("cg") or {}).get("tag", "")
    capture = _capture(code, name, (a or {}).get("value"), rate)
    lede = (f"Every state taxes gains, marriage, and death differently. Here is how {name} treats "
            f"capital gains at the top rate, the marriage penalty, estate and inheritance tax at death, "
            f"municipal-bond interest, the §1202 QSBS exclusion, and a harvested loss — and the after-tax "
            f"Structural Alpha our engine is built to recover from all of it.")
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
<link rel="icon" href="favicon.svg" />
<meta property="og:type" content="website" />
<meta property="og:site_name" content="Driftwood" />
<meta property="og:title" content="{_esc(title)}" />
<meta property="og:description" content="{_esc(desc)}" />
<meta property="og:url" content="{url}" />
<meta property="og:image" content="{og}" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{_esc(title)}" />
<meta name="twitter:description" content="{_esc(desc)}" />
<meta name="twitter:image" content="{og}" />
{_jsonld(name, code, rec, faq)}
<link rel="stylesheet" href="driftwood.css">
<script src="dw-context.js"></script>
<style>{_HEAD_CSS}</style>
</head>
<body>
<div class="sheet">
  <div class="frame">
    {NAV}
    <div class="bcrumb"><a href="index.html">Driftwood</a> › <a href="statemap.html">State Tax Map</a> › {_esc(name)}</div>
    <div class="hd">
      <div class="eyebrow">Driftwood · {_esc(name)} tax profile</div>
      <h1>{_esc(name)}: where your portfolio leaks to tax</h1>
      <p class="lede">{_esc(lede)}</p>
      {summary_p}
      {context_p}
    </div>
    {_alpha_hero(name, a)}
    <div class="grid">
      {_dim_cards(rec)}
    </div>
    <div class="sec"><div class="sh">How the engine plugs the leak</div>
      <div class="levers">{levers}</div></div>
    {faq_html}
    <div class="cta">
      <div class="ctxt">
        <div class="ch">See the number on your own {_esc(name)} portfolio.</div>
        <div class="cd">The personalized diagnostic computes your after-tax, asset-location, and harvesting picture — by bracket and holdings.</div>
      </div>
      <a class="primary" href="leakage.html?state={code}">Run my {_esc(name)} diagnostic →</a>
      <a class="ghost" href="taxlab.html?view=prospect&state={code}">Book a 15-min intro</a>
    </div>
{capture}
    <div class="rel">Compare nearby regimes: {related} · <a href="states.html">all 50 states + DC →</a></div>
    {DISCLOSURE}
    <div class="foot">Driftwood. Tax facts compiled from state statutes, tax year 2025.</div>
  </div>
</div>
</body>
</html>
"""


def render_states_index(pages: dict) -> str:
    """A crawlable directory of every state page — sorted, with each state's rate + illustrative alpha."""
    rows = []
    for code in sorted(pages, key=lambda c: STATE_NAMES[c]):
        d = pages[code]
        a = d["alpha"]
        cg = d["rec"].get("cg")
        rate = _esc(cg["tag"]) if cg else "—"
        alpha = f'+{a["value"]:.1f}%/yr' if a else "—"
        rows.append(f'<tr><td><a href="{page_path(code)}">{_esc(d["name"])}</a></td>'
                    f'<td>{rate}</td><td class="al">{alpha}</td></tr>')
    body = "\n".join(rows)
    url = f"{BASE_URL}/states.html"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
{PLAUSIBLE}
<title>State Capital Gains & Tax-Leakage Guides — all 50 states + DC | Driftwood</title>
<meta name="description" content="Tax-leakage and capital-gains guides for all 50 states and DC — top long-term rate and the illustrative after-tax Structural Alpha our engine targets in each. Illustrative, not advice." />
<link rel="canonical" href="{url}" />
<link rel="icon" href="favicon.svg" />
<meta property="og:type" content="website" />
<meta property="og:site_name" content="Driftwood" />
<meta property="og:title" content="State Capital Gains & Tax-Leakage Guides — Driftwood" />
<meta property="og:description" content="Guides for all 50 states + DC: top long-term capital-gains rate and the illustrative after-tax Structural Alpha in each." />
<meta property="og:url" content="{url}" />
<meta property="og:image" content="{BASE_URL}/og/statemap.png" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="State Tax-Leakage Guides — Driftwood" />
<meta name="twitter:description" content="Capital-gains + Structural Alpha guide for every state." />
<meta name="twitter:image" content="{BASE_URL}/og/statemap.png" />
<link rel="stylesheet" href="driftwood.css">
<script src="dw-context.js"></script>
<style>{_HEAD_CSS}
  table.st{{width:calc(100% - 80px);margin:6px 40px 0;border-collapse:collapse;font-size:13.5px}}
  table.st th,table.st td{{padding:8px 10px;border-bottom:1px solid var(--line2);text-align:right}}
  table.st th:first-child,table.st td:first-child{{text-align:left}}
  table.st thead th{{font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}}
  table.st td.al{{font-weight:700;color:var(--teal);font-variant-numeric:tabular-nums}}
  table.st a{{color:var(--ink);text-decoration:none;font-weight:600}} table.st a:hover{{color:var(--teal2)}}
  @media(max-width:760px){{table.st{{width:100%;margin:6px 0 0}}}}
</style>
</head>
<body>
<div class="sheet">
  <div class="frame">
    {NAV}
    <div class="hd">
      <div class="eyebrow">Driftwood · state tax guides</div>
      <h1>Capital-gains &amp; tax-leakage, state by state</h1>
      <p class="lede">Pick your state for its capital-gains, estate, marriage, and basis-step-up profile —
        and the illustrative after-tax Structural Alpha our engine is built to recover there.</p>
    </div>
    <table class="st">
      <thead><tr><th scope="col">State</th><th scope="col">Top LT rate</th><th scope="col">Structural Alpha</th></tr></thead>
      <tbody>{body}</tbody>
    </table>
    {DISCLOSURE}
    <div class="foot">Driftwood. Tax facts compiled from state statutes, tax year 2025.</div>
  </div>
</div>
</body>
</html>
"""


def export_state_pages(out_dir: str | Path = "docs") -> list[str]:
    """Write every per-state page + the states.html index. Returns the list of written filenames."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pages = build_state_pages()
    written = []
    for code, data in pages.items():
        fn = page_path(code)
        (out_dir / fn).write_text(render_state_html(data))
        written.append(fn)
    (out_dir / "states.html").write_text(render_states_index(pages))
    written.append("states.html")
    return written


# Core (non-state) pages that also belong in the sitemap, with priorities.
_CORE_SITEMAP = [
    ("index.html", "1.0", "weekly"), ("principles.html", "0.9", "monthly"),
    ("about.html", "0.9", "monthly"),
    ("taxlab.html", "0.9", "weekly"),
    ("leakage.html", "0.9", "monthly"), ("statemap.html", "0.8", "monthly"),
    ("concentration.html", "0.8", "monthly"),
    ("states.html", "0.8", "monthly"), ("thesis.html", "0.7", "monthly"),
    ("ledger.html", "0.5", "weekly"), ("tearsheet.html", "0.5", "weekly"),
    ("equities.html", "0.4", "weekly"), ("equities_case_studies.html", "0.4", "weekly"),
]


def render_sitemap() -> str:
    urls = list(_CORE_SITEMAP) + [(page_path(c), "0.7", "monthly") for c in STATE_PAGE_CODES]
    body = "\n".join(
        f"  <url><loc>{BASE_URL}/{loc}</loc><changefreq>{cf}</changefreq><priority>{pr}</priority></url>"
        for loc, pr, cf in urls)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            "<!-- Driftwood — generated by drift states (src/drift/statepage.py). -->\n"
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{body}\n</urlset>\n")


def export_sitemap(out_dir: str | Path = "docs") -> Path:
    p = Path(out_dir) / "sitemap.xml"
    p.write_text(render_sitemap())
    return p
