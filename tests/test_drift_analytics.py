import math

import pytest

from drift import analytics as a


def test_equity_and_max_drawdown():
    eq = a.equity_from_returns([0.1, -0.5, 0.2])
    assert eq[0] == pytest.approx(1.1)
    # peak 1.1 -> trough 0.55 => 50% drawdown
    assert a.max_drawdown(eq) == pytest.approx(0.5, abs=1e-9)


def test_sharpe_zero_without_dispersion():
    assert a.sharpe([0.01, 0.01, 0.01], 252) == 0.0


def test_sharpe_positive_for_positive_drift():
    rets = [0.001 * (1 if i % 2 else -1) + 0.001 for i in range(100)]
    assert a.sharpe(rets, 252) > 0


def test_sortino_ignores_upside_vol():
    # All-positive returns -> no downside -> infinite (capped to None in summary).
    assert a.sortino([0.01, 0.02, 0.03], 252) == float("inf")
    mixed = [0.02, -0.01, 0.03, -0.02]
    assert a.sortino(mixed, 252) != 0.0


def test_cagr_and_calmar():
    eq = a.equity_from_returns([0.0] * 503 + [])  # flat -> 0 cagr
    assert a.cagr(eq, 252) == pytest.approx(0.0, abs=1e-9)
    assert a.calmar(0.2, 0.1) == pytest.approx(2.0)
    assert a.calmar(0.2, 0.0) == 0.0


def test_returns_by_year_buckets_and_compounds():
    dated = [("2020-01-02", 0.1), ("2020-06-01", 0.1), ("2021-03-01", -0.2)]
    by = dict(a.returns_by_year(dated))
    assert by["2020"] == pytest.approx(1.1 * 1.1 - 1.0)
    assert by["2021"] == pytest.approx(-0.2)


def test_summary_block_has_all_metrics():
    dated = [(f"2020-01-{i:02d}", 0.01 * (1 if i % 2 else -1) + 0.002) for i in range(1, 28)]
    s = a.summary(dated, 252)
    for k in ("total_return", "cagr", "sharpe", "sortino", "calmar", "max_drawdown",
              "ann_vol", "hit_rate", "n_bars"):
        assert k in s
