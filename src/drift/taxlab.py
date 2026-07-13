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

from .firm_models import models_state
from .tax import STATE_RATES, gain_profile
from .state_facts import ESTATE as _ESTATE_FACTS, IL_AG_CURVE

# Death-tax environment by state, projected from the canonical estate table (drift.state_facts). IL is
# excluded — it is the precise engine (il_estate_tax), not a neutral card — and NYC is overlaid (a NYC
# resident faces NY's estate tax). One source, no separate estate membership.
_STATE_ESTATE = {code: e["regime"] for code, e in _ESTATE_FACTS.items() if code != "IL"}
_STATE_ESTATE["NYC"] = "estate"

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
    "default_advantaged": 1_000_000,   # (legacy two-bucket default; superseded by the three below)
    "default_traditional": 600_000,    # starting slider value — Traditional IRA / pre-tax 401(k)
    "default_roth": 400_000,           # starting slider value — Roth IRA / tax-free
    "wealth_max": 10_000_000,          # slider ceiling
    "wealth_step": 50_000,
    "growth_rate": 0.07,               # illustrative reinvestment rate for the terminal location alpha
    # Alpha-Turnover Frontier (Layer 3): the breakeven slope is gain_per_turn · r_st, where
    # gain_per_turn is the NAV fraction realized as short-term gain per 1.0 of annual turnover.
    # Calibrated from the live book in build_taxlab when a ledger exists; this is the fallback.
    "gain_per_turn": 0.03,
    "frontier_alpha": 0.05,            # default client strategy-alpha slider (5%)
    "frontier_turnover": 3.0,          # default client annual-turnover slider (300%)
    "alpha_max": 0.15,                 # alpha slider ceiling (15%)
    "turnover_max": 5.0,               # turnover slider ceiling (500%)
    # All-in annual cost layer (Tier 1: after-tax is reported BEFORE fees). Advisory fee +
    # blended fund expense ratio, in basis points; tunable in the page.
    "advisory_fee_bps": 100,
    "expense_ratio_bps": 30,
    "fee_max_bps": 300,
    # Portfolio-transition (Feature 4): the prospect's assumed legacy all-in cost, the lever the
    # before/after compares the low-cost institutional model against. Editable on the page.
    "legacy_fee_bps": 130,
    "legacy_fee_max_bps": 250,
    # Estate Planning View (2026 tax-law reference). Federal exemption is large and most
    # Illinois HNW estates fall under it; Illinois' $4M exclusion is the binding constraint.
    "estate": {
        "fed_exemption_indiv": 15_000_000,   # 2026 permanent federal exemption (individual)
        "fed_exemption_couple": 30_000_000,  # couple (portable)
        "fed_rate": 0.40,                    # federal top rate
        "il_exclusion": _ESTATE_FACTS["IL"]["exemption_usd"],   # canonical IL exclusion (no portability)
        "il_hb2601_exclusion": 8_000_000,    # HB 2601 (to $8M) — stalled in Rules, not enacted; a what-if toggle
        "il_top_rate": _ESTATE_FACTS["IL"]["top_rate"],         # canonical IL top marginal rate
        "default_individual": 3_000_000,
        "default_joint": 0,                  # individual-first; joint>0 unlocks the $30M portable exemption
        "default_trust": 1_000_000,
        # "True Net Worth" illiquid assets — these, not the liquid book, often trigger the state cliff.
        "default_real_estate": 1_500_000,    # primary residence + real estate
        "default_business": 0,               # closely-held business equity (full value; discounts apply)
        "default_life_insurance": 0,         # death benefit; in-estate only if owned by the insured (§2042)
        "estate_max": 30_000_000,
        "estate_step": 100_000,
        "trust_compression_top_threshold": 15_650,  # 2026 trust income hits the 37% bracket here
        # Death-tax environment by state: IL is modeled precisely (il_estate_tax); the other states get
        # a neutral card naming their regime and deferring the exact figure to the attorney. Projected
        # from the canonical estate table (one source), plus the NYC overlay.
        "state_estate": _STATE_ESTATE,
        # The Illinois AG estate-tax curve, injected so the workspace JS renders it instead of a
        # hand-typed mirror (one source for Python and the browser).
        "il_ag_curve": [list(r) for r in IL_AG_CURVE],
    },
    # Optimal Strategy & Rollover Engine (?view=strategy).
    "strategy": {
        "default_401k": 500_000,
        "k401_fee_bps": 50,          # legacy plan / target-date embedded fee (default)
        "k401_fee_max_bps": 150,
        "rollover_years": 10,
        "default_trad_ira": 800_000,
        "default_conversion": 100_000,
        "conversion_max": 500_000,
        # States that broadly exempt IRA/pension distributions from state income tax — so a Roth
        # conversion there incurs federal tax only (the "conversion arbitrage", led by Illinois).
        "states_exempt_retirement": ["IL", "PA", "MS"],
    },
}


def estate_classification(state: str) -> dict:
    """Death-tax environment for the estate view (Option 1: Illinois precise, others neutral).
    Returns {"kind": "illinois"|"levy"|"none", "type": "estate"|"inheritance"|"both"|None}. Pure;
    the page JS mirrors this by reading the same `state_estate` map off the embedded state."""
    if state == "IL":
        return {"kind": "illinois", "type": "estate"}
    t = ASSUMPTIONS["estate"]["state_estate"].get(state)
    return {"kind": "levy", "type": t} if t else {"kind": "none", "type": None}


def compounded_fee_drag(balance: float, fee_rate: float, growth_rate: float, years: float) -> float:
    """Terminal dollars lost to an annual fee over `years`: the gap between compounding at the
    gross growth rate versus net of the fee. Used by the 401(k) rollover escape-hatch comparison."""
    if balance <= 0:
        return 0.0
    return balance * ((1 + growth_rate) ** years - (1 + max(0.0, growth_rate - fee_rate)) ** years)


def roth_conversion(conversion: float, fed_ord_rate: float, state_rate: float,
                    state_exempts_retirement: bool) -> dict:
    """Tax on a Roth conversion: federal ordinary income on the converted amount, plus state
    ordinary tax UNLESS the state exempts retirement distributions (e.g. Illinois) — in which case
    only federal applies and `state_saved` is the state tax avoided (the conversion arbitrage)."""
    conv = max(0.0, conversion)
    fed = conv * max(0.0, fed_ord_rate)
    would_owe_state = conv * max(0.0, state_rate)
    state = 0.0 if state_exempts_retirement else would_owe_state
    return {"federal": fed, "state": state, "total": fed + state,
            "state_saved": would_owe_state if state_exempts_retirement else 0.0}

# The Illinois AG estate-tax curve is canonical in drift.state_facts (IL_AG_CURVE) — the same rows
# feed this Python calculator and the workspace JS (injected via il_ag_curve above). Illustrative;
# the real AG figure depends on QTIP elections/deductions and the estate attorney files the exact one.
_IL_AG_CURVE = IL_AG_CURVE


def _il_ag_tax(excess: float) -> float:
    """Calibrated IL estate tax on the amount over the exclusion (AG-calculator curve)."""
    if excess <= 0:
        return 0.0
    bp, base, rate = _IL_AG_CURVE[0]
    for b, t, r in _IL_AG_CURVE:
        if excess >= b:
            bp, base, rate = b, t, r
        else:
            break
    return base + rate * (excess - bp)


def il_estate_tax(estate: float, exclusion: float) -> float:
    """Illustrative Illinois estate tax, calibrated to the Illinois AG calculator: $0 at or below
    the exclusion (the cliff into taxability), then the calibrated curve on the amount above it
    (top marginal 16%). The HB2601 toggle raises the exclusion, shifting the whole curve's
    baseline. Illustrative only — Illinois' actual computation (QTIP elections, deductions) can
    differ; the estate attorney produces the filing figure. Mirrors the JS on the Tax Lab page."""
    return _il_ag_tax(max(0.0, estate - exclusion))


def location_alpha3(taxable: float, traditional: float, roth: float,
                    mom_drag_rate: float, passive_drag_rate: float,
                    growth_rate: float, years: float) -> dict:
    """Three-account asset-location alpha (taxable / Traditional pre-tax / Roth tax-free).

    Optimized placement stacks the high-turnover momentum sleeve into the tax-advantaged
    accounts (Roth first for tax-free compounding, then Traditional) and isolates the
    low-drag buy-and-hold benchmark in the taxable account. The Roth and Traditional balances
    grow identically whichever asset sits in them (both shelter the annual drag), so the alpha
    lives entirely in the taxable account: the annual tax saved versus a naive proportional
    spread is (T·A/W)·(mdr − pdr), with A = traditional + roth and W = T + A. Reinvested at
    `growth_rate`, the future value of that annual saving over the horizon is the terminal
    location alpha. Mirrors the JS on the Tax Lab page; kept here for automated coverage.
    """
    w = taxable + traditional + roth
    a = traditional + roth
    if w <= 0:
        return {"annual_saved": 0.0, "terminal_alpha": 0.0, "overlap": 0.0, "sleeve": a}
    overlap = taxable * a / w
    annual = overlap * max(0.0, mom_drag_rate - passive_drag_rate)
    fv = (((1 + growth_rate) ** years - 1) / growth_rate) if growth_rate > 0 else years
    return {"annual_saved": annual, "terminal_alpha": annual * fv, "overlap": overlap, "sleeve": a}


def location_alpha3_range(taxable: float, traditional: float, roth: float,
                          mom_drag_rate: float, passive_drag_rate: float,
                          growth_rate: float, years: float,
                          drag_band: float = 0.25, growth_band: float = 0.02) -> dict:
    """A defensible sensitivity interval around location_alpha3 (M3).

    The annual tax saved scales with the momentum sleeve's drag — itself the product of the
    effective tax rate, turnover, and realized-gain rate — so we flex that drag by ±`drag_band`
    (relative) to bound the annual figure. The terminal value also rides the reinvestment / market
    return, flexed by ±`growth_band` (absolute). Returns base / low / high for both the annual saving
    and the terminal location alpha — a range a CPA or examiner can interrogate, not a point claim.
    Illustrative; mirrors the JS on the Tax Lab page.
    """
    base = location_alpha3(taxable, traditional, roth, mom_drag_rate, passive_drag_rate, growth_rate, years)
    lo = location_alpha3(taxable, traditional, roth, max(0.0, mom_drag_rate * (1 - drag_band)),
                         passive_drag_rate, max(0.0, growth_rate - growth_band), years)
    hi = location_alpha3(taxable, traditional, roth, mom_drag_rate * (1 + drag_band),
                         passive_drag_rate, growth_rate + growth_band, years)
    return {
        "base": base["annual_saved"], "annual_low": lo["annual_saved"], "annual_high": hi["annual_saved"],
        "terminal_base": base["terminal_alpha"], "terminal_low": lo["terminal_alpha"],
        "terminal_high": hi["terminal_alpha"],
    }


def after_fee(after_tax_return: float, annual_fee_rate: float, years: float) -> float:
    """Reduce an after-tax total return by an all-in annual fee (advisory + expense ratio)
    applied over the track. First-order: fee_rate · years on the base — illustrative, like
    the page's other linear approximations. Mirrors the JS on the Tax Lab page."""
    return after_tax_return - annual_fee_rate * max(0.0, years)


def breakeven_alpha(turnover: float, r_st: float, gain_per_turn: float) -> float:
    """Pre-tax alpha at which a strategy's short-term tax drag exactly cancels it:

        alpha* = turnover · gain_per_turn · r_st

    `turnover` is annual (1.0 = 100%), `r_st` the effective short-term rate, `gain_per_turn`
    the NAV fraction realized short-term per unit of turnover. A point (alpha, turnover)
    below this line — more turnover, less alpha — has net-negative after-tax alpha. Mirrors
    the JS on the Tax Lab page; kept here for automated coverage.
    """
    return turnover * gain_per_turn * max(0.0, r_st)


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
        "assumptions": ASSUMPTIONS, "models": models_state(),
    }
    _attach_statemap(state)        # static dimension dataset — independent of the ledger
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
    # Calibrate the frontier's breakeven slope from the live book: short-term gain realized
    # per year, per unit of annual turnover. Falls back to the assumption when turnover is 0.
    annual_st = (gp.st_realized / years) if years else 0.0
    gpt = (annual_st / gp.annual_turnover) if gp.annual_turnover else ASSUMPTIONS["gain_per_turn"]
    state["header"].update({
        "inception": led.get("inception", entries[0]["date"] if entries else ""),
        "updated": led.get("updated", ""),
        "sessions": len(entries),
        "years": round(years, 2),
        "pretax_return": gp.pretax_return,
        "annual_turnover": gp.annual_turnover,
        "short_term_share": gp.short_term_share,
        "avg_holding_days": gp.avg_holding_days,
        "gain_per_turn": round(gpt, 4),
    })
    state["profile"] = {
        "pretax_return": gp.pretax_return,
        "st_realized": gp.st_realized, "lt_realized": gp.lt_realized,
        "harvested_st": gp.harvested_st, "harvested_lt": gp.harvested_lt,
        "embedded_st": gp.embedded_st, "embedded_lt": gp.embedded_lt,
        "years": round(years, 2),
    }
    return state


def _attach_statemap(state: dict) -> None:
    """Embed the multi-dimension State Tax Map dataset so the Tax Lab cartogram can switch dimensions
    (capital gains / marriage / estate / basis step-up / Structural Alpha) from the same data the
    standalone exhibit uses. Map coloring is independent of the tax calculator (which reads the
    selected state's rates), so adding dimensions never affects the computed figures."""
    from .statemap import build_statemap
    sm = build_statemap()
    state["statemap"] = {"dimensions": sm["dimensions"], "states": sm["states"]}
