"""The For Professionals tools band ships preset links; this pins the path they depend on.

The band on partners.html / estate-attorneys.html / referral.html hands a CPA or an attorney a
one-click link into each instrument with the state already chosen (`leakage.html?state=IL`). That
is the URL-param personalization path CLAUDE.md singles out: a page reads the same field from a URL
param and from the saved household bar, and the two can silently diverge, so the param path gets its
own test rather than being assumed to behave like the UI one.

The failure this catches is quiet and specific. A preset link goes on looking correct forever if its
destination stops reading `?state=` — or never read it, which is what happens the day a fourth
instrument is added to the band and given the same `?state=IL` suffix as its neighbours. Nothing
404s, nothing throws; the partner just lands on an unpersonalized page and the "already set to
Illinois" promise on the band above is quietly false.
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "src" / "drift" / "web"
DOCS = ROOT / "docs"

PROFESSIONAL_PAGES = ("partners.html", "estate-attorneys.html", "referral.html")

# Every href on those pages carrying a ?state= preset, as (page, target, code).
_PRESET_RE = re.compile(r'href="([a-z0-9-]+\.html)\?state=([A-Z]{2})"')


def _presets(page: Path):
    return _PRESET_RE.findall(page.read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", PROFESSIONAL_PAGES)
def test_the_band_actually_ships_preset_links(name):
    """The band's copy promises instruments 'preset to Illinois'. If the presets are gone, the
    promise is a lie the page keeps making."""
    presets = _presets(WEB / name)
    assert presets, f"{name}: the tools band no longer carries a single ?state= preset link"
    assert all(code == "IL" for _, code in presets), (
        f"{name}: a preset points at a state other than the practice's own — {presets}"
    )


@pytest.mark.parametrize("name", PROFESSIONAL_PAGES)
def test_every_preset_target_reads_the_state_off_the_url(name):
    """The destination has to honour the param, not merely accept it in the address bar."""
    for target, code in _presets(WEB / name):
        dest = WEB / target
        assert dest.exists(), f"{name}: preset link points at a missing page, {target}"
        t = dest.read_text(encoding="utf-8")
        assert 'qp.get("state")' in t or "qp.get('state')" in t, (
            f'{name}: {target}?state={code} is a preset link, but {target} never reads "state" '
            "off the URL — the link personalizes nothing"
        )


@pytest.mark.parametrize("name", PROFESSIONAL_PAGES)
def test_the_preset_survives_into_the_deployed_build(name):
    """docs/ is what ships; a preset present only in the template helps nobody."""
    assert _presets(DOCS / name) == _presets(WEB / name), (
        f"docs/{name} and the template disagree about their preset links — re-run "
        "scripts/sync_docs.py"
    )
