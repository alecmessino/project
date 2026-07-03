# Paper 1 — Outline & Draft Skeleton

**Working title:** *Public Information and Market Efficiency in Live MLB Totals Markets:
Do Publicly Observable Baseball Variables Provide Incremental Information Beyond a Sharp
Live Market?*

Status: historical phase complete; this outline maps every section to committed results
(`output/*.json`, `RESEARCH_LOG.md`). Prose is drafted in journal style for the anchor
sections (Abstract, Discussion) and skeletoned elsewhere. Language deliberately hedged
and bound to the experiment (Phase-4 discipline).

---

## Abstract (draft, ~170 words)

Live in-play sports betting markets are large, fast, and — unlike the heavily studied
pregame moneyline — almost unexamined in the market-efficiency literature, particularly
for baseball totals. We ask a single question: do publicly observable baseball state
variables carry *incremental* predictive information about remaining runs beyond the live
total posted by a sharp market? Using 163 MLB games (June 2026) with one-minute live-odds
trajectories (Pinnacle-grade pricing) joined to pitch-level Statcast data and full
play-by-play, we subject a sequence of community hypotheses — times-through-order,
velocity decline, bullpen fatigue, line-drop reversion, alternate-line skew, early-run
under-reaction, and weather/park conditioning — to escalating validation: out-of-sample
cross-validation, conditional (context-controlled) testing, and finally a forecast-
encompassing test against the market itself. No variable survives. A remaining-runs model
built from game state is well-calibrated (R²≈0.22) but adding fatigue terms changes its
error by <0.001 runs; forecast encompassing shows the market's forecast error is not
predictable from any feature we measure (out-of-sample R²≈0). An event-level transfer-
function analysis finds the sharp line adjusts to information shocks by approximately the
correct magnitude. Within the limits of our data, we find no evidence of exploitable
public-information inefficiency, and we characterize the boundary precisely.

---

## 1. Introduction (skeleton)
- Live/in-play betting is now a majority of handle, yet efficiency research concentrates
  on pregame moneylines/spreads; **live totals and calibration are under-studied.**
- MLB is a natural testbed: discrete events with well-established run values (RE24, linear
  weights), pitch-level Statcast, and a strong community prior (TTOP, fatigue).
- **Contribution:** not a betting system — a systematic, escalating-stringency map of
  where public baseball information stops adding value against a sharp live market.
- State the single research question; preview the negative result and its precise scope.

## 2. Related Work (skeleton)
- **TTOP:** continuous familiarity decay, not a fatigue cliff (arXiv 2210.06724).
- **Velocity → performance:** relative velocity ≈ 0.0006 wOBA/mph (Baseball Prospectus);
  velocity–fatigue link (sports-medicine review).
- **Betting-market efficiency:** overreaction / negative autocorrelation in movement
  (Simon 2025); real-time inefficiency design (*Management Science* 2024).
- **Information incorporation / latency:** benchmark-vs-price underreaction (~0.64:1,
  arXiv 2606.07811).
- **Gap:** none combine pitch-level baseball state, live totals, calibration, and
  encompassing against a sharp book.

## 3. Data
- 163 MLB games, June 2026. Live total + O/U prices at ~1-minute cadence (Odds Papi,
  Pinnacle-grade). MLB Stats API play-by-play + boxscore; Statcast `startSpeed`. Weather
  and venue from the feed. Realized finals for grading.
- Derived substrate (`features.py`): runs-by-inning with cause tags, velocity by TTO and
  by pitch-count band, per-team scoring, weather (temp/wind out-in), park factor,
  trailing-3-day bullpen usage (326 team-units).
- Report coverage, cadence, and the single-source caveat up front.

## 4. Methods — the escalating-stringency design (one subsection each)
The organizing principle: each test is *more* stringent than the last.
1. **Model-free reversion** (drop → Over/Under; banded; robustness gates).
2. **Gradient signal** (calibrated logistic replacing the binary gate; leave-one-game-out).
3. **Vector battery** V1 alt-line skew, V2 early-runs anchoring, V3 velocity/team-total,
   V4 bullpen fatigue — each with Wilson CIs.
4. **Calibration engine** — reliability curves, Brier, AUC, ECE; residual = model − implied.
5. **Debiasing** — early-window vs post-treatment velocity (selection control).
6. **Remaining-runs model** — Y=remaining runs on game state (the market's target).
7. **Forecast encompassing (G)** — Y~B, Y~X, Y~B+X; error (Y−B) ~ X; per-feature E+.
8. **Transfer function (A)** — ΔBook/ΔRE by event (RE24 base-out tracked), impulse response.

## 5. Results
**5.1 Hypothesis battery (organize the failures — this is the paper's strength):**

| Hypothesis | Test | Result |
|---|---|---|
| Times-through-order | binary gate + gradient | Refuted (OOS all thresholds −EV) |
| Velocity | debiased early-window | AUC 0.61→**0.52** (selection artifact) |
| Bullpen fatigue | isolated pen innings | No multiplier (gassed ≤ rested) |
| Line-drop reversion | banded + robustness | Not robust (band moves w/ snapshot) |
| Alt-line skew | tail vs efficient-implied | Priced (−EV every hook) |
| Early-run anchoring | post-1st Over | Efficient (~50%) |
| Weather / park | conditional split | Priced (over-adjusted, 46%<50%) |

**5.2 Remaining-runs model:** baseline (progress+tier+bullpen+score) R²=0.224, well
calibrated; **+ fatigue → ΔMAE = −0.001** (no incremental value).

**5.3 Forecast encompassing (G + E+):** market alone R²=0.304 > features (0.279); adding
features changes R² by **−0.017**; book error not predictable OOS (R²=−0.037); every
feature's individual ΔR² ≤ 0.002.

**5.4 Transfer function (A):** ΔRE validated against linear weights (HR 1.34 vs 1.40).
Response ratios ΔBook(+5m)/ΔRE cluster **0.63–0.84** across hit types — *uniform*,
consistent with a measurement low-pass filter rather than a per-event inefficiency; the
sharp line adjusts by approximately the correct magnitude.

## 6. Discussion (draft language)
The finding is **not** "baseball variables don't matter" — they demonstrably predict runs.
It is the sharper claim that a sharp live market **already reflects them**: after
conditioning on the market's own forecast, our variables carry no incremental information.
The uniformity of the transfer-function ratios is evidence about our *measurement pipeline*
(single source + convergence window), not the market. The one non-attenuation anomaly —
pitching changes — reflects a *benchmark* limitation (RE24 does not price reliever quality)
and motivates a live experiment, not a historical claim.

## 7. Limitations (important — write it prominently)
One month; 163 games; ~1-minute snapshots; a single Pinnacle-grade source (so we cannot
separate market latency from feed cadence, nor test cross-book divergence); no retail live
team totals; June-only (no pennant-race / weather-extreme regimes). Claims are bound to
these conditions.

## 8. Future Work → Paper 2
Live market microstructure on the timestamped streams now banking: price discovery /
information network `P(A→B)`, information half-life `τ½`, cross-book leadership,
distribution dynamics (μ/σ/skew/tail evolution), market compression (cross-book variance
spike→collapse), pitching-change repricing.

---

## Figures & tables to produce (Phase 3)
1. Experiment-timeline / escalating-stringency flow diagram.
2. Hypothesis→result summary table (5.1).
3. Reliability curve(s) from the calibration engine.
4. Encompassing bar: R²(market) vs features vs both; per-feature ΔR² (E+).
5. Velocity debiasing: biased vs early-window AUC.
6. Transfer-function elasticity plot: ΔBook vs ΔRE by event, with ratio band.
7. Remaining-runs calibration: predicted vs realized.

## Key references (from the literature scan)
- arXiv 2210.06724 (TTOP continuous vs discontinuity)
- Simon (2025), *Int'l J. Sport Finance* (autocorrelation/overreaction)
- *Management Science* (2024), "Inefficient Forecasts at the Sportsbook"
- arXiv 2606.07811 (real-time underreaction ~0.64:1)
- Baseball Prospectus, relative velocity ≈ 0.0006 wOBA/mph

---

## Collaboration phases (per your proposal)
- **Phase 1 — outline (this document).**
- Phase 2 — draft Abstract → Discussion in journal prose.
- Phase 3 — publication-quality figures/tables (many are one script away from the JSONs).
- Phase 4 — statistical-rigor edit (bind every claim to the experiment).
