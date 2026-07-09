# Daily Operations Review — standing format

An **operations** review for a research platform, not a status report trying to show success. The
default assumption is that nothing scientific changed; the job is to confirm the platform is healthy,
say what capability matured, and track what we know / assume / have yet to establish. If nothing
meaningful changed, say so confidently.

The report opens with an at-a-glance **Operational Status**, then four permanent sections, then a
change log.

---

## Operational Status (at-a-glance)

```
Production      🟢 / 🟡 / 🔴
Collector       🟢 / 🟡 / 🔴
Integrity       🟢 / 🟡 / 🔴
Capability      🟢 / 🟡 / 🔴
Unknowns        🟢 / 🟡 / 🔴

Scientific Status
  Paper 1       (frozen — state if anything even could bear on it)
  Paper 2       (data-gated — which gate, current state)
  Protocol      (stable / a Candidate defect open / a rule reclassified)
```

**Light rubric (objective, not vibes):**
- **Production 🟢** iff latest checkpoint age < ~45 min during game hours *and* the re-arm chain is intact. 🟡 if a benign no-game gap or a degraded-but-running condition. 🔴 if collection is stalled.
- **Collector 🟢** iff the daemon is polling and both expected live books are fresh. 🟡 if one feed is stale for a non-structural reason. 🔴 on a crash/outage.
- **Integrity 🟢** iff 0 malformed/missing/duplicate/future-ts *under the tool's field definition* (note the definition; see ED-4). 🔴 on any integrity break or schema regression.
- **Capability** reflects *maturation toward gates*, never a failure: 🟢 all target capabilities present, 🟡 some absent-but-progressing, 🔴 a required capability structurally missing (e.g., no 3rd book). A 🔴 here is **not** an incident.
- **Unknowns 🔴** while a top-ranked Known Unknown is unresolved and load-bearing (e.g., KU-1 Pinnacle root cause). 🟡 when unknowns exist but none blocks the critical path. 🟢 when none is material.

---

## 1. Production Health *(evaluated every day; a 🔴 here is an incident)*

Health = "is the machine alive and honest." Report and interpret:
- **Liveness** — latest checkpoint timestamp vs wall-clock (the health report's self-written "running normally" freezes when the collector dies, so checkpoint age is the real signal).
- **Checkpoint cadence** — is it on its ~15-min interval, or drifting/stalling.
- **GitHub Actions / re-arm chain** — current run ID; distinguish normal `cancelled` handoffs from real `failure`s; verify the chain against the API, not narrative.
- **Schema integrity** — malformed / missing / duplicate / future-ts, *stating the field definition* and any unvalidated fields (odds/status/line-type; ED-4).
- **API failures / stale feeds** — per-book freshness; separate a benign no-game gap from a feed fault.

## 2. System Capability *(maturation toward gates — NOT failures)*

Capability = "what the platform can currently do." A missing capability is a capability, not a
defect. Report the level and trend of:
- **Two-book overlap** — simultaneous live pairs, overlap games (with the ED-3 alt-line caveat on the pair count).
- **Third book** — present / absent and why (today: absent, ED-1 Pinnacle stillborn).
- **Alternate totals** — coverage and whether discriminated (ED-3).
- **Implied-PMF continuity** — SR-2 readiness (games with continuous PMF through ≥6 innings).
- **Coverage** — innings, games/day, new-game enrollment (the thing overlap-games depends on; EP-4).

Interpret each change as one of: **more data / better infrastructure / better measurement / actual
scientific progress** — these are not equivalent, and cumulative growth is *more data*, not evidence.

## 3. Research Status

- **Verification gates** — SR-1 / SR-2 / SR-3 current state, carrying their maturity label from
  `STOPPING_RULE_CLASSIFICATION.md` (empirically validated / provisional / design assumption /
  awaiting evidence). Keep three milestones separate: **Engineering complete ≠ Production verified ≠
  Research unlocked.**
- **Paper 1** — frozen; state plainly whether anything could even bear on it (usually: no, the live
  panels are temporally/book/data-type disjoint).
- **Paper 2** — which gate blocks it and its state.
- **Findings** — assume none. Nothing promotes to a Finding unless a stopping rule objectively clears.
  Classify everything else on the ladder below.
- **Engineering predictions resolved today** — link any resolution to `ENGINEERING_PREDICTION_LOG.md`.

**Classification ladder (use exactly these):**
`Observation` → `Candidate` → `Rejected` → `Finding` (only past a cleared gate), plus **`Known
Unknown`** for an unanswered question that is not yet even a hypothesis.

## 4. Engineering Debt / Known Unknowns

- **Top open debt** — from `ENGINEERING_DEBT_AND_KNOWN_UNKNOWNS.md`, ranked by risk-to-the-platform
  (currently ED-1 Pinnacle at the top: *unknown infrastructure is dangerous infrastructure*).
- **Known Unknowns** — the tracked open questions (KU-1..n); note any that moved.
- **Opened / closed today** — new debt or unknowns surfaced, and any that a shipped fix + confirming
  check closed.

---

## Today's Change Log

A short, literal list of what changed since the last report: data facts (rows/pairs/coverage deltas),
engineering/process changes (fixes shipped, docs added), and prediction resolutions. Each line tagged
with its type — `[data]` / `[infra]` / `[measurement]` / `[science]` / `[process]` — so the reader can
see at a glance that (almost always) the day was data + infra, not science.

---

## Standing rules & language discipline

- **No research analysis unless a predefined gate objectively clears.** The collector builds a
  research asset over months; it does not generate nightly discoveries.
- **Liveness first**, skeptical always: assume every attractive result is an artifact until validated;
  never confuse more observations with more evidence.
- **Health ≠ Capability.** A missing capability (third book, PMF continuity) is not a failure and does
  not turn Production/Integrity red.
- **Separate observed fact from architectural hypothesis.** "The metric is quantized by the 30 s poll
  interval" is an observed fact; "the gate is mis-specified" is an architectural conclusion. State the
  first as fact and label the second a **Candidate**. Do **not** institutionalize an engineering
  hypothesis as established methodology, and **flag** implementation-dependent metrics for redesign
  rather than silently revising them.
- **Data sources:** `collection_health.py` / `--trend`, `output/metrics_history.jsonl`, and the ops
  registers (`ENGINEERING_PREDICTION_LOG.md`, `STOPPING_RULE_CLASSIFICATION.md`,
  `ENGINEERING_DEBT_AND_KNOWN_UNKNOWNS.md`).
