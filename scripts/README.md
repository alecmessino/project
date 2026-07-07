# scripts/ — by project

Build/ops helpers for the monorepo, grouped by project. Files are **not** moved here (17
workflows and various docs reference `scripts/<name>` paths); this index just labels them.
Run from the repo root.

## 🪵 Driftwood (`drift`) — site build, research sweeps, ops
| Script | What it does |
|---|---|
| `sync_docs.py` | Re-render `docs/*.html` from the `src/drift/web/*.html` templates, preserving injected `window.__STATE__`; also copies `driftwood.css`. The no-network way to ship template/CSS edits. |
| `stamp_provenance.py` | Refresh `docs/_provenance.json` (build commit, data fingerprint, claim→source map). |
| `tax_alpha.py` | Tax-alpha / after-tax modeling used by the site's figures. |
| `og_cards.mjs`, `og_states.mjs` | Regenerate Open Graph social cards for the site / state pages (Playwright). |
| `shots.py` | Visual-QA screenshot harness for the site (Playwright). |
| `set_domain.py` | Set/refresh the Pages custom domain (writes `docs/CNAME`); see `OPERATIONS.md`. |
| `slow_sweep.py` | Slow-sleeve validation sweep (fast vs 40/60 vs 35/65), after-tax. |
| `tilt_sweep.py`, `tilt_optimize.py` | Region/factor tilt sweeps + optimizer over the cross-sectional book. |
| `id_sweep.py` | Information-Discreteness (Frog-in-the-Pan) validation sweep — internal R&D. |

## 🏀 mrbet — live NBA ops, backtest/board data, alerts
| Script | What it does |
|---|---|
| `live_run.py` | Live game loop runner. |
| `board_update.py` | Discover a league's Bovada slate → `docs/board.json`. |
| `gh_pages_update.py` | Cadence-aware forward-capture poller → `docs/state.json` + `docs/forward.json`. |
| `grade_forward.py` | Auto-grade the forward-capture ledger once ESPN reports finals. |
| `build_backtest_json.py` | Precompute the backtest/calibration report → `docs/backtest.json`. |
| `build_chart_history.py` | Bake chart trajectories → `docs/chart_history.json`. |
| `season_ledger.py` | Render `docs/season.json` → a human-readable Markdown ledger. |
| `fetch_historical_odds.py` | Pull historical odds for backtesting. |
| `game_sentinel.py`, `sentinel_watch.py` | Auto-start / watchdog for continuous live-game coverage. |
| `notify_test.py` | Verify notification secrets + send a test alert. |
| `verify_bovada_basketball.py`, `verify_bovada_live.py` | Bovada line/coverage checks. |
| `hot_push.sh` | Deploy helper. |

> ⚾ `the_third_turn` has its own scripts under `the_third_turn/`.
>
> Best-effort map — if any script is misfiled, correct it here; the source of truth is what
> each script imports/writes.
