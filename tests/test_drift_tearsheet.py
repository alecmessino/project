import json

from drift.config import Settings
from drift.exhibit import render_tearsheet
from drift.feed.synthetic import SyntheticFeed
from drift import tearsheet as ts


def _settings():
    return Settings(signal={"lookback": 20, "vol_window": 10, "breakout_channel": 15})


def _series(drifts, n=400):
    out = {}
    for i, d in enumerate(drifts):
        feed = SyntheticFeed(instruments=(f"S{i}",), n_bars=n, regimes=[(n, d)], seed=40 + i)
        out[f"S{i}"] = feed.series(f"S{i}")
    return out


def test_book_streams_returns_aligned_dated_pairs():
    strat, bench = ts.book_streams(_series([0.5, -0.5]), _settings())
    assert strat and bench
    assert len(strat) == len(bench)
    assert all(isinstance(d, str) for d, _ in strat)


def test_fit_params_returns_grid_member():
    series = _series([0.6, 0.2, -0.4])
    strat, _ = ts.book_streams(series, _settings())
    split = ts._split_date(strat, 0.6)
    L, c, sharpe = ts.fit_params(series, _settings(), split)
    assert L in ts.GRID_LOOKBACK and c in ts.GRID_CONTINUATION


def test_build_book_shape_and_oos_split():
    bk = ts.build_book("Test", _series([0.6, -0.3, 0.1]), _settings(), train_frac=0.6)
    for key in ("strategy", "benchmark", "oos", "by_year", "equity", "fit"):
        assert key in bk
    assert "train" in bk["oos"] and "test" in bk["oos"]
    # equity overlay arrays align and the split marker is within (0,1)
    assert len(bk["equity"]["strat"]) == len(bk["equity"]["bench"])
    assert 0.0 < bk["equity"]["split_frac"] < 1.0


def test_build_tearsheet_with_injected_series_is_serializable():
    report = ts.build_tearsheet(_settings(),
                                _series=[("Book A", _series([0.5, -0.5]))] and {"Book A": _series([0.5, -0.5])})
    assert report["books"]
    json.dumps(report)
    html = render_tearsheet(report)
    assert "/*__STATE__*/null/*__END__*/" not in html
    assert html.lstrip().startswith("<!DOCTYPE html>")
