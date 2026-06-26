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


def test_il_estate_tax_scales_above_10m_at_top_rate():
    from drift.taxlab import il_estate_tax
    # A $14M estate scales smoothly through the 16% top — not capped near ~$1.01M.
    assert abs(il_estate_tax(14_000_000, 4_000_000) - 1_620_000) < 1_000
    # the top slice is taxed at exactly 16%.
    step = il_estate_tax(20_000_000, 4_000_000) - il_estate_tax(19_000_000, 4_000_000)
    assert abs(step - 160_000) < 1


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


def test_compounded_fee_drag_401k():
    from drift.taxlab import compounded_fee_drag
    assert compounded_fee_drag(0, 0.005, 0.07, 10) == 0.0
    assert compounded_fee_drag(500_000, 0.0, 0.07, 10) == 0.0          # no fee -> no drag
    d = compounded_fee_drag(500_000, 0.005, 0.07, 10)
    assert d > 0                                                       # a real 10-yr fee drag
    # a bigger fee or balance always drags more
    assert compounded_fee_drag(500_000, 0.010, 0.07, 10) > d
    assert compounded_fee_drag(1_000_000, 0.005, 0.07, 10) > d


def test_roth_conversion_illinois_arbitrage():
    from drift.taxlab import roth_conversion
    # Taxed state: federal + state both apply.
    taxed = roth_conversion(100_000, 0.37, 0.0495, False)
    assert abs(taxed["federal"] - 37_000) < 1 and abs(taxed["state"] - 4_950) < 1
    assert abs(taxed["total"] - 41_950) < 1 and taxed["state_saved"] == 0.0
    # Illinois (exempts retirement income): federal only, the state tax is saved.
    il = roth_conversion(100_000, 0.37, 0.0495, True)
    assert abs(il["federal"] - 37_000) < 1 and il["state"] == 0.0
    assert abs(il["state_saved"] - 4_950) < 1 and il["total"] < taxed["total"]


def test_strategy_assumptions_embedded(tmp_path):
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
    st = build_taxlab(tmp_path)["assumptions"]["strategy"]
    assert st["k401_fee_bps"] == 50 and st["rollover_years"] == 10
    assert "IL" in st["states_exempt_retirement"]


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


def test_build_taxlab_degraded_without_ledger(tmp_path):
    """Fresh-checkout path the daily Action hits before any ledger exists: the page state must
    still be complete (states/brackets/assumptions, incl. estate+strategy) and JSON-serializable,
    with profile=None — never a crash or a half-built payload shipped to Pages."""
    import json
    from drift.taxlab import build_taxlab
    # (a) no ledger.json at all
    st = build_taxlab(tmp_path)
    assert st["profile"] is None
    for key in ("states", "brackets", "assumptions"):
        assert key in st and st[key]
    assert "estate" in st["assumptions"] and "strategy" in st["assumptions"]
    json.dumps(st)
    # (b) corrupt ledger.json -> same graceful fallback
    (tmp_path / "ledger.json").write_text("{not valid json")
    st2 = build_taxlab(tmp_path)
    assert st2["profile"] is None and st2["assumptions"]
    json.dumps(st2)
    # (c) ledger present but too short for a gain profile
    (tmp_path / "ledger.json").write_text(json.dumps({"entries": []}))
    st3 = build_taxlab(tmp_path)
    assert st3["profile"] is None and "strategy" in st3["assumptions"]
    json.dumps(st3)


def test_taxlab_js_mirrors_python_il_estate_curve():
    """The Tax Lab page JS hand-duplicates the Python IL estate curve as a literal IL_AG array.
    Guard them from silently drifting apart when _IL_AG_CURVE is tuned (the documented workflow)."""
    import ast
    import re
    from pathlib import Path
    import drift.taxlab as T
    html = (Path(T.__file__).with_name("web") / "taxlab.html").read_text()
    m = re.search(r"const IL_AG=(\[\[.*?\]\]);", html)
    assert m, "IL_AG array not found in taxlab.html"
    js_rows = ast.literal_eval(m.group(1))
    py_rows = [[bp, tax, rate] for (bp, tax, rate) in T._IL_AG_CURVE]
    assert js_rows == py_rows, f"JS IL_AG {js_rows} != Python _IL_AG_CURVE {py_rows}"


def test_pure_tax_fns_handle_edge_inputs():
    """Slider extremes / misconfigured assumptions must not yield NaN/Inf or negative dollars."""
    from drift.taxlab import roth_conversion, location_alpha3, compounded_fee_drag, after_fee
    # roth: zero conversion -> all-zero; negative clamps to zero
    z = roth_conversion(0.0, 0.37, 0.05, False)
    assert z["federal"] == 0.0 and z["state"] == 0.0 and z["total"] == 0.0 and z["state_saved"] == 0.0
    assert roth_conversion(-100_000.0, 0.37, 0.05, False)["total"] == 0.0
    # exempt state: federal only; state_saved is the avoided state tax
    ex = roth_conversion(100_000.0, 0.24, 0.0495, True)
    assert ex["state"] == 0.0 and abs(ex["state_saved"] - 4950.0) < 1e-6 and abs(ex["federal"] - 24000.0) < 1e-6
    # location alpha with zero growth -> terminal == annual_saved * years (annuity fv falls back to years)
    la = location_alpha3(1_000_000, 500_000, 500_000, 0.02, 0.005, 0.0, 30)
    assert abs(la["terminal_alpha"] - la["annual_saved"] * 30) < 1e-6
    # fee drag: negative balance -> 0; fee>growth stays finite & non-negative (net rate floored at 0)
    assert compounded_fee_drag(-1.0, 0.005, 0.07, 10) == 0.0
    d = compounded_fee_drag(1_000_000, 0.10, 0.07, 10)     # fee 10% exceeds 7% growth
    assert d > 0 and d == d and d != float("inf")
    # after_fee: negative horizon clamps to a no-op (max(0, years))
    assert after_fee(0.10, 0.01, -5) == 0.10


def test_estate_classification():
    """Option 1: Illinois precise, the ~12 estate/inheritance states neutral, everything else none."""
    from drift.taxlab import estate_classification, ASSUMPTIONS
    assert estate_classification("TX")["kind"] == "none"
    assert estate_classification("FL")["kind"] == "none"
    assert estate_classification("CA")["kind"] == "none"
    assert estate_classification("IL")["kind"] == "illinois"
    ny = estate_classification("NY"); assert ny["kind"] == "levy" and ny["type"] == "estate"
    assert estate_classification("WA")["kind"] == "levy"
    md = estate_classification("MD"); assert md["kind"] == "levy" and md["type"] == "both"
    pa = estate_classification("PA"); assert pa["kind"] == "levy" and pa["type"] == "inheritance"
    assert "IL" not in ASSUMPTIONS["estate"]["state_estate"]   # IL is the precise engine, not the map
    assert ASSUMPTIONS["estate"]["default_joint"] == 0          # individual-first default (T3)


def test_state_estate_embedded(tmp_path):
    """The state_estate map + individual-first default reach the page state and are serializable."""
    import json
    from drift.taxlab import build_taxlab
    st = build_taxlab(tmp_path)   # no ledger -> degraded, but assumptions must be present
    e = st["assumptions"]["estate"]
    assert e["state_estate"].get("NY") == "estate" and e["state_estate"].get("PA") == "inheritance"
    assert "IL" not in e["state_estate"]
    assert e["default_joint"] == 0
    json.dumps(st)


def test_methodology_dual_engine_and_honest():
    """Methodology copy describes the dual-engine architecture and NEVER claims the live track
    includes the offline-validated Slow Book (honesty guard)."""
    from pathlib import Path
    import drift.taxlab as T
    led = " ".join((Path(T.__file__).with_name("web") / "ledger.html").read_text().split())  # collapse HTML line-wrap
    assert "Fast Book" in led and "Slow Book" in led
    assert "asset location" in led.lower()
    assert "not part of the Model Portfolio above" in led   # the Slow Book is NOT in the model curve
    # Its comparative claim must be framed as a hypothetical/illustrative validation run, not a track record.
    assert "illustrative" in led.lower() and "scripts/slow_sweep.py" in led


def test_shipped_configs_ship_neutral_tilt():
    """Methodology guard: the EM/value/small overweight added no risk-adjusted value over 40y of
    real data (scripts/slow_sweep.py tilt_attribution), so the shipped books carry NO factor tilt
    (all multipliers 1.0). Re-introducing a tilt without re-validation must break this."""
    from drift.config import Settings
    for cfg in ("config/drift.yaml", "config/slow.yaml"):
        cs = Settings.load(cfg).cross_section
        for name, d in (("region", cs.tilt_region), ("size", cs.tilt_size), ("style", cs.tilt_style)):
            assert all(v == 1.0 for v in d.values()), f"{cfg} ships a non-neutral {name} tilt: {d}"
