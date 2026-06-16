import math

import pytest

from drift import sizing


def test_annualize_vol():
    assert sizing.annualize_vol(0.01, 252) == pytest.approx(0.01 * math.sqrt(252))
    assert sizing.annualize_vol(0.0, 252) == 0.0


def test_vol_target_weight_scales_inversely_with_vol():
    quiet = sizing.vol_target_weight(1, ann_vol=0.10, target_vol=0.15, max_leverage=2.0)
    wild = sizing.vol_target_weight(1, ann_vol=0.30, target_vol=0.15, max_leverage=2.0)
    assert quiet > wild > 0
    assert quiet == pytest.approx(1.5)  # 0.15 / 0.10


def test_vol_target_weight_capped_and_signed():
    capped = sizing.vol_target_weight(1, ann_vol=0.01, target_vol=0.15, max_leverage=2.0)
    assert capped == pytest.approx(2.0)
    short = sizing.vol_target_weight(-1, ann_vol=0.15, target_vol=0.15, max_leverage=2.0)
    assert short == pytest.approx(-1.0)
    assert sizing.vol_target_weight(0, 0.1, 0.15, 2.0) == 0.0


def test_kelly_leverage_zero_without_edge():
    assert sizing.kelly_leverage(-0.01, 0.0004, 5.0) == 0.0
    assert sizing.kelly_leverage(0.0, 0.0004, 5.0) == 0.0


def test_kelly_leverage_is_mu_over_variance_capped():
    f = sizing.kelly_leverage(0.001, 0.0004, max_leverage=10.0)
    assert f == pytest.approx(0.001 / 0.0004)
    assert sizing.kelly_leverage(1.0, 0.0004, max_leverage=3.0) == 3.0


def test_edge_net_of_cost_subtracts_round_trip():
    # expected 2bps/bar over 10 bars = 200bps gross, minus 2*5bps round trip.
    edge = sizing.edge_net_of_cost(0.0002, hold_bars=10, cost_bps_per_side=5.0)
    assert edge == pytest.approx(0.0002 * 10 - 2 * 0.0005)


def test_edge_net_of_cost_can_go_negative_when_cost_dominates():
    edge = sizing.edge_net_of_cost(0.00001, hold_bars=1, cost_bps_per_side=20.0)
    assert edge < 0
