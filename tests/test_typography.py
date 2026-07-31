"""Guard for the site-wide brand typeface.

Erode (Fontshare/ITF) is the Driftwood editorial face — display and editorial callouts (intros, credos,
pull-quotes). Per the "Satoshi for headings/body/UI, Erode for editorial callouts" typography decision,
the base body renders in --sans; Inter is retained for dense UI (nav, tables, tabular numbers, form
controls). These tests lock that in so a future edit can't silently regress the face back to Moret or
drop the self-hosted Erode woff2 files.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "src" / "drift" / "web" / "driftwood.css"
DOCS_CSS = ROOT / "docs" / "driftwood.css"
FONTS = ROOT / "docs" / "fonts"
WEB = ROOT / "src" / "drift" / "web"
SCRIPTS = ROOT / "scripts"

WOFF2_MAGIC = b"wOF2"


def test_both_families_ship_self_hosted_as_valid_woff2():
    """Four variable files, roman and italic, in BOTH trees.

    src/drift/web/fonts/ used to hold only the three Satoshi statics — the four Erode files lived in
    docs/ alone, so the source tree could not rebuild the site's own editorial face. Checking both
    trees is the point of this test, not an accident of it.
    """
    for tree in (FONTS, WEB / "fonts"):
        for name in ("Satoshi-Variable", "Satoshi-VariableItalic",
                     "Erode-Variable", "Erode-VariableItalic"):
            f = tree / f"{name}.woff2"
            assert f.exists(), f"missing self-hosted face: {f}"
            assert f.read_bytes()[:4] == WOFF2_MAGIC, f"{f} is not a valid woff2 (bad magic bytes)"


def test_css_declares_variable_faces_over_their_full_weight_ranges():
    css = CSS.read_text()
    # A weight RANGE is what declares a face variable. A single value here would pin every heading
    # and every body run to one master and silently synthesise the rest.
    for fam, style, rng, file in (
        ("Satoshi", "normal", "300 900", "Satoshi-Variable"),
        ("Satoshi", "italic", "300 900", "Satoshi-VariableItalic"),
        ("Erode", "normal", "300 700", "Erode-Variable"),
        ("Erode", "italic", "300 700", "Erode-VariableItalic"),
    ):
        face = f"font-family:'{fam}';font-style:{style};font-weight:{rng}"
        assert face in css, f"driftwood.css is missing the {fam} {style} variable face ({rng})"
        assert f'url("fonts/{file}.woff2") format("woff2")' in css,             f"{fam} {style} does not point at {file}.woff2 with a format browsers accept"
    # format("woff2-variations") is unrecognised by some engines, which skip the face entirely and
    # fall through to Georgia — the exact "fonts don't cascade" symptom this file exists to prevent.
    assert "woff2-variations" not in css, "the woff2-variations keyword can cause a face to be skipped"


def test_italics_are_drawn_not_synthesised():
    """Something on the site sets font-style:italic (the founder's line, editorial asides). Without a
    real italic face the browser mechanically slants the roman, which is not Erode's italic."""
    css = CSS.read_text()
    assert "font-style:italic" in css, "no italic face is declared"
    assert any("italic" in p.name.lower() for p in (WEB / "fonts").glob("*.woff2")), \
        "no italic woff2 is self-hosted"


def test_the_faces_are_self_hosted_not_fetched_from_a_cdn():
    """A third-party @import would put a render-blocking request in front of every page and hand a
    visitor's IP to a font CDN, for files already committed to this repo."""
    for css_file in (CSS, DOCS_CSS):
        text = css_file.read_text()
        assert "fontshare" not in text.lower(), f"{css_file.name} fetches fonts from a CDN"
        assert "@import" not in text, f"{css_file.name} uses @import for fonts"


def test_css_serif_token_is_erode_and_body_is_sans():
    css = CSS.read_text()
    assert "--serif:'Erode'" in css, "--serif token is no longer Erode"
    assert "body{ font-family:var(--sans)" in css, "base body no longer renders in the --sans token"
    assert "font-family:var(--serif)" in css, "Erode --serif is no longer used for editorial callouts"
    assert "'Satoshi','Inter'" in css, "--sans no longer leads with self-hosted Satoshi (Inter fallback)"


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
