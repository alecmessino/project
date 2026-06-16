from drift.backtest import backtest
from drift.config import Settings
from drift.feed.synthetic import SyntheticFeed


def _settings(cost_bps=5.0):
    return Settings(
        signal={"lookback": 20, "vol_window": 10, "breakout_channel": 15},
        triggers={"score_threshold": 0.5, "min_weight": 0.0},
        sizing={"cost_bps_per_side": cost_bps},
    )


def test_backtest_profits_on_clean_trend():
    s = _settings()
    feed = SyntheticFeed(instruments=("T",), n_bars=400, regimes=[(400, 0.60)], seed=11)
    res = backtest("T", feed.series("T"), s)
    assert res.net_return > 0
    assert res.n_trades >= 1
    assert res.equity_curve  # populated


def test_costs_drag_net_below_gross():
    s = _settings(cost_bps=25.0)  # punitive cost
    feed = SyntheticFeed(instruments=("T",), n_bars=400, regimes=[(400, 0.60)], seed=11)
    res = backtest("T", feed.series("T"), s)
    assert res.gross_return > res.net_return
    assert res.cost_drag > 0


def test_no_lookahead_handles_short_series():
    s = _settings()
    feed = SyntheticFeed(instruments=("T",), n_bars=40, regimes=[(40, 0.6)], seed=1)
    res = backtest("T", feed.series("T"), s)  # mostly warmup -> no blow-ups
    assert res.n_bars == 40
    assert res.max_drawdown >= 0.0
