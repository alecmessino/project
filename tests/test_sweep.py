"""Unit tests for the backtest harness — pure logic, no network."""

from mrbet.espn import GameHistory, TimelinePoint, _full_elapsed, _parse_clock
from mrbet.linemodel import _book_line, game_config_from_history, synth_snapshots
from mrbet.study import _fit, reversion_fit
from mrbet.sweep import Combo, Record, _grade, _passes, evaluate_combo


def _hist():
    h = GameHistory(
        event_id="t", date="2026", away="OKC", home="SA",
        away_name="Oklahoma City Thunder", home_name="San Antonio Spurs",
        pregame_total=218.0, pregame_spread_home=-4.0,
    )
    # cold start (slow), then catches up to a 220 final
    h.timeline = [
        TimelinePoint(6.0, 10, 8), TimelinePoint(12.0, 26, 24),
        TimelinePoint(24.0, 56, 54), TimelinePoint(48.0, 110, 110),
    ]
    h.finals = {"game": {"full": 220, "h1": 110, "q1": 50, "q2": 60, "q3": 55, "q4": 55},
                "team": {"OKC": 110, "SA": 110}}
    return h


# ---- ESPN parse helpers ---------------------------------------------------- #
def test_parse_clock_and_elapsed():
    assert abs(_parse_clock("10:09") - 10.15) < 0.01
    assert _parse_clock("12:00") == 12.0
    # period 3 with 10:09 left -> 24 + (12-10.15) = 25.85 full-game minutes
    assert abs(_full_elapsed(3, 10.15) - 25.85) < 0.02
    assert _full_elapsed(4, 0.0) == 48.0  # end of regulation clamps at 48


def test_team_total_split_from_spread():
    h = _hist()
    tt = h.pregame_team_totals()
    # total 218, home favored by 4 -> home 111, away 107
    assert tt["SA"] == 111.0
    assert tt["OKC"] == 107.0


# ---- line model ------------------------------------------------------------ #
def test_book_line_chases_pace_when_beta_zero():
    # 20 pts in 12 min, beta=0 -> pure extrapolation: 20 * 48/12 = 80
    assert _book_line(218.0, 48.0, 20, 12.0, 36.0, book_beta=0.0, min_elapsed=5.0) == 80.0


def test_book_line_holds_pregame_when_beta_one():
    # beta=1 -> line ignores pace, projects at pregame rate: 20 + 36*(218/48)=183.5
    out = _book_line(218.0, 48.0, 20, 12.0, 36.0, book_beta=1.0, min_elapsed=5.0)
    assert abs(out - 183.5) < 0.6  # snapped to 0.5


def test_synth_snapshots_carry_modeled_lines():
    h = _hist()
    cfg = game_config_from_history(h)
    snaps = synth_snapshots(h, cfg, book_beta=0.2, sample_minutes=6.0)
    assert snaps
    first = snaps[0]
    assert any(l.book == "modeled" for l in first.lines)
    # H1 market only appears before halftime
    assert any(l.period.value == "h1" for s in snaps for l in s.lines if s.state.minutes_elapsed < 24)


# ---- grading + threshold filter -------------------------------------------- #
def test_grade_win_loss_push():
    assert _grade("over", 200.0, 209.0, -110)[0] == "win"
    assert _grade("under", 200.0, 209.0, -110)[0] == "loss"
    assert _grade("over", 209.0, 209.0, -110)[0] == "push"
    # winning -110 returns ~0.909 profit on 1u
    assert abs(_grade("over", 200.0, 209.0, -110)[1] - 0.909) < 0.01


def _rec(move, edge, ev, rem, kind="full", outcome="win", profit=0.909, game="g", side="over"):
    return Record(game_id=game, market=f"m:{kind}", period_kind=kind, side=side, minute=6.0,
                  minutes_remaining=rem, pct_move=move, abs_move=abs(move), edge_pts=edge,
                  ev=ev, prob=0.6, line=200.0, odds=-110, outcome=outcome, profit_1u=profit)


def test_passes_gates_all_thresholds():
    c = Combo(0.10, 3.0, 0.0, 6.0)
    assert _passes(_rec(-0.12, 4.0, 0.05, 40), c)
    assert not _passes(_rec(-0.08, 4.0, 0.05, 40), c)   # move too small
    assert not _passes(_rec(-0.12, 2.0, 0.05, 40), c)   # edge too small
    assert not _passes(_rec(-0.12, 4.0, -0.01, 40), c)  # negative EV
    assert not _passes(_rec(-0.12, 4.0, 0.05, 3), c)    # too little time left


def test_min_minutes_scales_for_shorter_periods():
    c = Combo(0.10, 3.0, 0.0, 6.0)  # full=6 -> half=4, quarter=3
    assert _passes(_rec(-0.12, 4.0, 0.05, 4.5, kind="half"), c)
    assert not _passes(_rec(-0.12, 4.0, 0.05, 3.5, kind="half"), c)


def test_evaluate_combo_dedupes_to_first_crossing():
    c = Combo(0.10, 3.0, 0.0, 6.0)
    # two qualifying rows for the same game/market/side -> counts as ONE bet
    recs = [_rec(-0.12, 4.0, 0.05, 40), _rec(-0.15, 6.0, 0.08, 30)]
    row = evaluate_combo(recs, c)
    assert row.bets == 1
    assert row.wins == 1


# ---- reversion fit --------------------------------------------------------- #
def test_fit_recovers_known_beta():
    # y = 0.75 x exactly -> fit returns 0.75 with R^2 = 1
    samples = [(2.0, 1.5), (-1.0, -0.75), (4.0, 3.0)]
    beta, r2 = _fit(samples)
    assert abs(beta - 0.75) < 1e-9
    assert abs(r2 - 1.0) < 1e-9


def test_reversion_fit_on_cold_start_game():
    # synthetic cold-start game reverts upward -> beta should be strongly positive
    res = reversion_fit([_hist()], sample_at=6.0)
    assert res
    full = next(r for r in res if r.label.startswith("full-game @>=6"))
    assert full.beta > 0.5
