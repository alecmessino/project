from mrbet import backtest as bt
from mrbet.models import (
    Baseline,
    Evaluation,
    GameState,
    MarketLine,
    MarketType,
    Period,
    Side,
    Signal,
)
from mrbet.storage import Storage


def _log_flagged(storage, side, line, over_odds, under_odds, ts_state):
    base = Baseline(MarketType.GAME_TOTAL, Period.FULL, 219.0, -110, -110)
    live = MarketLine(MarketType.GAME_TOTAL, Period.FULL, line, over_odds, under_odds)
    ev = Evaluation(
        baseline=base, live=live, state=ts_state, side=side, fair_final=210.0,
        pct_move=(line - 219) / 219, edge_pts=5.0, prob=0.62, implied_prob=0.524,
        ev=0.12, kelly_stake=4.0,
    )
    storage.log(ev, Signal(ev, strong=True, reasons=["test"]))
    return ev


def test_backtest_grades_wins_and_losses(tmp_path):
    db = tmp_path / "obs.sqlite"
    storage = Storage(path=db, event_id="game1")
    state = GameState(Period.FULL, 12.0, 36.0, home_score=18, away_score=22)
    # OVER 187.5 -> with final 224 this WINS.
    _log_flagged(storage, Side.OVER, 187.5, -110, -110, state)
    # OVER 230.0 -> with final 224 this LOSES.
    _log_flagged(storage, Side.OVER, 230.0, -110, -110, state)
    storage.close()

    finals = {"game": {"full": 224}}
    summary = bt.grade(db, finals=finals, event_id="game1")

    assert summary.bets == 2
    assert summary.wins == 1
    assert summary.losses == 1
    assert summary.staked == 8.0
    # +4 * 0.909 (win) - 4 (loss) ~= -0.36
    assert summary.profit < 0
    assert summary.win_rate == 0.5


def test_backtest_push(tmp_path):
    db = tmp_path / "obs.sqlite"
    storage = Storage(path=db, event_id="g")
    state = GameState(Period.FULL, 12.0, 36.0, home_score=18, away_score=22)
    _log_flagged(storage, Side.OVER, 224.0, -110, -110, state)  # integer line == final
    storage.close()

    summary = bt.grade(db, finals={"game": {"full": 224}}, event_id="g")
    assert summary.pushes == 1
    assert summary.profit == 0.0


def test_closing_line_value_without_finals(tmp_path):
    db = tmp_path / "obs.sqlite"
    storage = Storage(path=db, event_id="g")
    state = GameState(Period.FULL, 12.0, 36.0, home_score=18, away_score=22)
    # Flag an OVER at 187.5, then the line drifts back up to 205 (the "close").
    _log_flagged(storage, Side.OVER, 187.5, -110, -110, state)
    _log_flagged(storage, Side.OVER, 205.0, -110, -110, state)
    storage.close()

    summary = bt.grade(db, finals=None, event_id="g")
    # Closing line for the market is the last one (205). The 187.5 OVER beat it.
    assert summary.clv_graded == 2
    assert summary.clv_beat >= 1
    assert summary.avg_clv_pts != 0.0
