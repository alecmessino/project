"""The pure RE24 run-environment model (Fix #3) — offline, deterministic."""

import pytest

from shared_piping.run_expectancy import (
    expected_final_total, fraction_remaining, park_factor, re24,
)


def test_re24_known_values():
    assert re24(False, False, False, 0) == pytest.approx(0.481)
    assert re24(True, True, True, 0) == pytest.approx(2.292)   # bases loaded, 0 out
    assert re24(False, False, False, 2) == pytest.approx(0.098)


def test_re24_monotonic_in_outs_and_runners():
    # fewer outs => higher expectancy
    assert re24(True, False, False, 0) > re24(True, False, False, 1) > re24(True, False, False, 2)
    # more runners => higher expectancy
    assert re24(True, True, True, 1) > re24(True, False, False, 1) > re24(False, False, False, 1)


def test_re24_clamps_outs():
    assert re24(False, False, False, 3) == re24(False, False, False, 2)


def test_park_factor_lookup():
    assert park_factor("COL") == 1.20
    assert park_factor("SEA") < 1.0
    assert park_factor("nonsense") == 1.00
    assert park_factor(None) == 1.00


def test_fraction_remaining_bounds():
    assert fraction_remaining(1, "top", 0) == pytest.approx(1.0)
    assert fraction_remaining(9, "bottom", 2) < 0.05
    assert 0.0 <= fraction_remaining(6, "top", 1) <= 1.0


def test_expected_final_rises_with_runners_and_falls_with_outs():
    kw = dict(pregame_total=9.0, runs_so_far=3, inning=6, half="top",
              home_key="ATL", ttop_mult=1.15, in_window=True)
    empty = expected_final_total(outs=0, on_first=False, on_second=False, on_third=False, **kw)
    loaded = expected_final_total(outs=0, on_first=True, on_second=True, on_third=True, **kw)
    two_out = expected_final_total(outs=2, on_first=False, on_second=False, on_third=False, **kw)
    assert loaded.expected_final > empty.expected_final
    assert empty.expected_final > two_out.expected_final


def test_ttop_bump_increases_anchor():
    kw = dict(pregame_total=9.0, runs_so_far=2, inning=6, half="top", outs=0,
              on_first=True, on_second=False, on_third=False, home_key="ATL")
    with_bump = expected_final_total(ttop_mult=1.15, in_window=True, **kw)
    without = expected_final_total(ttop_mult=1.15, in_window=False, **kw)
    assert with_bump.expected_final > without.expected_final


def test_park_scales_situational_premium():
    kw = dict(pregame_total=9.0, runs_so_far=2, inning=6, half="top", outs=0,
              on_first=True, on_second=True, on_third=False, ttop_mult=1.15, in_window=True)
    coors = expected_final_total(home_key="COL", **kw)
    seattle = expected_final_total(home_key="SEA", **kw)
    assert coors.situational > seattle.situational
