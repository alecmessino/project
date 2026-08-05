"""Build the dashboard/exhibit state and render the static page.

`build_state` turns a universe of price series into a single JSON-able dict, the
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

from .config import Settings
from .cross_section import cross_book_entries
from .models import Bar

TEMPLATE = Path(__file__).with_name("web") / "index.html"
REPORT_TEMPLATE = Path(__file__).with_name("web") / "report.html"
TEARSHEET_TEMPLATE = Path(__file__).with_name("web") / "tearsheet.html"
LEDGER_TEMPLATE = Path(__file__).with_name("web") / "ledger.html"
HUB_TEMPLATE = Path(__file__).with_name("web") / "hub.html"
THESIS_TEMPLATE = Path(__file__).with_name("web") / "thesis.html"
TAXLAB_TEMPLATE = Path(__file__).with_name("web") / "taxlab.html"
LEAKAGE_TEMPLATE = Path(__file__).with_name("web") / "leakage.html"
STATEMAP_TEMPLATE = Path(__file__).with_name("web") / "statemap.html"
CONCENTRATION_TEMPLATE = Path(__file__).with_name("web") / "concentration.html"


def _spark(curve: Sequence[float], n: int = 90) -> list[float]:
    """Downsample an equity curve to at most `n` points for a sparkline."""
    if len(curve) <= n:
        return list(curve)
    step = len(curve) / n
    return [curve[min(len(curve) - 1, int(i * step))] for i in range(n)]


def latest_rebalance_blotter(series: dict[str, list[Bar]], settings: Settings) -> dict | None:
    """Fallback blotter: recompute the book fresh and diff its last weight change. Only used when the
    forward ledger isn't available, the recomputation's window/boundaries can differ from the
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
    (docs/ledger.json), so 'the trades the book just made' can never contradict the ledger page."""
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
    turn, names entered, exited, and weights raised/trimmed, plus the P&L since.

    Built by diffing a per-session weight book (entries need date/weights/equity) at its last change,
    so it answers the dashboard's missing question ("what changed, and what to do now") straight from
    the book. Pure and self-contained; returns None when there isn't a prior book to diff against.
    """
    if len(entries) < 2:
        return None
    cur = entries[-1]["weights"]
    # Walk back to the last session whose weights differ from the one before it, that's the rebalance.
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


def build_dashboard_state(ledger_path: str | Path, settings: Settings, tax=None) -> dict | None:
    """The operational-dashboard state (`equities.html`), a projection of the ONE canonical portfolio
    object (`drift.portfolio.build_portfolio_state`) built from the Model Portfolio ledger.

    Single source of truth: the dashboard's holdings, signal strengths, statuses, the last rebalance,
    and the performance chart all derive from `docs/ledger.json`, so they can never contradict the
    ledger page (same universe, same date, same weights). Returns None when the ledger is absent/empty.
    """
    from .portfolio import build_portfolio_state, dashboard_projection
    try:
        ledger = json.loads(Path(ledger_path).read_text())
    except Exception:
        return None
    if not ledger.get("entries"):
        return None
    return dashboard_projection(build_portfolio_state(ledger, settings, tax))


def _embed(template: str, state: dict) -> str:
    """Embed the state blob AND resolve every build-time token.

    Why this exists: for a long time only `render_hub` resolved <!--FIRM_ANCHOR-->, so the nightly
    `drift statemap|taxlab|leakage` runs shipped docs/ pages containing the raw HTML comment where
    the firm identity strip belongs — the band naming the practice and its custodian. Running
    scripts/sync_docs.py repaired it, then the next nightly regressed it, so the live site lost that
    strip on those pages between builds. Every render path now goes through one function; adding a
    new token means editing one place, and test_no_build_token_ever_ships catches the rest.

    It happened again on 2026-08-05, the same way. `_embed` was introduced but four render paths
    were left hand-rolling the state replace and never picked up the token substitution:
    render_html (equities), render_report (case studies), render_tearsheet and render_ledger. The
    nightly exhibits job regenerated all four straight onto master, shipping the raw comment to the
    live site where the firm identity band belongs, and because that job commits directly it never
    faced PR CI. All four now go through here. If you add a fifth exhibit, route it through _embed
    rather than calling .replace yourself; that is the entire lesson of this function existing.
    """
    from .site import firm_anchor_html
    html = template.replace("/*__STATE__*/null/*__END__*/", json.dumps(state))
    return html.replace("<!--FIRM_ANCHOR-->", firm_anchor_html())


def render_html(state: dict) -> str:
    """Static, self-contained HTML: the template with the state embedded inline.

    The template fetches /api/state when served live; for export we replace the
    placeholder with a literal so the page renders with no server.
    """
    return _embed(TEMPLATE.read_text(), state)


def export_html(ledger_path: str | Path, settings: Settings, out: str | Path, tax=None) -> Path:
    """Build the operational dashboard state from the ledger and write a self-contained HTML to `out`."""
    state = build_dashboard_state(ledger_path, settings, tax)
    if state is None:
        raise ValueError(f"no ledger entries at {ledger_path}, build the Model Portfolio ledger first")
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_html(state))
    return out


def render_report(report: dict) -> str:
    """Static, self-contained case-studies HTML with the report embedded inline."""
    return _embed(REPORT_TEMPLATE.read_text(), report)


def export_report(report: dict, out: str | Path) -> Path:
    """Write a self-contained case-studies report HTML to `out`."""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_report(report))
    return out


def render_tearsheet(report: dict) -> str:
    """Static, self-contained long-history tearsheet HTML with state embedded."""
    return _embed(TEARSHEET_TEMPLATE.read_text(), report)


def export_tearsheet(report: dict, out: str | Path) -> Path:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_tearsheet(report))
    return out


def render_ledger(state: dict) -> str:
    """Static, self-contained forward-ledger HTML with state embedded."""
    return _embed(LEDGER_TEMPLATE.read_text(), state)


def export_ledger(state: dict, out: str | Path) -> Path:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_ledger(state))
    return out


def render_hub(state: dict) -> str:
    """Static, self-contained markets-only landing hub with state embedded.

    The firm-anchor coordinates band is injected here as well, not only in
    scripts/sync_docs.py, so every build path (the `drift hub` CLI, the nightly
    pages job, and any test that renders the hub) resolves the <!--FIRM_ANCHOR-->
    token instead of shipping it raw.
    """
    return _embed(HUB_TEMPLATE.read_text(), state)


def export_hub(state: dict, out: str | Path) -> Path:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_hub(state))
    return out


def render_thesis(state: dict) -> str:
    """Static, self-contained thesis page with state embedded."""
    return _embed(THESIS_TEMPLATE.read_text(), state)


def export_thesis(state: dict, out: str | Path) -> Path:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_thesis(state))
    return out


def render_taxlab(state: dict) -> str:
    """Static, self-contained Tax Lab page with state embedded."""
    return _embed(TAXLAB_TEMPLATE.read_text(), state)


def export_taxlab(state: dict, out: str | Path) -> Path:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_taxlab(state))
    return out



def render_leakage(state: dict) -> str:
    """Static, self-contained Tax-Leakage Diagnostic (Before/After) with state embedded."""
    return _embed(LEAKAGE_TEMPLATE.read_text(), state)


def export_leakage(state: dict, out: str | Path) -> Path:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_leakage(state))
    return out


def render_statemap(state: dict) -> str:
    """Static, self-contained multi-dimension State Tax Map with state embedded."""
    return _embed(STATEMAP_TEMPLATE.read_text(), state)


def export_statemap(state: dict, out: str | Path) -> Path:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_statemap(state))
    return out


def render_concentration(state: dict) -> str:
    """Static, self-contained "Single asset risk" heatmap with the strategy dataset embedded."""
    return _embed(CONCENTRATION_TEMPLATE.read_text(), state)


def export_concentration(state: dict, out: str | Path) -> Path:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_concentration(state))
    return out
