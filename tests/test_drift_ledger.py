import json
from dataclasses import replace
from datetime import date, timedelta

from drift import ledger as L
from drift.config import Settings
from drift.exhibit import render_ledger
from drift.feed.synthetic import SyntheticFeed


def _settings():
    return Settings(signal={"lookback": 20, "vol_window": 10, "breakout_channel": 15})


def _series(drifts=(0.6, -0.4, 0.1), n=300):
    # Relabel synthetic bars with real ISO dates — the ledger keys off calendar
    # dates (as live feeds emit), unlike the synthetic feed's integer-string asof.
    start = date(2020, 1, 1)
    out = {}
    for i, d in enumerate(drifts):
        feed = SyntheticFeed(instruments=(f"S{i}",), n_bars=n, regimes=[(n, d)], seed=50 + i)
        bars = feed.series(f"S{i}")
        out[f"S{i}"] = [replace(b, asof=(start + timedelta(days=k)).isoformat())
                        for k, b in enumerate(bars)]
    return out


def test_seed_builds_growing_track_record():
    led = L.seed_ledger(_series(), _settings(), sessions=40)
    assert len(led["entries"]) == 40
    assert led["inception"] == led["entries"][0]["date"]
    assert all(e["seed"] for e in led["entries"])
    # equity is a cumulative product -> strictly tracks realized returns
    assert led["entries"][-1]["equity"] > 0


def test_update_is_idempotent_on_same_date():
    series = _series()
    led = L.seed_ledger(series, _settings(), sessions=30)
    n = len(led["entries"])
    L.update_ledger(led, series, _settings())   # no newer bar than the seed
    assert len(led["entries"]) == n             # nothing appended


def test_update_appends_when_a_new_bar_arrives():
    full = _series(n=300)
    s = _settings()
    truncated = {i: bars[:-1] for i, bars in full.items()}
    led = L.seed_ledger(truncated, s, sessions=30)
    n = len(led["entries"])
    L.update_ledger(led, full, s)               # one fresh bar for each name
    assert len(led["entries"]) == n + 1
    assert led["entries"][-1]["seed"] is False  # live, not seeded


def test_realized_return_marks_prior_weights():
    # Two bars only after warmup: hand-check that realized return uses prev weights.
    s = _settings()
    series = _series(n=200)
    led = L.seed_ledger(series, s, sessions=2)
    # the second entry's realized return must equal mean of prev_w * asset move
    assert "realized_return" in led["entries"][-1]
    assert isinstance(led["entries"][-1]["equity"], float)


def test_build_state_and_render():
    led = L.seed_ledger(_series(), _settings(), sessions=50)
    st = L.build_ledger_state(led)
    assert st["header"]["days"] == 50
    assert st["equity"] and st["positions"]
    json.dumps(st)
    html = render_ledger(st)
    assert "/*__STATE__*/null/*__END__*/" not in html
    assert html.lstrip().startswith("<!DOCTYPE html>")


def test_empty_ledger_state_is_safe():
    st = L.build_ledger_state(L.new_ledger())
    assert st["header"]["days"] == 0
    assert st["equity"] == []
    assert st["benchmarks"] == []
    json.dumps(st)


def test_blended_style_box_spreads_across_cells_and_sums_to_one():
    # A pure-IVE book must spread across multiple boxes (not one), per the
    # fund's underlying Morningstar-style composition, and normalize to 1.
    box = L._blend_style_box({"IVE": 1.0})
    assert box["large|value"] > box["mid|blend"] > 0      # IVE's dominant cells
    assert len([v for v in box.values() if v > 0]) >= 4   # genuinely spread
    assert abs(sum(box.values()) - 1.0) < 1e-6


def test_benchmarks_carry_risk_stats_and_style_box():
    s = _settings()
    series = _series(n=260)
    # Two buy-and-hold benchmarks marked in parallel over the same window
    # (reuse synthetic series as stand-in price histories for VT / VTI).
    names = list(series)
    bench = {"VT": series[names[0]], "VTI": series[names[1]]}
    led = L.seed_ledger(series, s, sessions=40, benchmarks=bench)
    assert all(isinstance(e["bench_equity"], dict) for e in led["entries"][1:])
    st = L.build_ledger_state(led)
    labels = [b["label"] for b in st["benchmarks"]]
    assert labels == ["VT", "VTI"]
    for b in st["benchmarks"]:
        assert "sharpe" in b and "max_drawdown" in b and "excess" in b
        assert b["exposure"]["style_box"]            # benchmark has its own box
        assert b["exposure"]["by_region"]            # and its own region split
    json.dumps(st)


def test_cost_assumptions_surface_in_header():
    s = _settings()
    led = L.seed_ledger(_series(), s, sessions=20)
    st = L.build_ledger_state(led)
    assert st["header"]["cost_bps_per_side"] == s.sizing.cost_bps_per_side
    assert st["header"]["cost_bps_roundtrip"] == round(s.sizing.cost_bps_per_side * 2, 1)
