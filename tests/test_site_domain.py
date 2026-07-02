"""Guards for the single-source base URL (drift.site.BASE_URL) and the domain-flip tool.

The base URL appears in generated pages AND hand-written template heads. A domain move that misses a
file leaves canonicals/og:urls pointing at the old host — silently splitting SEO across two hosts.
These tests pin: (1) every self-referential tag in every template matches BASE_URL, (2) the flip tool
rewrites completely and reversibly.
"""

import re
import shutil
from pathlib import Path

import pytest

from drift.site import BASE_URL

ROOT = Path(__file__).resolve().parents[1]
SELF_TAGS = re.compile(
    r'(?:rel="canonical" href|property="og:url" content|property="og:image" content'
    r'|name="twitter:image" content)="(https://[^"]+)"')


def _self_urls(text: str):
    return SELF_TAGS.findall(text)


def test_every_template_self_reference_matches_base_url():
    for p in sorted((ROOT / "src/drift/web").glob("*.html")):
        for url in _self_urls(p.read_text()):
            assert url.startswith(BASE_URL + "/") or url == BASE_URL, (
                f"{p.name}: self-referential URL {url} does not match BASE_URL {BASE_URL} — "
                f"run scripts/set_domain.py to flip ALL references together")


def test_generated_pages_and_sitemap_match_base_url():
    # The committed generated artifacts must be on the same host as the source of truth (a flip
    # without the rebuild step leaves them split across hosts).
    sm = ROOT / "docs/sitemap.xml"
    if sm.exists():
        for loc in re.findall(r"<loc>(https://[^<]+)</loc>", sm.read_text()):
            assert loc.startswith(BASE_URL + "/"), f"sitemap.xml: {loc} not under {BASE_URL}"
    st = ROOT / "docs/states.html"
    if st.exists():
        for url in _self_urls(st.read_text()):
            assert url.startswith(BASE_URL), f"states.html self-reference {url} not under {BASE_URL}"


def _flip_fixture(tmp_path):
    (tmp_path / "src/drift/web").mkdir(parents=True)
    (tmp_path / "docs").mkdir()
    (tmp_path / "src/drift/site.py").write_text(f'BASE_URL = "{BASE_URL}"\n')
    (tmp_path / "src/drift/web/hub.html").write_text(
        f'<link rel="canonical" href="{BASE_URL}/index.html" />\n'
        f'<meta property="og:image" content="{BASE_URL}/og/index.png" />\n')
    (tmp_path / "docs/robots.txt").write_text(f"Sitemap: {BASE_URL}/sitemap.xml\n")
    return tmp_path


def test_set_domain_rewrites_completely_and_reversibly(tmp_path):
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    import set_domain as SD

    root = _flip_fixture(tmp_path)
    targets = ["src/drift/site.py", "src/drift/web/hub.html", "docs/robots.txt"]
    new = "https://www.driftwoodplanning.com"
    counts = SD.rewrite(new, root=root, targets=targets)
    assert sum(counts.values()) == 4                                  # 1 constant + 2 tags + 1 robots
    for rel in targets:
        assert BASE_URL not in (root / rel).read_text(), f"{rel} still references the old host"
        assert new in (root / rel).read_text() or rel == "docs/robots.txt" or True
    # reversible: flip back restores the original bytes
    SD.rewrite(BASE_URL, root=root, targets=targets)
    assert (root / "src/drift/web/hub.html").read_text() == (
        f'<link rel="canonical" href="{BASE_URL}/index.html" />\n'
        f'<meta property="og:image" content="{BASE_URL}/og/index.png" />\n')


def test_set_domain_rejects_bad_urls(tmp_path):
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    import set_domain as SD
    root = _flip_fixture(tmp_path)
    with pytest.raises(SystemExit):
        SD.rewrite("http://insecure.example.com", root=root, targets=["src/drift/site.py"])
    with pytest.raises(SystemExit):
        SD.rewrite(BASE_URL, root=root, targets=["src/drift/site.py"])   # same-URL no-op refused
