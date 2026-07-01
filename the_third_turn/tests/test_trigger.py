"""The pure trigger predicate is the heart of the engine — test it offline."""

import pytest

from config import Constraints
from live_engine import evaluate
from sources.base import LiveGameState, Quote


def make_state(**over):
    base = dict(game_pk=1, away="CWS", home="BAL", inning=6, half="top",
                away_score=2, home_score=1, pitcher_id=99, pitcher_name="Test Guy",
                pitch_count=95, batting_slot_due=2, times_through_order=3,
                status="Live")
    base.update(over)
    return LiveGameState(**base)


def make_quote(line=8.0):
    return Quote(book="fanduel", home="BAL", away="CWS", line=line,
                 over_odds=-110, under_odds=-110)


C = Constraints()  # defaults: inning>=6, top1-4, TTO>=3, PC>90, drop<1.5


def test_fires_when_all_conditions_met():
    # pregame 9.0 -> live 8.0 is a 1.0 drop (< 1.5): Over still live.
    trig = evaluate(make_state(), make_quote(8.0), pregame_total=9.0, c=C)
    assert trig is not None
    assert trig.drop == pytest.approx(1.0)
    assert len(trig.reasons) == 5


def test_no_fire_before_min_inning():
    assert evaluate(make_state(inning=5), make_quote(), 9.0, C) is None


def test_no_fire_below_tto():
    assert evaluate(make_state(times_through_order=2), make_quote(), 9.0, C) is None


def test_no_fire_outside_top_of_order():
    assert evaluate(make_state(batting_slot_due=5), make_quote(), 9.0, C) is None


def test_no_fire_at_or_below_pitch_threshold():
    # threshold is strict '>' — exactly 90 must not fire.
    assert evaluate(make_state(pitch_count=90), make_quote(), 9.0, C) is None
    assert evaluate(make_state(pitch_count=91), make_quote(), 9.0, C) is not None


def test_no_fire_when_market_already_faded():
    # drop of 2.0 (>= 1.5) means the Over already moved — skip.
    assert evaluate(make_state(), make_quote(7.0), pregame_total=9.0, c=C) is None


def test_drop_boundary_is_exclusive():
    # exactly 1.5 drop must NOT fire (condition is strict '<').
    assert evaluate(make_state(), make_quote(7.5), pregame_total=9.0, c=C) is None


def test_no_fire_without_state_data():
    assert evaluate(make_state(pitch_count=None), make_quote(), 9.0, C) is None
    assert evaluate(make_state(times_through_order=None), make_quote(), 9.0, C) is None


def test_no_fire_without_quote_or_pregame():
    assert evaluate(make_state(), None, 9.0, C) is None
    assert evaluate(make_state(), make_quote(), None, C) is None
