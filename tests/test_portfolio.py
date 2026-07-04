"""Guards for the ONE canonical portfolio state (drift.portfolio).

Every research page projects from this object, so these tests pin the invariants that make the old
"three universes / three weights / held-8-vs-9" contradictions impossible: one universe, held+watch
covers it exactly, three DISTINCT weight-like fields, and a deterministic status decision table.
"""

import json

from drift.config import Settings
from drift.portfolio import build_portfolio_state, dashboard_projection, _status, CANON_VERSION
from drift.ledger import seed_ledger
from drift.feed.synthetic import SyntheticFeed


def _settings():
    return Settings(signal={"lookback": 20, "vol_window": 10, "breakout_channel": 15})


def _ledger():
    series = {}
    for i, d in enumerate((0.6, 0.2, -0.1, -0.6)):
        series[f"S{i}"] = SyntheticFeed(instruments=(f"S{i}",), n_bars=250,
                                        regimes=[(250, d)], seed=4 + i).series(f"S{i}")
    return seed_ledger(series, _settings(), sessions=80)


def test_canonical_schema_and_one_universe():
    canon = build_portfolio_state(_ledger(), _settings())
    json.dumps(canon)                                            # JSON-able for embedding
    assert canon["version"] == CANON_VERSION and canon["date"]
    assert {"universe", "holdings", "watch", "rebalance", "performance", "cost"} <= set(canon)
    # held + waiting == the ONE universe — the anti-contradiction invariant
    codes = [h["instrument"] for h in canon["holdings"]] + [w["instrument"] for w in canon["watch"]]
    assert sorted(codes) == sorted(canon["universe"])
    assert len(set(codes)) == len(codes)                        # a name is in exactly one list


def test_three_distinct_weight_fields_never_conflated():
    canon = build_portfolio_state(_ledger(), _settings())
    for r in canon["holdings"] + canon["watch"]:
        assert "portfolio_weight" in r and "signal_strength" in r  # named, distinct
        assert "weight" not in r                                   # never a bare ambiguous "weight"
    # holdings carry a real allocation; watch names are exactly zero-weight and "Waiting"
    assert all(r["portfolio_weight"] > 0 for r in canon["holdings"])
    assert all(r["portfolio_weight"] == 0 and r["status"] == "Waiting" for r in canon["watch"])


def test_status_decision_table():
    # in-book action -> Buy/Increase/Reduce/Hold ; out-of-book -> Sell (EXIT) or Waiting
    assert _status("NEW", True) == "Buy"
    assert _status("ADD", True) == "Increase"
    assert _status("TRIM", True) == "Reduce"
    assert _status(None, True) == "Hold"
    assert _status("EXIT", False) == "Sell"
    assert _status(None, False) == "Waiting"


def test_dashboard_projection_matches_the_canonical_book():
    canon = build_portfolio_state(_ledger(), _settings())
    dash = dashboard_projection(canon)
    # the dashboard's held count IS the book's — it cannot show a different "names held"
    assert dash["header"]["n_held"] == len(canon["holdings"])
    assert dash["header"]["n_universe"] == len(canon["universe"])
    # the performance chart carries a dated x-axis parallel to the equity series
    perf = dash["performance"]
    assert len(perf["dates"]) == len(perf["equity"]) and perf["dates"]


def test_signal_strength_prefers_persisted_signals():
    led = _ledger()
    # seed_ledger persists per-name signals every session; the canonical z should read them
    assert "signals" in led["entries"][-1]
    canon = build_portfolio_state(led, _settings())
    zmap = {r["instrument"]: r["signal_strength"] for r in canon["holdings"] + canon["watch"]}
    for i, sg in led["entries"][-1]["signals"].items():
        assert abs(zmap[i] - round(sg["z"], 4)) < 1e-9
