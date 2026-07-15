"""Guards for the Household Record — the operating file that INDEXES the graph (PUBLISHING_SPEC §16–17).

The Household Record binds the reasoning graph to a household and its governing principle is
**reference, not duplicate**: it authors no reasoning, it points to the authoritative artifacts (the
Atlas page, the Crossing Brief, the Comparison, the Registers, the Annual Review). These tests lock
that binding — the references resolve to the real product URLs, and the summaries project from the
same graph records the other products render.
"""
import pytest

from drift import household, atlas, compare, crossing
from drift.householdpage import (
    render_household_html, render_household_index_html, export_households, sitemap_entries,
)
from drift.statepage import atlas_url, STATE_PAGE_CODES


def _harris():
    return household.build_household_record(household.HOUSEHOLD_BY_ID["harris"])


# ── The record binds the graph; it does not re-author it ─────────────────────────────────────────

def test_standing_decisions_are_the_current_environments_priorities():
    r = _harris()
    cur = atlas.build_state_edition("IL")
    assert [s["id"] for s in r["standing_decisions"]] == [c["id"] for c in cur["coordination"]]
    assert r["coordination"] == cur["coordination"]        # summarised, not restated


def test_references_resolve_to_the_authoritative_product_urls():
    r = _harris()
    R = r["references"]
    assert R["atlas_current"]["url"] == atlas_url("IL")
    assert R["atlas_potential"]["url"] == atlas_url("FL")
    assert R["comparison"]["url"] == compare.compare_url("IL", "FL")
    assert R["crossing"]["url"] == crossing.crossing_url("IL", "FL")
    assert R["decision_register"]["url"].endswith("decision-register.html")
    assert R["opportunity_register"]["url"].endswith("opportunity-register.html")
    assert R["annual_review"]["url"].endswith("awor.html")
    # governing documents point at the standing Record artifacts
    hrefs = {g["url"].rsplit("/", 1)[-1] for g in R["governing"]}
    assert {"constitution.html", "capital-allocation.html", "manual.html"} <= hrefs


def test_crossing_summary_matches_the_crossing_brief():
    r = _harris()
    x = crossing.build_crossing("IL", "FL")
    assert r["crossing"]["thesis"] == x["thesis"]
    assert r["crossing"]["changed"] == len(x["changed_signal_ids"])
    assert r["crossing"]["opened"] == len(x["opened_ids"])


def test_a_settled_household_has_no_move_references():
    r = household.build_household_record(household.HOUSEHOLD_BY_ID["bennett"])
    assert r["potential"] is None and r["crossing"] is None
    assert r["opportunities"] == []
    for k in ("atlas_potential", "comparison", "crossing", "annual_review"):
        assert k not in r["references"]
    assert r["references"]["atlas_current"]["url"] == atlas_url("TX")


def test_sample_households_are_valid_and_distinct():
    ids = [h["id"] for h in household.SAMPLE_HOUSEHOLDS]
    assert len(ids) == len(set(ids))
    for h in household.SAMPLE_HOUSEHOLDS:
        assert h["current"] in STATE_PAGE_CODES
        assert h["potential"] is None or h["potential"] in STATE_PAGE_CODES


# ── Rendered surfaces ────────────────────────────────────────────────────────────────────────────

def test_record_page_indexes_and_links_out_not_duplicates():
    html = render_household_html(_harris())
    assert "The Harris Family" in html
    # the reference-not-duplicate principle is stated and the outward links are present
    assert "Reference, not duplicate" in html
    assert atlas_url("IL") in html and crossing.crossing_url("IL", "FL") in html
    assert compare.compare_url("IL", "FL") in html and "decision-register.html" in html
    assert "awor.html" in html and "constitution.html" in html
    # institutional footer + no unfilled f-string braces in the body
    assert "Driftwood Wealth is a" in html and "adviserinfo.sec.gov" in html
    assert "{" not in html.split("<body>")[1]


def test_settled_record_omits_the_crossing_section():
    html = render_household_html(household.build_household_record(household.HOUSEHOLD_BY_ID["bennett"]))
    assert "Under consideration" not in html
    assert "Crossing Brief →" not in html


def test_index_lists_every_sample_household(tmp_path):
    idx = render_household_index_html()
    for h in household.SAMPLE_HOUSEHOLDS:
        assert household.build_household_record(h)["name"] in idx
        assert household.household_url(h["id"]) in idx
    written = export_households(tmp_path)
    assert (tmp_path / "atlas" / "2026" / "household" / "index.html").exists()
    for h in household.SAMPLE_HOUSEHOLDS:
        assert (tmp_path / "atlas" / "2026" / "household" / h["id"] / "index.html").exists()
    assert len(written) == len(household.SAMPLE_HOUSEHOLDS) + 1


def test_sitemap_entries_cover_index_plus_each_household():
    entries = sitemap_entries()
    assert (f"atlas/2026/household/", "0.5", "monthly") in entries
    assert len(entries) == len(household.SAMPLE_HOUSEHOLDS) + 1
