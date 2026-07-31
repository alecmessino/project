"""The Governance Register section: demonstrate the practice, don't diagram it.

This section was a table. A table is a picture of a *mechanism* — it showed how the register is
stored, which answers a question no prospect is asking. It is now a set of cards, each a matter being
carried: what it is, who has it, what it touches, when it is next examined. Same eight entries, same
data, different question answered.

The rules here are the ones that would decay quietly:

  - **The count in the prose must match the cards.** "Eight matters are already being carried" is a
    claim about what is on the page directly beneath it.
  - **Resolved matters stay.** They are the most trust-building entry on the page — proof the
    register produces outcomes rather than a backlog — and the easiest thing to delete when someone
    wants the section to look busier. OPERATIONS.md sets a floor of 25%; nothing enforced it until
    now.
  - **Every matter keeps an owner and a next date.** Those two fields ARE the differentiator. A card
    missing either is just a to-do.
  - **It stays illustrative.** A fictional household, disclosed as such, with no dollar figures.
"""
import re
from pathlib import Path

HUB = Path(__file__).resolve().parents[1] / "src" / "drift" / "web" / "hub.html"

_CARD_RE = re.compile(r'<article class="rc(?P<cls>[^"]*)"[^>]*>(?P<body>.*?)</article>', re.S)
_WORDS = {6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten", 11: "eleven", 12: "twelve"}


def _src():
    return HUB.read_text(encoding="utf-8")


def _cards():
    return [(m.group("cls"), m.group("body")) for m in _CARD_RE.finditer(_src())]


def test_the_register_is_cards_not_a_table():
    """A table answers 'how is this stored'. Cards answer 'what is being carried for me'."""
    t = _src()
    assert 'class="reg-cards"' in t
    assert 'class="reg-table"' not in t, "the register reverted to a table"
    assert len(_cards()) >= 6


def test_the_stated_count_matches_the_cards_on_the_page():
    """The prose says how many matters are carried; the cards are the evidence directly below it."""
    t = _src()
    n = len(_cards())
    assert _WORDS[n] in t.lower(), (
        f"{n} cards are on the page but the copy does not say '{_WORDS[n]}' — the claim and the "
        "evidence have drifted apart"
    )


def test_every_matter_carries_an_owner_a_touch_set_and_a_next_date():
    """Owner and next-review are the differentiator. Without them a card is a to-do item."""
    for cls, body in _cards():
        labels = re.findall(r"<dt>([^<]+)</dt>", body)
        assert labels == ["Owner", "Touches", "Next decision"], f"card fields are {labels}"
        values = [v.strip() for v in re.findall(r"<dd>(.*?)</dd>", body, re.S)]
        assert all(values), f"a card has an empty field: {body[:80]}"
        assert re.search(r'<h3 class="rc-t">.+?</h3>', body, re.S), "a card has no subject"
        assert re.search(r'<span class="st st-[a-z]+">.+?</span>', body, re.S), "a card has no status"


def test_resolved_matters_stay_on_the_record():
    """A resolved, dated matter is the most trust-building entry here — it proves the register
    closes things. OPERATIONS.md sets the floor at 25% of the sample; this enforces it."""
    cards = _cards()
    done = [c for c in cards if "rc--done" in c[0]]
    assert done, "no resolved matter is shown — the register looks like a backlog"
    ratio = len(done) / len(cards)
    assert ratio >= 0.25, f"resolved matters are {ratio:.0%} of the sample, floor is 25%"
    for _, body in done:
        assert "Resolved" in body
        assert re.search(r"<dd>Closed [A-Z][a-z]+</dd>", body), \
            "a resolved matter must carry the date it closed, not just the word"


def test_open_matters_outnumber_resolved_ones():
    """It is a live register, not a trophy case."""
    cards = _cards()
    done = sum(1 for c in cards if "rc--done" in c[0])
    assert done < len(cards) - done, "more matters are closed than open"


def test_the_section_stays_illustrative_and_figure_free():
    """A fictional household, disclosed. And no dollar or percentage figure — the register makes a
    claim about attention, not about amounts, so it needs no FIGURE_PROVENANCE row."""
    t = _src()
    sec = re.search(r'<div class="sec gal" id="governance">(.*?)\n    </div>', t, re.S)
    assert sec, "the register section is missing"
    body = sec.group(1)
    assert "fictional household" in body and "not client data" in body
    text = re.sub(r"<[^>]+>", " ", body)
    assert "$" not in text, "a dollar figure appeared in the register"
    assert "%" not in text, "a percentage appeared in the register"


def test_the_heading_names_the_benefit_not_the_mechanism():
    """It read "Everything we find is written down and owned" — true, and a description of process.
    The reader's question is what that gets them."""
    h2 = re.search(r'<h2 class="reg-h">(.*?)</h2>', _src(), re.S)
    assert h2
    head = h2.group(1).lower()
    assert "annual review" in head or "waiting" in head, f"register heading is {h2.group(1)!r}"


def test_the_cards_still_reveal_accessibly():
    """The staggered reveal must not leave a keyboard user focused on an invisible card, and must
    short-circuit under reduced motion."""
    t = _src()
    assert ".reg.seeded .rc{opacity:0" in t
    assert ".reg.seeded.in .rc{opacity:1" in t
    assert "focusin" in t, "no keyboard-safety reveal"
    assert "prefers-reduced-motion" in t
