"""Build-time provenance stamp for the published Driftwood exhibits.

The first slice of SEC Rule 204-2 advertising recordkeeping: write a machine-readable record tying the
published numbers to the exact code + data + determinism settings that produced them, so an examiner (or
a successor maintainer) can trace any claim back to its source. The nightly workflow regenerates this on
every refresh; git history then provides the immutable, timestamped archive.

    python scripts/stamp_provenance.py        # writes docs/_provenance.json (set PROVENANCE_TS to pin the time)
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def git(*args, default="unknown"):
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:  # noqa: BLE001
        return default


def sha256_16(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16] if p.exists() else None


def main() -> int:
    cache = ROOT / "tests" / "data" / "matrix_history.json"
    prov = {
        "generated_at": os.environ.get("PROVENANCE_TS")
        or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_commit": git("rev-parse", "HEAD"),
        "git_short": git("rev-parse", "--short", "HEAD"),
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "determinism": "PYTHONHASHSEED=0 for the lot-protected tax-alpha path (scripts/tax_alpha.py)",
        "data_sources": {
            "tests/data/matrix_history.json": {
                "sha256_16": sha256_16(cache),
                "note": "40y proxy-spliced ETF cache (Tiingo->Stooq->Yahoo); the published figures use "
                        "the most recent 30y window (1996-2026).",
            },
        },
        "claims": {
            "Structural Alpha (tax) +3.7-4.7%/yr": {
                "source": "scripts/tax_alpha.py::all_state_alpha -> src/drift/leakage.py::STATE_ALPHA",
                "window": "30y (1996-2026)",
                "regression_test": "tests/test_leakage_alpha_lineage.py",
            },
            "Model Portfolio backtest (hypothetical)": {
                "source": "src/drift/ledger.py, src/drift/tearsheet.py",
                "note": "hypothetical / backtested model results — not a live account or client track.",
            },
        },
        "research_flags": {
            "tilt_overlay": False,
            "lot_protect": False,
            "note": "OFF in every shipped config; enforced by tests/test_drift_tax.py "
                    "(test_shipped_configs_keep_research_flags_off) AND the drift-pages.yml pre-publish gate.",
        },
        "disclosures": "Every exhibit carries RIA identity + Form ADV/CRS + hypothetical-performance "
                       "language; guarded by tests/test_drift_disclosures.py.",
    }
    out = ROOT / "docs" / "_provenance.json"
    out.write_text(json.dumps(prov, indent=2) + "\n")
    print(f"wrote {out.relative_to(ROOT)} · commit {prov['git_short']} · "
          f"cache {prov['data_sources']['tests/data/matrix_history.json']['sha256_16']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
