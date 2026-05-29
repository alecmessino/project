"""Unit tests for the forward-test ledger (pure logic, no network)."""

from mrbet import forward as fwd
from mrbet.models import (
    Baseline, Evaluation, GameState, MarketLine, MarketType, Period, Side,
)


def _eval(line, side=Side.OVER, ev=0.05, prob=0.62, team=None,
          mt=MarketType.GAME_TOTAL, period=Period.FULL):
    base = Baseline(mt, period, 219.0, -110, -110, team=team)
    live = MarketLine(mt, period, line, -110, -110, team=team)
    state = GameState(Period.FULL, 12.0, 36.0, 50, 45)
    return Evaluation(base, live, state, side, 210.0, -0.1, 5.0, prob, 0.524, ev, 4.0)


def test_merge_locks_entry_advances_close_over():
    led = {}
    fwd.merge_signal(led, _eval(187.5), "t0", "OKC @ SAS")
    fwd.merge_signal(led, _eval(200.0), "t1", "OKC @ SAS")  # line bounced back up
    (e,) = led.values()
    assert e["entry_line"] == 187.5          # entry locked at first sighting
    assert e["close_line"] == 200.0          # close advanced
    assert e["clv_pts"] == 12.5              # over: close - entry


def test_clv_direction_under():
    led = {}
    fwd.merge_signal(led, _eval(230.0, side=Side.UNDER), "t0", "m")
    fwd.merge_signal(led, _eval(220.0, side=Side.UNDER), "t1", "m")
    (e,) = led.values()
    assert e["clv_pts"] == 10.0              # under: entry - close


def test_distinct_keys_per_market_side():
    led = {}
    fwd.merge_signal(led, _eval(187.5, side=Side.OVER), "t0", "m")
    fwd.merge_signal(led, _eval(95.5, side=Side.OVER, team="OKC",
                                mt=MarketType.TEAM_TOTAL), "t0", "m")
    assert len(led) == 2


def test_grades_when_finals_present():
    led = {}
    finals = {"game": {"full": 209}, "team": {}}
    fwd.merge_signal(led, _eval(187.5, side=Side.OVER), "t0", "m", finals)
    (e,) = led.values()
    assert e["outcome"] == "win"             # 209 > 187.5
    assert e["profit"] > 0


def test_summarize_rolls_up():
    led = {}
    finals = {"game": {"full": 209}}
    fwd.merge_signal(led, _eval(187.5, side=Side.OVER), "t0", "m", finals)   # win
    fwd.merge_signal(led, _eval(250.0, side=Side.OVER, period=Period.H1), "t0", "m", finals)  # h1 ungraded->pending? finals has no h1
    s = fwd.summarize(led)
    assert s["bets"] == 2
    assert s["wins"] == 1
    assert s["clv_graded"] == 2


def test_dump_and_load_roundtrip(tmp_path):
    led = {}
    fwd.merge_signal(led, _eval(187.5), "t0", "OKC @ SAS")
    p = tmp_path / "forward.json"
    fwd.dump(p, led, scope={"matchup": "OKC @ SAS"})
    back = fwd.load_ledger(p)
    assert len(back) == 1
    assert list(back.values())[0]["entry_line"] == 187.5
