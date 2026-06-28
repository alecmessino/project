"""The Tax-Leakage Diagnostic state — a one-page Before/After pitch artifact.

A concentrated, high-turnover portfolio quietly leaks return to tax via short-term gains; the
Structural Alpha engine plugs those leaks (lot protection + hysteresis, harvesting + rate arbitrage,
asset location). This module holds the diagnostic's numbers in ONE place and assembles the JSON-able
state the page renders.

The figures are the committed real-cache outputs of `scripts/tax_alpha.py` (the Tax-Alpha
decomposition), documented in `docs/Tilt_Validation_Results.md` → "Tax-Alpha decomposition". They are
ILLUSTRATIVE, after-tax, paid-as-you-go, on a single 40-year proxy-spliced path — a tax-efficiency
result, NOT a pre-tax return claim (the structural book's pre-tax CAGR is slightly LOWER). Nothing
here is a forecast that any fund out-performs; `tilt_overlay`/`lot_protect` are OFF in every shipped
config and not wired into the live signal.

`STATE_ALPHA` (per-state after-tax CAGR %/yr) drives the personalized diagnostic (`leakage.html`
reads `?state`/`?port`). Regenerate it with `TAX_ALPHA_STATES=1 python scripts/tax_alpha.py`.
"""

from __future__ import annotations

import time

# Per-state after-tax CAGR (%/yr): {state_code: {before (concentrated, naive), after (Structural
# Alpha), alpha (recovered)}}. "—" = no state tax (federal only). Source: tax_alpha.all_state_alpha
# on tests/data/matrix_history.json (PYTHONHASHSEED=0). "NYC" carries the NYC local overlay.
STATE_ALPHA = {
    "—": {"before": 3.1, "after": 6.4, "alpha": 3.2},
    "AK": {"before": 3.1, "after": 6.4, "alpha": 3.2}, "FL": {"before": 3.1, "after": 6.4, "alpha": 3.2},
    "NV": {"before": 3.1, "after": 6.4, "alpha": 3.2}, "NH": {"before": 3.1, "after": 6.4, "alpha": 3.2},
    "SD": {"before": 3.1, "after": 6.4, "alpha": 3.2}, "TN": {"before": 3.1, "after": 6.4, "alpha": 3.2},
    "TX": {"before": 3.1, "after": 6.4, "alpha": 3.2}, "WY": {"before": 3.1, "after": 6.4, "alpha": 3.2},
    "WA": {"before": 3.1, "after": 6.1, "alpha": 3.0}, "AZ": {"before": 2.7, "after": 6.1, "alpha": 3.4},
    "CO": {"before": 2.4, "after": 6.0, "alpha": 3.6}, "GA": {"before": 2.2, "after": 5.9, "alpha": 3.7},
    "ID": {"before": 2.1, "after": 5.8, "alpha": 3.7}, "IL": {"before": 2.3, "after": 5.9, "alpha": 3.6},
    "IN": {"before": 2.6, "after": 6.1, "alpha": 3.5}, "IA": {"before": 2.1, "after": 5.8, "alpha": 3.7},
    "KY": {"before": 2.4, "after": 6.0, "alpha": 3.6}, "MA": {"before": 1.7, "after": 5.7, "alpha": 4.0},
    "MI": {"before": 2.4, "after": 6.0, "alpha": 3.6}, "MS": {"before": 2.3, "after": 5.9, "alpha": 3.6},
    "NC": {"before": 2.3, "after": 6.0, "alpha": 3.6}, "PA": {"before": 2.6, "after": 6.1, "alpha": 3.5},
    "UT": {"before": 2.3, "after": 6.0, "alpha": 3.6}, "AL": {"before": 2.3, "after": 5.9, "alpha": 3.6},
    "AR": {"before": 2.5, "after": 6.1, "alpha": 3.6}, "CA": {"before": 0.8, "after": 5.2, "alpha": 4.3},
    "CT": {"before": 1.9, "after": 5.7, "alpha": 3.8}, "DE": {"before": 2.0, "after": 5.8, "alpha": 3.8},
    "DC": {"before": 1.3, "after": 5.4, "alpha": 4.1}, "HI": {"before": 1.3, "after": 5.5, "alpha": 4.2},
    "KS": {"before": 2.1, "after": 5.8, "alpha": 3.7}, "LA": {"before": 2.4, "after": 6.0, "alpha": 3.6},
    "ME": {"before": 1.9, "after": 5.7, "alpha": 3.8}, "MD": {"before": 2.1, "after": 5.8, "alpha": 3.7},
    "MN": {"before": 1.4, "after": 5.5, "alpha": 4.0}, "MO": {"before": 2.3, "after": 5.9, "alpha": 3.6},
    "MT": {"before": 2.1, "after": 5.9, "alpha": 3.8}, "NE": {"before": 2.1, "after": 5.8, "alpha": 3.7},
    "NJ": {"before": 1.3, "after": 5.4, "alpha": 4.1}, "NM": {"before": 2.1, "after": 5.9, "alpha": 3.8},
    "NY": {"before": 1.3, "after": 5.4, "alpha": 4.1}, "ND": {"before": 2.7, "after": 6.2, "alpha": 3.5},
    "NYC": {"before": 0.6, "after": 5.0, "alpha": 4.4}, "OH": {"before": 2.5, "after": 6.0, "alpha": 3.5},
    "OK": {"before": 2.3, "after": 5.9, "alpha": 3.6}, "OR": {"before": 1.4, "after": 5.5, "alpha": 4.0},
    "RI": {"before": 2.1, "after": 5.8, "alpha": 3.7}, "SC": {"before": 2.1, "after": 5.9, "alpha": 3.8},
    "VT": {"before": 1.7, "after": 5.7, "alpha": 4.1}, "VA": {"before": 2.1, "after": 5.8, "alpha": 3.7},
    "WV": {"before": 2.2, "after": 5.9, "alpha": 3.7}, "WI": {"before": 1.8, "after": 5.8, "alpha": 3.9},
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
     "share": "≈ 55–60%",
     "desc": "Holds positions through noise and protects unrealized lots, converting short-term churn "
             "into long-term gains taxed ~17 points lower."},
    {"name": "Harvesting + rate arbitrage",
     "share": "≈ 40–45%",
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
            "source": "scripts/tax_alpha.py · 40y proxy-spliced cache (tests/data/matrix_history.json)",
            "horizon_years": 40,
        },
        # The headline recovery range across states (the Structural Alpha (tax) number).
        "headline": {"alpha_low": 3.2, "alpha_high": 4.3,
                     "pretax_before": 9.9, "pretax_after": 9.3},
        "before": {
            "label": "Concentrated · high-turnover",
            "sub": "A legacy momentum / concentrated book in a taxable account, taxed naively.",
            "st_share": 94, "turnover": 344,
            "atc_low": 0.8, "atc_high": 3.1,         # after-tax CAGR, CA → federal-only
            "keep_pct": 6,                            # keeps 6% of the 40y pre-tax gain after tax
        },
        "after": {
            "label": "Structural Alpha · tax-managed",
            "sub": "The same exposure, run through the engine: lot protection + hysteresis + harvesting.",
            "st_share": 50, "turnover": 141,
            "atc_low": 5.2, "atc_high": 6.4,
            "keep_pct": 32,
        },
        "levers": _LEVERS,
        "states": [{"state": label, "before": STATE_ALPHA[c]["before"],
                    "after": STATE_ALPHA[c]["after"], "alpha": STATE_ALPHA[c]["alpha"]}
                   for label, c in _DISPLAY],
        # For the personalized diagnostic: full per-state table + names; the page localizes from these.
        "state_alpha": STATE_ALPHA,
        "state_names": STATE_NAMES,
    }
