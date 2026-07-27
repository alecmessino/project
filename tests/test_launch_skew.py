"""Unit tests for the Launch Skew Monitor config schema + demo provider."""

import pytest
from launch_skew.config import Settings


def test_default_settings():
    s = Settings()
    assert s.skew.universe.min_market_cap == 1_000_000
    assert s.skew.universe.max_market_cap == 50_000_000
    assert s.skew.module_a.turnover_sweet_min == 0.30
    assert s.skew.module_a.turnover_sweet_max == 0.60
    assert s.skew.module_b.pressure_threshold == 2.0
    assert s.skew.module_c.residual_threshold == 1.0
    assert s.skew.server.host == "127.0.0.1"
    assert s.skew.server.port == 8766 or s.skew.server.port == 8765


def test_load_from_yaml():
    import tempfile, os
    yaml_content = """
universe:
  min_market_cap: 500000
  max_market_cap: 25000000
module_a:
  turnover_sweet_max: 0.45
module_b:
  pressure_threshold: 1.5
server:
  port: 9999
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        path = f.name
    try:
        s = Settings.load(path)
        assert s.skew.universe.min_market_cap == 500000
        assert s.skew.universe.max_market_cap == 25_000_000
        assert s.skew.module_a.turnover_sweet_max == 0.45
        assert s.skew.module_b.pressure_threshold == 1.5
        assert s.skew.server.port == 9999
    finally:
        os.unlink(path)


def test_signal_gate_conjunctive():
    """A token must pass ALL modules per the conjunctive gate."""
    s = Settings()
    assert s.skew.signal_gate.require_module_a_pass is True
    assert s.skew.signal_gate.require_module_b_pass is True
    assert s.skew.signal_gate.require_module_c_pass is True


def test_demo_provider_snapshot_keys():
    """Demo provider produces well-formed data with all required keys."""
    from launch_skew.web.server import DemoProvider
    s = Settings()
    provider = DemoProvider(s.skew)
    data = provider.snapshot()
    assert "day1" in data
    assert "vesting" in data
    assert "adoption" in data
    assert "signals" in data
    assert "factors" in data
    assert "ranked" in data
    assert "cohort" in data
    assert "institutional" in data
    assert "streaming" in data
    assert len(data["day1"]) >= 1
    assert len(data["vesting"]) >= 1
    assert len(data["ranked"]) >= 1

    # Module A: day1 entries have required keys
    d = data["day1"][0]
    for key in ("symbol", "market_cap", "volume_24h", "turnover_pct",
                "dev_active", "liquidity_depth", "mvrv",
                "holder_concentration", "protocol_revenue_24h"):
        assert key in d

    # Module B: vesting entries have required keys
    v = data["vesting"][0]
    for key in ("symbol", "unlocks_30d", "unlocks_usd", "daily_vol",
                "pressure_x", "cliff_days", "dilution_rate"):
        assert key in v

    # Module C: adoption entries have required keys
    a = data["adoption"][0]
    for key in ("symbol", "active_addr", "price", "trend", "residual",
                "undervalued", "on_trendline", "trajectory"):
        assert key in a

    # Ranked entries have conviction + gate fields
    r = data["ranked"][0]
    for key in ("symbol", "conviction", "score_a", "score_b", "score_c",
                "all_clear", "strong", "passes_a", "passes_b", "passes_c"):
        assert key in r

    # Cohort has survivors + failures
    assert "survivors" in data["cohort"]
    assert "failures" in data["cohort"]

    # Institutional context has key metrics
    inst = data["institutional"]
    for key in ("btc_institutional_pct", "etf_onramp_pct",
                "allocators_increasing", "rwa_tokenized_value_b"):
        assert key in inst


def test_conjunctive_gate_correctness():
    """Only tokens passing all 3 modules appear in signals."""
    from launch_skew.web.server import DemoProvider
    s = Settings()
    provider = DemoProvider(s.skew)
    data = provider.snapshot()
    day1_by_sym = {d["symbol"]: d for d in data["day1"]}
    vest_by_sym = {v["symbol"]: v for v in data["vesting"]}
    adopt_by_sym = {a["symbol"]: a for a in data["adoption"]}
    ranked_by_sym = {r["symbol"]: r for r in data["ranked"]}

    for sig in data["signals"]:
        sym = sig["symbol"]
        d1 = day1_by_sym[sym]
        v = vest_by_sym[sym]
        a = adopt_by_sym[sym]
        r = ranked_by_sym[sym]
        # All gates must be true
        assert r["all_clear"] is True
        assert r["passes_a"] is True
        assert r["passes_b"] is True
        assert r["passes_c"] is True
        # Module A: sweet spot turnover + low holder concentration
        assert 30 <= d1["turnover_pct"] <= 100
        assert d1["holder_concentration"] < 70
        # Module B: pressure below threshold
        assert v["pressure_x"] < 2.0
        # Module C: undervalued (negative residual) or MVRV < 1.0
        assert a["residual"] < 0 or d1["mvrv"] < 1.0


def test_conviction_score_range():
    """Conviction scores must be in [0, 100]."""
    from launch_skew.web.server import DemoProvider
    s = Settings()
    provider = DemoProvider(s.skew)
    data = provider.snapshot()
    for r in data["ranked"]:
        assert 0 <= r["conviction"] <= 100


def test_ranked_sorted_by_conviction():
    """Ranked list must be sorted by conviction descending."""
    from launch_skew.web.server import DemoProvider
    s = Settings()
    provider = DemoProvider(s.skew)
    data = provider.snapshot()
    convictions = [r["conviction"] for r in data["ranked"]]
    assert convictions == sorted(convictions, reverse=True)


def test_cohort_overlay_structure():
    """Cohort overlay contains survivor trajectories for benchmarking."""
    from launch_skew.web.server import DemoProvider, _COHORT_SURVIVORS, _COHORT_FAILURES
    s = Settings()
    provider = DemoProvider(s.skew)
    data = provider.snapshot()
    assert len(data["cohort"]["survivors"]) >= 2
    assert len(data["cohort"]["failures"]) >= 1
    for c in data["cohort"]["survivors"]:
        assert c["survived"] is True
        assert len(c["trajectory"]) >= 3
        assert "cohort" in c
    for c in data["cohort"]["failures"]:
        assert c["survived"] is False


def test_institutional_context_values():
    """Institutional context contains real survey data from EY-Parthenon / Coinbase."""
    from launch_skew.web.server import DemoProvider
    s = Settings()
    provider = DemoProvider(s.skew)
    data = provider.snapshot()
    inst = data["institutional"]
    assert inst["btc_institutional_pct"] == 19.4   # 19.4% BTC held institutionally
    assert inst["etf_onramp_pct"] == 66            # 66% use spot ETFs/ETPs
    assert inst["registered_vehicle_pct"] == 81    # 81% prefer registered vehicles
    assert inst["allocators_increasing"] == 73     # 73% planning to increase
    assert inst["rwa_tokenized_value_b"] == 31     # $31B tokenized RWA AUM
