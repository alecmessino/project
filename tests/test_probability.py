import math

import pytest

from mrbet import probability as p


def test_american_to_decimal():
    assert p.american_to_decimal(100) == pytest.approx(2.0)
    assert p.american_to_decimal(-110) == pytest.approx(1.909, abs=1e-3)
    assert p.american_to_decimal(150) == pytest.approx(2.5)


def test_american_to_profit():
    assert p.american_to_profit(-110) == pytest.approx(0.909, abs=1e-3)
    assert p.american_to_profit(100) == pytest.approx(1.0)


def test_implied_prob_roundtrip_favorite_and_dog():
    # -110 both sides -> ~52.38% each (vig).
    assert p.american_to_implied_prob(-110) == pytest.approx(0.5238, abs=1e-3)
    assert p.american_to_implied_prob(100) == pytest.approx(0.5)
    assert p.american_to_implied_prob(150) == pytest.approx(0.4)


def test_prob_over_symmetry():
    # At the mean, half-point line -> ~50/50.
    assert p.prob_over(200.5, 200.5, 10) == pytest.approx(0.5, abs=1e-6)
    assert p.prob_over(200.5, 200.5, 10) + p.prob_under(200.5, 200.5, 10) == pytest.approx(1.0)


def test_prob_over_increases_with_mean():
    low = p.prob_over(200, 195, 10)
    high = p.prob_over(200, 210, 10)
    assert high > low
    assert 0 <= low <= 1 and 0 <= high <= 1


def test_push_prob_zero_for_half_point():
    assert p.push_prob(200.5, 200, 10) == 0.0
    assert p.push_prob(200, 200, 10) > 0.0


def test_ev_sign_matches_edge():
    # Model thinks 60% to win at +100 (even money) -> clearly +EV.
    assert p.expected_value(0.60, 100) > 0
    # 40% at -110 -> -EV.
    assert p.expected_value(0.40, -110) < 0


def test_kelly_zero_when_no_edge():
    # Fair coin at -110 has negative edge -> Kelly 0.
    assert p.kelly_fraction(0.50, -110) == 0.0
    # Real edge -> positive, bounded.
    f = p.kelly_fraction(0.60, -110)
    assert 0 < f <= 1
