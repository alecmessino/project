# Live collection panels — data dictionary

**Field reference for the append-only observational panels** (Paper 2's substrate). Documentation
only: this file describes the structure of data already collected. It reports no results and is not
part of any analysis.

Companion to [`schema.md`](schema.md), which documents the **frozen Paper-1 benchmark dataset**
(half-inning snapshots, 163 games, June 2026). The two are different objects:

|  | `schema.md` (Benchmark v1) | this file (live panels) |
|---|---|---|
| Status | **Frozen**, versioned `2026.06` | **Accumulating**, ~15 min checkpoints |
| Key | `game_pk` — a true unique game identifier | `game` — a **matchup string** (`AWY@HOM`) |
| Redistribution | Tier B — under review | **Tier C — not redistributed** |

> **Counts are deliberately omitted here.** They change every checkpoint. For a dated inventory with
> an explicit as-of stamp, see `ops/THIRD_TURN_PROGRAM_REVIEW_2026_08.md` §6.

---

## The `game` key — read this first

In every panel below, `game` is a **matchup string**, not a unique game identifier. `ARI@LAD` on
07-11 and `ARI@LAD` on 07-12 share one key. Consequences:

- Per-game statistics computed on this key **pool across dates**.
- Clustered inference on this key **clusters on matchups**, not games.
- A (matchup, date) pair is the closest available proxy for a game, and is what analyses should use.

This is stated in Paper 2 and in `ops/EVIDENCE_LEDGER.md` (E-023a). It is a property of the
instrument, not a defect to be silently repaired in downstream code.

## Storage layout

Files over ~32 MB are stored **sharded** — `<name>.part00.jsonl`, `.part01.jsonl`, … — because
GitHub hard-rejects any file over 100 MiB (see E-026). Sharding is by line count and byte cap, never
by date, so reassembly is exact by construction and rows are **not** guaranteed chronologically
ordered within or across shards.

```bash
python3 the_third_turn/panel_shards.py reassemble   # shards -> monolith
python3 the_third_turn/panel_shards.py verify       # round-trip is byte-identical
```

Analysis code reads the reassembled monolith (`output/book_panel.jsonl`); git only ever stores the
shards.

---

## `book_panel` — quotes (sharded)

One row per (book, market) observation per poll. Polling cadence is ~30 s.

| Field | Type | Notes |
|---|---|---|
| `ts` | ISO-8601 UTC | Time **we received** the object, not when the book published it. See `provenance_probe`. |
| `game` | string | Matchup string — see above |
| `book` | string | `fanduel`, `bovada`, `pinnacle` |
| `line` | float | Total |
| `over_odds` | int | American odds |
| `under_odds` | int | American odds |
| `live` | bool | In-play vs pregame |
| `status` | string | Market status (`OPEN`/`SUSPENDED`/`REMOVED`). **Added in collector v1.1 — absent from earlier rows.** |

**Structural asymmetry, load-bearing for analysis:** ~54% of *pregame* (game, book, ts) groups carry
two posted lines (alternates); **0.0% of *live* groups carry more than one.** In a live-only sample
every main-line extraction rule selects the same quote. See E-025/E-025r before computing any
level-based main-line metric.

## `game_state_panel` — game state (sharded)

| Field | Type | Notes |
|---|---|---|
| `ts` | ISO-8601 UTC | |
| `game` | string | Matchup string |
| `inning` | int | 1–12 observed |
| `half` | string | `top` / `bottom` |
| `outs` | int | |
| `away_score`, `home_score` | int | Cumulative |
| `bases` | [int,int,int] | Occupancy flags, 1st/2nd/3rd |
| `tto` | int | Times through the order |
| `pitch_count` | int | Starter's count |
| `starter_on` | bool | |
| `starter_tier` | string | `Ace` / `Mid` / `Back` / `Unknown` |
| `pitcher_id` | int | MLB StatsAPI id |
| `velo_early`, `velo_recent`, `velo_drop` | float | Velocity decline inputs; sparse in early rows |

Source: MLB StatsAPI. **Subject to MLB terms — see `ops/DATA_RIGHTS_REVIEW.md` R3.**

## `team_total_panel` — modelled team totals

| Field | Type | Notes |
|---|---|---|
| `ts`, `game` | | |
| `team` | string | Team abbreviation |
| `line`, `sd`, `skew` | float | Modelled, not quoted |
| `probs` | object | Distribution over `0`…`8+` |
| `live` | bool | **Pregame only in practice** — this panel contains no live rows |
| `state` | string | |

## `market_provenance` — per-market transitions with delivery metadata

The instrument behind Paper 2 §5.3/§7.4.

| Field | Type | Notes |
|---|---|---|
| `ts` | ISO-8601 UTC | Receipt time |
| `fetch_id` | string | Groups rows from one fetch |
| `book` | string | |
| `baseline` | bool | First observation of the market |
| `changed` | list | Field names that moved since the previous observation |
| `event_id`, `market_id` | string | Book-native identifiers |
| `live` | bool | |
| `line` | float | |
| `age` | number | Reported object age |
| `event_times`, `market_times` | object | Book-supplied event/market clocks |
| `date` | HTTP date | Response `Date` header |
| `cache_control` | string | Response header |
| `x_cache` | string | CDN hit/miss — **one book only** |

**The two books do not share a schema.** Verified 2026-08-22:

| | price keys | `x_cache` |
|---|---|---|
| **fanduel** | `px_Over` / `px_Unde` | present (100%) |
| **bovada** | `px_O` / `px_U` | **absent** |

Any code reading prices from this panel must handle both spellings. This divergence is the concrete
form of Paper 2's "Book A / Book B" distinction — the cache-age book versus the book carrying an
event-level clock.

## `provenance_probe` — delivery-path measurement (sharded)

| Field | Type | Notes |
|---|---|---|
| `ts` | ISO-8601 UTC | Receipt time |
| `book` | string | |
| `n_quotes`, `n_live` | int | Quotes in the payload |
| `state` | string | `live` / `pregame` / `empty` |
| `server_date` | float | Server-reported epoch |
| `recv_minus_server_s` | float | **Delivered-object staleness** (`λ_deliv`), seconds |
| `payload_time_fields` | list | Enumerated candidate time fields with dotted path, key, kind, value kind, sample flag |

**`recv_minus_server_s` measures delivery, not publication.** It bounds how stale the object we
received was; it says nothing about when the book set the price (`λ_feed`, unmeasured). Conflating
the two is the specific error Paper 2 exists to rule out. Keep `λ_price`, `λ_feed`, `λ_deliv` and
`λ_samp` distinct.

---

## Known continuity gaps

Three documented gaps; eight calendar days absent. See `ops/DATA_CONTINUITY.md` for mechanisms and
`ops/EVIDENCE_LEDGER.md` E-022/E-023/E-026. Two of the three were **persistence** failures — the
collector ran and reported healthy while nothing reached the repository — so absence of rows does
not imply absence of collection.

| Gap | Window | Days absent |
|---|---|---|
| 1 | 2026-07-12 → 07-15 | 07-13, 07-14 |
| 2 | 2026-08-06 → 08-10 | 08-07, 08-08, 08-09 |
| 3 | 2026-08-14 → 08-17 | 08-15, 08-16, 08-17 |

No gap touches Paper 1, whose sample is June 2026 and temporally disjoint.
