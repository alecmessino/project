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

### GD-12 · 2026-07-19 · Doctrine: de-risk the measurement system, do not discover results
- **Decision:** Standing directive supersedes the "attack the highest assumption" cadence where they conflict. **The job is to make future results impossible to fool, not to discover results.** If a day's work would raise confidence in a *future conclusion* without first reducing uncertainty in the **measurement system or protocol**, do not do it — **collect instead.** Identifiability/leadership probes of the E-018 kind are paused under this rule until they de-risk measurement/protocol or a gate clears.
- **Evidence:** The last three attacks produced two refutations and one preliminary signal (E-016/17/18); the signal (E-018) is precisely a "confidence in a future conclusion" result, and it stalled on an unresolved measurement question (feed-latency vs information). The owner judged the marginal value of more such probes to be negative versus reducing measurement uncertainty and accumulating the hold-out.
- **Alternatives rejected:** Continue up the assumption hierarchy into feed-latency-vs-information now (would build confidence in a Paper-2 conclusion before the measurement system is trustworthy or SR-1 clears).
- **Reasoning:** A result is only as trustworthy as the instrument. Priority order is now: (1) reduce measurement/protocol uncertainty, (2) collect, (3) publish already-frozen work (Paper 1). Discovery is last and gated.
- **Future implications:** Daily reviews default to health + collection unless a measurement/protocol de-risking is available. Paper 1 (frozen) publishing proceeds — it is not "discovery." Paper 2 stays frozen. No confidence level moved.

---

### GD-13 · 2026-07-28 · **APPROVED 2026-07-28** · Supersede GD-7's Paper 2 scope
- **Status:** **APPROVED BY OWNER**, with one clarification: the GD-7 vig/inventory concept becomes a **separate future paper**, explicitly **not merged** into Paper 2. *"I do not want Paper 2 trying to answer two research questions."* Alternatives (a) and (b) below are therefore rejected; option (c) is adopted.
- **Ruling in force:** **Paper 2 = the identification paper** (single research question). GD-7's Paper 2 designation is superseded; GD-7's Paper 1 appendix decisions stand untouched. The vig/inventory study is re-homed as a separate future output with no scheduled start. Drafting is authorized for **non-result sections only**; GD-12 stands unchanged.
- **The problem — implicit scope drift, admitted.** Two incompatible Paper 2 scopes are on the record:
  - **GD-7 (2026-07-14, approved):** Paper 2 = **Avenue 2, within-book vig/inventory dynamics vs. game leverage.** GD-7 *explicitly rejected* Avenue 1 (cross-book leader-laggard) as blocked on ED-1/RD-1.
  - **ROADMAP (2026-07-19, edited by me, endorsed in conversation, never logged):** Paper 2 = **"When can information leadership be identified from live betting markets?"** — which is Avenue 1 territory, the thing GD-7 rejected.
  The roadmap edit changed the approved scope without a decision-log entry superseding GD-7. That is the drift the owner flagged. It is mine, and this entry exists to make it explicit rather than let it harden by default.
- **Consequence of the drift:** the 07-28 "defer Paper 2" recommendation was reasoned against the *identification* scope while GD-7's *vig* scope was still nominally in force, and it further mistook the identification framing for a novel proposal when it was already the (informally) approved objective. Both errors trace to the unlogged change.
- **The proposal:** make **Paper 2 = the identification paper** (roadmap scope) and **re-home GD-7's vig/inventory study as a separate later paper**, not as Paper 2.
  - *Why identification:* it inherits Paper 1's character (method + honest limits over positive findings); its raw material (E-016 frequency confound, E-017 extraction sensitivity, E-018 latency-vs-information) is **already generated and recorded**; and the blockers to a *leadership magnitude* are the paper's **subject matter**, not obstacles to it.
  - *Why not vig-as-Paper-2:* it is genuinely *less blocked* (within-book, no third book needed), which is the strongest argument against this proposal and is stated here rather than buried. But it is a conventional microstructure study whose contribution does not compound with Paper 1, and RD-3 still bites it (whose line's vig?).
- **Alternatives the owner may pick instead:** (a) keep GD-7 as written, vig = Paper 2, identification = Paper 3; (b) merge both into one microstructure paper; (c) this proposal.
- **What does NOT change under any option:** GD-12 stands. No empirical Paper 2 result is produced until measurement is de-risked. Approving this proposal authorizes **drafting of non-result sections only** (see the drafting/blocked split delivered 2026-07-28).
- **If approved:** GD-7's Paper 2 designation is superseded (its Paper 1 appendix decisions stand untouched); ROADMAP §3 is corrected to name the vig study explicitly as a separate output.

---

### GD-14 · 2026-07-28 · **APPROVED, with a mandatory scope correction** · Separate drafting from evidence
- **Decision (owner):** Run two parallel tracks. **Track 1:** fully draft Paper 2 on the pre-registered estimand/hypotheses/methods, writing outcome-dependent sections to accommodate either result. **Track 2:** independently analyze the newly collected games as *evidence discovery*, not paper revision; follow the evidence wherever it leads. Paper 1 stays frozen (repo/DOI/reproducibility/copyedit only); new data is **not** retrofitted. Placement of any material finding is decided afterward.
- **Track 1: accepted as written.** Drafting non-result sections raises no confidence in a conclusion, so GD-12 is not engaged. Outcome-agnostic drafting of gated sections is permitted *provided* no section asserts a direction.
- **Track 2: accepted in purpose, but CANNOT be executed as "a replication of Paper 1." The instrument changed.** Verified 2026-07-28 against the raw files:

  | | Paper 1 (Jun 1-23, 163 games) | New data (Jul 3-28, 103 live games) |
  |---|---|---|
  | Benchmark line | **Pinnacle** (sharp), via Odds Papi historical trajectories | **fanduel 256,893 / bovada 131,016 / pinnacle 6** (recreational; Pinnacle stillborn, ED-1) |
  | Velocity feature `vdrop` | present (Statcast) | **absent** (Baseball Savant 403) |
  | Weather `temp`/`wind` | present | **absent** from the live panels |
  | Cadence | ~1 min | 30 s |

  Running Paper 1's pipeline on the new month would therefore **confound time with instrument**: a different book class, a missing feature set (including `vdrop`, the survivorship-bias centerpiece), and a different sampling cadence. Any difference in result could not be attributed to the month. **This is a validity threat, not a logistics problem**, and it is not fixed by unblocking the feeds.
- **Corrected Track 2, in two clearly separated arms:**
  1. **Confirmatory (a true temporal replication).** Requires re-running the *same* instrument: Odds Papi historical **Pinnacle** for the new month **plus** Statcast features, on a host where both are reachable (both 403 here). Pre-specify the analysis **before** the data are examined; it is the frozen Paper 1 pipeline run unchanged. **Currently blocked on host access, not on method.**
  2. **Exploratory (the two-book live dataset on its own terms).** Analyzable now, but it is *not* Paper 1's question and must never be reported as replicating or failing to replicate Paper 1. It is largely Paper 2's substrate and is governed by the Paper 2 design brief.
- **Mandatory discipline on Track 2 (added, not optional):** "follow the evidence wherever it leads" across 100+ new games and dozens of candidate variables is the garden-of-forking-paths that Paper 1 exists to warn about. Therefore: **arm 1 is pre-registered before looking**; **arm 2's outputs are labelled `Exploratory` on the record and may not enter any paper without independent confirmation on data not used to generate them.** This preserves the owner's intent (genuine discovery, no confirmation bias) without reintroducing the failure mode the protocol was built to prevent.
- **Alternatives rejected:** run Paper 1's pipeline on the new books and call it a replication (invalid, confounded); defer Track 2 entirely (loses real discovery value in arm 2); allow unlabelled exploratory findings into a paper (false-discovery risk).
- **Future implications:** Paper 1.1 (temporal replication) remains **host-gated**, and is now also formally **instrument-gated**. No confidence level moved; no analysis run today.

---

*Append new decisions below this line. Never edit a past entry; correct with a new dated entry that
supersedes it.*
