# Paper 1 — Publication Package

Everything needed to disseminate Paper 1, in the order it gets used. Ready-to-paste assets live in
`SUBMISSION_KIT.md` (referenced by ID below, e.g. **D1**); this file is the operational checklist.

**Artifact under dissemination:** `paper/paper1.pdf` (1,312 KB, 11 figures, rebuilt 2026-07-28).
**Status:** scientific content **frozen**. Permitted changes are limited to, and only to:
data-availability substitution · repository URL · DOI · reproducibility language · copyediting.
No empirical claim, number, figure, or result may change (owner ruling, 2026-07-28).

---

## 1. SSRN package

| Field | Value / source |
|---|---|
| Title | From Pitcher Fatigue to Market Efficiency: A Forecast-Encompassing Test of Public Information in Live Baseball Wagering Markets |
| Author | Alec Messino |
| Affiliation | **The Third Turn Research Initiative** (independent). SSRN accepts an unaffiliated/independent entry; do not invent an institution. |
| Abstract | **D1** (~150 words) |
| Keywords | **D2** |
| JEL codes | **D2** |
| Paper file | `paper1.pdf` |
| Abstract-page summary | **D5** (plain-language) |
| Classification | Suggested networks: Econometrics, Behavioral & Experimental Finance, Sports Economics |

**Steps:** log in → *Submit a paper* → paste title/abstract/keywords/JEL → upload `paper1.pdf` →
select networks → submit. Approval is typically **1–3 business days**, not instant.

## 2. arXiv package

| Field | Value / source |
|---|---|
| Primary category | **q-fin.ST** (Statistical Finance) |
| Cross-list | **econ.EM** (Econometrics) |
| Title / abstract | Same as SSRN (**D1**); arXiv abstract field is plain text, strip markdown |
| Metadata block | **D3** |
| Upload | `paper1.pdf` (PDF-only submission is accepted) |
| License | Recommend CC BY 4.0 (matches `CITATION.cff`) |

**Note:** a first-time arXiv submission in q-fin may require **endorsement**. If prompted, request it
from a published author in the area (a cited author is a natural ask; see outreach **D8**). Budget
extra days for this — it is the single most likely cause of an arXiv delay.

## 3. GitHub release bundle

Built and verified 2026-07-28 via `bash the_third_turn/release/build_release.sh <outdir>`.

- **173 files**, MIT `LICENSE`, `CITATION.cff`, `README.md` included.
- **Secret scan: clean** (the only regex hit was the substring `ri`**`sk-`**`to-the`, a false positive).
- **Two publication decisions required before pushing:**

| Decision | Options | Recommendation |
|---|---|---|
| **Raw live panels** (`output/*_panel.jsonl`, 85 MB) | include / exclude | **Exclude for v1.** Bundle drops **106 MB → 12 MB**. Paper 1 reproduces from `output/*.json` (4.2 MB) alone; the panels are Paper 2's substrate, are still growing, and publishing an in-progress dataset invites questions Paper 1 does not need to answer. Release them with the Paper 2 / benchmark dataset. |
| **`ops/` governance registers** | include / exclude | **Include.** They contain no secrets and are the strongest available evidence for the protocol claim (a documented falsification trail, including self-corrections). This is a judgment call and reasonable people differ; excluding costs nothing scientifically. |

**Steps:** create a **public** repo `third-turn` → run the build script → `git branch -M main` →
add remote → push → tag `v1.0` → create a GitHub Release from the tag (Zenodo hooks on releases).

## 4. Zenodo checklist

1. Link Zenodo to GitHub, enable the webhook for the `third-turn` repo (**do this before tagging**).
2. Publish GitHub Release `v1.0` → Zenodo mints the DOI automatically.
3. On the Zenodo record: set title/authors to match `CITATION.cff`, license **CC BY 4.0**, resource
   type *Dataset* (or *Software* if you prefer the code framing).
4. **Then perform the one permitted Paper 1 edit** — replace the closing sentence of *Data and code
   availability* with:

   > The cleaned data, feature schema, and frozen result files are released as the Third Turn
   > Benchmark Dataset (v1) at `<repo URL>`, archived at `<DOI>`; reference implementations
   > reproduce every number reported here from the committed inputs.

5. **Also apply the reproducibility strengthening** (§4b below) in the same edit pass.
6. Rebuild: `python3 paper/build_pdf.py` → re-upload the revised PDF to SSRN (SSRN supports
   revisions) and arXiv (**v2**). Add the DOI to `CITATION.cff`.

## 4b. Reproducibility strengthening (§3.5) — pre-drafted, applies with the DOI

Permitted under the freeze: it adds infrastructure detail and changes **no empirical claim**. Append
to the end of §3.5 once the repo and DOI exist, substituting the two bracketed values:

> The full pipeline, including the collector, is released at `<repo URL>` and archived at `<DOI>`,
> with citation metadata in `CITATION.cff`. Release `v1.0` corresponds to the results reported here.
> The environment is Python 3.11 with dependencies pinned in `requirements.txt`; the analysis is
> versioned on three independent axes, Protocol 1.0, Collector 1.1, and Benchmark Dataset 2026.06,
> because method, engineering, and data evolve separately. From a clean checkout of the release tag,
> `pip install -r requirements.txt` followed by `python3 paper/make_figures.py` and
> `python3 paper/build_pdf.py` regenerates every figure and the manuscript from the committed inputs.

**Verify before publishing:** run that exact command sequence in a clean clone of the release bundle
and confirm it reproduces. Do not ship a reproduction command that has not been executed as written.

## 5. Conference submission checklist

### MIT Sloan SSAC 2027 — 🔴 the only hard deadline
- **Abstract due Oct 1, 2026, 11:59pm EST.** Submissions are open now.
- **An open-source repository link is REQUIRED.** This is why §3 is on the critical path.
- Selection on novelty, academic rigor, impact. Presentations (if selected) due mid-Feb 2027.
- Submit: abstract (**D1**) + repo link + `paper1.pdf`.

### SABR Analytics 2027 (Phoenix, ~March 2027)
- The 2027 call is **not yet posted**. The 2026 cycle closed **Nov 21, 2025**, so expect a deadline
  in **late November 2026**. **Verify on the live call before relying on it.**
- Baseball-native audience; lead with the fatigue/TTOP hook, not the econometrics.

### Secondary (no action required now)
NESSIS (~summer 2027 abstracts) · CMSAC (fall, reproducible-research track) · UCSAS (fall) ·
Saberseminar (summer) · JSM Statistics in Sports (~Feb abstracts for August).

## 6. Journals

Primary **International Journal of Forecasting** (cover letter **D4** ready). Fallbacks in order:
*Journal of Sports Economics* → *JQAS* → *Journal of Forecasting*. Aspirational only with the
strengthened draft: *Management Science*. All rolling; no deadlines.

---

## Pre-flight verification (all passing as of 2026-07-28)

- Placeholders: none · §2 Related Work: complete (16 sources, gap stated) · Citations: 0 unlisted
- Figures: 11 referenced / 11 present · Prose discipline: 0 em-dashes, 0 arrows
- PDF builds clean from source · §6 forward-promise error: **fixed**
- Outstanding: **data-availability substitution only** (blocked on repo + DOI, §3–§4)
