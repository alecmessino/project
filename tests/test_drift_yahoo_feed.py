"""Yahoo Finance feed tests using a fake HTTP session — no network."""

from drift.feed.base import PriceFeed, get_feed
from drift.feed.yahoo import YahooFeed


class _Resp:
    def __init__(self, payload, status=200):
        self._p, self.status = payload, status

    def json(self):
        return self._p

    def raise_for_status(self):
        if self.status >= 400:
            raise RuntimeError(f"HTTP {self.status}")


class _Session:
    def __init__(self, payload, status=200):
        self.payload, self.status, self.calls = payload, status, []
        self.headers = {}

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params))
        return _Resp(self.payload, self.status)


def _payload():
    # Two bars; the second close is null (holiday) and must be dropped. adjclose
    # differs from close so back-adjustment scales high/low by adjclose/close.
    return {"chart": {"result": [{
        "timestamp": [1_700_000_000, 1_700_086_400, 1_700_172_800],
        "indicators": {
            "quote": [{"high": [11.0, 12.0, 99.0], "low": [9.0, 10.0, 88.0],
                       "close": [10.0, 11.0, None], "volume": [100, 110, 120]}],
            "adjclose": [{"adjclose": [5.0, 5.5, None]}],  # factor 0.5
        },
    }], "error": None}}


def test_parse_chart_drops_null_and_back_adjusts():
    bars = YahooFeed.parse_chart(_payload())
    assert len(bars) == 2                       # null-close bar dropped
    assert bars[0].close == 5.0                 # uses adjclose
    assert bars[0].high == 5.5 and bars[0].low == 4.5   # 11*0.5, 9*0.5
    assert bars[0].low <= bars[0].close <= bars[0].high  # internally consistent
    assert bars[0].volume == 100.0


def test_parse_chart_empty():
    assert YahooFeed.parse_chart({"chart": {"result": []}}) == []
    assert YahooFeed.parse_chart({}) == []


def test_fetch_and_snapshots_with_fake_session():
    feed = YahooFeed(instruments=["SPY"], session=_Session(_payload()))
    snaps = list(feed.snapshots())
    assert len(snaps) == 2
    assert all("SPY" in s.bars for s in snaps)
    assert "chart/SPY" in feed._session.calls[0][0]
    assert isinstance(feed, PriceFeed)


def test_fails_over_to_second_host(monkeypatch):
    # First host raises (status 500), retry path returns the same fake — fetch
    # should still raise only if BOTH hosts fail. Here the session always 500s.
    feed = YahooFeed(instruments=["SPY"], session=_Session(_payload(), status=500))
    raised = False
    try:
        feed.fetch("SPY")
    except Exception:
        raised = True
    assert raised
    assert len(feed._session.calls) == 2        # tried query1 then query2


def test_factory_builds_yahoo_for_equity_aliases():
    for alias in ("yahoo", "equities", "stocks"):
        assert isinstance(get_feed(alias, instruments=["SPY"]), YahooFeed)


def test_params_uses_range_by_default_and_epochs_when_set():
    assert YahooFeed(range="2y")._params() == {"range": "2y", "interval": "1d"}
    # Explicit epoch bounds force true daily history (range=max is coarsened to monthly).
    p = YahooFeed(period1=0, period2=1000)._params()
    assert p["period1"] == 0 and p["period2"] == 1000 and "range" not in p
