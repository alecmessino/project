"""One-command domain flip for the Driftwood site.

    python scripts/set_domain.py https://www.driftwoodplanning.com

Rewrites every occurrence of the current base URL (drift.site.BASE_URL) across the source templates,
the generator constant, and the static docs files — then prints the rebuild + DNS checklist. Idempotent
and reversible (run it again with the old URL). Refuses trailing slashes and non-https schemes.

Run this ONLY once the domain's DNS is live (see OPERATIONS.md 'Moving to the custom domain');
flipping canonicals to a dead host de-indexes the site.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Files carrying the base URL: the constant, the hand-written template heads, and static docs assets.
# Generated docs/*.html + sitemap.xml are NOT rewritten here — the rebuild regenerates them.
TARGETS = [
    "src/drift/site.py",
    *[str(p.relative_to(ROOT)) for p in (ROOT / "src/drift/web").glob("*.html")],
    "docs/robots.txt",
]


def current_base() -> str:
    m = re.search(r'BASE_URL = "([^"]+)"', (ROOT / "src/drift/site.py").read_text())
    if not m:
        raise SystemExit("could not read BASE_URL from src/drift/site.py")
    return m.group(1)


def rewrite(new: str, root: Path = ROOT, targets: list[str] | None = None) -> dict[str, int]:
    """Swap the base URL in-place across `targets`. Returns {file: replacements}."""
    new = new.rstrip("/")
    if not new.startswith("https://"):
        raise SystemExit(f"base URL must be https:// — got {new!r}")
    old = re.search(r'BASE_URL = "([^"]+)"', (root / "src/drift/site.py").read_text()).group(1)
    if old == new:
        raise SystemExit(f"base URL is already {new}")
    counts: dict[str, int] = {}
    for rel in targets or TARGETS:
        p = root / rel
        if not p.exists():
            continue
        t = p.read_text()
        n = t.count(old)
        if n:
            p.write_text(t.replace(old, new))
            counts[rel] = n
    return counts


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    old = current_base()
    counts = rewrite(sys.argv[1])
    total = sum(counts.values())
    for f, n in sorted(counts.items()):
        print(f"  {f}: {n} reference(s)")
    print(f"\nrewrote {total} reference(s): {old} -> {sys.argv[1].rstrip('/')}")
    host = sys.argv[1].split("//", 1)[1].rstrip("/")
    print(f"""
Next (in order — see OPERATIONS.md 'Moving to the custom domain'):
  1. echo "{host}" > docs/CNAME       # tells GitHub Pages to serve on the domain
  2. drift states --out-dir docs && drift hub --docs docs --out docs/index.html   # regenerate
     (plus leakage/statemap/taxlab/thesis, or let the nightly workflow rebuild the data exhibits)
  3. python scripts/stamp_provenance.py
  4. pytest -q tests/test_site_domain.py   # asserts no stale-host references remain
  5. commit + push; then in repo Settings -> Pages set the custom domain + Enforce HTTPS.
""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
