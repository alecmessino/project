# Go-To-Market — Findings & Recommendations

A working memo on the Structural Alpha business-development phase: what I found, what I changed, and
what needs a decision or a principal sign-off before anything goes external. Companion to
`GTM_Playbook.md` (positioning) and `GTM_Scripts.md` (outreach copy).

---

## 1. Compliance — the two things that gate everything

**a) "Fee-only" vs. selling insurance — resolved as refer-out.** The site brands **"Fiduciary,
fee-only"** (`hub.html`). Earning commission on Guardian / Park Avenue protection products is
incompatible with that label (NAPFA / CFP Board definitions) and is exactly the kind of contradiction
an examiner looks for. **Decision (locked): keep fee-only; the protection angle is a fiduciary
*recommendation* + referral to a licensed specialist — the RIA sells nothing and earns no commission.**
All "found money → protection" copy in `GTM_Scripts.md` is written that way. If the firm ever wants to
*earn* on insurance, that's a deliberate move to a **fee-based** model (relabel the badge, add Form ADV
conflict disclosures) — not something to drift into.

**b) The +3.6%/yr figure is hypothetical-backtest output.** Under SEC Marketing Rule 206(4)-1, every
outreach piece is an advertisement. Saying *"you are losing 3.6% a year"* to a prospect we haven't
analyzed is a misleading performance claim. **Decision (locked): compliant reframe — "up to ~3.6%/yr in
our illustrative modeling," with the real number gated behind the personalized diagnostic.** The
diagnostic now does exactly that (below). Cold/"kitchen-table" outreach that leads to business is still
advertising — the playbook flags what needs sign-off.

## 2. What I built this phase

- **The Tax-Leakage Diagnostic is now personalized.** `leakage.html` reads `?state` / `?port` and
  localizes off a per-state Tax-Alpha table (`drift.leakage.STATE_ALPHA`, 50 states + DC + NYC,
  regenerable via `TAX_ALPHA_STATES=1 python scripts/tax_alpha.py`). A prospect link shows *their*
  state's Before/After, the recovered alpha as "up to +X%", and the dollar translation on their
  portfolio — while keeping every illustrative/hypothetical disclosure. This is **more** compliant than
  a generic claim (it's their inputs, clearly labeled illustrative), and far more persuasive.
- **Conversion path closed.** Added a booking CTA on the diagnostic and a "Book a 15-min diagnostic"
  tile on the hub; both route into the existing Tax Lab prospect funnel, forwarding `state/port/utm`.
- **Attribution confirmed.** The UTM parser was already wired (`taxlab.html`) and is now guarded by a
  test — geo/segment campaigns are measurable end-to-end (Plausible reads `utm_*` natively; they also
  ride along on the lead email).

## 3. Channel sequencing (recommendation)

1. **CPA / gatekeeper first.** Lowest compliance risk, highest leverage, partner-not-poach, and the
   `CPA_Technical_Brief.md` already exists. One CPA relationship is many clients.
2. **Illinois geo second.** The infra is pre-wired (IL estate-cliff modeling, Roth-conversion arbitrage,
   the state heat-map, the personalized diagnostic). The "Illinois Hedge" narrative is in the playbook.
3. **Austin tech third.** Pre-liquidity / concentrated-equity wedge; a second geo once IL is running.

## 4. Thesis / methodology notes (smaller, worth tracking)

- **The "Before" book is a worst-case.** The diagnostic's BEFORE is a concentrated, ~94%-short-term,
  ~344%-turnover book — fair as an illustration of the leak, but it is the *high end*. The honest
  framing (used throughout) is "a concentrated / high-turnover book," and the personalized diagnostic
  lets each prospect see a number grounded in their own state rather than the worst case.
- **Horizon inconsistency.** The tearsheet defaults to a 30-year window; the leakage diagnostic cites
  40 years. Not wrong, but the story is cleaner if one headline horizon is used across artifacts —
  recommend aligning the diagnostic to 30y (or footnoting why it's 40y) before heavy external use.
- **Asset location is still the one un-quantified lever in the diagnostic** (shown "household-specific").
  That's correct — it genuinely depends on account balances — and the Tax Lab computes it per client via
  `location_alpha3`. Keep it that way; don't bake a single asset-location number into outreach.

## 5. Sign-off gate (do not skip)

`GTM_Playbook.md` and `GTM_Scripts.md` are **internal sales-enablement drafts**. Nothing here is
auto-published or cleared for external send. Before any campaign goes live: the principal reviews the
copy, confirms the compliant-reframe language is intact, and books/keeps the advertising records the
Marketing Rule's recordkeeping provisions (Rule 204-2) require. The personalized diagnostic and the
Tax Lab are already disclosure-complete; the *outreach copy* is the piece that needs the human gate.
