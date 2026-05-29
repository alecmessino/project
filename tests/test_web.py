import json
from pathlib import Path

from mrbet.config import GameConfig, Settings
from mrbet.engine import Engine
from mrbet.odds.manual import ManualProvider
from mrbet.web.server import DashboardState

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "config" / "games" / "okc_sas_2026-05-28.yaml"
REPLAY = ROOT / "tests" / "data" / "replay_okc_sas.json"


def test_dashboard_state_accumulates_rows_and_signals():
    settings = Settings.load(ROOT / "config" / "settings.yaml")
    game = GameConfig.load(GAME)
    engine = Engine(settings, game, provider=None)
    state = DashboardState(game)

    for snap in ManualProvider(replay=str(REPLAY)).snapshots():
        results = engine.process_snapshot(snap)
        state.update(snap, results)
        for r in results:
            if r.signal:
                state.add_signal(r.signal)

    payload = json.loads(state.to_json())
    assert payload["header"]["away"] == "OKC"
    assert payload["header"]["away_score"] is not None
    assert payload["rows"], "expected market rows in the last snapshot"
    # The cold trough flags at least the full-game OVER.
    assert any("OVER" in s["title"] and "FULL" in s["title"] for s in payload["signals"])


def test_dashboard_poller_fires_notifications():
    # The dashboard must alert (not just display) when a market flags.
    from mrbet.web.server import _poller

    settings = Settings.load(ROOT / "config" / "settings.yaml")
    game = GameConfig.load(GAME)
    engine = Engine(settings, game, provider=None)
    state = DashboardState(game)
    provider = ManualProvider(replay=str(REPLAY))

    sent = []

    class FakeNotifier:
        def maybe_notify(self, signal):
            sent.append(signal)

    _poller(state, engine, provider, FakeNotifier(), log=False)
    assert sent, "dashboard poller should fire notifications on flagged signals"


def test_dashboard_row_shape():
    settings = Settings.load(ROOT / "config" / "settings.yaml")
    game = GameConfig.load(GAME)
    engine = Engine(settings, game, provider=None)
    state = DashboardState(game)
    snap = next(ManualProvider(replay=str(REPLAY)).snapshots())
    state.update(snap, engine.process_snapshot(snap))
    row = json.loads(state.to_json())["rows"][0]
    for key in ("market", "book", "pre", "live", "move_pct", "side", "fair", "edge", "prob", "ev", "stake", "flagged"):
        assert key in row
