# The Driftwood Governance Architecture

*Frozen — **v1.1**. This defines the operating system before we design its first screen. The onboarding
worksheet, the Manual layout, the AWOR sections, and any future software are **interfaces onto this
architecture** — they may change freely. What is written here may not, except by deliberate
amendment. If an interface and this document disagree, the interface is wrong. (Changelog at the end.)*

Companion to the [Design Constitution](DESIGN_CONSTITUTION.md): that governs how the system
*looks*; this governs how it *thinks*.

---

## Preamble — the scarce resource is judgment

Financial information is being commoditized to zero. Balances aggregate themselves; a slider
projects a number; an LLM drafts adequate advice. What does **not** commoditize — what a family
office actually preserves internally, and what complex households cannot buy off a shelf — is
**durable judgment**: not only making a good decision today, but preserving *why it was good*, under
*what assumptions*, so the next decision is better than it would have been.

Therefore the central object of this system is not a record of decisions. It is a **record of
judgment.**

The distinction is the whole architecture:

> A **decision** — "create an ILIT" — becomes obsolete the moment it is executed or the law moves.
> The **judgment** — "we isolated this asset because liquidity and estate flexibility outweighed
> administrative cost, under these assumptions" — keeps teaching the next decision for decades.

The decision is the artifact. The judgment is the asset. We store the judgment.

## The stack

Driftwood is five layers. Each exists to serve the one below it and is read by the one above.

| Layer | Purpose |
|---|---|
| **Governance** | What the client buys — accountable ownership of how the whole system fits together. |
| **Judgment** | What Driftwood actually produces — reasoning in context, not facts. |
| **Institutional memory** | How judgment compounds across time instead of resetting each year. |
| **Decision Records** | The primitive that stores a unit of judgment. |
| **Manual · AWOR · Operating Sessions** | Interfaces that read and write those records. |

The layer that quietly ties the system together is the middle one. Nino accumulates data; an RIA
generates advice; a CPA files returns. None of them **preserve and compound judgment**. That is the
category Driftwood occupies, and this architecture is how it is delivered.

## The four invariant questions

Every recurring artifact must answer at least one of these; together, the artifacts must answer all
four. If a proposed feature answers none of them, it does not belong in the system.

1. **What decisions currently govern this household?**
2. **Why were those decisions made?**
3. **What assumptions are those decisions resting on?**
4. **What events would require us to revisit them?**

These are the invariant. If they hold, onboarding, the Manual, the AWOR, the Operating Sessions, and
eventually software are all just different interfaces onto the same governance system.

| Question | Field that answers it | Where it surfaces |
|---|---|---|
| 1 · What governs | *(the record's existence + status)* | The Manual (current-state view); the Decision Log |
| 2 · Why | **Rationale** | The Decision Log |
| 3 · On what assumptions | **Assumptions** | Checked by the AWOR |
| 4 · What would reopen it | **Trigger** (with its owner) | Watched by the trigger's named owner; checked at every review |

## The Decision Record — canonical schema

The unit of judgment. Eight fields; three carry the judgment and are non-negotiable. (v1.1 added
**Dependencies** and gave **Trigger** an owner and cadence — see the changelog.)

| Field | Holds | |
|---|---|---|
| **What was decided** | The structural fact | The part that goes obsolete |
| **Rationale** | *Why*, in the household's own goals | **The field that compounds** |
| **Assumptions** | The rates, law, and family facts on the day | What silently goes stale |
| **Alternatives** | What was rejected, and why | Prevents re-litigating settled ground |
| **Owner** | The accountable name | Governance requires a person, not a department |
| **Trigger** | The condition that reopens the decision — **plus who watches it, and how/when** | **What makes review governance, not narrative** |
| **Dependencies** | Which decisions this one **depends on**, and which it **blocks** | **The interactions across time, made a first-class object** |
| **Status + lineage** | State, dates, and links to predecessor/successor | **What preserves memory instead of rewriting it** |

Three of these are architectural, not implementation detail, and are frozen:

- **Rationale** is why the record is an asset and not a log line. It is written in the client's
  context, never as generic advice.
- **Trigger** is what converts the annual review from a re-read into an auditable act: *did the
  condition fire?* A record without a trigger is incomplete — and, as of v1.1, a trigger without a
  named **owner** who watches it and a **cadence** for how it is watched is not yet operational.
- **Supersession** (in Status + lineage) is what preserves institutional memory. A record is never
  edited after it is confirmed and never deleted — only superseded or archived, with the original
  reasoning left intact beside what changed.

### Dependencies — the decision graph (v1.1)

Decisions relate to one another in two different ways, and the schema now names both. **Lineage** is
vertical and historical: a record's predecessor and successor across time (supersession).
**Dependencies** are horizontal and logical: which *currently-live* decisions constrain each other,
and in what order they must be executed. A residency decision *blocks* a business-sale decision,
which *blocks* a diversification decision; recording that ordering is the difference between a pile of
records and a governable plan. Because managing the interactions *between* decisions across time is
the firm's central claim, those relationships must be a first-class field, not prose buried in a
rationale. Dependencies form a directed graph, and it must stay acyclic — if A depends on B, B cannot
depend on A.

### Triggers are owned (v1.1)

A trigger no one is assigned to watch is decoration, not a control. Every trigger therefore carries an
**owner** — Driftwood, the client, or a named professional — and a **cadence** for how it is observed:
*continuous* (a law or market condition Driftwood monitors), *periodic* (checked on a stated schedule),
or *client-surfaced* (a life event only the family can report, which the AWOR must therefore actively
ask about, not passively wait for). The trigger-watch list is the union of these across all live
records, and it becomes a real control only when every line has an owner.

## The lifecycle

A Decision Record moves through four states. **Superseded and Archived are terminal and immutable.**
A record's judgment is frozen the moment it is Confirmed; any change to a live decision is a *new*
record, linked to the one it replaces — not an edit.

```
                    ┌───────────── re-affirm each cycle (dated) ─────────────┐
                    │                                                        │
     ∅ ──create──▶ OPEN ─────── first clean review ───────▶ CONFIRMED ───────┘
                    │  │                                        │
                    │  │        trigger fires / assumption breaks│
                    │  └──────────── opens a successor ──────────┤
                    │                                            ▼
                    │                                       SUPERSEDED ─▶ (terminal, immutable)
                    │  governed structure ceases to exist        ▲
                    └────────────────────────┐                   │ (governed structure
                                             ▼                   │  ceases to exist)
                                         ARCHIVED ◀──────────────┘
                                    (terminal, immutable)
```

**The states**

- **Open** — recorded and governing, but not yet through a full review. Three sub-conditions live
  here: *authored* (fully reasoned, awaiting first confirmation), *deferred* (intentionally held
  pending a trigger — the deferral itself is the judgment), and *placeholder* (a real structure that
  predates Driftwood, catalogued with its rationale still to be captured — the graceful-degradation
  entry point). A placeholder must be authored before it can be confirmed.
- **Confirmed** — reviewed within a cycle: rationale captured, assumptions checked and holding,
  trigger checked and not fired. Still governs. Re-affirmed (with a date) at each subsequent cycle.
- **Superseded** — a trigger fired or an assumption broke, the decision was re-made, and this record
  was closed and linked forward to its **successor**. The successor is a new Open record. The
  original is retained verbatim.
- **Archived** — the structure this record governed no longer exists (the business was sold, the
  policy lapsed, the child is independent). It no longer governs and has **no successor**. It is
  retained solely for the judgment it still teaches.

**The transitions**

| From | To | What causes it | Who performs it |
|---|---|---|---|
| ∅ | Open | A decision is made, or existing structure is catalogued | Onboarding · Operating Session |
| Open | Confirmed | First clean review — rationale captured, assumptions hold, trigger not fired | Operating Session · AWOR |
| Confirmed | Confirmed | Periodic re-affirmation, dated | AWOR (annual) · Operating Session |
| Open / Confirmed | Superseded | Trigger fires or assumption breaks; decision re-made (a successor is opened) | Operating Session · AWOR |
| Open / Confirmed | Archived | The governed structure ceases to exist (no successor) | Operating Session · AWOR |
| Superseded / Archived | — | Terminal. Never edited, never reopened. | — |

"Reopening a decision" is not a state transition — it is the birth of a new record (∅ → Open) whose
lineage points back to the one it supersedes.

## Responsibilities within the lifecycle

The **Decision Log is the system of record** — the append-only, canonical store where every record
in every state lives. It is not an actor; it is the ledger every actor writes to and reads from.
Everything else is an interface onto it.

| Artifact | Creates | Reads | Updates | Its job in the lifecycle |
|---|:---:|:---:|:---:|---|
| **Onboarding** | ● | | | Writes the initial batch — including retroactive records for pre-existing structure and placeholders where rationale is still to be captured. |
| **Operating Sessions** | ● | ● | ● | The write cadence between reviews: opens new records, authors placeholders, confirms, supersedes, archives. |
| **The Decision Log** | | | *(append)* | The single source of truth. Stores all records and their lineage. Never overwrites. |
| **The Manual** | | ● | | A current-state view. Shows which record governs each holding (provenance) and where rationale is not yet recorded. Never a source of truth. |
| **The AWOR** | | ● | ● | The scheduled trigger check: reads every Open/Confirmed record and asks *did its assumption hold, did its trigger fire?* — producing Confirmed, Superseded, or Archived transitions. It is a review measured against recorded intent, not a yearly reset. |

Read this table as the definition of each artifact. The Manual is a **read**; if it ever becomes a
place decisions are *authored*, the architecture has been violated. The AWOR is the **scheduled
reader that triggers writes**; the Operating Session is the **ad-hoc writer**. Onboarding is simply
the first Operating Session.

## Governing principles — invariant across every future version

These hold regardless of how the software evolves. They are the constitution; screens are policy.

1. **The record stores judgment, not the decision.** The reasoning-in-context is the asset; the
   structural fact is disposable.
2. **Append-only.** Confirmed records are immutable; Superseded and Archived are terminal. History
   is preserved, never rewritten. The system's memory is the point.
3. **Every governing structure traces to a record — or to an honest, visible gap.** A client's
   history does not have to begin with Driftwood; unrecorded rationale is surfaced, not hidden, and
   becomes part of the work over time.
4. **Rationale is written in the household's own goals and context**, never as generic advice that
   would read identically for any client.
5. **Every record carries a trigger, and every trigger carries an owner.** A decision with no stated
   condition to revisit it — or a condition no one is assigned to watch — is not yet a complete record.
6. **The Decision Log is the single source of truth; every other list is a view of it.** The Manual,
   the AWOR, the Operating Sessions, and any future application are interfaces onto it. In particular
   (v1.1) the **Opportunity and Risk registers are saved filtered views over the Decision Log, never
   parallel lists** — an opportunity or risk that has been noticed but not yet decided is simply an
   Open record in an *Identified* status, not a separate object. (Register statuses like *Identified*
   or *In progress* are presentation labels over the four lifecycle states, not new states.)
   Interfaces change; the record does not.
7. **The purpose is compounding judgment, not storing facts.** Every mechanism is justified by one
   test: does it help a future decision — possibly made by a different advisor, in a different
   decade, for the next generation — inherit the judgment behind this one?

## Held for a future amendment — under design, NOT frozen

Validation Run 01 surfaced two findings whose fixes would change the *ontology* of the system, not
merely add metadata. They are deliberately **excluded** from v1.1 and recorded here so the reasoning
is preserved and nothing premature is frozen. Neither may be treated as spec until amended.

- **Plural intent → stakeholder objectives (from F-01).** "Household intent" may not be the right
  primitive. In a blended family — and equally with business partners, parents, adult children, or
  trustees — there are *multiple stakeholder objectives*, and the household objective is best modeled
  as an **explicit reconciliation** of them, not a single statement and not merely two intent lines.
  This is a richer model than `Intent(s)` and must be thought through before it is frozen.
- **Operational validity vs. historical certainty (from F-05 / F-16).** "Confirmed" currently
  conflates two orthogonal things: whether a decision is *operationally active*, and whether its
  provenance is *historically certain*. A legacy trust can be fully operational while nobody remembers
  why it exists; a SLAT can be operational while its assumptions have drifted. The likely fix is
  **metadata, not more lifecycle states** — an *Evidence Level* (how certain the recovered rationale
  is) and an *Assumption Status* (whether the assumptions still hold) carried alongside the state — so
  the four-state machine stays simple. To be designed before any amendment.

Both are gated behind a **repeatability check** — a second competent advisor, working only from these
documents, should produce essentially the same records for the same household — before either is
considered for a v1.2.

## What this freezes, and what it leaves open

**Frozen (v1.1):** the four invariant questions; the record schema — now eight fields — especially
Rationale, Trigger (with owner and cadence), Dependencies, and Supersession; the four-state lifecycle
and its transitions; the rule that the registers are views over the Decision Log, not parallel lists;
the responsibility of each artifact; and the seven principles.

**Left to product design:** how any of it looks and feels — the onboarding worksheet's questions and
order, the Manual's layout, the AWOR's sections, the Operating Session's script, the data model and
storage, and eventually the software's screens. Those are implementation onto a stable architecture.

With this frozen, the strategic work is complete. What remains is product design — and the onboarding
worksheet is now an implementation detail, not the thing that defines the process.

---

## Changelog

- **v1.1** — Three bounded amendments from Validation Run 01, none touching the philosophy:
  - Added the **Dependencies** field — the horizontal decision graph (depends-on / blocks), so the
    firm's interactions-across-time claim is representable (F-08).
  - Gave every **Trigger** an **owner** and a **cadence**, so the trigger-watch list is an
    enforceable control rather than a wish (F-17).
  - Declared the **Opportunity and Risk registers to be filtered views over the Decision Log**, never
    parallel lists; a noticed-but-undecided item is an Open record in *Identified* status (F-14, and
    F-13 as a consequence).

  Two deeper findings — plural/stakeholder intent (F-01) and operational-vs-historical certainty
  (F-05/F-16) — are **held under design**, not frozen.
- **v1.0** — Initial frozen architecture.
