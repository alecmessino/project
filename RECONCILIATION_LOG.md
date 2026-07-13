# Atlas reconciliation log

The State Tax Atlas is an **editioned publication** (2026 edition, 2025 tax-year law), not a live
calculator. This log records every tax fact reconciled to a single canonical source
(`src/drift/state_facts.py`) against a primary/official authority, so each factual change is
reviewable before merge. One source of truth: the after-tax calculator (`tax.STATE_RATES`), the
Atlas display (`statemap`), the state pages, and the JS all project from `state_facts.RATES` — no
rate is authored twice.

---

## 1 · Income & capital-gains rates (2025 tax-year)

**Standard adopted:** the *top-of-bracket effective* long-term (LT) and short-term (ST) rate a
high-income resident ($1M+ of gains) actually pays — **including** any millionaire / net-investment
surtax and reflecting any long-term exclusion. Previously `tax.py` carried base rates (understating
surtax states) and stale pre-2025 figures, while `statemap` carried the display headline; the two
disagreed on 21 states. All values below verified `high` confidence.

| State | Prev (tax.py LT/ST · statemap) | Adopted LT/ST | Authority | Effective |
|---|---|---|---|---|
| AZ | 2.50/2.50 · 1.88% | **1.88 / 2.50** | A.R.S. §43-1022 (25% LT subtraction) + AZDOR 2.5% flat | TY2025 |
| GA | 5.39/5.39 · 5.19% | **5.19 / 5.19** | GA HB 111 (2025), retroactive to Jan 1 2025 | Jan 1 2025 |
| IA | 5.70/5.70 · 3.80% | **3.80 / 3.80** | Iowa DOR — flat 3.8% for 2025 | Jan 1 2025 |
| ID | 5.80/5.80 · 5.30% | **5.30 / 5.30** | Idaho HB 40 (2025), retroactive to Jan 1 2025 | Jan 1 2025 |
| IN | 3.05/3.05 · 3% | **3.00 / 3.00** | Indiana DOR — 3.0% flat for 2025 | TY2025 |
| KS | 5.70/5.70 · 5.58% | **5.58 / 5.58** | Kansas DOR — two-bracket top 5.58% | TY2025 |
| LA | 4.25/4.25 · 3% | **3.00 / 3.00** | Louisiana DOR RIB 25-012 — flat 3%, cap-gains deduction repealed | Jan 1 2025 |
| MA | 5.00/8.50 · 9% | **9.00 / 12.50** | Mass.gov — 4% surtax over $1,083,150 on LT (5%) and ST (8.5%) | TY2025 |
| MD | 5.75/5.75 · 8.50% | **8.50 / 6.50** | MD Comptroller TB-58 + 2025 Budget Recon. Act (6.5% top + 2% cap-gains surtax on LT) | TY2025 |
| MN | 9.85/9.85 · 10.8% | **10.85 / 10.85** | MN DOR — 9.85% top + 1% NIIT surtax over $1M | TY2024+ |
| MO | 4.80/4.80 · 0% | **0.00 / 0.00** | MO HB 594 (2025) — 100% capital-gains exemption | Jan 1 2025 |
| MS | 4.70/4.70 · 4.40% | **4.40 / 4.40** | MS DOR — flat 4.4% for 2025 | TY2025 |
| NC | 4.50/4.50 · 4.25% | **4.25 / 4.25** | NCDOR — flat 4.25% for 2025 | TY2025 |
| NE | 5.84/5.84 · 5.20% | **5.20 / 5.20** | Nebraska LB 754 / R.S. 77-2715.03 | TY2025 |
| NM | 3.54/5.90 · 5.90% | **5.90 / 5.90** | NM Stat. 7-2-34 (HB 252) — general 40% LT exclusion repealed | Jan 1 2025 |
| OH | 3.50/3.50 · 3.13% | **3.125 / 3.125** | Ohio Dept. of Taxation — 3.125% top for 2025 | TY2025 |
| SC | 3.47/6.20 · 3.36% | **3.36 / 6.00** | SC DOR — 2025 top rate 6.0%; 44% LT deduction (§12-6-1150) | TY2025 |
| UT | 4.55/4.55 · 4.50% | **4.50 / 4.50** | Utah HB 106 (2025), retroactive to Jan 1 2025 | Jan 1 2025 |
| VT | 5.25/8.75 · 8.75% | **8.75 / 8.75** | VT Dept. of Taxes / Reg. 1.5811(21)(B)(ii) — 40% LT exclusion unavailable for listed securities | TY2025 |
| WA | 7.00/0.00 · 9.90% | **9.90 / 0.00** | WA DOR — SB 5813 added a 2.9% tier over $1M to the 7% LT excise | Jan 1 2025 |
| WV | 5.12/5.12 · 4.82% | **4.82 / 4.82** | WV Tax Division — 2025 IT-140 top rate 4.82% | Jan 1 2025 |

Full URLs live beside each value in `state_facts.RATE_SOURCES`; the test suite asserts every
reconciled state carries an authority, URL, and effective date. **No-conflict states** (both prior
encodings already agreed and were confirmed against 2025 law — e.g. CA 13.3%, NY 10.9%, IL 4.95%,
DC 10.75%, NJ 10.75%) are unchanged.

### Downstream: the Structural Alpha table (`leakage.STATE_ALPHA`)

`STATE_ALPHA` (the "+3.7–4.7%/yr" tax-management figures) is **computed from** these rates, so it was
regenerated deterministically (`PYTHONHASHSEED=0`, 30-y proxy cache). **14 tail states** moved (MO
down — gains now exempt, so less tax to manage; MA up — the surtax adds recoverable leakage; others
≤0.2). **The four displayed headline jurisdictions (Federal / IL / NY / CA) are unchanged, so the
advertised band does not move.** The lineage guard (`tests/test_leakage_alpha_lineage.py`) re-derives
the table from the engine and confirms the match.

---

## 2 · Estate / inheritance facts

Pending — reconciled in the next step (step 3). Research is complete (16 death-tax states + the
Illinois pending-bill conflict resolved against primary sources); the canonical estate block and its
log entries land with that PR.
