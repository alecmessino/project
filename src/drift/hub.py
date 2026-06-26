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

# (title, file, blurb) — order is the order shown on the hub.
EXHIBITS = [
    ("Thesis & findings", "thesis.html",
     "The trend-following thesis, the research, the results — and the name."),
    ("Model Portfolio (hypothetical)", "ledger.html",
     "Hypothetical, append-only backtest of the strategy — marked daily, with alpha/beta attribution. Not actual trading or any client account."),
    ("Model Portfolio · long history", "tearsheet.html",
     "The Model Portfolio across decades of daily history: strategy vs buy-and-hold, fit in-sample and reported out-of-sample."),
    ("Tax Lab", "taxlab.html",
     "Holistic asset-location engine: after-tax return, three-account placement (taxable / Traditional / "
     "Roth), estate step-up, and tax-loss harvesting — personalized by bracket and state."),
    ("Dashboard", "equities.html",
     "Live trend signals, the relative-strength ranking, and per-name backtests across the matrix."),
    ("Case studies", "equities_case_studies.html",
     "Five backtests: time-series, cross-sectional, lookback & cost sensitivity, and a control."),
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


def build_hub(docs_dir: str | Path = "docs") -> dict:
    """Assemble the hub state: live headline metrics + the exhibit index."""
    docs = Path(docs_dir)
    headline: list[dict] = []

    # Read the long-history tearsheet first so the Model Portfolio headline can carry its own
    # risk (max drawdown) alongside the return — a return shown without its drawdown is exactly the
    # imbalanced framing the Marketing Rule's fair-and-balanced standard targets.
    ts = _embedded_state(docs / "tearsheet.html")
    strat_dd = None
    if ts:
        for bk in ts.get("books", []):
            if bk.get("strategy", {}).get("max_drawdown") is not None:
                strat_dd = bk["strategy"]["max_drawdown"]
                break

    led = docs / "ledger.json"
    if led.exists():
        try:
            j = json.loads(led.read_text())
            entries = j.get("entries", [])
            if entries:
                tr = entries[-1]["equity"] - 1.0
                sub = f"{len(entries)} sessions · hypothetical backtest from {j.get('inception', '')}"
                if strat_dd is not None:
                    sub += f" · −{strat_dd*100:.0f}% max drawdown"
                headline.append({
                    "label": "Model Portfolio (hypothetical)",
                    "value": f"{tr*100:+.1f}%",
                    # Deliberately neutral: a hypothetical return is not a win to colour green.
                    "sub": sub,
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
                "sub": f"strategy vs buy & hold · OOS Sharpe {o['sharpe']:.2f}",
                "tone": "neutral",
            })

    exhibits = [{"title": t, "href": h, "desc": d, "present": (docs / h).exists()}
                for t, h, d in EXHIBITS]
    return {
        "header": {
            "generated": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        },
        "headline": headline,
        "exhibits": exhibits,
    }
