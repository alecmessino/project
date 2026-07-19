# Governance Decision Log

The permanent audit trail of governance decisions: **why** beliefs, gates, and priorities changed.
Distinct from `../decisions/RESEARCH_DECISIONS_LOG.md` (which records killed *hypotheses*), this log
records *operating* decisions about the collector, protocol, gates, and the research program's
direction. Each entry is append-only and carries: decision, evidence, alternatives rejected,
reasoning, and future implications. This is the record a collaborator or referee can audit to see
that methodological choices were deliberate and evidence-driven.

The four governance artifacts: **Engineering Debt** (what can break) · **Research Debt** (what can
invalidate inference) · **Confidence Register** (what the evidence justifies believing) · **this log**
(why those beliefs changed).

---

### GD-1 · 2026-07-06 · Fix the collector re-arm single point of failure
- **Decision:** Move the workflow re-arm into an `always()` step so a platform cancellation cannot stop collection without recovery; activate immediately by dispatching a fresh run (concurrency supersedes the old one).
- **Evidence:** Run #14 was platform-cancelled mid-daemon; the tail re-arm never fired; cron is disabled and cannot fire from a feature branch; ~8.4 h outage resulted.
- **Alternatives rejected:** Re-enable cron (cannot target a feature branch); an out-of-band watchdog (needs default-branch placement, outside remit); wait for the next natural re-arm (leaves the window open).
- **Reasoning:** `always()` steps run during cancellation cleanup, which is the exact failure window observed; it eliminates the specific SPOF without leaving the branch.
- **Future implications:** Two residual failure modes remain uncovered (hard runner loss; <60-min-cancel dead zone) — tracked as ED-6. Confirmed working (EP-2) → Collector reliability held at High.

### GD-2 · 2026-07-09 · Treat the collector as production infrastructure; freeze Paper 1
- **Decision:** Operate the collector as production infra and the live data as a growing asset; Paper 1 is frozen unless an external reviewer finds a substantive issue; run no analysis unless a gate objectively clears.
- **Evidence:** The adversarial audit confirmed the live panels are disjoint from Paper 1 and that every research channel is gate-blocked.
- **Alternatives rejected:** Continue nightly exploratory analysis of incoming data (risks data-dredging and false discovery).
- **Reasoning:** The scarce asset is a trustworthy evidence pipeline over months, not nightly findings.
- **Future implications:** Standing discipline for all subsequent reviews; makes "no scientific progress today" an expected and acceptable verdict.

### GD-3 · 2026-07-09 · Flag the SR-1 sync sub-gate as a Candidate defect; do NOT revise it
- **Decision:** Record the sync-lag sub-gate as a Candidate design defect (implementation-dependent), leave the 15 s threshold and the health tool unchanged, and bring a volume/fraction redesign back for an explicit decision with a power analysis.
- **Evidence:** Independent recompute shows lags quantized to {0} ∪ [30 s, ∞); a PASS at median 0 certifies collector co-capture, not sub-15 s market contemporaneity; the naive fresh-pair-lag replacement is near-tautological.
- **Alternatives rejected:** Immediately revise/lower the threshold (would institutionalize an engineering hypothesis as methodology and risk rescuing a gate mid-flight).
- **Reasoning:** An observed implementation-dependence is fact; "mis-specified" is an architectural conclusion that requires a decision, not a silent edit. Flag, don't revise.
- **Future implications:** Tracked as ED-2 / RD-1; Synchronization split into "understanding: High" vs "gate validity: Moderate" in the Confidence Register.

### GD-4 · 2026-07-09 · Separate System Health from System Capability; add Known Unknowns
- **Decision:** In the daily review, evaluate Health (alive/honest) separately from Capability (what the platform can do); add a Known Unknowns category and a language-discipline rule (fact vs architectural hypothesis).
- **Evidence:** Prior reports conflated a missing capability (third book) with a health failure, and stated an architectural hypothesis as fact.
- **Alternatives rejected:** Keep a single blended status (obscures that the machine is healthy while a capability is structurally absent).
- **Reasoning:** Conflating the two produces false alarms and false confidence; the distinction makes the report auditable.
- **Future implications:** Encoded in the report template; Pinnacle's absence reads as Capability 🔴, not an incident.

### GD-5 · 2026-07-09 · Establish the four-artifact governance framework (v4 review)
- **Decision:** Adopt the v4 Research Governance Review format (daily Bayesian update on confidence) and stand up the Confidence Register and this Decision Log alongside the existing Engineering Debt and Research Debt registers.
- **Evidence:** The project has transitioned from building to operating; descriptive daily reports no longer add marginal value versus governing confidence and threats to inference.
- **Alternatives rejected:** Keep the v3 descriptive-with-Research-Debt format (does not force an explicit confidence update or a decision trail).
- **Reasoning:** A governance framework that separates *what can break / what can invalidate inference / what we believe / why beliefs changed* gives a rigorous audit trail and makes methodological choices defensible to referees.
- **Future implications:** Every future review updates the Confidence Register and appends decisions here; the daily review's purpose is explicitly to increase confidence in the eventual papers, not to produce them.

### GD-6 · 2026-07-09 · Complete and FREEZE the governance framework; enter Phase 4
- **Decision:** Add exactly three self-calibration artifacts — Evidence Ledger, Assumption Register, Inference Graph — then declare the governance framework feature-complete and adopt an artifact-admission rule. Enter Phase 4 (Evidence Accumulation): stabilize the collector, resolve the highest-impact Research Debt, accumulate data with minimal intervention, and resist analysis until gates clear.
- **Evidence:** Governance had the four pillars but no quantitative link between evidence and belief (Evidence Ledger), no explicit assumption inventory (Assumption Register), and no auditable provenance from observation to paper claim (Inference Graph). Beyond these three, further governance would grow faster than the research.
- **Alternatives rejected:** Keep expanding governance horizontally (risks governance-as-technical-debt); add nothing (leaves confidence changes justified by prose, not cited evidence).
- **Reasoning:** The three artifacts each satisfy the admission rule (auditability + reproducibility + reduced false-discovery risk). A hard stop plus an admission rule prevents the process from outgrowing the research.
- **Future implications:** No new governance artifact without a decision-log entry justifying it against the four admission criteria. **Explicitly: adding these process artifacts did NOT move any Confidence-Register level** — process auditability improved, but no specific inference threat (RD-1..7) was eliminated, and confidence in the science must not rise for building better paperwork. The next highest-leverage work is engineering/measurement on RD-1/RD-2/RD-3, then disciplined accumulation.

---

### GD-7 · 2026-07-14 · Pivot Paper 2 to Avenue 2 (inventory/vig dynamics); defer the temporal hold-out
- **Decision:** Make the market-microstructure follow-on **Avenue 2 (spread/vig dynamics vs. game leverage)** rather than Avenue 1 (cross-book leader-laggard) or Avenue 3 (PIN/adverse selection). Add a transaction-cost appendix (vig hurdle) and a power/MDE figure to Paper 1. Defer the Paper-1 temporal hold-out.
- **Evidence:** (a) Avenue 1 (Hasbrouck/VAR) needs a live *sharp* feed and synchronized cross-book series; we have two *recreational* books (Pinnacle stillborn, ED-1) and a sync-lag Candidate defect (RD-1). (b) Avenue 3 (PIN) needs order-flow/volume, which we do not observe. (c) Avenue 2 is within-book and uses data we already collect (vig derivable from over/under odds). (d) Hold-out feasibility check: `pybaseball` present and `.env` keys exist, but **Baseball Savant returns 403 in-session**, so the pipeline cannot reconstruct July play-by-play here; Odds Papi is also metered. Architecturally sound (June used Odds Papi historical Pinnacle), so runnable on a Statcast-reachable host with the keys.
- **Alternatives rejected:** Start Avenue 1 now (blocked on ED-1/RD-1); force the hold-out in this container (Statcast unreachable); put leader-laggard into Paper 1 (SR-1 BLOCKED, would be an under-powered artifact).
- **Reasoning:** Pick the microstructure question the current data actually supports; strengthen Paper 1 with cost-context that needs no new data; run the hold-out deliberately where the sources are reachable.
- **Future implications:** Paper 2 scoped to vig/inventory dynamics. The hold-out remains roadmap item #1, gated on a Statcast-reachable run with the API keys and a budgeted Odds Papi pull. No confidence level moved.

---

### GD-8 · 2026-07-19 · Adopt block-type gate classification + Inference Readiness; retire "Paper 2 readiness"
- **Decision:** Amend the daily governance format (v4) with two permanent additions: (a) a **block-type classification** on every unmet stopping-rule criterion — Dataset / Scientific sampling (self-resolving) vs Measurement / Engineering (never self-resolving); (b) a standing **Inference Readiness** metric — the conjunction of Engineering, Measurement, Dataset, Protocol, and Research Debt pillars, answering "would a conclusion drawn today survive peer review?" Retire "Paper 2 readiness" language in favor of it.
- **Evidence:** The 07-19 review conflated an engineering block (dead third book) with a self-resolving one (overlap-game accrual) and jumped to "replace the book or amend the gate" — a governance error the owner caught. Block-typing makes that error structurally hard to repeat. "Enough data to analyze?" is the wrong question; "can we trust the analysis?" is the right one.
- **Alternatives rejected:** Keep the v4 format unchanged (repeats the conflation); add Inference Readiness as prose only (not enforced each day).
- **Reasoning:** Both additions satisfy the artifact-admission rule (reduce false discovery + improve auditability) without new documents — they are amendments to an existing artifact, not new ones.
- **Future implications:** Every review now block-types unmet criteria and reports Inference Readiness (a sixth Executive-Verdict line). No confidence level moved.

### GD-9 · 2026-07-19 · SR-1 Gate Design Review — no criterion changed
- **Decision:** Complete a formal five-question design review of all four SR-1 criteria (`SR1_GATE_DESIGN_REVIEW.md`). **Change nothing.** Establish the *property* each criterion defends; do not touch thresholds.
- **Evidence:** Reframed the third-book question from "should SR-1 require 3 books?" to "what property does ≥3 books guarantee?" Answer: **single-book-artifact protection** (majority-vote outlier rejection). That property is real and not yet satisfiable another way. Criteria 1–2 pass; Criterion 3 (overlap games) is self-resolving scientific sampling; Criterion 2 remains a flagged measurement-redesign candidate (RD-1).
- **Alternatives rejected:** Recommend replacing Pinnacle or amending to a two-book gate (both premature — remedies before the property was even named); lower Criterion 3.
- **Reasoning:** A criterion is a proxy for a property; we defend properties, not thresholds. Revisiting Criterion 4 is gated on the Book Characterization establishing two-book independence + an outlier-detection substitute.
- **Future implications:** SR-1 unchanged. The third-book question is dormant until Criterion 3 (60/100) nears satisfaction; the Book Characterization is its prerequisite evidence. No confidence level moved.

### GD-10 · 2026-07-19 · Book Characterization v0.1 — books provisionally non-interchangeable; leadership deferred
- **Decision:** Produce the first-edition Book Characterization (`BOOK_CHARACTERIZATION.md`, `book_characterization.py`) as instrument measurement only. Report the measured behavioral split; **defer** the leadership ("who moves first") question rather than report a confounded number; open **RD-8** (non-interchangeability).
- **Evidence:** FanDuel = high-frequency/tight-vig (31 s cadence, IQR 0.36 pp); Bovada = coarse/sticky (8 min cadence, IQR 1.80 pp); Pinnacle absent (ED-1). The naive first-arrival leadership metric flips leader entirely under two reasonable definitions (69% Bovada vs 76% FanDuel) with nonsensical ~24 h gaps — proof it is granularity-confounded, not price discovery. Suspend/reopen ordering is structurally un-measurable (Bovada emits no status, RD-4).
- **Alternatives rejected:** Report the first-arrival leader as a finding (confounded); claim a benchmark/noisy designation (requires the deferred event-aligned test).
- **Reasoning:** Characterizing the instrument before trusting it is measurement, permitted under the discipline mandate and explicitly commissioned. Leadership requires an event-aligned `book_panel × game_state_panel` join (edition v0.2), which is also what the RD-1 sync redesign needs.
- **Future implications:** Any future cross-book statistic must account for RD-8. Edition v0.2 (event-aligned leadership) is the next characterization step, not Paper 2. **No scientific conclusion drawn; no confidence level in any finding moved** — this raised Measurement/Instrumentation maturity only.

---

### GD-11 · 2026-07-19 · Adopt the Scientific > Measurement > Implementation hierarchy; freeze A-11; leadership is the frontier
- **Decision:** Adopt the owner's selection rule for the falsification program: classify each candidate assumption **Scientific / Measurement / Implementation**; prefer Scientific over Measurement over Implementation; keep attacking a Measurement assumption **only** if resolving it materially changes a Scientific answer, else freeze it and move up. Applied today: **freeze A-11** (main-line extraction) with its limitation recorded; **promote the Scientific identifiability question** (A-12) as the current frontier.
- **Evidence:** The leadership verdict (E-018) is **byte-identical** under the modal and balanced main-line definitions — so the Scientific answer does not depend on the frozen Measurement choice, which is exactly the test the rule requires before freezing. Continuing to attack A-11 would have been Measurement work with no Scientific payoff.
- **Alternatives rejected:** Keep drilling A-11's remedy (a validated discriminator) now — deferred to only-if-a-level-based-Scientific-answer-needs-it; run the leadership analysis on a single extraction rule without the invariance check (would leave the confound unaddressed).
- **Reasoning:** The hierarchy prevents the program from drifting into measurement rabbit holes. Freeze-and-record is the correct disposition for a Measurement assumption that does not gate a Scientific one.
- **Future implications:** A-11 stays frozen (odds-anchored, transition-invariant) until a *level-based* Scientific question depends on it. The live frontier is A-12 and specifically the **feed-latency vs information** distinction, which decides whether cross-book leadership is economically interesting. **SR-1 remains BLOCKED**: E-018 is an identifiability/feasibility result, explicitly **not** a gated efficiency finding, and no market-efficiency confidence level was moved.

---

*Append new decisions below this line. Never edit a past entry; correct with a new dated entry that
supersedes it.*
