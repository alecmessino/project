"""Guards for the per-state SEO landing pages (src/drift/statepage.py).

These pages advertise an illustrative performance figure to the public, one per state, so every one must
carry the same SEO scaffolding AND the full RIA + hypothetical-performance disclosure the interactive
exhibits do — and its number must match the single source of truth (leakage.STATE_ALPHA). If a future
change drops a disclosure, breaks a canonical, or lets a page's alpha drift from the table, this fails.
"""

import pytest

from drift import statepage as SP
from drift.leakage import STATE_ALPHA, STATE_NAMES
from drift.statemap import AS_OF_LAW

PAGES = SP.build_state_pages()

# The disclosure strings the Marketing Rule guards (mirrors tests/test_drift_disclosures.py).
_REQUIRED_DISCLOSURE = [
    "Park Avenue Securities",
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
    # The canonical is the editioned publication URL.
    assert name in h and f'href="{SP.atlas_url(code)}"' in h
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
    """The capture converts in place, posts to Driftwood, and promises only what it can keep.

    This test used to assert the OPPOSITE of its first rule: it required "api.web3forms.com" and
    "access_key" to be present, which pinned all fifty-one Atlas pages to posting a stranger's
    address straight from the browser to a third party, under a key anyone could read in the page
    source. The honesty guardrails it carried are kept verbatim below, because they were right.
    """
    h = SP.render_state_html(PAGES[code])
    assert 'id="capform"' in h                              # inline lead capture, converts in place
    assert '"/api/request"' in h                            # Driftwood's own endpoint
    assert f'state:"{code}"' in h                           # tagged for attribution
    assert "report is on its way" not in h                  # honesty guardrail (mirror of the taxlab test)
    assert "within a business day" in h                     # honest manual-follow-up framing
    assert "consent_text" in h                              # what they agreed to is recorded


@pytest.mark.parametrize("code", ["CA", "TX", "NY", "IL"])
def test_no_state_page_hands_an_address_to_a_third_party(code):
    """A prospect's email address leaves the browser for exactly one destination: Driftwood's own
    endpoint. No form service, no embedded key, no cross-origin POST — this is the specific defect
    that shipped on every Atlas page until 2026-08-01, and the reason it survived so long is that
    the test above required it."""
    h = SP.render_state_html(PAGES[code])
    for token in ("web3forms", "access_key", "formspree", "cf6b1c2d"):
        assert token not in h.lower(), f"{code}: capture still references {token!r}"


def test_sitemap_lists_editioned_canonicals_not_flat_aliases():
    xml = SP.render_sitemap()
    # core + the edition index + one URL per state. This used to read `len(_CORE_SITEMAP) +
    # len(STATE_PAGE_CODES)`, which only balanced because "states.html" sat in _CORE_SITEMAP purely
    # to be filtered out and replaced by the edition index — the +1 and the -1 cancelled. That
    # sentinel was removed on 2026-07-31 (it was never emitted and made the list read as if the
    # flat alias were being announced), so the arithmetic is now stated plainly.
    assert xml.count("<loc>") == len(SP._CORE_SITEMAP) + 1 + len(SP.STATE_PAGE_CODES)
    for code in SP.STATE_PAGE_CODES:
        assert SP.atlas_url(code) in xml, f"sitemap missing editioned {code}"
    assert SP.edition_url() in xml                              # the edition index (replaces states.html)
    # The flat redirect aliases must NOT appear (they would be duplicate content).
    assert f"{SP.BASE_URL}/{SP.page_path('CA')}" not in xml
    assert f"{SP.BASE_URL}/states.html" not in xml


def test_states_index_links_every_editioned_page_and_discloses():
    idx = SP.render_states_index(PAGES)
    for code in SP.STATE_PAGE_CODES:
        assert f'href="{SP.atlas_url(code)}"' in idx, f"index missing {code}"
    assert "Park Avenue Securities" in idx
    assert "adviserinfo.sec.gov" not in idx


def test_flat_slugs_are_permanent_redirects_to_the_editioned_canonical():
    stub = SP.render_redirect(SP.atlas_url("CA"), "moved")
    assert 'http-equiv="refresh"' in stub and f'content="0; url={SP.atlas_url("CA")}"' in stub
    assert f'rel="canonical" href="{SP.atlas_url("CA")}"' in stub


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
        n = h.replace(STATE_NAMES[code], "STATE").replace(SP.slug_for(code), "slug").replace(SP.state_slug(code), "slug")
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


def test_export_writes_editioned_pages_and_redirect_aliases(tmp_path):
    written = SP.export_state_pages(tmp_path)
    # 51 editioned pages + 51 flat redirect aliases + edition index + states.html alias +
    # /atlas/ redirect + the 51 partner briefs, which are published in the same pass so a state
    # page can never link a brief the build did not write.
    assert len(written) == 51 * 3 + 3
    assert (tmp_path / "atlas" / "2026" / "california" / "index.html").exists()   # editioned canonical
    assert (tmp_path / "california-tax.html").exists()                            # flat redirect alias
    assert (tmp_path / "atlas" / "2026" / "index.html").exists()                  # edition index
    assert (tmp_path / "atlas" / "index.html").exists()                          # /atlas/ → current edition
    assert (tmp_path / "states.html").exists()                                    # flat index alias
    SP.export_sitemap(tmp_path)
    assert (tmp_path / "sitemap.xml").exists()


# ── Collisions ────────────────────────────────────────────────────────────────────────────────────
# These are the most assertive statements of law on an Atlas page, published by a registered
# representative across 51 public URLs, and the first draft of them was refused by three independent
# reviews. Every guard below encodes a specific defect that draft had.
from pathlib import Path as _Path  # noqa: E402

import drift.reasoning as _R  # noqa: E402

ROOT = _Path(__file__).resolve().parents[1]
from drift.state_facts import RATES as _RATES, ESTATE as _ESTATE  # noqa: E402


def _collisions(code):
    env = SP._state_record(code)
    lt = _RATES.get(code, (0.0, 0.0))[0]
    ctx = _R._Ctx(code=code, lt=lt, rate_display=f"{lt * 100:g}%", estate=_ESTATE.get(code), env=env)
    return _R.build_collisions(ctx)


@pytest.mark.parametrize("code", SP.STATE_PAGE_CODES)
def test_a_state_never_spends_one_dimension_twice(code):
    """Two cards closing on `stepup` would state the same basis fact in two voices."""
    cs = _collisions(code)
    assert 0 <= len(cs) <= _R.MAX_COLLISIONS
    assert len({c["closes_on"] for c in cs}) == len(cs), f"{code}: two cards close the same dimension"


def test_no_state_is_given_a_collision_it_does_not_have():
    """Coverage is not the product. The draft that forced two cards onto all 51 states invented two
    archetypes to do it, and both shipped claims that were false outside their showcase state.
    Missouri, New Hampshire and Wyoming tax neither gains nor estates and carry no loss mechanic,
    so nothing collides and the block does not render."""
    empty = [c for c in SP.STATE_PAGE_CODES if not _collisions(c)]
    assert set(empty) == {"MO", "NH", "WY"}, f"the set of no-collision states moved: {empty}"
    h = SP.render_state_html(PAGES["MO"])
    assert "Where two Missouri rules meet" not in h


def test_every_collision_body_is_distinct():
    """A template that reads the same in two states is a template that reads a state's own facts."""
    bodies = [c["body"] for code in SP.STATE_PAGE_CODES for c in _collisions(code)]
    assert len(set(bodies)) == len(bodies), "two states render identical collision prose"


@pytest.mark.parametrize("code", SP.STATE_PAGE_CODES)
def test_collision_copy_holds_the_house_style(code):
    """Rendered, not just the objects: the first draft's em dash was in a CSS comment."""
    for c in _collisions(code):
        for field in (c["title"], c["body"]):
            assert "—" not in field and "–" not in field, f"{code}: dash in collision copy"
            assert " you should " not in f" {field.lower()} ", f"{code}: collision gives advice"


def test_the_specific_false_claims_that_were_caught_cannot_return():
    """Each string below shipped in the reviewed draft and was refused. Named so a future edit that
    reintroduces one fails here rather than in production."""
    every = " ".join(c["title"] + " " + c["body"]
                     for code in SP.STATE_PAGE_CODES for c in _collisions(code))
    # FALSE in 24 of the 33 states it would have rendered on: no death tax does not mean no return.
    assert "no state return follows a death" not in every
    # Read as "municipal bonds buy nothing here" while omitting the untouched federal exemption.
    assert "buys nothing here" not in every
    # Superlatives, and a claim about a household the block cannot know.
    for banned in ("the rarest configuration", "The only shelter", "The largest single basis event"):
        assert banned not in every, f"a refused superlative is back: {banned!r}"


def test_the_muni_collision_quotes_the_ordinary_rate_not_the_capital_gains_rate():
    """Municipal interest is ordinary income. The draft printed Wisconsin's 5.36% long-term rate
    for a decision governed by its 7.65% ordinary rate."""
    for code in ("IA", "IL", "WI"):
        body = next(c["body"] for c in _collisions(code) if c["id"] == "no_muni_shelter")
        assert f"{_RATES[code][1] * 100:g}%" in body, f"{code}: not the ordinary rate"
        assert "federal exemption is unaffected" in body, f"{code}: federal exemption not preserved"


def test_the_inheritance_collision_leads_with_the_close_heir_exemption():
    """The draft manufactured exposure by omitting what the same page says twice elsewhere: close
    heirs are largely or wholly exempt."""
    for code in ("KY", "NE", "NJ", "PA", "MD"):
        cs = {c["id"]: c for c in _collisions(code)}
        assert "heir_class_form" in cs, f"{code}: the inheritance card was crowded out"
        assert _ESTATE[code]["heir_detail"] in cs["heir_class_form"]["body"]


def test_connecticut_gets_no_estate_collision():
    """CT's exemption IS the federal exclusion, so the 'second, lower threshold' this card is
    entirely about does not exist there."""
    assert "estate_and_realization" not in {c["id"] for c in _collisions("CT")}
    assert (_ESTATE["CT"]["exemption_usd"] or 0) >= _R._FED_ESTATE_EXEMPTION


def test_illinois_and_new_york_do_not_share_one_cliff_sentence():
    """Different mechanisms: Illinois taxes essentially the whole estate past $4M; New York phases
    the exclusion out over 105%. The draft reused Illinois's sentence for both."""
    il = next(c["body"] for c in _collisions("IL") if c["id"] == "estate_and_realization")
    ny = next(c["body"] for c in _collisions("NY") if c["id"] == "estate_and_realization")
    assert "essentially the whole estate" in il and "5% over that figure" not in il
    assert "5% over that figure" in ny and "essentially the whole estate" not in ny


def test_no_collision_block_is_published():
    """The collision layer is STAGED, not shipped. Two adversarial reviews refused it, and the
    second found false claims introduced by the first round of fixes. Until the data-layer gaps
    named at the top of reasoning.py's collision section are closed and the copy is cleared, no
    Atlas page may render it. See also test_the_withheld_copy_is_not_wired_into_the_graph."""
    for code in ("IL", "CA", "NJ", "WA", "MD", "PA"):
        h = SP.render_state_html(PAGES[code])
        assert "rules meet" not in h, f"{code}: the withheld collision block is being published"
    built = ROOT / "docs" / "atlas"
    if built.is_dir():
        offenders = [str(f.relative_to(built)) for f in built.rglob("index.html")
                     if "rules meet" in f.read_text(encoding="utf-8")]
        assert not offenders, f"the withheld collision block is in the build: {offenders[:5]}"


def test_the_withheld_copy_is_not_wired_into_the_graph():
    """build_collisions stays importable and tested so the work is not lost, but nothing calls it."""
    assert "collisions" not in _R.build_reasoning("IL", SP._state_record("IL"))
    assert "collisions" not in _R.CHAIN


def test_the_specific_defects_that_blocked_publication_are_recorded():
    """The reasons are load-bearing: without them the next person reads ~250 lines of finished-
    looking code and wires it up."""
    src = (ROOT / "src" / "drift" / "reasoning.py").read_text(encoding="utf-8")
    for reason in ("STAGED, NOT PUBLISHED", "marital deduction", "PAS/OSJ"):
        assert reason in src, f"the withholding rationale no longer explains {reason!r}"
