"""Guards for the per-state SEO landing pages (src/drift/statepage.py).

These pages advertise an illustrative performance figure to the public, one per state, so every one must
carry the same SEO scaffolding AND the full RIA + hypothetical-performance disclosure the interactive
exhibits do — and its number must match the single source of truth (leakage.STATE_ALPHA). If a future
change drops a disclosure, breaks a canonical, or lets a page's alpha drift from the table, this fails.
"""

import pytest

from drift import statepage as SP
from drift.leakage import STATE_ALPHA, STATE_NAMES

PAGES = SP.build_state_pages()

# The disclosure strings the Marketing Rule guards (mirrors tests/test_drift_disclosures.py).
_REQUIRED_DISCLOSURE = [
    "registered investment adviser", "adviserinfo.sec.gov", "Form ADV", "Form CRS",
    "Intended for sophisticated investors", "may not be relevant to your situation",
    "no client capital was invested", "retroactive application", "does not guarantee future results",
]
_REQUIRED_SEO = ['<title>', 'rel="canonical"', 'property="og:image"',
                 'application/ld+json', '"FAQPage"', '"BreadcrumbList"']


def test_all_states_plus_dc_generate():
    assert len(SP.STATE_PAGE_CODES) == 51, "expected 50 states + DC"
    assert set(PAGES) == set(SP.STATE_PAGE_CODES)
    assert "DC" in PAGES and "CA" in PAGES
    assert "NYC" not in PAGES and "—" not in PAGES     # pseudo-keys excluded


def test_slugs_are_unique_and_readable():
    slugs = [SP.slug_for(c) for c in SP.STATE_PAGE_CODES]
    assert len(set(slugs)) == len(slugs), "slug collision"
    assert SP.slug_for("CA") == "california-tax"
    assert SP.slug_for("DC") == "washington-dc-tax"
    assert SP.slug_for("NY") == "new-york-tax"


@pytest.mark.parametrize("code", SP.STATE_PAGE_CODES)
def test_page_carries_seo_and_full_disclosure(code):
    h = SP.render_state_html(PAGES[code])
    name = STATE_NAMES[code]
    assert name in h and f'href="{SP.BASE_URL}/{SP.page_path(code)}"' in h
    for s in _REQUIRED_SEO:
        assert s in h, f"{code}: missing SEO element {s!r}"
    for s in _REQUIRED_DISCLOSURE:
        assert s in h, f"{code}: missing disclosure {s!r}"
    # CTA must route into the personalized funnel for THIS state.
    assert f"leakage.html?state={code}" in h


@pytest.mark.parametrize("code", SP.STATE_PAGE_CODES)
def test_page_alpha_matches_the_source_of_truth(code):
    h = SP.render_state_html(PAGES[code])
    a = STATE_ALPHA[code]
    assert f"+{a['alpha']:.1f}" in h, f"{code}: headline alpha not rendered from STATE_ALPHA"
    assert f"{a['before']:.1f}%/yr" in h and f"{a['after']:.1f}%/yr" in h


@pytest.mark.parametrize("code", ["CA", "TX", "NY", "IL"])
def test_page_has_honest_inline_capture(code):
    h = SP.render_state_html(PAGES[code])
    assert 'id="capform"' in h                              # inline lead capture, converts in place
    assert "api.web3forms.com" in h and "access_key" in h
    assert 'source:"state_page"' in h                       # tagged for attribution
    assert "report is on its way" not in h                  # honesty guardrail (mirror of the taxlab test)
    assert "usually within a business day" in h             # honest manual-follow-up framing


def test_sitemap_covers_core_plus_every_state():
    xml = SP.render_sitemap()
    assert xml.count("<loc>") == len(SP._CORE_SITEMAP) + len(SP.STATE_PAGE_CODES)
    for code in SP.STATE_PAGE_CODES:
        assert f"{SP.BASE_URL}/{SP.page_path(code)}" in xml
    assert f"{SP.BASE_URL}/states.html" in xml


def test_states_index_links_every_page_and_discloses():
    idx = SP.render_states_index(PAGES)
    for code in SP.STATE_PAGE_CODES:
        assert f'href="{SP.page_path(code)}"' in idx, f"index missing {code}"
    for s in ("registered investment adviser", "adviserinfo.sec.gov"):
        assert s in idx


def test_no_tax_state_with_a_loss_quirk_is_not_misstated():
    # MO exempts capital gains but still deducts losses (up to 4.7%). The generic "notax" note claims a
    # harvested loss is "worth only the federal rate", which is FALSE for MO — this guards the fix.
    h = SP.render_state_html(PAGES["MO"])
    assert "losses still deduct" in h, "MO's real loss-deduction quirk was dropped"
    assert "only the federal rate" not in h, "MO page states a false state-tax fact"


def test_pages_carry_a_distinct_profile_summary():
    # Differentiation guard (duplicate-content): the per-state synthesis renders and distinct-profile
    # states do not share it.
    ca = SP._summary("California", PAGES["CA"]["rec"])
    tx = SP._summary("Texas", PAGES["TX"]["rec"])
    ny = SP._summary("New York", PAGES["NY"]["rec"])
    wa = SP._summary("Washington", PAGES["WA"]["rec"])
    assert ca and tx and ny and wa
    assert len({ca, tx, ny, wa}) == 4                       # four distinct profiles -> four distinct summaries
    assert "13.3%" in ca                                    # weaves in the real top rate
    assert "excise" in wa                                   # explains WA's unusual long-term-only excise


# The no-income-tax states are identical on EVERY regime dimension (income/marriage/estate/muni/qsbs/
# loss/step-up), so only hand-authored context can differentiate their pages. This is the evidence-backed
# duplicate-content SEO risk; the guard is that each renders genuinely distinct body prose.
_NO_TAX_CLUSTER = ["AK", "FL", "NV", "NH", "SD", "TN", "TX", "WY"]


def test_no_tax_pages_carry_distinct_hand_authored_context():
    for code in _NO_TAX_CLUSTER:
        assert code in SP._STATE_CONTEXT, f"{code} needs a hand-authored context nugget for dedup"
        h = SP.render_state_html(PAGES[code])
        # the nugget's distinctive opening actually renders on the page
        assert SP._STATE_CONTEXT[code][:48] in h, f"{code} context not rendered"


def test_no_tax_pages_are_not_near_duplicates():
    norm_bodies = []
    for code in _NO_TAX_CLUSTER:
        h = SP.render_state_html(PAGES[code])
        # strip every state-identifying token so what's left is the real body prose
        n = h.replace(STATE_NAMES[code], "STATE").replace(SP.slug_for(code), "slug")
        n = n.replace(f"state={code}", "state=CC").replace(code.lower(), "cc").replace(code, "CC")
        norm_bodies.append(n)
    assert len(set(norm_bodies)) == len(norm_bodies), \
        "no-tax state pages are still near-duplicates after normalizing names — add distinct context"


def test_new_dimensions_surface_on_state_pages():
    h = SP.render_state_html(PAGES["CA"])
    for label in ("Munis", "QSBS", "Losses"):
        assert label in h, f"CA page is missing the {label} dimension card"
    # the muni/qsbs/loss FAQ questions render too
    assert "municipal-bond interest" in h and "§1202" in h


def test_export_writes_all_files(tmp_path):
    written = SP.export_state_pages(tmp_path)
    assert len(written) == 52                              # 51 states + states.html
    assert (tmp_path / "california-tax.html").exists()
    assert (tmp_path / "states.html").exists()
    SP.export_sitemap(tmp_path)
    assert (tmp_path / "sitemap.xml").exists()
