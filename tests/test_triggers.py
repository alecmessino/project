import pytest

from mrbet.config import Settings
from mrbet.models import (
    Baseline,
    GameState,
    MarketLine,
    MarketType,
    Period,
    Side,
)
from mrbet.triggers import evaluate_market, to_signal


def _settings():
    return Settings()


def _full_state(elapsed, total):
    return GameState(Period.FULL, elapsed, 48 - elapsed, home_score=total // 2, away_score=total - total // 2)


def test_cold_start_flags_over():
    s = _settings()
    state = _full_state(12.0, 40)
    base = Baseline(MarketType.GAME_TOTAL, Period.FULL, 219.0, -110, -110)
    live = MarketLine(MarketType.GAME_TOTAL, Period.FULL, 187.5, -110, -110)
    ev = evaluate_market(base, live, state, points_so_far=40, settings=s)
    assert ev.side is Side.OVER
    sig = to_signal(ev, s)
    assert sig is not None
    assert ev.edge_pts >= s.triggers.edge_pts_threshold
    assert ev.ev >= s.triggers.ev_threshold


def test_small_move_does_not_flag():
    s = _settings()
    state = _full_state(6.0, 22)
    base = Baseline(MarketType.GAME_TOTAL, Period.FULL, 219.0, -110, -110)
    live = MarketLine(MarketType.GAME_TOTAL, Period.FULL, 212.5, -110, -110)  # ~3% move
    ev = evaluate_market(base, live, state, points_so_far=22, settings=s)
    assert to_signal(ev, s) is None


def test_no_flag_when_edge_below_threshold():
    s = _settings()
    state = _full_state(12.0, 40)
    base = Baseline(MarketType.GAME_TOTAL, Period.FULL, 219.0, -110, -110)
    # Big % move but line sits right at the fair projection -> tiny edge.
    fair = evaluate_market(base, MarketLine(MarketType.GAME_TOTAL, Period.FULL, 190.0, -110, -110), state, 40, s)
    near_fair_line = round(fair.fair_final * 2) / 2  # nearest half point
    live = MarketLine(MarketType.GAME_TOTAL, Period.FULL, near_fair_line, -110, -110)
    ev = evaluate_market(base, live, state, 40, s)
    assert abs(ev.edge_pts) < s.triggers.edge_pts_threshold
    assert to_signal(ev, s) is None


def test_min_time_remaining_gate():
    s = _settings()
    # Only 2 minutes left in the game — below the 'full' threshold of 6.
    state = GameState(Period.FULL, 46.0, 2.0, home_score=100, away_score=80)
    base = Baseline(MarketType.GAME_TOTAL, Period.FULL, 219.0, -110, -110)
    live = MarketLine(MarketType.GAME_TOTAL, Period.FULL, 187.5, -110, -110)
    ev = evaluate_market(base, live, state, points_so_far=180, settings=s)
    assert to_signal(ev, s) is None


def test_under_symmetry_on_hot_start():
    s = _settings()
    # Hot start: lots of points early. The market over-spikes the line ABOVE the
    # reverting projection (which still weights pace at beta<1), so UNDER is value.
    state = _full_state(12.0, 80)
    base = Baseline(MarketType.GAME_TOTAL, Period.FULL, 219.0, -110, -110)
    live = MarketLine(MarketType.GAME_TOTAL, Period.FULL, 280.0, -110, -110)
    ev = evaluate_market(base, live, state, points_so_far=80, settings=s)
    assert ev.side is Side.UNDER
    sig = to_signal(ev, s)
    assert sig is not None
    assert ev.pct_move > 0  # line moved UP


def test_team_total_uses_team_sigma_and_points():
    s = _settings()
    state = _full_state(12.0, 40)
    base = Baseline(MarketType.TEAM_TOTAL, Period.FULL, 108.5, -110, -115, team="OKC")
    live = MarketLine(MarketType.TEAM_TOTAL, Period.FULL, 95.5, -110, -115, team="OKC")
    ev = evaluate_market(base, live, state, points_so_far=22, settings=s)
    assert ev.side is Side.OVER
    assert ev.fair_final > 95.5
