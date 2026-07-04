"""Guard for the site-wide brand typeface.

Erode (Fontshare/ITF) is the Driftwood brand face — editorial display AND body/prose. Inter is retained
ONLY for dense UI (nav, tables, tabular numbers, form controls). These tests lock that in so a future edit
can't silently regress the brand face back to Moret or drop the self-hosted Erode woff2 files.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "src" / "drift" / "web" / "driftwood.css"
DOCS_CSS = ROOT / "docs" / "driftwood.css"
FONTS = ROOT / "docs" / "fonts"
WEB = ROOT / "src" / "drift" / "web"
SCRIPTS = ROOT / "scripts"

WOFF2_MAGIC = b"wOF2"


def test_erode_woff2_files_present_and_valid():
    for w in (400, 500, 600, 700):
        f = FONTS / f"erode-{w}.woff2"
        assert f.exists(), f"missing self-hosted Erode weight: {f.name}"
        assert f.read_bytes()[:4] == WOFF2_MAGIC, f"{f.name} is not a valid woff2 (bad magic bytes)"


def test_css_defines_erode_faces_and_serif_token_is_erode():
    css = CSS.read_text()
    for w in (400, 500, 600, 700):
        assert f"font-family:'Erode';font-style:normal;font-weight:{w}" in css, \
            f"driftwood.css missing @font-face for Erode {w}"
    # --serif (the brand/display+body token) must be Erode; body must resolve to it.
    assert "--serif:'Erode'" in css, "--serif token is no longer Erode"
    assert "body{ font-family:var(--serif)" in css, "body no longer renders in the Erode --serif token"
    # Inter is retained for dense UI only — the four UI weights must still be present.
    for w in (400, 500, 600, 700):
        assert f"font-family:'Inter';font-style:normal;font-weight:{w}" in css, \
            f"driftwood.css dropped the Inter UI face {w}"


def test_dense_ui_and_numbers_pinned_to_inter():
    css = CSS.read_text()
    # tabular-number atoms and dense UI (tables/nav/form controls) must stay on --sans (Inter),
    # or serif numerals would misalign in columns.
    assert ".num,.v,.big,output,.amt,.recovered{ font-family:var(--sans)" in css, \
        "numeric atoms are no longer pinned to the Inter --sans token"
    assert "table,th,td" in css and "input,select,textarea,button" in css, \
        "dense-UI elements are no longer pinned to Inter"


def test_no_page_or_script_still_references_moret():
    # Moret was the previous display face; nothing shipped should reference it anymore.
    offenders = []
    for p in list(WEB.glob("*.html")) + [CSS, DOCS_CSS] + list(SCRIPTS.glob("og_*.mjs")):
        if "moret" in p.read_text().lower():
            offenders.append(p.name)
    assert not offenders, f"Moret is still referenced (should be Erode): {offenders}"


def test_docs_css_mirrors_source():
    # docs/driftwood.css is a plain copy of the source (via scripts/sync_docs.py) — they must match,
    # else the live site serves a stale font system.
    assert DOCS_CSS.read_text() == CSS.read_text(), \
        "docs/driftwood.css is out of sync with src — run scripts/sync_docs.py"
