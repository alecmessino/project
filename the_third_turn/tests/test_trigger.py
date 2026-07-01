"""The ARM / CONFIRM trigger predicates (Revision 2) — pure, offline."""

import pytest

from config import Constraints
from live_engine import evaluate_confirm, evaluate_lookahead
from sources.base import LiveGameState, Quote

C = Constraints()  # v2 defaults: inning>=5, TTO>=3, top1-4, RE24 edge>=0.5, bullpen<3.8 elite


def confirm_state(**over):
    base = dict(game_pk=1, away="CWS", home="ATL", inning=6, half="top",
                away_score=2, home_score=1, pitcher_id=99, pitcher_name="Test Guy",
                pitch_count=95, batting_slot_due=2, times_through_order=3, status="Live",
                outs=0, on_first=False, on_second=False, on_third=False,
                starter_id=99, starter_on_mound=True, starter_tier="Back")
    base.update(over)
    return LiveGameState(**base)


def quote(line):
    return Quote(book="fanduel", home="ATL", away="CWS", line=line,
                 over_odds=-110, under_odds=-110)


# With pregame 9.0, score 3, inning 6, bases empty: RE24 expected ≈ 7.07, so a
# live line of 6.0 clears the 0.5 edge; 7.5 does not. Bullpen 4.5 = not elite.
GOOD_LINE, HIGH_LINE, WEAK_PEN, ELITE_PEN = 6.0, 7.5, 4.5, 3.0


# ------------------------------- CONFIRM ---------------------------------- #
def test_confirm_fires_when_everything_aligns():
    t = evaluate_confirm(confirm_state(), quote(GOOD_LINE), 9.0, C, WEAK_PEN)
    assert t is not None and t.alert_type == "CONFIRM"
    assert t.edge >= C.line_edge_min_runs


def test_confirm_no_fire_before_min_inning():
    assert evaluate_confirm(confirm_state(inning=4), quote(GOOD_LINE), 9.0, C, WEAK_PEN) is None


def test_confirm_no_fire_below_tto():
    assert evaluate_confirm(confirm_state(times_through_order=2), quote(GOOD_LINE), 9.0, C, WEAK_PEN) is None


def test_confirm_no_fire_outside_top_of_order():
    assert evaluate_confirm(confirm_state(batting_slot_due=6), quote(GOOD_LINE), 9.0, C, WEAK_PEN) is None


def test_confirm_no_fire_when_starter_pulled():
    # Fix #4: a reliever is already on -> thesis void.
    assert evaluate_confirm(confirm_state(starter_on_mound=False), quote(GOOD_LINE), 9.0, C, WEAK_PEN) is None


def test_confirm_suppressed_by_elite_bullpen():
    # Fix #4: an elite pen means a pull neutralizes the Over -> suppress.
    assert evaluate_confirm(confirm_state(), quote(GOOD_LINE), 9.0, C, ELITE_PEN) is None


def test_confirm_no_fire_when_market_has_no_edge():
    # Fix #3: live line already at/above the RE24 expected anchor.
    assert evaluate_confirm(confirm_state(), quote(HIGH_LINE), 9.0, C, WEAK_PEN) is None


def test_confirm_no_fire_without_quote_or_pregame():
    assert evaluate_confirm(confirm_state(), None, 9.0, C, WEAK_PEN) is None
    assert evaluate_confirm(confirm_state(), quote(GOOD_LINE), None, C, WEAK_PEN) is None


def test_confirm_unknown_bullpen_allowed():
    # bullpen quality missing -> annotate, don't suppress.
    assert evaluate_confirm(confirm_state(), quote(GOOD_LINE), 9.0, C, None) is not None


def test_confirm_tier_filter():
    c = Constraints(starter_tier_filter=["Back"])
    assert evaluate_confirm(confirm_state(starter_tier="Ace"), quote(GOOD_LINE), 9.0, c, WEAK_PEN) is None
    assert evaluate_confirm(confirm_state(starter_tier="Back"), quote(GOOD_LINE), 9.0, c, WEAK_PEN) is not None


# ------------------------------- ARM (look-ahead) ------------------------- #
def arm_state(**over):
    # 2 outs, 8-hitter up, TTO 2 -> top-of-order 3rd turn leads off next inning.
    defaults = dict(outs=2, batting_slot_due=8, times_through_order=2)
    defaults.update(over)
    return confirm_state(**defaults)


def test_arm_fires_on_lookahead_state():
    t = evaluate_lookahead(arm_state(), quote(GOOD_LINE), 9.0, C, WEAK_PEN)
    assert t is not None and t.alert_type == "ARM"


def test_arm_needs_two_outs():
    assert evaluate_lookahead(arm_state(outs=1), quote(GOOD_LINE), 9.0, C, WEAK_PEN) is None


def test_arm_needs_bottom_of_order():
    assert evaluate_lookahead(arm_state(batting_slot_due=5), quote(GOOD_LINE), 9.0, C, WEAK_PEN) is None


def test_arm_needs_prior_tto():
    # TTO must be one below target (2), so the NEXT inning's leadoff is TTO 3.
    assert evaluate_lookahead(arm_state(times_through_order=3), quote(GOOD_LINE), 9.0, C, WEAK_PEN) is None


def test_arm_and_confirm_are_disjoint():
    # a confirm-shaped state must not fire ARM, and vice versa.
    assert evaluate_lookahead(confirm_state(), quote(GOOD_LINE), 9.0, C, WEAK_PEN) is None
    assert evaluate_confirm(arm_state(), quote(GOOD_LINE), 9.0, C, WEAK_PEN) is None
