"""Stooq/Tiingo feed parsing + the ledger source-fallback (Yahoo IP-banned on CI -> Stooq/Tiingo)."""
import json
from dataclasses import replace
from datetime import date, timedelta

from typer.testing import CliRunner

from drift import ledger as L
from drift.cli import app
from drift.config import Settings
from drift.feed.stooq import StooqFeed
from drift.feed.tiingo import TiingoFeed
from drift.feed.synthetic import SyntheticFeed

runner = CliRunner()
SYMS = ["S0", "S1", "S2", "S3", "S4"]
CONFIG = "config/drift.yaml"
SET = Settings.load(CONFIG)


class _Resp:
    def __init__(self, text=None, payload=None):
        self._text = text
        self._payload = payload
    def raise_for_status(self):
        return None
    @property
    def text(self):
        return self._text
    def json(self):
        return self._payload


class _Session:
    def __init__(self, resp):
        self._resp = resp
        self.calls = []
    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params))
        return self._resp


def test_stooq_parses_csv():
    csv = "Date,Open,High,Low,Close,Volume\n2026-06-22,10,11,9,10.5,1000\n2026-06-23,10.5,12,10,11.8,1200\n"
    bars = StooqFeed.parse_csv(csv)
    assert len(bars) == 2
    assert bars[-1].asof == "2026-06-23" and bars[-1].close == 11.8
    assert bars[-1].high == 12.0 and bars[-1].low == 10.0


def test_stooq_ignores_challenge_page():
    assert StooqFeed.parse_csv("<!DOCTYPE html><html><body>verify your browser</body></html>") == []
    assert StooqFeed.parse_csv("") == []


def test_stooq_fetch_with_fake_session_adds_us_suffix():
    sess = _Session(_Resp(text="Date,Open,High,Low,Close,Volume\n2026-06-23,1,2,0.5,1.5,9\n"))
    bars = StooqFeed(session=sess, retries=1, backoff=0).fetch("VT")
    assert len(bars) == 1 and bars[0].close == 1.5
    assert sess.calls[0][1]["s"] == "vt.us"          # .us suffix applied


def test_tiingo_parses_adjusted_json():
    rows = [{"date": "2026-06-23T00:00:00Z", "close": 100, "adjClose": 90,
             "high": 105, "adjHigh": 94, "low": 99, "adjLow": 89, "adjVolume": 5}]
    bars = TiingoFeed.parse_json(rows)
    assert len(bars) == 1 and bars[0].close == 90 and bars[0].high == 94   # uses adjusted series
    assert bars[0].asof == "2026-06-23"


def test_tiingo_fetch_with_fake_session():
    sess = _Session(_Resp(payload=[{"date": "2026-06-23", "adjClose": 7.0, "adjHigh": 7.2, "adjLow": 6.8, "adjVolume": 3}]))
    bars = TiingoFeed("TOKEN", session=sess, retries=1, backoff=0).fetch("VTI")
    assert len(bars) == 1 and bars[0].close == 7.0
    assert "VTI/prices" in sess.calls[0][0] and sess.calls[0][1]["token"] == "TOKEN"


def _bars(name, n=400, seed=7, days0=0):
    start = date(2020, 1, 1)
    bars = SyntheticFeed(instruments=(name,), n_bars=n, regimes=[(n, 0.2)], seed=seed).series(name)
    return [replace(b, asof=(start + timedelta(days=days0 + k)).isoformat()) for k, b in enumerate(bars)]


def test_ledger_falls_back_to_stooq_when_yahoo_blocked(tmp_path, monkeypatch):
    """Yahoo raises (IP-banned) for every symbol; Stooq serves a fresh bar -> ledger still appends."""
    full = {s: _bars(s, seed=10 + i) for i, s in enumerate(SYMS)}
    full["VT"] = _bars("VT", seed=1); full["VTI"] = _bars("VTI", seed=2)
    trunc = {s: full[s][:-1] for s in SYMS}                 # seed missing the last day
    p = tmp_path / "ledger.json"
    led = L.seed_ledger(trunc, SET, sessions=30)
    p.write_text(json.dumps(led))
    n = len(led["entries"])

    class _Yahoo:                                            # always blocked
        def __init__(self, **kw): pass
        def fetch(self, sym): raise ConnectionError("429 rate limited")

    class _Stooq:                                            # serves the fresh full series
        def __init__(self, **kw): pass
        def fetch(self, sym): return full[sym]

    monkeypatch.delenv("TIINGO_API_KEY", raising=False)      # force the Stooq path
    monkeypatch.setattr("drift.feed.yahoo.YahooFeed", _Yahoo)
    monkeypatch.setattr("drift.feed.stooq.StooqFeed", _Stooq)
    r = runner.invoke(app, ["ledger", "--state", str(p), "--out", str(tmp_path / "l.html"),
                            "--equities", ",".join(SYMS), "--pause", "0", "--config", CONFIG])
    assert r.exit_code == 0, r.output
    assert len(json.loads(p.read_text())["entries"]) == n + 1   # Stooq fallback advanced the ledger


def _Y_raises():
    class Y:
        def __init__(self, **k): pass
        def fetch(self, s): raise ConnectionError("429 rate limited")
    return Y()


def test_equity_feeds_long_history_requests_deep():
    from drift.feed.resolve import equity_feeds
    chain = equity_feeds(long_history=True, env={})              # no key -> stooq, yahoo
    assert [n for n, _ in chain] == ["stooq", "yahoo"]
    yahoo = dict(chain)["yahoo"]
    assert yahoo.period1 is not None and yahoo.period2 is not None   # explicit ~40y epoch bounds
    chain2 = equity_feeds(long_history=True, env={"TIINGO_API_KEY": "tok"})
    assert chain2[0][0] == "tiingo" and dict(chain2)["tiingo"].lookback_days > 10000
    assert dict(equity_feeds(env={}))["yahoo"].period1 is None       # short path uses range, not bounds


def test_equity_universe_falls_back_to_stooq():
    from drift.case_studies import equity_universe
    syms = ["A", "B", "C"]
    data = {s: _bars(s, seed=i) for i, s in enumerate(syms)}

    class S:
        def __init__(self, **k): pass
        def fetch(self, s): return data[s]
    out = equity_universe(syms, feeds=[("yahoo", _Y_raises()), ("stooq", S())])
    assert set(out) == set(syms) and len(out["A"]) >= 60             # Yahoo blocked -> Stooq served


def test_tearsheet_pull_falls_back_to_stooq():
    from drift.tearsheet import _pull
    syms = ["VTI", "VEA"]
    data = {s: _bars(s, n=400, seed=i) for i, s in enumerate(syms)}

    class S:
        def __init__(self, **k): pass
        def fetch(self, s): return data[s]
    series, applied = _pull(syms, feeds=[("yahoo", _Y_raises()), ("stooq", S())], proxies=False, pause=0)
    assert set(series) == set(syms)                                  # 40y path also survives a Yahoo ban
