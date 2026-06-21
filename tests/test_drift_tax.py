"""Lot-aware after-tax engine, state profiles, and the tax-aware no-trade band."""

from drift.config import CrossSectionSettings, TaxSettings
from drift.cross_section import _tax_aware_weights
from drift.tax import STATE_RATES, after_tax_track, profile_for_state


def _entries(weights_seq, prices_seq, ret=0.01):
    # Build minimal ledger-style entries with per-name prices for the lot engine.
    eq = 1.0
    out = []
    for i, (w, px) in enumerate(zip(weights_seq, prices_seq)):
        eq = round(eq * (1.0 + ret), 6)
        out.append({"date": f"2020-01-{i+1:02d}", "weights": w, "prices": px,
                    "realized_return": ret, "equity": eq, "seed": True})
    return out


def test_after_tax_needs_prices():
    no_px = [{"date": "2020-01-01", "weights": {"A": 1.0}, "realized_return": 0.0, "equity": 1.0}]
    assert after_tax_track(no_px, TaxSettings()) is None


def test_short_term_gains_taxed_harder_than_long_term():
    # Same book that sells an appreciated lot — once after <1y (short) and once after >1y.
    px_up = [{"A": 1.0 + 0.001 * i, "B": 1.0} for i in range(300)]
    # Hold A then rotate fully to B: a quick rotation (idx 5) vs a slow one (idx 270).
    quick = [{"A": 1.0}] * 5 + [{"B": 1.0}] * 5
    slow = [{"A": 1.0}] * 270 + [{"B": 1.0}] * 5
    tax = TaxSettings(enabled=True)
    at_quick = after_tax_track(_entries(quick, px_up[:10], ret=0.0), tax)
    at_slow = after_tax_track(_entries(slow, px_up[:275], ret=0.0), tax)
    # The quick rotation realizes short-term gains; the slow one long-term.
    assert at_quick.short_term_share > at_slow.short_term_share


def test_state_profile_raises_effective_rates():
    base = TaxSettings()
    ca = profile_for_state(base, "CA")
    assert ca.state == "CA" and ca.state_lt == STATE_RATES["CA"][0]
    assert ca.rate_lt > base.rate_lt and ca.rate_st > base.rate_st   # CA adds state tax
    tx = profile_for_state(base, "TX")
    assert tx.rate_lt == base.rate_lt                                # no-income-tax state


def _cs(**kw):
    base = dict(gross_exposure=1.0, tax_aware=True, no_trade_band=0.05)
    base.update(kw)
    return CrossSectionSettings(**base)


def test_no_trade_band_holds_small_moves_and_keeps_gross():
    prev = {"A": 0.5, "B": 0.5}
    target = {"A": 0.52, "B": 0.48}              # both within the 0.05 band
    out = _tax_aware_weights(target, prev, _cs())
    assert out == prev                            # no trade at all
    # A large move is taken, and a new name entering is taken; gross stays ~1.
    out2 = _tax_aware_weights({"A": 0.7, "B": 0.0, "C": 0.3}, prev, _cs())
    assert abs(sum(out2.values()) - 1.0) < 1e-9
    assert out2["B"] == 0.0                        # exited in full


def test_band_is_noop_when_disabled():
    target = {"A": 0.52, "B": 0.48}
    prev = {"A": 0.5, "B": 0.5}
    assert _tax_aware_weights(target, prev, _cs(tax_aware=False)) == target
