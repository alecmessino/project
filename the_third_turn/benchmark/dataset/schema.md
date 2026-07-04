# Third Turn Benchmark Dataset (v1) — schema

163 Major League Baseball games, June 2026. The unit of analysis is the **half-inning snapshot**: a
moment at the start of a half-inning at which both the market's live total and the full game state
are observed. All frozen artifacts live under `../../output/` and are recomputable from
`../../data/trajectories.jsonl` (the raw live line + price trajectories) joined to the MLB Stats API
play-by-play.

## The two forecasts (the core of the benchmark)

| symbol | definition | meaning |
|---|---|---|
| `B` | live total − runs already scored | **incumbent forecast** of remaining runs (the market) |
| `Y` | final total − runs already scored | **realized** remaining runs (ground truth) |
| `Y − B` | | the market's **forecast error** — the object a signal must predict to be incremental |

A candidate signal `X` is "incremental" iff it predicts `Y − B` out-of-sample (rung 6).

## Snapshot features (`output/encompass_cache.json`, n = 2,505)

Each record is one snapshot with `Y`, `B`, `game` (group id for leave-one-game-out), and the
candidate features below. Features are constructed without reference to the outcome.

| feature | description |
|---|---|
| `vdrop` | starter velocity decline, early-window (first 20 pitches vs next 20) |
| `back`, `mid` | starter tier indicators (season-baseline quality buckets) |
| `pen` | fielding team's bullpen runs allowed per nine |
| `tto` | times through the order for the due batter |
| `pc` | starter cumulative pitch count |
| `temp`, `wind` | temperature; signed wind (out − in) |
| `park` | park run factor |
| `inning` | inning number |

## Event stream for the transfer function (`output/program_a_cache.json`, n = 6,414)

Each record is one in-game event with `type`, `dre` (ΔRE = runs scored + ΔRE24, Tango base-out run
expectancy), and `d` (the converged change in the live total at +1 and +5 minutes). Event types:
`home_run`, `triple`, `double`, `single`, `walk`, `hit_by_pitch`, `pitching_change`.

## Remaining-runs snapshots (`output/remaining_snapshots.json`, n = 2,859)

Per half-inning state for the remaining-runs baseline model: `inn_remaining`, `tto`, `pitches`,
`starter_on`, `back`, `mid`, `pen`, `score_diff`, `remaining` (target), `game`.

## Frozen result artifacts

| file | what |
|---|---|
| `output/encompass.json` | encompassing R²(market/features/both), per-feature incremental ΔR², book-error OOS R² |
| `output/program_a.json` | transfer-function ΔRE and ΔBook by event type |
| `output/remaining_runs.json` | remaining-runs model MAE/R², with and without fatigue terms |
| `output/calibration.json` | calibration + velocity-debiasing AUCs |

## Caveats (see the paper's Limitations)

Single month; single Pinnacle-grade source at ~1-minute cadence (cannot separate latency from
cadence); single-book benchmark; static RE24/park values. The dataset characterizes the boundary
precisely under these conditions and makes no claim of seasonal or cross-sport generality.
