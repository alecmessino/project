<!-- Provenance: synthesized by a multi-agent in-repo audit (funnel / SEO / product / GTM-docs),
     then run through an SEC Marketing-Rule (206(4)-1) compliance pass. Three concrete findings
     were independently verified against the code before adoption:
       - leakage.html:176-177 — the "Book a 15-min intro" CTA is a ghost (same href as "Run my analysis").
       - statemap.html — zero links from the cartogram cells to the 51 per-state SEO pages (orphaned cluster).
       - taxlab.html:695 — Calendly slug still 'alec-messino-cwsplanning' (a live third-party URL; deliberately
         left during de-CWS, changeable only once a Driftwood-branded Calendly slug exists).
     This is an internal planning artifact — not investment advice and not a client-facing advertisement. -->

# Driftwood GTM: How We Bring In Prospects Starting Tomorrow — and Take It to the Next Level

The whole machine is already built and tested: 51 server-rendered SEO pages, seven exhibits, a personalized diagnostic, a rich deep-link scheme, and end-to-end Plausible analytics. It is also almost entirely **un-sent** — zero leads, zero bookings — and the one live conversion endpoint still shows the retired "cwsplanning" brand. So the plan is not "build more." It is: **ship the outreach that already exists, plug the leaks between a click and a booked call, then compound with passive assets that run without you.** Every tier leads with the CPA channel, because for a one-adviser shop the highest-leverage truth in the audits is *one CPA relationship is many clients.*

---

## TOMORROW — 0–1 day, zero/low build, assets that already exist

### 1. [LEAD] Sign off the CPA track and open the advertising-record log
- **Move.** A 60–90 min sitting: Alec reads `GTM_Scripts.md §2a/2b/2c` and `docs/CPA_Technical_Brief.md` end-to-end, confirms the locked compliant-reframe language is intact, and opens a dated Rule 204-2 advertising log (a single sheet). Sign off the CPA channel **only**.
- **Why it works for a solo.** Every GTM doc ends with the same hard gate — "nothing ships without principal sign-off." Clearing it for one channel legally unblocks the entire funnel without over-committing a single operator to three channels at once.
- **Leverages.** `GTM_Scripts.md` §Master checklist, `docs/CPA_Technical_Brief.md`, `OPERATIONS.md` (Compliance gates); sign-off gate in `GTM_Playbook.md`/`GTM_Findings.md §5`.
- **Effort:** 60–90 min · **Impact:** High — this is the one blocker gating everything below.
- **Guardrail (sign-off scope):** The principal sign-off must explicitly cover, and the 204-2 log must retain a dated copy of, *every* advertisement in the CPA send — the §2a opener text, the exact `CPA_Technical_Brief.md` version attached, and the landing page the deep-link resolves to (`leakage.html`). Log the sign-off as covering all performance/hypothetical figures those assets display, not just the channel decision. (Safe item, made audit-provable.)

### 2. Fix the two live conversion-path leaks: Calendly brand + autoresponder
- **Move.** Swap the Calendly slug `alec-messino-cwsplanning` → the Driftwood-branded link in `docs/taxlab.html` (`calendlyUrl`, :695) and rebuild; then enable the Web3Forms autoresponder in the dashboard so booked prospects get an instant copy of their diagnostic.
- **Why it works for a solo.** Every outreach link you send tomorrow routes through these two endpoints. A prospect who books today literally sees the retired brand in the URL, and gets no follow-up — you can't afford to burn your first real leads on a brand leak.
- **Leverages.** `docs/taxlab.html` `calendlyUrl` (contradicts rebrand commit 922cd8a); `OPERATIONS.md` "Leads, analytics, booking."
- **Effort:** <1 hr · **Impact:** High.
- **Guardrail (autoresponder content = an advertisement):** The auto-emailed diagnostic copy is a distributed communication and inherits the Marketing Rule. Confirm the emailed version carries the same "hypothetical model / research only / not personalized advice" disclosure the on-site diagnostic enforces, and that any figure in it is labeled hypothetical — do not let the email strip the disclaimer that the page renders. Brand-slug swap itself is compliance-neutral.

### 3. Ship the same-day funnel & measurement patch (~1–2 hrs of edits)
- **Move.** Four small edits in `taxlab.html`: (a) fire `track('lead_form_opened',{state,view})` when `ctaForm()` reveals the email field (:1216) and add click events to the `statepage.py:502-503` exit CTAs — lights up the currently-dark hook→CTA→submit drop-off; (b) add a working `CONFIG.calendlyUrl` link to the `ctaError` path (:1259) so a Web3Forms hiccup no longer kills the *only* booking route; (c) append `utm_*` + a compact `state/bracket/port` string to the Calendly URL (:1277, from `leadProps()`:1226 / `LEAD_UTM`:1691) so booked calls are attributed and you arrive prepared; (d) add a "Prefer to skip ahead? Book a call →" link under `ctaInitial` (:1212).
- **Why it works for a solo.** Instrumentation first is the point: it's the prerequisite for knowing which later fix actually moved the needle — you can't run experiments blind with no bandwidth to guess. The rest are pure resilience/attribution with no copy or disclosure change.
- **Leverages.** `taxlab.html:702` (`track`), :1216, :1259, :1277, :1212; `statepage.py:502-503`.
- **Effort:** Same-day · **Impact:** High (measurement) + Medium (resilience/attribution).
- *Safe as written — analytics/attribution/resilience only, no marketing copy or performance change. Keep as-is.*

---

## THIS WEEK — small build

### 1. [LEAD] Build a 15-name Chicagoland CPA list, then send the first batch of 5
- **Move.** Assemble 10–15 HNW/business-owner-focused CPAs & EAs in Chicagoland (name, firm, email, personalization hook) *in the same sheet as the Rule 204-2 log*. Send **5** personalized `§2a` peer openers, each attaching `CPA_Technical_Brief.md` and carrying the `cpa_il` deep-link (`leakage.html?state=IL&port=3000000&utm_source=cpa&utm_medium=partner&utm_campaign=cpa_il`). Watch Plausible for the `cpa_il` campaign + reply rate; scale only after the opener+brief combo pulls a coffee meeting.
- **Why it works for a solo.** The list is the one artifact standing between finished scripts and an actual send. Batch-of-5 respects one person's bandwidth and turns the copy into a *measurable test* rather than a blast — and CPA-first is the documented max-leverage-per-solo-hour play.
- **Leverages.** `GTM_Scripts.md §2a/§2c`, `docs/CPA_Technical_Brief.md`, the `cpa_il` deep-link in `GTM_Playbook.md`, Plausible `diagnostic_to_taxlab` funnel.
- **Effort:** Half-day list + sends · **Impact:** High — first real pipeline signal in 1–2 weeks.
- **Guardrail (referral compensation / endorsement — the load-bearing one):** The `utm_medium=partner` tag and the "one CPA = many clients" model imply a referral relationship. Decide and document which regime you are in *before* the first send:
  - **If no compensation flows either way** (CPA refers clients gratis, you refer none for pay): keep it, but state in the opener and log that the relationship is uncompensated, so a later examiner can't infer a hidden solicitation arrangement. Change `utm_medium=partner` to a neutral tag (e.g. `referral_uncompensated` / `cpa_direct`) so the analytics label doesn't itself assert a paid partnership.
  - **If any compensation, fee-share, reciprocal referral, or in-kind value is exchanged:** the CPA becomes a compensated *endorser* under Rule 206(4)-1(b). That triggers (i) a written agreement, (ii) clear-and-prominent disclosure of the compensation and of the material conflict on every client-facing touch the CPA hands off, and (iii) adviser oversight/ineligibility screening (204-2 records). Do not send until those are in place.
- **Guardrail (brief content):** Confirm `CPA_Technical_Brief.md` and the §2a opener contain no results-as-achieved figures, no "will save/earn," and no client outcomes stated as fact — reframe any such line as hypothetical-model / illustrative (see Month items). The attachment is an advertisement the moment it's emailed.

### 2. Kill the email wall on the highest-intent visitors
- **Move.** Add a direct booking route to `taxlab.html`: accept `?book=1` and on load render the existing branded pre-call block + `CONFIG.calendlyUrl` iframe immediately (reuse `ctaSuccess()`'s precall/iframe, :1279-1292), email optional-prefill not hard gate. Repoint every "Book a 15-min intro" CTA (`leakage.html:177`, `statepage.py:503`) to `...?view=prospect&book=1&state=XX` with UTM forwarded, and make `leakage.html`'s misleading ghost CTA (identical href today, :176-177) actually book. Add the `_capture()` inline Web3Forms block so `leakage.html` also converts in place instead of being a pure pass-through.
- **Why it works for a solo.** This is the single largest conversion leak and it penalizes your *best* visitors — the ones who clicked "Book." Your CPA-referred prospects land on `leakage.html`; today they're forced back through a lead form before the scheduler ever appears. Booking a call is not advice, so this is compliance-neutral.
- **Leverages.** `taxlab.html:695/1279-1292/1728`, `leakage.html:176-177`, `statepage.py:365` (`_capture`) + :503.
- **Effort:** Small build · **Impact:** High.
- **Guardrail (surface, not the copy):** Booking flow itself is compliance-neutral, as stated. One check: because `leakage.html` now converts *in place* rather than passing through `taxlab.html`, verify the required "hypothetical model / research only / not advice" disclosure is present and clear-and-prominent on `leakage.html` at the point of capture — a page that previously relied on a downstream page to carry the disclaimer must now carry its own.

### 3. Add one "Copy link / Send to my CPA" share primitive site-wide
- **Move.** A tiny reusable helper (one `<script>` or an addition to `dw-context.js`) that reads the live control values, serializes them into the query scheme the pages *already parse on load*, and offers `navigator.share()` with a clipboard fallback. Drop the button on `taxlab.html`, `leakage.html`, and `statemap.html`.
- **Why it works for a solo.** The plumbing is 90% built — these pages read `state/bracket/port/home/li/biz/utm` but only ever write `?view` back (`taxlab.html:1432`). This turns every private, self-tuned session into a forwardable artifact at the exact advisor-handoff moment — i.e., your *prospects and their CPAs do the selling for you*, the definition of solo leverage.
- **Leverages.** `taxlab.html:1687-1717/:1432`, `leakage.html`, `dw-context.js`.
- **Effort:** Small build · **Impact:** High.
- **Guardrail (disclosure must travel with the number):** A forwarded, self-tuned link resolves to a page showing a personalized figure to a third party who never saw the on-site framing. Ensure the disclosure and hypothetical-model label are rendered by the destination page *from the query state itself* (server/JS-rendered on load), so the shared artifact can never display a `port`/`Structural-Alpha`/`up-to-%` figure without its "hypothetical model, illustrative, not personalized advice" caption attached. Do not let the share primitive produce a bare number-only unfurl.

### 4. Un-orphan the organic assets (one-time internal-link edits)
- **Move.** Three cheap edits: (a) wire each `statemap.html` state cell + detail-card CTA to `slug_for(code)+'.html'` — connecting the orphaned 51-page SEO cluster to your highest-traffic exhibit and finally matching the breadcrumb parentage; (b) add "State Guides" (`states.html`) and "Concentrated Stock" (`concentration.html`) to `statepage.NAV`/the `dwnav` block so the two strongest pure-organic assets stop being orphans; (c) emit `<lastmod>` in `render_sitemap()`.
- **Why it works for a solo.** Set-and-forget internal link equity that compounds passively — no ongoing labor, exactly what a one-person shop needs. `lastmod` is the only sitemap freshness signal Google still honors.
- **Leverages.** `statemap.html` + `statepage.slug_for()`; `statepage.NAV` + `dwnav`; `statepage.render_sitemap()`.
- **Effort:** A few small edits · **Impact:** High (SEO, compounds over 2–4 weeks).
- *Safe as written — internal linking and sitemap metadata only. Keep as-is.*

---

## THIS MONTH / BIGGER BETS

### 1. [LEAD] Stand up the passive SEO acquisition engine (a factory, not hand-pages)
- **Move.** Mirror the `statepage.py` factory to generate two new clusters from data that already exists: (a) **~20–25 strategy pages** from `concentration.py` (exchange fund, VPF, collar, QSBS §1202, QOF, CRUT, DAF, 351 conversion, direct indexing/TLH — names, blurbs, families, 6-axis scores are all there); (b) **8–10 relocation/comparison pages** ("Moving from CA to TX: the tax math," NY→FL, IL→FL…) diffing the 7 dimensions + Structural-Alpha delta from `statemap._state_record`. Each with `HowTo`/`FAQPage`/`BreadcrumbList` JSON-LD, an OG card (extend `og_states.mjs`), and internal links into the state cluster. Fold the three service terms (tax-loss harvesting, direct indexing, asset location) in as the same pattern using the `leakage` "levers" copy. Add `HowTo`+`FAQPage` schema to `concentration.html` itself.
- **Why it works for a solo.** This is the highest buyer-intent *untapped* demand, and the factory + data already exist — you build the generator once and it ranks and converts while you sleep. Passive, compounding acquisition with no ongoing labor is the single best fit for a bandwidth-limited adviser.
- **Leverages.** `src/drift/concentration.py`, `statemap._state_record`, `statepage.py` factory (render/`_jsonld`/export/sitemap), `leakage.build_leakage()` levers.
- **Effort:** One build cycle · **Impact:** High — new long-tail clusters ranking over 3–6 months.
- **Guardrail (hypothetical performance at factory scale — Rule 206(4)-1(d)):** The "Structural-Alpha delta" and the 6-axis "scores" are model outputs and read as performance. Because these pages are mass-distributed to an audience you can't screen, bake the following into the *generator template* so it's structurally impossible to ship a page without them: (i) every delta/score labeled "hypothetical model output — illustrative, not a projection or guarantee"; (ii) a standing disclosure block stating the material assumptions, methodology, and limitations behind `_state_record`/`concentration.py` scoring; (iii) confirm the underlying Marketing-Rule policies-and-procedures for hypothetical performance are the ones referenced in the 204-2 log. Keep the strategy descriptions educational — no "will reduce your tax" phrasing; use "may, depending on facts." FAQ answers must not become individualized advice.

### 2. Make the 50-state footprint individually forwardable + add the trust layer
- **Move.** Generate per-state `og/<slug>.png` cards ~~("up to +X%/yr" + the 7 dims)~~ **(the 7 dims, plus a hypothetical model figure shown as a range with an on-card "hypothetical / illustrative" label — see guardrail)** from the data `statepage.py` already assembles, so a forwarded state link unfurls in iMessage/Slack/email with *that state's own number*. Pair with an E-E-A-T pass: a lightweight `/about` page (named adviser, ADV/CRS links, `sameAs`) plus `Organization`+`WebSite`+`Person` JSON-LD on the homepage.
- **Why it works for a solo.** Localized unfurls turn your existing SEO pages into social shares at no marginal cost; the Person/Organization schema is what Google weights for YMYL finance queries and enables sitelinks — and the authority facts already exist (`statepage.DISCLOSURE` cites `adviserinfo.sec.gov`).
- **Leverages.** `statepage.py` per-state assembly, existing OG generation (`og_states.mjs`), `docs/index.html` head, `statepage.DISCLOSURE`.
- **Effort:** Moderate · **Impact:** High (shareability) / Medium (E-E-A-T, compounds over 2–3 months).
- **Guardrail (cherry-picked "up to" figure = misleading performance):** "up to +X%/yr" presents the single most favorable outcome as the headline number on a bare social card that travels with no context — this is the clearest Marketing-Rule violation in the plan (cherry-picking + un-labeled hypothetical performance + fair-and-balanced failure). Do not print a naked "up to" max. Instead: show a *representative range* (or a clearly-defined base case), stamp "Hypothetical model result — illustrative, not a prediction; assumes [key assumption]. Not advice." *on the card image itself* (so it survives the unfurl), and drive to a landing page carrying the full assumptions/limitations disclosure. The `/about` + ADV/CRS + Person/Organization schema half of this item is safe and encouraged as-is.

### 3. Governance guardrails: sequence discipline + defer the domain
- **Move.** Commit to **CPA-only** for the first 4–6 week cycle; explicitly hold the Illinois (`§4a/4b`) and Austin (`§1a-1c`) scripts until a CPA relationship is proven or the CPA batch demonstrably fails. Make the domain call: **defer** the purchase/trademark screen (CPA converts over email + PDF + coffee and doesn't need a polished domain) and reserve the `set_domain.py` flip for *before* the cold-DM wave, where a `github.io/project` link would undercut credibility with strangers.
- **Why it works for a solo.** One person is the RIA, the engine maintainer, the site operator, and the salesforce — across three projects in this tree. Launching three channels he can't service dilutes the exact CPA leverage the docs identify. This item is what keeps the plan sustainable.
- **Leverages.** `GTM_Findings.md §3` sequencing; `scripts/set_domain.py` + `OPERATIONS.md` §Moving to the custom domain (tooling ready, purchase/trademark outstanding).
- **Effort:** A decision + discipline · **Impact:** Medium — protects the whole first cycle.
- *Safe as written — sequencing/operational discipline, pro-compliance. Keep as-is.*

### 4. (Stretch, only after the CPA channel shows life) The concentrated-position exit calculator
- **Move.** A net-new mini-tool: inputs = position value, basis %, state, bracket → output = an ordered shortlist of the 22 strategies with an illustrative after-tax number and a shareable result URL, reusing `concentration.py` scores + `tax.py` + `leakage` math and the `window.__STATE__` pattern.
- **Why it works for a solo.** It answers the single most-referred HNW problem (founder/RSU/concentrated stock) that the site currently treats only qualitatively, and could become a top organic entry point. Flagged as a stretch because it's the one net-new interactive surface that carries ongoing maintenance — don't build it until CPA pipeline justifies the upkeep.
- **Leverages.** `concentration.py`, `tax.py`, `leakage.STATE_ALPHA`, `concentration.html` shell.
- **Effort:** Build cycle + maintenance · **Impact:** High if pursued; gate it behind CPA traction.
- **Guardrail (interactive hypothetical performance + shareable output):** A user-specific "illustrative after-tax number" is hypothetical performance generated on-the-fly for an unscreened audience, and the shareable result URL re-broadcasts it. Ship only with: (i) each number labeled "hypothetical illustration based on your inputs — not a quote, projection, or guarantee, and not personalized tax or investment advice"; (ii) visible assumptions/limitations (rates, timing, ignored costs) adjacent to the output; (iii) the shareable-URL destination rendering that same label from state (per the This-Week #3 guardrail — no bare-number unfurl); (iv) coverage under the firm's hypothetical-performance policies referenced in the 204-2 log. Framed this way the tool ships; without it, it's an individualized performance projection that contradicts the site's "research only / not advice" posture.

---

## Explicitly cut or deferred (so a solo doesn't over-invest)
- **Launching IL + Austin cold-DM in parallel** — held until CPA proves (bandwidth).
- **Buying/flipping the custom domain now** — deferred to the cold-DM wave.
- **Completing all 50 "Prove it" citations, a DefinedTerm glossary hub, expanding `_STATE_CONTEXT` to all 51** — real but low-marginal-return polish; do opportunistically, not now.
- **Hub step-5 "proposal" fix and portfolio-in-`dw-context` persistence** — minor; roll into the this-week share-affordance edit if convenient, otherwise skip.

**The through-line:** Tomorrow you *unblock and stop bleeding*. This week you *send and convert*. This month you *build the one passive engine that compounds while you're in client meetings* — and you protect all of it by running exactly one channel at a time.

---

## Compliance notes (SEC Marketing Rule, 206(4)-1)

Nothing in this plan requires cutting a move — every flagged item ships once the labeling/disclosure/guardrail is attached. Six themes drove the edits:

1. **CPA channel = endorsement/solicitation risk (This-Week #1).** The single biggest legal decision. If any compensation, fee-share, or reciprocal-referral value moves in either direction, each CPA is a compensated endorser under 206(4)-1(b): written agreement, clear-and-prominent compensation + conflict disclosure on every handoff, and adviser oversight/ineligibility screening are prerequisites to sending. If uncompensated, keep it but document that fact and drop the `utm_medium=partner` label, which itself asserts a paid partnership.

2. **Hypothetical performance must be labeled and supported (Month #1, #2, #4).** "Structural-Alpha delta," the 6-axis scores, per-state numbers, and the calculator's after-tax figures are all hypothetical model output. Rule 206(4)-1(d) requires policies/procedures plus disclosure of assumptions, methodology, and limitations, and relevance to the audience. Because these go to an unscreened mass audience, bake the labels and disclosure into the *generators and card templates* so a bare figure cannot ship.

3. **No cherry-picking (Month #2).** The "up to +X%/yr" headline presents the best case as the number — replace with a representative range/base case and an on-image "hypothetical, not a prediction" stamp.

4. **Disclosure must travel with forwarded/shared artifacts (This-Week #2, #3; Month #4).** Any page or card that can now display a personalized figure to a third party must render the "hypothetical model / research only / not advice" disclosure *from the query state itself*, since the recipient never saw the site's framing. Pages that formerly relied on a downstream page for the disclaimer (`leakage.html` in-place capture) must now carry their own.

5. **Distributed copies are advertisements (Tomorrow #2, This-Week #1).** The autoresponder diagnostic email and the attached `CPA_Technical_Brief.md` inherit the Rule the moment they're sent — same disclosures, same hypothetical labeling, logged in 204-2.

6. **Recordkeeping (Tomorrow #1).** Rule 204-2 requires retaining every disseminated advertisement and the substantiation behind performance claims. Log dated copies of the opener, the exact brief version, and each landing page under the principal sign-off — not just the channel decision.

Genuinely-safe items left untouched: Tomorrow #3 (analytics/resilience), This-Week #4 (internal linking/sitemap), Month #3 (sequencing discipline), the booking-flow mechanics of This-Week #2, the `/about` + ADV/CRS + Person/Organization schema in Month #2, and the entire cut/deferred list.
