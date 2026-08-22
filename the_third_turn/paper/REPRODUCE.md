# Reproducing the papers

Canonical replication instructions for **Paper 1** and **Paper 2**. Every command below was run
end-to-end on 2026-08-22 against commit `721f388`; the verification results are stated inline.

> **Read this before `README.md`.** The replication block in the release `README.md` previously
> listed a figure step that *overwrites* three committed figures. See "Known pitfall" below.

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
python3 paper/make_figures.py         # Paper 1: 11 figures (+ shared)
python3 paper/make_paper2_figures.py  # Paper 2: 10 figures
```

**Verified:** **21 of 21** figures referenced by the two manuscripts regenerate **byte-identical**
to the committed PNGs.

### Known pitfall — do not run `make_concept_figures.py`

`paper/make_concept_figures.py` is **superseded**. It writes three files —
`concept_laboratory.png`, `concept_encompassing.png`, `appendix_vig.png` — that
`make_figures.py` already produces, and it produces *different* images. Running it after
`make_figures.py` replaces three committed figures with versions that do not match the paper.

Verified by isolation: after `make_figures.py` alone, all three are byte-identical to the committed
figures; after `make_concept_figures.py` alone, all three differ. The script is retained for
history and is not part of any replication path.

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
