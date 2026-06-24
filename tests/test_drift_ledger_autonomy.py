"""Adversarial autonomy tests for the daily forward-ledger pipeline.

Proves the loud-failure contract: a rate-limited/outage run exits non-zero and NEVER silently
rewrites the ledger as a success, while a healthy run with no fresh bar is a clean no-op.
"""
import json
from dataclasses import replace
from datetime import date, timedelta

from typer.testing import CliRunner

from drift import ledger as L
from drift.cli import app
from drift.config import Settings
from drift.feed.synthetic import SyntheticFeed

runner = CliRunner()
SYMS = ["S0", "S1", "S2", "S3", "S4"]
CONFIG = "config/drift.yaml"
SET = Settings.load(CONFIG)


def _bars(name, n=400, seed=7, days0=0):
    start = date(2020, 1, 1)
    bars = SyntheticFeed(instruments=(name,), n_bars=n, regimes=[(n, 0.2)], seed=seed).series(name)
    return [replace(b, asof=(start + timedelta(days=days0 + k)).isoformat()) for k, b in enumerate(bars)]


def _series(syms=SYMS, n=400):
    return {s: _bars(s, n=n, seed=10 + i) for i, s in enumerate(syms)}


class _FakeFeed:
    """Returns bars per symbol; a symbol mapped to None raises (simulating a 429)."""
    def __init__(self, table, **kw):
        self.table = table

    def fetch(self, sym):
        b = self.table.get(sym)
        if b is None:
            raise ConnectionError("429 rate limited")
        return b


def _install(monkeypatch, table):
    monkeypatch.setattr("drift.feed.yahoo.YahooFeed", lambda **kw: _FakeFeed(table, **kw))


def _invoke(p, out):
    return runner.invoke(app, ["ledger", "--state", str(p), "--out", str(out),
                               "--equities", ",".join(SYMS), "--pause", "0",
                               "--seed-sessions", "30", "--config", CONFIG])


def test_all_429_exits_nonzero_without_rewriting(tmp_path, monkeypatch):
    series = _series()
    p = tmp_path / "ledger.json"
    p.write_text(json.dumps(L.seed_ledger(series, SET, sessions=30)))
    original = p.read_text()
    _install(monkeypatch, {})                       # every fetch raises -> 0% coverage
    r = _invoke(p, tmp_path / "l.html")
    assert r.exit_code != 0                          # LOUD failure, not a silent success
    assert p.read_text() == original                 # ledger NOT rewritten


def test_coverage_gate_partial_raises(tmp_path, monkeypatch):
    series = _series()
    p = tmp_path / "ledger.json"
    p.write_text(json.dumps(L.seed_ledger(series, SET, sessions=30)))
    _install(monkeypatch, {s: series[s] for s in SYMS[:2]})   # 2/5 = 40% < 60%
    r = _invoke(p, tmp_path / "l.html")
    assert r.exit_code != 0


def test_healthy_no_new_bar_is_clean_noop(tmp_path, monkeypatch):
    series = _series()
    p = tmp_path / "ledger.json"
    led = L.seed_ledger(series, SET, sessions=30)
    p.write_text(json.dumps(led))
    n = len(led["entries"])
    table = dict(series); table["VT"] = _bars("VT", seed=1); table["VTI"] = _bars("VTI", seed=2)
    _install(monkeypatch, table)                     # full coverage, same latest bar
    r = _invoke(p, tmp_path / "l.html")
    assert r.exit_code == 0                           # healthy no-op exits clean
    assert len(json.loads(p.read_text())["entries"]) == n   # nothing appended


def test_fresh_bar_appends_exactly_one(tmp_path, monkeypatch):
    full = _series(n=400)
    trunc = {s: full[s][:-1] for s in SYMS}           # seed missing the last day
    p = tmp_path / "ledger.json"
    led = L.seed_ledger(trunc, SET, sessions=30)
    p.write_text(json.dumps(led))
    n = len(led["entries"])
    table = dict(full); table["VT"] = _bars("VT", seed=1); table["VTI"] = _bars("VTI", seed=2)
    _install(monkeypatch, table)                      # one newer bar across the universe
    r = _invoke(p, tmp_path / "l.html")
    assert r.exit_code == 0
    assert len(json.loads(p.read_text())["entries"]) == n + 1   # autonomy: exactly one session
