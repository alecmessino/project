# Driftwood v1 Refinement Backlog

*The working checklist for the polish phase — shift from building capability to refining the
experience (depth, clarity, narrative, conversion), not adding breadth. Compiled from a three-lens
usability assessment (prospect · CPA/attorney · advisor) of the four flagships + homepage + the
conversion journey.*

## Locked decisions (principal, this cycle)

1. **Returns figure** — *keep the analysis, remove the headline return framing.* The public layer
   reads **Coordination Opportunity → dollar impact → explanation**; the modeled `+X%/yr` moves to the
   deep methodology / advisor / Household-Record layers. Governs the Atlas hero (→ "Estimated After-Tax
   Coordination Opportunity, $XX,XXX/yr"), the Atlas-index column ("Tax Management Impact" →
   "Illustrative Coordination Opportunity"), and the Comparison impact line ("Illustrative coordination
   gap"). *Scheduled for the flagship-refinements phase (step 3), not the spine.*
2. **Build sequence** — (1) forward spine → (2) homepage narrative → (3) flagship-specific refinements
   → (4) final category-consistency audit.

## Homepage template of record

The marketing homepage is **`src/drift/web/hub.html`** (`sync_docs.py` maps `hub.html → docs/index.html`;
the confusingly-named `src/drift/web/index.html` renders to `docs/equities.html`, the markets hub).
Never hand-edit `docs/*.html`.

## Status

- **PR #84 — the forward spine** *(this PR)* — DONE: a narrative process spine
  (`Environment → Compare → Plan → Coordinate → Review`) on every flagship; onward CTAs where surfaces
  dead-ended (Atlas index → Compare/Crossing/Household; Comparison → coordination record + Crossing;
  Crossing → "Prepare this as your Household Record"; Household → terminal meeting CTA); one-click
  Calendly from flagship body CTAs; this backlog committed.
- **PR #85 — homepage** — NEXT (awaiting approved hero + diagnostic copy): the complexity-threshold
  narrative + the interactive recognition diagnostic.
- **PR #86+ — flagship refinements** — the returns reframe (decision 1) and the remaining ranked items.
- **PR #87 — category-consistency audit.**

---

# DRIFTWOOD v1 REFINEMENT BACKLOG

*(Compiled from 3-lens findings, de-duplicated and ranked against the principal's strategic frame. 41 raw findings → 32 backlog items.)*

---

## 1. THE THROUGH-LINE

Every public surface currently **leads with the answer (coordination / a tax figure) instead of the realisation ("my financial life has crossed a complexity threshold")**, and the funnel **leaks at both ends** — the homepage never opens the recognition, and the deep flagships (Atlas → Comparison → Crossing → Household Record) each dead-end backward or sideways instead of pulling toward a meeting. The single job of the polish phase is to (a) open the homepage on the prospect's lived complexity threshold and drop in the recognition diagnostic, then (b) install a one-directional forward spine so that every surface, especially the highest-intent ones, has an obvious reason to go deeper and a clean one-click path to book.

**One flag before anything ships:** findings cite the homepage template as both `src/drift/web/hub.html` and `src/drift/web/index.html`. Confirm which is canonical (per CLAUDE.md, `sync_docs.py` re-renders `docs/index.html`; never hand-edit `docs/*.html`).

---

## 2. RANKED BACKLOG (highest impact first)

**1. Reframe the homepage hero to the complexity threshold** *(DIRECTED)*
- Surface: Homepage (`src/drift/web/hub.html` `.hero` block → `docs/index.html` 252-254) · Lens: Prospect + CPA/Attorney · Narrative · **High** · **Medium**
- Build: Replace the framework-first opener ("Most advisors manage investments." / h1 "Driftwood coordinates your financial life as one system.") with a three-beat arc: (1) kick names the threshold — *"More accounts. More entities. More advisors. Every good decision now depends on three others."*; (2) pivot — *"You already have excellent specialists. What no one owns is how they work together."* (this line doubles as the CPA/attorney non-replacement reassurance, see #16); (3) only then the h1 introduces coordination as the resolution. Re-render via `scripts/sync_docs.py`.
- Conversion rationale: A prospect who hasn't self-diagnosed can't act on a solution. Making them *feel* the threshold first is what earns the next click.
- **EDITORIAL DECISION for the principal:** exact hero copy.

**2. Build the interactive recognition diagnostic** *(DIRECTED)*
- Surface: Homepage, new block immediately after hero · Lens: Conversion (Prospect) · Conversion · **High** · **Large**
- Build: Net-new interactive block + small JS handler (mirror the existing systems-diagram JS pattern already in the file). 5-6 checkable self-recognition prompts from the frame — *"My CPA and advisor rarely communicate" · "I have multiple custodians or account structures" · "My estate plan hasn't been reviewed alongside my investments" · "I'm considering relocating or have multiple residences" · "My business, equity comp, or trusts have increased complexity."* Checks tally into a results state ("your highest-value coordination opportunities") whose CTA is **"Identify your highest-value coordination opportunities"** (recognition, not urgency) and which routes into `/atlas/2026/`. Demote the current `leakage.html` Tax Diagnostic to a secondary downstream link.
- Conversion rationale: This is the missing Homepage→Diagnostic transition and the whole funnel's on-ramp; it converts a broad realisation into a personalised reason to enter the Atlas.
- **EDITORIAL DECISION:** prompt wording, tally logic, results-screen copy, and where each result routes.

**3. Give the hero one primary CTA**
- Surface: Homepage `.hero .ctas` (`docs/index.html` 257-260, primary style defined 93) · Lens: Conversion · Hierarchy · **High** · **Small**
- Build: The hero currently has *two* `.ghost` links and no `.primary`; the only `.primary` ("Schedule a conversation →") is buried at the page bottom (518). Apply `.primary` to the diagnostic CTA ("Identify your coordination opportunities"), keep at most one `.ghost` beside it, reserve bottom "Schedule a conversation" as the terminal CTA.
- Conversion rationale: At the highest-intent moment (first screen) the visitor gets one emphasised path instead of two equally-weighted faint ones.

**4. Reorder homepage: realisation + diagnostic before the "operating system" archive**
- Surface: Homepage section order (`docs/index.html` "The operating system" 264-291) · Lens: Prospect · Narrative · **High** · **Medium**
- Build: The section directly under the hero opens on *how we operate* (Wealth Operating Manual, Decision/Opportunity Registers, Annual Review) — "how" before the prospect has a reason to care. The `hub.html` line-55 comment claims order "problem → category → how" but the render skips problem/category. Move the complexity-realisation beat + diagnostic + five-systems thesis above the operating-system archive.
- Conversion rationale: Emotional arc must precede operational proof or the proof lands on no one.

**5. Build the homepage on-ramp to the four flagships + fix the nav target**
- Surface: Homepage body + nav (`docs/index.html` 244, 354-382) · Lens: Conversion · Conversion · **High** · **Medium**
- Build: Today the body routes to `leakage/taxlab/coordination/library/manual/decision-register`; Atlas appears only obliquely as "State Tax Atlas" → `statemap.html`, and Comparison/Crossing/Household are effectively unreachable without knowing URLs. Surface the four flagships by consistent name (Atlas · Comparison · Crossing Brief · Household Record) as an explicit entry (card row or diagnostic result) deep-linking to `/atlas/2026/`, `/compare/`, `/crossing/`, `/household/`, and repoint the nav "State Tax Atlas" to `/atlas/2026/` (not `statemap.html`).
- Conversion rationale: Establishes the forward spine from the front door; without it the documented journey has no entrance.

**6. Add the forward rel-bar + CTA to the Atlas *index***
- Surface: Atlas index (`render_states_index`, `src/drift/statepage.py:687` → `docs/atlas/2026/index.html`) · Lens: Conversion · Conversion · **High** · **Small**
- Build: After the 51-row table the page goes straight to as-of → disclosure → footer with no onward path — strictly *less* connected than its own state leaves. Add the same `.rel` bar and `.cta` the state page already carries (links to `compare/`, `crossing/`, `household/`, plus a meeting CTA).
- Conversion rationale: Flagged in findings as "the single highest-leverage funnel fix" — organic-search landers on the index currently have nowhere to go but into one state.

**7. Crossing Brief → forward CTA to Household Record + meeting**
- Surface: Individual brief (`render_crossing_html`, `crossingpage.py` 246-254) · Lens: Conversion · Conversion · **High** · **Small**
- Build: Highest-intent surface, yet its CTAs ("Florida Atlas →" primary, "Compare the two →" ghost, "Crossing Brief index →") all pull *up-funnel*. Replace with forward pair: primary **"Prepare this as your Household Record →"** (`/atlas/{edition}/household/`), secondary **"Start a conversation →"**; demote Atlas/Compare links to a small "Read either environment in full" footnote. Place the meeting CTA right after "Questions worth asking" to capture the momentum those questions build.
- Conversion rationale: The person reading a specific corridor brief because a move is real is exactly who should reach a meeting — currently they're sent backward.

**8. Household Record → terminal meeting CTA (close the final leak)**
- Surface: Household Record brief + index (`render_household_html`, `householdpage.py` ~194-202) · Lens: Conversion · Conversion · **High** · **Medium**
- Build: The last surface before Meeting dead-ends into governing-docs → principle → provenance → disclosure, with the `.cta` CSS defined but unused. Add a closing `.cta` (reuse styles) anchored to the "Opportunities open" the file just surfaced (e.g. "Asset titling for step-up review"): recognition-framed copy — *"This is how one household's system is coordinated. Ours would begin the same way — as a standing record, not a folder."* — primary "Start a conversation", ghost back to Atlas. Same on the index after the sample cards: *"If your household spans more than one state, entity, or advisor, this is the file we would build first."*
- Conversion rationale: This is where the entire funnel leaks at its final step; the visitor who traveled the whole journey is otherwise handed no human.

**9. Comparison corridor → forward handoff to the Crossing Brief**
- Surface: Corridor page (`render_comparison_html`, `comparepage.py` 246-254) · Lens: Conversion · Conversion · **High** · **Small**
- Build: The deepest comparison surface only offers "Read either environment in full" (Atlas) and "Weigh another pair" (lateral) — no forward step, though it even states direction ("the destination other households move toward, not from"). Add a directional Crossing handoff *above* the Atlas CTA, reusing the index copy pattern (`comparepage.py:407`): *"Moving from California to Texas? A Crossing Brief turns this difference into a sequenced operating plan — who does what, in what order."* Make Atlas links secondary/ghost.
- Conversion rationale: Installs the Comparison→Crossing transition where intent is concentrated.

**10. Reframe the Atlas state page: recognition first, coordination above alpha**
- Surface: Illinois/state page (`statepage.render_state_html`, `.hd` ~648; reasoning chain `illinois/index.html` 203-213) · Lens: Prospect + Advisor · Narrative + Hierarchy · **High** · **Medium**
- Build: Page opens as a pure tax lecture ("How Illinois taxes investors." + 7 statutory cards); "coordination" first appears at line 207 far below the fold. Insert one framing sentence between H1 and the dimension grid: *"If you have a CPA, an estate attorney, and an advisor, each already handles their piece of Illinois's code well. What no one owns is how these decisions fit together — this page maps that surface."* Then reorder `render_state_html` so the reasoning chain (Decision Framework → "Coordination priorities … with your advisor + CPA / estate attorney" → numbered "What should happen next" action register) sits *above* the illustrative-impact section — so an advisor screen-sharing lands on coordination, not a return figure.
- Conversion rationale: Makes the reference read as recognition and puts the meeting-ready, advisor-lens material first.

**11. Demote / reframe the Atlas "+4.0%/yr" alpha hero**
- Surface: State page navy hero (`_impact_block`, `illinois/index.html` 196) · Lens: CPA/Attorney · Hierarchy · **High** · **Medium**
- Build: The loudest element on the page is a 44px "+4.0%/yr" kept-vs-lost performance figure — a returns claim that reads as "Driftwood outperforms," cutting against the improves-not-replaces test and forcing a heavy hypothetical-performance disclaimer. Shrink it / move it below the coordination sections and relabel from a return toward *what coordinated execution is worth* (the levers below — asset location, lot selection, harvesting — are already framed as "Coordination itself"). Pairs with #10.
- Conversion rationale: Removes the one element most likely to make a CPA/attorney read Driftwood as a competitor.
- **EDITORIAL DECISION for the principal (positioning, applies to #11, #14-column, #19):** does Driftwood surface a "+X%/yr" performance number publicly at all, and if so how prominent/relabeled? This is one call across Atlas hero, the Atlas-index "Tax Management Impact" column, and the Comparison impact line.

**12. Atlas state page: promote Comparison/Crossing, add Household Record, keep diagnostic secondary**
- Surface: State page `.cta` / `.rel` (`illinois/index.html` 219, 255) · Lens: Conversion · Conversion · **High** · **Small**
- Build: Primary CTA is "Run my Illinois diagnostic →" (`leakage.html`) — a step *before* Atlas in the journey — while the true next steps, Comparison ("weigh two states →") and Crossing ("plan a move →"), are a 12.5px text row indistinguishable from "nearby regimes." Household Record isn't linked at all. Promote Comparison + Crossing to first-class onward steps with one-line reasons ("weigh Illinois against the state you're considering" / "if a move is on the table, see the crossing brief"), add a Household Record link, demote the diagnostic to a quiet fallback. Also collapse the three stacked asks at the foot (diagnostic + "Start a conversation" + email capture, 219-227) to one primary + one quiet secondary — see #31.
- Conversion rationale: Stops the Atlas from pulling visitors back to a step they already passed.

**13. Fix "Opportunities the move opens" so the label matches the payload**
- Surface: Crossing Brief (`_opportunities`, `crossingpage.py` 139-147) · Lens: Advisor · Narrative · **High** · **Medium**
- Build: In Illinois→Florida, 4 of 5 rows are "Stands down" items with the identical templated line "no longer triggered at the destination — one fewer thing to coordinate," duplicating the "Standing decisions to reconsider" section directly above; only one row genuinely opens. Split into two honestly-named registers, or collapse the four stand-downs into one line (*"Four origin-state priorities stand down: residency, estate structure, loss harvesting, asset location — the move simplifies the household's coordination load"*) and reserve "Opportunities the move opens" for genuine opens.
- Conversion rationale: An advisor shouldn't have to explain a section that contradicts its own heading live.

**14. Point all flagship "Start a conversation" CTAs directly at Calendly**
- Surface: Journey — `dwnav-cta`, crossing/household/state CTAs · Lens: Advisor · Friction · **Medium** · **Small**
- Build: Deep-page CTAs point to `index.html#conversation` (homepage close), forcing a second click on "Schedule a conversation →" with a full context reset. Point them straight at the Calendly URL the homepage close uses, so booking from any flagship is one click.
- Conversion rationale: An advisor demoing a flagship live can book in one action; removes a whole hop from every deep-surface conversion.

**15. Cross-link the four flagships as one navigable system (breadcrumb + lateral strip)**
- Surface: Journey — all four index renderers (`statepage.py`, `comparepage.py`, `crossingpage.py`, `householdpage.py`) · Lens: Conversion · Hierarchy · **Medium** · **Medium**
- Build: `.bcrumb` styles are defined in every flagship template but no breadcrumb is rendered; lateral links are partial (Comparison→Crossing exists, Atlas→siblings absent, Household→siblings absent). Emit a shared breadcrumb/lateral strip (Atlas · Compare · Crossing · Household) on all four indexes.
- Conversion rationale: Lets visitors move Atlas↔Compare↔Crossing↔Household and *embodies* "your financial life run as one system."

**16. Elevate the non-replacement message for the CPA/attorney lens**
- Surface: Homepage hero/pivot (chip at `docs/index.html` 506; hover line 603-604) · Lens: CPA/Attorney · Clarity · **Medium** · **Small**
- Build: The reassurance lives only in one credibility chip and one hover-gated diagram line. Promote it to a first-class line in the reframed pivot: *"Most affluent households already have excellent specialists — Driftwood doesn't replace them, it makes them work as one."* Folds into #1.
- Conversion rationale: A CPA/attorney evaluating threat-to-relationship needs this stated in the main flow, not buried in a chip.

**17. Give the five-systems thesis diagram a no-hover fallback**
- Surface: Homepage thesis JS+markup (`docs/index.html` 294-348; JS 638-643) · Lens: Advisor · Friction · **Medium** · **Medium**
- Build: The "emotional centre" micro-stories ("Portfolios determine taxes.") are revealed *only* on mouseenter/focus; at rest and on touch/projected screens it collapses to five dots + "Hover any system." Provide a fallback: auto-cycle the stories, render one as the default resting state, or tap-to-advance on touch/reduced-pointer — so a projected or mobile viewer sees at least one complete "one decision touches all five" story without interaction.
- Conversion rationale: Directly fails the advisor lens ("open it in a real meeting with minimal explanation") on any non-hover device.

**18. Comparison index: promote the Crossing invite above the corridor wall**
- Surface: Comparison index (`comparepage.py` after 401; invite at 261) · Lens: Conversion · Hierarchy · **Medium** · **Small**
- Build: The one journey-advancing CTA sits below the live picker *and* below a 25-item "High-intent corridors" link wall. Move it to immediately follow the live `#cmpOut` result; consider surfacing it more prominently when the weighed pair shows a large delta; group/demote the 25 corridors.
- Conversion rationale: Presents the forward step the moment recognition peaks (right after a pair is weighed).

**19. Interpret the Comparison "Illustrative impact" line**
- Surface: Corridor page (`_impact_line`, `comparepage.py` 151-160) · Lens: Prospect · Clarity · **Medium** · **Medium**
- Build: "+4.7%/yr in California vs +3.7%/yr in Texas" sits uninterpreted above the CTAs; a CA→TX mover can read it as "coordination is worth more if I *stay*." Add one clause: the higher figure reflects that a higher-tax environment leaves more for coordinated management to recover — and the move decision itself is what a Crossing Brief quantifies. (Governed by the positioning decision in #11.)
- Conversion rationale: Removes a reading that argues *against* moving, and creates forward pull to the Crossing Brief.

**20. Bridge the Comparison instrument to the threshold thesis**
- Surface: Comparison index + corridor `.hd` lede (`render_comparison_html` 220, `render_compare_index_html` 390) · Lens: Prospect · Narrative · **Medium** · **Small**
- Build: Both open in pure analytical mode. Add one framing line under each h1: *"A change of state is one of the few events that touches every specialist at once — which is exactly why it needs to be read as one system."*
- Conversion rationale: Ties the instrument back to the realisation that anchors the rest of the site.

**21. Replace the Comparison "None triggered." fallback**
- Surface: Corridor page (`_pri_items`, `comparepage.py` 124; line 252) · Lens: Prospect · Narrative · **Medium** · **Small**
- Build: "None triggered." under "Only Texas" reads as a dead log cell and implies Texas households need no coordination — contradicting the thesis. Replace with *"Texas opens no coordination priorities that California doesn't also require"* (keep in `_pri_items` so static + live-JS match).
- Conversion rationale: Protects the "every household past the threshold needs coordination" thesis at a visible touchpoint.

**22. Name the corridor in the Crossing Brief H1**
- Surface: Individual brief (`render_crossing_html` 206) · Lens: Prospect · Hierarchy · **Medium** · **Small**
- Build: Every brief's H1 is the generic "What changes when a household crosses state lines."; the actual move (Illinois→Florida) is only in the smaller navy `.xband`. Make the H1 name the corridor ("Illinois → Florida: what changes when this household crosses state lines.") using `o_name`/`d_name` already in scope; keep the generic phrasing for the index H1 only.
- Conversion rationale: Preserves the "prepared for you" framing for search/screen-share landers.

**23. Deepen the Crossing Brief "Coordination priorities" table**
- Surface: Individual brief · Lens: Conversion · Hierarchy · **Medium** · **Medium**
- Build: The section that most demonstrates Driftwood's differentiator renders a single row ("Asset titling for step-up") for Illinois→Florida. Surface the full cross-specialist choreography (estate attorney on titling, CPA on part-year/final-state return + domicile substantiation, custodian on registration, advisor on realization timing); if the graph truly yields one priority, add owner/handoff columns so it reads as orchestration, not a lone task.
- Conversion rationale: The operations flagship must make coordination feel substantive, not thin.

**24. Resolve the Crossing Brief QSBS §1202 hedge deterministically**
- Surface: Crossing build logic · Lens: CPA/Attorney · Clarity · **Medium** · **Medium**
- Build: Florida's QSBS cell reads "either the jurisdiction levies no tax… or it does not separately recognize the §1202 exclusion" — telling a CPA the document doesn't know which. For no-income-tax destinations render the definite statement: *"Moot — no state income tax, so the federal §1202 exclusion is the only one that applies."* Reserve the hedge for genuinely unsettled states.
- Conversion rationale: Ambiguity on a technical point in an operating memo erodes CPA trust more than omission would.

**25. Give Crossing Brief + Household Record their own disclosure variant**
- Surface: Crossing (`illinois-to-florida` 225) + Household (`harris` 225, index 210); shared `DISCLOSURE` constant in `statepage.py` · Lens: CPA/Attorney · Clarity/Friction · **Medium** · **Medium**
- Build: Both surfaces render the boilerplate "The tax-management impact figure is a hypothetical…" but neither displays any such figure. Gate the tax-management-figure sentence on pages that actually show the figure, or pass a page-type variant so these inherit only relevant clauses (state-law summaries, "confirm with counsel," RIA/ADV/CRS).
- Conversion rationale: A specialist reading a disclaimer for an absent number wonders what was hidden — quietly erodes the precision posture. (Consolidates the two duplicate disclosure findings.)

**26. Name the realisation on the Household Record**
- Surface: Harris file (`householdpage.py` 90-92; `harris/index.html` 210) · Lens: Prospect · Narrative · **Medium** · **Medium**
- Build: The coordination mini-list ("Residency & domicile · advisor + CPA", "Estate structure · estate attorney", "Loss harvesting · advisor + CPA") *is* the category story but is rendered as a quiet annotation. Name it: *"Four domains, four specialists, one household. Each is expert in its own lane; the Record is the only place their decisions are read together."* — letting the specialist tags become the evidence.
- Conversion rationale: The deepest surface is best positioned to land the threshold realisation; today it leads with mechanics instead.

**27. Differentiate the two duplicate-link Household cards**
- Surface: Harris file (`householdpage.py` 187, 89-92; `harris/index.html` 209-210) · Lens: Prospect · Clarity · **Medium** · **Small**
- Build: "The tax environment" and "Coordination priorities in force" both `go=` the same `/atlas/2026/illinois/` URL, reading as padding against the "reference, not duplicate" promise. Point "Coordination priorities" at a specific Atlas anchor, or merge the two cards, or give the second card its own content (the specialist coordination map).
- Conversion rationale: Makes the index look substantive exactly where it claims rigor.

**28. Fix Household Record breadcrumb / nav / aria-current**
- Surface: Harris file + index (`harris/index.html` 176-191, 36-37) · Lens: Advisor · Friction · **Medium** · **Medium**
- Build: No `.bcrumb` rendered though styled; top nav omits Household Record and Atlas flagships; `aria-current='page'` sits on "State Tax Atlas" while the user is on the Household Record. Render the breadcrumb (Atlas → Household Record → The Harris Family), add Household Record/Atlas to the nav "Discover" group, correct the aria-current.
- Conversion rationale: A search/OG-share lander must be able to move up and across; the false current-page signal also fails accessibility.

**29. Atlas *edition index*: coordination framing + onward row + column rename**
- Surface: Atlas index (`render_states_index`, `docs/atlas/2026/index.html`) · Lens: Prospect/Conversion · Conversion · **Medium** · **Medium**
- Build: The index is framed as a returns leaderboard ("Tax Management Impact" column: +4.7%/yr, +4.0%/yr…). Add a coordination framing line above the table (not a returns pitch), and retitle the impact column so it doesn't read as ranking states by return. (Onward links overlap #6; this is the copy/framing half.)
- Conversion rationale: Prevents the reference hub from reading as a performance ranking. Column rename is part of the #11 positioning decision.

**30. De-duplicate the Atlas FAQ**
- Surface: State page (`statepage._faq` / `_faq_html`, `illinois/index.html` 185-191) · Lens: Prospect · Clarity · **Medium** · **Small**
- Build: The "Frequently asked — 7 on Illinois" answers are verbatim copies of the seven dimension cards (a full screen of duplicated text). Either drop the visible accordion and keep only the FAQPage JSON-LD for rich snippets, or make each visible answer additive with a coordination angle ("who owns this decision, and what changes when they talk").
- Conversion rationale: Removes a screen of padding; earns its keep as schema, not reading.
- **EDITORIAL DECISION:** drop visible FAQ vs. rewrite as additive.

**31. Collapse the three stacked Atlas conversion asks**
- Surface: State page foot (`illinois/index.html` 219-227) · Lens: Conversion · Friction · **Medium** · **Small**
- Build: Diagnostic + "Start a conversation" + email capture stack consecutively, diluting each. Collapse to one primary recognition-framed action (the onward flagship, per #12) plus at most one quiet secondary (diagnostic *or* email, not both).
- Conversion rationale: Removes decision overload at the moment the visitor decides whether to continue.

**32. Comparison picker affordance / same-state no-op**
- Surface: Comparison index (`_INDEX_JS`, `comparepage.py` 331-338; `index.html` 230) · Lens: Advisor · Friction · **Low** · **Small**
- Build: Output re-renders on every `change`, making "Weigh them →" redundant/ambiguous; `go()` silently no-ops when A===B. Either remove the button or add a "Updates as you choose." hint, and surface "Pick two different states to weigh" for the A===B case.
- Conversion rationale: Minor clarity fix so the live instrument doesn't feel broken.

---

## 3. QUICK WINS (small effort — ship first)

- **#3** Hero primary CTA (once diagnostic exists)
- **#6** Atlas index forward rel-bar + CTA — *highest-leverage single funnel fix*
- **#7** Crossing Brief forward CTA to Household Record + meeting
- **#9** Comparison corridor → Crossing Brief handoff
- **#12** Atlas state page: promote Comparison/Crossing, add Household Record link
- **#14** Point flagship CTAs straight at Calendly
- **#16** Elevate non-replacement line into the hero pivot
- **#22** Name the corridor in the Crossing Brief H1
- **#21** Replace "None triggered." fallback
- **#30** De-duplicate the Atlas FAQ
- **#18** Promote Comparison index Crossing invite above the corridor wall

*(Together #6, #7, #9, #12 install most of the forward spine at small effort — do these as one pass.)*

---

## 4. JOURNEY FIXES (Homepage → Diagnostic → Atlas → Comparison → Crossing Brief → Household Record → Meeting)

| Transition | Current gap | Fix |
|---|---|---|
| **Homepage → Diagnostic** | Diagnostic doesn't exist; hero leads with a tax-leakage tool | **#2** build the recognition diagnostic; **#3** make its CTA the hero primary |
| **Diagnostic → Atlas** | No routing from a (nonexistent) result into the flagship | **#2** results state routes to `/atlas/2026/`; **#5** repoint nav "State Tax Atlas" to `/atlas/2026/` |
| **Atlas → Comparison** | Atlas *index* has no forward path at all; state page buries Comparison in a 12.5px `.rel` row | **#6** index rel-bar + CTA; **#12** promote Comparison/Crossing on state pages |
| **Comparison → Crossing Brief** | Corridor page has *no* Crossing link (CTAs point backward/lateral); index buries the invite below a 25-link wall | **#9** corridor forward handoff; **#18** promote index invite above the corridor wall |
| **Crossing Brief → Household Record** | Only an inline-prose link; the visible ghost CTA points *backward* to Compare | **#7** primary "Prepare this as your Household Record →" + secondary "Start a conversation" |
| **Household Record → Meeting** | Both brief and index dead-end into disclosure with no CTA — the funnel's final leak | **#8** terminal recognition-framed meeting CTA on brief and index |
| **Cross-cutting** | Flagship CTAs bounce through `index.html#conversation` before Calendly; no breadcrumb spine ties the set together | **#14** direct-to-Calendly; **#15** shared breadcrumb/lateral strip |

---

## 5. EDITORIAL / NARRATIVE DECISIONS TO CONFIRM BEFORE BUILDING

1. **Homepage hero copy** (#1) — the exact three-beat progression and kick/pivot/h1 wording.
2. **Diagnostic design** (#2) — the 5-6 prompt wordings, how checks tally, the results-screen copy, and where each result routes.
3. **The returns/alpha positioning** (#11, #29-column, #19) — *one decision*: does Driftwood surface a "+X%/yr" performance figure publicly at all, and if so how demoted/relabeled? This governs the Atlas hero, the Atlas-index "Tax Management Impact" column name, and the Comparison impact line simultaneously.
4. **Atlas FAQ** (#30) — drop the visible accordion (keep JSON-LD) vs. rewrite each answer with a coordination angle.
5. **Template of record** — confirm the homepage template is `src/drift/web/hub.html` (findings also cite `src/drift/web/index.html`); all homepage edits re-render through `scripts/sync_docs.py`, never hand-edit `docs/*.html`.
