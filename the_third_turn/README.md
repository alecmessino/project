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
entering pitch count**, and per-PA **H / BB / outs / runs**. It then compares a
window of interest to the innings-1–3 baseline and prints a decision matrix.

```bash
python the_third_turn/backtest_thesis.py --seasons 2025            # one season
python the_third_turn/backtest_thesis.py --seasons 2024 2025 2026  # full sample
python the_third_turn/backtest_thesis.py --start 2025-04-01 --end 2025-05-01  # fast slice
```

Outputs (in `output/`): `ttop_decision_matrix.csv`, `era_calibration_report.json`,
and `constraints.json` (consumed by the engine).

### Findings (full 2025 season, 80k+ starter PAs)

| Window | BF | WHIP | RA/9 | WHIP lift | RA/9 lift |
|---|---:|---:|---:|---:|---:|
| Innings 1-3 (baseline) | 64,729 | 1.293 | 4.37 | — | — |
| **3rd time thru, top 4** | 15,002 | **1.414** | **5.02** | **+0.120** | **+0.65** |
| 3rd/top4 & PC>75 | 6,775 | 1.370 | 5.01 | +0.076 | +0.64 |
| 3rd/top4 & PC>85 | 1,938 | 1.351 | 5.19 | +0.058 | +0.82 |
| 3rd/top4 & PC>90 | 927 | 1.332 | 4.75 | +0.038 | +0.38 |

* **The TTOP is real:** the 3rd-time-through-top-4 window allows +0.120 WHIP and
  +0.65 RA/9 over innings 1–3.
* **The `>75 vs >90` question:** the WHIP edge is *larger* at **PC>75** (+0.076) than
  PC>90 (+0.038), so the engine uses `pitch_count_threshold=75`. Note the honest
  nuance: **layering a pitch-count filter on top of TTO *weakens* the WHIP edge**
  (survivorship — a manager only lets an effective starter reach 90+ pitches the 3rd
  time through). The dominant driver is the time-through-order itself, not raw pitch
  count. RA/9 (runs) peaks a little later, at PC>85.

### ERA calibration (second source)

Window-level *earned* runs are a scorer judgment, so the backtest computes **exact
WHIP** and **RA/9** (runs) from Statcast and validates RA/9 against **true ERA** from
the **MLB Stats API** (FanGraphs and the Chadwick register are IP-blocked here). Full
season, 224 pitchers:

* RA/9 → true ERA: **Pearson r = 0.928**, R² = 0.86, p ≈ 2e-97
* Statcast RA/9 vs true RA/9: r = 0.948 · Statcast WHIP vs true WHIP: r = 0.936
* Regression: `true_ERA ≈ 0.972 · RA9 + 0.172`

**Takeaway:** RA/9 is a reliable proxy for true ERA — the quick metric can be trusted.

## 2. Live Execution Engine — `live_engine.py`

An `asyncio`/`aiohttp` daemon that polls three sources concurrently every 30s:

* **Source A — MLB Stats API:** live inning, current pitcher, pitch count, lineup slot,
  times-through-order.
* **Source B — FanDuel:** live game totals. *(Replaces DraftKings — see below.)*
* **Source C — Bovada:** live game totals.
* **Fallback — Pinnacle:** sharp game totals, used only if FanDuel returns nothing.

It fires an alert (once per game/pitcher/inning) when the **live state matches the
backtested constraints AND the Over is still cheap**:

```
inning ≥ min_inning (5)  AND  TTO ≥ 3  AND  slot ∈ {1,2,3,4}
AND  pitch_count > 75  AND  (pregame_total − live_total) < 1.5
```

The last clause means the market hasn't already faded the total by ≥1.5 runs, so the
Over still has value. The trigger predicate (`evaluate`) is a **pure function** and is
unit-tested offline.

```bash
python the_third_turn/live_engine.py          # headless daemon (SIGINT/SIGTERM clean)
python the_third_turn/live_engine.py --once    # one poll, then exit (dry run)
```

## Connectivity check — `connection_check.py`

```bash
python the_third_turn/connection_check.py
```

Pings every source once, prints HTTP status / latency / payload size / a parsed sample,
and exits non-zero if any **required** source (MLB, FanDuel, Bovada) 403s or fails.

## Tests

```bash
pytest the_third_turn -q     # pure, offline: team_map, header rotation, trigger predicate
```

## Notes & honest limitations

* **DraftKings is intentionally excluded.** Its API returns **403** to this datacenter
  IP — an edge/IP-level block that **User-Agent rotation cannot defeat** (rotation only
  beats header filtering; it needs a residential IP/proxy). FanDuel replaces it.
* **Book feeds are undocumented public JSON** and can change shape or geo-block; every
  adapter degrades gracefully (a failed source never kills the poll loop).
* **`constraints.json` is only as good as the sample.** The committed values are from
  2025 alone; re-run with `--seasons 2024 2025 2026` before trusting live triggers.
* This tool **only signals**. It never places a wager, and it respects each site's
  terms via personal, low-rate polling.
