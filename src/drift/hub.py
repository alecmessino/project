"""The public landing hub, a markets-only front door for Driftwood.

Navigational + a few live headline numbers pulled from the already-generated
exhibits (the ledger JSON and the tearsheet's embedded state), degrading
gracefully when a file isn't present yet. mrbet is intentionally not linked here;
this site is markets-only.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Optional

# (title, file, blurb, appendix), order is the order shown on the hub. The primary funnel
# (appendix=False) is the flagship Structural Alpha + the tax-location tools; the Core Alpha (momentum)
# engine's hypothetical model portfolios sit in a "Core Alpha Research" appendix (appendix=True).
EXHIBITS = [
    ("How we invest", "thesis.html",
     "How Driftwood invests: evidence over prediction, taxes treated as part of investing, and a "
     "diversified core placed alongside a focused complement, one portfolio, measured after tax.", False),
    ("After-Tax Review", "taxlab.html",
     "See your after-tax return, and where each holding belongs, taxable, Traditional, or Roth, with "
     "estate step-up and tax-loss harvesting, by your bracket and state.", False),
    ("The Tax Diagnostic", "leakage.html",
     "The one-page before/after: where a concentrated, high-turnover account loses return to tax, "
     "and how much careful placement puts back on an identical exposure.", False),
    ("State Tax Atlas", "statemap.html",
     "Fifty states across eight dimensions, capital gains, marriage, estate, munis, QSBS, losses, and "
     "basis step-up, plus what careful tax management can change in each.", False),
    ("State tax guides (50 states + DC)", "states.html",
     "A capital-gains, estate, marriage, and basis-step-up profile for every state, each with what "
     "careful tax management can recover there, and a one-click personalized diagnostic.", False),
    ("Single asset risk", "concentration.html",
     "How to de-risk a concentrated stock position: 22 strategies across selling, harvesting, hedging, "
     "deferring, and giving, scored on liquidity, speed, fees, tax cost, customization, and simplicity.", False),
    ("Current model portfolio", "equities.html",
     "What the hypothetical model portfolio holds now, its sleeves, the last rebalance in and out, and "
     "the dated track. A research model, not a client account.", True),
    ("Model portfolio ledger", "ledger.html",
     "The append-only historical record: every change, every mark, with attribution. A hypothetical "
     "backtest, not actual trading or any client account.", True),
    ("Model portfolio · long history", "tearsheet.html",
     "The model across decades of daily history: strategy vs buy-and-hold, fit in-sample and reported "
     "out-of-sample. Hypothetical.", True),
    ("Research studies", "equities_case_studies.html",
     "Educational backtests on why the approach behaves as it does: time-series, cross-sectional, "
     "lookback & cost sensitivity, and a no-trend control.", True),
]


def _embedded_state(path: Path) -> Optional[dict]:
    """Extract the inlined window.__STATE__ JSON from a generated exhibit."""
    try:
        html = path.read_text()
    except Exception:
        return None
    m = re.search(r"window\.__STATE__ = (.*?);\n", html)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except Exception:
        return None


def _max_drawdown(equity: list[float]) -> float:
    """Worst peak-to-trough decline of a cumulative equity series (0..1)."""
    peak, mdd = float("-inf"), 0.0
    for v in equity:
        if v > peak:
            peak = v
        if peak > 0:
            mdd = max(mdd, 1.0 - v / peak)
    return mdd


def build_hub(docs_dir: str | Path = "docs") -> dict:
    """Assemble the hub state: live headline metrics, value-adds, and the exhibit index."""
    docs = Path(docs_dir)
    headline: list[dict] = []
    value_adds: list[dict] = []

    # ── Hero: the firm's SUBSTANTIATED edge (Structural Alpha), not the momentum research track.
    # Sourced from the leakage engine (regression-locked to scripts/tax_alpha by
    # tests/test_leakage_alpha_lineage.py), a contextualized before/after, never a bare return.
    from .leakage import build_leakage
    leak = build_leakage()
    hero = {
        "keep_before": leak["before"]["keep_pct"],       # % of the 30y pre-tax gain kept, tax-naive
        "keep_after": leak["after"]["keep_pct"],         # … same exposure, tax-managed
        "alpha_low": leak["headline"]["alpha_low"],      # illustrative Structural Alpha band (%/yr)
        "alpha_high": leak["headline"]["alpha_high"],
        "horizon": leak["header"]["horizon_years"],
        # The honest inversion: the tax-managed book earns slightly LESS pre-tax and still ends
        # wealthier after tax, the sentence sophisticated readers look for.
        "pretax_before": leak["headline"]["pretax_before"],
        "pretax_after": leak["headline"]["pretax_after"],
    }

    # The homepage carries NO performance numbers, not the model return, not Sharpe, not drawdown. Those
    # figures live one click deeper, on the research pages themselves (linked from the "Research" appendix).
    # `headline` stays empty by design; the hero + the single tax pillar are the only figures on the page.

    # Three DISTINCT dimensions of value, tax efficiency, implementation quality, behavioral durability.
    # The homepage makes NO expected-return claim: only the tax pillar carries a number (the firm's
    # substantiated edge). All performance figures, Sharpe, the model track, live in Research.

    # 1 · Keep more (taxes), the one number. Dollars lead (families think in dollars); the annualized
    # band is the supporting frame. "Structural Alpha" is named once, small, in the note.
    value_adds.append({
        "tag": "Keep more",
        "title": "A portfolio built to be held, and taxed lightly.",
        "stat": f"${hero['keep_before'] * 10_000:,.0f} → ${hero['keep_after'] * 10_000:,.0f}",
        "stat_label": f"kept from $1 million of realized gains over {hero['horizon']} years, after tax, an "
                      f"illustrative +{hero['alpha_low']:.1f}–{hero['alpha_high']:.1f}%/yr (modeled; federal to a high-tax state)",
        "note": "A diversified, low-turnover portfolio, with harvesting, lot selection, and account "
                "placement handing less of it to taxes. Driftwood calls the cumulative benefit of those "
                "implementation decisions Structural Alpha. Illustrative; your figure depends on your "
                "bracket and holdings.",
    })

    # 2 · Build better (architecture), no number. A process advantage, not a forecast.
    value_adds.append({
        "tag": "Build better",
        "title": "One portfolio, built as a system.",
        "stat": "",
        "stat_label": "",
        "note": "A diversified, low-turnover core, placed by account and coordinated across taxable, "
                "Traditional, and Roth, so allocation, location, harvesting, and withdrawals work "
                "together, not apart. Implementation, not prediction.",
    })

    # 3 · Stay invested (behavior), no number. The durability that lets compounding finish.
    value_adds.append({
        "tag": "Stay invested",
        "title": "The best portfolio is one you're glad to own in twenty years.",
        "stat": "",
        "stat_label": "",
        "note": "Most of the damage in investing is done by leaving at the wrong time. A portfolio built "
                "to be held, diversified, low-cost, and understood, is one you can stay with long enough "
                "for compounding to do its work.",
    })

    exhibits = [{"title": t, "href": h, "desc": d, "present": (docs / h).exists(), "appendix": ap}
                for t, h, d, ap in EXHIBITS]
    return {
        "header": {
            "generated": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        },
        "hero": hero,
        "headline": headline,
        "value_adds": value_adds,
        "exhibits": exhibits,
    }
