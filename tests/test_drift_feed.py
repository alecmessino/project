from drift.feed.base import PriceFeed, get_feed
from drift.feed.replay import ReplayFeed
from drift.feed.synthetic import SyntheticFeed
from drift.models import Bar


def test_feeds_satisfy_protocol():
    assert isinstance(SyntheticFeed(n_bars=10), PriceFeed)
    assert isinstance(ReplayFeed({"X": [Bar("0", 1.0)]}), PriceFeed)


def test_factory_builds_known_feeds():
    assert isinstance(get_feed("synthetic", n_bars=10), SyntheticFeed)
    assert isinstance(get_feed("replay", series={"X": [Bar("0", 1.0)]}), ReplayFeed)


def test_replay_aligns_ragged_series():
    series = {
        "A": [Bar(str(i), 1.0 + i) for i in range(3)],
        "B": [Bar(str(i), 2.0 + i) for i in range(2)],
    }
    snaps = list(ReplayFeed(series).snapshots())
    assert len(snaps) == 3
    assert set(snaps[0].bars) == {"A", "B"}
    assert set(snaps[2].bars) == {"A"}  # B exhausted


def test_bar_defaults_high_low_to_close():
    b = Bar(asof="0", close=42.0)
    assert b.high == 42.0 and b.low == 42.0


def test_synthetic_is_deterministic():
    a = SyntheticFeed(n_bars=50, seed=5).series()
    b = SyntheticFeed(n_bars=50, seed=5).series()
    assert [x.close for x in a] == [x.close for x in b]
