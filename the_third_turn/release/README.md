# The Third Turn

**From Pitcher Fatigue to Market Efficiency** — a forecast-encompassing test of public information
in live baseball wagering markets.

This repository accompanies the working paper of the same name. It began as an attempt to trade the
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

## What is here

| Path | Contents |
|---|---|
| `paper/` | The paper (`paper1.pdf`, `paper1.md`) and all nine figures. |
| `paper/build_pdf.py`, `make_figures.py`, `make_concept_figures.py`, `figstyle.py` | Regenerate the figures and the PDF. |
| `*.py` (top level) | The analysis that produces `output/*.json` (encompassing, calibration, transfer function, remaining-runs model, debiasing). |
| `output/` | The **frozen Paper-1 result caches** (`*.json`) that reproduce the paper, plus the **live collection panels** (see Data). |
| `protocol/` | The Third Turn Protocol: the validation ladder, the safeguard registry, and the objective stopping rules. |
| `benchmark/` | The Third Turn Benchmark Dataset docs: schema, reference results, changelog. |
| `ops/` | *(optional reading)* the research-governance registers, the culture of falsification made auditable. |

## Reproduce the paper

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 paper/make_figures.py          # data figures from output/*.json
python3 paper/make_concept_figures.py  # the two conceptual figures
python3 paper/build_pdf.py             # -> paper/paper1.pdf
```

Every number in the paper regenerates deterministically from the committed caches in `output/`; no
live feed access is required.

## Data

Two kinds of data ship here, kept separate on purpose:

- **`output/*.json` (frozen Paper-1 caches).** The derived snapshots and results that reproduce the
  paper exactly. This is the reproducibility core.
- **`output/*_panel.jsonl` (live collection).** Timestamped book quotes, game state, and team
  totals collected continuously since the paper's sample, accruing toward the market-microstructure
  follow-on. These are **not** used in Paper 1 (which is frozen on the June-2026 sample); they are
  provided as a growing research asset. See `benchmark/dataset/schema.md` for the field dictionary.

The panels are derived from public sportsbook feeds and are provided for research use. Verify the
relevant terms before redistribution or commercial use.

## License

- **Code:** MIT (`LICENSE`).
- **Data and paper text:** Creative Commons Attribution 4.0 (CC BY 4.0).

## Citation

See `CITATION.cff`. Please cite the paper and, if you use the data, the Third Turn Benchmark Dataset.
