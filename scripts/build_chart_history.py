"""Precompute Move%/Edge trajectories for the chart's historical view.

The dashboard (served from docs/) can only fetch files under docs/, so this
script bakes the trajectories for the chart's "Historical: Triggered Game" and
"Historical: Dud Game" selector options into docs/chart_history.json.

For the scaffold we synthesize two illustrative MLB scenarios. Once you wire a
real live poller and capture archive, replace the synthetic generators here with
real per-half-inning records.
"""

from __future__ import annotations

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from triggers import (   # noqa: E402  (path mutated above)
    Baseline,
    GameState,
    HALF_INNINGS_PER_GAME,
    Half,
    MarketLine,
    MarketType,
    Period,
    evaluate_market,
    load_settings,
)

OUT = ROOT / "docs" / "chart_history.json"


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #
def _state_at(half_idx: int, away_runs: int, home_runs: int) -> GameState:
    """Build a state at the END of a given half-inning (1..18)."""
    inning = (half_idx - 1) // 2 + 1
    half = Half.TOP if half_idx % 2 == 1 else Half.BOTTOM
    # outs=3 would advance the half — we represent end-of-half as outs=0 in the
    # next half. To keep `half_innings_elapsed` clean, we move to the next slot.
    if half is Half.TOP:
        return GameState(inning=inning, half=Half.BOTTOM, outs=0,
                         away_runs=away_runs, home_runs=home_runs)
    return GameState(inning=inning + 1, half=Half.TOP, outs=0,
                     away_runs=away_runs, home_runs=home_runs)


def trajectory(
    pregame_total: float,
    away_runs_at: dict[int, int],
    home_runs_at: dict[int, int],
    live_line_at: dict[int, float],
    model,
) -> dict:
    """Replay a game across the 18 half-innings, emit FULL-game Move%/Edge series."""
    base = Baseline(MarketType.GAME_TOTAL, Period.FULL, pregame_total, -110, -110)
    move, edge = [], []
    for half_idx in sorted(live_line_at):
        state = _state_at(half_idx, away_runs_at.get(half_idx, 0),
                          home_runs_at.get(half_idx, 0))
        live = MarketLine(MarketType.GAME_TOTAL, Period.FULL,
                          live_line_at[half_idx], -110, -110)
        ev = evaluate_market(base, live, state, state.total_runs(), model)
        move.append({"x": half_idx, "y": round(abs(ev.pct_move) * 100, 1)})
        edge.append({"x": half_idx, "y": round(ev.edge_runs, 2)})
    return {"move": move, "edge": edge}


# --------------------------------------------------------------------------- #
# Main                                                                        #
# --------------------------------------------------------------------------- #
def main() -> None:
    model, triggers = load_settings(ROOT / "settings.yaml")
    thresholds = {"pct_move": triggers.pct_move_threshold,
                  "edge_runs": triggers.edge_runs_threshold}

    # ---- triggered: books slash on a mid-game shutout, model still bullish -- #
    # Pregame 8.5; both teams score normally early (4 runs through 4 innings),
    # then a 4-inning shutout. Books panic and cut the live line to 6.5 around
    # half_idx 10. Our model — anchored to pregame pace + still-positive
    # half-game pace — projects ~9 runs left, so OVER has 3+ runs of edge.
    # cumulative runs (away+home) by half_idx: 0,1,2,3,4,5,5,5,5,5,5,6,7,8,9,10,10,10
    # Hot early scoring, then a 5-inning shutout — books cut to 6.5; model is still
    # anchored to pregame 8.5 and the strong early pace, so OVER edge stays >2.5r.
    triggered = trajectory(
        pregame_total=8.5, model=model,
        away_runs_at={1:0,2:0,3:1,4:1,5:2,6:2,7:2,8:2,9:2,10:2,
                      11:2,12:3,13:3,14:4,15:4,16:5,17:5,18:5},
        home_runs_at={1:0,2:1,3:1,4:2,5:2,6:3,7:3,8:3,9:3,10:3,
                      11:3,12:3,13:4,14:4,15:5,16:5,17:5,18:5},
        live_line_at={1:8.5, 2:8.5, 3:8.5, 4:8.5, 5:8.5,
                      6:8.0, 7:7.5, 8:7.0, 9:6.5, 10:6.5,
                      11:7.0, 12:7.5, 13:8.0, 14:8.5, 15:9.0,
                      16:9.5, 17:10.0, 18:10.5},
    )
    # ---- dud: book tracks the actual pace, line barely moves --------------- #
    dud = trajectory(
        pregame_total=8.5, model=model,
        away_runs_at={1:0,2:1,3:1,4:2,5:2,6:2,7:3,8:3,9:3,10:4,
                      11:4,12:4,13:4,14:5,15:5,16:5,17:5,18:5},
        home_runs_at={1:0,2:0,3:1,4:1,5:2,6:2,7:2,8:3,9:3,10:3,
                      11:3,12:4,13:4,14:4,15:4,16:5,17:5,18:5},
        live_line_at={i: 8.5 for i in range(1, 9)} |
                     {i: 9.0 for i in range(9, 19)},
    )

    payload = {
        "thresholds": thresholds,
        "games": {
            "triggered": {
                "label": "Synthetic — pitchers duel reversion (fired)",
                **triggered,
            },
            "dud": {
                "label": "Synthetic — pace-tracking line (no signal)",
                **dud,
            },
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2))
    print(f"wrote {OUT}")
    for k, g in payload["games"].items():
        last_m = g["move"][-1] if g["move"] else None
        last_e = g["edge"][-1] if g["edge"] else None
        print(f"  {k:<10} {g['label']}  -> move={last_m} edge={last_e}")


if __name__ == "__main__":
    main()
