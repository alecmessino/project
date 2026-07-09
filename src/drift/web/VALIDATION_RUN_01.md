# Validation Run 01 — a complex household through the frozen operating system

*This is a QA exercise, not a design exercise. [GOVERNANCE_ARCHITECTURE.md](GOVERNANCE_ARCHITECTURE.md)
and [THE_FIRST_90_DAYS.md](THE_FIRST_90_DAYS.md) are treated as **frozen specifications**. The goal
is not to admire the flow — it is to find every place an experienced advisor would hesitate because
the procedure doesn't tell them what to write. Each hesitation is logged as a **Finding** (⟐ F-NN)
and consolidated at the end. New concepts are proposed only where the procedure genuinely fails, and
any change that would touch the frozen spec is flagged as requiring sign-off — QA does not amend the
architecture unilaterally.*

**Finding taxonomy:** `PROMPT` (a question the guide should ask) · `FIELD` (data the record should
carry) · `ARTIFACT` (a missing deliverable) · `IMPOSSIBLE` (the process asks something that can't be
done as written) · `SPEC` (the fix would change the frozen architecture — needs sign-off).

---

## The household — the Adeyemi–Duarte family

Deliberately not simplified. A Coordination Index Tier IV household.

**People.** Marcus Adeyemi (55) and Elena Duarte (52), married 12 years. Marcus has two adult
children from his first marriage — Zoe (29, works in Marcus's business) and Theo (26, estranged-ish,
not involved). Marcus and Elena have one child together, Nia (15). Marcus's first wife is living.

**Money & structures.**
- **Marcus** owns 62% of **Adeyemi Industrial LLC** (taxed as S-corp; industrial services; operates
  in CA, NV, AZ, TX). Two minority partners (38% between them). A **buy-sell agreement** exists;
  funding unclear. A sale or recapitalization is contemplated in 24–36 months. Est. enterprise value
  ~$28M; Marcus's stake ~$17M.
- **Elena** is an SVP at a public semiconductor company: ~$6.2M concentrated single-stock across
  vested RSUs, exercised ISOs (with an AMT credit carryforward), and NQSOs; a **10b5-1 plan** runs
  quarterly. She also has a **NQDC** (deferred comp) balance of ~$2.1M.
- **The Adeyemi–Duarte Family Trust** — joint revocable living trust.
- **A 2011 irrevocable trust** for Marcus's first-marriage children (Zoe, Theo). Drafting attorney
  has since retired; the firm has dissolved. Marcus is fuzzy on its terms and purpose.
- **A 2021 SLAT** Elena funded for Marcus's benefit with ~$2M of her company stock during the
  high-exemption window.
- **A 2019 GRAT** Marcus funded with pre-liquidity company units; the term ends in ~4 months.
- **An ILIT** holding a $5M second-to-die policy; premiums funded by annual gifts.
- **Adeyemi Holdings LP** — a family limited partnership holding a Montana ranch property and a
  ~$1.5M brokerage sleeve; Marcus & Elena are GPs; discounted LP interests were gifted to a trust in
  prior years.
- **A real-estate LLC** owning the commercial building leased back to Adeyemi Industrial.
- **A donor-advised fund** (~$900k) at a national sponsor.
- **529 plans** for Nia.
- Residence in California; a **Montana** vacation property (in the LP); **Nevada residency** is being
  considered ahead of the business sale.
- Contemplated: a **Charitable Remainder Trust** funded with business interest ahead of the sale.

**Family-governance tension (stated up front because it colors everything).** Marcus wants to protect
his first-marriage children and keep the business path open for Zoe. Elena wants all three children
"treated equally" and is uneasy that the 2011 trust and the business favor Marcus's older two. They
have never resolved this.

---

## Phase 1 · The Intent Conversation → Intent Brief

Conducted as Meeting 1 (90 min). Run the two-question pass at household level, then per domain.

> ⟐ **F-01 · `PROMPT` / `SPEC` — the procedure assumes a single household intent.** The Intent Brief
> template ("goals, non-negotiables, fears — in the client's language") has one voice. Ten minutes in,
> Marcus and Elena openly disagree about equal-vs-protective treatment of the children. Whose intent
> becomes the Rationale yardstick every future record is measured against? An experienced advisor
> stops here: do I record a single blended intent, two divergent intents, or the unresolved conflict
> itself? The spec has no answer. **This is the most consequential gap in the run** — a blended family
> is common, not exotic, and the entire governance system measures decisions against "intent" as if it
> were singular.

### Intent Brief — Adeyemi–Duarte (Yr 0)

**What "gone right in twenty years" looks like** — *captured as two voices, per the F-01 workaround
below.*
- *Marcus:* the business transitions on his terms (ideally with Zoe involved), the first-marriage
  children are secure regardless of the marriage, and the family name means something philanthropically.
- *Elena:* the three children are treated as one family; her career equity converts into lasting
  security that isn't hostage to the business; giving is structured, not ad hoc.
- *Shared:* no forced sale of anything under time pressure; the children never litigate against each
  other; taxes are minimized *lawfully and defensibly*, not aggressively.

**Non-negotiables.** Nia's education fully funded regardless of any sale outcome. No structure that
requires the couple to be in lock-step agreement to function (given the unresolved equalization
question). Charitable intent survives both of them.

**Fears.** A business sale that triggers a tax and liquidity scramble; the 2011 trust doing something
nobody remembers agreeing to; the concentrated stock position cratering before it's diversified; the
blended-family estate becoming a fight.

> ⟐ **F-02 · `PROMPT` — Intent has no time horizon or revisit cue.** Intent is captured once, at Yr 0.
> But Nia turning 18, a sale, or a death will move it. Nothing in the procedure says intent itself is
> versioned or re-examined — only decisions carry triggers. An advisor hesitates: is the Intent Brief a
> living record with its own lifecycle, or a founding snapshot? Undefined.

---

## Phase 1 · Structure Inventory

Every existing structure gets a line and a disposition (*capture / capture+verify / reconstruct /
placeholder*).

| # | Structure | Domain | Disposition | Becomes |
|---|---|---|---|---|
| 1 | Adeyemi–Duarte Family Trust (RLT) | Estate | Capture | DR-001 |
| 2 | 2011 children's irrevocable trust | Estate/Family | **Reconstruct → unrecoverable?** | DR-002 |
| 3 | 2021 SLAT (Elena→Marcus) | Estate/Tax | Capture+verify | DR-003 |
| 4 | 2019 GRAT (term ends ~4 mo) | Estate/Tax | Capture+verify | DR-004 |
| 5 | ILIT ($5M second-to-die) | Estate | Capture | DR-005 |
| 6 | Adeyemi Industrial LLC (S-corp, 62%) | Business | Capture | DR-006 |
| 7 | Buy-sell agreement | Business | **Capture+verify (funding unknown)** | DR-007 |
| 8 | Adeyemi Holdings LP (FLP) | Entity/Tax | Capture+verify | DR-008 |
| 9 | Real-estate LLC (building leaseback) | Entity/Tax | Capture | DR-009 |
| 10 | Donor-advised fund | Charitable | Capture | DR-010 |
| 11 | Elena's concentrated stock + 10b5-1 | Investments | Capture | DR-011 |
| 12 | NQDC (deferred comp) | Tax/Liquidity | Placeholder | (pending) |
| 13 | 529 plans (Nia) | Family | Capture | DR-012 |
| 14 | Beneficiary designations (all accts) | Estate | **Capture+verify** | DR-013 |
| 15 | Marcus & Elena estate documents | Estate | Capture+verify | DR-014 |

> ⟐ **F-03 · `PROMPT`/`SPEC` — record granularity is undefined.** Is "the estate plan" one record or
> fifteen? Is the SLAT one record, or does *funding it with concentrated stock* (an investment-concentration
> judgment) + *the distribution standard* + *the trustee choice* deserve separate records? Two competent
> advisors will decompose this household differently — one writes 15 records, another writes 40 — which
> breaks the promise of *consistent* output. The procedure says "one per structure/decision" but never
> defines the unit. **This is the second structural gap.** Needs a granularity rule (e.g., "one record
> per decision that carries its own rationale, assumptions, and trigger" — but that itself needs a worked
> heuristic, and it touches the frozen schema, so: sign-off.)

> ⟐ **F-04 · `IMPOSSIBLE` — the 90-minute Provenance Session cannot cover 15+ interacting structures.**
> At Tier IV this is ~5 minutes per structure, several of which (SLAT, GRAT, FLP, buy-sell) each need 30.
> The procedure implies fixed meeting durations. It should scale meeting count/duration to the
> Coordination Index tier — the tier is already computed and sitting right there, unused for scheduling.

---

## Phase 2 · The Provenance Session → Decision Records

A representative-but-complete set follows (the range that surfaces findings); remaining inventory
lines carry the dispositions above.

### DR-001 — Hold the family assets in a joint revocable living trust
```
State: ● Confirmed   Domain: Estate   Date decided: 2013 (captured Yr 0)   Owner: Estate attorney + Driftwood
WHAT: Marcus & Elena's jointly-held assets titled to the Adeyemi–Duarte Family Trust (revocable).
★ RATIONALE: Probate avoidance and incapacity continuity for a two-earner household with property in
  two states; a revocable trust keeps administration private and out of two probate courts.
ASSUMPTIONS: CA + MT as the only situs states; no estate-tax planning intended at this layer (that
  sits in the irrevocable structures); both spouses competent co-trustees.
ALTERNATIVES: Wills + TOD/POD only — rejected; two-state property makes probate avoidance worth the
  admin. TRIGGER: A state move (esp. the contemplated NV residency), a divorce, or incapacity of a
  co-trustee. LINEAGE: —   Last confirmed: Yr 0 Charter.
```

### DR-002 — 2011 irrevocable trust for the first-marriage children
```
State: ○ Open (rationale UNRECOVERABLE)   Domain: Estate/Family   Date decided: 2011   Owner: ??? 
WHAT: An irrevocable trust f/b/o Zoe and Theo, funded 2011. Terms on file; purpose undocumented.
★ RATIONALE: UNKNOWN. Drafting attorney retired; firm dissolved; Marcus recalls "the lawyer said it
  would protect the kids if anything happened." Reconstruction from the instrument suggests a
  grantor trust for creditor/ divorce protection and to remove early-stage business appreciation from
  the estate — BUT this is inference, not confirmed, and the distribution standard and trustee-
  succession language have real ambiguities that affect Elena's equalization concern.
ASSUMPTIONS: (cannot state original assumptions — see finding)
ALTERNATIVES: (unknown) TRIGGER: (cannot set a meaningful trigger without knowing intent) LINEAGE: —
```

> ⟐ **F-05 · `IMPOSSIBLE`/`SPEC` — the provenance ladder has no terminal for "rationale unrecoverable."**
> The ladder's last rung is "Placeholder — to confirm with [professional]," which assumes the professional
> is reachable. Here they are gone. The record can never reach Confirmed (Confirming requires assumptions
> that hold; there are no known assumptions to hold). An advisor is stuck: DR-002 is a major governing
> structure that is architecturally un-confirmable. The system needs an explicit state or flag —
> *"accepted with reconstructed rationale, provenance unrecoverable, confidence: low"* — or the record
> jams. Touches the lifecycle → sign-off.

> ⟐ **F-06 · `PROMPT` — no protocol for "get the instrument re-read."** The obvious real-world move is
> "have an estate attorney read the 2011 trust and opine on its actual terms." That's an Execution-Bench
> task, but the procedure never tells the advisor to commission a document re-reading, nor where its
> output lands (a new record? an annotation to DR-002?). Missing step.

### DR-003 — SLAT funded with Elena's concentrated stock (2021)
```
State: ○ Open (capture+verify)   Domain: Estate/Tax   Date decided: 2021   Owner: Estate attorney + Driftwood
WHAT: Elena funded a spousal lifetime access trust for Marcus's benefit with ~$2M of company stock
  during the elevated federal exemption window.
★ RATIONALE: Use exemption before a scheduled sunset; move future stock appreciation out of the
  estate while retaining indirect access through Marcus as beneficiary.
ASSUMPTIONS (2021): exemption sunset as then-scheduled; the marriage intact (SLAT access depends on
  it); the funded stock appreciates. ★ Two of three assumptions are now stale/at-risk: exemption law
  has moved AND the stock is now a concentration problem the couple wants to diversify — but it sits
  in an irrevocable trust.
ALTERNATIVES: Outright gift (rejected — no access); wait (rejected — exemption risk). TRIGGER: exemption
  law change, divorce, or a decision to diversify the trust's concentrated holding. LINEAGE: —
```

> ⟐ **F-07 · `FIELD`/`SPEC` — "assumptions at the time" is temporally ambiguous for retroactive records,
> and there is no field for *current validity*.** DR-003 has 2021 assumptions, two of which are now
> broken. The schema records assumptions-at-decision but has nowhere to record *"as of Yr 0 capture,
> these still hold / these have broken."* The advisor wants to write both and can't without inventing a
> field. Without it, a 2036 reader can't tell whether anyone ever checked. (This is arguably what the
> AWOR does — but for a retroactive record captured mid-life, the first check happens at capture, not a
> year later.) Needs a `Validity-at-capture` note or an explicit first-review stamp. Schema → sign-off.

### DR-006 / DR-011 / DR-015 — the interlocking sale sequence (forward decisions)

These are the forward decisions opened before the Charter Session. They are **not independent** — and
that is the point.

```
DR-011 — Diversify Elena's concentrated position   State: ○ Open   Domain: Investments
★ RATIONALE: $6.2M in one semiconductor name is ~40% of liquid net worth; concentration risk dwarfs
  expected excess return. Diversify via accelerated 10b5-1 + gifting appreciated shares to the DAF/CRT
  rather than selling into tax.
TRIGGER: position >X% of net worth; a blackout lift; the CRT decision (DR-016).
DEPENDS ON: DR-016 (CRT), DR-018 (NV residency) — sequencing changes the tax outcome materially.
```
```
DR-016 — Fund a CRT with business interest ahead of the sale   State: ○ Open   Domain: Charitable/Tax
★ RATIONALE: Contribute a slice of Adeyemi Industrial to a CRT pre-sale to defer/spread gain and
  create an income stream + a DAF-aligned remainder — but only if done before a binding sale agreement.
DEPENDS ON: DR-006 (sale structure), DR-018 (residency), and the buy-sell (DR-007) permitting the
  transfer. TRIGGER: a letter of intent on the business (hard deadline — after LOI this option narrows).
```
```
DR-018 — Establish Nevada residency before the sale   State: ○ Open   Domain: Multistate/Tax
★ RATIONALE: Move ~$17M of sale gain out of CA source taxation by substantiating NV domicile well
  before a close; the order is the whole value.
DEPENDS ON: nothing upstream. IS DEPENDED ON BY: DR-006, DR-011, DR-016. TRIGGER: a buyer timeline
  that would force a close before residency is defensible.
```

> ⟐ **F-08 · `FIELD`/`SPEC` — the schema has no dependency/sequencing field, yet sequencing is the
> firm's stated advantage.** GOVERNANCE_ARCHITECTURE calls optimizing interactions-across-time the
> product, but the Decision Record's only relational field is `lineage` (supersession). There is nowhere
> to record "DR-016 must precede DR-006, which must follow DR-018." I had to invent a `DEPENDS ON` line
> to write these at all. Four interlocking records with an ordering constraint cannot be represented in
> the frozen schema. **This is the third structural gap and the most technically important** — it's the
> difference between a pile of records and a governable plan. A `Depends-on / Blocks` field (a DAG) is
> the minimal fix. Schema → sign-off.

> ⟐ **F-09 · `PROMPT` — no guidance on writing a *forward* decision's assumptions when they're
> forecasts, not facts.** DR-016's "assumptions" are projections (a sale will happen; value ≈ $28M; law
> holds). The guide's assumptions prompt ("law, rates, family facts") reads as present-tense facts. An
> advisor hesitates on how to record probabilistic assumptions and at what confidence. Add a forward-
> looking prompt + a confidence marker.

### DR-004 — the expiring 2019 GRAT (a supersession in motion)
```
State: ○ Open → to be Superseded   Domain: Estate/Tax   Date decided: 2019   Owner: Estate attorney + Driftwood
WHAT: GRAT funded 2019 with pre-liquidity units; annuity term ends in ~4 months; remainder passes to
  a grantor trust for the children.
★ RATIONALE (2019): freeze/transfer appreciation on units expected to jump in a liquidity event, at
  near-zero gift cost. ASSUMPTIONS: Marcus survives the term (he has); units appreciate (TBD at sale).
TRIGGER: term expiry (imminent) → decision required on the remainder and whether to roll a new GRAT.
```

> ⟐ **F-10 · `PROMPT` — the Operating Session agenda handles "trigger fired → supersede," but not a
> trigger that fires on a *calendar certainty* requiring a fresh decision.** The GRAT term ending isn't
> an assumption breaking; it's a scheduled maturation that demands a *new* decision (roll it? let it
> pass?). Is that a supersession, or a brand-new record with a lineage link, or both? The agenda step
> "Supersede the records whose trigger fired" doesn't cleanly fit a maturation event. Needs a defined
> handling for scheduled-maturation triggers.

### DR-010 / DR-017 — the DAF and the family philanthropic mandate (a values decision)
```
DR-017 — Govern family giving through the DAF as a multi-generational vehicle   State: ○ Open   Domain: Family/Charitable
★ RATIONALE: Elena and Marcus want giving to be a shared family practice that outlives them and gives
  the three children a neutral table to act as one family — explicitly chosen as a governance tool, not
  just a tax vehicle. Successor advisors: the DAF's PURPOSE is family cohesion first, deduction second.
ASSUMPTIONS: the children will participate; the DAF sponsor permits successor advisors across
  generations. TRIGGER: a child declines to participate; a values divergence; sponsor policy change.
```

> ⟐ **F-11 · `PROMPT`/`SPEC` — non-structural "values / family-governance" decisions strain the schema.**
> "Every governing structure traces to a record." DR-017 governs *behavior and intent*, not a structure —
> and yet it's exactly the kind of judgment a 2036 advisor most needs ("why is the DAF run this way?").
> It fits the fields, but the procedure never tells the advisor that values decisions are in-scope, so a
> literal-minded advisor would omit it and a broad one would include it → inconsistent. Add an explicit
> domain and a prompt for governance/values decisions.

### DR-007 — buy-sell agreement (the "we don't know" that's a live risk)
```
State: ○ Open (capture+verify — funding unknown)   Domain: Business   Owner: Business counsel + Driftwood
WHAT: A buy-sell among the three owners exists; whether it is insurance-funded, and whether its
  valuation clause matches current EV, is unknown pending counsel review.
★ RATIONALE: (to be recovered) presumably to force an orderly transfer on death/disability/exit.
TRIGGER: any owner's death/disability, or the contemplated sale — either could invoke a stale formula.
```

> ⟐ **F-12 · `PROMPT` — the boundary between a `capture+verify` Decision Record and a Risk-register
> line is undefined.** DR-007 is simultaneously an Open record AND obviously a Risk ("stale/underfunded
> buy-sell"). Do I write it once (as a record, and the register *reads* it) or twice? The architecture
> forbids parallel sources of truth, which implies the register must be a *view* of records — but
> THE_FIRST_90_DAYS describes the registers as assembled findings, not as a projection of records. These
> two frozen documents are in mild tension. Needs an explicit statement: **registers are views over
> records, not parallel lists.** (See F-14.)

---

## Phase 3 · Opportunity & Risk Registers

Assembled — but per F-12/F-14, assembled *as a read over the records above*, each line tracing to a DR.

**Opportunity Register** (Basis → record)
| Opportunity | Basis | Status |
|---|---|---|
| Sequence residency → CRT → sale for maximum after-tax | DR-018·016·006 | Identified |
| Diversify concentrated stock via charitable gifting, not sale | DR-011·010 | Identified |
| Roll or retire the 2019 GRAT remainder at term | DR-004 | Needs action |
| Equalize the blended-family estate deliberately | DR-002·014·(F-01) | Identified |

**Risk Register** (Basis → record)
| Risk | Basis | Status |
|---|---|---|
| 2011 trust terms unknown; may conflict with equalization intent | DR-002 | Open (unrecoverable) |
| Buy-sell possibly unfunded / stale valuation | DR-007 | Open |
| Concentrated stock (~40% of liquid NW) before diversification | DR-011 | In progress |
| SLAT holds concentrated stock the couple wants to diversify but can't easily reach | DR-003 | Open |
| CA source tax on a $17M gain if residency isn't sequenced first | DR-018 | Open |

> ⟐ **F-13 · `ARTIFACT` — there is no home for an opportunity/risk that is real but has no decision
> yet.** "Concentrated stock is 40% of net worth" is a risk the day it's noticed, *before* DR-011 is
> opened. During the run I could only list it by pointing at a record that didn't exist until I wrote it.
> What holds a surfaced-but-undecided concern in the minutes/hours before it becomes a record? Either
> risks can exist without a record (violating single-source-of-truth) or every noticed concern must be
> instantly recorded (heavy). Undefined.

> ⟐ **F-14 · `SPEC` — the two frozen docs disagree on whether registers are views or lists.**
> GOVERNANCE_ARCHITECTURE: "no parallel source of truth; the Manual reads from the Log." THE_FIRST_90_DAYS
> Phase 3: registers are "findings from Phase 2." If findings are their own list, they're parallel truth;
> if they're projections of records, they can't hold undecided items (F-13). The spec must pick one. QA
> recommendation (not applied): **registers are saved views/queries over the Decision Log** — but that
> forces every risk to be at least a stub record, which resolves F-13 by making "noticed concern" a valid
> Open sub-state. Sign-off required.

---

## Phase 3 · The Wealth Operating Manual v1 (assembled as a read)

| Section | Populated from | Notes surfaced |
|---|---|---|
| Team & who owns what | Owners on DR-001…014 | ⟐ **F-15 below** |
| Balance sheet & ownership | Structures 1–15, each Basis→DR or *Next session* | NQDC (#12) shows *Next session* |
| Coordination Index | Drivers: business, 4 entities, 3 trusts, equity comp, multistate, blended family | Tier IV (~12/14) |
| Operating calendar | Union of triggers across all open records | GRAT term (4 mo) is the nearest hard date |
| Decision dashboard (forward) | DR-006, 011, 016, 018 (+ dependency ordering) | dependency arrows can't render (F-08) |
| Opportunity / Risk registers | views over records (F-14) | 2 items lack a clean record home (F-13) |

> ⟐ **F-15 · `FIELD` — "Owner = accountable name," but half the records have *shared* or *external*
> owners.** DR-002's owner is genuinely unknown; DR-003/007's owner is "estate attorney + Driftwood" —
> two parties. The Manual's "who owns what" wants one accountable name per line and the records don't
> supply it cleanly. Is Driftwood *always* the accountable owner (as coordinating principal) with the
> professional as executor? That's a defensible rule — but the procedure doesn't state it, so advisors
> will fill Owner inconsistently. Define Owner precisely (recommend: Owner = the single accountable
> principal; a separate `Executor(s)` field lists the professional[s]). Small schema touch → sign-off.

Manual v1 is assembleable. It publishes with 14 records (5 Confirmed at Charter, 9 Open), 1 placeholder
(NQDC), and 4 forward decisions. It is dated `v1`, Yr 0.

---

## Phase 3 · The Charter Session (first Operating Session)

Running the agenda against the founding set:
- **Confirm:** DR-001, 005, 009, 012, 013 — assumptions hold, triggers set. → Confirmed.
- **Cannot confirm:** DR-002 (unrecoverable, F-05), DR-003 (assumptions already broken — do we confirm a
  record whose assumptions we *know* have failed, or immediately supersede it? F-16), DR-007 (pending
  counsel).
- **Open + set triggers:** DR-006, 011, 016, 018 (with the dependency ordering the schema can't hold).
- **Supersede:** DR-004 pending the term-end decision (F-10).
- **Placeholders owned:** NQDC → Elena's employer benefits contact, due next session.

> ⟐ **F-16 · `IMPOSSIBLE` — you cannot "Confirm" a record whose assumptions are already known broken,
> and the lifecycle offers no other move at first review.** DR-003's stock-concentration assumption has
> failed *before its first confirmation*. Confirm = "assumptions hold" (false here). Supersede =
> "decision re-made" (it hasn't been — the SLAT still stands; only its context changed). Archive = "structure
> gone" (it isn't). The record has no valid transition at the Charter Session. This is a genuine
> state-machine hole for **retroactively-captured records that arrive already stale** — extremely common.
> Likely needs a `Flagged` / `Review-required` sub-state of Open. Lifecycle → sign-off.

---

## Phase 4 · AWOR setup & trigger-watch

**Trigger-watch list** (union of open-record triggers), with the attribute the run revealed is missing:

| Trigger | From | Who watches / how observed |
|---|---|---|
| Federal exemption law change | DR-003, 005 | **Driftwood (continuous)** |
| Business LOI / binding sale | DR-006, 011, 016 | **Client must surface** |
| GRAT term expiry (~4 mo) | DR-004 | Driftwood (calendar) |
| Concentration > threshold | DR-011 | Driftwood (quarterly) |
| Residency defensibility at risk | DR-018 | Shared |
| A child declines DAF participation | DR-017 | Client must surface |

> ⟐ **F-17 · `FIELD` — a trigger with no owner is not monitored.** The architecture says "every record
> carries a trigger" but never says *who watches it or how*. Half these triggers only fire if the client
> volunteers a life event; the other half Driftwood must monitor. Without a `Monitored-by / observable-how`
> attribute per trigger, the trigger-watch list is a wish, not a control. This is the retention engine's
> load-bearing detail and it's absent. Schema/artifact → sign-off.

> ⟐ **F-18 · `PROMPT` — the AWOR's "did the trigger fire?" is unanswerable for client-surfaced triggers
> the client didn't surface.** If "a child declines DAF participation" happened quietly, the annual pass
> won't catch it. The AWOR needs a prompt set that actively *asks* the family about the client-surfaced
> triggers, not just checks the observable ones. Missing from the AWOR agenda.

---

## Consolidated Findings Register

18 hesitation points. Ranked by whether they block *consistent* output. **None are cosmetic.**

| # | Type | One-line | Blocks consistency? | Touches frozen spec? |
|---|---|---|---|---|
| F-01 | PROMPT/SPEC | Single-household-intent assumption fails for blended families | **High** | Yes |
| F-03 | PROMPT/SPEC | Record granularity undefined (15 vs 40 records) | **High** | Yes |
| F-08 | FIELD/SPEC | No dependency/sequencing field — the stated advantage can't be recorded | **High** | Yes |
| F-16 | IMPOSSIBLE | Retroactive records that arrive already-stale have no valid transition | **High** | Yes (lifecycle) |
| F-05 | IMPOSSIBLE/SPEC | No terminal for "rationale unrecoverable"; record can't reach Confirmed | **High** | Yes (lifecycle) |
| F-14 | SPEC | Two frozen docs disagree: registers = views or lists? | **High** | Yes |
| F-17 | FIELD | Triggers have no monitor/owner → watch-list is unenforceable | **High** | Yes |
| F-07 | FIELD/SPEC | "Assumptions at the time" temporally ambiguous; no current-validity field | Med | Yes |
| F-15 | FIELD | Owner semantics (single vs shared vs external) undefined | Med | Minor |
| F-13 | ARTIFACT | No home for a noticed risk before it's a decision | Med | Maybe |
| F-11 | PROMPT/SPEC | Values/family-governance decisions in-scope? unclear | Med | Minor |
| F-04 | IMPOSSIBLE | Meeting durations don't scale to Coordination tier | Med | No (procedure) |
| F-09 | PROMPT | No guidance for forward/probabilistic assumptions + confidence | Med | No |
| F-10 | PROMPT | Scheduled-maturation triggers don't fit "supersede" cleanly | Med | No |
| F-18 | PROMPT | AWOR can't check client-surfaced triggers without asking | Med | No |
| F-06 | PROMPT | No step to commission re-reading of an opaque instrument | Low | No |
| F-02 | PROMPT | Intent Brief has no lifecycle of its own | Low | Maybe |
| F-12 | PROMPT | DR-vs-Risk-line boundary fuzzy (subsumed by F-14) | Low | Yes |

**The five that actually matter** (fix these and the system is executable for real complexity):
1. **F-08 dependency graph** — without it, "we optimize interactions across time" is unrecordable. The
   single most important gap, because it's the moat made concrete.
2. **F-01 plural intent** — blended families are the norm at this asset level; a single-intent yardstick
   silently mis-measures every downstream decision.
3. **F-16 + F-05 lifecycle holes** — retroactively-captured records routinely arrive stale or
   provenance-less; the four-state machine has no move for either, so real onboarding jams on day one.
4. **F-17 trigger ownership** — the retention/annuity engine depends on triggers actually being watched;
   an unmonitored trigger is decoration.
5. **F-14 registers-as-views** — resolve the contradiction between the two frozen docs before either is
   built into software, or two teams build two truths.

---

## Verdict — does the paper test pass?

**Partially, and instructively.** A skilled advisor *can* carry the Adeyemi–Duarte family through the
90 days on paper and produce every artifact — Intent Brief, Inventory, Records, Registers, Manual v1,
AWOR setup. So the workflow's spine holds under genuine complexity.

**But two advisors would not produce the same records**, because of F-03 (granularity), F-01 (whose
intent), and F-08 (no way to encode the sequence). And the lifecycle **jams** on two extremely common
cases — the stale-on-arrival retroactive record (F-16) and the unrecoverable-provenance record (F-05).
So the system is *executable* but not yet *consistently* executable — which is exactly the distinction
this run existed to find.

**The 2036 test** — *can another advisor pick up the Adeyemi record and understand not just what was
done but why?* — passes for the clean records (DR-001, 003, 016 read beautifully a decade out) and
**fails precisely where the findings cluster**: they'd inherit DR-002 with no idea why it exists, a
sale sequence with no recorded ordering, and a trigger list nobody was assigned to watch.

**QA conclusion:** the architecture is sound and the procedure is close. It is not yet ready to freeze
into software. Resolving the five priority findings — four of which are small, bounded additions to the
frozen schema/lifecycle and therefore need your explicit sign-off — would take the system from
"executable by its author" to "consistently executable by any advisor," which is the real bar. No new
philosophy is required; the discoveries are all at the level of fields, states, and prompts, exactly
where a validation exercise should leave them.

---

## Resolution status — updated after founder authorization (v1.1)

The findings were triaged into a bounded amendment. This section keeps the register a living record.

**Resolved in Governance Architecture v1.1** (folded into the frozen spec + the 90-day procedure + the
Decision Record form):
- **F-08** — a first-class **Dependencies** field (depends-on / blocks; acyclic decision graph).
- **F-17** — every **Trigger** now carries an **owner** and a **cadence** (continuous / periodic /
  client-surfaced).
- **F-14** — the **Opportunity/Risk registers are filtered views over the Decision Log**, not parallel
  lists; **F-13** and **F-12** are resolved as a consequence (a noticed-but-undecided item is an Open
  record in *Identified* status).
- **F-18** — partially picked up by F-17: client-surfaced triggers are the ones the AWOR must actively
  ask about.

**Held under design — deliberately NOT frozen** (would change the ontology; each reframed by the
founder to a better primitive than the raw finding proposed):
- **F-01** → *stakeholder objectives with an explicit household reconciliation*, not `Intent(s)`.
- **F-05 / F-16** → separate *operational validity* from *historical certainty* via metadata
  (*Evidence Level*, *Assumption Status*), not new lifecycle states.

**Open — procedure-level, not yet actioned** (prompts/guidance in THE_FIRST_90_DAYS, no architecture
impact; awaiting direction): F-02 (Intent Brief's own lifecycle), F-04 (scale meeting time to the
Coordination tier), F-06 (a step to commission re-reading an opaque instrument), F-09 (forward /
probabilistic assumptions + confidence), F-10 (scheduled-maturation triggers), F-11 (values/governance
decisions explicitly in-scope), F-15 (precise Owner semantics).

**Gate before any v1.2:** a **repeatability run** — a second competent advisor, working only from the
frozen documents, executes the *same* household from scratch. Every materially different artifact is a
residual ambiguity in the spec. Repeatability, not correctness, is the bar at this stage.
