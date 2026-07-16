"""Guards for the Crossing Brief — the directional operating document (PUBLISHING_SPEC §16–17).

The Crossing Brief is a product: a thin, DIRECTIONAL query over the reasoning graph. These tests lock
that it authors nothing (every section projects from the two graph records), that direction matters
(origin→destination ≠ destination→origin), and that the operating structure — coordination table,
stale decisions, phased actions, questions — is driven by the graph primitives, not product prose.
"""
import pytest

from drift import crossing, atlas, reasoning
from drift.crossingpage import (
    render_crossing_html, render_crossing_index_html, export_crossings, sitemap_entries,
)
from drift.statepage import STATE_PAGE_CODES


# ── The graph additions the Crossing Brief reads ─────────────────────────────────────────────────

def test_actions_carry_a_crossing_phase_and_priorities_a_crossing_question():
    rec = atlas.build_state_edition("CA")
    for a in rec["actions"]:
        assert a["crossing_phase"] in ("before", "during", "after")
    for c in rec["coordination"]:
        assert c["crossing_question"] and c["crossing_question"].endswith("?")
    # the additions are on the canonical primitives, so every state inherits them
    for a in reasoning.ACTIONS:
        assert a["crossing_phase"] in ("before", "during", "after")
    for p in reasoning.COORDINATION_PRIORITIES:
        assert p["crossing_question"].endswith("?")


# ── The engine is a directional, projecting query ────────────────────────────────────────────────

def test_slug_and_record_are_directional():
    assert crossing.crossing_slug("IL", "FL") == "illinois-to-florida"
    assert crossing.crossing_slug("FL", "IL") == "florida-to-illinois"
    a, b = crossing.build_crossing("IL", "FL"), crossing.build_crossing("FL", "IL")
    assert a["origin"]["code"] == "IL" and a["destination"]["code"] == "FL"
    assert b["origin"]["code"] == "FL" and b["destination"]["code"] == "IL"
    assert a["thesis"] != b["thesis"]


def test_brief_projects_the_two_state_records_only():
    c = crossing.build_crossing("IL", "FL")
    ro, rd = atlas.build_state_edition("IL"), atlas.build_state_edition("FL")
    so = {s["id"]: s for s in ro["framework"]}
    sd = {s["id"]: s for s in rd["framework"]}
    for s in c["signals"]:
        assert s["from_level"] == so[s["id"]]["level"] and s["to_level"] == sd[s["id"]]["level"]


def test_environment_changed_lists_only_changed_dimensions():
    c = crossing.build_crossing("IL", "FL")
    ro = atlas.build_state_edition("IL")["environment"]
    rd = atlas.build_state_edition("FL")["environment"]
    for x in c["environment_changed"]:
        a, b = ro[x["dim"]], rd[x["dim"]]
        assert a.get("tag") != b.get("tag") or a.get("regime") != b.get("regime")


def test_coordination_flags_newly_opened_priorities_and_uses_real_primitives():
    c = crossing.build_crossing("TX", "CA")   # moving to high-tax opens priorities
    o_ids = {p["id"] for p in atlas.build_state_edition("TX")["coordination"]}
    d_ids = {p["id"] for p in atlas.build_state_edition("CA")["coordination"]}
    newly = d_ids - o_ids
    for r in c["coordination"]:
        assert r["id"] in reasoning.PRIORITY_BY_ID
        assert r["new"] == (r["id"] in newly)
    assert any(r["new"] for r in c["coordination"])   # the move opens at least one


def test_decisions_to_reconsider_are_the_changed_signals():
    c = crossing.build_crossing("IL", "FL")
    changed = [s["id"] for s in c["signals"] if s["from_level"] != s["to_level"]]
    assert c["changed_signal_ids"] == changed
    # Illinois' estate cliff → none is the headline decision to reconsider
    est = next((d for d in c["decisions"] if d["signal"] == "Estate exposure"), None)
    assert est and est["from_level"] == "severe" and est["to_level"] == "none"


def test_actions_are_sequenced_before_during_after_from_the_graph():
    c = crossing.build_crossing("IL", "FL")
    ph = c["actions"]
    assert set(ph) == {"before", "during", "after"}
    # a briefed relocation always establishes domicile during the move
    assert any(a["title"] == "Establish the new domicile" for a in ph["during"])
    # before models the move; after sets up the destination's basis titling
    assert any("domicile" in a["title"].lower() for a in ph["before"])
    assert any(a["references"] == "basis_titling" for a in ph["after"])


def test_directional_asymmetry_moving_to_low_tax_sheds_moving_to_high_tax_adds():
    to_low = crossing.build_crossing("CA", "TX")     # shed coordination
    to_high = crossing.build_crossing("TX", "CA")    # add coordination
    # more after-actions setting up the higher-tax destination than the low-tax one
    assert len(to_high["actions"]["after"]) > len(to_low["actions"]["after"])
    assert any(o["kind"] == "closes" for o in to_low["opportunities"])
    assert any(o["kind"] == "opens" for o in to_high["opportunities"])


def test_questions_include_graph_questions_then_the_universals():
    c = crossing.build_crossing("TX", "CA")
    # every active destination priority's crossing_question should appear
    for p in atlas.build_state_edition("CA")["coordination"]:
        assert p["crossing_question"] in c["questions"]
    # and the move-universal advisor question closes it out
    assert any("advisors" in q for q in c["questions"])


def test_moving_to_the_same_state_changes_nothing():
    c = crossing.build_crossing("TX", "TX")
    assert c["environment_changed"] == [] and c["changed_signal_ids"] == []
    assert "changes little" in c["thesis"]


# ── Rendered surfaces ────────────────────────────────────────────────────────────────────────────

def test_crossing_page_renders_the_operating_document():
    html = render_crossing_html(crossing.build_crossing("IL", "FL"))
    for section in ("Executive summary", "operating environment that changed", "Coordination priorities",
                    "Standing decisions to reconsider", "action register", "Questions worth asking"):
        assert section in html
    assert "Before the move" in html and "During the move" in html and "After the move" in html
    assert "not currently a registered investment adviser" in html and "adviserinfo.sec.gov" not in html
    assert "{" not in html.split("<body>")[1]   # no unfilled f-string braces in the body


def test_index_groups_featured_routes_and_export_writes_one_per_corridor(tmp_path):
    idx = render_crossing_index_html()
    assert "Crossing Brief" in idx and "Moving to Florida" in idx
    written = export_crossings(tmp_path)
    assert any(p.endswith("crossing/index.html") for p in written)
    for o, d in crossing.FEATURED_CROSSINGS:
        assert (tmp_path / "atlas" / "2026" / "crossing" / crossing.crossing_slug(o, d) / "index.html").exists()
    assert len(written) == len(crossing.FEATURED_CROSSINGS) + 1


def test_featured_crossings_are_valid_distinct_directional_pairs():
    seen = set()
    for o, d in crossing.FEATURED_CROSSINGS:
        assert o in STATE_PAGE_CODES and d in STATE_PAGE_CODES and o != d
        assert (o, d) not in seen   # no duplicate directional corridor
        seen.add((o, d))


def test_sitemap_entries_cover_index_plus_every_featured_corridor():
    entries = sitemap_entries()
    assert (f"atlas/2026/crossing/", "0.6", "monthly") in entries
    assert len(entries) == len(crossing.FEATURED_CROSSINGS) + 1
