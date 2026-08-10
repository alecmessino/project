"""The COI-ready state brief: a document a partner forwards to a client.

Everything guarded here is a property that makes it safe to forward. A brief is the one Driftwood
surface that leaves the site inside somebody else's email, so the things that must hold are: it
collects nothing, it asserts nothing the Atlas page does not already publish, it never carries the
staged collision layer, and the note written for the SENDER never reaches the recipient's printout.
"""
import html as _html_mod
import re
from pathlib import Path

import pytest

from drift import briefpage as B
from drift.statepage import STATE_PAGE_CODES, atlas_url, build_state_pages

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
PAGES = build_state_pages()
SAMPLE = ["IL", "CA", "TX", "NY", "WA", "NH"]


def _html(code):
    return B.render_brief(PAGES[code])


def _flat(s: str) -> str:
    """Rendered HTML, whitespace-normalised. Source copy wraps across lines and _esc turns an
    apostrophe into &#x27;, so a raw substring test compares against something the page never
    contains."""
    return re.sub(r"\s+", " ", s)


def _in_page(needle: str, page: str) -> bool:
    return _flat(_html_mod.escape(needle, quote=True)) in _flat(page)


def test_one_brief_per_state_is_published():
    for code in STATE_PAGE_CODES:
        f = DOCS / B.brief_path(code) / "index.html"
        assert f.exists(), f"{code}: no brief in the build, run drift states"


@pytest.mark.parametrize("code", SAMPLE)
def test_the_brief_collects_nothing(code):
    """It has no form, no input, no saved-household script, and no URL personalization, so there is
    no path by which forwarding it could move a household's data anywhere."""
    h = _html(code)
    for token in ("<input", "<form", "dw-context.js", "api/request", "qp.get(", "URLSearchParams"):
        assert token not in h, f"{code}: the brief carries {token!r}"


@pytest.mark.parametrize("code", SAMPLE)
def test_the_brief_never_carries_the_staged_collision_layer(code):
    """Collisions are unpublished pending the data-layer work recorded in reasoning.py. A document
    designed to be forwarded is the last place an unverified tax claim should debut."""
    assert "rules meet" not in _html(code)


@pytest.mark.parametrize("code", SAMPLE)
def test_the_brief_is_noindex_and_points_its_canonical_at_the_atlas_page(code):
    """It restates the Atlas page for a different reader. Two indexed URLs on one set of facts is
    the duplicate-content problem the editioned canonical exists to prevent."""
    h = _html(code)
    assert 'name="robots" content="noindex,follow"' in h
    assert f'<link rel="canonical" href="{atlas_url(code)}" />' in h


@pytest.mark.parametrize("code", SAMPLE)
def test_the_senders_note_is_never_printed(code):
    """The talk track is addressed to the professional. If it survives printing, the client's copy
    arrives carrying the note the professional was supposed to write themselves."""
    h = _html(code)
    assert 'id="btalk"' in h, f"{code}: the talk track is gone"
    css = h.split("<style>")[1].split("</style>")[0]
    printblock = re.search(r"@media print\{(.*?)\n  \}", css, re.S)
    assert printblock and ".strip{display:none}" in printblock.group(1).replace(" ", ""), \
        f"{code}: the sender strip is not hidden in print"


@pytest.mark.parametrize("code", SAMPLE)
def test_the_brief_keeps_the_non_competitive_framing(code):
    """The whole reason a partner forwards this is that it does not route their client away."""
    h = _html(code)
    for promise in ("does not file returns", "permanent seat",
                    "does not pay or receive compensation for professional referrals"):
        assert _flat(promise) in _flat(h), f"{code}: the brief dropped {promise!r}"


@pytest.mark.parametrize("code", SAMPLE)
def test_any_figure_carries_its_hypothetical_disclosure(code):
    """The per-$1M number is a hypothetical, and this page can end up anywhere."""
    h = _html(code)
    if "per $1M of taxable assets" in h:
        assert "Illustrative and hypothetical, not a track record" in h
        assert "no client capital was invested" in h or "no client capital invested" in h
        assert "Treat it as the floor" in h, f"{code}: the figure is not scoped to the portfolio"


def test_the_brief_books_under_the_partner_campaign():
    """A booking that starts on a partner document is partner-channel evidence, and it is the only
    evidence this document can produce."""
    for code in SAMPLE:
        assert "utm_campaign=cpa_referral" in _html(code)
        assert "utm_campaign=coordination_review" not in _html(code)


def test_no_per_partner_tracking_was_built():
    """The ask was to know which briefs partners open and forward. That needs a registry, a backend
    and a privacy-policy amendment, and OPERATIONS.md records the referral workflow as DEFERRED
    pending exactly those. A forward beacon also points at the partner's client, who agreed to
    nothing. Aggregate only: no cookie, no identifier, no per-recipient token."""
    h = _html("IL")
    for token in ("document.cookie", "localStorage", "sessionStorage", "<img", "partner_id"):
        assert token not in h, f"the brief carries per-partner tracking: {token!r}"


def test_the_brief_asserts_nothing_the_atlas_page_does_not():
    """It is an arrangement of published material, not a new set of claims. Every sentence of the
    agenda and the action register comes from the same reasoning graph the state page renders."""
    r = PAGES["IL"]["reasoning"]
    h = _html("IL")
    for c in r["coordination"]:
        assert _in_page(c["rationale"], h) or _in_page(c["title"], h)
    for a in r["actions"]:
        assert _in_page(a["step"], h), f"action step missing: {a['id']}"
        assert _in_page(a["bring"], h), f"action artifact missing: {a['id']}"


def test_nothing_calls_the_brief_a_one_pager():
    """It is two Letter pages, measured. It was briefly advertised as one, which is the kind of
    small lie a reader checks in ten seconds by hitting print."""
    import re as _re
    from drift.statepage import build_state_pages as _b, render_state_html as _r
    # The CLAIM, not the words: "One page is enough to know..." is legitimate action copy, and the
    # brief's own CSS comment explains why one page was not achievable.
    claim = _re.compile(r"one[- ]page[^.<]{0,40}brief|brief[^.<]{0,40}one[- ]page", _re.I)
    for name, h in {"brief": _html("IL"), "state page": _r(_b()["IL"])}.items():
        m = claim.search(h)
        assert not m, f"{name} still calls the brief a one-pager: {m.group(0)!r}"
