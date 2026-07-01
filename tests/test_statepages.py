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


def test_export_writes_all_files(tmp_path):
    written = SP.export_state_pages(tmp_path)
    assert len(written) == 52                              # 51 states + states.html
    assert (tmp_path / "california-tax.html").exists()
    assert (tmp_path / "states.html").exists()
    SP.export_sitemap(tmp_path)
    assert (tmp_path / "sitemap.xml").exists()
