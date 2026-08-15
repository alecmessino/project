"""No build-time token may ever reach a shipped page.

The templates carry tokens that are resolved at build time — `<!--FIRM_ANCHOR-->` renders the band
naming the practice and its custodian ("A PRACTICE OF ALEC MESSINO · custody Park Avenue Securities
LLC (PAS), member FINRA/SIPC"), and `<!--PLATE_LIBRARY-->` expands the canonical survey library.

The failure mode is silent and it recurred for weeks. There are two build paths — `scripts/sync_docs.py`
and the `drift` CLI (which the nightly pages job runs) — and only `render_hub` resolved the firm
anchor. So `drift statemap|taxlab|leakage` wrote docs/ pages containing the literal HTML comment
where the identity strip belongs. An HTML comment renders as nothing, so the page looked merely a
little short rather than broken. Running sync_docs.py repaired it; the next nightly run regressed it.

Two guards, because either alone is insufficient: the render functions must resolve tokens (or the
CLI reintroduces it), and the shipped output must be clean (or a future template with a new token
slips through a path nobody thought to update).
"""
import re
from pathlib import Path

import pytest

from drift import exhibit

DOCS = Path(__file__).resolve().parents[1] / "docs"
WEB = Path(__file__).resolve().parents[1] / "src" / "drift" / "web"

TOKENS = ("<!--FIRM_ANCHOR-->", "<!--PLATE_LIBRARY-->")

# Deliberately unresolved, and it must stay that way. privacy.html and terms.html are structured
# drafts awaiting counsel and the compliance principal; each carries `<!--LEGAL_DATE-->[date pending]`
# so the *visible* text reads "Last updated: [date pending]" while the token marks where a real
# effective date goes once the policy text is approved. Inventing a "last updated" date for a legal
# document that has not been reviewed would be a false representation, so nothing resolves it. The
# guard below pins it to those two draft pages so it cannot spread onto a live one.
DEFERRED = {"LEGAL_DATE": {"privacy.html", "terms.html"}}

# Every render_* that turns a template into a shipped page, and the template each one reads.
#
# This list was the hole. It named only the six renderers that already went through `_embed`, so
# the render-layer guard confirmed the fixed paths stayed fixed and said nothing about the four
# that never were: equities, the case studies, the tearsheet and the ledger each hand-rolled the
# state replace and dropped the token substitution. The nightly exhibits job regenerated all four
# onto master on 2026-08-05 and shipped the raw comment live; only the shipped-output backstop
# caught it, and only once a PR happened to run CI over master's own output. Derive the list
# rather than curate it, so a new exhibit is covered the day it is written.
RENDERERS = {
    "render_html": "TEMPLATE",
    "render_report": "REPORT_TEMPLATE",
    "render_tearsheet": "TEARSHEET_TEMPLATE",
    "render_ledger": "LEDGER_TEMPLATE",
    "render_hub": "HUB_TEMPLATE",
    "render_thesis": "THESIS_TEMPLATE",
    "render_taxlab": "TAXLAB_TEMPLATE",
    "render_leakage": "LEAKAGE_TEMPLATE",
    "render_statemap": "STATEMAP_TEMPLATE",
    "render_workspace": "WORKSPACE_TEMPLATE",
    "render_concentration": "CONCENTRATION_TEMPLATE",
}


@pytest.mark.parametrize("name", RENDERERS)
def test_no_render_path_emits_a_raw_token(name):
    """The CLI path must resolve tokens, not just sync_docs.py."""
    html = getattr(exhibit, name)({})
    for token in TOKENS:
        assert token not in html, f"{name}() ships a raw {token}"


@pytest.mark.parametrize("name", RENDERERS)
def test_every_render_path_carrying_the_anchor_actually_renders_it(name):
    """Stronger than 'no token': if the template asks for the identity strip, the output has it.
    A renderer that stripped the token without substituting anything would pass the test above."""
    template_attr = RENDERERS[name]
    template = getattr(exhibit, template_attr).read_text(encoding="utf-8")
    if "<!--FIRM_ANCHOR-->" not in template:
        pytest.skip(f"{template_attr} does not use the firm anchor")
    html = getattr(exhibit, name)({})
    assert 'class="firm-anchor"' in html, f"{name}() dropped the identity strip instead of rendering it"
    assert "Park Avenue Securities" in html


def test_every_exhibit_renderer_is_covered():
    """A renderer absent from RENDERERS is a renderer nobody is checking, which is exactly how the
    four exhibit paths went unguarded. Fail on the omission itself, not on its consequence."""
    declared = set(RENDERERS)
    actual = {n for n in dir(exhibit) if n.startswith("render_") and callable(getattr(exhibit, n))}
    assert not (actual - declared), (
        f"render path(s) not covered by the token guards: {sorted(actual - declared)} — "
        "add them to RENDERERS with the template they read")


def test_no_shipped_page_contains_a_raw_token():
    """The backstop. Covers every page and every build path, including ones added later."""
    bad = []
    for page in sorted(DOCS.glob("*.html")):
        text = page.read_text(encoding="utf-8")
        for token in TOKENS:
            if token in text:
                bad.append(f"{page.name}: {token}")
    assert not bad, f"raw build tokens shipped in docs/: {bad}"


def _paired_regions(text: str) -> set[str]:
    """Names written as a REGION rather than as a substitution: <!--X--> … <!--/X-->.

    A different mechanism with a different failure mode, and the distinction matters. A
    substitution token is empty in the template and must be replaced by a build path, so an
    unhandled one ships as nothing. A paired region already contains its rendered content in the
    committed template (scripts/kospi_interval.py writes the figures and the derived prose of
    the-interval-problem.html this way, so the page is complete before any build runs), and a
    regenerator overwrites between the markers. It cannot ship raw; it can only ship EMPTY, which
    is what the guard below checks instead.
    """
    return set(re.findall(r"<!--/([A-Z][A-Z0-9_-]{2,})-->", text))


def test_every_template_token_is_one_the_build_knows_how_to_resolve():
    """A new <!--SOMETHING--> token in a template that no build path handles would ship raw. This
    fails at authoring time instead of in production."""
    known = {t.strip("<!->") for t in TOKENS}
    unknown = set()
    for tpl in sorted(WEB.glob("*.html")):
        text = tpl.read_text(encoding="utf-8")
        paired = _paired_regions(text)
        for m in re.findall(r"<!--([A-Z][A-Z0-9_]{3,})-->", text):
            if m in known or m in paired or tpl.name in DEFERRED.get(m, ()):
                continue
            unknown.add(f"{tpl.name}: <!--{m}-->")
    assert not unknown, (
        f"template tokens no build path resolves: {sorted(unknown)}. Add handling in "
        "drift/exhibit.py::_embed and scripts/sync_docs.py::_inject_tokens, then list it in TOKENS."
    )


def test_no_generated_region_ships_empty():
    """The exemption above is only safe while the regions actually carry their content.

    An empty <!--FIG-JULY--><!--/FIG-JULY--> pair renders as a blank space with a caption under
    it, and nothing else on the page looks wrong, which is precisely the silent failure this file
    exists for. Checked in docs/, the deploy artifact, so it covers a template that was edited
    without re-running its generator.
    """
    empty = []
    for page in sorted(DOCS.glob("*.html")):
        text = page.read_text(encoding="utf-8")
        for name in _paired_regions(text):
            m = re.search(r"<!--%s-->([\s\S]*?)<!--/%s-->" % (re.escape(name), re.escape(name)),
                          text)
            if not m:
                empty.append(f"{page.name}: <!--/{name}--> has no opening marker")
            elif not m.group(1).strip():
                empty.append(f"{page.name}: <!--{name}--> is empty")
    assert not empty, f"generated regions shipped with nothing in them: {empty}"


def test_deferred_tokens_stay_on_their_draft_pages_and_show_a_human_fallback():
    """A deliberately-unresolved token is only acceptable where the visible text is honest about it.
    If LEGAL_DATE spreads to a live page, or loses its "[date pending]" fallback, it would render as
    an empty gap where a date should be — which reads as a date the reader simply missed."""
    for token, pages in DEFERRED.items():
        for tpl in sorted(WEB.glob("*.html")):
            if f"<!--{token}-->" not in tpl.read_text(encoding="utf-8"):
                continue
            assert tpl.name in pages, f"<!--{token}--> escaped onto {tpl.name}"
            shipped = (DOCS / tpl.name).read_text(encoding="utf-8")
            assert "[date pending]" in shipped, f"{tpl.name} lost its visible fallback"
            assert "structured draft" in shipped, (
                f"{tpl.name} no longer declares itself a draft, so a pending date is no longer honest"
            )
