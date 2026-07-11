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

*Append new decisions below this line. Never edit a past entry; correct with a new dated entry that
supersedes it.*
