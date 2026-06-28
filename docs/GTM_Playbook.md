# Structural Alpha — Segment Playbook

Internal sales-enablement. Positioning, personas, and ready-to-send deep-links for the firm's first
campaigns. Tone throughout: **wealth architect, not salesperson.** Every number is **illustrative /
hypothetical, diagnostic-gated** (see the framing rules). Outreach copy lives in `GTM_Scripts.md`;
the rationale and compliance posture are in `GTM_Findings.md`. **Nothing here ships without principal
sign-off.**

---

## The framing rules (non-negotiable)

1. Never state a prospect's leak as fact. Always **"up to ~X%/yr in our illustrative modeling"**, and
   let the **personalized diagnostic** show their number from their own inputs.
2. The edge is **after-tax** and **structural** — never a pre-tax or stock-picking claim. We do **not**
   claim the funds out-perform; we engineer what's *kept*.
3. Protection is **referral-only** under the fee-only model — a fiduciary recommendation, never a
   product sale, never a commission.
4. Lead with the **diagnostic**, not the dollar. The artifact does the persuading; the rep stays the
   architect.

## The deep-link recipe

The campaign asset is the **personalized Tax-Leakage Diagnostic**. A cold link pre-loads the
prospect's state + portfolio and tags the campaign for attribution:

```
leakage.html?state=<CODE>&port=<DOLLARS>&utm_source=<src>&utm_medium=<med>&utm_campaign=<name>
```

It renders "up to +X%/yr" for their state, the $/yr translation on `port`, and a CTA that carries
`state/port/utm` into the Tax Lab prospect funnel (email capture → Calendly). Plausible attributes the
funnel to the campaign automatically.

| Segment | Example deep-link |
|---|---|
| Chicagoland professional | `leakage.html?state=IL&port=2000000&utm_source=linkedin&utm_medium=dm&utm_campaign=il_hedge` |
| Chicago business owner | `leakage.html?state=IL&port=4000000&utm_source=referral&utm_medium=intro&utm_campaign=il_owner` |
| Austin tech (pre-liquidity) | `leakage.html?state=TX&port=1500000&utm_source=linkedin&utm_medium=dm&utm_campaign=atx_tech` |
| CPA partner (sends to their client) | `leakage.html?state=IL&port=3000000&utm_source=cpa&utm_medium=partner&utm_campaign=cpa_il` |

(30y window: IL alpha ≈ +4.0%/yr, NY ≈ +4.5, CA ≈ +4.7, no-tax states ≈ +3.7 — all illustrative; the
page shows the prospect's own state.)

---

## Segment 1 — Chicagoland: "The Illinois Hedge"

**Narrative.** In a punitive-tax state, Structural Alpha isn't portfolio optimization trivia — it's a
*local financial hedge*. Illinois taxes capital gains as ordinary income (~4.95%) on top of federal, and
the estate-tax cliff (~$4M exclusion) is a live HNW threat. We position as the **local wealth architect**
who contains tax leakage — not a stock-picker.

**Persona A — the high-earning professional (Big Law / medical / tech).** High income, zero time for
asset-location mechanics. *Architect message:* "In our illustrative modeling, a high-turnover Illinois
book can leak up to ~4.0%/yr after tax versus a tax-managed one of the same exposure. My system
automates the location-matching so you keep more of it — here's the diagnostic on your numbers." →
`il_hedge` deep-link.

**Persona B — the Chicagoland business owner.** Over-concentrated in the business, liquid-poor
personally. *Architect message:* "Your business is your growth engine and your risk. Your personal
portfolio shouldn't be timing markets — it should be an ultra-efficient, low-leakage compounding base
that funds your family and retirement goals." → `il_owner` deep-link. Pairs naturally with the estate
view (the IL cliff is already modeled in the Tax Lab).

**Estate-cliff angle.** Frame Structural Alpha as a wealth-*preservation* machine: maximizing the
after-tax asset base today means more capital available for tax-efficient transfer tomorrow. Route to
`taxlab.html?view=estate&state=IL&port=<estate>` for the cliff illustration.

## Segment 2 — Austin tech: the pre-liquidity wedge

**Narrative.** Engineering tax efficiency and asset location **before** a liquidity event, rather than
timing the market. Target tech directors / startup employees with concentrated equity. The two real
problems are **concentration risk** and **tax-inefficient location** of whatever they already hold.

*Architect message:* "I work with a small group of tech leaders on pre-liquidity wealth architecture —
Structural Alpha, not market timing. Most are unintentionally leaking returns through tax drag and
suboptimal location. I can run a Leakage Diagnostic on your setup to show what's on the table." →
`atx_tech` deep-link. (Three tailored variants — Concentration / Tax-Efficiency / Fiduciary Standard —
in `GTM_Scripts.md`.)

## Segment 3 — CPA / gatekeeper (lead with this channel)

**Narrative — partner, don't poach.** The CPA is usually the one cleaning up the tax mess that
high-turnover, return-chasing advisors create. We offer a portfolio that is a **tax-friendly asset** on
their clients' returns — lower short-term-gain churn to reconcile in April. *We are not trying to take
their client; we want their clients' after-tax reality to be better.*

*Architect message:* "My methodology is built on Structural Alpha — lot protection, asset location,
tax-loss harvesting — so the portfolio is net-neutral-to-friendly at filing time. Could I show you the
Tax-Leakage Diagnostic and the technical brief over coffee?" Hand them `CPA_Technical_Brief.md` and the
`cpa_il` deep-link to forward to a client. Follow-up email in `GTM_Scripts.md`.

## The holistic bridge — "found money," fee-only refer-out

When the diagnostic surfaces recoverable leakage, that's **"found money"** — capital already rightfully
the client's. Under the **fee-only** model we **recommend and coordinate**, we do not sell:

> "We've recovered capital that was leaking to tax. I'd recommend we use it to fully fund your
> protection layer — disability, life, long-term care — and I'll coordinate with a licensed specialist
> so it doesn't touch your monthly cash flow. We're reallocating money the portfolio was already
> losing, not asking for new dollars."

No product is sold by the RIA and no commission is earned — it is fiduciary planning advice plus a
referral. (If the firm later chooses to *earn* on protection, that is a deliberate move to a fee-based
model with a relabeled badge and conflict disclosures — out of scope here.)

---

## Sign-off gate

These are drafts. Before any external send: principal review of the copy, confirmation the
compliant-reframe language is intact, and advertising recordkeeping (Rule 204-2). The diagnostic and
Tax Lab are disclosure-complete; the outreach copy is what needs the human gate.
