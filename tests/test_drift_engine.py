from drift.config import Settings
from drift.engine import Engine
from drift.feed.replay import ReplayFeed
from drift.feed.synthetic import SyntheticFeed
from drift.models import Bar, Side
from drift.triggers import evaluate, to_signal


def _settings():
    # Small windows so tests stay fast but the gate logic is exercised.
    return Settings(
        signal={"lookback": 20, "vol_window": 10, "breakout_channel": 15},
        triggers={"score_threshold": 0.5, "min_weight": 0.0},
    )


def test_evaluate_returns_none_before_warmup():
    s = _settings()
    short = [Bar(asof=str(i), close=100.0 + i) for i in range(5)]
    assert evaluate("X", short, s) is None


def test_uptrend_fires_long_signal():
    s = _settings()
    feed = SyntheticFeed(instruments=("UP",), n_bars=200,
                         regimes=[(200, 0.60)], seed=3)
    fired = []
    Engine(s, feed).run(on_result=lambda r: r.signal and fired.append(r.signal))
    assert fired, "a strong, breakout-confirmed up-trend should fire at least one signal"
    assert all(sig.evaluation.side is Side.LONG for sig in fired)


def test_random_walk_fires_far_fewer_than_trend():
    s = _settings()
    trend = SyntheticFeed(instruments=("T",), n_bars=300, regimes=[(300, 0.60)], seed=1)
    walk = SyntheticFeed(instruments=("W",), n_bars=300, regimes=[(300, 0.0)], seed=1)

    def count(feed):
        n = 0
        Engine(s, feed).run(on_result=lambda r: None if r.signal is None else n)
        c = []
        Engine(s, feed).run(on_result=lambda r: r.signal and c.append(1))
        return len(c)

    assert count(trend) > count(walk)


def test_instrument_filter_skips_untracked():
    s = _settings()
    s.engine.instruments = ["KEEP"]
    bars = {
        "KEEP": [Bar(asof=str(i), close=100.0 + i) for i in range(60)],
        "DROP": [Bar(asof=str(i), close=100.0 + i) for i in range(60)],
    }
    seen = set()
    Engine(s, ReplayFeed(bars)).run(on_result=lambda r: seen.add(r.evaluation.instrument))
    assert seen == {"KEEP"}
