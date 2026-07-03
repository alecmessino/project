"""Unit tests for the Pinnacle implied-run-distribution math (pure, no I/O)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from team_totals import implied_distribution


def test_devig_sums_to_one_and_centers():
    d = implied_distribution({"0": 100, "1": 100})   # even money each -> 50/50
    assert abs(sum(d["probs"].values()) - 1.0) < 1e-9
    assert abs(d["mean"] - 0.5) < 1e-9


def test_heavy_favorite_pulls_mean_to_that_bucket():
    d = implied_distribution({"0": 10000, "1": 10000, "2": 10000, "3": -100000, "4": 10000})
    assert 2.8 < d["mean"] < 3.2


def test_open_bucket_uses_centroid():
    d = implied_distribution({"0": 100, "8+": 100}, open_centroid=8.5)
    assert abs(d["mean"] - 4.25) < 1e-9        # (0 + 8.5) / 2


def test_low_mass_with_high_tail_is_right_skewed():
    d = implied_distribution({"0": -300, "1": 300, "2": 600, "8+": 700})
    assert d["skew"] > 0


def test_empty_prices_returns_empty():
    assert implied_distribution({}) == {}
    assert implied_distribution({"0": None}) == {}
