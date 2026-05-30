"""Precompute Move%/Edge trajectories for the chart's historical view.

Runs the engine over two games in the batch file — one that fires a signal
(cold-start G7) and one that doesn't (G6) — and writes docs/chart_history.json
with each game's FULL-game-total Move % and Edge pts series. The dashboard can
only fetch files under docs/, so this bakes the trajectories the chart needs.
Re-run if the batch data or thresholds change.
"""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mrbet.cadence import timeout_marks
from mrbet.config import Settings
from mrbet.engine import Engine
from mrbet.historical import JsonFileSource, _game_config_from_dict
from mrbet.models import GameState, Period
from mrbet.odds.base import Snapshot

FULL_KEY = "game_total:full:game"
BATCH = ROOT / "tests" / "data" / "2026_playoffs_batch.json"
OUT = ROOT / "docs" / "chart_history.json"

# (chart key, event_id, label) — one game that fired, one that stayed quiet.
PICKS = [
    ("triggered", "sas_okc_2026-05-30", "G7 SAS@OKC — cold-start reversion (fired)"),
    ("dud",       "okc_sas_2026-05-28", "G6 OKC@SAS — tracked pregame (no signal)"),
]

settings = Settings.load(ROOT / "config" / "settings.yaml")
src = JsonFileSource(BATCH)
by_id = {g["event_id"]: g for g in src.game_dicts()}

games = {}
for key, eid, label in PICKS:
    g = _game_config_from_dict(by_id[eid])
    move, edge = [], []
    for mark in timeout_marks():
        scores = src.score_at(eid, mark)
        lines = src.lines_at(eid, mark)
        if scores is None or not lines:
            continue
        away, home = scores
        state = GameState(period=Period.FULL, minutes_elapsed=mark,
                          minutes_remaining=48.0 - mark, home_score=home, away_score=away)
        snap = Snapshot(state=state, lines=lines, meta={})
        for r in Engine(settings, g, provider=None).process_snapshot(snap):
            b = r.evaluation.baseline
            if f"{b.market_type.value}:{b.period.value}:{b.team or 'game'}" == FULL_KEY:
                move.append({"x": mark, "y": round(abs(r.evaluation.pct_move) * 100, 1)})
                edge.append({"x": mark, "y": round(r.evaluation.edge_pts, 1)})
    games[key] = {"label": label, "move": move, "edge": edge}

OUT.write_text(json.dumps({
    "thresholds": {"pct_move": settings.triggers.pct_move_threshold,
                   "edge_pts": settings.triggers.edge_pts_threshold},
    "games": games,
}, indent=2))
print("wrote", OUT)
for k, v in games.items():
    print(f"  {k:<10} {v['label']}  -> {len(v['move'])} marks")
