import pytest

from mrbet.models import GameState, Period
from mrbet.reversion import projected_final, sigma_for


def _state(period, elapsed, total):
    length = period.length_minutes
    return GameState(period, elapsed, length - elapsed, home_score=total // 2, away_score=total - total // 2)


def test_full_reversion_uses_pregame_rate():
    # beta=1: remaining play scores at the pregame rate regardless of pace.
    st = _state(Period.FULL, 12.0, 40)  # cold first quarter
    pre = 219.0
    fair = projected_final(pre, points_so_far=40, state=st, beta=1.0)
    # 40 + 36 * (219/48)
    assert fair == pytest.approx(40 + 36 * (219 / 48), abs=1e-6)


def test_no_reversion_uses_current_pace():
    # beta=0: extrapolate the current pace to the end.
    st = _state(Period.FULL, 12.0, 40)
    fair = projected_final(219.0, points_so_far=40, state=st, beta=0.0)
    # pace = 40/12; final = 40 + 36*(40/12) = 40/12 * 48
    assert fair == pytest.approx((40 / 12) * 48, abs=1e-6)


def test_blended_between_extremes():
    st = _state(Period.FULL, 12.0, 40)
    low = projected_final(219.0, 40, st, beta=0.0)
    high = projected_final(219.0, 40, st, beta=1.0)
    mid = projected_final(219.0, 40, st, beta=0.7)
    assert low < mid < high


def test_cold_start_projects_above_depressed_market():
    # The core thesis: after a cold start, a partially-reverting projection sits
    # above a market line that has over-dropped.
    st = _state(Period.FULL, 12.0, 40)
    fair = projected_final(219.0, 40, st, beta=0.7)
    assert fair > 187.5  # the depressed market line in the replay data


def test_early_minutes_fall_back_to_pregame_rate():
    # Before min_minutes_elapsed the pace term is ignored (uses pregame rate).
    st = _state(Period.FULL, 1.0, 2)
    fair = projected_final(219.0, 2, st, beta=0.0, min_minutes_elapsed=2.0)
    # With pace ignored, blended rate == pregame rate even at beta=0.
    assert fair == pytest.approx(2 + 47 * (219 / 48), abs=1e-6)


def test_sigma_shrinks_with_time_remaining():
    early = sigma_for(_state(Period.FULL, 6.0, 20), 11.0)
    late = sigma_for(_state(Period.FULL, 42.0, 200), 11.0)
    assert early > late
    assert late >= 0
