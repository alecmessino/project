"""Correctness guards for the Tax-Alpha decomposition (scripts/tax_alpha.py).

The script is the empirical backbone of the "Structural Alpha (tax)" claim: it isolates how much
after-tax CAGR the firm's tax machinery recovers on the SAME universe versus a tax-naive book. We
test the decomposition INVARIANTS on a tiny hand-built path (fast, deterministic) rather than the
40-year run:
  • the local FIFO lot walk reproduces drift.tax.after_tax_track (adversarial cross-check);
  • harvesting can only ever lower tax (managed after-tax >= naive after-tax on the same path);
  • the two engine levers (lot+hysteresis, harvesting) sum exactly to the Tax-Alpha total;
  • the structural book never loses to the naive concentrated one.
"""

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import tax_alpha as TA  # re-exec is skipped under pytest (see module top)
from drift.config import Settings
from drift.tax import after_tax_track, profile_for_state


def _toy_entries():
    """A 6-step, 2-name path with both gains and harvestable losses so the levers have material.
    Carries the per-entry shape the lot walk needs: weights, prices, realized_return, equity."""
    A = [100, 110, 121, 121, 133, 146]      # trends up -> realized gains
    B = [100, 90, 81, 89, 80, 88]           # choppy/down -> harvestable losses
    W = [{"A": 0.5, "B": 0.5}, {"A": 0.7, "B": 0.3}, {"A": 0.4, "B": 0.6},
         {"A": 0.7, "B": 0.3}, {"A": 0.4, "B": 0.6}, {"A": 0.6, "B": 0.4}]
    entries, eq, prev = [], 1.0, {"A": 100, "B": 100}
    for i, (a, b, w) in enumerate(zip(A, B, W)):
        wprev = W[i - 1] if i else {"A": 0.5, "B": 0.5}
        r = wprev["A"] * (a / prev["A"] - 1) + wprev["B"] * (b / prev["B"] - 1) if i else 0.0
        eq *= (1.0 + r)
        entries.append({"weights": w, "prices": {"A": a, "B": b},
                        "realized_return": r, "equity": round(eq, 8)})
        prev = {"A": a, "B": b}
    return entries


def test_local_lot_walk_matches_library_after_tax_track():
    e = _toy_entries()
    s = Settings.load("config/drift.yaml")
    tax = profile_for_state(s.tax, "CA")
    lib = after_tax_track(e, tax, TA.BPY)
    mine, *_ = TA.lot_after_tax(e, lib.rate_st, lib.rate_lt, tax.lt_holding_bars, harvest=True)
    # library rounds its curve to 6 dp each step; allow that rounding, catch any real divergence.
    assert abs(mine - lib.after_tax_return) < 1e-5


def test_harvesting_never_raises_tax_on_the_same_path():
    e = _toy_entries()
    naive, t_naive, *_ = TA.lot_after_tax(e, 0.45, 0.25, 2, harvest=False)
    mgd, t_mgd, *_ = TA.lot_after_tax(e, 0.45, 0.25, 2, harvest=True)
    assert mgd >= naive - 1e-12          # netting losses can only help the after-tax outcome
    assert t_mgd <= t_naive + 1e-12      # ... by paying no more tax


def test_decomposition_is_additive_and_non_negative_across_states():
    fast = _toy_entries()
    # a lower-turnover "structural" variant of the same names (fewer, gentler rebalances)
    hybrid = _toy_entries()
    for i, en in enumerate(hybrid):
        en["weights"] = {"A": 0.5, "B": 0.5} if i % 2 else {"A": 0.55, "B": 0.45}
    s = Settings.load("config/drift.yaml")
    for st in ("—", "IL", "CA"):
        tax = profile_for_state(s.tax, st)
        d = TA.decompose(fast, hybrid, tax, years=1.0)
        assert abs((d["turnover_lever"] + d["harvest_lever"]) - d["total"]) < 1e-12
        assert d["harvest_lever"] >= -1e-12
        assert d["total"] >= -1e-12


def test_cagr_helper_is_sane():
    assert abs(TA._cagr(0.0, 10) - 0.0) < 1e-12
    assert abs(TA._cagr(1.0, 1) - 1.0) < 1e-12          # +100% over 1y
    assert abs((1 + TA._cagr(3.0, 4)) ** 4 - 4.0) < 1e-9  # quadruples over 4y
