"""Guards for the Comparison instrument (PUBLISHING_SPEC §16–17).

Comparison is a PRODUCT: a thin query over the reasoning graph. These tests lock the two properties
that keep it honest — it authors no facts of its own (every field projects from the two
`atlas.build_state_edition` records), and it is order-independent (a pair has one canonical page).
They also pin the known IL/FL corridor so a regression in the graph surfaces here.
"""
import re

import pytest

from drift import compare, atlas
from drift import reasoning
from drift.comparepage import (
    render_comparison_html, render_compare_index_html, export_comparisons, sitemap_entries,
)
from drift.statepage import STATE_PAGE_CODES, state_slug


# ── The engine is a pure, order-independent query ────────────────────────────────────────────────

def test_comparison_authors_no_facts_it_projects_the_two_state_records():
    c = compare.build_comparison("IL", "FL")
    ra = atlas.build_state_edition(c["a"]["code"])
    rb = atlas.build_state_edition(c["b"]["code"])
    # Every signal's level/reading is exactly the state record's — nothing re-evaluated here.
    for s in c["signals"]:
        assert s["a_level"] == next(x for x in ra["framework"] if x["id"] == s["id"])["level"]
        assert s["b_reading"] == next(x for x in rb["framework"] if x["id"] == s["id"])["reading"]


def test_pair_is_canonical_and_order_independent():
    # compare(FL, IL) and compare(IL, FL) resolve to ONE canonical page with the same A/B assignment.
    assert compare.compare_slug("IL", "FL") == compare.compare_slug("FL", "IL") == "florida-vs-illinois"
    a, b = compare.canonical_pair("IL", "FL")
    assert (a, b) == ("FL", "IL")  # florida sorts before illinois
    c1, c2 = compare.build_comparison("IL", "FL"), compare.build_comparison("FL", "IL")
    assert c1["a"]["code"] == c2["a"]["code"] and c1["b"]["code"] == c2["b"]["code"]
    assert c1["signals"] == c2["signals"]


def test_slug_uses_vs_separator_so_hyphenated_states_are_unambiguous():
    # 'new-york' + 'florida' must not collide with any single hyphenated slug.
    assert compare.compare_slug("NY", "FL") == "florida-vs-new-york"
    assert "-vs-" in compare.compare_slug("DC", "CA")


def test_all_five_framework_signals_align_in_canonical_order():
    c = compare.build_comparison("CA", "TX")
    assert [s["id"] for s in c["signals"]] == [s["id"] for s in reasoning.FRAMEWORK_SIGNALS]
    assert c["signals_total"] == 5


def test_changed_signals_are_exactly_the_level_mismatches():
    c = compare.build_comparison("CA", "TX")
    changed = [s["id"] for s in c["signals"] if s["a_level"] != s["b_level"]]
    assert c["changed_signal_ids"] == changed
    assert c["signals_changed"] == len(changed)


def test_coordination_setdiff_partitions_the_two_states_priorities():
    c = compare.build_comparison("IL", "FL")
    co = c["coordination"]
    a_ids = {p["id"] for p in atlas.build_state_edition(c["a"]["code"])["coordination"]}
    b_ids = {p["id"] for p in atlas.build_state_edition(c["b"]["code"])["coordination"]}
    assert {p["id"] for p in co["only_a"]} == a_ids - b_ids
    assert {p["id"] for p in co["only_b"]} == b_ids - a_ids
    assert {p["id"] for p in co["shared"]} == a_ids & b_ids
    assert c["priorities_changed"] == len(co["only_a"]) + len(co["only_b"])
    # every listed priority is a real, addressable primitive
    for p in co["only_a"] + co["only_b"] + co["shared"]:
        assert p["id"] in reasoning.PRIORITY_BY_ID


def test_the_illinois_florida_corridor_reads_as_expected():
    # Illinois' $4M estate cliff vs Florida's none is the corridor's defining difference.
    c = compare.build_comparison("IL", "FL")
    est = next(s for s in c["signals"] if s["id"] == "estate_exposure")
    fl_lvl = est["a_level"] if c["a"]["code"] == "FL" else est["b_level"]
    il_lvl = est["a_level"] if c["a"]["code"] == "IL" else est["b_level"]
    assert fl_lvl == "none" and il_lvl == "severe"
    assert est["changed"]
    # Illinois opens an estate-structure priority that Florida does not.
    il_only = c["coordination"]["only_a"] if c["a"]["code"] == "IL" else c["coordination"]["only_b"]
    assert "estate_structure" in {p["id"] for p in il_only}


def test_identical_state_compared_with_itself_has_no_differences():
    # A degenerate but useful invariant: nothing differs, no priority changes.
    c = compare.build_comparison("TX", "TX")
    assert c["signals_changed"] == 0 and c["priorities_changed"] == 0
    assert c["environment_diffs"] == []


def test_environment_diffs_only_lists_dimensions_that_actually_differ():
    c = compare.build_comparison("CA", "TX")
    ra = atlas.build_state_edition("CA")["environment"]
    rb = atlas.build_state_edition("TX")["environment"]
    for d in c["environment_diffs"]:
        da, db = ra[d["dim"]], rb[d["dim"]]
        assert (da.get("tag") != db.get("tag")) or (da.get("regime") != db.get("regime"))


# ── The index dataset the browser instrument lays out ────────────────────────────────────────────

def test_index_dataset_covers_every_state_with_decided_reasoning():
    data = compare.index_dataset()
    assert set(data["states"]) == set(STATE_PAGE_CODES)
    assert len(data["signals"]) == len(reasoning.FRAMEWORK_SIGNALS)
    # each state's embedded levels match the canonical graph (the browser never re-derives them)
    for code in ("IL", "CA", "TX"):
        rec = atlas.build_state_edition(code)
        for s in rec["framework"]:
            assert data["states"][code]["signals"][s["id"]]["level"] == s["level"]
        assert data["states"][code]["priorities"] == [c["id"] for c in rec["coordination"]]


def test_featured_corridors_are_valid_distinct_jurisdictions():
    for a, b in compare.FEATURED_CORRIDORS:
        assert a in STATE_PAGE_CODES and b in STATE_PAGE_CODES and a != b


# ── The rendered surfaces ────────────────────────────────────────────────────────────────────────

def test_comparison_page_renders_without_unfilled_placeholders():
    html = render_comparison_html(compare.build_comparison("CA", "TX"))
    assert "California" in html and "Texas" in html
    assert "weighed as two operating environments" in html
    # the compare-specific tally class (renamed to dodge driftwood.css's .tally meter component)
    assert 'class="cmp-tally"' in html and 'class="tally"' not in html
    assert "{" not in html.split("<body>")[1].replace("{", "", 0)  # no stray f-string braces in body
    # RIA identity uses the full legal name; disclosure present
    assert "Driftwood Wealth is a" in html and "adviserinfo.sec.gov" in html


def test_index_embeds_the_graph_and_the_picker():
    html = render_compare_index_html()
    assert "window.__CMP__" in html and 'id="cmpA"' in html and 'id="cmpOut"' in html
    assert '"states"' in html and '"signals"' in html and '"priorities"' in html
    assert "Weigh any two operating environments" in html


def test_export_writes_index_plus_one_page_per_featured_corridor(tmp_path):
    written = export_comparisons(tmp_path)
    slugs = {compare.compare_slug(a, b) for a, b in compare.FEATURED_CORRIDORS}
    assert any(p.endswith("compare/index.html") for p in written)
    assert (tmp_path / "atlas" / "2026" / "compare" / "index.html").exists()
    for slug in slugs:
        assert (tmp_path / "atlas" / "2026" / "compare" / slug / "index.html").exists()
    # one page per DISTINCT canonical corridor (deduped), plus the index
    assert len(written) == len(slugs) + 1


def test_sitemap_entries_are_canonical_and_deduped():
    entries = sitemap_entries()
    locs = [loc for loc, _, _ in entries]
    assert f"atlas/2026/compare/" in locs
    assert len(locs) == len(set(locs))  # no duplicates
