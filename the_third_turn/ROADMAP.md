# The Third Turn — Research Roadmap and Submission Plan

Owner: Alec Messino. Last updated: July 2026.

Scope: what remains to get **Paper 1** submission-ready, the **venues** it can go to (with timing
and requirements), and the **forthcoming-papers** program. This is a planning document, not a
protocol; the method lives in `protocol/` and the killed-hypothesis record in `RESEARCH_LOG.md`.

Current status stamps (from `version.py`): Protocol **1.0** · Collector **1.1** (FanDuel
market-`inPlay` fix + status capture) · Benchmark Dataset **2026.06** (the frozen Paper-1 month).

---

## Operating cadence — set 2026-07-19 (two-week horizon)

Owner directive. The project is in disciplined accumulation, not output.

1. Continue daily governance reviews (v4 format + block-typing + Inference Readiness).
2. Keep the collector **untouched** unless an Engineering-Debt or Research-Debt item requires it.
3. Produce **one SR-1 Gate Design Review** — ✅ done (`ops/SR1_GATE_DESIGN_REVIEW.md`, no change).
4. Produce **one Book Characterization Report** — ✅ v0.1 done (`ops/BOOK_CHARACTERIZATION.md`);
   v0.2 (event-aligned leadership) is the next characterization step.
5. **Do not begin Paper 2.** Everything else is data accumulation.

The near-term gating constraint is SR-1 Criterion 3 (overlap games, 60/100), which only time fixes.

---

## 0. Where things stand

- **Paper 1** — "The Efficient Frontier of Public Information: Evidence from High-Frequency Sports
  Betting Markets." Draft 1.0, reframed around the Chong-Hendry forecast-encompassing test, written
  in SSRN register, 7 figures, reproducible end to end from committed caches
  (`paper/build_pdf.py`, `paper/make_figures.py`). Numbers are frozen at the June-2026 sample.
- **Method + data** — the Third Turn Protocol and Benchmark Dataset v1 are specified and versioned
  independently, with a safeguard registry and objective stopping rules.
- **Forward collection** — running toward (a) a **second month** of live data for Paper 1's
  temporal hold-out and (b) the **timestamped, multi-book** streams Paper 2 needs. The single
  load-bearing engineering fix (FanDuel `inPlay` read on the market, not the event) is live and
  takes effect on runner re-arm.

---

## 1. Paper 1 — action items to submission-ready

Ranked. Items 1-2 are load-bearing; the rest strengthen the paper or preempt a referee.

### Must-do (gates a serious-venue submission)

1. **Add the second month of live data as a temporal hold-out.** *(empirical, data-gated)*
   The paper's single biggest exposure is that the sample is one month (June 2026). The manuscript
   already promises a second month "before journal submission." Collect it, then re-run the frozen
   pipeline on the pooled two months and report whether the encompassing gain stays at or below
   zero out of sample in the new month. Completion is defined by **observed behavior, not elapsed
   time**: the collector has logged enough matched live snapshots in the new month to re-estimate
   the encompassing test at comparable power (target on the order of the current ~2,500 snapshots
   over ~150+ games). Do not peek at the July estimate before the sample is closed.

2. **Freeze Draft 1.1 on the pooled data and regenerate every number and figure.** *(mechanical)*
   Re-run `revision1.py`, the encompassing/calibration/transfer scripts, `make_figures.py`, then
   `build_pdf.py`. Update the sample-size lines (163 games, 2,505 / 2,859 / 6,414 units) and the
   "single month" limitation. Bump `BENCHMARK_DATASET` to `2026.07` (or `2026.q3`) and note the
   change in the dataset CHANGELOG. This is the version that goes to a journal.

### Should-do (referee-anticipating; a Chicago-school reader will ask)

3. **State the multiple-testing posture explicitly.** Ten candidate hypotheses invite the "of
   course one looked alive" objection. The answer is already in the design (the velocity
   deconstruction is exactly that objection, answered), but say it out loud: cite the protocol's
   stopping rules and safeguard registry in Methods, note that no hypothesis was added after seeing
   the encompassing result, and frame the joint encompassing test as the family-wise control. One
   paragraph.

4. **Second-book robustness for the encompassing benchmark.** *(data-gated, shares Paper 2 data)*
   The single-book benchmark is a named limitation. As the multi-book live streams accrue, re-run
   the error-on-features regression against a second sharp book (or a two-book consensus) and report
   that the null holds. This converts a limitation into a robustness result.

5. **External read before submission.** Circulate to three readers with distinct lenses: a
   forecasting econometrician (does the Clark-West / Diebold-Mariano usage hold up?), a
   sports-analytics reader (are the baseball claims fair?), and a markets reader (is the
   asset-pricing framing credible?). Budget two weeks.

### Polish (do now; none blocks the above)

6. **Post to SSRN and arXiv immediately.** The paper is written for it and needs no new data.
   Establishes priority and starts collecting comments while the second month accrues. See §2.
7. **Mint the dataset DOI.** Package Benchmark Dataset v1 to Zenodo so the "persistent DOI pending
   publication" line in Data-and-code-availability resolves to a real identifier.
8. **Plain-language summary.** One paragraph for the SSRN abstract page and any thread/blog, in the
   three-questions frame (predicting runs, beating the price, and turning a profit are different
   problems).

---

## 2. Submission avenues

**Recommended path, in order.** Post as a working paper now; target a forecasting journal as the
scholarly home; use the sports-analytics conference for visibility.

> Journals below are **rolling** (no deadline). The one hard deadline is the MIT Sloan conference,
> and its exact 2027 date must be **verified on the current call for papers** — historically the
> research-paper track closes in the **fall of the prior year** (roughly early-to-mid November).
> Do not rely on the month below without checking the site.

| Venue | Type | Why it fits the reframed paper | Timing | What's needed |
|---|---|---|---|---|
| **SSRN + arXiv** (q-fin.ST primary, econ.EM cross-list) | Preprint | Priority + comments; the paper is already in this register; peers here (Angelini-De Angelis) live on arXiv | **Now**, rolling | The PDF, a 150-word abstract, JEL/keyword tags (already set) |
| **International Journal of Forecasting** | Journal (primary target) | The encompassing / Clark-West / Diebold-Mariano toolkit **is** their core; they publish negative forecast-comparison results and value a reusable protocol | Rolling | ~30-40pp single-column, cover letter positioning the protocol as the contribution, data/code link |
| **MIT Sloan Sports Analytics Conf. 2027 — research track** | Conference (visibility) | Highest-profile sports venue; the methodology angle differentiates from the usual positive-result entries | **Deadline fall 2026 — verify** | Full paper (competition format), check their preprint/prior-publication policy (an SSRN preprint is normally allowed) |
| **Journal of Sports Economics** | Journal (fallback) | Natural sports-plus-econ home; friendly to market-efficiency findings | Rolling | Standard econ submission |
| **Journal of Quantitative Analysis in Sports** | Journal (fallback) | Where Brill-Deshpande-Wyner (cited) published the TTOP work; fits the methodology | Rolling | Standard submission |
| **Management Science** / a finance field journal (e.g. *Journal of Empirical Finance*) | Journal (aspirational) | Where Simon (2024, cited) published; the betting-as-asset-pricing-laboratory framing (Thaler-Ziemba lineage) can reach here **if** the two-month result and cross-book robustness both land | Rolling | The strongest version only; high risk, submit after 1-4 are in hand |

**One-line strategy:** SSRN/arXiv this month → *International Journal of Forecasting* as the primary
journal once the second month is folded in → SSAC 2027 for reach if the deadline fits → Sports
Economics / JQAS as fallbacks → Management Science only as a reach with the fully strengthened
draft.

**Positioning note for the cover letter.** Lead with the *method* and the *negative result as
measurement*, not with baseball. The contribution is a protocol that shifts the burden of proof
from prediction to incremental information beyond a sharp forecast, validated in a clean laboratory
where every contract has a terminal payoff. The velocity survivorship-bias deconstruction is the
single most persuasive exhibit that the protocol earns its keep; put it early in the letter.

---

## 3. Forthcoming papers and program strategy

### Paper 2 — Market microstructure of live information *(the follow-on Paper 1 advertises)*
The §7 "Remaining Questions" are the outline: does information propagate across books with a
measurable lag, and is a laggard ever tradable? What is the information half-life of a shock (home
run, pitching change, injury)? Does the market update the *shape* of the implied run distribution
(variance, skew, tails) as well as its mean, or is higher-moment miscalibration where a residual
edge hides? Does the frontier move when the market isolates the starters (first-five-inning
totals)? Every one is a live-data question, unanswerable from one-minute single-book snapshots.
**Data-gated:** write it only once the forward streams are deep enough (observed-behavior gate:
a target count of simultaneous cross-book live quotes across a target number of games), not on a
calendar. This is the natural place for any real edge to appear, because Paper 1 has ruled out the
first-moment, single-book one.

### Paper 3 — The Third Turn Protocol as a standalone method / benchmark *(optional, reception-gated)*
The reviewer's read is that the durable value is the protocol plus the survivorship-bias
deconstruction. If Paper 1's referees latch onto the protocol, spin it out as a short methods or
benchmark/resource paper (forecasting-methods or reproducibility venue) presenting the ladder and
the Benchmark Dataset as reusable infrastructure, independent of the baseball findings. If they
don't, it stays as Paper 1's methodological core. Decide after Paper 1's first response, not before.

### Cross-sport replication *(cheap robustness leg; folds into Paper 2 or stands alone)*
Run the protocol unchanged on NBA totals or NFL spreads to show the frontier generalizes. The
ladder is designed to transfer to any market with a sharp public forecast and observable state.
This is the highest value-per-effort extension and directly supports the "citable protocol" claim.

### Operating doctrine (the principles that keep the program honest)
- The durable asset is the **culture of falsification**, not any single finding. Lead every paper
  with the protocol.
- Keep infrastructure **lean and in service of papers**. The documentation must not become the
  project.
- The accruing streams are a **hold-out, not a sandbox**. Pre-commit each analysis before looking;
  resist mining the data nightly.
- **Version Protocol / Collector / Benchmark independently**, and freeze a paper's numbers at
  submission.
- Define collection and production milestones by **observed behavior, not elapsed time**.

---

## Near-term checklist (next ~30 days)

- [ ] Post Paper 1 to SSRN + arXiv (q-fin.ST, cross-list econ.EM).
- [ ] Package Benchmark Dataset v1 to Zenodo; wire the DOI into the paper.
- [ ] Confirm the SSAC 2027 research-track deadline and preprint policy on the live call.
- [ ] Keep the collector running; watch the second-month snapshot count toward the re-estimation gate.
- [ ] Send Draft 1.0 to the three external readers.
- [ ] Draft the IJF cover letter (method-first positioning).
