# The Third Turn — Research Log

Running record of every hypothesis tested, the result, and what's still open. All numbers
are from the committed `output/*.json` result files. Sample = 163 real MLB games (June 2026)
with live line + price trajectories (Odds Papi) joined to play-by-play + Statcast velocity
(MLB Stats API), unless noted. Breakeven at −110 = **52.4%**.

---

## TL;DR

- **No proven +EV signal exists yet.** Every static/handicapping edge we tested is priced
  by the market. The pitcher-fatigue / TTOP thesis was refuted **three independent ways**.
- **The one hypothesis still standing** is *in-play information latency* — does the live
  line lag a sharp in-game signal before adjusting? That needs live data (now banking).
- The project has shifted from "find a betting angle" to **measuring market calibration
  error** (model P vs sportsbook implied P vs realized), which is the more robust frame.

---

## Results — everything tested

| # | Hypothesis | n | Key result | Verdict |
|---|---|---|---|---|
| 1 | **Legacy TTO binary gate** (Mid/Back starter, 2nd/3rd time through, edge vs anchor) | 163 | At/below breakeven on real Pinnacle lines | ❌ Not +EV |
| 2 | **Simple drop → Over** (bet Over at end-of-3rd after ≥X% line drop) | 78–81 | 40% at any drop; ≤44% at every threshold; all below breakeven. Final avg **+0.69** above the dropped line but right-skewed (lose-small/win-big) | ❌ Refuted |
| 3 | **Drop → Under** (flip side) | 65–81 | Looked strong cumulatively (60% overall, 63% on ≥10% drops) but **banded + robustness testing killed it**: not monotonic, doesn't survive a snapshot-inning change, concentrated in the recent half of the sample | ❌ Not robust |
| 4 | **Gradient signal** (soft P(Over) replacing the binary gate) | 564 | TTO3 coef **+0.43** (physics detectable), but OOS every threshold −EV (P≥0.50 → 34.6%, −35 units) | ❌ Refuted |
| 5 | **V1 · Alt-line skew** (buy Over at plus-money hooks to catch the fat tail) | 161 | Distribution right-skewed (skew **+1.36**) but empirical win% < efficient-implied at **every** hook (line+0..+3); EV negative throughout | ❌ Tail is priced |
| 6 | **V2 · Early-runs anchoring** (2+ runs in 1st → Over under-reaction) | 46 | Over **50%**, market efficient; **49/50 explosions are hit-driven** (no fluky-runs population to fade) | ❌ Refuted |
| 7 | **V3 · Velocity → team total** | 163 / 326 | Facing-team runs rise with starter velocity drop (3.9→5.3 across 0→2-3 mph); isolating the **team total sharpens signal** (Cohen's d **0.28** vs 0.19 for game total) | ⚠️ Alive → later debiased (#10) |
| 8 | **V4 · Bullpen fatigue multiplier** (gassed pen amplifies the cliff) | 326 | Cliff + gassed pen **6.90** vs cliff + rested **7.70**; isolating the pen's own innings also flat/wrong-way | ❌ No multiplier |
| 9 | **V5 · Juice/latency arbitrage** | — | Forward-only; multi-book panel banking | ⏳ Open |
| 10 | **Velocity debiasing** (early-window vs post-treatment) | 272/319 | Biased `vel_drop_13` (TTO1→3) AUC **0.61**, but the clean early-window signal (pitches 1-20 vs 21-40) is AUC **0.52** — barely above coinflip. **The edge was largely selection bias** (a big drop only exists if the starter survived to get shelled) | ❌ Signal ≈ artifact |
| 11 | **Expected remaining runs** (the model side of the residual) | 2,859 snaps | Baseline (game progress + tier + bullpen + score) is **well-calibrated**, R²=**0.226**. Adding fatigue (TTO, pitch count, starter-in) changes MAE by **−0.001** — nothing | ❌ Fatigue adds zero |
| 12 | **Project 3 · Distribution/tail calibration** (Pinnacle implied vs realized, PIT) | live | Harness built; 0 graded yet (games in progress). Accumulates nightly | ⏳ Open |
| 13 | **Conditional under-reaction** (edge only in hitter-friendly weather/park?) | 163 | No slice clears breakeven; baseline hitter-friendly Overs hit **46% < 50%** neutral — the market **over-adjusts** for observable context | ❌ Context is priced |
| 14 | **Project G · Forecast encompassing** (does the book contain our features?) | 2,505 snaps | Market alone R²=**0.304** beats our features (0.279); adding features to the market changes R² by **−0.017**. The book's forecast error (final − live line) is **not predictable** OOS (R²=−0.037). **E+** per-feature: every feature's incremental ΔR² beyond the market is **≤ 0.002** (bullpen best at +0.0018; velocity/tier/park all ≤0) | ❌ **Book encompasses everything we measure** |

**Pivotal conclusion (G + E+):** the sportsbook forecast statistically **encompasses every public baseball variable we can measure.** Per the research design, this converges the project onto **market microstructure** — latency, cross-book divergence, transient state-specific miscalibration — not discovering another baseball variable. All three are live-data-gated (banking now).

| 15 | **Program A · Transfer function** (does the line move by the *correct amount*?) | 6,414 events | ΔRE = runs + ΔRE24 (validated vs linear weights). Response ratio ΔBook(+5m)/ΔRE by event: HR **0.81**, 3B 0.84, 2B 0.64, 1B 0.72, BB 0.63 — hits cluster **0.64–0.84**, roughly *uniform* (⇒ the sub-1 level is single-source/convergence attenuation, not a per-event edge). Line takes >1 min to converge (+1m ≈ half of +5m). Pitching change **0.12** but RE24 can't benchmark it (ignores reliever quality) | ✅ Sharp market adjusts ~correctly; **historical phase complete** |

**Historical phase complete — precise conclusion.** *Within the limits of our data (163 games, ~1-minute historical odds snapshots, one Pinnacle-grade source), we find no evidence that publicly observable baseball state variables provide incremental predictive information beyond the live market.* We deliberately bind the claim to the experiment rather than asserting universal efficiency.

Program A adds a methodological point: the response ratios are **remarkably stable** (0.63–0.84 across every hit type). That uniformity is evidence about the **measurement pipeline** — a low-pass filter (single source + convergence window attenuating every event equally) — *not* about market inefficiency. Its consistency strengthens the experiment's credibility. The one non-attenuation anomaly, pitching changes, is a *benchmark* gap (RE24 can't price reliever quality) and is a live experiment, not a historical result.

## Forward agenda — live market microstructure (all live-data-gated)

The project has crossed from sports analytics into **price-discovery / information-processing** research. These run on the timestamped odds + game-state + implied-distribution streams now banking; each needs days–weeks of accumulation.

1. **Price discovery / information network** — how does a shock propagate *across* books? Estimate the directed graph `P(A→B)` (movement in A precedes B). Who leads, who follows.
2. **Information half-life (τ½)** — per event type, the time for 50% of the eventual adjustment. A measurable market characteristic (e.g. HR vs pitching change vs injury may differ).
3. **Cross-book price leadership** — Pinnacle vs FanDuel/Bovada move-order and lag distribution; the *tradable* version (bet the laggard / a derivative market).
4. **Distribution dynamics (flagship)** — not just μ: how do σ, skew, and tail probabilities evolve after each event? Markets often update the mean better than the higher moments — the Pinnacle implied-distribution panel is built to test this.
5. **Market compression (new)** — cross-book variance spikes at a shock then collapses as books update. Measures *when disagreement exists* — arguably more actionable than move-order alone.
6. **Pitching-change repricing** — does the live line correctly reprice the run environment when a pitcher changes? (The one lead Program A surfaced; RE24-blind, so a quality-aware model could differ.)

**Stopping rule:** if cross-book propagation is effectively instantaneous and distributional calibration is accurate, the live market is highly efficient under the conditions measured. If persistent lags or systematic distributional miscalibration appear, that's a market mechanism to evaluate for economic significance. Either outcome is a falsifiable, publishable result.

**Fatigue/TTOP edge refuted 3×:** V4 bullpen (#8), velocity debiasing (#10), remaining-runs fatigue terms (#11). Consistent with the literature.

---

## Literature scan (what's known / open)

- **No published live-MLB-totals calibration study** — this niche is genuinely open. Field
  methods: reliability curves, Brier, log-loss, CLV, change-autocorrelation.
- ⚠️ **The TTOP "cliff" is not supported** — decay is *continuous* and driven by batter
  **familiarity**, not a fatigue cliff (arXiv 2210.06724). Our own results agree.
- Velocity → offense is real but **small** (~0.0006 wOBA/mph, BP). Real-time markets
  **underreact ~0.64-for-one** to new info (arXiv 2606.07811) — a latency template.
- The Odds API historical in-play data exists back to mid-2020 but requires a **paid plan**.

---

## Infrastructure (durable, on the branch)

- **24/7 Actions runner** (`the_third_turn_live.yml`) — self-re-arming ~5.5h loop, commits
  every 15 min, independent of any session. Banks four streams:
  - `ledger.jsonl` — legacy-signal fires
  - `book_panel.jsonl` — FanDuel/Bovada **game-total** line movements (change-only)
  - `team_total_panel.jsonl` — Pinnacle per-team **implied run distribution** (mean/σ/skew) + game state
  - `game_state_panel.jsonl` — every game-state change (inning/outs/score/base-out/TTO/pitch-count) for matching odds↔events by timestamp
- **Calibration engine** (`calibration.py`) — market side (`implied_over` from a Pinnacle
  distribution), diagnostics (reliability curve, Brier, AUC, ECE), residual = model − implied.
- **Expected-remaining-runs model** (`remaining_runs.py`) — the velocity-free model side.
- **Feature substrate** (`features.py`) — per game: runs-by-inning + cause, velocity by TTO
  **and** by pitch-count band, per-team scoring, cliff timing, **weather** (temp/wind
  out-in), **park factor**, bullpen usage.
- **Ripeness monitor** — Discord ping when the live sample crosses ~50 cliff events.

---

## Data assets

- `data/trajectories.jsonl` — 163 games, live line + O/U price series.
- `output/features_cache.json` — full per-game features (committed, ~2.7 MB).
- `output/bullpen_cache.json` — trailing-3-day reliever usage, 326 team-units.
- **Live banking (accumulating):** book panel, team-total distributions, game-state — all
  matched by timestamp for the latency/calibration studies.

---

## Still open / untested (ideas to investigate)

1. **In-play information latency** — the live hypothesis still standing. Does the live line
   lag a sharp in-game signal (velocity crater, sudden run cluster) before adjusting?
   *Needs live-velocity capture (not yet in the daemon) + banked data.*
2. **Cross-book divergence** — with FanDuel/Bovada vs Pinnacle matched by timestamp, who
   moves first and by how much? Bet the laggard. The tradable version of the latency question.
3. **Event study (T=0)** — treat each run/XBH/pitching-change as t=0; measure book movement
   at t+1..t+20s vs the model's expected-run change. Direct market-response measurement.
4. **First-5-innings (F5) totals** — Pinnacle exposes period totals (`s;1;ou`). F5 **isolates
   the starters** (no bullpen noise), a cleaner target for any pitcher signal than full-game.
   *Untested and well-matched to the thesis.*
5. **PIT conditioned on state** — once live distributions bank, test PIT uniformity
   *specifically in the post-cliff state*; non-uniform there = the miscalibration to hunt.
6. **Distribution shape, not mean** — does the book's implied **skew/tail** update correctly
   after state changes even when the mean is right? (Project 3, live.)
7. **Umpire strike-zone effects** on totals — public but sometimes slow to price. Untested.
8. **Live team totals via a paid Odds API tier / DK access** — would unlock retail-lag
   (Project 1) and historical in-play (run the calibration study now vs. banking for weeks).

---

## Standing caveats

- Everything historical is **n=163** (June 2026). Banded/sub-sliced conclusions are thin —
  always read the Wilson CIs.
- Historical backtests are vs **Pinnacle** (sharpest book) — the hardest benchmark.
- Live team totals are **not offered by retail** in the feeds we scrape (DK 403s our IP);
  Pinnacle's implied distribution is our stand-in.
- The legacy Discord alerts fire from the **refuted** binary gate — informational, not +EV.
