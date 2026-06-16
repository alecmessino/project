"""Retry/backoff behavior for the live feeds — no network, no real sleeping."""

import pytest

from drift.feed._retry import with_retries
from drift.feed.coinbase import CoinbaseFeed
from drift.feed.yahoo import YahooFeed


class _Resp:
    def __init__(self, payload):
        self._p = payload

    def json(self):
        return self._p

    def raise_for_status(self):
        pass


class _FlakySession:
    """Raises on the first `fail_n` GETs, then returns `payload`."""

    def __init__(self, payload, fail_n=0):
        self.payload, self.fail_n, self.calls = payload, fail_n, 0
        self.headers = {}

    def get(self, url, params=None, timeout=None):
        self.calls += 1
        if self.calls <= self.fail_n:
            raise ConnectionError("429 rate limited")
        return _Resp(self.payload)


def test_with_retries_succeeds_after_transient_failures():
    seen = []

    def call(attempt):
        seen.append(attempt)
        if attempt < 2:
            raise ConnectionError("boom")
        return "ok"

    assert with_retries(call, attempts=4, backoff=0) == "ok"
    assert seen == [0, 1, 2]            # retried until success


def test_with_retries_reraises_after_exhausting():
    def call(_):
        raise ValueError("always")

    with pytest.raises(ValueError, match="always"):
        with_retries(call, attempts=3, backoff=0)


def _yahoo_payload():
    return {"chart": {"result": [{
        "timestamp": [1_700_000_000, 1_700_086_400],
        "indicators": {"quote": [{"high": [2, 3], "low": [1, 2],
                                  "close": [1.5, 2.5], "volume": [10, 11]}],
                       "adjclose": [{"adjclose": [1.5, 2.5]}]},
    }]}}


def test_yahoo_retries_then_succeeds():
    sess = _FlakySession(_yahoo_payload(), fail_n=2)
    feed = YahooFeed(instruments=["SPY"], session=sess, retries=4, backoff=0)
    bars = feed.fetch("SPY")
    assert len(bars) == 2
    assert sess.calls == 3              # 2 failures + 1 success (host rotated each try)


def test_coinbase_retries_then_succeeds():
    rows = [[i, i, i + 2, i, i + 1, 10.0] for i in range(100, 103)]
    sess = _FlakySession(rows, fail_n=1)
    feed = CoinbaseFeed(instruments=["BTC-USD"], session=sess, retries=3, backoff=0)
    bars = feed.fetch("BTC-USD")
    assert len(bars) == 3
    assert sess.calls == 2


def test_feed_gives_up_and_raises_when_always_failing():
    sess = _FlakySession(_yahoo_payload(), fail_n=99)
    feed = YahooFeed(instruments=["SPY"], session=sess, retries=3, backoff=0)
    with pytest.raises(Exception):
        feed.fetch("SPY")
    assert sess.calls == 3              # exactly `retries` attempts, then give up
