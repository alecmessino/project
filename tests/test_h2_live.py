"""Live H2 derivation: providers must surface the settled H1-final so the
engine can split a cumulative score into the 2nd-half slice."""

from pathlib import Path
from types import SimpleNamespace

import mrbet.bovada_feed as bovada_feed
from mrbet.bovada_feed import BovadaProvider
from mrbet.config import GameConfig, Settings
from mrbet.engine import Engine, derive_state
from mrbet.espn import h1_from_competitors
from mrbet.models import GameState, MarketLine, MarketType, Period
from mrbet.odds.base import Snapshot
from mrbet.odds.theodds import MARKET_KEYS, _PERIOD_FOR_KEY, TheOddsProvider

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "config" / "games" / "okc_sas_2026-05-28.yaml"

EVENT = SimpleNamespace(
    home="San Antonio Spurs", away="Oklahoma City Thunder",
    home_key="SAS", away_key="OKC", bovada_event_id="123",
)


def _competitor(home_away: str, q1: int, q2: int) -> dict:
    return {"homeAway": home_away, "linescores": [{"value": q1}, {"value": q2}]}


# --- engine derivation ------------------------------------------------------ #
def test_derive_h2_requires_h1_final():
    full = GameState(Period.FULL, 30.0, 18.0, home_score=60, away_score=55)
    assert derive_state(full, Period.H2) is None


def test_derive_h2_with_h1_final():
    full = GameState(Period.FULL, 30.0, 18.0, home_score=60, away_score=55,
                     h1_home=33, h1_away=30)
    h2 = derive_state(full, Period.H2)
    assert h2 is not None
    assert h2.period is Period.H2
    assert h2.minutes_elapsed == 6.0
    assert h2.minutes_remaining == 18.0
    assert h2.home_score == 27 and h2.away_score == 25


def test_engine_evaluates_h2_market_with_h1_final():
    settings = Settings.load(ROOT / "config" / "settings.yaml")
    game = GameConfig.load(GAME)
    engine = Engine(settings, game, provider=None)
    line = MarketLine(MarketType.GAME_TOTAL, Period.H2, 100.5, -110, -110)

    without_h1 = GameState(Period.FULL, 30.0, 18.0, home_score=60, away_score=55)
    assert engine.process_snapshot(Snapshot(state=without_h1, lines=[line])) == []

    with_h1 = GameState(Period.FULL, 30.0, 18.0, home_score=60, away_score=55,
                        h1_home=33, h1_away=30)
    results = engine.process_snapshot(Snapshot(state=with_h1, lines=[line]))
    assert len(results) == 1
    assert results[0].evaluation.baseline.period is Period.H2


# --- ESPN linescore parsing ------------------------------------------------- #
def test_h1_from_competitors():
    got = h1_from_competitors([_competitor("away", 28, 30), _competitor("home", 25, 27)])
    assert got == (58, 52)


def test_h1_from_competitors_unsettled():
    only_q1 = {"homeAway": "away", "linescores": [{"value": 28}]}
    assert h1_from_competitors([only_q1, _competitor("home", 25, 27)]) is None
    assert h1_from_competitors([]) is None


# --- TheOdds provider ------------------------------------------------------- #
def test_theodds_tracks_h2_market():
    assert MARKET_KEYS["total_h2"] == "totals_h2"
    assert _PERIOD_FOR_KEY["totals_h2"] is Period.H2


def _espn_teams(period: int, clock_secs: float) -> dict:
    return {
        "home": {"homeAway": "home", "score": "60", "team": {"displayName": EVENT.home},
                 "linescores": [{"value": 25}, {"value": 27}]},
        "away": {"homeAway": "away", "score": "55", "team": {"displayName": EVENT.away},
                 "linescores": [{"value": 28}, {"value": 30}]},
        "_status": {"period": period, "clock": clock_secs, "displayClock": "6:00"},
    }


def test_theodds_state_attaches_h1_after_halftime():
    p = TheOddsProvider(EVENT, markets=["total_h2"], api_key="test")
    state = p._espn_state(_espn_teams(period=3, clock_secs=360.0))   # 30 min elapsed
    assert state.h1_away == 58 and state.h1_home == 52


def test_theodds_state_no_h1_before_halftime():
    p = TheOddsProvider(EVENT, markets=["total_h2"], api_key="test")
    state = p._espn_state(_espn_teams(period=2, clock_secs=360.0))   # 18 min elapsed
    assert state.h1_away is None and state.h1_home is None


# --- Bovada provider -------------------------------------------------------- #
def _live_scores(period: int, game_time: str) -> dict:
    return {
        "gameStatus": "IN_PROGRESS",
        "clock": {"periodNumber": period, "gameTime": game_time, "isTicking": True},
        "latestScore": {"visitor": "55", "home": "60"},
    }


def test_bovada_state_attaches_h1_after_halftime(monkeypatch):
    p = BovadaProvider(EVENT, max_polls=1)
    p._raw_event = {"id": "123"}
    monkeypatch.setattr(bovada_feed, "live_h1_final", lambda lg, a, h: (58, 52))
    monkeypatch.setattr(p, "_fetch_scores", lambda eid: _live_scores(3, "6:00"))
    state = p._fetch_state()
    assert state.h1_away == 58 and state.h1_home == 52
    # Cached: a second poll must not re-fetch from ESPN.
    monkeypatch.setattr(bovada_feed, "live_h1_final",
                        lambda lg, a, h: (_ for _ in ()).throw(AssertionError("re-fetched")))
    state = p._fetch_state()
    assert state.h1_away == 58 and state.h1_home == 52


def test_bovada_state_no_h1_before_halftime(monkeypatch):
    p = BovadaProvider(EVENT, max_polls=1)
    p._raw_event = {"id": "123"}
    monkeypatch.setattr(bovada_feed, "live_h1_final",
                        lambda lg, a, h: (_ for _ in ()).throw(AssertionError("fetched too early")))
    monkeypatch.setattr(p, "_fetch_scores", lambda eid: _live_scores(2, "6:00"))
    state = p._fetch_state()
    assert state.h1_away is None and state.h1_home is None
