"""Pure, offline units for the line-edge investigation helpers."""

import math

import pytest

from investigate_line_edge import (
    bucket_label,
    closing_line,
    half_inning_observations,
    roi_per_unit,
    wilson_interval,
)


# ------------------------------- Wilson CI -----------------------------------
def test_wilson_known_case():
    # 14/25 ≈ 56% with a wide interval (the shipped-gate sample the user flagged)
    lo, hi = wilson_interval(14, 25)
    assert 0.36 < lo < 0.40 and 0.72 < hi < 0.76
    assert lo < 14 / 25 < hi


def test_wilson_degenerate():
    assert wilson_interval(0, 0) == pytest.approx((float("nan"), float("nan")), nan_ok=True)
    lo, hi = wilson_interval(10, 10)   # all wins -> upper bound capped at 1.0
    assert hi == pytest.approx(1.0) and lo < 1.0


# ------------------------------ drop buckets ---------------------------------
def test_bucket_boundaries_are_low_exclusive_high_inclusive():
    assert bucket_label(0.0) == "<= 0 (no drop / up)"     # 0 is not a drop
    assert bucket_label(-0.5) == "<= 0 (no drop / up)"
    assert bucket_label(0.5) == "(0, 0.5]"                 # upper edge included
    assert bucket_label(0.6) == "(0.5, 1.0]"
    assert bucket_label(1.0) == "(0.5, 1.0]"
    assert bucket_label(1.01) == "(1.0, 1.5]"
    assert bucket_label(2.0) == "(1.5, 2.0]"
    assert bucket_label(2.5) == "> 2.0"


def test_roi_at_breakeven_is_near_zero():
    assert roi_per_unit(110 / 210) == pytest.approx(0.0, abs=1e-9)
    assert roi_per_unit(0.60) > 0 and roi_per_unit(0.50) < 0


# ------------------------------ closing line ---------------------------------
def test_closing_line_picks_last_point_before_first_pitch():
    pts = [{"ts": "2026-06-15T18:00", "line": 9.0},   # opening (day-of, early)
           {"ts": "2026-06-15T20:55", "line": 8.5},   # last pre-pitch
           {"ts": "2026-06-15T21:40", "line": 8.0}]   # in-game (after first pitch)
    assert closing_line(pts, "2026-06-15T21:05:00Z") == 8.5


def test_closing_line_falls_back_to_open_when_all_points_after_start():
    pts = [{"ts": "2026-06-15T21:10", "line": 7.5}]
    assert closing_line(pts, "2026-06-15T21:05:00Z") == 7.5


# --------------------------- half-inning sampling ----------------------------
def test_observations_one_per_half_inning_from_third_and_push_flagged():
    pts = [{"ts": "2026-06-15T21:00", "line": 9.0},
           {"ts": "2026-06-15T21:45", "line": 8.0},   # inning 3
           {"ts": "2026-06-15T22:30", "line": 7.0}]   # inning 5
    # timeline: (ts, inning, half, outs, runs) — two plays in inning 3 top, one inning 5
    tl = [("2026-06-15T21:45:00", 3, "top", 0, 1),
          ("2026-06-15T21:50:00", 3, "top", 2, 1),   # same half-inning -> not resampled
          ("2026-06-15T22:30:00", 5, "top", 0, 3)]
    obs = half_inning_observations(pts, tl, final_total=9, closing=9.0)
    assert len(obs) == 2                              # one per (inning,half), inning>=3
    first = obs[0]
    assert first["inning"] == 3 and first["line"] == 8.0
    assert first["drop"] == pytest.approx(1.0)        # closing 9.0 - live 8.0
    assert first["win"] is True and first["push"] is False   # final 9 > 8.0 -> Over
    # a push is flagged when the final lands exactly on the live line
    push_obs = half_inning_observations(pts, tl, final_total=8, closing=9.0)[0]
    assert push_obs["push"] is True and push_obs["win"] is False   # 8 == 8.0


def test_observations_skip_innings_before_three():
    pts = [{"ts": "2026-06-15T21:00", "line": 9.0},
           {"ts": "2026-06-15T21:20", "line": 8.5}]
    tl = [("2026-06-15T21:20:00", 2, "bottom", 0, 0)]   # inning 2 -> skipped
    assert half_inning_observations(pts, tl, final_total=10, closing=9.0) == []
