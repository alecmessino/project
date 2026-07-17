# Gated-PDF Spec, "the artifact before the meeting," done compliantly

**Goal:** give a prospect a valuable, educational artifact in exchange for an email, so the meeting becomes the warm next step instead of the cold first ask. This is the one genuinely-good idea from the outside CMO memo, implemented so it survives a FINRA/OSJ review.

**Non-negotiable framing:** you are a registered rep of Park Avenue Securities. Everything below is advertising and must be **OSJ-approved before launch**. The artifact stays **educational / illustrative**, no performance claims, no individualized advice, no client-specific recommendations.

## 1. What the artifact is (v1)
A **static, evergreen educational PDF**, not a per-user computed report. Static content sidesteps the "is a machine-generated personalized output individualized advice?" question entirely, and it is faster to get approved.

Recommended first brief, repackaged from content you already have (`coordination.html`):
> **"The Ordering Problem: how the sequence of a liquidity event decides more than the deal."** 4–6 pages. Residency → gifting window → Roth conversions → asset location, as an educational walkthrough, with the site's existing illustrative figures and the full disclosure on the last page.

Later candidates (same mechanism): a State-Relocation education brief; an "after-tax vs pre-tax" primer.

## 2. The gate (works on static GitHub Pages, no backend)
Reuse the **Web3Forms** endpoint + key already wired into the State Atlas capture and the new `waitlist.html`. No new infrastructure.

- Form: email (required) + first name (optional). One field, one button, same look as `waitlist.html`.
- On submit → Web3Forms notifies your firm inbox (the lead) **and** the page shows the success state.

**Delivery, pick one (both compliant):**
- **(A) Honest manual follow-up (recommended for a rep):** success copy = *"Thank you. We'll email the brief to you shortly, usually within a business day."* You (or an assistant) send the OSJ-approved PDF by hand. Matches the site's existing honest pattern, starts a human relationship, and never over-promises an automated deliverable. Best relationship + compliance posture.
- **(B) Immediate download:** on Web3Forms success, reveal a `<a download href="briefs/the-ordering-problem.pdf">`. Lower friction; the URL is technically discoverable (a soft gate), which is fine for a lead magnet. You still get the lead via Web3Forms.

Do **not** gate the existing free tools (Diagnostic / Atlas), keep them open for SEO/E-E-A-T. The gate is only for this **additive** downloadable brief.

## 3. Honest-UX guardrails (already enforced in the codebase, reuse them)
- No *"your custom report is on its way"* when the backend only notifies the firm (the repo's tests forbid this exact over-promise, mirror that copy).
- *"We never share your address."* Privacy Policy covers the capture.
- PAS/Guardian disclosure on the page **and** on the PDF's last page.

## 4. Build steps (say go and I'll do 2–3)
1. **You:** get the PDF content OSJ-approved (I can draft the copy from `coordination.html` for their review).
2. **Me:** build `brief.html` (form + honest success state) reusing the `waitlist.html` / Web3Forms pattern, in the frozen style; add to `sync_docs`.
3. **You:** drop the approved PDF at `docs/briefs/the-ordering-problem.pdf`.
4. **Both:** point outreach Touch-2 and LinkedIn at `driftwoodwealth.com/brief.html`.

## 5. Deliberately deferred (v2)
A **personalized** computed brief (gate `score.html` and email the person their Coordination Index) is higher-touch but raises a real "is this individualized advice?" question and needs a bigger build + closer OSJ scrutiny. Ship the static brief first; revisit personalization once the simple version is approved and converting.
