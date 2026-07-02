"""Freshness guard for the published data exhibits.

The site once froze silently for weeks because every workflow cron was disabled in one sweep — the
exhibits kept serving June data into July with nothing red anywhere. This fails the suite loudly when
the committed forward ledger is materially stale, so staleness is a visible defect, not a surprise.

Tolerance is 10 calendar days: generous for holiday stretches, tight enough to catch a halted refresh.
Set DRIFT_SKIP_FRESHNESS=1 for archival/offline work on old snapshots.
"""

import datetime as dt
import json
import os
import pathlib

import pytest

LEDGER = pathlib.Path("docs/ledger.json")
MAX_STALE_DAYS = 10


def test_published_ledger_is_fresh():
    if os.environ.get("DRIFT_SKIP_FRESHNESS") == "1":
        pytest.skip("freshness guard disabled via DRIFT_SKIP_FRESHNESS")
    if not LEDGER.exists():
        pytest.skip("no published ledger in this checkout")
    entries = json.loads(LEDGER.read_text()).get("entries", [])
    if not entries:
        pytest.skip("ledger has no entries")
    last = dt.date.fromisoformat(entries[-1]["date"])
    age = (dt.date.today() - last).days
    assert age <= MAX_STALE_DAYS, (
        f"docs/ledger.json last session is {last} ({age} days old) — the refresh pipeline is not "
        f"running. Re-enable the drift-pages.yml cron or trigger it via workflow_dispatch "
        f"(see OPERATIONS.md 'Interpreting a failed nightly run')."
    )
