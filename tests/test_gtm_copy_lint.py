"""Compliance lint for the go-to-market outreach copy (docs/GTM_*.md).

These are sign-off-gated sales-enablement drafts. The SEC Marketing Rule (206(4)-1) bars guarantees and
unqualified performance promises in adviser advertising. Principal sign-off is the human gate; this is
the automated backstop so a future edit can't slip a prohibited claim into the copy unnoticed.

Two tiers:
  • HARD — phrases that are never acceptable in outreach (e.g. "beat the market", "risk-free").
  • SOFT — words allowed ONLY in a negated/disclaimer context ("not a promise", "does not guarantee").
The negation allowlist is what lets the current compliant line "not a promise about any specific
client's account" pass while a bare "we promise …" would fail.
"""

import re
from pathlib import Path

GTM_DOCS = sorted((Path(__file__).resolve().parents[1] / "docs").glob("GTM_*.md"))

# Never acceptable in outreach copy, in any context.
HARD = [
    r"beat(?:s|ing)? the market",
    r"outperform(?:s|ing)? the market",
    r"risk[\s-]?free",
    r"riskless",
    r"can(?:no|')t lose",
    r"cannot lose",
    r"\bno risk\b",
    r"sure thing",
    r"can't miss",
    r"will (?:earn|beat|outperform|double|make you)",
    r"guaranteed returns?",
]

# Allowed only when negated/disclaimed (a negation token within the preceding ~30 chars).
SOFT = [r"\bguarantee[ds]?\b", r"\bpromise[ds]?\b", r"\bassure[ds]?\b"]
NEGATORS = ("not", "no ", "never", "without", "n't", "cannot", "can't", "don't",
            "does not", "doesn't", "isn't", "aren't", "won't")


def _violations(text: str):
    low = text.lower()
    out = []
    for pat in HARD:
        for m in re.finditer(pat, low):
            out.append(f"prohibited claim {m.group(0)!r}")
    for pat in SOFT:
        for m in re.finditer(pat, low):
            ctx = low[max(0, m.start() - 30):m.start()]
            if not any(neg in ctx for neg in NEGATORS):
                out.append(f"unqualified {m.group(0)!r} (use a negated/illustrative framing)")
    return out


def test_gtm_docs_exist():
    assert GTM_DOCS, "no docs/GTM_*.md found — the lint must have copy to guard"


def test_gtm_copy_has_no_prohibited_claims():
    problems = []
    for p in GTM_DOCS:
        for ln, line in enumerate(p.read_text().splitlines(), 1):
            for v in _violations(line):
                problems.append(f"{p.name}:{ln}: {v} -> {line.strip()[:90]}")
    assert not problems, "GTM copy contains prohibited / unqualified claims:\n  " + "\n  ".join(problems)


def test_lint_catches_a_planted_violation():
    """Self-check: the lint actually fires on a bad line and clears a properly-negated one."""
    assert _violations("Our model will beat the market and guarantees returns.")
    assert _violations("We promise you'll make money.")
    assert not _violations("This is not a promise about any specific client's account.")
    assert not _violations("Past performance does not guarantee future results.")
