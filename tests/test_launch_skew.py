"""Unit tests for the Launch Skew Monitor (real-data pipeline).

These exercise the production modules in launch_skew/: the pegged-asset
exclusion set, the LiquidityFit scoring curve, the LAVL alpha engine, and the
nightly ledger row schema. No network calls; fixtures use real field shapes.
"""
import math
import sys
from dataclasses import dataclass

import pytest

# Ensure the repo root is importable when run from tests/.
sys.path.insert(0, str(__file__).split("tests")[0])

from launch_skew.data.provider import TokenData, SignalScanner  # noqa: E402
from launch_skew.lavl import compute_lavl  # noqa: E402
from launch_skew.ledger import SignalRow  # noqa: E402


def _tok(symbol="SOL", price=150.0, mc=7e10, vol=4e9, chg=4.0):
    return TokenData(
        id=symbol.lower(), symbol=symbol, name=symbol,
        price=price, market_cap=mc, volume_24h=vol, supply=mc / price,
        price_change_24h_pct=chg,
    )


# ---- pegged-asset exclusion -------------------------------------------------
def test_nonspeculative_excludes_stables_and_pegs():
    ns = SignalScanner.NON_SPECULATIVE
    for s in ("USDT", "USDC", "USD1", "USDG", "XAUT", "PAXG"):
        assert s in ns, f"{s} must be excluded from the speculative universe"
    # majors must NOT be excluded
    for s in ("BTC", "ETH", "SOL", "NEAR"):
        assert s not in ns


def test_get_signals_strips_pegged_assets():
    class FakeProv:
        def get_tokens(self, n):
            return [
                _tok("BTC"), _tok("USDT", vol=1e9, mc=1e11),
                _tok("ETH"), _tok("XAUT", vol=1e6, mc=1e10), _tok("SOL"),
            ]
    scanner = SignalScanner(FakeProv())
    out = scanner.get_signals(10)
    symbols = {m.symbol for m in out}
    assert "USDT" not in symbols and "XAUT" not in symbols
    assert "BTC" in symbols and "SOL" in symbols


# ---- LiquidityFit monotonicity (via _calculate_metrics) --------------------
def test_liquidityfit_peaks_in_sweet_spot():
    scanner = SignalScanner(__import__("launch_skew.data.provider", fromlist=["CoinGeckoProvider"]).CoinGeckoProvider())
    # build tokens at different turnovers; turnover = vol/mc
    def tok_at(turnover):
        mc = 1e10
        return _tok("X", mc=mc, vol=mc * turnover, chg=2.0)
    low = scanner._calculate_metrics(tok_at(0.05)).conviction
    sweet = scanner._calculate_metrics(tok_at(0.45)).conviction
    high = scanner._calculate_metrics(tok_at(0.95)).conviction
    # sweet spot scores higher than both thin-liquidity and wash-trading tails
    assert sweet > low, f"sweet {sweet} !> low {low}"
    assert sweet > high, f"sweet {sweet} !> high {high}"


# ---- LAVL alpha engine ------------------------------------------------------
def test_lavl_alpha_rush_for_strong_token():
    t = {"price": 1.39, "chg": 6.0, "high24": 1.42, "low24": 1.36,
         "vol": 3e8, "mc": 4e9, "mcapChg": 3.0}
    r = compute_lavl(t)
    assert r.lavl > 2.5, f"expected ALPHA RUSH, got {r.lavl}"
    assert r.regime_band == "ALPHA RUSH"


def test_lavl_compress_for_dead_token():
    t = {"price": 0.5, "chg": 0.1, "high24": 0.51, "low24": 0.49,
         "vol": 1e5, "mc": 1e7, "mcapChg": 0.0}
    r = compute_lavl(t)
    assert r.lavl < 0.5, f"expected flat, got {r.lavl}"
    assert r.regime_band in ("COMPRESS", "LIQ TRAP")
    assert r.risk_mult == 1.0  # neutral until a derivatives feed is connected


# ---- ledger row schema ------------------------------------------------------
def test_signalrow_roundtrip_fields():
    row = SignalRow(date="2026-08-01", symbol="SOL", name="Solana",
                    price=150.0, market_cap=7e10, turnover_pct=5.0,
                    erosion_ratio=1.2, conviction=72, signal="BUY")
    d = row.to_dict()
    assert d["symbol"] == "SOL" and d["conviction"] == 72
    assert d["roi_30d"] is None and d["survived"] is None
    assert set(d.keys()) >= {"date", "symbol", "price", "signal"}
