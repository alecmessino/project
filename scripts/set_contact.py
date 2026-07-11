"""One-command contact flip for the Driftwood site — the companion to set_domain.py.

    python scripts/set_contact.py --email hello@driftwoodplanning.com \
                                  --booking https://cal.com/driftwood/intro

Rewrites every occurrence of the current contact email and/or booking URL (drift.site.CONTACT_EMAIL /
BOOKING_URL) across the source templates, the page generators, and the static docs — then updates the
constants in src/drift/site.py so the source of truth and the rendered site stay in agreement. Pass
only the flag(s) you want to change. Idempotent and reversible.

Use this the day a firm inbox / scheduler exists; until then the current values remain in place. This
never fabricates a value — it only propagates one you supply. Registration/CRD/custodian are NOT
handled here (they render only through the firm-anchor band once set in site.py; see FOUNDATION_FACTS.md).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "src/drift/site.py"

# Files that can carry a contact literal: the source templates, the Python generators, and the
# already-rendered docs (generated docs are also rewritten so a flip needs no rebuild to take effect).
def _targets() -> list[Path]:
    out: list[Path] = [SITE]
    out += sorted((ROOT / "src/drift/web").glob("*.html"))
    out += sorted((ROOT / "src/drift").glob("*.py"))
    out += sorted((ROOT / "docs").glob("*.html"))
    return out


def _current(name: str) -> str:
    m = re.search(rf'{name} = "([^"]*)"', SITE.read_text())
    if not m:
        raise SystemExit(f"could not read {name} from src/drift/site.py")
    return m.group(1)


def _rewrite(old: str, new: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    if not old or old == new:
        return counts
    for p in _targets():
        t = p.read_text()
        n = t.count(old)
        if n:
            p.write_text(t.replace(old, new))
            counts[str(p.relative_to(ROOT))] = n
    return counts


def main() -> int:
    ap = argparse.ArgumentParser(description="Flip the site's contact email and/or booking URL.")
    ap.add_argument("--email", help="new contact email (e.g. hello@driftwoodplanning.com)")
    ap.add_argument("--booking", help="new booking URL (https://…)")
    args = ap.parse_args()
    if not args.email and not args.booking:
        ap.print_help()
        return 2
    if args.booking and not args.booking.startswith("https://"):
        raise SystemExit(f"booking URL must be https:// — got {args.booking!r}")
    if args.email and "@" not in args.email:
        raise SystemExit(f"email looks wrong — got {args.email!r}")

    total = 0
    for name, new in (("CONTACT_EMAIL", args.email), ("BOOKING_URL", args.booking)):
        if not new:
            continue
        old = _current(name)
        counts = _rewrite(old, new)
        n = sum(counts.values())
        total += n
        print(f"{name}: {old} -> {new}  ({n} reference(s) across {len(counts)} file(s))")

    print(f"\nrewrote {total} reference(s). Next: python3 scripts/sync_docs.py && pytest -q")
    return 0


if __name__ == "__main__":
    sys.exit(main())
