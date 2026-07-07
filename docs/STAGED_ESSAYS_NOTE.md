# Staged essays — for your read (not published)

Two reserved Insights pieces have been brought to publishable standard and are **staged only**:
they live in `src/drift/web/` but are **not** copied into `docs/`, **not** listed on the
`insights.html` index, and are therefore not reachable on the live site. Publishing is a
one-word go/no-go from you (see "To publish" below).

Both were part of the institutional-credibility remediation: the audit's rule is *match the
confidence of the presentation to the level of the evidence*. That is what changed in each.

---

## 1. `the-worlds-largest-investors.html` — "The World's Largest Investors Pay Attention Differently"

**What it argues:** endowments and families can buy the same funds; what separates them is
attention to the layers that actually set outcomes (allocation, location, tax, behavior, time),
not access or intelligence.

**What changed:**
- **Anchored the two load-bearing empirical claims to real literature** (they were "overheard in
  the committee room" authority before):
  - The "each layer decides more than any single holding" claim now cites **Brinson, Hood &
    Beebower, "Determinants of Portfolio Performance"** (FAJ 1986; updated 1991) — the classic
    policy-allocation-dominates finding. Footnote [1].
  - The endowment-committee description now cites **David Swensen, *Unconventional Success*** (2005)
    and *Pioneering Portfolio Management* (2000). Footnote [2].
  - Added a numbered sources list and a foot note that citations are third-party context, not
    endorsements.
- **Wired the handoff into the tool:** a quiet closing paragraph links the same "attention to
  taxes and location" into the **After-Tax Review** (`taxlab.html`).
- **Resolved the draft state:** kicker changed from `· draft` to `· July 2026`.

**One judgment call for you:** the Brinson finding is frequently *over*-stated in the industry
("93% of returns come from allocation" — a misreading of an R² of *variance*, not of *return
level*). I wrote the sentence carefully — "the great majority of the **variation** in
institutional returns" — to state it correctly. Worth a glance to confirm you're comfortable with
the framing.

## 2. `enough-is-a-number.html` — "Enough Is a Number"

**What it argues:** a portfolio is a machine for funding a life, not a scoreboard; once you price
the life, "enough" becomes a number, and that number reframes risk and behavior.

**What changed:**
- **No citations added — deliberately.** This is a philosophy/opinion piece (Level-3 evidence),
  and it is honestly presented as such: no empirical claims dressed as facts, so nothing to anchor.
  The evidence hierarchy is satisfied by *not* manufacturing false authority here.
- **Wired the handoff into the tool:** a restrained closing paragraph connects "protecting what
  reaches the number" to the **After-Tax Review** — kept light so it doesn't turn a contemplative
  piece into a sales page.
- **Resolved the draft state:** kicker changed from `· draft` to `· July 2026`.

---

## To publish (when you say go)

For each essay you approve, one small commit does it:
1. Add the filename to the copy list in `scripts/sync_docs.py` (line ~53, alongside
   `every-portfolio-has-two-returns.html`).
2. Add a card to the `insights.html` index (mirror the existing flagship card markup).
3. Run `python3 scripts/sync_docs.py`, verify, deploy.

Nothing about the essays needs to change to publish — they are shelf-ready. The only open item is
your read and go/no-go.
