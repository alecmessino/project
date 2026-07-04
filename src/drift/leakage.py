"""The Tax-Leakage Diagnostic state — a one-page Before/After pitch artifact.

A concentrated, high-turnover portfolio quietly leaks return to tax via short-term gains; the
Structural Alpha engine plugs those leaks (lot protection + hysteresis, harvesting + rate arbitrage,
asset location). This module holds the diagnostic's numbers in ONE place and assembles the JSON-able
state the page renders.

The figures are the committed real-cache outputs of `scripts/tax_alpha.py` (the Tax-Alpha
decomposition) over the **30-year window (1996–2026)** — the SAME horizon the long-history tearsheet
uses, so every client artifact is calibrated to one headline horizon. They are ILLUSTRATIVE,
after-tax, paid-as-you-go on a single proxy-spliced path — a tax-efficiency result, NOT a pre-tax
return claim (the structural book's pre-tax CAGR is slightly LOWER). Nothing here is a forecast that
any fund out-performs; `tilt_overlay`/`lot_protect` are OFF in every shipped config and not wired
into the live signal.

`STATE_ALPHA` (per-state after-tax CAGR %/yr) drives the personalized diagnostic (`leakage.html`
reads `?state`/`?port`). Regenerate it with `TAX_ALPHA_STATES=1 python scripts/tax_alpha.py` (the
30-year window is the script's default; `TAX_ALPHA_YEARS=40` reproduces the prior full-sample run).
"""

from __future__ import annotations

import time

# Per-state after-tax CAGR (%/yr): {state_code: {before (concentrated, naive), after (Structural
# Alpha), alpha (recovered)}}. "—" = no state tax (federal only). Source: tax_alpha.all_state_alpha
# on tests/data/matrix_history.json, 30y window (PYTHONHASHSEED=0). "NYC" carries the NYC local overlay.
STATE_ALPHA = {
    "—": {"before": 2.7, "after": 6.3, "alpha": 3.7},
    "AK": {"before": 2.7, "after": 6.3, "alpha": 3.7}, "FL": {"before": 2.7, "after": 6.3, "alpha": 3.7},
    "NV": {"before": 2.7, "after": 6.3, "alpha": 3.7}, "NH": {"before": 2.7, "after": 6.3, "alpha": 3.7},
    "SD": {"before": 2.7, "after": 6.3, "alpha": 3.7}, "TN": {"before": 2.7, "after": 6.3, "alpha": 3.7},
    "TX": {"before": 2.7, "after": 6.3, "alpha": 3.7}, "WY": {"before": 2.7, "after": 6.3, "alpha": 3.7},
    "WA": {"before": 2.6, "after": 6.0, "alpha": 3.4}, "AZ": {"before": 2.2, "after": 6.1, "alpha": 3.9},
    "CO": {"before": 1.9, "after": 5.9, "alpha": 4.0}, "GA": {"before": 1.7, "after": 5.8, "alpha": 4.1},
    "ID": {"before": 1.7, "after": 5.8, "alpha": 4.1}, "IL": {"before": 1.8, "after": 5.9, "alpha": 4.0},
    "IN": {"before": 2.1, "after": 6.0, "alpha": 3.9}, "IA": {"before": 1.7, "after": 5.8, "alpha": 4.1},
    "KY": {"before": 2.0, "after": 6.0, "alpha": 4.0}, "MA": {"before": 1.3, "after": 5.7, "alpha": 4.4},
    "MI": {"before": 1.9, "after": 5.9, "alpha": 4.0}, "MS": {"before": 1.9, "after": 5.9, "alpha": 4.0},
    "NC": {"before": 1.9, "after": 5.9, "alpha": 4.0}, "PA": {"before": 2.1, "after": 6.0, "alpha": 3.9},
    "UT": {"before": 1.9, "after": 5.9, "alpha": 4.0}, "AL": {"before": 1.8, "after": 5.9, "alpha": 4.1},
    "AR": {"before": 2.0, "after": 6.0, "alpha": 4.0}, "CA": {"before": 0.4, "after": 5.1, "alpha": 4.7},
    "CT": {"before": 1.5, "after": 5.7, "alpha": 4.2}, "DE": {"before": 1.5, "after": 5.7, "alpha": 4.2},
    "DC": {"before": 0.8, "after": 5.4, "alpha": 4.5}, "HI": {"before": 0.8, "after": 5.5, "alpha": 4.7},
    "KS": {"before": 1.7, "after": 5.8, "alpha": 4.1}, "LA": {"before": 1.9, "after": 5.9, "alpha": 4.0},
    "ME": {"before": 1.5, "after": 5.7, "alpha": 4.2}, "MD": {"before": 1.7, "after": 5.8, "alpha": 4.1},
    "MN": {"before": 1.0, "after": 5.4, "alpha": 4.4}, "MO": {"before": 1.8, "after": 5.9, "alpha": 4.0},
    "MT": {"before": 1.7, "after": 5.9, "alpha": 4.2}, "NE": {"before": 1.7, "after": 5.8, "alpha": 4.1},
    "NJ": {"before": 0.8, "after": 5.4, "alpha": 4.5}, "NM": {"before": 1.7, "after": 5.9, "alpha": 4.2},
    "NY": {"before": 0.8, "after": 5.3, "alpha": 4.5}, "ND": {"before": 2.2, "after": 6.1, "alpha": 3.9},
    "NYC": {"before": 0.2, "after": 5.0, "alpha": 4.8}, "OH": {"before": 2.1, "after": 6.0, "alpha": 3.9},
    "OK": {"before": 1.9, "after": 5.9, "alpha": 4.0}, "OR": {"before": 1.0, "after": 5.4, "alpha": 4.4},
    "RI": {"before": 1.6, "after": 5.8, "alpha": 4.1}, "SC": {"before": 1.6, "after": 5.9, "alpha": 4.2},
    "VT": {"before": 1.2, "after": 5.7, "alpha": 4.5}, "VA": {"before": 1.7, "after": 5.8, "alpha": 4.1},
    "WV": {"before": 1.8, "after": 5.9, "alpha": 4.1}, "WI": {"before": 1.4, "after": 5.7, "alpha": 4.3},
}

# Friendly names for the personalized headline ("for an Illinois portfolio"). Codes not present fall
# back to the code itself.
STATE_NAMES = {
    "—": "a no-income-tax state", "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "DC": "Washington DC",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana",
    "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri",
    "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey",
    "NM": "New Mexico", "NY": "New York", "NYC": "New York City", "NC": "North Carolina",
    "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania",
    "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas",
    "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming",
}

# The four curated rows shown in the static "by state" exhibit (numbers pulled from STATE_ALPHA).
_DISPLAY = [("Federal only", "—"), ("Illinois", "IL"), ("New York", "NY"), ("California", "CA")]

# The two engine levers that make up the assumption-free recovery (after-tax %/yr; ~federal→CA range).
_LEVERS = [
    {"name": "Lot protection + hysteresis",
     "share": "≈ 60–65%",
     "desc": "Holds positions through noise and protects unrealized lots, converting short-term churn "
             "into long-term gains taxed ~17 points lower."},
    {"name": "Harvesting + rate arbitrage",
     "share": "≈ 35–40%",
     "desc": "Realizes losses and nets them short-term-first against the highest-rate gains — banking "
             "the spread a buy-and-hold ETF can't reach."},
    {"name": "Asset location",
     "share": "household-specific",
     "desc": "Stacks the high-turnover sleeve into Roth/Traditional so its short-term gains escape tax; "
             "quantified per client in the Tax Lab."},
]


def build_leakage() -> dict:
    """Assemble the Tax-Leakage Diagnostic state (fixed illustrative figures + the per-state table for
    the personalized variant). `leakage.html` reads `?state`/`?port` to localize off `state_alpha`."""
    return {
        "header": {
            "generated": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "source": "scripts/tax_alpha.py · 30y proxy-spliced cache, 1996–2026 (tests/data/matrix_history.json)",
            "horizon_years": 30,
        },
        # The headline recovery range across states (the Structural Alpha (tax) number).
        "headline": {"alpha_low": 3.7, "alpha_high": 4.7,
                     "pretax_before": 9.4, "pretax_after": 9.1},
        "before": {
            "label": "Concentrated · high-turnover",
            "sub": "A concentrated, high-turnover book in a taxable account, taxed naively.",
            "st_share": 96, "turnover": 371,
            "atc_low": 0.4, "atc_high": 2.7,         # after-tax CAGR, CA → federal-only
            "keep_pct": 9,                            # keeps 9% of the 30y pre-tax gain after tax
        },
        "after": {
            "label": "Structural Alpha · tax-managed",
            "sub": "The same exposure, run through the engine: lot protection + hysteresis + harvesting.",
            "st_share": 53, "turnover": 136,
            "atc_low": 5.1, "atc_high": 6.3,
            "keep_pct": 41,
        },
        "levers": _LEVERS,
        "states": [{"state": label, "before": STATE_ALPHA[c]["before"],
                    "after": STATE_ALPHA[c]["after"], "alpha": STATE_ALPHA[c]["alpha"]}
                   for label, c in _DISPLAY],
        # For the personalized diagnostic: full per-state table + names; the page localizes from these.
        "state_alpha": STATE_ALPHA,
        "state_names": STATE_NAMES,
    }
