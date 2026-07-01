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
# (appendix=False) leads with Structural Alpha; the momentum exhibits are relegated to an honestly
# labeled "Exploratory research" appendix (appendix=True) — proof-of-work, not the deployed strategy.
EXHIBITS = [
    ("Thesis & approach", "thesis.html",
     "How Structural Alpha works — deliberate factor exposure (engineered beta) plus mechanical tax "
     "management — and the honest research behind the name.", False),
    ("Tax Lab", "taxlab.html",
     "Holistic asset-location engine: after-tax return, three-account placement (taxable / Traditional / "
     "Roth), estate step-up, and tax-loss harvesting — personalized by bracket and state.", False),
    ("Tax-Leakage Diagnostic", "leakage.html",
     "The one-page Before/After: where a concentrated, high-turnover book leaks return to tax, and how "
     "Structural Alpha plugs it — the quantified tax edge on an identical exposure.", False),
    ("State Tax Map", "statemap.html",
     "Fifty states, five dimensions — capital gains, marriage, estate, basis step-up, and the "
     "Structural Alpha our engine recovers from each state's tax landscape.", False),
    ("State tax guides (50 states + DC)", "states.html",
     "A capital-gains, estate, marriage, and basis-step-up profile for every state — each with the "
     "illustrative Structural Alpha our engine targets there and a one-click personalized diagnostic.", False),
    ("Model Portfolio (hypothetical)", "ledger.html",
     "Exploratory research — a hypothetical, append-only momentum backtest marked daily, with alpha/beta "
     "attribution. Not the deployed strategy, not actual trading or any client account.", True),
    ("Model Portfolio · long history", "tearsheet.html",
     "Exploratory research — the momentum model across decades of daily history: strategy vs buy-and-hold, "
     "fit in-sample and reported out-of-sample.", True),
    ("Dashboard", "equities.html",
     "Exploratory research — the momentum engine's signals, the relative-strength ranking, and per-name "
     "backtests across the matrix.", True),
    ("Case studies", "equities_case_studies.html",
     "Exploratory research — five momentum backtests: time-series, cross-sectional, lookback & cost "
     "sensitivity, and a control.", True),
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
                    "sub": f"{len(entries)} sessions · hypothetical backtest from {j.get('inception', '')}",
                    "dd": f"−{own_dd*100:.0f}%",
                    "dd_label": "max drawdown · this track",
                    # Deliberately neutral: a hypothetical return is not a win to colour green.
                    "tone": "neutral",
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

    # ── Value-adds: the few things an investor actually weighs, each sourced from real exhibit
    # state and kept fair-and-balanced (every performance figure carries its risk and a hypothetical
    # label). Cards degrade gracefully — absent when their source exhibit isn't built yet.
    hdr = (led_state or {}).get("header", {})
    benches = (led_state or {}).get("benchmarks", [])
    # 1 · Tax + fee optimization — the firm's actual, deterministic edge (not product outperformance).
    if hdr.get("tax_drag") is not None and hdr.get("after_tax_total_return") is not None:
        value_adds.append({
            "tag": "Tax + fee optimization",
            "title": "We target the tax drag — not just the return.",
            "stat": f"−{hdr['tax_drag']*100:.0f}%",
            "stat_label": f"the model's own {hdr.get('total_return', 0)*100:.0f}% pre-tax → "
                          f"{hdr['after_tax_total_return']*100:.0f}% after tax",
            "note": "Asset location across taxable / Traditional / Roth plus tax-loss harvesting is built "
                    "to recover a share of exactly this drag. Illustrative — your figures depend on your situation.",
        })
    # 2 · Risk-managed — from the live track, paired with its drawdown (fair-and-balanced by construction).
    if hdr.get("sharpe") is not None and benches and own_dd is not None:
        bench_sh = " / ".join(f"{b.get('sharpe', 0):.2f}" for b in benches[:2])
        bench_lbl = " / ".join(b.get("label", "") for b in benches[:2])
        dd_self = own_dd
        bench_dd = " / ".join(f"−{b.get('max_drawdown', 0)*100:.0f}%" for b in benches[:2])
        value_adds.append({
            "tag": "Risk-managed, not return-chasing",
            "title": "Kept pace with equities — at a shallower drawdown.",
            "stat": f"{hdr['sharpe']:.2f}",
            "stat_label": f"Sharpe vs {bench_sh} for {bench_lbl} buy-and-hold",
            "note": f"Worst drawdown −{dd_self*100:.0f}% vs {bench_dd} over the same window. "
                    "Hypothetical model track, not a client account.",
        })
    # 3 · Out-of-sample honesty — from the multi-decade backtest; the trust signal is reporting the
    # number after the fit, with its full drawdown disclosed.
    if ts and ts.get("books"):
        bk = ts["books"][0]
        s, b, o = bk["strategy"], bk["benchmark"], bk["oos"]["test"]
        value_adds.append({
            "tag": "Stress-tested across decades",
            "title": "We report the out-of-sample number.",
            "stat": f"{o['sharpe']:.2f}",
            "stat_label": "out-of-sample Sharpe · multi-decade backtest, after the fit",
            "note": f"Through a worst-case −{s['max_drawdown']*100:.0f}% drawdown "
                    f"(vs −{b['max_drawdown']*100:.0f}% buy-and-hold). We show the figure after the fit, "
                    "including the worst loss — not just the in-sample curve.",
        })

    exhibits = [{"title": t, "href": h, "desc": d, "present": (docs / h).exists(), "appendix": ap}
                for t, h, d, ap in EXHIBITS]
    return {
        "header": {
            "generated": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        },
        "headline": headline,
        "value_adds": value_adds,
        "exhibits": exhibits,
    }
