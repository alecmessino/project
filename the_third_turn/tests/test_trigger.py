"""Per-rule ARM/CONFIRM/WATCH predicates (Revision 3) — pure, offline.

Key property under test: rules match times_through_order EXACTLY, so a TTO2 rule and
a TTO3 rule are independent and never both fire on the same state.
"""

import pytest

from config import Constraints, TriggerRule
from live_engine import evaluate_confirm, evaluate_lookahead, evaluate_rule, evaluate_watch
from sources.base import LiveGameState, Quote

C = Constraints()  # globals: bullpen_elite 3.8, lookahead outs=2 slots=[8,9], edge 0.5

TTO2 = TriggerRule(name="TTO2-Back/Mid", times_through_order=2, top_of_order_slots=[1, 2, 3, 4, 5],
                   starter_tier_filter=["Mid", "Back"], min_inning=3, ttop_run_multiplier=1.15)
TTO3 = TriggerRule(name="TTO3-Mid/Back", times_through_order=3, top_of_order_slots=[1, 2, 3, 4],
                   starter_tier_filter=["Mid", "Back"], min_inning=5, ttop_run_multiplier=1.15)
WATCH = TriggerRule(name="WATCH", kind="watch", enabled=True, starter_tier_filter=["Mid", "Back"],
                    watch_max_inning=4, watch_max_runs=2)

GOOD_LINE, HIGH_LINE, WEAK_PEN, ELITE_PEN = 5.0, 12.0, 4.5, 3.0


def state(**over):
    base = dict(game_pk=1, away="CWS", home="ATL", inning=6, half="top", away_score=2,
                home_score=1, pitcher_id=99, pitcher_name="Test Guy", pitch_count=80,
                batting_slot_due=2, times_through_order=3, status="Live", outs=0,
                on_first=False, on_second=False, on_third=False, starter_id=99,
                starter_on_mound=True, starter_tier="Back")
    base.update(over)
    return LiveGameState(**base)


def q(line=GOOD_LINE):
    return Quote(book="fanduel", home="ATL", away="CWS", line=line)


# --------------------------- exact-TTO independence ---------------------------
def test_tto3_state_fires_tto3_not_tto2():
    s = state(inning=6, times_through_order=3, batting_slot_due=2)
    assert evaluate_confirm(s, q(), 9.0, TTO3, C, WEAK_PEN) is not None
    assert evaluate_confirm(s, q(), 9.0, TTO2, C, WEAK_PEN) is None   # tto != 2


def test_tto2_state_fires_tto2_not_tto3():
    s = state(inning=4, times_through_order=2, batting_slot_due=2)
    assert evaluate_confirm(s, q(), 9.0, TTO2, C, WEAK_PEN) is not None
    assert evaluate_confirm(s, q(), 9.0, TTO3, C, WEAK_PEN) is None   # tto != 3


# ------------------------------- CONFIRM gates --------------------------------
def test_confirm_needs_min_inning():
    assert evaluate_confirm(state(inning=4, times_through_order=3), q(), 9.0, TTO3, C, WEAK_PEN) is None


def test_confirm_needs_slot_in_range():
    assert evaluate_confirm(state(batting_slot_due=6), q(), 9.0, TTO3, C, WEAK_PEN) is None


def test_confirm_blocked_when_starter_pulled():
    assert evaluate_confirm(state(starter_on_mound=False), q(), 9.0, TTO3, C, WEAK_PEN) is None


def test_confirm_suppressed_by_elite_bullpen():
    assert evaluate_confirm(state(), q(), 9.0, TTO3, C, ELITE_PEN) is None


def test_confirm_blocked_by_tier_filter():
    assert evaluate_confirm(state(starter_tier="Ace"), q(), 9.0, TTO3, C, WEAK_PEN) is None


def test_confirm_needs_re24_edge():
    assert evaluate_confirm(state(), q(HIGH_LINE), 9.0, TTO3, C, WEAK_PEN) is None


def test_confirm_unknown_bullpen_allowed():
    assert evaluate_confirm(state(), q(), 9.0, TTO3, C, None) is not None


# --------------------------------- ARM ----------------------------------------
def test_arm_fires_one_turn_early():
    # 2 outs, slot 8, TTO 2 -> TTO3 leads off next inning.
    s = state(inning=6, outs=2, batting_slot_due=8, times_through_order=2)
    assert evaluate_lookahead(s, q(), 9.0, TTO3, C, WEAK_PEN) is not None


def test_arm_needs_two_outs_and_bottom_slot():
    assert evaluate_lookahead(state(outs=1, batting_slot_due=8, times_through_order=2),
                              q(), 9.0, TTO3, C, WEAK_PEN) is None
    assert evaluate_lookahead(state(outs=2, batting_slot_due=5, times_through_order=2),
                              q(), 9.0, TTO3, C, WEAK_PEN) is None


def test_arm_needs_prior_turn():
    # for TTO3 the arming batter must be at TTO 2, not 3.
    assert evaluate_lookahead(state(outs=2, batting_slot_due=8, times_through_order=3),
                              q(), 9.0, TTO3, C, WEAK_PEN) is None


# --------------------------------- WATCH --------------------------------------
def test_watch_fires_low_scoring_early():
    s = state(inning=3, away_score=1, home_score=0, times_through_order=1, batting_slot_due=3)
    assert evaluate_watch(s, q(), 9.0, WATCH, C, WEAK_PEN) is not None


def test_watch_skips_high_scoring_or_late():
    assert evaluate_watch(state(inning=3, away_score=3, home_score=2), q(), 9.0, WATCH, C, WEAK_PEN) is None
    assert evaluate_watch(state(inning=6, away_score=0, home_score=1), q(), 9.0, WATCH, C, WEAK_PEN) is None


# ------------------------------ dispatch --------------------------------------
def test_evaluate_rule_dispatches():
    s = state(inning=6, times_through_order=3, batting_slot_due=2)
    fired = evaluate_rule(TTO3, s, q(), 9.0, C, WEAK_PEN)
    assert [t.trigger_type for t in fired] == ["CONFIRM"]
    watch = evaluate_rule(WATCH, state(inning=3, away_score=0, home_score=0), q(), 9.0, C, WEAK_PEN)
    assert watch and watch[0].trigger_type == "WATCH"


def test_dedupe_key_separates_rules_and_types():
    s = state(inning=6, times_through_order=3, batting_slot_due=2)
    t3 = evaluate_confirm(s, q(), 9.0, TTO3, C, WEAK_PEN)
    assert t3.rule_name == "TTO3-Mid/Back" and t3.trigger_type == "CONFIRM"
    assert "TTO3-Mid/Back" in t3.dedupe_key and t3.dedupe_key.startswith("CONFIRM")
