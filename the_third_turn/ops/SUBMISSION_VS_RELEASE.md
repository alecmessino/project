# Submission materials vs. archival/public-release materials

**Created 2026-08-22.** Companion to `THIRD_TURN_PROGRAM_REVIEW_2026_08.md`.

The two are routinely conflated, and conflating them is what turns a solvable rights question into a
publication blocker. **A paper can be submitted with data that cannot be archived.** Journals accept
restricted-access data statements; Zenodo deposit and CC-BY relicensing are a strictly stronger act
requiring rights the program has not established.

This file fixes the separation so each track can move independently.

---

## Track A — Submission materials

Everything a referee needs. **No public hosting, no relicensing, no permanent archive.**

| Item | Paper 1 | Paper 2 |
|---|---|---|
| Manuscript (`.md` + `.pdf`) | ✅ | ✅ |
| Figures | ✅ 11 | ✅ 10 |
| Appendices | ✅ A/B/C | ✅ 1 |
| Frozen result caches `output/*.json` | ✅ | n/a |
| Analysis + figure code | ✅ | ✅ |
| `paper/REPRODUCE.md` | ✅ | ✅ |
| `requirements-lock.txt` | ✅ | ✅ |
| Data availability **statement** | ⚠️ must be rewritten (cites a tag that does not exist) | ❌ absent — must be written |
| Data dictionary | ✅ `benchmark/dataset/schema.md` | ✅ `benchmark/dataset/panels_schema.md` |

**Track A is not blocked by data rights.** Both papers can be submitted with an availability
statement of the form: *derived artifacts sufficient to reproduce every reported number are
available at [repo]; the underlying third-party quote observations are not redistributed, and their
terms are under review.* That statement is true today and is acceptable at every venue in the
review's shortlist.

## Track B — Archival / public-release materials

Public repository, release tag, Zenodo deposit, DOI, CC-BY licensing.

**Track B is blocked until `DATA_RIGHTS_REVIEW.md` is complete.** Not partially — the blocking item
is the licence grant itself, which applies to whatever is deposited.

### Data tiers, and what may be published

| Tier | Contents | Public release | DOI/Zenodo | Commercial |
|---|---|---|---|---|
| **A · Derived reproducibility artifacts** | `output/*.json` frozen caches, `paper/figures/*.png`, `health_report.*`, test fixtures, all code | ✅ Yes | ✅ Yes | ✅ Yes (code is MIT) |
| **B · Transformed research data** | `data/trajectories.jsonl`, `data/closing_lines.csv`, `benchmark/dataset/reference_results.md` | ⚠️ Review first | ⚠️ Review first | ❌ Hold |
| **C · Raw third-party quote & header data** | `output/book_panel.part*.jsonl`, `game_state_panel.part*.jsonl`, `provenance_probe.part*.jsonl`, `market_provenance.jsonl`, `team_total_panel.jsonl` | ❌ **No** | ❌ **No** | ❌ **No** |

Tier B is not obviously safe merely because it is transformed: `trajectories.jsonl` still contains
verbatim quoted prices (`line`, `over_dec`, `under_dec`) keyed to identified fixtures. It is the
substrate of the released Benchmark Dataset v1, so its status is the **single most consequential**
question in the rights review.

### Enforcement — implemented 2026-08-22

`release/build_release.sh` now excludes Tier C **by prefix** and **fails closed** if any raw panel
file survives. Before this fix the exclusion matched 1 of 12 tracked panel files and would have
published ~260 MB of Tier C data. Verified: the built release is 22 MB and contains no panel files.

### Decisions still owed by a human

1. **`ops/` in public releases.** The builder publishes the whole directory. That now includes
   `THIRD_TURN_PROGRAM_REVIEW_2026_08.md`, an internal strategy memorandum with commercial and
   monetization analysis. It should be removed before any public push. The builder warns; it does
   not delete, because publication scope is not a decision this repository should make silently.
2. **The CC BY 4.0 grant over "Data"** in `release/README.md` and `benchmark/README.md`. Unchanged
   pending the rights review. See `DATA_RIGHTS_REVIEW.md`.
3. **Which repository is canonical**, and whether a real `v1.0` tag is cut. Paper 1 currently cites
   a tag that does not exist.
