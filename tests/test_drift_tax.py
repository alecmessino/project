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


def test_gain_profile_decomposes_and_is_rate_independent():
    from drift.tax import gain_profile
    px = [{"A": 1.0 + 0.002 * i, "B": 1.0} for i in range(40)]
    w = [{"A": 1.0}] * 6 + [{"B": 1.0}] * 6      # sell appreciated A early -> short-term gain
    eq = 1.0
    ents = []
    for i, (wi, pxi) in enumerate(zip(w, px)):
        eq = round(eq * 1.0, 6)
        ents.append({"date": f"2020-01-{i+1:02d}", "weights": wi, "prices": pxi,
                     "realized_return": 0.0, "equity": eq, "seed": True})
    gp = gain_profile(ents, lt_holding_bars=252)
    assert gp is not None
    assert gp.st_realized > 0 and gp.lt_realized == 0      # quick sell -> all short-term
    assert 0.0 <= gp.short_term_share <= 1.0


def test_build_taxlab_embeds_profile_and_states(tmp_path):
    import json
    from drift import ledger as L
    from drift.config import Settings
    from drift.taxlab import build_taxlab
    from drift.feed.synthetic import SyntheticFeed
    from dataclasses import replace
    from datetime import date, timedelta
    s = Settings(signal={"lookback": 20, "vol_window": 10, "breakout_channel": 15})
    start = date(2020, 1, 1)
    series = {}
    for i, d in enumerate((0.5, -0.3, 0.2, 0.4)):
        bars = SyntheticFeed(instruments=(f"S{i}",), n_bars=300, regimes=[(300, d)], seed=5 + i).series(f"S{i}")
        series[f"S{i}"] = [replace(b, asof=(start + timedelta(days=k)).isoformat()) for k, b in enumerate(bars)]
    led = L.seed_ledger(series, s, sessions=120)
    (tmp_path / "ledger.json").write_text(json.dumps(led))
    st = build_taxlab(tmp_path)
    assert st["profile"] and "st_realized" in st["profile"]
    assert "CA" in st["states"] and st["brackets"]
    json.dumps(st)                                          # must be embeddable


def _cs_slow(**kw):
    base = dict(slow_sleeve_mode=True, gross_exposure=1.0,
                lt_protection_window_bars=30, catastrophic_quantile=0.10)
    base.update(kw)
    return CrossSectionSettings(**base)


def test_lot_protection_delays_near_lt_sale():
    from drift.cross_section import _lot_protected_weights
    cs = _cs_slow()
    names = list("ABCDEFGHIJ")
    scores = {n: float(10 - i) for i, n in enumerate(names)}   # A best (rank 0) .. J worst
    prev = {"A": 0.5, "B": 0.5}
    target = {"A": 1.0, "B": 0.0}                              # ranking liquidates B
    # B (rank 1, not catastrophic) held 240 bars -> within 30 of the 252 LT mark -> frozen.
    out = _lot_protected_weights(target, prev, scores, {"A": 300, "B": 240}, cs, lt_bars=252)
    assert out["B"] == 0.5                                     # sale delayed
    assert abs(sum(out.values()) - 1.0) < 1e-9                # book stays fully invested


def test_lot_protection_sells_catastrophic_breakdown():
    from drift.cross_section import _lot_protected_weights
    cs = _cs_slow()
    names = ["A", "C", "D", "E", "F", "G", "H", "I", "J", "B"]  # B is now the worst (rank 9/10)
    scores = {n: float(10 - i) for i, n in enumerate(names)}
    prev = {"A": 0.5, "B": 0.5}
    target = {"A": 1.0, "B": 0.0}
    # Even within the LT cushion, a bottom-10% breakdown is sold rather than nursed.
    out = _lot_protected_weights(target, prev, scores, {"A": 300, "B": 240}, cs, lt_bars=252)
    assert out.get("B", 0.0) == 0.0


def test_lot_protection_noop_when_not_near_lt():
    from drift.cross_section import _lot_protected_weights
    cs = _cs_slow()
    names = list("ABCDEFGHIJ")
    scores = {n: float(10 - i) for i, n in enumerate(names)}
    prev = {"A": 0.5, "B": 0.5}
    target = {"A": 1.0, "B": 0.0}
    # B held only 100 bars -> nowhere near the LT threshold -> the sale proceeds untouched.
    out = _lot_protected_weights(target, prev, scores, {"A": 300, "B": 100}, cs, lt_bars=252)
    assert out == target


def test_lot_protection_is_noop_when_slow_mode_off():
    from drift.cross_section import _lot_protected_weights
    cs = CrossSectionSettings(slow_sleeve_mode=False, gross_exposure=1.0)
    target = {"A": 1.0, "B": 0.0}
    out = _lot_protected_weights(target, {"A": 0.5, "B": 0.5},
                                 {"A": 3.0, "B": 1.0}, {"B": 240}, cs, lt_bars=252)
    assert out == target


def test_slow_sleeve_config_defaults():
    cs = CrossSectionSettings()
    assert cs.slow_sleeve_mode is False
    assert cs.buy_quantile == 0.40 and cs.hold_quantile == 0.60
    assert cs.slow_lookback == 252
    assert cs.lt_protection_window_bars == 30 and cs.catastrophic_quantile == 0.10


def test_slow_yaml_loads_the_sleeve_preset():
    from pathlib import Path
    from drift.config import Settings
    root = Path(__file__).resolve().parents[1]
    s = Settings.load(root / "config" / "slow.yaml")
    cs = s.cross_section
    assert cs.slow_sleeve_mode is True
    assert cs.buy_quantile == 0.40 and cs.hold_quantile == 0.60
    assert cs.slow_lookback == 252 and cs.tax_aware is True


def test_location_alpha_peaks_at_equal_balance_and_zeroes_at_extremes():
    from drift.taxlab import location_alpha
    mdr, pdr = 0.08, 0.004                       # momentum vs passive annual drag rates
    equal = location_alpha(1_000_000, 1_000_000, mdr, pdr)
    skew = location_alpha(1_900_000, 100_000, mdr, pdr)
    # Nothing to shelter / nothing misplaced -> no location alpha at the extremes.
    assert location_alpha(0, 1_000_000, mdr, pdr)["annual_dollars"] == 0.0
    assert location_alpha(1_000_000, 0, mdr, pdr)["annual_dollars"] == 0.0
    # Overlap (A·T/(A+T)) is maximized at an equal split.
    assert equal["annual_dollars"] > skew["annual_dollars"]
    # (1e6·1e6/2e6)·(0.08−0.004) = 5e5·0.076 = 38_000.
    assert abs(equal["annual_dollars"] - 38_000) < 1e-6
    assert abs(equal["annual_rate"] - 38_000 / 2_000_000) < 1e-9


def test_location_alpha_never_negative_when_passive_cheaper():
    from drift.taxlab import location_alpha
    # Even if a degenerate input flips the spread, alpha is floored at zero (no penalty
    # for locating — the optimizer only ever helps or no-ops).
    assert location_alpha(1_000_000, 1_000_000, 0.002, 0.05)["annual_dollars"] == 0.0


def test_breakeven_alpha_rises_with_turnover_and_rate():
    from drift.taxlab import breakeven_alpha
    assert breakeven_alpha(0.0, 0.5, 0.03) == 0.0
    lo = breakeven_alpha(3.0, 0.408, 0.03)          # federal-only top ST rate
    hi = breakeven_alpha(3.0, 0.541, 0.03)          # + CA state -> steeper line
    assert hi > lo > 0
    assert breakeven_alpha(5.0, 0.408, 0.03) > lo   # more turnover -> higher breakeven
    assert abs(breakeven_alpha(3.0, 0.5, 0.03) - 0.045) < 1e-12


def test_build_taxlab_calibrates_gain_per_turn(tmp_path):
    import json
    from drift import ledger as L
    from drift.config import Settings
    from drift.taxlab import build_taxlab
    from drift.feed.synthetic import SyntheticFeed
    from dataclasses import replace
    from datetime import date, timedelta
    s = Settings(signal={"lookback": 20, "vol_window": 10, "breakout_channel": 15})
    start = date(2020, 1, 1)
    series = {}
    for i, d in enumerate((0.5, -0.3, 0.2, 0.4)):
        bars = SyntheticFeed(instruments=(f"S{i}",), n_bars=300, regimes=[(300, d)], seed=5 + i).series(f"S{i}")
        series[f"S{i}"] = [replace(b, asof=(start + timedelta(days=k)).isoformat()) for k, b in enumerate(bars)]
    led = L.seed_ledger(series, s, sessions=120)
    (tmp_path / "ledger.json").write_text(json.dumps(led))
    st = build_taxlab(tmp_path)
    assert st["header"]["gain_per_turn"] > 0          # calibrated from the live book


def test_build_taxlab_embeds_assumptions(tmp_path):
    import json
    from drift import ledger as L
    from drift.config import Settings
    from drift.taxlab import build_taxlab
    from drift.feed.synthetic import SyntheticFeed
    from dataclasses import replace
    from datetime import date, timedelta
    s = Settings(signal={"lookback": 20, "vol_window": 10, "breakout_channel": 15})
    start = date(2020, 1, 1)
    series = {}
    for i, d in enumerate((0.5, -0.3, 0.2, 0.4)):
        bars = SyntheticFeed(instruments=(f"S{i}",), n_bars=300, regimes=[(300, d)], seed=5 + i).series(f"S{i}")
        series[f"S{i}"] = [replace(b, asof=(start + timedelta(days=k)).isoformat()) for k, b in enumerate(bars)]
    led = L.seed_ledger(series, s, sessions=120)
    (tmp_path / "ledger.json").write_text(json.dumps(led))
    st = build_taxlab(tmp_path)
    a = st["assumptions"]
    assert a["passive_div_yield"] > 0 and a["horizon_years"] > 0
    assert a["default_taxable"] > 0 and a["default_advantaged"] > 0 and a["wealth_max"] >= a["default_taxable"]
    json.dumps(st)                                          # still fully embeddable


def test_nyc_overlay_stacks_local_tax_on_new_york():
    from drift.tax import STATE_RATES, profile_for_state
    from drift.config import TaxSettings
    assert "NYC" in STATE_RATES
    ny_lt, ny_st = STATE_RATES["NY"]
    nyc_lt, nyc_st = STATE_RATES["NYC"]
    assert nyc_lt > ny_lt and nyc_st > ny_st            # ~3.88% local stacks on NY's 10.9%
    assert abs(nyc_lt - 0.1478) < 1e-6                  # combined 14.78% top marginal
    base = TaxSettings()
    pny, pnyc = profile_for_state(base, "NY"), profile_for_state(base, "NYC")
    assert pnyc.rate_lt > pny.rate_lt and pnyc.rate_st > pny.rate_st   # cascades into effective rates


def test_wa_excise_is_long_term_only():
    from drift.tax import STATE_RATES
    lt, st = STATE_RATES["WA"]
    assert abs(lt - 0.07) < 1e-9 and st == 0.0          # 7% LT cap-gains excise, no income/ST tax


def test_il_estate_tax_cliff_and_hb2601_toggle():
    from drift.taxlab import il_estate_tax
    # At or below the $4M exclusion: no Illinois estate tax (the cliff into taxability).
    assert il_estate_tax(3_000_000, 4_000_000) == 0.0
    assert il_estate_tax(4_000_000, 4_000_000) == 0.0
    # Calibrated to the Illinois AG calculator anchor points (single estate, $4M exclusion).
    assert abs(il_estate_tax(5_000_000, 4_000_000) - 285_000) < 1_000
    assert abs(il_estate_tax(8_000_000, 4_000_000) - 690_000) < 1_000
    assert abs(il_estate_tax(10_000_000, 4_000_000) - 980_000) < 1_000
    # Top marginal rate caps at 16% (a $1M slice up at the top adds <= $160k).
    hi = il_estate_tax(12_000_000, 4_000_000) - il_estate_tax(11_000_000, 4_000_000)
    assert hi <= 160_000 + 1e-6
    # HB2601 doubles the exclusion to $8M -> shifts the baseline: $0 at/below $8M, and the
    # calibrated curve resumes above (a $9M estate matches the $5M-at-$4M figure, ~$285k).
    assert il_estate_tax(8_000_000, 8_000_000) == 0.0
    assert abs(il_estate_tax(9_000_000, 8_000_000) - 285_000) < 1_000
    assert il_estate_tax(8_000_000, 4_000_000) > 0.0      # ...vs a real bill under current law


def test_il_estate_tax_monotonic_and_exclusion_layer():
    from drift.taxlab import il_estate_tax
    prev = -1.0
    for e in range(4_000_000, 12_000_001, 500_000):
        t = il_estate_tax(e, 4_000_000)
        assert t >= prev                                  # non-decreasing in estate size
        prev = t
    # A higher exclusion never increases the tax (HB2601 only ever helps).
    assert il_estate_tax(7_000_000, 8_000_000) <= il_estate_tax(7_000_000, 4_000_000)


def test_estate_assumptions_embedded(tmp_path):
    import json
    from drift import ledger as L
    from drift.config import Settings
    from drift.taxlab import build_taxlab
    from drift.feed.synthetic import SyntheticFeed
    from dataclasses import replace
    from datetime import date, timedelta
    s = Settings(signal={"lookback": 20, "vol_window": 10, "breakout_channel": 15})
    start = date(2020, 1, 1)
    series = {}
    for i, d in enumerate((0.5, -0.3, 0.2, 0.4)):
        bars = SyntheticFeed(instruments=(f"S{i}",), n_bars=300, regimes=[(300, d)], seed=5 + i).series(f"S{i}")
        series[f"S{i}"] = [replace(b, asof=(start + timedelta(days=k)).isoformat()) for k, b in enumerate(bars)]
    led = L.seed_ledger(series, s, sessions=120)
    (tmp_path / "ledger.json").write_text(json.dumps(led))
    e = build_taxlab(tmp_path)["assumptions"]["estate"]
    assert e["il_exclusion"] == 4_000_000 and e["il_hb2601_exclusion"] == 8_000_000
    assert e["fed_exemption_indiv"] == 15_000_000 and e["il_top_rate"] == 0.16


def test_location_alpha3_three_buckets():
    from drift.taxlab import location_alpha3
    mdr, pdr, g, H = 0.08, 0.004, 0.07, 30
    # Roth and Traditional are interchangeable for the annual alpha (both shelter the drag):
    a = location_alpha3(1_000_000, 1_000_000, 0, mdr, pdr, g, H)
    b = location_alpha3(1_000_000, 0, 1_000_000, mdr, pdr, g, H)
    assert abs(a["annual_saved"] - b["annual_saved"]) < 1e-6
    # Equal taxable vs sheltered maximizes the overlap; both extremes zero it out.
    assert location_alpha3(0, 500_000, 500_000, mdr, pdr, g, H)["annual_saved"] == 0.0   # nothing in taxable
    assert location_alpha3(1_000_000, 0, 0, mdr, pdr, g, H)["annual_saved"] == 0.0        # nothing sheltered
    eq = location_alpha3(1_000_000, 500_000, 500_000, mdr, pdr, g, H)
    # annual = (T·A/W)·(mdr−pdr) = (1e6·1e6/2e6)·0.076 = 38_000
    assert abs(eq["annual_saved"] - 38_000) < 1e-6
    # terminal alpha = annual · future-value-of-annuity factor (compounding the saved tax)
    fv = ((1 + g) ** H - 1) / g
    assert abs(eq["terminal_alpha"] - 38_000 * fv) < 1e-3
    assert eq["terminal_alpha"] > eq["annual_saved"]      # compounding lifts it well above one year
    assert eq["sleeve"] == 1_000_000                      # momentum sleeve = Traditional + Roth


def test_after_fee_subtracts_annual_cost_over_the_track():
    from drift.taxlab import after_fee
    # 26.56% after-tax, 130 bps all-in fee, 1.75y -> 26.56 - 1.30*1.75 = 24.28%
    assert abs(after_fee(0.2656, 0.013, 1.75) - 0.24285) < 1e-9
    assert after_fee(0.10, 0.0, 5) == 0.10          # zero fee is a no-op
    assert after_fee(0.10, 0.01, 0) == 0.10         # zero horizon is a no-op


def test_benchmark_after_tax_is_only_dividend_drag():
    from drift.ledger import _bench_after_tax
    brets = [0.001] * 252                            # ~+28.6% over a year, buy-and-hold
    pretax = 1.0
    for r in brets:
        pretax *= (1.0 + r)
    pretax -= 1.0
    at = _bench_after_tax(brets, r_lt=0.238, bars_per_year=252)
    assert at < pretax                               # dividends are taxed
    assert pretax - at < 0.01                        # ...but only lightly (no realized gains)
    assert abs(_bench_after_tax(brets, r_lt=0.0, bars_per_year=252) - pretax) < 1e-9  # no LT tax -> no drag


def test_state_table_is_complete_with_special_cases():
    from drift.tax import STATE_RATES
    assert len(STATE_RATES) >= 52                          # 50 states + DC + the "—" default
    assert "IL" in STATE_RATES and STATE_RATES["IL"][0] > 0
    assert STATE_RATES["TX"] == (0.0, 0.0)                 # no income tax
    assert STATE_RATES["MA"][1] > STATE_RATES["MA"][0]     # MA taxes short-term higher
    assert STATE_RATES["WA"][0] > 0 and STATE_RATES["WA"][1] == 0   # WA LT-only excise
    assert STATE_RATES["SC"][0] < STATE_RATES["SC"][1]     # SC long-term exclusion
