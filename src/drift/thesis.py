"""The thesis page state — equities-first narrative with live headline numbers.

Reads the already-generated tearsheet (for the Equities & ETFs and Crypto books)
and the forward ledger, so the figures quoted on the page stay current as the
daily Action regenerates them. Pure/IO-light; degrades gracefully when a source
file is missing.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

from .hub import _embedded_state


def _book(ts: dict, needle: str) -> Optional[dict]:
    for bk in ts.get("books", []):
        if needle.lower() in bk.get("name", "").lower():
            return bk
    return None


def _book_metrics(bk: dict) -> dict:
    s, b, o = bk["strategy"], bk["benchmark"], bk["oos"]["test"]
    return {
        "name": bk["name"],
        "span": f"{bk['span'][0][:4]}–{bk['span'][1][:4]}",
        "n_names": bk.get("n_names", 0),
        "strat_maxdd": s["max_drawdown"], "bench_maxdd": b["max_drawdown"],
        "strat_sharpe": s["sharpe"], "bench_sharpe": b["sharpe"],
        "strat_cagr": s["cagr"], "bench_cagr": b["cagr"],
        "oos_sharpe": o["sharpe"],
    }


def build_thesis(docs_dir: str | Path = "docs") -> dict:
    docs = Path(docs_dir)
    state: dict = {
        "header": {"generated": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())},
        "equities": None, "crypto": None, "ledger": None,
    }
    ts = _embedded_state(docs / "tearsheet.html")
    if ts:
        eq = _book(ts, "equit")
        cr = _book(ts, "crypto")
        if eq:
            state["equities"] = _book_metrics(eq)
        if cr:
            state["crypto"] = _book_metrics(cr)
    led = docs / "ledger.json"
    if led.exists():
        try:
            j = json.loads(led.read_text())
            e = j.get("entries", [])
            if e:
                state["ledger"] = {
                    "total_return": e[-1]["equity"] - 1.0,
                    "sessions": len(e),
                    "inception": j.get("inception", ""),
                    "universe": len(j.get("universe", [])),
                }
        except Exception:
            pass
    return state
