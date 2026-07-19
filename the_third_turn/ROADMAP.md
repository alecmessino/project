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

## 1. Paper 1 (Frozen) — disseminate; Paper 1.1 — validate independently

**Mindset: Paper 1 is done, not being finished.** The paper, benchmark, methodology, and numbers
are frozen at the June-2026 sample. There are **no further empirical changes to Paper 1.** All work
splits into two buckets: *disseminate the frozen paper now*, and *validate it independently later*
as a separate output (Paper 1.1). Any new empirical content belongs to Paper 1.1 or a revision —
never back into Paper 1.

### Paper 1 (Frozen) — dissemination (do now; no new data)

- Post the **SSRN preprint** (q-fin.ST primary, econ.EM cross-list).
- Post the **arXiv preprint** (same categories).
- **Archive the frozen benchmark + code** (public release bundle, already built).
- **Mint the dataset DOI** (Benchmark v1 → Zenodo; resolves the "DOI pending" line).
- **Solicit referee feedback** — three readers (forecasting econometrician · sports-analytics ·
  markets); budget two weeks.
- **Plain-language summary** for the SSRN page (three-questions frame).
- **No further empirical changes.**

### Paper 1.1 — *independent* temporal validation *(data-gated; NOT a rewrite of Paper 1)*

A second month is **validation, not a pooled re-draft.** Paper 1 stays June-only. Paper 1.1 is a
separate, short output: *"Independent temporal validation of the Third Turn encompassing result."*

1. **Collect the second month and run the frozen pipeline on that month ALONE.** *(empirical,
   data-gated)* Report whether the encompassing gain stays at or below zero **out of sample in the
   new month** — a genuine hold-out, not a pooled re-fit. Completion is **observed behavior, not
   elapsed time**: enough matched live snapshots in the new month to re-estimate at comparable power
   (~2,500 snapshots over ~150+ games). Do not peek before the month closes.

2. **Write Paper 1.1 as its own artifact.** New benchmark slice (`2026.07`) with its own CHANGELOG
   entry; Paper 1's `2026.06` benchmark is untouched. The validation either replicates the null out
   of sample (strong) or does not (also publishable, and more important). This is scientifically
   stronger than folding a second month into Paper 1.

### Deferred to Paper 1.1 / a revision (NOT changes to frozen Paper 1)

- **Multiple-testing posture, stated explicitly.** A one-paragraph Methods addition for the
  validation/revision: cite the protocol's stopping rules and safeguard registry, note no hypothesis
  was added after seeing the encompassing result, frame the joint encompassing test as the
  family-wise control. (Text clarification only — no number changes; ships with Paper 1.1 or a v-note.)
- **Second-book robustness for the encompassing benchmark.** *(data-gated, shares Paper 2 data)* As
  multi-book live streams accrue and a validated main-line series exists (RD-3), re-run the
  error-on-features regression against a two-book consensus and report the null holds — converting a
  named limitation into a robustness result. Belongs to Paper 1.1, not Paper 1.

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

### Paper 2 — *When can information leadership be identified from live betting markets?*
The question has sharpened from "measure information leadership" to **"under what conditions is
cross-book information leadership even identifiable, and when is an apparent leader an artifact of
update frequency or feed latency?"** Half the paper may be about **identification**, not results —
which is stronger, not weaker: it inherits Paper 1's character (the contribution is method and honest
limits, not a positive finding). The naive-leadership traps already found (frequency confound,
main-line-definition sensitivity, latency-vs-information) are the paper's raw material. It stays
**frozen** under GD-12 until measurement/protocol are de-risked or SR-1 clears.

The §7 "Remaining Questions" remain the substantive menu once identification is settled: does
information propagate across books with a
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
