"""Tax Lab state — the interactive after-tax / TLH / asset-location exhibit.

Reads the live forward ledger, decomposes its gains rate-independently (drift.tax.
gain_profile), and embeds the pieces a client-side page needs to recompute after-tax
return, tax-loss-harvesting value, and the asset-location benefit for ANY federal
bracket and state. Personalized but self-contained — the math runs in the browser, so
the page is shareable with no server (the apres.tax pattern, made portfolio-specific).
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from .tax import STATE_RATES, gain_profile

# A few representative federal points (ordinary rate / LT cap-gains rate / NIIT).
FED_BRACKETS = [
    {"label": "22% ordinary · 15% LT", "ord": 0.22, "lt": 0.15, "niit": 0.0},
    {"label": "24% ordinary · 15% LT", "ord": 0.24, "lt": 0.15, "niit": 0.0},
    {"label": "32% ordinary · 15% LT · NIIT", "ord": 0.32, "lt": 0.15, "niit": 0.038},
    {"label": "35% ordinary · 20% LT · NIIT", "ord": 0.35, "lt": 0.20, "niit": 0.038},
    {"label": "37% ordinary · 20% LT · NIIT (top)", "ord": 0.37, "lt": 0.20, "niit": 0.038},
]

# Illustrative assumptions for the asset-location simulator (Layer 1), embedded in the page
# so the client-side math is tunable rather than hardcoded. The passive sleeve that occupies
# the taxable account is a low-turnover, qualified-dividend index core: its only material
# annual drag is tax on qualified dividends at the long-term rate (near-zero realized gains).
ASSUMPTIONS = {
    "passive_div_yield": 0.018,        # qualified-dividend yield of the taxable passive core
    "horizon_years": 30,               # projection horizon for the terminal-wealth boost
    "default_taxable": 1_500_000,      # starting slider value — taxable brokerage balance
    "default_advantaged": 1_000_000,   # starting slider value — tax-advantaged (IRA/Roth) balance
    "wealth_max": 10_000_000,          # slider ceiling
    "wealth_step": 50_000,
}


def location_alpha(taxable: float, advantaged: float,
                   mom_drag_rate: float, passive_drag_rate: float) -> dict:
    """Annual asset-location alpha in dollars: the household tax saved by stacking the
    high-turnover momentum sleeve into the tax-advantaged account (sized to its capacity)
    and leaving a low-turnover, qualified-dividend passive core in the taxable account,
    versus spreading the sleeve proportionally across both accounts.

        alpha$ = (A·T / (A+T)) · (mom_drag_rate − passive_drag_rate)

    The (A·T/(A+T)) term is the momentum dollars that land in taxable under the naive
    (proportional) split — maximized at an equal balance, zero when either account is empty.
    The rate spread is the drag that misplacement incurs. This mirrors the JS on the Tax Lab
    page; it lives here so the headline math has automated test coverage.
    """
    w = taxable + advantaged
    if w <= 0:
        return {"annual_dollars": 0.0, "annual_rate": 0.0, "overlap": 0.0,
                "mom_drag_rate": mom_drag_rate, "passive_drag_rate": passive_drag_rate}
    overlap = advantaged * taxable / w
    annual = overlap * max(0.0, mom_drag_rate - passive_drag_rate)
    return {"annual_dollars": annual, "annual_rate": annual / w, "overlap": overlap,
            "mom_drag_rate": mom_drag_rate, "passive_drag_rate": passive_drag_rate}


def build_taxlab(docs_dir: str | Path = "docs") -> dict:
    docs = Path(docs_dir)
    state: dict = {
        "header": {"generated": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())},
        "profile": None, "states": STATE_RATES, "brackets": FED_BRACKETS,
        "assumptions": ASSUMPTIONS,
    }
    led_path = docs / "ledger.json"
    if not led_path.exists():
        return state
    try:
        led = json.loads(led_path.read_text())
    except Exception:
        return state
    entries = led.get("entries", [])
    gp = gain_profile(entries, lt_holding_bars=252, bars_per_year=252.0)
    if gp is None:
        return state
    years = max(1e-9, len(entries) / 252.0)
    state["header"].update({
        "inception": led.get("inception", entries[0]["date"] if entries else ""),
        "updated": led.get("updated", ""),
        "sessions": len(entries),
        "years": round(years, 2),
        "pretax_return": gp.pretax_return,
        "annual_turnover": gp.annual_turnover,
        "short_term_share": gp.short_term_share,
        "avg_holding_days": gp.avg_holding_days,
    })
    state["profile"] = {
        "pretax_return": gp.pretax_return,
        "st_realized": gp.st_realized, "lt_realized": gp.lt_realized,
        "harvested_st": gp.harvested_st, "harvested_lt": gp.harvested_lt,
        "embedded_st": gp.embedded_st, "embedded_lt": gp.embedded_lt,
        "years": round(years, 2),
    }
    return state
