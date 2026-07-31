"""Decision Memos: the reasoning of record, and what keeps them from becoming case studies.

A Decision Memo and a Decision Library entry look similar and are not the same thing. The Library is
a **reference** — "here is what happens when a household sells a business" — evergreen, written for
someone who has not decided yet. A memo is **evidence**: one decision already taken, dated and
attributed, carrying the alternatives that were rejected and the condition that would reopen it.

Left unguarded, a memo decays into a case study. The dateline goes, the rejected options go (they
are the least flattering part), the reopening condition goes (it is the only part that creates an
obligation), and what remains is marketing prose about a hypothetical family. Each of those is
pinned here.

The category was reserved on 2026-07-31 and deliberately withheld from the masthead until a memo
existed. The overlap check that preceded it found `ic-memo.html` was already a decision memo filed
under an investment-only name, which is why the shelf launched with two entries rather than one new
page duplicating an old one.
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "src" / "drift" / "web"
DOCS = ROOT / "docs"

MEMOS = ("decision-memo-domicile.html", "ic-memo.html")
NEW_MEMO = WEB / "decision-memo-domicile.html"

# The seven systems, as the homepage names them.
SYSTEMS = ("Taxes", "Business Ownership", "Cash Flow", "Estate", "Investments",
           "Family / Purpose", "Protection")


def _text(p: Path) -> str:
    """Rendered copy: markup and the explanatory CSS comments stripped, so a rule about what the
    PAGE says is never satisfied by a comment about what the page does."""
    t = p.read_text(encoding="utf-8")
    t = re.sub(r"<style>.*?</style>", " ", t, flags=re.S)
    t = re.sub(r"<script>.*?</script>", " ", t, flags=re.S)
    t = re.sub(r"<!--.*?-->", " ", t, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t))


# ── what makes it a memo ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("name", MEMOS)
def test_every_memo_is_dated_attributed_and_tied_to_a_register_entry(name):
    """A memo without a date is an essay. Without an owner it is an opinion. Without a register
    entry it is unfindable five years on, which is the whole use case."""
    t = (WEB / name).read_text(encoding="utf-8")
    start = t.find('<div class="frontmatter"')
    assert start != -1, f"{name} has no front matter"
    # the block runs to the first section that follows it; a non-greedy match on nested <div>s
    # stops at the first cell and would pass on a one-field front matter
    end = t.find('<div class="sec"', start)
    block = t[start:end if end != -1 else len(t)]
    labels = set(re.findall(r'<div class="k">([^<]+)</div>', block))
    for field in ("Memo", "Household", "Date", "Present", "Status", "Recorded as"):
        assert field in labels, f"{name} front matter is missing {field!r} (has {sorted(labels)})"
    assert re.search(r"DR-\d{3}", block), f"{name} is not tied to a Decision Register entry"


@pytest.mark.parametrize("name", MEMOS)
def test_every_memo_records_the_alternatives_it_rejected(name):
    """The least flattering part of a memo and the first thing that gets cut. Without it the record
    reads as though the chosen answer was obvious, and the ground gets re-litigated from zero."""
    t = _text(WEB / name)
    assert "Alternatives" in t, f"{name} does not record alternatives"
    assert t.count("Rejected") >= 2, f"{name} records fewer than two rejected alternatives"


def test_the_memo_records_what_would_reopen_the_decision():
    """The field the Decision Register calls out as the one most advisors skip. It is what makes a
    review an act with a pass/fail condition rather than a re-read."""
    t = _text(NEW_MEMO)
    assert "Reopens if" in t
    assert t.count("Reopens if") >= 3, "a single trigger is a gesture, not a review condition"
    assert "change our mind" in t.lower()


def test_the_memo_records_the_assumptions_the_answer_rests_on():
    """Assumptions are what quietly go stale. Recording them is how a future reader tells whether
    the decision aged badly or the world moved."""
    t = _text(NEW_MEMO)
    assert t.count("Assumption") >= 3


def test_the_memo_shows_what_the_decision_set_in_motion():
    """The section that distinguishes a Decision Memo from an investment-committee memo: a decision
    that only affected itself would not need one. This is the coordination claim made concrete
    inside a single artifact instead of asserted on a landing page."""
    t = (WEB / "decision-memo-domicile.html").read_text(encoding="utf-8")
    assert 'class="downstream"' in t
    refs = set(re.findall(r'<span class="dr">(DR-\d{3})</span>', t))
    assert len(refs) >= 2, f"only {refs} downstream entries — the decision changed nothing else"
    body = _text(NEW_MEMO)
    for dr in refs:
        assert dr in body


def test_the_memo_names_the_systems_it_moves_and_the_one_it_does_not():
    """Six of seven, and Protection explicitly carried unchanged. A memo that finds every system
    implicated is not reading carefully — naming the one that did NOT move is what makes the other
    six credible."""
    t = (WEB / "decision-memo-domicile.html").read_text(encoding="utf-8")
    moves = re.search(r'<ul class="moves">.*?</ul>', t, re.S)
    assert moves, "the memo does not name the systems it moves"
    block = moves.group(0)
    named = [s for s in SYSTEMS if s in block]
    assert len(named) == len(SYSTEMS), f"systems missing from the list: {set(SYSTEMS) - set(named)}"
    quiet = re.findall(r'<li class="quiet">.*?<span class="mk">([^<]+)</span>', block, re.S)
    assert len(quiet) == 1, "exactly one system should be marked as not moved"
    assert "not moved" in quiet[0].lower()


# ── the prohibitions ──────────────────────────────────────────────────────────────────────────

def test_the_memo_publishes_no_dollar_or_percentage_figure():
    """It reasons about order, exposure and substantiation — which is what the decision actually
    turned on — so it needs no FIGURE_PROVENANCE row. A memo is exactly where an illustrative
    number would look authoritative and be unsourced."""
    t = _text(NEW_MEMO)
    assert "$" not in t, "a dollar figure appeared in the memo"
    assert "%" not in t, "a percentage appeared in the memo"


@pytest.mark.parametrize("name", MEMOS)
def test_every_memo_discloses_that_the_household_is_fictional(name):
    t = _text(WEB / name)
    assert "illustrative sample" in t.lower() or "illustrative" in t.lower()
    assert "hypothetical" in t.lower()
    assert "not investment, tax, or legal advice" in t.lower()


def test_the_memo_does_not_give_tax_or_legal_advice_in_its_own_voice():
    """Domicile is fact-specific and contested, and the memo's subject is a state-tax question. It
    has to say plainly that establishing residency is counsel's call, not the adviser's."""
    t = _text(NEW_MEMO)
    assert "legal question for counsel" in t
    assert "does not provide tax or legal advice" in t


# ── it ships, and it is reachable ─────────────────────────────────────────────────────────────

def test_the_memo_is_built_and_carries_the_masthead():
    built = DOCS / "decision-memo-domicile.html"
    assert built.exists(), "the memo is not registered in scripts/sync_docs.py"
    b = built.read_text(encoding="utf-8")
    assert 'class="dwnav dwnav--phase2"' in b
    assert "<!--FIRM_ANCHOR-->" not in b and "firm-anchor" in b


def test_the_memos_shelf_lists_every_memo():
    """A memo that exists but is unreachable from the shelf is an orphan — the same defect as a
    case study missing from the Decision Library."""
    section = re.search(r'id="decision-memos".*?</section>',
                        (WEB / "insights.html").read_text(encoding="utf-8"), re.S)
    assert section, "the Decision Memos shelf is missing"
    for name in MEMOS:
        assert f'href="{name}"' in section.group(0), f"the shelf omits {name}"


def test_the_memo_and_the_register_agree():
    """The memo documents DR-002. If the register's entry for it changes subject, one of the two is
    lying and the record stops being a record."""
    memo = _text(NEW_MEMO)
    reg = _text(WEB / "decision-register.html")
    assert "DR-002" in memo
    for claim in ("residency", "Texas", "Illinois"):
        assert claim in memo, f"the memo does not mention {claim!r}"
        assert claim in reg, f"the register entry does not mention {claim!r}"
    assert "Harris" in memo and "Harris" in reg


def test_the_memo_links_back_to_the_register_and_across_to_its_sibling():
    t = (WEB / "decision-memo-domicile.html").read_text(encoding="utf-8")
    assert 'href="decision-register.html"' in t
    assert 'href="ic-memo.html"' in t, "the two memos should acknowledge each other as one series"
