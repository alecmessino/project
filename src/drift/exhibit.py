"""Build the dashboard/exhibit state and render the static page.

`build_state` turns a universe of price series into a single JSON-able dict — the
time-series signal per instrument, the cross-sectional ranking, and both backtests
with (downsampled) equity curves. It is pure and side-effect-free, so the live
server (`web/server.py`) and the static exporter share one code path and one
render template (`web/index.html`).
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Sequence

from .backtest import backtest
from .config import Settings
from .cross_section import cross_backtest, cross_book_entries, rank_snapshot
from .models import Bar
from .triggers import evaluate, to_signal

TEMPLATE = Path(__file__).with_name("web") / "index.html"
REPORT_TEMPLATE = Path(__file__).with_name("web") / "report.html"
TEARSHEET_TEMPLATE = Path(__file__).with_name("web") / "tearsheet.html"
LEDGER_TEMPLATE = Path(__file__).with_name("web") / "ledger.html"
HUB_TEMPLATE = Path(__file__).with_name("web") / "hub.html"
THESIS_TEMPLATE = Path(__file__).with_name("web") / "thesis.html"
TAXLAB_TEMPLATE = Path(__file__).with_name("web") / "taxlab.html"
LEAKAGE_TEMPLATE = Path(__file__).with_name("web") / "leakage.html"
STATEMAP_TEMPLATE = Path(__file__).with_name("web") / "statemap.html"


def _spark(curve: Sequence[float], n: int = 90) -> list[float]:
    """Downsample an equity curve to at most `n` points for a sparkline."""
    if len(curve) <= n:
        return list(curve)
    step = len(curve) / n
    return [curve[min(len(curve) - 1, int(i * step))] for i in range(n)]


def latest_rebalance_blotter(series: dict[str, list[Bar]], settings: Settings) -> dict | None:
    """Fallback blotter: recompute the book fresh and diff its last weight change. Only used when the
    forward ledger isn't available — the recomputation's window/boundaries can differ from the
    ledger's persisted path, so `ledger_blotter` is ALWAYS preferred (single source of truth)."""
    try:
        entries = cross_book_entries(series, settings)
    except Exception:
        return None
    b = blotter_from_entries(entries)
    if b:
        b["book"] = "recomputed"
    return b


def ledger_blotter(ledger_path: str | Path) -> dict | None:
    """The dashboard blotter derived from the SAME entries the Model Portfolio ledger publishes
    (docs/ledger.json) — so 'the trades the book just made' can never contradict the ledger page."""
    try:
        j = json.loads(Path(ledger_path).read_text())
        entries = j.get("entries", [])
    except Exception:
        return None
    b = blotter_from_entries(entries)
    if b:
        b["book"] = "ledger"
    return b


def blotter_from_entries(entries: list[dict]) -> dict | None:
    """The most recent rebalance as a trade blotter: what the book actually did at its last
    turn — names entered, exited, and weights raised/trimmed — plus the P&L since.

    Built by diffing a per-session weight book (entries need date/weights/equity) at its last change,
    so it answers the dashboard's missing question ("what changed, and what to do now") straight from
    the book. Pure and self-contained; returns None when there isn't a prior book to diff against.
    """
    if len(entries) < 2:
        return None
    cur = entries[-1]["weights"]
    # Walk back to the last session whose weights differ from the one before it — that's the rebalance.
    reb = None
    for i in range(len(entries) - 1, 0, -1):
        if entries[i]["weights"] != entries[i - 1]["weights"]:
            reb = i
            break
    if reb is None:                                   # weights never changed (degenerate)
        return None
    before = entries[reb - 1]["weights"]
    after = entries[reb]["weights"]
    eps = 5e-4
    trades: list[dict] = []
    for inst in sorted(set(before) | set(after)):
        p, c = before.get(inst, 0.0), after.get(inst, 0.0)
        if p <= 0 < c:
            action = "NEW"
        elif c <= 0 < p:
            action = "EXIT"
        elif c - p > eps:
            action = "ADD"
        elif p - c > eps:
            action = "TRIM"
        else:
            continue                                  # held, immaterial change
        trades.append({"instrument": inst, "action": action,
                       "prev_weight": round(p, 4), "weight": round(c, 4), "delta": round(c - p, 4)})
    order = {"NEW": 0, "ADD": 1, "TRIM": 2, "EXIT": 3}
    trades.sort(key=lambda t: (order[t["action"]], -t["weight"], -abs(t["delta"])))
    eq_now, eq_at_reb = entries[-1]["equity"], entries[reb - 1]["equity"]
    since = (eq_now / eq_at_reb - 1.0) if eq_at_reb else 0.0
    return {
        "date": entries[reb]["date"],
        "prev_date": entries[reb - 1]["date"],
        "since_return": round(since, 4),
        "sessions_since": len(entries) - reb,
        "n_held": sum(1 for w in cur.values() if w > 0),
        "trades": trades,
    }


def build_state(series: dict[str, list[Bar]], settings: Settings, source: str = "—",
                ledger_path: str | Path | None = None) -> dict:
    """Full dashboard state for a universe of instrument -> bar-series.

    `ledger_path`: when the forward ledger exists, the 'Latest rebalance' blotter is derived from ITS
    entries (single source of truth with the Model Portfolio page) instead of a fresh recomputation."""
    s = settings.signal
    instruments: list[dict] = []
    for inst, bars in sorted(series.items()):
        ev = evaluate(inst, bars, settings)
        sigobj = to_signal(ev, settings) if ev is not None else None
        bt = backtest(inst, bars, settings)
        instruments.append({
            "instrument": inst,
            "asof": bars[-1].asof if bars else "",
            "last_close": bars[-1].close if bars else None,
            "score": round(ev.score, 3) if ev else None,
            "side": ev.side.value.upper() if ev else "FLAT",
            "breakout": ev.breakout if ev else 0,
            "weight": round(ev.target_weight, 3) if ev else 0.0,
            "ann_vol": round(ev.ann_vol, 4) if ev else None,
            "flagged": sigobj is not None,
            "strong": bool(sigobj and sigobj.strong),
            "reasons": sigobj.reasons if sigobj else [],
            "backtest": {
                "net_return": round(bt.net_return, 4),
                "gross_return": round(bt.gross_return, 4),
                "sharpe": round(bt.sharpe, 2),
                "max_drawdown": round(bt.max_drawdown, 4),
                "n_trades": bt.n_trades,
                "equity": _spark(bt.equity_curve),
            },
        })

    rankings = [vars(r) for r in rank_snapshot(series, settings)]
    xbt = cross_backtest(series, settings)
    blotter = (ledger_blotter(ledger_path) if ledger_path and Path(ledger_path).exists() else None) \
        or latest_rebalance_blotter(series, settings)
    n_bars = max((len(b) for b in series.values()), default=0)

    return {
        "blotter": blotter,
        "header": {
            "source": source,
            "n_instruments": len(series),
            "n_bars": n_bars,
            "n_flagged": sum(1 for i in instruments if i["flagged"]),
            "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
            # Last bar across the universe — dates the DATA, not just the render.
            "data_through": max((b[-1].asof for b in series.values() if b), default=""),
            "model": f"lookback {s.lookback} · vol {s.vol_window} · channel {s.breakout_channel}",
        },
        "instruments": instruments,
        "rankings": rankings,
        "cross_backtest": {
            "net_return": round(xbt.net_return, 4),
            "gross_return": round(xbt.gross_return, 4),
            "cost_drag": round(xbt.cost_drag, 4),
            "sharpe": round(xbt.sharpe, 2),
            "max_drawdown": round(xbt.max_drawdown, 4),
            "turnover": round(xbt.turnover, 1),
            "avg_names_held": round(xbt.avg_names_held, 1),
            "equity": _spark(xbt.equity_curve),
        },
    }


def render_html(state: dict) -> str:
    """Static, self-contained HTML: the template with the state embedded inline.

    The template fetches /api/state when served live; for export we replace the
    placeholder with a literal so the page renders with no server.
    """
    template = TEMPLATE.read_text()
    payload = json.dumps(state)
    return template.replace("/*__STATE__*/null/*__END__*/", payload)


def export_html(series: dict[str, list[Bar]], settings: Settings, out: str | Path,
                source: str = "—", ledger_path: str | Path | None = None) -> Path:
    """Build state and write a self-contained exhibit HTML to `out`."""
    state = build_state(series, settings, source=source, ledger_path=ledger_path)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_html(state))
    return out


def render_report(report: dict) -> str:
    """Static, self-contained case-studies HTML with the report embedded inline."""
    template = REPORT_TEMPLATE.read_text()
    return template.replace("/*__STATE__*/null/*__END__*/", json.dumps(report))


def export_report(report: dict, out: str | Path) -> Path:
    """Write a self-contained case-studies report HTML to `out`."""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_report(report))
    return out


def render_tearsheet(report: dict) -> str:
    """Static, self-contained long-history tearsheet HTML with state embedded."""
    template = TEARSHEET_TEMPLATE.read_text()
    return template.replace("/*__STATE__*/null/*__END__*/", json.dumps(report))


def export_tearsheet(report: dict, out: str | Path) -> Path:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_tearsheet(report))
    return out


def render_ledger(state: dict) -> str:
    """Static, self-contained forward-ledger HTML with state embedded."""
    template = LEDGER_TEMPLATE.read_text()
    return template.replace("/*__STATE__*/null/*__END__*/", json.dumps(state))


def export_ledger(state: dict, out: str | Path) -> Path:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_ledger(state))
    return out


def render_hub(state: dict) -> str:
    """Static, self-contained markets-only landing hub with state embedded."""
    template = HUB_TEMPLATE.read_text()
    return template.replace("/*__STATE__*/null/*__END__*/", json.dumps(state))


def export_hub(state: dict, out: str | Path) -> Path:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_hub(state))
    return out


def render_thesis(state: dict) -> str:
    """Static, self-contained thesis page with state embedded."""
    template = THESIS_TEMPLATE.read_text()
    return template.replace("/*__STATE__*/null/*__END__*/", json.dumps(state))


def export_thesis(state: dict, out: str | Path) -> Path:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_thesis(state))
    return out


def render_taxlab(state: dict) -> str:
    """Static, self-contained Tax Lab page with state embedded."""
    template = TAXLAB_TEMPLATE.read_text()
    return template.replace("/*__STATE__*/null/*__END__*/", json.dumps(state))


def export_taxlab(state: dict, out: str | Path) -> Path:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_taxlab(state))
    return out


def render_leakage(state: dict) -> str:
    """Static, self-contained Tax-Leakage Diagnostic (Before/After) with state embedded."""
    template = LEAKAGE_TEMPLATE.read_text()
    return template.replace("/*__STATE__*/null/*__END__*/", json.dumps(state))


def export_leakage(state: dict, out: str | Path) -> Path:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_leakage(state))
    return out


def render_statemap(state: dict) -> str:
    """Static, self-contained multi-dimension State Tax Map with state embedded."""
    template = STATEMAP_TEMPLATE.read_text()
    return template.replace("/*__STATE__*/null/*__END__*/", json.dumps(state))


def export_statemap(state: dict, out: str | Path) -> Path:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_statemap(state))
    return out
