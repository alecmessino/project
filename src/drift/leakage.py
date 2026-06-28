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
"""

from __future__ import annotations

import time

# After-tax CAGR (%/yr) by state — from scripts/tax_alpha.py on tests/data/matrix_history.json.
# (state_label, before_concentrated_naive, after_structural, tax_alpha_recovered)
_STATE_ROWS = [
    ("Federal only", 3.1, 6.4, 3.2),
    ("Illinois",     2.3, 5.9, 3.6),
    ("New York",     1.3, 5.4, 4.1),
    ("California",   0.8, 5.2, 4.3),
]

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
    """Assemble the Tax-Leakage Diagnostic state (fixed illustrative figures + provenance)."""
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
        "states": [{"state": s, "before": b, "after": a, "alpha": al} for s, b, a, al in _STATE_ROWS],
    }
