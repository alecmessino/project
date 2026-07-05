"""The public landing hub — a markets-only front door for Driftwood.

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

# (title, file, blurb, appendix) — order is the order shown on the hub. The primary funnel
# (appendix=False) is the flagship Structural Alpha + the tax-location tools; the Core Alpha (momentum)
# engine's hypothetical model portfolios sit in a "Core Alpha Research" appendix (appendix=True).
EXHIBITS = [
    ("How we invest", "thesis.html",
     "How Driftwood invests: evidence over prediction, taxes treated as part of investing, and a "
     "diversified core placed alongside a focused complement — one portfolio, measured after tax.", False),
    ("Tax Lab", "taxlab.html",
     "See your after-tax return, and where each holding belongs — taxable, Traditional, or Roth — with "
     "estate step-up and tax-loss harvesting, by your bracket and state.", False),
    ("Tax-Leakage Diagnostic", "leakage.html",
     "The one-page before/after: where a concentrated, high-turnover account quietly loses return to "
     "tax, and how much careful placement puts back on an identical exposure.", False),
    ("State Tax Map", "statemap.html",
     "Fifty states across seven dimensions — capital gains, marriage, estate, munis, QSBS, losses, and "
     "basis step-up — and what careful tax management can recover from each.", False),
    ("State tax guides (50 states + DC)", "states.html",
     "A capital-gains, estate, marriage, and basis-step-up profile for every state — each with what "
     "careful tax management can recover there, and a one-click personalized diagnostic.", False),
    ("Single asset risk", "concentration.html",
     "How to de-risk a concentrated stock position: 22 strategies across selling, harvesting, hedging, "
     "deferring, and giving — scored on liquidity, speed, fees, tax cost, customization, and simplicity.", False),
    ("Core Alpha book (hypothetical)", "equities.html",
     "Core Alpha Research — the current book: what the hypothetical Model Portfolio holds now, its signal "
     "strength by sleeve, the last rebalance in and out, and the dated track.", True),
    ("Model Portfolio ledger", "ledger.html",
     "Core Alpha Research — the append-only historical record: every change, every mark, with alpha/beta "
     "attribution. A hypothetical backtest, not actual trading or any client account.", True),
    ("Model Portfolio · long history", "tearsheet.html",
     "Core Alpha Research — the model across decades of daily history: strategy vs buy-and-hold, fit "
     "in-sample and reported out-of-sample (it survived the fit nearly unchanged).", True),
    ("Research studies", "equities_case_studies.html",
     "Core Alpha Research — educational backtests on why the engine behaves as it does: time-series, "
     "cross-sectional, lookback & cost sensitivity, and a no-trend control.", True),
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
    # tests/test_leakage_alpha_lineage.py) — a contextualized before/after, never a bare return.
    from .leakage import build_leakage
    leak = build_leakage()
    hero = {
        "keep_before": leak["before"]["keep_pct"],       # % of the 30y pre-tax gain kept, tax-naive
        "keep_after": leak["after"]["keep_pct"],         # … same exposure, tax-managed
        "alpha_low": leak["headline"]["alpha_low"],      # illustrative Structural Alpha band (%/yr)
        "alpha_high": leak["headline"]["alpha_high"],
        "horizon": leak["header"]["horizon_years"],
    }

    # Long-history tearsheet (the multi-decade backtest) and the live 445-session ledger are two
    # DISTINCT tracks. Keep their risk figures attributed to their own track — pairing one's return
    # with the other's drawdown is exactly the imbalanced framing the Marketing Rule targets.
    ts = _embedded_state(docs / "tearsheet.html")
    led_state = _embedded_state(docs / "ledger.html")

    # This track's OWN max drawdown, computed from its own equity curve — never borrowed from the
    # multi-decade backtest. Shared by the headline card and the risk value-add.
    own_dd = None
    led = docs / "ledger.json"
    if led.exists():
        try:
            j = json.loads(led.read_text())
            entries = j.get("entries", [])
            if entries:
                tr = entries[-1]["equity"] - 1.0
                own_dd = _max_drawdown([e["equity"] for e in entries if "equity" in e])
                headline.append({
                    "label": "Model Portfolio (hypothetical)",
                    "value": f"{tr*100:+.1f}%",
                    # Always date the data: an undated figure reads as current the day it goes stale.
                    "sub": f"{len(entries)} sessions · hypothetical backtest from {j.get('inception', '')} "
                           f"· data through {entries[-1].get('date', '?')}",
                    "dd": f"−{own_dd*100:.0f}%",
                    "dd_label": "max drawdown · this track",
                    # Deliberately neutral: a hypothetical return is not a win to colour green.
                    "tone": "neutral",
                    # A raw hypothetical return is research context, not the pitch — the template
                    # renders research-tagged headlines in the exploratory-research appendix.
                    "research": True,
                })
        except Exception:
            pass

    if ts:
        for bk in ts.get("books", []):
            s, b, o = bk["strategy"], bk["benchmark"], bk["oos"]["test"]
            headline.append({
                "label": f"{bk['name']} · max drawdown",
                "value": f"{s['max_drawdown']*100:.0f}% vs {b['max_drawdown']*100:.0f}%",
                "sub": f"multi-decade backtest, strategy vs buy & hold · OOS Sharpe {o['sharpe']:.2f}",
                "tone": "neutral",
            })

    # ── Value-adds: the three pillars of the architecture, process-led. Each number appears ONCE across
    # the whole hub (no repeated figures), and each performance figure carries its risk + a hypothetical
    # label. Cards degrade gracefully — absent when their source exhibit isn't built yet.
    hdr = (led_state or {}).get("header", {})
    benches = (led_state or {}).get("benchmarks", [])

    # 1 · Structural Alpha — the flagship (taxable wealth). Lead with the process; the tax-location
    # recovery is the supporting number.
    value_adds.append({
        "tag": "Structural Alpha · the flagship",
        "title": "A portfolio built to be held — and taxed lightly.",
        "stat": f"+{hero['alpha_low']:.1f}–{hero['alpha_high']:.1f}%/yr",
        "stat_label": "illustrative after-tax recovery, from no-tax states to California",
        "note": "A diversified, low-turnover portfolio, tilted toward the sources of return that have "
                "paid patient investors over time — and managed so that harvesting, lot selection, and "
                "account placement quietly hand less of it to taxes. For taxable accounts. Illustrative; "
                "your figure depends on your bracket and holdings.",
    })

    # 2 · Core Alpha — the tactical engine (tax-advantaged capital). The strongest honest stat is that
    # it survived out-of-sample nearly unchanged (no overfit); the current hypothetical track is context.
    if ts and ts.get("books"):
        bk = ts["books"][0]
        o = bk["oos"]["test"]
        tr = (bk["oos"].get("train") or {}).get("sharpe")
        robust = f"{o['sharpe']:.2f} ≈ {tr:.2f}" if tr is not None else f"{o['sharpe']:.2f}"
        cur = ""
        if hdr.get("sharpe") is not None and benches:
            bench_sh = " / ".join(f"{b.get('sharpe', 0):.2f}" for b in benches[:2])
            bench_lbl = " / ".join(b.get("label", "") for b in benches[:2])
            cur = (f" The current hypothetical track runs at Sharpe {hdr['sharpe']:.2f} "
                   f"(vs {bench_sh} for {bench_lbl}) — a separate, shorter window.")
        value_adds.append({
            "tag": "Core Alpha · a complementary engine",
            "title": "Built to persist, not to impress.",
            "stat": robust,
            "stat_label": "the out-of-sample result matched the in-sample one — the approach didn't flatter itself",
            "note": "The research prioritizes persistence over historical optimization. Tested across "
                    "decades, the out-of-sample result held up nearly unchanged — the sign of an approach "
                    "that wasn't fit to the past." + cur + " Higher-turnover, and meant for tax-advantaged "
                    "accounts. A hypothetical backtest, not a client account.",
        })

    # 3 · Tax-location — the engine that routes them (the moat). The before/after is the same exposure,
    # tax-naive vs tax-managed (NOT a jab at either return engine).
    value_adds.append({
        "tag": "Tax-location · where each dollar lives",
        "title": "The account is the decision that compounds.",
        "stat": f"{hero['keep_before']}% → {hero['keep_after']}%",
        "stat_label": f"share of a {hero['horizon']}-year gain kept after tax — the same holdings, taxed carelessly vs. deliberately",
        "note": "Placing the tactical strategy in tax-advantaged accounts and the diversified one in "
                "taxable — then harvesting losses along the way — is the quiet work that decides how much "
                "a family keeps. Federal-only illustration; not a forecast.",
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
