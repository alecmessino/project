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
from .cross_section import cross_backtest, rank_snapshot
from .models import Bar
from .triggers import evaluate, to_signal

TEMPLATE = Path(__file__).with_name("web") / "index.html"
REPORT_TEMPLATE = Path(__file__).with_name("web") / "report.html"
TEARSHEET_TEMPLATE = Path(__file__).with_name("web") / "tearsheet.html"


def _spark(curve: Sequence[float], n: int = 90) -> list[float]:
    """Downsample an equity curve to at most `n` points for a sparkline."""
    if len(curve) <= n:
        return list(curve)
    step = len(curve) / n
    return [curve[min(len(curve) - 1, int(i * step))] for i in range(n)]


def build_state(series: dict[str, list[Bar]], settings: Settings, source: str = "—") -> dict:
    """Full dashboard state for a universe of instrument -> bar-series."""
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
    n_bars = max((len(b) for b in series.values()), default=0)

    return {
        "header": {
            "source": source,
            "n_instruments": len(series),
            "n_bars": n_bars,
            "n_flagged": sum(1 for i in instruments if i["flagged"]),
            "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
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
                source: str = "—") -> Path:
    """Build state and write a self-contained exhibit HTML to `out`."""
    state = build_state(series, settings, source=source)
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
