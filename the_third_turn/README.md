# The Third Turn

A **decoupled, headless** MLB signal service that flags live-Over opportunities off
the **Time-Through-Order Penalty (TTOP)**: starting pitchers degrade when they face
the top of the order for the 3rd time. Like its sibling `mrbet`, it is a *signal*
system — it flags +EV spots and alerts; **it does not place bets.**

It runs isolated from the `mrbet` NBA code (own folder, own deps, own async runtime)
and has two halves, joined by one artifact (`output/constraints.json`):

```
backtest_thesis.py ──writes──▶ output/constraints.json ──read by──▶ live_engine.py
   (prove the edge)              (the fitted parameters)            (fire alerts)
```

## Install

```bash
pip install -r the_third_turn/requirements.txt
```

## 1. Historical Validator — `backtest_thesis.py`

Pulls MLB Statcast pitch-by-pitch data (via `pybaseball`, cached to disk) and derives,
per starter and plate appearance: **starter identity, lineup slot, times-through-order,
entering pitch count, starter tier**, and per-PA **H / BB / outs / runs**. It measures the
run environment vs the innings-1–3 baseline and runs a **dynamic indicator sweep**.

```bash
python the_third_turn/backtest_thesis.py --seasons 2025            # one season
python the_third_turn/backtest_thesis.py --seasons 2024 2025 2026  # full sample
python the_third_turn/backtest_thesis.py --start 2025-04-01 --end 2025-05-01  # fast slice
```

Outputs (`output/`): `constraints.json`, `indicator_sweep.csv`, `ttop_decision_matrix.csv`,
`run_environment_report.json`.

### Findings (full 2024 + 2025 + 2026-YTD sample)

**The TTOP is real, and the cliff comes EARLIER for weaker arms.** The dynamic sweep,
ranked by Welch t across ~55k+ plate appearances, is topped decisively by
**2nd-time-through vs Back-of-rotation starters** — not the canonical 3rd turn:

| Rank | Indicator | PAs | RA/9 lift | Welch t | p |
|---|---|---:|---:|---:|---:|
| 1 | **TTO2 · top5 · Back** | 25,929 | **+1.42** | 9.8 | 1e-22 |
| 2 | TTO2 · top4 · Back | 20,847 | +1.56 | 9.6 | 6e-22 |
| 3 | TTO2 · top3 · Back | 15,702 | +1.63 | 8.7 | 5e-18 |
| 4 | TTO3 · top4 · All (canonical) | 38,086 | +0.75 | 6.3 | 2e-10 |

The baseball story: **the weaker the starter, the earlier the penalty.** Aces have the
arsenal to fool a lineup a 3rd time; back/mid-rotation and spot starters get hit hard the
*2nd* time through. So the engine **auto-pivots** its live trigger to the sweep's #1 robust
signal (`backtest_thesis.choose_trigger`, gated on p < 1e-6 and ≥ 2000 PAs) and excludes
aces via `starter_tier_filter`. The current fitted trigger is **TTO ≥ 2, slots 1–5, tiers
{Mid, Back}, inning ≥ 3** — recorded in `constraints.top_indicator`. If a future run finds a
different robust #1, the trigger follows it automatically; otherwise it falls back to the
canonical 3rd-turn top-4.

### Run-environment validation (calibrate to *runs*, not ERA)

A live Over pays on **total runs** (earned or not), so we validate Statcast RA/9 against
**true RA/9** (runs allowed) from the MLB Stats API — not ERA. Across the 3-season sample,
329 pitchers: **Pearson r = 0.908**, R² = 0.82 (`true_RA9 ≈ 0.92·RA9 + 0.65`). Statcast
run-attribution is a reliable proxy for actual runs allowed.

## 2. Live Execution Engine — `live_engine.py`

An `asyncio`/`aiohttp` daemon polling three sources concurrently every 30s:

* **Source A — MLB Stats API:** inning, pitcher, pitch count, lineup slot, TTO, **outs,
  base state, starter-on-mound, starter tier**.
* **Source B — FanDuel:** live game totals. *(Replaces DraftKings — see below.)*
* **Source C — Bovada:** live game totals.
* **Fallback — Pinnacle:** used only if FanDuel returns nothing.

It evaluates a **list of independent `TriggerRule`s** (from `constraints.rules`) against
every game. The backtest emits both TTOP archetypes — **`TTO2·Mid/Back`** (weaker arms
cliff at the 2nd turn) and **`TTO3·Mid/Back`** (mid-rotation an inning later). Rules match
`times_through_order` **exactly**, so they never overlap: a Mid starter can fire the TTO2
rule at his 2nd turn *and* the TTO3 rule at his 3rd — two distinct bets. Each rule fires:

* **🟡 ARM (look-ahead)** — `2 outs` + an `8/9` hitter up + one turn short of the target, so
  the target turn **leads off next inning**. Beats the ~10–20s MLB-API latency, giving a
  buffer to read the odds *before* books move at the break.
* **🔴 CONFIRM** — the target turn is actually at bat.

Both require: the **starter still on the mound**, the **fielding bullpen not elite**
(a pull would neutralize the Over), an **RE24 run-environment edge** (live total below the
expected-final anchor by `line_edge_min_runs`), and the starter's tier passing the rule's
`starter_tier_filter` (aces excluded).

A third **`WATCH` rule** (the low-scoring game-script heuristic) is **disabled by default**;
enabled, it logs to console with a `[WATCH_RULE]` prefix and **never** posts to Discord.

**Alerting & ledger:** validated CONFIRM/ARM signals post a formatted **Discord embed**
(**Why** / **Gap** vs RE24 fair / **Pull Risk** / **Score** + game-script / **Latency**).
**Every** fired signal — CONFIRM, ARM, *and* WATCH — is appended to `output/ledger.jsonl`
with a `trigger_type` tag for post-season hit-rate analysis. Each alert carries the MLB
feed's **data age**; a ⚠ warns when it exceeds `max_data_age_seconds` (the feed runs ~20s
behind, which is why the ARM look-ahead exists).

```bash
export DISCORD_WEBHOOK_URL=...                 # optional; without it, console + ledger only
python the_third_turn/live_engine.py           # headless daemon (SIGINT/SIGTERM clean)
python the_third_turn/live_engine.py --once     # one poll, then exit (dry run)
```

## 3. Execution simulation — `simulate_execution.py`

Replays the **exact live predicates** over historical play-by-play (reconstructing per-PA
base/out/score state into a `LiveGameState` and calling the same `evaluate_rule` + RE24 +
rules the engine uses) to report how often the bot fires and how reliable it is.

```bash
python the_third_turn/simulate_execution.py --seasons 2024 2025 2026
python the_third_turn/simulate_execution.py --seasons 2025 --totals-csv closing_lines.csv
```

Outputs `output/report.csv` (**trigger density**, **hit rate**, **conditional hit rate by
rule**) + `output/simulation_ledger.jsonl`. The pregame line (when no real line is supplied) is a
**matchup model** by default — `total = park · Σ_side (SP_RA9·5.3 + PEN_RA9·3.7)/9` from cached
starter/bullpen RA/9 — which deflates the phantom edge of a flat average (`--proxy park` for the
old flat line, `--totals-csv` for real lines, `--real-only` to score only real-line games).

### Same-day check — `replay_today.py`

Baseball Savant publishes a day late, so to check *today's* completed games run:

```bash
python the_third_turn/replay_today.py            # reconstructs state from the MLB Stats API
```

It walks `feed/live` play-by-play, runs the exact rules, and prints which games fired + whether
they went Over. (Base/out RE24 premium is approximated bases-empty; the full Statcast replay runs
next day.)

> ⚠ **Proxy caveat:** no historical live-odds feed is reachable, so the default pregame total
> is a park-adjusted league average. Hit rates measure "does firing predict above-average
> scoring," **not** edge against a sharp closing line — supply `--totals-csv` real lines (or an
> Odds API key) for true EV. The WATCH rows are included so its hit rate is measurable before
> it's ever enabled live.

## Real lines & Discord alerts — `odds_collector.py`, `.env`

Copy `.env.example` → `.env` (git-ignored) and set `DISCORD_WEBHOOK_URL` and `ODDS_API_KEY`
(scripts load `.env` automatically via `shared_piping/envload.py`). Secrets stay in the
environment — never committed.

```bash
python the_third_turn/send_test_alert.py     # post one embed to confirm the webhook
python the_third_turn/odds_collector.py       # snapshot real pregame totals (1 credit)
```

`odds_collector.py` pulls **real** pregame game totals from The Odds API current-odds endpoint
(median Over across US books, sanity-filtered), matches each to its `game_pk`, and appends to
`data/closing_lines.csv` (resumable). Feed that to the simulation for **true** hit rates:

```bash
python the_third_turn/simulate_execution.py --seasons 2025 --totals-csv data/closing_lines.csv --real-only
```

The report then **splits hit rate by `line_source`** (real closing line vs park-average proxy).

> ⚠ **Free-tier reality:** The Odds API free plan does **not** allow historical retro-fill
> (`HISTORICAL_UNAVAILABLE_ON_FREE_USAGE_PLAN`), so past-season closing lines aren't available.
> The collector runs **forward** (1 credit/day) to accumulate real lines as games are played;
> true real-line hit rates therefore build up over time. Retro-filling 2024–25 needs a paid plan.

## Reference tables — `build_reference.py`

Precomputes what the engine loads (from the MLB Stats API; xFIP/FanGraphs are IP-blocked):

```bash
python the_third_turn/build_reference.py --seasons 2025
```

* `config/bullpen_quality.json` — per-team bullpen **RA/9** (relievers = `gamesStarted 0`).
* `config/starter_tiers.json` — `{pitcher_id: Ace|Mid|Back}` by season WHIP.

## Connectivity check — `connection_check.py`

Pings every source once; prints HTTP status / latency / payload size / a parsed sample;
exits non-zero if any **required** source (MLB, FanDuel, Bovada) 403s or fails.

## Tests

```bash
pytest the_third_turn -q     # pure/offline: team_map, headers, RE24 model, ARM/CONFIRM predicates
```

## Notes & honest limitations

* **DraftKings is intentionally excluded** — its API 403s this datacenter IP (an edge/IP-level
  block **User-Agent rotation cannot defeat**; it needs a residential IP/proxy). FanDuel replaces it.
* **RE24 matrix and park factors are static published constants** — tune them against logged
  live data before trusting the run-environment anchor.
* **Bullpen quality is RA/9, not xFIP** (FanGraphs is blocked) — which aligns with the
  runs-not-ERA framing anyway. **Reliever rest/usage fatigue is a phase-2 enhancement.**
* **`constraints.json` is only as good as the sample** — committed values are 2025-only;
  re-run with `--seasons 2024 2025 2026` before trusting live triggers.
* **Live alerts require a running daemon on a persistent host.** `live_engine.py` only pushes
  Discord alerts *while it is running* with `DISCORD_WEBHOOK_URL` set — run it (and a daily
  `odds_collector.py` cron) on an always-on machine during the games. `output/ledger.jsonl` is
  created on the first fire and appends every signal (CONFIRM/ARM/WATCH) for later retraining.
* This tool **only signals**. It never places a wager, and it respects each site's terms via
  personal, low-rate polling.
