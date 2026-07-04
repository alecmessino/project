"""Driftwood institutional model portfolios (firm IPS layer).

These are the firm's *standard allocation models* — the destination a prospect's legacy
portfolio transitions into. They are deliberately SEPARATE from the Driftwood momentum
backtest (`ledger.py`): Driftwood is one hypothetical, high-turnover satellite sleeve; these
are diversified, low-cost strategic allocations built primarily on Avantis funds. The
"Estimated Structural Alpha" a transition produces is tax + fee optimization (see
`taxlab.location_alpha3` and the fee delta), NOT a claim that these funds out-perform.

Target weights are illustrative and must be CONFIRMED against the firm's signed IPS before
use with a client. Expense ratios are representative public figures (decimal, e.g. 0.0015 =
15 bps) for the blended-cost estimate; verify against current fund prospectuses.
"""

from __future__ import annotations

# asset_class ∈ {"equity", "fixed_income", "cash"}. "DRIFT" is the firm's own momentum sleeve
# (the Driftwood satellite), priced at its strategy cost, not a third-party fund.
_HOLDING_NAMES = {
    "AVUS": "Avantis U.S. Equity",
    "AVUV": "Avantis U.S. Small Cap Value",
    "AVDE": "Avantis International Equity",
    "AVES": "Avantis Emerging Markets Value",
    "AVIG": "Avantis Core Fixed Income",
    "BIL":  "SPDR Bloomberg 1-3 Month T-Bill",
    "DRIFT": "Driftwood momentum sleeve (satellite)",
}
_HOLDING_ER = {
    "AVUS": 0.0015, "AVUV": 0.0025, "AVDE": 0.0023, "AVES": 0.0036,
    "AVIG": 0.0015, "BIL": 0.001359, "DRIFT": 0.0030,
}
_HOLDING_CLASS = {
    "AVUS": "equity", "AVUV": "equity", "AVDE": "equity", "AVES": "equity",
    "AVIG": "fixed_income", "BIL": "cash", "DRIFT": "equity",
}

# (ticker, weight) — weights are fractions and must sum to 1.0 per model (asserted in tests).
_MODELS_RAW = [
    {
        "id": "aggressive_growth",
        "name": "Aggressive Growth",
        "tagline": "95% equity / 5% liquidity — maximal diversified equity exposure.",
        "holdings": [("AVUS", 0.45), ("AVUV", 0.20), ("AVDE", 0.18), ("AVES", 0.12), ("BIL", 0.05)],
    },
    {
        "id": "growth",
        "name": "Growth",
        "tagline": "85% equity / 15% fixed income — a fixed-income ballast via Avantis Core.",
        "holdings": [("AVUS", 0.38), ("AVUV", 0.15), ("AVDE", 0.17), ("AVES", 0.15), ("AVIG", 0.15)],
    },
    {
        "id": "core_satellite",
        "name": "Aggressive Core + Satellite",
        "tagline": "87% disciplined core / 8% Driftwood satellite / 5% cash.",
        "holdings": [("AVUS", 0.40), ("AVUV", 0.12), ("AVDE", 0.20), ("AVES", 0.15),
                     ("DRIFT", 0.08), ("BIL", 0.05)],
        # Structure split (distinct from the asset-class mix below): the self-directed satellite
        # is the Driftwood momentum sleeve — the one place the firm's engine enters a model.
        "structure": {"core": 0.87, "satellite": 0.08, "cash": 0.05},
    },
]


def _expand(model: dict) -> dict:
    """Attach per-holding names/ER/class, the blended expense ratio, and the asset-class mix."""
    holdings = []
    mix = {"equity": 0.0, "fixed_income": 0.0, "cash": 0.0}
    blended_er = 0.0
    for ticker, w in model["holdings"]:
        cls = _HOLDING_CLASS[ticker]
        mix[cls] += w
        blended_er += w * _HOLDING_ER[ticker]
        holdings.append({
            "ticker": ticker, "name": _HOLDING_NAMES[ticker], "weight": round(w, 4),
            "asset_class": cls, "er": _HOLDING_ER[ticker],
        })
    out = {
        "id": model["id"], "name": model["name"], "tagline": model["tagline"],
        "holdings": holdings,
        "blended_er": round(blended_er, 5),
        "asset_mix": {k: round(v, 4) for k, v in mix.items()},
        "note": "Illustrative target weights — confirm against the firm's signed IPS.",
    }
    if "structure" in model:
        out["structure"] = model["structure"]
    return out


MODELS = [_expand(m) for m in _MODELS_RAW]


def models_state() -> list[dict]:
    """The JSON-able firm-model list embedded into the Tax Lab state."""
    return MODELS
