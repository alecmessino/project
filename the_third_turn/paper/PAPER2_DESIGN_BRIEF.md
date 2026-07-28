# Paper 2 — Design Brief (governing specification)

**Status:** authoritative. Scope locked by **GD-13** (approved 2026-07-28). One research question only.
Any change to this brief requires a decision-log entry. Drafting is authorized for non-result
sections; **Results, Discussion, Abstract findings, and Conclusion are prohibited** until §9 clears.

---

### 1. Research question
**Under what conditions is cross-book information leadership in live betting markets identifiable
from observational quote data, and when is an apparent leader an artifact of the measurement
apparatus rather than of information?**

Not "which book leads." That question is downstream and may prove unanswerable with these feeds;
this paper establishes whether it *can* be asked.

### 2. Hypothesis
**H0 (maintained):** an observed cross-book lead is fully explained by measurement artifacts, namely
(i) differential update frequency, (ii) main-line extraction choice, and (iii) differential feed
latency. Leadership is *not* identified without controls for all three.

**H1:** after controlling for all three, a residual, direction-stable lead survives, and the
conditions under which it survives can be stated precisely.

The paper is written to be publishable under **either** outcome. Failure to identify is the result,
not a failed paper, exactly as Paper 1's null was the result.

### 3. Estimand
Let book *b* post main-line price series *P_b(t)*, and let *E* be a discrete game-state event at time
*t_E* (from `game_state_panel`). Define the **event-anchored response lag**

> **λ_b = E[ t_b(E) − t_E ]**, where *t_b(E)* is book *b*'s first main-line revision attributable to *E*.

The estimand is the **contrast Δλ = λ_bovada − λ_fanduel**, the differential event-response latency.

**Why anchored to the event and not to the other book.** Book-to-book timing (what E-018 measured)
is contaminated by update frequency: a book that re-prices more often reaches any level sooner by
construction. Anchoring both books to an exogenous third clock (the game event) removes that
mechanical advantage. This is the paper's central methodological move.

### 4. Identification assumptions
| # | Assumption | Status |
|---|---|---|
| **A1** | Game events are exogenous to book quoting behaviour | Plausible; runs are not caused by the books |
| **A2** | Event timestamps and quote timestamps are on a common, comparable clock | **Untested.** Requires the collector-clock audit (§6) |
| **A3** | A book's main-line series is well defined | **Refuted as stated (A-11/RD-3).** Requires a fixed, validated discriminator |
| **A4** | Feed-transport latency is separable from price-formation latency | **Open. The binding assumption.** Needs an independent latency reference |
| **A5** | Two books suffice to detect a single-book artifact | **Contested (SR-1 C4, RD-2).** Needs a third book or an outlier-detection substitute |
| **A6** | Response attribution (which revision is "caused by" *E*) is not arbitrary | Requires a pre-registered attribution window, fixed before estimation |

**A4 is the paper's hinge.** If feed-transport latency cannot be separated from price-formation
latency, Δλ is not an information quantity and H0 cannot be rejected. Establishing this cleanly, in
either direction, is a publishable contribution.

### 5. Success criteria
The paper succeeds if it delivers **all** of:
1. A precise statement of the conditions under which Δλ is identified, with each assumption tested or
   explicitly bounded.
2. A reproducible, pre-registered estimation procedure fixed before the data are re-examined.
3. A demonstration that the three named artifacts (frequency, extraction, latency) can each
   *manufacture* an apparent leader, with magnitudes.
4. Either an identified Δλ with stated conditions, **or** a defended impossibility result.

It does **not** require finding a leader. It does **not** require a tradable edge.

### 6. Blocked measurements *(and what unblocks each)*
| Blocked | Blocker | Unblocked by |
|---|---|---|
| Any Δλ point estimate | **A4** (latency vs information) | An independent per-book transport-latency reference, or a design where transport latency is common-mode and differences out |
| Any cross-book price series | **RD-3 / A3** | A fixed, unit-tested main-line discriminator (odds-anchored: balanced ∧ near-modal) |
| Clock comparability | **A2** | Collector-clock audit: quote-timestamp provenance (book-supplied vs. capture time) per feed |
| Single-book-artifact robustness | **SR-1 C4 / A5** | Third live book, or a documented outlier-detection substitute |
| Attribution windows | **A6** | Pre-registration of the window before estimation (self-imposed; clears with the plan) |

Note the asymmetry: **A6 clears by writing; A2/A3 clear by measurement work; A4/A5 may not clear at
all** — and that is a finding, not a failure.

### 7. Expected figures
1. **The three artifacts, illustrated** — how frequency, extraction, and latency each manufacture a
   false leader (schematic; needs no new data).
2. **Extraction sensitivity** — the same leadership statistic under three main-line definitions
   (E-017 material; already generated).
3. **Base-rate placebo** — pre/post symmetry test that separates a real lead from a frequency
   artifact (E-018 material; already generated).
4. **Event-anchored response distribution** — λ_b per book, relative to the game event. **BLOCKED (A3, A2).**
5. **Identification region** — the conditions (cadence, book count, extraction rule) under which Δλ is
   identified. **BLOCKED (A4).**

Figures 1–3 are draftable now. Figures 4–5 are gated.

### 8. Expected tables
1. Data and institutional setting: books, cadence, coverage, panel schema. **Draftable now.**
2. Identification assumptions A1–A6 with status and test. **Draftable now.**
3. Artifact magnitudes: how large a false lead each artifact can produce. **Draftable now** (E-016/17/18).
4. Δλ estimates with CIs. **BLOCKED.**
5. Robustness across extraction rules, windows, book pairs. **BLOCKED.**

### 9. Exact conditions required before Results may be written
**All four, verified and logged to the Evidence Ledger:**

1. **RD-3 closed** — a main-line discriminator fixed in code, unit-tested, and shown to make the
   leadership statistic definition-invariant (the E-017 swing of 1.1×–9.5× collapses).
2. **A2 verified** — a collector-clock audit establishing that event and quote timestamps are
   comparable, with the residual skew quantified.
3. **A4 resolved in one direction** — either an independent latency reference exists, or a defended
   argument that transport latency is common-mode; **or** a documented impossibility, which converts
   the paper to a pure identification result and *also* satisfies this condition.
4. **A5 satisfied** — third live book, **or** the GD-9 outlier-detection substitute documented and
   accepted.

**Until all four hold, Results/Discussion/Abstract-findings/Conclusion remain prohibited.** Sections
may be drafted in the approved order (plan → identification → data → methods → intro → related work →
limitations) without touching a blocked number.

---

### Drafting order (owner-specified, 2026-07-28)
1. Pre-registered analysis plan · 2. Identification framework and estimand · 3. Data and institutional
setting · 4. Methods · 5. Introduction · 6. Related work · 7. Limitations.

**Out of scope by GD-13:** within-book vig/inventory dynamics (separate future paper); any tradability
or profitability claim; any Paper 1 re-analysis.
