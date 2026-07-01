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

It fires **two** alert types (both keyed to the fitted `times_through_order`, currently 2):

* **🟡 ARM (look-ahead)** — `2 outs` + an `8/9` hitter up + that batter one turn short of
  the target, so the top-of-order target turn **leads off next inning**. This beats the
  ~10–20s MLB-API latency, giving a buffer to read the odds *before* books move at the break.
* **🔴 CONFIRM** — the top-of-order target turn is actually at bat.

Both require, beyond the state match:

1. **the starter is still on the mound** (thesis void if a reliever is already in),
2. **the fielding bullpen is not elite** (`RA/9 ≥ bullpen_elite_ra9`) — an elite pen means
   a pull would neutralize the Over,
3. **an RE24 run-environment edge**: the live total sits below the expected-final anchor
   (base level from the pregame total × innings-remaining, plus a park-scaled situational
   premium from the **RE24 base/out matrix** and the backtested **TTOP multiplier**) by at
   least `line_edge_min_runs`,
4. (optional) the starter's tier passes `starter_tier_filter`.

```bash
python the_third_turn/live_engine.py          # headless daemon (SIGINT/SIGTERM clean)
python the_third_turn/live_engine.py --once    # one poll, then exit (dry run)
```

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
* This tool **only signals**. It never places a wager, and it respects each site's terms via
  personal, low-rate polling.
