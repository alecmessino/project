# Research Debt

Unresolved issues that could threaten the **validity of a future inference**. This is not
engineering debt. Engineering debt is "the machine is fragile or broken" (see
`ENGINEERING_DEBT_AND_KNOWN_UNKNOWNS.md`); research debt is "a conclusion drawn from this data could
be **wrong or unidentifiable** even if the machine runs perfectly." Many items have an engineering
fix and a research consequence; this register states the **inference threat**, the analysis it
endangers, and the mechanism of the bias — not the code fix.

**Why this list matters more as Paper 2 approaches.** These are the threats to valid inference that
must be *cleared or explicitly bounded before any gated analysis is run* — a pre-analysis threat
list, in the spirit of pre-registration. Clearing this backlog is worth more than another day of
descriptive statistics: it decides whether a future result survives hostile scrutiny.

**Discipline.** An item is closed only when the threat is *eliminated or quantified and bounded*,
with the resolution recorded. "We collected more data" never closes a research-debt item. Promotion
of any related observation to a Finding still requires the relevant stopping rule to clear.

| ID | Inference threat | Endangers | Mechanism (how it would bias / invalidate) | Status / mitigation | Eng link |
|---|---|---|---|---|---|
| **RD-1** | The SR-1 sync sub-gate certifies collector **co-capture** (30 s poll granularity), not sub-15 s market **contemporaneity**. | SR-1 leadership / lead-lag | A lead-lag estimate built on "simultaneous" pairs that are only same-poll co-captures could attribute to *who moved first in the market* what is actually *poll-timing jitter* — a directional artifact masquerading as leadership. | Candidate design defect, flagged not revised; SR-1 stays BLOCKED so no estimate is run. Redesign toward a volume/fraction criterion is proposed, undecided. | ED-2 |
| **RD-2** | Only **two live books**; the third is absent (Pinnacle stillborn, cause unknown). | SR-1 leadership; SR-2 (sharp PMF source) | With two books, cross-book leadership is likely **under-identified / noise-dominated** (the S-10/S-11 one-night lesson); an estimate could be unstable or non-reproducible. SR-2's implied-PMF stream requires the sharp source, which does not exist in live form. | Structural block held by SR-1; root cause undiagnosed (KU-1). Whether 3 books are actually *needed* for identification is itself open (KU-3). | ED-1 |
| **RD-3** | `book_panel` mixes **main and alternate total lines** with no discriminator (~95% of (game,book,ts) groups carry 2–3 lines). **Promoted (E-017):** the reasonable candidate discriminators (balanced-odds / modal anchor / median) **disagree 71% of the time**, and the choice materially changes downstream results (book-frequency ratio swung 1.1×–9.5×). | Any line-based inference: leadership, drop/reversion, SR-3 encompassing robustness, **book characterization** | Conflating distinct contracts makes "the line moved" ambiguous and biases any line-keyed signal. Worse than first stated: even *after* deciding to extract "a main line," the extraction rule is itself an outcome-affecting free parameter — a second-order confound that already flipped an E-016 magnitude. | A validated main-line discriminator (odds-anchored: balanced ∧ near-modal) must be fixed and unit-tested before ANY cross-book or line-movement inference. Highest-priority measurement debt. | ED-3, A-11 |
| **RD-4** | **Status coverage is asymmetric** — fanduel emits OPEN/SUSPENDED/REMOVED; bovada emits none. | Any analysis that filters non-tradeable (suspended/removed) quotes; cross-book comparison | Filtering one book's suspended quotes but not the other's introduces **asymmetric selection**: the un-filtered book looks artificially cleaner/faster, which could bias the very cross-book leadership or divergence estimate toward the filtered book. | Do not apply a suspension filter for cross-book work until bovada status coverage exists or the asymmetry is explicitly modeled. | ED-5 |
| **RD-5** | **Integrity checks ignore odds fields.** 61 fanduel rows (36 live) carry null odds and pass; odds are heavy-tailed (to −50000 / +2000). | De-vig / implied-probability inference; calibration; SR-3 encompassing robustness | Null or extreme odds silently entering an implied-probability or de-vig computation would corrupt calibration and any encompassing robustness re-run; the null-odds rows sit *inside* the co-live instants SR-1 would consume. | Use robust/median odds statistics only; validate/flag odds before any implied-prob work. Not yet enforced. | ED-4 |
| **RD-6** | The **"simultaneous pairs" metric has no defined staleness horizon** for the forward-filled leg. | SR-1 leadership; SR-1 pairs sub-gate | A "pair" may include a leg that is minutes stale, so the count (the one passing sub-gate) and any lead-lag built on it can include non-contemporaneous quotes — the exact confound the gate exists to prevent. | Define and enforce a max forward-fill age before the pairs count or any leadership estimate is trusted. Tied to the RD-1 redesign. | ED-2, ED-3 |
| **RD-7** | **Safeguard/protocol text can drift from reality.** S-14 reads "field not yet collected," but `status` has been collected since 2026-07-05. | Integrity of the safeguard registry as a design-time risk control | A safeguard that misdescribes the data cannot manage the risk it names, and a stale registry erodes trust that documented controls reflect the live system — a slow threat to the whole falsification culture. | Refresh S-14 (and audit the registry for other drift) as part of the next protocol touch; tracked, not yet done. | ED-5 |
| **RD-8** | **The two live books differ in update frequency (confirmed).** Falsification-tested 2026-07-19 (E-016), controlling for RD-3 alt-lines + 30 s poll cadence: FanDuel re-prices its main line **4.7× more often** than Bovada (53/60 games). *The pricing-tightness half of the original claim was refuted as an alt-line artifact — not part of this debt.* | Any cross-book statistic — consensus line, leadership, divergence, encompassing robustness | A "who moved first" count is dominated by the higher-frequency book purely by how often it re-prices; a naive median blends a live tape with a slow anchor. Any cross-book estimate that weights the two symmetrically is mis-specified. **Refutes** the behavioral-interchangeability assumption (A-10). | Confirmed on the frequency axis; not yet modeled. Cross-book analysis must weight by update behavior or restrict to one book; leadership still needs the event-aligned test (deferred). | ED-1, RD-2, RD-3, RD-4 |

## How this register is used

- The **Adversarial Audit** in the daily review feeds this list: any weakness found behind a green
  health check that could bias a *future* conclusion is logged here (as an inference threat), even
  when it is benign for *today's* operation.
- Before any stopping rule clears and an analysis is authorized, the relevant RD items for that
  analysis must be **cleared or explicitly bounded in the analysis plan** — otherwise the result is
  not defensible under hostile scrutiny regardless of the gate.
- Items are cross-linked to engineering debt (where the fix lives) but are tracked separately,
  because a shipped engineering fix closes an ED item only; the RD item closes when the *inference
  threat* is eliminated or quantified.
