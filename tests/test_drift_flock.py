"""The hero flock, and the one rule that actually matters about it.

The flock is atmosphere. It is generated (`src/drift/flock.py`), it is a deployed asset, and it
is wired to the homepage only behind `?hero=flock` so it can be judged on the live page. None of
that is delicate.

What IS delicate is the boundary between this file and the house mark. Driftwood has exactly one
bird that means something — a great blue heron, one master, currently on no web page, whose entire
value is scarcity (see tests/test_drift_heron.py). The flock is a few dozen anonymous birds that
mean nothing on purpose. Those two things are one bad afternoon apart: pull the count down, push
one silhouette up in scale, give it a good position, and the homepage has quietly grown a second
house mark — one that never had to argue for the slot, because it arrived as texture.

So the drawing is tested lightly and the *distinction* is tested hard: plural, small, anonymous,
one-pass, and default-off. Those five are the flock's whole licence to exist.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from drift import flock  # noqa: E402

WEB = ROOT / "src" / "drift" / "web"
DOCS = ROOT / "docs"
ASSET = WEB / "img" / "hero-flock.svg"
HUB = WEB / "hub.html"


# ── the generator ─────────────────────────────────────────────────────────────────────────────

def test_the_flock_is_byte_identical_on_every_run():
    """A committed asset from a drifting generator rewrites itself in every future diff — the
    same reason the house mark uses a local LCG instead of the stdlib one."""
    assert flock.render_svg() == flock.render_svg()


def test_the_committed_asset_matches_the_generator():
    """If flock.py changed, `python3 scripts/build_flock.py` was the other half of the change."""
    assert ASSET.exists(), "the flock asset is missing"
    assert ASSET.read_text(encoding="utf-8") == flock.render_svg(), \
        "src/drift/web/img/hero-flock.svg is stale — run python3 scripts/build_flock.py"


def test_the_module_is_pure():
    """Math and drawing modules do no I/O (CLAUDE.md). No filesystem, no clock, no global RNG —
    a clock in here would make the asset different on every build."""
    src = (ROOT / "src" / "drift" / "flock.py").read_text(encoding="utf-8")
    for banned in ("import random", "import time", "import datetime", "open(", "Path("):
        assert banned not in src, f"flock.py is no longer pure: {banned}"


# ── the distinction from the house mark: plural, small, anonymous ─────────────────────────────

def test_the_flock_is_plural_by_a_wide_margin():
    """One bird is a house mark. A handful of birds is a composition with subjects in it. Only a
    crowd is weather, and weather is the only thing this file is licensed to be."""
    birds = flock.build()
    assert len(birds) >= flock.FLOCK_MIN_COUNT, \
        f"{len(birds)} birds is no longer a flock — it is a group portrait"


def test_no_bird_is_large_enough_to_be_a_subject():
    """THE governance number. Above the ceiling a silhouette stops being distance and starts being
    a drawing of a bird, which is the moment the page has a second mark on it whether or not
    anyone decided to give it one."""
    birds = flock.build()
    worst = max(b.span for b in birds) / flock.W
    assert worst <= flock.FLOCK_MAX_SPAN, (
        f"a bird reaches {worst:.3f} of the plate (ceiling {flock.FLOCK_MAX_SPAN}) — "
        "it has become a subject"
    )


def test_no_single_bird_dominates_the_flock():
    """Scarcity is spent by prominence, not only by size: one bird materially bigger than the rest
    is a mark with a crowd behind it. Keep the largest close to the pack."""
    spans = sorted(b.span for b in flock.build())
    median = spans[len(spans) // 2]
    assert spans[-1] <= 2.6 * median, \
        f"the largest bird is {spans[-1] / median:.1f}x the median — the flock has a protagonist"


def test_the_flock_is_not_the_house_mark():
    """Different object, different file, different technique. The flock is closed silhouettes in
    four tiers of blue; the mark is open hatch in a single ink with no outline anywhere. If these
    ever converge, one of them is being turned into the other."""
    svg = ASSET.read_text(encoding="utf-8")
    from drift import heron
    assert heron.INK.lower() not in svg.lower(), "the flock is being drawn in the house mark's ink"
    assert "heron" not in svg.lower(), "the flock asset is referencing the house mark"
    colours = set(c.lower() for c in re.findall(r"#[0-9A-Fa-f]{6}", svg))
    assert colours <= set(c.lower() for c in flock.TIERS), \
        f"the flock has left the watershed's palette: {sorted(colours)}"


def test_the_flock_does_not_ship_the_footage():
    """The whole argument for generating this was not shipping video. A raster or an embedded
    frame in here means the trade was quietly reversed."""
    svg = ASSET.read_text(encoding="utf-8")
    assert "<image" not in svg and "data:" not in svg, "the flock has grown a raster"
    assert not list(WEB.glob("**/*.mp4")) and not list(WEB.glob("**/*.webm")), \
        "video has appeared in the web tree"
    assert len(svg) < 60_000, f"the asset is {len(svg) // 1024} KB — heavier than the case for it"


# ── one pass, then nothing ────────────────────────────────────────────────────────────────────

def test_the_flock_settles_once_and_never_moves_again():
    """The doctrine the hero slot and the house mark both run under (OPERATIONS.md, 2026-08-10):
    one pass, then nothing. A slot that keeps moving asks to be watched, and this one is weather
    behind a headline."""
    svg = ASSET.read_text(encoding="utf-8")
    assert "infinite" not in svg, "the flock has acquired a loop"
    assert "alternate" not in svg, "the flock is breathing"
    assert ":hover" not in svg, "the flock is answering the cursor"


def test_the_flock_uses_longhand_animation_properties():
    """The same rule the watershed's paths carry, for the same reason: every delay here is a
    per-element inline style, and the `animation` shorthand brings an animation-delay:0 with it
    that flattens the whole entry the moment one delay moves into the stylesheet."""
    svg = ASSET.read_text(encoding="utf-8")
    assert not re.search(r"[^-]animation:", svg), \
        "the animation shorthand is back; it will flatten the per-bird delays"
    assert "animation-name:flkin" in svg, "the entry animation is gone"


def test_reduced_motion_keeps_every_bird():
    """Reduced motion loses the arrival, not the drawing — the finished frame is the picture."""
    svg = ASSET.read_text(encoding="utf-8")
    block = re.search(r"@media\(prefers-reduced-motion:reduce\)\{(.*?)\}\}", svg, re.S)
    assert block, "the flock does not honour reduced motion"
    assert "opacity:1" in block.group(1), \
        "reduced motion is hiding birds rather than seating them"


# ── the control arm is default-off ────────────────────────────────────────────────────────────

def _pages(root: Path):
    return sorted(p for p in root.glob("*.html"))


def test_the_flock_is_wired_to_exactly_one_page_and_only_behind_the_param():
    """It is an experiment, not a rollout. Any page that renders it unconditionally has adopted
    it without anyone deciding to."""
    strays = []
    for root in (WEB, DOCS):
        for page in _pages(root):
            t = page.read_text(encoding="utf-8")
            if "hero-flock.svg" not in t:
                continue
            if page.name not in ("hub.html", "index.html"):
                strays.append(f"{root.name}/{page.name}")
            elif 'hero=flock' not in t:
                strays.append(f"{root.name}/{page.name} (unconditional)")
    assert not strays, f"the flock has escaped its control arm: {strays}"


def test_the_arm_carries_no_src_until_the_param_is_read():
    """Default-off has to mean the live page fetches nothing, not merely that it displays
    nothing. `data-src` is the guarantee; a plain src would download the asset for every visitor
    to a page that never shows it."""
    t = HUB.read_text(encoding="utf-8")
    tag = re.search(r"<img class=\"flk\"[^>]*>", t)
    assert tag, "the control arm has lost its plate"
    assert 'data-src="img/hero-flock.svg"' in tag.group(0), "the arm is not deferred"
    assert not re.search(r'\ssrc=', tag.group(0)), \
        "the arm has a real src — every visitor now downloads the experiment"
    assert 'aria-hidden="true"' in tag.group(0), "the flock is announcing itself to screen readers"


def test_the_arm_replaces_the_watershed_rather_than_joining_it():
    """Two atmospheric plates in one hero is what took the house mark off the site on 2026-08-06:
    both go quieter and neither wins the slot. What is being tested here is a swap."""
    t = HUB.read_text(encoding="utf-8")
    assert re.search(r"\.hero--flock \.ws\{[^}]*display:none", t), \
        "the arm now shows the flock alongside the watershed"


def test_the_default_page_is_still_the_watershed():
    """The live homepage is unchanged by this work. If the arm ever becomes the default, that is
    an amendment to the Design Constitution and a deliberate edit to this test."""
    t = HUB.read_text(encoding="utf-8")
    assert '<svg class="ws"' in t, "the hero has lost the watershed"
    assert ".flk{display:none" in t, "the control arm is no longer default-off"
