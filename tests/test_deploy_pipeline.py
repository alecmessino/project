"""Guard for the GitHub Pages deploy pipeline.

The nightly refresh once committed with `[skip ci]`, which skips ALL workflows for that commit —
including pages.yml (on: push). So refreshed data reached master but never DEPLOYED, and the live site
served weeks-old numbers with nothing red. These tests lock the fix: the refresh commit must not carry
a skip-ci token, and pages.yml must actually publish docs/ on a push to master.
"""

import re
from pathlib import Path

WF = Path(__file__).resolve().parents[1] / ".github" / "workflows"
SKIP_CI = re.compile(r"\[\s*(?:skip[ -]ci|ci[ -]skip|no[ -]ci|skip[ -]actions)\s*\]", re.I)


def test_refresh_commit_does_not_skip_ci_or_the_deploy():
    text = (WF / "drift-pages.yml").read_text()
    commit = next((l for l in text.splitlines() if "git commit -m" in l and "refresh Driftwood" in l), None)
    assert commit is not None, "drift-pages.yml no longer has the refresh commit line"
    assert not SKIP_CI.search(commit), (
        f"refresh commit message carries a skip-ci token — it would skip pages.yml and the data would "
        f"never deploy: {commit.strip()}")


def test_pages_workflow_deploys_docs_on_push_to_master():
    text = (WF / "pages.yml").read_text()
    assert "actions/deploy-pages@" in text, "pages.yml no longer deploys via actions/deploy-pages"
    assert "path: docs" in text, "pages.yml must upload the docs/ directory as the Pages artifact"
    # triggered by a push to master (the branch the refresh + merges land on)
    assert re.search(r"push:\s*\n\s*branches:\s*\[?\s*master", text), \
        "pages.yml must trigger on push to master"
