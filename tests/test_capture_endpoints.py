"""Guards for the two capture endpoints and every capture surface on the site.

These endpoints are the only server-side code in an otherwise static build, and every request they
handle carries a stranger's email address. What follows is the set of properties that must hold no
matter who edits them next.

THE DEFECT THIS FILE EXISTS BECAUSE OF. Until 2026-08-01 the site had a working, live email capture
on fifty-five built pages that posted straight from the browser to api.web3forms.com with its access
key inline in the HTML. A third party held every address, the key was public to anyone who viewed
source, nothing recorded what a reader had agreed to, and the essay-strip handler in dw-context.js
added its success class inside its own `.catch`, so a reader whose subscription failed outright was
still shown the confirmation. Two separate test files asserted parts of that arrangement were
correct. Tests pin behaviour whether or not the behaviour is right, so these are written to pin the
properties rather than the implementation.
"""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
API = ROOT / "api"
WEB = ROOT / "src" / "drift" / "web"
DOCS = ROOT / "docs"

ENDPOINTS = ("subscribe.js", "request.js")


def _api(name):
    return (API / name).read_text(encoding="utf-8")


def _code(name):
    """The endpoint with its comments stripped.

    Scans that look for a token in raw source keep catching the prose that explains why the token
    is absent. Rules about what the code DOES must read the code.
    """
    s = _api(name)
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    return re.sub(r"^\s*//.*$", "", s, flags=re.M)


# ── nothing secret reaches the browser ────────────────────────────────────────────────────────

def test_no_provider_key_is_ever_written_into_a_shipped_page():
    """The whole point of moving off the third-party form. A key in the page source is not a key."""
    bad = re.compile(r"(api[_-]?key|access[_-]?key|server[_-]?token)\s*[:=]\s*['\"][A-Za-z0-9_\-]{8,}",
                     re.I)
    for p in list(WEB.glob("*.html")) + list(WEB.glob("*.js")) + list(DOCS.glob("*.html")):
        t = p.read_text(encoding="utf-8", errors="ignore")
        m = bad.search(t)
        assert not m, f"{p.name} embeds what looks like a provider credential: {m.group(0)[:40]!r}"


@pytest.mark.parametrize("name", ENDPOINTS)
def test_endpoints_read_their_keys_from_the_environment(name):
    s = _code(name)
    assert "process.env" in s or "env(" in s
    assert not re.search(r"['\"][A-Za-z0-9]{24,}['\"]", s), f"{name} looks like it hardcodes a secret"


def test_no_shipped_page_posts_an_address_to_a_third_party():
    """Every capture form on the site targets a Driftwood path, never another origin."""
    for p in list(WEB.glob("*.html")) + list(DOCS.glob("**/*.html")):
        t = p.read_text(encoding="utf-8", errors="ignore")
        for action in re.findall(r'<form[^>]+action="([^"]+)"', t):
            assert action.startswith("/api/"), f"{p.name}: form posts to {action!r}"
        for token in ("web3forms", "formspree.io", "api.mailchimp"):
            assert token not in t.lower(), f"{p.name} still references {token!r}"


# ── the two consents stay separate ────────────────────────────────────────────────────────────

def test_the_request_endpoint_cannot_subscribe_anyone():
    """A reader who asks for one document has consented to one document.

    If this ever fails, someone has made the request path quietly add people to the list, which is
    the single change most likely to turn an honest capture into the thing it replaced.
    """
    assert "buttondown" not in _code("request.js").lower(), \
        "request.js must not touch the subscriber list"


def test_both_endpoints_record_what_was_consented_to():
    for name in ENDPOINTS:
        s = _api(name)
        assert "consentRecord" in s, f"{name} does not write a consent record"
    lib = (API / "_lib.js").read_text(encoding="utf-8")
    for field in ("consent_kind", "consent_text", "source_page", "submitted_at"):
        assert field in lib, f"the consent record is missing {field}"


def test_the_publication_uses_double_opt_in():
    """A single opt-in list accumulates addresses that never asked, and this sending domain also
    carries the firm's client mail."""
    assert '"unactivated"' in _api("subscribe.js")


# ── the endpoints refuse what they should refuse ──────────────────────────────────────────────

@pytest.mark.parametrize("name", ENDPOINTS)
def test_endpoints_reject_offsite_callers(name):
    """Without an origin check the endpoint is an open relay for Driftwood-branded mail."""
    s = _code(name)
    assert "fromOurSite" in s and "403" in s


@pytest.mark.parametrize("name", ENDPOINTS)
def test_endpoints_are_post_only_and_rate_limited(name):
    s = _code(name)
    assert "405" in s and 'req.method !== "POST"' in s
    assert "tooFast" in s and "429" in s


@pytest.mark.parametrize("name", ENDPOINTS)
def test_endpoints_honour_the_honeypot_without_announcing_it(name):
    s = _code(name)
    assert "isBot" in s
    assert re.search(r"isBot\(body\)\)\s*return send\(res, 200", s), \
        f"{name} should answer a bot exactly as it answers a person"


# ── promises the code can actually keep ───────────────────────────────────────────────────────

def test_every_offered_artifact_resolves_to_a_page_that_exists():
    """A link in a Driftwood email that 404s costs more than the document was worth."""
    s = _api("request.js")
    for href in re.findall(r"href: `\$\{SITE\}/([a-z0-9\-]+\.html)", s):
        assert (WEB / href).exists(), f"request.js offers {href}, which is not a page"


def test_only_real_publications_can_be_subscribed_to():
    """'no placeholders ship', applied to email: the endpoint will not open a list for a
    publication that does not exist on the site yet."""
    s = _api("subscribe.js")
    topics = re.findall(r'^\s*"([a-z0-9\-]+)":', s, re.M)
    assert topics, "no topic map found"
    for t in topics:
        page = {"driftwood-review": "driftwood-review.html",
                "research": "research.html",
                "commentary": "commentary.html"}.get(t)
        assert page and (WEB / page).exists(), f"subscribe.js offers {t!r} with no page behind it"


def test_no_capture_surface_names_a_retired_publication():
    """The Driftwood Letter became The Driftwood Review. A form that subscribes a reader to a name
    the site no longer uses tells them, correctly, that nobody is minding the details."""
    for p in WEB.glob("*.html"):
        t = p.read_text(encoding="utf-8")
        if 'class="es-form"' not in t and 'class="capform"' not in t:
            continue
        assert "Driftwood Letter" not in t, f"{p.name} subscribes readers to a retired publication"


def test_the_confirmation_is_not_shown_when_the_request_failed():
    """dw-context.js used to add the success class inside its .catch. The replacement must only
    congratulate a reader whose request actually succeeded."""
    s = (WEB / "dw-capture.js").read_text(encoding="utf-8")
    catch = s[s.index(".catch(function ()"):]
    assert "DONE" not in catch.split("});")[0], "dw-capture.js reports success on failure"
    assert "res && res.ok" in s, "success must be gated on the endpoint's own answer"


def test_every_disclosure_in_outbound_mail_matches_the_site():
    """Mail is an advertising communication by a registered representative, and its disclosure has
    to say what the site's does, including the affiliate sentence collapsed on 2026-08-01."""
    s = _api("request.js")
    assert "Park Avenue Securities" in s
    assert "Driftwood Wealth is not an affiliate or" in s
    assert "Capitol Wealth Strategies" not in s
    for banned in ("Form ADV", "Form CRS", "adviserinfo.sec.gov"):
        assert banned not in s, f"outbound mail references {banned!r}"
