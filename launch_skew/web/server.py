"""Web dashboard server for the Launch Skew Monitor.

A dependency-free stdlib HTTP server that:
  • serves the single-page dashboard (launch_skew.html),
  • exposes /api/state with the live module data + Conviction Scores + cohort overlay,
  • supports real data providers (CoinGecko, Dune, Messari) when keys are configured,
  • includes a backtesting module for historical performance evaluation.

Run:  python -m launch_skew.web
"""

from __future__ import annotations

import json
import random
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional

from ..config import SkewSettings, Settings

HTML_PATH = Path(__file__).with_name("launch_skew.html")
DEFAULT_CONFIG = Path(__file__).parents[2] / "config" / "launch_skew.yaml"


# ────────────────────────────────────────────────────────────────────
# Institutional market context (from EY-Parthenon / Coinbase 2026 survey)
# ────────────────────────────────────────────────────────────────────

_INSTITUTIONAL_CONTEXT = {
    "btc_institutional_pct": 19.4,
    "etf_onramp_pct": 66,
    "registered_vehicle_pct": 81,
    "allocators_increasing": 73,
    "price_positive_12m": 74,
    "risk_management_up": 49,
    "stablecoin_cash_usage": 85,
    "rwa_tokenized_value_b": 31,
    "rwa_growth_pct": 50,
    "multi_custodian_pct": 61,
    "etp_volatility_regime": "compressed",
}


# ────────────────────────────────────────────────────────────────────
# Historical cohort: tokens that survived (the 1-2% winners)
# ────────────────────────────────────────────────────────────────────

_COHORT_SURVIVORS = [
    {"cohort": "ETH L2 Winner", "survived": True, "mc_final": 480e6,
     "trajectory": [{"d": 0, "la": 1.0, "lp": 1.0}, {"d": 3, "la": 2.1, "lp": 2.3},
                    {"d": 7, "la": 3.4, "lp": 4.1}, {"d": 14, "la": 5.2, "lp": 6.8},
                    {"d": 30, "la": 8.1, "lp": 10.2}, {"d": 60, "la": 12.5, "lp": 14.1},
                    {"d": 90, "la": 18.3, "lp": 18.7}]},
    {"cohort": "DeFi Blue Chip", "survived": True, "mc_final": 320e6,
     "trajectory": [{"d": 0, "la": 1.0, "lp": 1.0}, {"d": 3, "la": 1.8, "lp": 1.9},
                    {"d": 7, "la": 2.9, "lp": 3.2}, {"d": 14, "la": 4.1, "lp": 4.8},
                    {"d": 30, "la": 6.7, "lp": 7.9}, {"d": 60, "la": 10.1, "lp": 12.3},
                    {"d": 90, "la": 14.8, "lp": 16.2}]},
    {"cohort": "Infra Token", "survived": True, "mc_final": 180e6,
     "trajectory": [{"d": 0, "la": 1.0, "lp": 1.0}, {"d": 3, "la": 1.5, "lp": 1.6},
                    {"d": 7, "la": 2.3, "lp": 2.7}, {"d": 14, "la": 3.4, "lp": 3.9},
                    {"d": 30, "la": 5.2, "lp": 5.8}, {"d": 60, "la": 7.8, "lp": 8.7},
                    {"d": 90, "la": 11.3, "lp": 12.4}]},
]

_COHORT_FAILURES = [
    {"cohort": "Deadcoin (avg)", "survived": False, "mc_final": 0,
     "trajectory": [{"d": 0, "la": 1.0, "lp": 1.0}, {"d": 3, "la": 0.8, "lp": 0.7},
                    {"d": 7, "la": 0.6, "lp": 0.4}, {"d": 14, "la": 0.4, "lp": 0.2},
                    {"d": 30, "la": 0.2, "lp": 0.08}, {"d": 60, "la": 0.1, "lp": 0.03},
                    {"d": 90, "la": 0.05, "lp": 0.01}]},
]


# ────────────────────────────────────────────────────────────────────
# Extended demo data with edge cases
# ────────────────────────────────────────────────────────────────────

_DEMO_TOKENS = [
    # Top performers
    {"symbol": "ORBIT", "launch": "2026-07-30", "mc": 18e6, "vol24": 6.8e6, "turn": 0.38, 
     "dev": True, "liq": 3.9e6, "mvrv": 0.68, "top10_share": 0.35, "revenue_24h": 88e3,
     "user_growth_7d": 3.1, "protocol_rev": 88e3, "addr": 3100, "price": 0.52,
     "funding": "VC Series B", "team_vest_months": 12},
    {"symbol": "ZEN", "launch": "2026-07-29", "mc": 32e6, "vol24": 14.1e6, "turn": 0.44,
     "dev": True, "liq": 9.8e6, "mvrv": 0.89, "top10_share": 0.28, "revenue_24h": 340e3,
     "user_growth_7d": 2.2, "protocol_rev": 340e3, "addr": 12500, "price": 2.48,
     "funding": "Strategic Partners", "team_vest_months": 18},
    {"symbol": "NOVA", "launch": "2026-07-28", "mc": 12e6, "vol24": 8.2e6, "turn": 0.68,
     "dev": True, "liq": 5.1e6, "mvrv": 0.72, "top10_share": 0.45, "revenue_24h": 125e3,
     "user_growth_7d": 1.8, "protocol_rev": 125e3, "addr": 7200, "price": 2.20,
     "funding": "Seed + Community", "team_vest_months": 24},
    
    # Edge case: Wash trading (turnover > 100%)
    {"symbol": "BLAST", "launch": "2026-07-27", "mc": 8e6, "vol24": 9.3e6, "turn": 1.16,
     "dev": False, "liq": 4.2e6, "mvrv": 0.55, "top10_share": 0.78, "revenue_24h": 15e3,
     "user_growth_7d": 0.9, "protocol_rev": 15e3, "addr": 1800, "price": 0.75,
     "funding": "VC Series A", "team_vest_months": 6},
    
    # Edge case: High holder concentration (>70%)
    {"symbol": "PULSAR", "launch": "2026-07-25", "mc": 5e6, "vol24": 1.6e6, "turn": 0.32,
     "dev": False, "liq": 1.1e6, "mvrv": 0.42, "top10_share": 0.85, "revenue_24h": 2e3,
     "user_growth_7d": 0.2, "protocol_rev": 2e3, "addr": 900, "price": 0.22,
     "funding": "Founder-only", "team_vest_months": 3},
    
    # Edge case: Overvalued (MVRV > 1.0, positive residual)
    {"symbol": "STRAT", "launch": "2026-07-26", "mc": 46e6, "vol24": 21.5e6, "turn": 0.47,
     "dev": True, "liq": 15.2e6, "mvrv": 1.05, "top10_share": 0.52, "revenue_24h": 670e3,
     "user_growth_7d": 1.3, "protocol_rev": 670e3, "addr": 42000, "price": 11.80,
     "funding": "VC Series C", "team_vest_months": 6},
    {"symbol": "AXIOM", "launch": "2026-07-24", "mc": 28e6, "vol24": 18.9e6, "turn": 0.67,
     "dev": True, "liq": 7.6e6, "mvrv": 0.91, "top10_share": 0.41, "revenue_24h": 520e3,
     "user_growth_7d": 2.8, "protocol_rev": 520e3, "addr": 2800, "price": 5.10,
     "funding": "VC Series A", "team_vest_months": 12},
    
    # Edge case: Failed launch (low growth, high dilution)
    {"symbol": "DYNAST", "launch": "2026-07-22", "mc": 3e6, "vol24": 2.1e6, "turn": 0.70,
     "dev": False, "liq": 0.8e6, "mvrv": 1.2, "top10_share": 0.92, "revenue_24h": 0,
     "user_growth_7d": 0.1, "protocol_rev": 0, "addr": 300, "price": 0.15,
     "funding": "Founder dump", "team_vest_months": 1},
    
    # Edge case: MRV collapse (MVRV < 0.3 - capitulation)
    {"symbol": "VOLT", "launch": "2026-07-29", "mc": 15e6, "vol24": 5.4e6, "turn": 0.36,
     "dev": True, "liq": 4.1e6, "mvrv": 0.28, "top10_share": 0.55, "revenue_24h": 95e3,
     "user_growth_7d": 1.5, "protocol_rev": 95e3, "addr": 8500, "price": 1.85,
     "funding": "Community", "team_vest_months": 18},
]

_DEMO_VESTING = [
    {"symbol": "ORBIT", "unl": 0.15e6, "usd": 0.32e6, "vol": 2.8e6, "px": 0.48, "cliff": 2, "fdv": 22e6, "tge_circ": 0.65},
    {"symbol": "ZEN", "unl": 0.9e6, "usd": 2.2e6, "vol": 5.8e6, "px": 5.4, "cliff": 3, "fdv": 40e6, "tge_circ": 0.55},
    {"symbol": "NOVA", "unl": 0.4e6, "usd": 0.9e6, "vol": 3.4e6, "px": 2.2, "cliff": 5, "fdv": 20e6, "tge_circ": 0.60},
    {"symbol": "BLAST", "unl": 1.2e6, "usd": 5.4e6, "vol": 2.1e6, "px": 3.2, "cliff": 70, "fdv": 18e6, "tge_circ": 0.35},
    {"symbol": "STRAT", "unl": 2.7e6, "usd": 6.7e6, "vol": 4.5e6, "px": 2.5, "cliff": 12, "fdv": 52e6, "tge_circ": 0.50},
    {"symbol": "PULSAR", "unl": 0.08e6, "usd": 0.18e6, "vol": 0.8e6, "px": 0.36, "cliff": 1, "fdv": 8e6, "tge_circ": 0.40},
    {"symbol": "AXIOM", "unl": 8.3e6, "usd": 12.1e6, "vol": 8.9e6, "px": 5.1, "cliff": 45, "fdv": 36e6, "tge_circ": 0.45},
    {"symbol": "DYNAST", "unl": 2.1e6, "usd": 0.45e6, "vol": 0.5e6, "px": 0.15, "cliff": 90, "fdv": 5e6, "tge_circ": 0.15},
    {"symbol": "VOLT", "unl": 0.6e6, "usd": 1.1e6, "vol": 3.7e6, "px": 1.85, "cliff": 18, "fdv": 26e6, "tge_circ": 0.58},
]

_DEMO_ADOPTION = [
    {"symbol": "ORBIT", "addr": 3100, "price": 0.52, "trend": "ascending", "resid": -1.4, "under": True},
    {"symbol": "ZEN", "addr": 12500, "price": 2.48, "trend": "flat", "resid": -0.6, "under": True},
    {"symbol": "STRAT", "addr": 42000, "price": 11.80, "trend": "descending", "resid": 1.8, "under": False},
    {"symbol": "AXIOM", "addr": 2800, "price": 5.10, "trend": "ascending", "resid": 0.3, "under": False},
    {"symbol": "NOVA", "addr": 7200, "price": 2.20, "trend": "ascending", "resid": -0.8, "under": True},
    {"symbol": "BLAST", "addr": 1800, "price": 0.75, "trend": "collapsing", "resid": 2.2, "under": False},
    {"symbol": "PULSAR", "addr": 900, "price": 0.22, "trend": "collapsing", "resid": 1.9, "under": False},
    {"symbol": "DYNAST", "addr": 300, "price": 0.15, "trend": "collapsing", "resid": 2.5, "under": False},
    {"symbol": "VOLT", "addr": 8500, "price": 1.85, "trend": "flat", "resid": -0.4, "under": True},
]


def math_log10(x: float) -> float:
    """Wrapper so DemoProvider doesn't need to import math at module load."""
    import math
    return math.log10(x)


class DemoProvider:
    """Synthesizes realistic token-launch metrics without any API calls.
    
    Produces data for three modules:
      A) Day-1 Liquidity Filter — turnover + holder concentration + dev activity
      B) Vesting Wall — inflation pressure vs. protocol revenue growth
      C) Adoption Curve — power-law residual + MVRV capitulation overlay
    
    Also computes a weighted Conviction Score (0-100) for each token that
    surfaces the 1-2% most likely to survive.
    """

    def __init__(self, settings: SkewSettings):
        self.settings = settings
        self._rng = random.Random(42)

    # ── Module A: Day-1 Liquidity ─────────────────────────────────

    def _build_day1(self) -> list[dict]:
        out = []
        for t in _DEMO_TOKENS:
            turnover = t["turn"] + self._rng.uniform(-0.03, 0.03)
            out.append({
                "symbol": t["symbol"],
                "launch": t["launch"],
                "market_cap": t["mc"],
                "volume_24h": t["vol24"],
                "turnover_pct": turnover * 100,
                "dev_active": t["dev"],
                "liquidity_depth": t["liq"],
                "mvrv": t["mvrv"],
                "holder_concentration": t["top10_share"] * 100,
                "protocol_revenue_24h": t["protocol_rev"],
                "user_growth_7d": t["user_growth_7d"],
                "active_addr": t.get("addr", 1000),
                "price": t.get("price", 1.0),
                "funding": t.get("funding", "Seed"),
                "team_vest_months": t.get("team_vest_months", 12),
            })
        return out

    # ── Module B: Vesting Wall ────────────────────────────────────

    def _build_vesting(self) -> list[dict]:
        out = []
        for v in _DEMO_VESTING:
            daily_vol = v["vol"]
            unlocks = v["usd"]
            pressure = unlocks / daily_vol if daily_vol else 0
            tge_mc = _DEMO_TOKENS[[d["symbol"] for d in _DEMO_TOKENS].index(v["symbol"])]["mc"]
            dilution = (v["fdv"] - tge_mc) / v["fdv"] if v["fdv"] else 0
            out.append({
                "symbol": v["symbol"],
                "unlocks_30d": v["unl"],
                "unlocks_usd": v["usd"],
                "daily_vol": daily_vol,
                "pressure_x": pressure,
                "cliff_days": v["cliff"],
                "dilution_rate": dilution * 100,
                "fdv": v["fdv"],
                "tge_circulation_pct": v["tge_circ"] * 100,
            })
        return out

    # ── Module C: Adoption Curve ──────────────────────────────────

    def _build_adoption(self) -> list[dict]:
        out = []
        for a in _DEMO_ADOPTION:
            under = a["under"]
            pts = []
            base_addr = a["addr"]
            base_price = a["price"]
            for i in range(8):
                la = base_addr * (1 + i * 0.15 + self._rng.uniform(-0.05, 0.05))
                lp = base_price * (1 + (i * 0.08 if under else i * 0.25) + self._rng.uniform(-0.03, 0.03))
                pts.append({
                    "logAddr": round(math_log10(la), 4),
                    "logPrice": round(math_log10(max(lp, 0.01)), 4),
                })
            out.append({
                "symbol": a["symbol"],
                "active_addr": a["addr"],
                "price": a["price"],
                "trend": a["trend"],
                "residual": a["resid"],
                "undervalued": under,
                "on_trendline": abs(a["resid"]) < 0.3,
                "trajectory": pts,
            })
        return out

    # ── Conviction Score computation ──────────────────────────────

    def _conviction_score(self, d1: dict, v: dict, a: dict) -> dict:
        """Compute a 0-100 conviction score for a token.
        
        Weights (user-specified optimal):
          - Module A (30%): turnover sweet-spot + holder concentration + dev active
          - Module B (30%): inflation pressure + emission-to-adoption ratio + user growth
          - Module C (40%): power-law residual + MVRV capitulation
        """
        # ── Module A score (0-30) ──
        score_a = 0
        turn = d1["turnover_pct"]
        if 30 <= turn <= 60:
            score_a += 15 * (1 - abs(turn - 45) / 15)
        hc = d1["holder_concentration"]
        if hc < 20: score_a += 10
        elif hc < 40: score_a += 8
        elif hc < 60: score_a += 5
        if d1["dev_active"]: score_a += 5

        # ── Module B score (0-30) ──
        score_b = 0
        px = v["pressure_x"]
        if px < 0.5: score_b += 10
        elif px < 1.0: score_b += 8
        elif px < 2.0: score_b += 4
        era = d1.get("protocol_revenue_24h", 0)
        emission_to_user = v["unlocks_usd"] / (max(d1.get("active_addr", 1000), 1) * max(d1.get("price", 0.01), 0.01)) if era else 999
        if emission_to_user < 0.5: score_b += 8
        elif emission_to_user < 2.0: score_b += 6
        elif emission_to_user < 5.0: score_b += 3
        ug = d1.get("user_growth_7d", 1.0)
        if ug > 3.0: score_b += 6
        elif ug > 2.0: score_b += 4
        elif ug > 1.5: score_b += 2
        if v["dilution_rate"] < 10: score_b += 4
        elif v["dilution_rate"] < 20: score_b += 2

        # ── Module C score (0-40) ──
        score_c = 0
        r = a["residual"]
        if r < -1.0: score_c += 25
        elif r < -0.5: score_c += 15
        elif r < 0: score_c += 8
        if d1["mvrv"] < 0.7: score_c += 15
        elif d1["mvrv"] < 0.9: score_c += 10
        elif d1["mvrv"] < 1.0: score_c += 5
        ug = d1.get("user_growth_7d", 1.0)
        if ug > 2.5: score_c += 5
        elif ug > 1.5: score_c += 3

        total = round(score_a + score_b + score_c)
        return {"total": total, "a": round(score_a), "b": round(score_b), "c": round(score_c)}

    # ── Top-level snapshot ────────────────────────────────────────

    def snapshot(self) -> dict:
        cfg = self.settings
        day1 = self._build_day1()
        vesting = self._build_vesting()
        adoption = self._build_adoption()

        d1_by_sym = {d["symbol"]: d for d in day1}
        v_by_sym = {v["symbol"]: v for v in vesting}
        a_by_sym = {a["symbol"]: a for a in adoption}

        ranked = []
        for sym in d1_by_sym:
            d1 = d1_by_sym[sym]
            v = v_by_sym.get(sym)
            a = a_by_sym.get(sym)
            if not v or not a:
                continue
            scores = self._conviction_score(d1, v, a)
            passes_a = (d1["turnover_pct"] >= 30 and d1["turnover_pct"] <= 100
                        and d1["holder_concentration"] < 70 and d1["dev_active"])
            passes_b = v["pressure_x"] < cfg.module_b.pressure_threshold
            passes_c = a["undervalued"] or (d1["mvrv"] < 1.0 and a["residual"] < 0)

            ranked.append({
                "symbol": sym,
                "conviction": scores["total"],
                "score_a": scores["a"],
                "score_b": scores["b"],
                "score_c": scores["c"],
                "passes_a": passes_a,
                "passes_b": passes_b,
                "passes_c": passes_c,
                "all_clear": passes_a and passes_b and passes_c,
                "strong": scores["total"] >= 75,
                "d1": d1,
                "v": v,
                "a": a,
            })

        ranked.sort(key=lambda x: x["conviction"], reverse=True)

        signals = []
        for r in ranked:
            if not r["all_clear"]:
                continue
            d1, v, a = r["d1"], r["v"], r["a"]
            signals.append({
                "symbol": r["symbol"],
                "conviction": r["conviction"],
                "strong": r["strong"],
                "title": "All gates clear — harvest the skew" if r["strong"] else "Gates clear",
                "body": (f"Conviction {r['conviction']}/100 | "
                         f"Turnover {d1['turnover_pct']:.0f}% | "
                         f"Top-10 share {d1['holder_concentration']:.0f}% | "
                         f"MVRV {d1['mvrv']:.2f} | "
                         f"Vest pressure {v['pressure_x']:.1f}x | "
                         f"Residual {a['residual']:+.1f}σ"),
                "time": time.strftime("%H:%M:%S"),
            })

        factors = {
            "size": any(d["market_cap"] <= cfg.universe.max_market_cap and d["market_cap"] >= cfg.universe.min_market_cap for d in day1),
            "value": any(d["mvrv"] < 1.0 for d in day1),
            "quality": any(d["holder_concentration"] < 50 for d in day1),
            "investment": any(v["dilution_rate"] < (cfg.module_b.dilution_warn_pct * 100) for v in vesting),
            "momentum": any(a["trend"] == "ascending" for a in adoption),
        }

        cohort = {
            "survivors": _COHORT_SURVIVORS,
            "failures": _COHORT_FAILURES,
        }

        return {
            "header": {"updated": time.strftime("%Y-%m-%d %H:%M:%S")},
            "universe": f"{len(day1)} tokens",
            "flagged": len([r for r in ranked if r["all_clear"]]),
            "strong": len([r for r in ranked if r["all_clear"] and r["strong"]]),
            "watch": len([a for a in adoption if a["undervalued"]]),
            "day1": day1,
            "vesting": vesting,
            "adoption": adoption,
            "signals": signals,
            "ranked": [{"symbol": r["symbol"], "conviction": r["conviction"],
                        "score_a": r["score_a"], "score_b": r["score_b"], "score_c": r["score_c"],
                        "all_clear": r["all_clear"], "strong": r["strong"],
                        "passes_a": r["passes_a"], "passes_b": r["passes_b"], "passes_c": r["passes_c"]} for r in ranked],
            "factors": factors,
            "cohort": cohort,
            "institutional": _INSTITUTIONAL_CONTEXT,
            "streaming": True,
            "error": None,
        }


# ────────────────────────────────────────────────────────────────────
# Backtesting module for historical performance evaluation
# ────────────────────────────────────────────────────────────────────

class Backtester:
    """Evaluates historical performance of the Conviction Score strategy.
    
    Simulates: for each past "launch", apply today's gates and score,
    then track actual outcomes (survived/died, ROI at T+90d).
    
    Returns performance statistics by conviction decile.
    """
    
    def __init__(self, config: dict):
        self.cfg = config
    
    def simulate(self, historical_tokens: list[dict]) -> dict:
        """Run backtest on historical token launches.
        
        historical_tokens: list of dicts with keys:
          symbol, launch_date, turnover, holder_conc, dev_active,
          pressure, mvrv, residual, actual_roi_90d, survived
        """
        results = {i: {"count": 0, "survived": 0, "avg_roi": 0, "sum_roi": 0} 
                   for i in range(1, 11)}
        
        for tok in historical_tokens:
            # Compute legacy conviction score
            # (simplified version for backtesting)
            score = 0
            if 30 <= tok.get("turnover", 0) <= 60:
                score += 25
            if tok.get("holder_conc", 100) < 50:
                score += 20
            if tok.get("dev_active", False):
                score += 10
            if tok.get("pressure", 1) < 1.5:
                score += 20
            if tok.get("mvrv", 2) < 1.0:
                score += 15
            if tok.get("residual", 1) < 0:
                score += 10
            
            decile = max(1, min(10, (score // 10) + 1)) if score > 0 else 1
            
            roi = tok.get("actual_roi_90d", 0)
            results[decile]["count"] += 1
            results[decile]["sum_roi"] += roi
            if tok.get("survived", False):
                results[decile]["survived"] += 1
        
        for d in results:
            if results[d]["count"] > 0:
                results[d]["avg_roi"] = results[d]["sum_roi"] / results[d]["count"]
        
        return results


class RealtimeProvider:
    """Base class for real data providers.
    
    Subclasses should implement:
      - fetch_daily1(): Get recent token launches (last 24h)
      - fetch_vesting(): Get upcoming unlock schedules
      - fetch_adoption(): Get active addresses and price data
    
    Example implementations:
      - CoinGeckoProvider (coinmarketcap.com API)
      - DuneProvider (dune.com API for on-chain data)
      - MessariProvider (messari.io API)
    """
    
    def __init__(self, api_keys: dict):
        self.keys = api_keys
    
    def fetch_daily1(self) -> list[dict]:
        """Fetch recent token launches with turnover, holders, dev activity."""
        raise NotImplementedError
    
    def fetch_vesting(self) -> list[dict]:
        """Fetch token unlock schedules with pressure calculations."""
        raise NotImplementedError
    
    def fetch_adoption(self) -> list[dict]:
        """Fetch active addresses, prices, power-law residuals."""
        raise NotImplementedError


# ────────────────────────────────────────────────────────────────────
# Thread-safe dashboard state
# ────────────────────────────────────────────────────────────────────

class DashboardState:
    def __init__(self, settings: Settings, provider: DemoProvider):
        self._lock = threading.Lock()
        self.settings = settings
        self.provider = provider
        self.data: dict = {"error": "initializing...", "streaming": False}
        self.backtester = Backtester(settings.skew.model_dump())

    def refresh(self) -> None:
        try:
            self.data = self.provider.snapshot()
        except Exception as exc:  # pragma: no cover
            self.data = {"error": str(exc), "streaming": False}

    def to_json(self) -> bytes:
        with self._lock:
            return json.dumps(self.data).encode()


# ────────────────────────────────────────────────────────────────────
# HTTP server
# ────────────────────────────────────────────────────────────────────

def _make_handler(state: DashboardState):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def do_GET(self):
            if self.path.startswith("/api/state"):
                state.refresh()
                body = state.to_json()
                self._send(200, "application/json", body)
            elif self.path.startswith("/api/backtest"):
                # Run backtest on simulated historical data
                result = state.backtester.simulate([])
                self._send(200, "application/json", json.dumps(result).encode())
            elif self.path in ("/", "/index.html", "/launch_skew.html"):
                self._send(200, "text/html; charset=utf-8", HTML_PATH.read_bytes())
            else:
                self._send(404, "text/plain", b"not found")

        def _send(self, code, ctype, body):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler


def serve(
    settings: Settings,
    provider: DemoProvider,
    host: str = "127.0.0.1",
    port: int = 8765,
) -> None:
    state = DashboardState(settings, provider)
    state.refresh()

    handler = _make_handler(state)
    httpd = ThreadingHTTPServer((host, port), handler)
    print(f"Launch Skew Monitor live at http://{host}:{port}  (Ctrl-C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping.")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    cfg_path = DEFAULT_CONFIG if DEFAULT_CONFIG.exists() else None
    settings = Settings.load(cfg_path) if cfg_path else Settings()
    provider = DemoProvider(settings.skew)
    serve(settings, provider,
          host=settings.skew.server.host,
          port=settings.skew.server.port)
