# Reproducing the papers

Canonical replication instructions for **Paper 1** and **Paper 2**. Every command below was run
end-to-end on 2026-08-22 against commit `721f388`; the verification results are stated inline.

> **Correction, 2026-08-27.** An earlier revision of this document told replicators *not* to run
> `paper/make_concept_figures.py`, on the finding that `make_figures.py` already produced the same
> three figures. That finding was wrong, and the isolation test behind it was wrong: it restored the
> committed PNGs before running `make_figures.py`, so three files that were never rewritten were read
> as "reproduced". `make_concept_figures.py` is the **sole** producer of `concept_laboratory.png`,
> `concept_encompassing.png` and `appendix_vig.png`. Re-verified by deleting all three and running
> `make_figures.py` alone: none reappears. Following the old instruction left three of Paper 1's
> eleven figures with no generator. The step is now in the sequence below.

## 1. Environment

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r the_third_turn/requirements-lock.txt
```

Use **`requirements-lock.txt`**, not `requirements.txt`. The latter is the live collector's runtime
set: floors only (`>=`), and it pulls `pybaseball`, `pyarrow` and `streamlit`, none of which are
needed to reproduce either paper. Interpreter: **Python 3.11.15**.

Building the PDFs additionally needs **Chromium** on `PATH` (or at `/opt/pw-browsers/chromium`).
Nothing else in this document needs it.

## 2. Reproduce the analysis outputs — byte-identical

```bash
cd the_third_turn
python3 encompass.py        # -> output/encompass.json
python3 calibration.py      # -> output/calibration.json
python3 program_a.py        # -> output/program_a.json
```

**Verified:** all three regenerate **byte-identical** to the committed files. No live feed access is
required; everything reads the frozen caches in `output/`.

## 3. Reproduce the figures — byte-identical

```bash
python3 paper/make_figures.py          # Paper 1: 8 figures
python3 paper/make_concept_figures.py  # Paper 1: 3 more (concept_*, appendix_vig)
python3 paper/make_paper2_figures.py   # Paper 2: 10 figures
python3 docs/make_companion_figures.py # Visual Companion: 3 figures
```

All four are required: each writes a disjoint set, and together they produce the **21 figures the two
manuscripts reference** plus the companion's three. Run order does not matter.

Each call writes **three coeval renditions** of one figure from one converged canvas:

| file | role |
|---|---|
| `<name>.svg` | vector master — what `build_pdf.py` embeds in the manuscript |
| `<name>.pdf` | vector master — the form a journal's production desk asks for |
| `<name>.png` | raster preview for markdown and web, written at 360 dpi (>= 300 PPI at the text measure) |

**Verified:** every figure regenerates to the same geometry; the PNGs are byte-identical to the
committed files.

## 4. Build the PDFs

```bash
python3 paper/build_pdf.py         # -> paper/paper1.pdf
python3 paper/build_pdf.py paper2  # -> paper/paper2.pdf
```

`build_pdf.py` takes an optional manuscript stem (default `paper1`); `paper2` is the documented way
to build the second manuscript.

**Verified:** both build successfully. PDFs are **not byte-reproducible** — the writer embeds a
creation timestamp — but rebuild to the same size with identical content. Byte-level
reproducibility claims apply to the JSON outputs and the figures, not to the PDFs.

`build_pdf.py` rewrites each `figures/<name>.png` reference to `figures/<name>.svg` when the master
exists, so the manuscripts embed their line art as vector rather than as a raster object. The
markdown sources are untouched — they still name the PNG. `paper/check_figure_output.py` gates the
result: every built PDF must embed its figures as vector, or as raster at no less than 300 PPI.

## 5. Tests

```bash
python3 -m pytest tests/ -q
```

**Verified: 113 passed.**

## 6. What is *not* reproducible from this repository

- **The live panels** (`output/book_panel.part*.jsonl`, `game_state_panel.part*.jsonl`,
  `provenance_probe.part*.jsonl`, `market_provenance.jsonl`) are append-only observational records
  of third-party feeds. They cannot be regenerated; they can only be re-observed, and not for a past
  date. Statistics computed on them are reproducible **only at their own as-of instant** — see
  `july_analyses.py --asof` and `paper/PAPER2_DRAFT_QC.md` §7.1.
- **Redistribution of those panels is unresolved.** See `ops/DATA_RIGHTS_REVIEW.md`. They are
  excluded from the public release build by default.
