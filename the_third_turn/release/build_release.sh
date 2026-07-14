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
rm -f "$OUT/output/daemon.log" "$OUT/output/streamlit.log" 2>/dev/null || true
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

Before pushing, review two things:
  - data: output/*_panel.jsonl are raw live-collection panels. The paper reproduces from
    output/*.json alone, so you may 'git rm --cached output/*_panel.jsonl' if you prefer to
    keep the raw scraped panels private.
  - ops/: the governance registers are internal-flavored; remove that folder if you would
    rather not publish it.
EOF
