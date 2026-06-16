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
     "The trend-following thesis, the research, the equities results — and the name."),
    ("Live forward ledger", "ledger.html",
     "Append-only, out-of-sample paper track record — marked and committed daily."),
    ("Long-history tearsheet", "tearsheet.html",
     "Decades of daily history: strategy vs buy-and-hold, fit in-sample and reported out-of-sample."),
    ("Crypto dashboard", "drift.html",
     "Live trend signals and per-name backtests across crypto majors (Coinbase)."),
    ("Equities dashboard", "equities.html",
     "Live trend signals and per-name backtests across equities/ETFs (Yahoo)."),
    ("Crypto case studies", "case_studies.html",
     "Five backtests: time-series, cross-sectional, lookback & cost sensitivity, and a control."),
    ("Equities case studies", "equities_case_studies.html",
     "The same five studies on equities and ETFs."),
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

    led = docs / "ledger.json"
    if led.exists():
        try:
            j = json.loads(led.read_text())
            entries = j.get("entries", [])
            if entries:
                tr = entries[-1]["equity"] - 1.0
                headline.append({
                    "label": "Forward ledger",
                    "value": f"{tr*100:+.1f}%",
                    "sub": f"{len(entries)} sessions · since {j.get('inception', '')}",
                    "tone": "pos" if tr > 0 else "neg" if tr < 0 else "neutral",
                })
        except Exception:
            pass

    ts = _embedded_state(docs / "tearsheet.html")
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
