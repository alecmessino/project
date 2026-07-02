"""Empirical decay calibration (the revealed-pace bias fix) — pure, offline."""

import pytest

from shared_piping.decay import DEFAULT_SURFACE, bucket_of, decay_ratio, load_surface
from shared_piping.run_expectancy import expected_final_total


def test_bucketing_progress_and_pace():
    # top 2, 0 outs, 0 runs on a 9.0 total: early game, on-pace-ish -> normal
    assert bucket_of(9.0, 2, "top", 0, 0) == ("early", "normal")
    # bottom 5, 2-2 (4 runs) on 9.0: mid game; expected_so_far ≈ 4.5 -> normal
    assert bucket_of(9.0, 5, "bottom", 0, 4) == ("mid", "normal")
    # bottom 5, 1 run total on 9.0: expected ≈ 4.5, 1 < 3.0 -> cold
    assert bucket_of(9.0, 5, "bottom", 0, 1) == ("mid", "cold")
    # inning 8: late
    assert bucket_of(9.0, 8, "top", 1, 3)[0] == "late"


def test_ratio_discounts_cold_mid_games():
    r_cold = decay_ratio(9.0, 5, "bottom", 0, 1, surface=DEFAULT_SURFACE)
    r_norm = decay_ratio(9.0, 5, "bottom", 0, 4, surface=DEFAULT_SURFACE)
    assert r_cold < r_norm <= 1.05
    assert r_cold == pytest.approx(0.943)


def test_ratio_clamped_and_defaults_on_missing_bucket():
    assert decay_ratio(9.0, 5, "top", 0, 2, surface={"mid|cold": 0.1}) == 0.60  # clamp low
    assert decay_ratio(9.0, 2, "top", 0, 1, surface={}) == 1.0                  # missing -> 1


def test_fair_drops_with_decay_ratio():
    kw = dict(pregame_total=9.0, runs_so_far=2, inning=6, half="top", outs=0,
              on_first=False, on_second=False, on_third=False, home_key="ATL",
              ttop_mult=1.15, in_window=True)
    naive = expected_final_total(decay_ratio=1.0, **kw)
    calibrated = expected_final_total(decay_ratio=0.9, **kw)
    # 10% discount on the 4.0 naive remaining runs (top 6) = 0.4 lower fair
    assert naive.expected_final - calibrated.expected_final == pytest.approx(0.4, abs=0.05)


def test_load_surface_falls_back_to_defaults(tmp_path):
    assert load_surface(tmp_path / "nope.json") == DEFAULT_SURFACE
    p = tmp_path / "s.json"
    p.write_text('{"mid|cold": {"median": 0.91, "n": 50}}')
    assert load_surface(p) == {"mid|cold": 0.91}
