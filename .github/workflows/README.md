# .github/workflows/ — by project

The 17 scheduled/CI workflows span all three projects. Grouped here for legibility (the
files are named per GitHub's convention; not renamed).

## 🪵 Driftwood (`drift`) — site build, deploy, validation
| Workflow | Role |
|---|---|
| `drift-pages.yml` | Refresh Driftwood exhibits (keyless, Yahoo) — the nightly site rebuild. |
| `pages.yml` | Deploy `docs/` to GitHub Pages. |
| `ci.yml` | CI (runs tests + `scripts/shots.py` visual QA). |
| `validate.yml` | Validate methodology on real data (`scripts/slow_sweep.py`). |
| `tilt-real-sweep.yml` | Tilt hybrid sweep on real data (`scripts/tilt_sweep.py`). |

## 🏀 mrbet — live NBA ops (scheduled)
| Workflow | Role |
|---|---|
| `backtest.yml` | Refresh backtest data (`build_backtest_json.py`, `build_chart_history.py`). |
| `board.yml` | Refresh tonight's board (`board_update.py`). |
| `poll.yml` | Update live odds (`gh_pages_update.py`, `grade_forward.py`). |
| `live.yml`, `live_game_tracker.yml` | Live game loops (`live_run.py`). |
| `game_sentinel.yml`, `sentinel_watch.yml` | Auto-start + watchdog for live coverage. |
| `pregame_lock.yml` | Pregame lock-in of final closing lines. |
| `midnight_reset.yml` | Midnight reset → load the next slate. |
| `notify_test.yml` | Verify secrets + send a test alert. |

## ⚾ the_third_turn
| Workflow | Role |
|---|---|
| `the_third_turn_live.yml` | Live MLB ledger (24/7 self-rearming). |

## Housekeeping
| Workflow | Role |
|---|---|
| `migrate-scaffold.yml` | One-shot manual migration that pushes the `mlb-scaffold-export` branch to the `alecmessino/fair-value-territory` repo. Safe to delete once the migration is done. |
