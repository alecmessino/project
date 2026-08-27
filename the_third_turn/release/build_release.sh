#!/usr/bin/env bash
# Assemble the public release of The Third Turn from the tracked files in this repo,
# then initialize a fresh git repo ready to push to a new PUBLIC GitHub repository.
#
#   bash the_third_turn/release/build_release.sh [OUTPUT_DIR]
#
# Default OUTPUT_DIR is ~/third-turn-public. Only committed files are included
# (so no .env, no caches outside git, no __pycache__). Run it from anywhere in the repo.
set -euo pipefail

OUT="${1:-$HOME/third-turn-public}"
ROOT="$(git rev-parse --show-toplevel)"

echo "==> assembling public release into: $OUT"
rm -rf "$OUT"; mkdir -p "$OUT"

# tracked contents of the_third_turn/ become the repo root (subtree archive, no prefix)
git -C "$ROOT" archive "HEAD:the_third_turn" | tar -x -C "$OUT"

# drop operational noise and the release-builder itself
rm -rf "$OUT/release"
find "$OUT" -type f -name '*.log' -delete

# Raw live-collection panels are EXCLUDED by default (v1 release decision, 2026-07-28):
# they are Paper 2's substrate rather than Paper 1's, they are still growing, and their
# REDISTRIBUTION RIGHTS ARE UNRESOLVED (ops/DATA_RIGHTS_REVIEW.md). Paper 1 reproduces
# from output/*.json alone.
#
# BUG FIXED 2026-08-22. The old pattern was `rm -f "$OUT"/output/*_panel.jsonl`. It was
# written before the panels were sharded (E-026, 2026-08-18) and silently stopped
# matching: of the 12 tracked panel files it excluded exactly ONE (team_total_panel.jsonl)
# and let 11 through -- book_panel.part0*.jsonl, game_state_panel.part0*.jsonl,
# provenance_probe.part0*.jsonl and market_provenance.jsonl, ~260 MB of raw third-party
# quote and HTTP-header data. Any release built between the sharding change and this fix
# would have published all of it. Exclusion is now by PREFIX, so new shards are covered
# automatically, and the result is VERIFIED below rather than assumed.
RAW_PANEL_PREFIXES="book_panel game_state_panel provenance_probe market_provenance team_total_panel"

if [ "${WITH_PANELS:-0}" = "1" ]; then
  echo "==> WARNING: including raw live panels (WITH_PANELS=1)."
  echo "==> Redistribution rights for these files are UNRESOLVED -- see ops/DATA_RIGHTS_REVIEW.md."
  echo "==> Do not publish this build until that review is complete."
else
  for pfx in $RAW_PANEL_PREFIXES; do
    rm -f "$OUT"/output/"$pfx".jsonl "$OUT"/output/"$pfx".part*.jsonl
  done
  # Fail closed: never ship a release that still contains a raw panel file.
  leftover=$(find "$OUT/output" -maxdepth 1 -type f \( -name '*panel*.jsonl' -o -name 'provenance_probe*.jsonl' -o -name 'market_provenance*.jsonl' \) 2>/dev/null || true)
  if [ -n "$leftover" ]; then
    echo "==> ERROR: raw panel files survived exclusion:" >&2
    echo "$leftover" >&2
    exit 1
  fi
  echo "==> excluded raw live panels (verified none remain; set WITH_PANELS=1 to include)"
fi
rm -f "$OUT/output/daemon.log" "$OUT/output/streamlit.log" 2>/dev/null || true

# INTERNAL OPERATIONAL MATERIALS — excluded from the public publication build
# (architecture decision, 2026-08-22). The publication repo carries the manuscripts, the
# reproducibility code and artifacts, and the governance registers that constitute the
# papers' audit trail. It does NOT carry strategy memoranda, engineering planning, or
# runtime logs.
#
# ops/GATE_DETERMINATION_66.md is DELIBERATELY RETAINED: Paper 2 cites it by path, so
# removing it would break a manuscript reference. Same reasoning for the evidence ledger,
# the governance decision log, the continuity register and the QC record -- they are the
# scientific record, not operational noise.
INTERNAL_DOCS="
ops/THIRD_TURN_PROGRAM_REVIEW_2026_08.md
ops/FINAL_PUBLICATION_STRATEGY.md
ops/SUBMISSION_VS_RELEASE.md
ops/DATA_RIGHTS_REVIEW.md
ops/DAILY_REPORT_TEMPLATE.md
ops/ENGINEERING_DEBT_AND_KNOWN_UNKNOWNS.md
ops/ENGINEERING_PREDICTION_LOG.md
ops/RESEARCH_DEBT.md
output/health_report.txt
output/health_report.json
output/metrics_history.jsonl
output/ledger.jsonl
"
for f in $INTERNAL_DOCS; do rm -f "$OUT/$f"; done
# Anonymized submission copies are venue artifacts, not public-release objects.
rm -f "$OUT"/paper/*_anon.md "$OUT"/paper/*_anon.pdf "$OUT"/paper/*_anon.html

# Fail closed: the strategy memorandum must never ship.
if [ -e "$OUT/ops/THIRD_TURN_PROGRAM_REVIEW_2026_08.md" ]; then
  echo "==> ERROR: internal program review survived exclusion" >&2
  exit 1
fi
echo "==> excluded internal operational materials (kept the cited governance registers)"

# PUBLICATION-ARTIFACT GATE. Fails the release if any manuscript's title block runs
# into the margins. Added 2026-08-27 after a retitle left the Paper 2 supplement's
# title about 3pt from both margins -- inside the page box, so nothing caught it,
# but read as clipped by a reader rendering it independently. A check that is only
# run by hand is not a gate, so it runs here, where the artifacts are assembled.
#
# Fails closed when pdftotext is unavailable: a release whose artifacts could not be
# verified should not be published.
echo "==> verifying title-block margins"
if ! command -v pdftotext >/dev/null 2>&1; then
  echo "==> ERROR: pdftotext not found; cannot verify publication artifacts." >&2
  echo "==>        install poppler-utils (apt-get install -y poppler-utils) and re-run." >&2
  exit 1
fi
if ! python3 "$ROOT/the_third_turn/paper/check_title_margins.py" "$OUT"/paper/*.pdf; then
  echo "==> ERROR: title-block margin check failed; release aborted." >&2
  exit 1
fi

echo "==> verifying figure legibility"
if ! python3 "$ROOT/the_third_turn/paper/check_figure_legibility.py"; then
  echo "==> ERROR: figure legibility check failed; release aborted." >&2
  exit 1
fi

# FIGURE-OUTPUT GATE. Added 2026-08-27 after `pdfimages -list` showed every shipped
# PDF embedding its line art as ~200 PPI PNGs. The gate accepts either production
# route -- figures embedded as vector, or embedded as raster at no less than 300 PPI
# -- and fails the release on anything below that. It also refuses to publish a
# release in which a figure has no vector master, since the masters are the form a
# journal's production desk asks for.
echo "==> verifying figure embedding (vector, or >= 300 PPI raster)"
if ! command -v pdfimages >/dev/null 2>&1; then
  echo "==> ERROR: pdfimages not found; cannot verify figure embedding." >&2
  echo "==>        install poppler-utils (apt-get install -y poppler-utils) and re-run." >&2
  exit 1
fi
if ! python3 "$ROOT/the_third_turn/paper/check_figure_output.py" \
       "$OUT"/paper/*.pdf "$OUT"/docs/VISUAL_COMPANION.pdf; then
  echo "==> ERROR: figure embedding check failed; release aborted." >&2
  exit 1
fi

# The vector masters ride along as release assets: one SVG and one PDF per figure,
# beside the PNG preview, so a production desk never has to ask for them.
masters=$(find "$OUT/paper/figures" "$OUT/docs/figures" -type f \( -name '*.svg' -o -name '*.pdf' \) 2>/dev/null | wc -l)
previews=$(find "$OUT/paper/figures" "$OUT/docs/figures" -type f -name '*.png' 2>/dev/null | wc -l)
if [ "$masters" -ne "$((previews * 2))" ]; then
  echo "==> ERROR: $previews figure(s) but $masters vector master(s); expected $((previews * 2))." >&2
  exit 1
fi
echo "==> figure masters shipped: $masters vector file(s) for $previews figure(s)"
find "$OUT" -type d -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null || true

# top-level public files (authored in release/)
cp "$ROOT/the_third_turn/release/README.md"    "$OUT/README.md"
cp "$ROOT/the_third_turn/release/LICENSE"       "$OUT/LICENSE"
cp "$ROOT/the_third_turn/release/CITATION.cff"  "$OUT/CITATION.cff"

# a .gitignore so a cloner's runtime output does not get committed
cat > "$OUT/.gitignore" <<'GI'
.venv/
__pycache__/
*.pyc
.env
*.log
GI

echo "==> files assembled:"
( cd "$OUT" && find . -maxdepth 2 -type d | sort | sed 's/^/    /' )
echo "==> total size: $(du -sh "$OUT" | cut -f1)"

# fresh git history (the user's, not this repo's)
cd "$OUT"
git init -q
git add -A
git -c user.name="Alec Messino" -c user.email="alec.messino@gmail.com" \
    commit -q -m "The Third Turn: paper, code, protocol, and benchmark dataset"

cat <<EOF

==> DONE. A clean git repo is ready at: $OUT

Next steps (you run these — creating/pushing a public repo is your action):
  1. Create a new EMPTY public repository on github.com, e.g. named 'third-turn'
     (no README/license — this bundle already has them).
  2. Push:
       cd "$OUT"
       git branch -M main
       git remote add origin https://github.com/<your-username>/third-turn.git
       git push -u origin main

Before pushing, review three things:
  - data: raw live-collection panels are now excluded automatically (and the build fails if
    any survive). Nothing further is needed unless you set WITH_PANELS=1 -- in which case do
    NOT push until the review in ops/DATA_RIGHTS_REVIEW.md is complete.
  - ops/: the governance registers are internal-flavored; remove that folder if you would
    rather not publish it. NOTE ops/THIRD_TURN_PROGRAM_REVIEW_2026_08.md in particular --
    it is an internal strategy memorandum containing commercial and monetization analysis
    and venue plans. It is almost certainly NOT intended for public release. Delete it, or
    delete ops/ entirely, before pushing.
  - licensing: README.md currently offers 'Data' under CC BY 4.0. That claim has not been
    reconciled with the third-party terms governing the collected quotes. See
    ops/DATA_RIGHTS_REVIEW.md before publishing or minting a DOI.
EOF
