# Inference Graph

The provenance of every claim: `Observation → Evidence → Candidate → Finding → Paper Claim`. Each
edge cites what licensed the step — safeguards (S-\*), assumptions (A-\*), evidence (E-\*), stopping
rules (SR-\*), and decisions (GD-\*). The point is that anyone — a collaborator or a referee — can
start at a sentence in a paper and walk back to the exact evidence and gate that justify it, or see
precisely where a chain stopped and why.

**Node types.** `O` observation · `E` evidence (Evidence-Ledger IDs) · `C` candidate · `F` finding
(only past a cleared stopping rule) · `PC` paper claim. A chain may **terminate early** — that is
information, not failure.

---

## Paper 1 chains (frozen — complete to a claim)

### IG-1 · Velocity signal is survivorship, not fatigue
```
O-1  velocity decline raises OOS AUC 0.42 → 0.61 ("team scores > 4.5 runs")
  │  edge: raw OOS association is the weakest admissible evidence  [S: debiasing rung]  [A: reject "OOS AUC = edge"]
E    pre-treatment (first-20 vs next-20) window AUC → 0.524, CI straddles 0.50
  │  edge: debiasing rung applied  [S-11-class selection control]  [E: Paper-1 revision analysis]
C-1  apparent signal is post-treatment selection (survivors are the already-hit starters)
  │  edge: clears the debiasing rung as a diagnosed artifact  [SR: n/a — Paper-1 regime, June cache]
F-1  the velocity "signal" is survivorship bias  [negative/methodological finding]
  │
PC-1 Paper 1 §Results, Figure 5 — "Post-treatment bias in the velocity signal"
```

### IG-2 · The market encompasses all tested public variables
```
O-2  public features predict runs (feature-only OOS R² = 0.279)
  │  edge: prediction ≠ increment  [S: encompassing rung]  [A-08 RE24 transfer: Moderate]
E    market forecast error Y−B not predictable OOS (R² = −0.037); Clark-West does not favor the
     augmented model; block-bootstrap gain CI [−0.036, +0.002]
  │  edge: OOS/LOGO + Chong-Hendry encompassing (highest standard in the paper)
C-2  no public variable adds incremental information beyond the live market
  │  edge: clears the encompassing rung
F-2  the market encompasses every public variable tested
  │
PC-2 Paper 1 §4 Figure 4; Abstract ("No variable survives")
```

---

## Paper 2 chains (live data — terminate before a claim, by design)

### IG-3 · Cross-book leadership / lead-lag  — TERMINATES at Candidate
```
O-3  books appear to move at different times; cross-book divergence is visible
  │  edge: [E-005 sync collapse understood]  [E-012 arbs dissolved]
E    576 nominal "arbs" dissolve (E-012); "sync lag" is collector co-capture, not market
     contemporaneity (E-006)
  │  edge: [A-01 executable prices: Weak] [A-03 cadence: Challenged] [A-04 two-book ID: Weak]
  │        [Research Debt RD-1, RD-2, RD-4]
C-3  any lead-lag estimate is a Candidate — not currently evaluable
  │
  ╳  STOPPING RULE SR-1: BLOCKED (2 books, 30 games; pairs/lag caveats)  →  NO Finding  →  NO Paper Claim
```
*Reading: the chain is complete up to a Candidate and then stops at SR-1. There is no Paper 2 claim
because the gate has not cleared — exactly what should be visible.*

### IG-4 · Higher-moment (variance/skew/tail) repricing — NOT STARTED
```
O-4  the implied distribution may reprice higher moments differently than the mean
     (Paper 1 §7 open question)
  │
  ╳  blocked upstream: SR-2 awaiting evidence; sharp implied-PMF stream does not exist
     [A-07 sharp source: Refuted via E-007 Pinnacle stillborn]  →  chain not started
```

---

## Program-level reading

- **No live-data chain has reached a Finding.** Every Paper 2 chain terminates at Candidate or
  earlier, gated by SR-1 / SR-2. This is the correct state for Phase 4 and should stay true until a
  stopping rule objectively clears.
- The two completed chains belong to **Paper 1 (frozen)**; their evidence is the June cache, disjoint
  from the live panels (E-011), so live collection cannot alter them.
- A chain edge that cites a `Weak`/`Challenged` assumption or an open Research-Debt item is a marked
  weak link: it must be strengthened or explicitly bounded before that chain can advance a node.

## Discipline

A node advances only when the citing safeguard/gate is actually satisfied — never because the next
node is desirable. Adding `F` or `PC` nodes for live data before a stopping rule clears is the single
most dangerous edit this graph can receive; it is prohibited.
