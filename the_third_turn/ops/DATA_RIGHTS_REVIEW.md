# Data rights review — requirements

**Created 2026-08-22. STATUS: NOT STARTED.**

This file specifies **what must be established** before any public archival deposit, DOI mint, or
commercial use of collected data. It records no conclusions and changes no licence. Nothing here
authorizes anything; completing it is a prerequisite, not a permission.

> **Scope note.** This blocks **Track B only** (archival/public release/commercial) per
> `SUBMISSION_VS_RELEASE.md`. It does **not** block journal submission of either paper.

---

## Why this exists

`release/README.md` states: *"**Data and paper text:** Creative Commons Attribution 4.0."*
CC BY 4.0 grants the world an irrevocable right to redistribute, modify and **commercially exploit**
the licensed material. The material includes observations obtained from third parties.

The same README also says *"Verify the relevant terms before redistribution or commercial use."*
These two sentences contradict each other: one grants the right, the other disclaims knowledge of
whether it exists. The contradiction resolves against the program.

**No terms-of-service analysis exists anywhere in this repository.** A full-text search returns only
incidental mentions.

## Where the data comes from

Established from `sources/*.py`, `odds_collector.py` and `microstructure_probe.py`:

| Endpoint | Nature | What must be established |
|---|---|---|
| `api.the-odds-api.com/v4/...` | **Commercial licensed API** (subscriber key) | Whether the subscriber agreement permits redistribution, relicensing, or commercial use of derived/stored quotes; retention limits; attribution requirements |
| `www.bovada.lv/services/sports/event/coupon/...` | **Undocumented internal endpoint** | Site ToS position on automated access, storage, redistribution |
| `sportsbook.fanduel.com` / `sbapi...` | **Undocumented internal endpoint** | Same |
| `guest.api.arcadia.pinnacle.com` | Semi-public internal endpoint | Same |
| `statsapi.mlb.com` | MLB StatsAPI | MLB terms — commercial use is restricted; game state and IDs are affected |

`RESEARCH_LOG.md` L132 records the collection mode in the program's own words — *"the feeds we
scrape (DK 403s our IP)"* — which also documents that one operator actively blocked the collector.

## Required findings

Each must be answered in writing, with the source clause cited, before Track B proceeds.

**R1 · The Odds API subscriber terms.** May stored quotes be redistributed? Relicensed? Used
commercially? Is there a retention limit or a deletion obligation? *This is the gating question for
`data/trajectories.jsonl`, and therefore for the released Benchmark Dataset v1.*

**R2 · Sportsbook ToS (Bovada, FanDuel, Pinnacle).** Position on automated collection, storage, and
redistribution of odds. Note that odds may be asserted as proprietary even where publicly displayed.

**R3 · MLB StatsAPI terms.** Applies to `game_state_panel` and to `game_pk` identifiers in the
benchmark dataset.

**R4 · Tier B determination.** Is `data/trajectories.jsonl` sufficiently transformed to be
redistributable notwithstanding R1–R2? It still contains verbatim quoted prices keyed to identified
fixtures. **Assume not, until established.**

**R5 · Whether a factual-compilation argument applies**, and in which jurisdictions. Prices may be
uncopyrightable facts in some jurisdictions while contract terms still bind the collector
independently of copyright. Contract and copyright must be answered separately.

**R6 · HTTP headers and delivery metadata.** `market_provenance.jsonl` and `provenance_probe.*`
store response headers (`x-cache`, `cache-control`, `date`) and payload structure. Whether these are
covered by the same terms as the odds is a distinct question and is probably the most defensible
tier to publish.

**R7 · Counsel review** before any Zenodo deposit or commercial agreement, if R1–R6 leave doubt.

## Until this is complete

- **Do not** deposit any Tier B or C data to Zenodo or mint a DOI covering it.
- **Do not** relicense collected data under CC BY 4.0 or any other public licence.
- **Do not** enter any commercial arrangement involving the collected quotes.
- **Do** proceed with journal submission of both papers using a restricted-access data statement.
- **Do** publish Tier A (derived artifacts and code) freely — code is MIT and unaffected.

## Recommended interim wording

Until R1–R7 are answered, the accurate public statement is:

> Derived artifacts sufficient to reproduce every number reported in this paper are available at
> [repository]. The underlying third-party sportsbook quote observations are not redistributed; they
> were obtained from commercial and public endpoints whose terms govern their reuse, and are
> available to researchers on request subject to those terms.

This is true today, requires no rights determination, and is acceptable at the venues under
consideration.
