from pathlib import Path

from mrbet.config import GameConfig, Settings
from mrbet.engine import Engine, derive_state, points_for
from mrbet.models import GameState, MarketLine, MarketType, Period
from mrbet.odds.manual import ManualProvider

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "config" / "games" / "okc_sas_2026-05-28.yaml"
REPLAY = ROOT / "tests" / "data" / "replay_okc_sas.json"


def test_derive_h1_from_full_state():
    full = GameState(Period.FULL, 12.0, 36.0, home_score=18, away_score=22)
    h1 = derive_state(full, Period.H1)
    assert h1 is not None
    assert h1.period is Period.H1
    assert h1.minutes_remaining == 12.0


def test_derive_h1_closed_after_halftime():
    full = GameState(Period.FULL, 30.0, 18.0, home_score=60, away_score=55)
    assert derive_state(full, Period.H1) is None


def test_points_for_team_total():
    g = GameConfig.load(GAME)
    state = GameState(Period.FULL, 12.0, 36.0, home_score=18, away_score=22)
    okc_line = MarketLine(MarketType.TEAM_TOTAL, Period.FULL, 95.5, -110, -115, team="OKC")
    # OKC is the away team in the config.
    assert points_for(state, okc_line, g) == 22.0


def test_replay_produces_over_flags():
    settings = Settings.load(ROOT / "config" / "settings.yaml")
    game = GameConfig.load(GAME)
    provider = ManualProvider(replay=str(REPLAY))
    engine = Engine(settings, game, provider)

    flags = []
    for snap in provider.snapshots():
        for res in engine.process_snapshot(snap):
            if res.signal:
                flags.append(res.signal)

    # The cold trough (snapshot B) should flag at least the full-game OVER.
    assert flags, "expected at least one flagged opportunity"
    assert any(
        f.evaluation.side.value == "over"
        and f.evaluation.baseline.market_type is MarketType.GAME_TOTAL
        and f.evaluation.baseline.period is Period.FULL
        for f in flags
    )
