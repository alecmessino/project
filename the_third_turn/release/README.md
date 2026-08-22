# The Third Turn

Two working papers on live betting markets, with the code, derived artifacts and governance record
that reproduce them.

- **Paper 1 — *From Pitcher Fatigue to Market Efficiency***: a forecast-encompassing test of public
  information in live baseball wagering markets. (`paper/paper1.md`, `paper/paper1.pdf`)
- **Paper 2 — *What Prices Cannot Tell You***: an identification study of information transmission.
  The pre-registered gate returned **Outcome C — the pricing contrast is not identifiable with this
  class of instrument**, and no estimate of it is reported. (`paper/paper2.md`, `paper/paper2.pdf`)

This repository accompanies the first paper of the same name. It began as an attempt to trade the
pitcher times-through-order penalty and became a study of a harder question: does *any* publicly
observable baseball variable improve on a sharp live betting market's own forecast of remaining
runs? Across 163 Major League Baseball games, none does. The market's forecast error is not
predictable out of sample (R² = −0.037), and the one variable that appears to beat the market, a
starter's velocity decline, turns out to be post-treatment survivorship bias.

The contribution is threefold: an **empirical** map of where public information stops improving a
sharp forecast; a **methodological** one, an escalating validation protocol (the Third Turn
Protocol) that shifts the burden of proof from predicting an outcome to improving on an existing
forecast; and an **infrastructure** one, a released benchmark dataset and the reference code that
reproduces every number and figure in the paper.

## The research program

**Paper 1 asked whether prices contain public information. Paper 2 asks whether prices reveal how
that information entered the market.** Information in prices; formation of prices. The two are
distinct questions, answered with different instruments and different assumptions.

## What is here

| Path | Contents |
|---|---|
| `paper/` | Both papers (`paper1.md`/`.pdf`, `paper2.md`/`.pdf`), all figures, and `REPRODUCE.md`. |
| `paper/build_pdf.py`, `make_figures.py`, `figstyle.py` | Regenerate the figures and the PDF. See `paper/REPRODUCE.md`. |
| `*.py` (top level) | The analysis that produces `output/*.json` (encompassing, calibration, transfer function, remaining-runs model, debiasing). |
| `output/` | The **frozen Paper-1 result caches** (`*.json`) that reproduce the paper, plus the **live collection panels** (see Data). |
| `protocol/` | The Third Turn Protocol: the validation ladder, the safeguard registry, and the objective stopping rules. |
| `benchmark/` | The Third Turn Benchmark Dataset docs: schema, reference results, changelog. |
| `ops/` | *(optional reading)* the research-governance registers, the culture of falsification made auditable. |

## Reproduce the paper

Full instructions, with the verification results for each step, are in
[`paper/REPRODUCE.md`](paper/REPRODUCE.md). The short version:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-lock.txt   # the pinned REPLICATION set
python3 encompass.py                   # -> output/encompass.json
python3 calibration.py                 # -> output/calibration.json
python3 program_a.py                   # -> output/program_a.json
python3 paper/make_figures.py          # Paper 1 figures
python3 paper/make_paper2_figures.py   # Paper 2 figures
python3 paper/build_pdf.py             # -> paper/paper1.pdf   (needs Chromium)
python3 paper/build_pdf.py paper2      # -> paper/paper2.pdf
```

Install from **`requirements-lock.txt`** (exact pins, verified). `requirements.txt` is the live
collector's runtime set — floors only, and it pulls packages replication does not need.

Every number in the paper regenerates deterministically from the committed caches in `output/`; no
live feed access is required. Verified 2026-08-22: the JSON outputs and all figures regenerate
**byte-identically**, and `pytest tests/` reports **113 passed**. PDFs rebuild to identical content
but are not byte-identical (the writer embeds a creation timestamp).

> **Do not run `paper/make_concept_figures.py`.** It is superseded: it rewrites three figures that
> `make_figures.py` already produces, with different images. See `paper/REPRODUCE.md`.

## Data

Two kinds of data ship here, kept separate on purpose:

- **`output/*.json` (frozen Paper-1 caches).** The derived snapshots and results that reproduce the
  paper exactly. This is the reproducibility core.
- **`output/*_panel.jsonl` (live collection).** Timestamped book quotes, game state, and team
  totals collected continuously since the paper's sample, accruing toward the market-microstructure
  follow-on. These are **not** used in Paper 1 (which is frozen on the June-2026 sample); they are
  provided as a growing research asset. See `benchmark/dataset/schema.md` for the field dictionary.

**The raw live-collection panels are NOT included in this repository.** They are third-party
sportsbook quote and HTTP-header observations whose redistribution terms have not been established,
and they are excluded from every public build. Field-level documentation is published in
`benchmark/dataset/panels_schema.md`; the data itself is available to researchers on request,
subject to the originating endpoints' terms. Neither paper's figures require them: Paper 1
reproduces from the frozen `output/*.json` caches, and Paper 2's figures are schematic.

## License

- **Code:** MIT (`LICENSE`).
- **Paper text and documentation:** Creative Commons Attribution 4.0 (CC BY 4.0).
- **Data:** the derived result artifacts in `output/*.json` are released under CC BY 4.0. The
  Benchmark Dataset (`data/trajectories.jsonl`) contains quoted prices obtained from a third-party
  odds feed; **its redistribution terms are under review and no licence is asserted over it beyond
  the research use for which it was released.** Raw live panels are not distributed at all. A
  persistent archive or DOI will not be minted until that review is complete.

## Citation

See `CITATION.cff`. Please cite the paper and, if you use the data, the Third Turn Benchmark Dataset.
