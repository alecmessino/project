# Book Characterization Report — first edition (v0.1)

- **Date:** 2026-07-19
- **Purpose:** Characterize each book as a **measurement instrument**. The project has, until now,
  treated the books as interchangeable. That assumption has never been tested. This document tests
  it. It is measurement only: **no inference about market efficiency, no trading conclusions.**
- **Source:** `output/book_panel.jsonl`, 218,069 rows, 2026-07-03 → 2026-07-19 (post-All-Star
  slate included). Reproducible via `python3 the_third_turn/book_characterization.py`.
- **Status:** First edition. Numbers will firm up as games accumulate (60 live games so far). Two of
  the eight questions cannot be answered with the current panel and are flagged as instrumentation
  gaps, not guesses.

## Headline

The two live books are **not interchangeable** — they are two *different kinds of instrument*. The
book-interchangeability assumption is provisionally **falsified**, which is exactly why this
characterization must precede any cross-book efficiency claim (and why SR-1's third-book criterion
guards a real property — see `SR1_GATE_DESIGN_REVIEW.md`).

## The measured facts (trustworthy)

| Property | FanDuel | Bovada | Pinnacle |
|---|---|---|---|
| Live games quoted | 60 | 60 | **0** |
| Rows stored / live rows | 155,345 / 27,372 | 62,718 / 23,173 | 6 / 0 |
| Quote **change rate** (per live poll) | **0.65** | 0.07 | — |
| Median seconds between changes | **31 s** | 488 s (~8 min) | — |
| Distinct quote states per game (median) | **191** | 25 | — |
| Median implied vig | 4.95 % | 4.76 % | (3.42 %, n=6) |
| Vig **IQR** (pricing tightness) | **0.36 pp** | 1.80 pp | — |
| Line-reversal rate | 0.70 | 0.53 | — |

Read across the row and the two instruments separate cleanly:

- **FanDuel — the high-resolution instrument.** It re-prices constantly (a change on ~2 of every 3
  live polls; a new state roughly every 31 s; ~191 distinct states per game) and prices *tightly*
  (vig IQR 0.36 pp — the whole distribution of its overround sits within a third of a point). Its
  higher tick-level reversal rate (0.70) is the expected signature of a high-frequency feed making
  many small adjustments, not evidence of error. This is the book with the microstructure resolution
  any live-efficiency measurement wants.

- **Bovada — the coarse, sticky instrument.** It changes rarely (7 % of polls; a new state every
  ~8 minutes; only ~25 states per game) and its pricing is far looser (vig IQR 1.80 pp, 5× FanDuel's).
  It sets a line and largely sits on it. Fewer, larger moves; lower reversal rate. Not "worse" — a
  *different* instrument, closer to a slow consensus anchor than a live tape.

- **Pinnacle — absent.** 6 rows ever, 0 live. This is Engineering Debt item **ED-1** (stillborn
  feed), not a characterization result. Its 3.42 % vig on 6 rows is a curiosity, not a measurement.

## The question I will **not** answer yet: which book leads?

The most important question — *which book incorporates information first* — is **unresolved, and I am
deferring it deliberately rather than reporting a confounded number.**

A naive "who reaches a given line level first" metric is worthless here, and I can prove it: under
two equally reasonable definitions of "first arrival at a line level," the leader **flips entirely** —
one definition says Bovada leads 69 % of the time, the other says FanDuel leads 76 % — and the
implied median "lead" balloons to ~24 hours, which is obviously the pregame line being set a day
early, not price discovery. The metric is confounded by the very granularity difference documented
above: a coarse book trivially "arrives first" at a line level and sits there while a granular book
oscillates through and re-touches levels later.

**Leadership can only be measured by aligning each book's moves to game events** (runs scored, outs,
inning changes) from `game_state_panel.jsonl` and asking which book adjusts first *after a
state-changing event*. That event-aligned test is the next edition's job. It is the same
event-alignment the sync-lag design review needs, so the two converge.

## Scorecard against the eight questions asked

| Question | Answer | Confidence |
|---|---|---|
| Which book updates most often? | **FanDuel** (0.65 vs 0.07 change rate) | High |
| Which book posts the widest menu? | Tie live (60 each); Bovada lists a few more pregame (66) | High |
| Which book has the fewest stale quotes? | **FanDuel** by cadence (31 s vs 8 min between changes) — but "stale" ≠ "wrong" for a sticky book | Medium |
| Which book is most internally consistent (pricing)? | **FanDuel** (vig IQR 0.36 pp vs 1.80 pp) | High |
| Which book updates first (leads)? | **Unresolved — confounded; deferred to event-aligned test** | — |
| Which book suspends first? | **Instrumentation gap** — needs the market-status stream (OPEN/SUSPENDED/REMOVED), not in `book_panel` | — |
| Which book reopens first? | **Instrumentation gap** — same status stream | — |
| Which should be benchmark vs noisy? | **Not designatable yet** — requires the leadership test above | — |

## Two instrumentation gaps this surfaced

1. **Suspend/reopen ordering is structurally un-measurable, not just a missing panel field.** Per
   `RESEARCH_DEBT.md` **RD-4**, FanDuel emits OPEN/SUSPENDED/REMOVED but **Bovada emits no status at
   all**. So the question "which book suspends first" cannot be answered by adding a `status` column
   to `book_panel` — one of the two instruments never reports the event. This is a source-level
   asymmetry (a data limitation of the Bovada feed), and filtering on FanDuel's status alone would
   itself introduce asymmetric selection (RD-4). The honest disposition: this question is
   **unanswerable with the current two-book roster**, full stop — not a to-do.
2. **No event-aligned join is materialized.** Leadership needs `book_panel` × `game_state_panel` on
   `(game, ts)`. The data exists; the join does not. This is the core of edition v0.2.

## What this changes (and does not change)

- **Changes:** the book-interchangeability assumption is now provisionally **false** and belongs in
  the Research Debt register as a measurement threat — any future cross-book statistic must account
  for the fact that FanDuel and Bovada are different instruments.
- **Does not change:** any scientific conclusion, Paper 1, or the collector. No efficiency claim is
  made or implied. This is instrument characterization that makes future analysis *harder to fool*.
