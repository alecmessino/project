"""Liquidity-Adjusted Velocity & Leverage (LAVL) score.

Honest implementation: components are computed from fields the free CoinGecko
`/coins/markets` call actually returns. Order-book depth, bid-ask spread, and
perpetual funding/OI are NOT available on the free tier, so:

  * Spread proxy   = (high_24h - low_24h) / price          (real, from 24h range)
  * Depth proxy    = total_volume / DEPTH_BASELINE          (real liquidity proxy)
  * POC proxy      = range tightness = 1 - (high-low)/price (real concentration proxy)
  * RiskMult_perp  = 1.0 (NEUTRAL) when no funding/OI feed   (never fabricated)

When a Dune/exchange feed supplies funding_rate + open_interest, pass
`perp={'funding_rate': fr, 'oi': oi, 'oi_avg': oi_avg}` and the real
RiskMult_perp = exp(-lambda * |fr * dOI/OIavg|) is applied.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field

W1 = 0.6          # velocity weight
W2 = 0.4          # divergence weight
LAMBDA = 1.0      # perp sensitivity
DEPTH_BASELINE = 5_000_000.0   # $5M reference liquidity depth


@dataclass
class LAVLResult:
    velo_liq: float
    diverge_vol: float
    risk_mult: float
    perp_available: bool
    lavl: float
    regime: str

    @property
    def regime_band(self) -> str:
        if self.lavl > 2.5:
            return "ALPHA RUSH"
        if self.lavl >= 0.5:
            return "STABLE"
        if self.lavl < -1.0:
            return "LIQ TRAP"
        return "COMPRESS"


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def compute_lavl(
    token: dict,
    perp: dict | None = None,
) -> LAVLResult:
    """token keys (from CoinGecko / build()):
        price, chg (24h %), high24, low24, vol (24h volume), mc (market cap),
        mcap_chg (24h market-cap % change, divergence proxy)
    perp (optional): {'funding_rate': float, 'oi': float, 'oi_avg': float}
    """
    price = float(token.get("price") or 0.0)
    chg = float(token.get("chg") or 0.0)
    high24 = float(token.get("high24") or price)
    low24 = float(token.get("low24") or price)
    vol = float(token.get("vol") or 0.0)
    mc = float(token.get("mc") or 0.0)
    mcap_chg = float(token.get("mcap_chg") or 0.0)

    # --- 1. Liquidity-Adjusted Velocity ---
    spread = max((high24 - low24) / price, 0.001) if price > 0 else 0.001
    depth_ratio = max(vol / DEPTH_BASELINE, 1e-4)
    log_depth = math.log(depth_ratio)
    price_delta = chg / 100.0
    velo_liq = (price_delta / spread) * log_depth
    velo_liq = _clamp(velo_liq, -4.0, 4.0)

    # --- 2. Volume Profile Divergence ---
    # vol_shock: current intensity vs a turnover baseline (vol/mc normalized)
    turnover = (vol / mc) if mc > 0 else 0.0
    baseline_turn = 0.05  # ~5% daily turnover reference
    vol_shock = _clamp(turnover / baseline_turn, 0.0, 4.0)
    # POC concentration proxy: tight 24h range => capital concentrated near mid
    poc = _clamp(1.0 - spread, 0.0, 1.0)
    # mcap_chg reinforces accumulation/distribution signal
    diverge_vol = vol_shock * poc * (1.0 + _clamp(mcap_chg / 5.0, -1.0, 1.0))
    diverge_vol = _clamp(diverge_vol, -3.0, 3.0)

    # --- 3. Derivatives Risk Multiplier ---
    if perp and "funding_rate" in perp and "oi" in perp and "oi_avg" in perp:
        fr = float(perp["funding_rate"])
        oi = float(perp["oi"])
        oi_avg = max(float(perp["oi_avg"]), 1.0)
        d_oi = (oi - float(perp.get("oi_hist0", oi_avg))) / oi_avg
        leverage_risk = abs(fr * d_oi)
        risk_mult = math.exp(-LAMBDA * leverage_risk)
        perp_available = True
    else:
        risk_mult = 1.0
        perp_available = False

    lavl = (W1 * velo_liq + W2 * diverge_vol) * risk_mult
    lavl = _clamp(lavl, -5.0, 5.0)

    return LAVLResult(
        velo_liq=round(velo_liq, 4),
        diverge_vol=round(diverge_vol, 4),
        risk_mult=round(risk_mult, 4),
        perp_available=perp_available,
        lavl=round(lavl, 4),
        regime="",
    )
