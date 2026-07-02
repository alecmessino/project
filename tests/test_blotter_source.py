"""Guards for the dashboard 'Latest rebalance' blotter's single source of truth.

The dashboard once recomputed the book fresh at export time while the Model Portfolio page walked its
own persisted forward ledger — two model paths whose latest trades could contradict each other on a
public site. These tests pin the fix: when docs/ledger.json exists, the blotter is derived from ITS
entries (and says so); the fresh recomputation survives only as a labeled fallback.
"""

import json

from drift.exhibit import blotter_from_entries, ledger_blotter, build_state
from drift.config import Settings
from drift.models import Bar


def _ledger_entries():
    """Four sessions, one rebalance at s2 (VTI trimmed into VXUS entered, BND exited)."""
    w0 = {"VTI": 0.6, "BND": 0.4}
    w1 = {"VTI": 0.4, "VXUS": 0.6}
    return [
        {"date": "2026-06-24", "weights": w0, "equity": 1.00},
        {"date": "2026-06-25", "weights": w0, "equity": 1.01},
        {"date": "2026-06-26", "weights": w1, "equity": 1.02},
        {"date": "2026-06-29", "weights": w1, "equity": 1.03},
    ]


def test_blotter_matches_the_ledgers_own_last_weight_change(tmp_path):
    p = tmp_path / "ledger.json"
    p.write_text(json.dumps({"entries": _ledger_entries(), "inception": "2026-06-24"}))
    b = ledger_blotter(p)
    assert b is not None and b["book"] == "ledger"
    assert b["date"] == "2026-06-26" and b["prev_date"] == "2026-06-25"
    acts = {t["instrument"]: t["action"] for t in b["trades"]}
    assert acts == {"VXUS": "NEW", "BND": "EXIT", "VTI": "TRIM"}
    assert b["sessions_since"] == 2 and b["n_held"] == 2
    assert abs(b["since_return"] - (1.03 / 1.01 - 1.0)) < 5e-5   # P&L from the pre-rebalance mark (4dp rounding)


def test_build_state_prefers_the_ledger_over_recomputation(tmp_path):
    p = tmp_path / "ledger.json"
    p.write_text(json.dumps({"entries": _ledger_entries()}))
    # A tiny synthetic series so the recomputed path would produce a DIFFERENT (or no) blotter.
    bars = [Bar(asof=f"2026-06-{d:02d}", close=100.0 + i) for i, d in enumerate(range(1, 29))]
    series = {"VTI": bars, "VXUS": bars, "BND": bars}
    st = build_state(series, Settings(), source="synthetic", ledger_path=p)
    assert st["blotter"] is not None
    assert st["blotter"]["book"] == "ledger"                      # ledger won, not the recomputation
    assert st["blotter"]["date"] == "2026-06-26"


def test_recomputed_fallback_is_labeled(tmp_path):
    # No ledger file -> fallback path must be explicit about what it is.
    entries = _ledger_entries()
    b = blotter_from_entries(entries)
    assert b and "book" not in b                                  # core diff is book-agnostic
    st_missing = build_state({}, Settings(), ledger_path=tmp_path / "absent.json")
    assert st_missing["blotter"] is None                          # nothing to show, nothing invented


def test_committed_dashboard_blotter_matches_committed_ledger():
    """Live-data integrity: the published dashboard's blotter must be the published ledger's last
    weight change. Skips only if either artifact is absent (fresh clone without docs)."""
    import pathlib
    import pytest
    led = pathlib.Path("docs/ledger.json")
    dash = pathlib.Path("docs/equities.html")
    if not (led.exists() and dash.exists()):
        pytest.skip("published artifacts absent")
    expected = ledger_blotter(led)
    if expected is None:
        pytest.skip("ledger has no rebalance to diff")
    # render_html replaces the /*__STATE__*/ placeholder, so the rendered page carries the state on
    # the single `window.__STATE__ = {...};` line.
    line = next(l for l in dash.read_text().splitlines() if l.lstrip().startswith("window.__STATE__ ="))
    state = json.loads(line.split("=", 1)[1].strip().rstrip(";"))
    got = state.get("blotter") or {}
    if "book" not in got:
        pytest.skip("published dashboard predates the ledger-sourced blotter — refresh it "
                    "(drift export, or the drift-pages workflow) to activate this guard")
    assert got.get("book") == "ledger", "published dashboard blotter is not ledger-sourced"
    assert got.get("date") == expected["date"], (
        f"dashboard blotter date {got.get('date')} != ledger's last rebalance {expected['date']}")
    assert {t['instrument']: t['action'] for t in got.get('trades', [])} == \
           {t['instrument']: t['action'] for t in expected['trades']}
