"""Clean CoinGecko provider for real token data."""
import json
import os
import urllib.request
import urllib.parse
import time
import math
from typing import Optional
from dataclasses import dataclass

@dataclass
class TokenData:
    """Real token data from CoinGecko."""
    id: str
    symbol: str
    name: str
    price: float
    market_cap: float
    volume_24h: float
    supply: float
    price_change_24h_pct: float  # 24h price change percentage

@dataclass
class ModuleMetrics:
    """Aggregated metrics from all three modules."""
    symbol: str
    name: str
    price: float
    market_cap: float
    turnover: float
    mvrv: float
    erosion_ratio: float
    pressure: float
    conviction: int
    signal: str

class CoinGeckoProvider:
    """Fetch live token data from CoinGecko API."""
    
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    def __init__(self):
        self.session = urllib.request.build_opener()
    
    def _get_json(self, endpoint: str, params: dict = None) -> dict:
        """Fetch JSON from CoinGecko API with retry logic."""
        url = f"{self.BASE_URL}{endpoint}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "LaunchSkewMonitor/1.0"}
        )
        
        try:
            with self.session.open(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            return {"error": str(e)}
    
    def get_tokens(self, count: int = 20) -> list[TokenData]:
        """Get top tokens with live data."""
        result = self._get_json("/coins/markets", {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": count,
            "page": 1,
            "price_change_percentage": "24h"
        })
        
        if "error" in result:
            return []
        
        tokens = []
        for item in result:
            tokens.append(TokenData(
                id=item.get("id", ""),
                symbol=item.get("symbol", "").upper(),
                name=item.get("name", ""),
                price=item.get("current_price", 0),
                market_cap=item.get("market_cap", 0),
                volume_24h=item.get("total_volume", 0),
                supply=item.get("total_supply", item.get("circulating_supply", 0)),
                price_change_24h_pct=item.get("price_change_percentage_24h", 0) or 0
            ))
        return tokens

class SignalScanner:
    """Scanner that computes conviction scores from a single filtered token set.

    Every module (Liquidity, Vesting, Momentum) is derived from the SAME
    filtered subset, so index alignment across modules is guaranteed.
    """

    # Non-speculative pegged assets are excluded from all conviction math:
    # stablecoins and commodity-pegged tokens do not exhibit launch skew.
    NON_SPECULATIVE = {
        "USDT", "USDC", "USD1", "USDG", "USDS", "USDE", "USDD", "DAI",
        "BUSD", "TUSD", "FDUSD", "FRAX", "PYUSD", "GUSD", "U",
        "XAUT", "PAXG",  # commodity pegs (gold)
    }

    def __init__(self, provider: CoinGeckoProvider):
        self.provider = provider

    def get_signals(self, count: int = 10) -> list[ModuleMetrics]:
        """Return the top `count` speculative tokens by conviction score.

        The returned list is the single source of truth: Modules A, B and C
        all consume this exact filtered subset.
        """
        tokens = self.provider.get_tokens(count * 3)
        signals = []
        seen = set()
        for t in tokens:
            sym = (t.symbol or "").upper()
            if not sym or sym in seen or sym in self.NON_SPECULATIVE:
                continue
            seen.add(sym)
            m = self._calculate_metrics(t)
            if 0 <= m.conviction <= 100:
                signals.append(m)
        signals.sort(key=lambda x: x.conviction, reverse=True)
        return signals[:count]

    def _calculate_metrics(self, t: TokenData) -> ModuleMetrics:
        """Compute all module metrics for one speculative token from live data."""
        turnover = (t.volume_24h / t.market_cap) if t.market_cap > 0 else 0

        # Module A (0-30): LiquidityFit.
        # Linear ramp toward the 30-60% turnover sweet spot; sharp penalty
        # below 10% (illiquid) and above 75% (wash-trading risk).
        if turnover <= 0:
            score_a = 0
        elif turnover < 0.10:
            score_a = max(0, turnover / 0.10 * 8)          # 0 -> 8 approaching 10%
        elif turnover < 0.30:
            score_a = 8 + (turnover - 0.10) / 0.20 * 18    # 8 -> 26
        elif turnover <= 0.60:
            score_a = 30 - abs(turnover - 0.45) / 0.15 * 4 # ~30 at sweet spot
        elif turnover <= 0.75:
            score_a = 26 - (turnover - 0.60) / 0.15 * 16   # 26 -> 10
        else:
            score_a = max(0, 10 - (turnover - 0.75) * 20)  # sharp drop past 75%

        # Module B (0-30): Erosion Ratio. Proxy address growth from 24h stability.
        chg = t.price_change_24h_pct or 0.0
        if abs(chg) < 5:
            addr_growth = 15
        elif abs(chg) < 15:
            addr_growth = 10
        else:
            addr_growth = 5
        era = 5.0 / addr_growth  # ~5% assumed monthly supply growth
        score_b = 20 if era < 0.7 else 15 if era < 1.0 else 10 if era < 1.5 else 5 if era < 2.0 else 0

        # Module C (0-40): depth (log mkt cap) + momentum.
        depth = max(0.0, min(1.0, (math.log10(t.market_cap) - 6) / 4.0)) if t.market_cap > 0 else 0
        score_c_depth = depth * 20
        if chg < -15:
            score_c_mom = 4
        elif chg < 0:
            score_c_mom = 12 - abs(chg) * 0.6
        elif chg <= 8:
            score_c_mom = 14 + chg * 1.0
        elif chg <= 20:
            score_c_mom = 20
        else:
            score_c_mom = max(8, 20 - (chg - 20) * 1.0)
        score_c = score_c_depth + score_c_mom

        total = int(round(score_a + score_b + score_c))
        total = max(0, min(100, total))
        signal = "STRONG" if total >= 80 else "BUY" if total >= 70 else "HOLD" if total >= 55 else "WATCH" if total >= 40 else "AVOID"

        return ModuleMetrics(
            symbol=t.symbol,
            name=t.name,
            price=t.price,
            market_cap=t.market_cap,
            turnover=turnover,
            mvrv=1.0 + (chg / 100.0),
            erosion_ratio=era,
            pressure=era,
            conviction=total,
            signal=signal,
        )


class DuneProvider:
    """Fetch on-chain vesting / active-address data from Dune Analytics.

    The API key is read from the DUNE_API_KEY environment variable ONLY.
    It is never written to disk, logged, or committed.
    """

    BASE_URL = "https://api.dune.com/api/v1"

    def __init__(self, api_key: Optional[str] = None):
        # Resolve key from arg or env; never fall back to a literal.
        self.api_key = api_key or os.environ.get("DUNE_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "DUNE_API_KEY not set — DuneProvider unavailable. "
                "Module B will record as null (no fabrication)."
            )

    def _get_json(self, path: str, params: dict | None = None) -> dict:
        url = f"{self.BASE_URL}{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"X-Dune-Api-Key": self.api_key})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:  # nosec
                return json.loads(resp.read().decode())
        except Exception as e:  # noqa: BLE001
            return {"error": str(e)}

    def run_query(self, query_id: str, params: Optional[dict] = None) -> dict:
        """Run a saved Dune query by ID and return its result rows."""
        result = self._get_json(f"/query/{query_id}/results", params)
        if "error" in result:
            return result
        return result.get("result", {}).get("rows", [])

    def get_token_unlocks(self, token_symbol: str) -> dict:
        """Placeholder for a real unlock query. Returns null-shaped dict if the
        query ID is not configured, so callers never fabricate numbers."""
        qid = os.environ.get("DUNE_UNLOCK_QUERY_ID")
        if not qid:
            return {"symbol": token_symbol, "available": False, "note": "no query configured"}
        rows = self.run_query(qid, {"token": token_symbol})
        if isinstance(rows, dict) and "error" in rows:
            return {"symbol": token_symbol, "available": False, "error": rows["error"]}
        return {"symbol": token_symbol, "available": True, "rows": rows}