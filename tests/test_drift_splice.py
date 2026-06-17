import math

import pytest

from drift.models import Bar
from drift.tearsheet import _splice


def _bars(start_day, n, start_price, step):
    out, p = [], start_price
    for k in range(n):
        out.append(Bar(asof=f"20{start_day + k:02d}-01-01"[:10] if False else f"2010-01-{k+1:02d}",
                       close=round(p, 4), high=p * 1.01, low=p * 0.99))
        p *= math.exp(step)
    return out


def test_splice_prepends_proxy_and_is_continuous():
    # Proxy covers 2008-2010; fund starts 2011. Build by explicit dates instead.
    proxy = [Bar(asof=f"2008-01-{d:02d}", close=10.0 + d) for d in range(1, 6)]   # 11..15
    fund = [Bar(asof=f"2011-01-{d:02d}", close=100.0 + d) for d in range(1, 4)]   # 101..103
    out = _splice(fund, proxy)
    # pre-inception proxy bars are prepended, fund bars unchanged at the end
    assert len(out) == len(proxy) + len(fund)
    assert [b.close for b in out[-3:]] == [101.0, 102.0, 103.0]
    # proxy scaled so its LAST pre bar lines up just below the fund's first level
    # (continuity: scaled proxy preserves proxy RETURNS)
    pre = out[: len(proxy)]
    raw_ret = proxy[1].close / proxy[0].close
    spliced_ret = pre[1].close / pre[0].close
    assert spliced_ret == pytest.approx(raw_ret)          # returns preserved
    factor = fund[0].close / proxy[-1].close
    assert pre[-1].close == pytest.approx(proxy[-1].close * factor)


def test_splice_noop_when_proxy_not_older():
    fund = [Bar(asof="2011-01-01", close=100.0), Bar(asof="2011-01-02", close=101.0)]
    proxy = [Bar(asof="2012-01-01", close=50.0)]           # newer than fund -> ignored
    assert _splice(fund, proxy) == fund


def test_splice_handles_empty():
    fund = [Bar(asof="2011-01-01", close=100.0)]
    assert _splice(fund, []) == fund
    assert _splice([], [Bar(asof="2010-01-01", close=1.0)]) == []
