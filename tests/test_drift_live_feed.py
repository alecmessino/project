"""Live-feed tests using fake HTTP sessions — no network calls."""

import pytest

from drift.feed.base import PriceFeed, get_feed
from drift.feed.coinbase import CoinbaseFeed
from drift.feed.polygon import PolygonFeed


class _FakeResp:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload

    def raise_for_status(self):
        pass


class _FakeSession:
    """Records the last request and returns a canned payload."""

    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params))
        return _FakeResp(self.payload)


# --- Coinbase ---------------------------------------------------------------

def test_coinbase_parse_orders_oldest_first():
    # Coinbase returns newest-first: [time, low, high, open, close, volume].
    rows = [
        [200, 9.0, 11.0, 10.0, 10.5, 100.0],
        [100, 8.0, 10.0, 9.0, 9.5, 80.0],
    ]
    bars = CoinbaseFeed.parse_candles(rows)
    assert [b.close for b in bars] == [9.5, 10.5]   # sorted ascending by time
    assert bars[0].high == 10.0 and bars[0].low == 8.0


def test_coinbase_fetch_and_snapshots_with_fake_session():
    rows = [[i, i, i + 2, i, i + 1, 10.0] for i in range(100, 105)]
    feed = CoinbaseFeed(instruments=["BTC-USD"], session=_FakeSession(rows))
    snaps = list(feed.snapshots())
    assert len(snaps) == 5
    assert all("BTC-USD" in s.bars for s in snaps)
    assert isinstance(feed, PriceFeed)
    assert "products/BTC-USD/candles" in feed._session.calls[0][0]


# --- Polygon ----------------------------------------------------------------

def test_polygon_parse_aggs():
    payload = {"results": [
        {"t": 1_700_000_000_000, "o": 1, "h": 3, "l": 0.5, "c": 2, "v": 1000},
        {"t": 1_699_900_000_000, "o": 1, "h": 2, "l": 0.8, "c": 1.5, "v": 900},
    ]}
    bars = PolygonFeed.parse_aggs(payload)
    assert [b.close for b in bars] == [1.5, 2.0]  # sorted ascending by asof
    assert bars[1].high == 3.0


def test_polygon_fetch_requires_key():
    feed = PolygonFeed(instruments=["SPY"], api_key=None, session=_FakeSession({"results": []}))
    feed.api_key = None
    with pytest.raises(RuntimeError, match="POLYGON_API_KEY"):
        feed.fetch("SPY")


def test_polygon_fetch_with_fake_session():
    payload = {"results": [{"t": 1_700_000_000_000 + i * 86_400_000,
                            "o": 1, "h": 2, "l": 0.5, "c": 1 + i, "v": 10}
                           for i in range(3)]}
    feed = PolygonFeed(instruments=["SPY"], api_key="test", session=_FakeSession(payload))
    bars = feed.fetch("SPY")
    assert len(bars) == 3
    url, params = feed._session.calls[0]
    assert "aggs/ticker/SPY/range/1/day" in url
    assert params["apiKey"] == "test"


# --- factory ----------------------------------------------------------------

def test_factory_builds_live_feeds():
    assert isinstance(get_feed("coinbase", instruments=["BTC-USD"]), CoinbaseFeed)
    assert isinstance(get_feed("polygon", instruments=["SPY"], api_key="x"), PolygonFeed)
