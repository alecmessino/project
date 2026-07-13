# Foundation Facts — deferred operational values

The institutional-design execution (Study C) deliberately did **not** invent, infer, or placeholder any
operational fact that is not yet finalized. Each such fact has a **single insertion point** below, so a
production value can be set once and propagate site-wide. Until a value is set, nothing inaccurate is
published — empty facts render nothing.

This file is the checklist for the trust-foundation items the design work is gated on (roadmap track
**Operational credibility**, PRs 1–4, and the firm-anchor band IA-4).

| Fact | Status | Single insertion point | How to insert | Unblocks |
|---|---|---|---|---|
| **Production domain** | pending | `src/drift/site.py :: BASE_URL` | `python scripts/set_domain.py https://…` then rebuild (see OPERATIONS.md) | canonical / og / JSON-LD on all 92 pages · PR-1 |
| **Firm email** | **firm-domain placeholder set** (`hello@driftwoodplanning.com`) — Gmail retired sitewide | `src/drift/site.py :: CONTACT_EMAIL` | `python scripts/set_contact.py --email hello@…` when the reserved inbox is live | ✅ Gmail gone on all pages |
| **Booking URL** | live, but slug still branded to the prior firm (`…cwsplanning…`) | `src/drift/site.py :: BOOKING_URL` | `python scripts/set_contact.py --booking https://…` | homepage invitation now points here |
| **Firm location** | **confirmed: Austin, Texas** (principal-directed) | `src/drift/site.py :: FIRM_LOCATION` | set the constant | ✅ firm-anchor band |
| **Founding year ("since")** | **confirmed: 2024** (principal-directed) | `src/drift/site.py :: FIRM_SINCE` | set the constant | ✅ firm-anchor band |
| **CRD number** | not set | `src/drift/site.py :: FIRM_CRD` | set the constant | firm-anchor band grows a line when set |
| **Custodian** | not set | `src/drift/site.py :: FIRM_CUSTODIAN` | set the constant | firm-anchor band grows a line when set |
| **RIA registration / disclosures** | **legal decision — untouched** | existing footer + schema (test-guarded) | confirm with counsel; see note below | PR-3 |

## How the firm-anchor band consumes these

`src/drift/site.py :: firm_facts()` returns only the **non-empty** facts. The firm-anchor band (the
restrained identity+contact strip the roadmap adds to the homepage and every orphaned entry point) is to
be built to iterate that dict, so it renders exactly the lines that are true today and grows automatically
as facts are confirmed. A partially-known firm therefore shows a correct, smaller band — never a
placeholder. The band itself is not built yet: it is gated on at least the custodian + CRD being real.

## What was intentionally NOT changed

Per the execution guardrails, no strategic or legal item was resolved in code:

- **RIA registration and disclosure language** were left exactly as-is (and remain guarded by
  `tests/test_drift_disclosures.py`). Whether the "registered investment adviser" assertion is in force,
  and the CRD/ADV/CRS links, are a decision for counsel — not a design edit.
- **Pricing / fee schedule, State Atlas future, Tax Lab scope, positioning descriptor** — all deferred to
  the strategic gates in the roadmap (Study C · Part II).

Everything else in the objective tracks (type system, wordmark, favicon/identity, editorial subtraction)
was executed and is independent of these facts.
