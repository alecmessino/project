"""The two watershed assets are one drawing, and two edits can silently split them.

`watershed-hero.svg` and `watershed-hero-static.svg` are the same twelve-feeder network: the
static file is the animated file's final frame. Nothing structural enforces that — they are two
hand-maintained files — so a geometry change made to one and not the other leaves a repo where
print and screen quietly disagree, and the pages still render.

The animated file has a second exposure the static one does not. Its paint and its draw live in a
`<style>` block, and the Claude Design exporter drops `<style>` while keeping inline attributes.
Two separate exports arrived stripped, rendering as solid black shapes, which is why the block is
hand-authored here. Re-exporting over it is a live hazard rather than a hypothetical, and the
failure is invisible in a diff summary: the file still parses, still has every path, and renders
as black blobs. So the load-bearing parts are pinned here by name.

Both files are design sources under design/, not part of the deployed site.
"""
import re
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

SVG = "{http://www.w3.org/2000/svg}"
ASSETS = Path(__file__).resolve().parents[1] / "design" / "watershed-diagram-redesign" / "assets"
ANIMATED = ASSETS / "watershed-hero.svg"
STATIC = ASSETS / "watershed-hero-static.svg"

VIEWBOX = "370 52 680 626"
# tier -> (stroke, stroke-width). Copied from the locked values in watershed-hero.README.txt.
TIERS = {
    "t1": ("#5d7e96", "9.75"),
    "t2": ("#486e8a", "15"),
    "t3": ("#386280", "18"),
    "t4": ("#2c5878", "21.75"),
}


def _tree(path):
    return ET.parse(path).getroot()


def _geometry(root):
    """Every drawn element in document order, reduced to its shape alone."""
    out = []
    for el in root.iter():
        if el.tag == f"{SVG}path":
            out.append(("path", " ".join(el.get("d", "").split())))
        elif el.tag == f"{SVG}circle":
            out.append(("circle", el.get("cx"), el.get("cy"), el.get("r")))
    return out


@pytest.fixture(scope="module")
def animated():
    return _tree(ANIMATED)


@pytest.fixture(scope="module")
def static():
    return _tree(STATIC)


# ── the two files are one drawing ─────────────────────────────────────────────────────────────

def test_both_assets_exist():
    assert ANIMATED.is_file() and STATIC.is_file()


def test_the_static_file_is_the_animated_file_s_final_frame(animated, static):
    """Same shapes, same order. Diverge here and print stops matching screen."""
    assert _geometry(animated) == _geometry(static)


def test_the_drawing_is_twelve_feeders_four_two_one(animated):
    geo = _geometry(animated)
    assert sum(1 for g in geo if g[0] == "path") == 19  # 12 feeders + 4 + 2 + 1 outflow
    assert sum(1 for g in geo if g[0] == "circle") == 7  # 4 junctions + 2 confluences + 1 outflow


# ── the responsive contract ───────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("path", [ANIMATED, STATIC], ids=["animated", "static"])
def test_no_fixed_pixel_size_on_the_root(path):
    """The exporter writes width="680" height="626" every time. It has to come back off:
    the viewBox is the only intrinsic thing either file is allowed to carry."""
    root = _tree(path)
    assert root.get("width") is None
    assert root.get("height") is None


@pytest.mark.parametrize("path", [ANIMATED, STATIC], ids=["animated", "static"])
def test_viewbox_and_aspect_ratio_are_preserved(path):
    root = _tree(path)
    assert root.get("viewBox") == VIEWBOX
    assert root.get("preserveAspectRatio") == "xMaxYMid meet"


# ── what a re-export would destroy ────────────────────────────────────────────────────────────

def test_the_animated_file_still_has_its_style_block(animated):
    """The failure this guards is silent: stripped of <style>, every path falls back to the SVG
    default of fill:black; stroke:none and the file renders as solid black shapes."""
    style = animated.find(f".//{SVG}style")
    assert style is not None and style.text, (
        "watershed-hero.svg has lost its <style> block — it was almost certainly re-exported "
        "from Claude Design, which drops <style>. It now renders as solid black shapes."
    )


def test_the_animated_file_declares_the_locked_palette_and_weights(animated):
    """The tier paint lives in CSS here and in presentation attributes in the static file, so the
    equality test above cannot see it. Pin it against the locked values instead."""
    css = animated.find(f".//{SVG}style").text
    for tier, (stroke, width) in TIERS.items():
        block = re.search(rf"\.?{tier}\b[^{{]*\{{([^}}]*)\}}", css)
        assert block, f"no rule for tier {tier}"
        body = block.group(1)
        assert f"stroke:{stroke}" in body, f"{tier} stroke drifted from {stroke}"
        assert f"stroke-width:{width}" in body, f"{tier} stroke-width drifted from {width}"


def test_every_animated_path_carries_pathlength_one(animated):
    """pathLength normalises each path to one unit so a single dasharray draws a 130-unit feeder
    and a 150-unit outflow alike. It has no CSS form — drop the attribute and the draw breaks."""
    paths = [el for el in animated.iter() if el.tag == f"{SVG}path"]
    assert paths and all(el.get("pathLength") == "1" for el in paths)


def test_the_animation_uses_longhands_so_the_per_element_delays_survive(animated):
    """Every delay in the file is a per-element inline style. The `animation` shorthand resets
    animation-delay to 0, which would flatten all 19 paths onto one start and turn the tier
    sequence into a single flash — a change that looks harmless in a diff."""
    css = animated.find(f".//{SVG}style").text
    # Only the base rules. Inside the reduced-motion branch `animation:none` is the point.
    outside_media = re.sub(r"@media[^{]*\{.*?\}\s*\}", "", css, flags=re.S)
    base_rules = re.findall(r"\.ws (?:path|circle)\s*\{([^}]*)\}", outside_media)
    assert len(base_rules) == 2
    for body in base_rules:
        assert "animation-name:" in body
        assert not re.search(r"(?<![-\w])animation\s*:", body), (
            "the `animation` shorthand resets animation-delay and would collapse the sequence"
        )


def test_reduced_motion_renders_the_final_state_rather_than_nothing(animated):
    """The drawing is the argument; only its arrival is motion. Reduced motion must keep every
    stroke and node, not hide them."""
    css = animated.find(f".//{SVG}style").text
    block = re.search(r"prefers-reduced-motion:\s*reduce\s*\)\s*\{(.*?\}\s*)\}", css, re.S)
    assert block, "no prefers-reduced-motion branch"
    body = block.group(1)
    assert "stroke-dashoffset:0" in body  # paths end fully drawn
    assert "opacity:1" in body            # nodes end fully visible


def test_the_delay_ladder_runs_outward_to_inward(animated):
    """The order is the argument: water arrives at the edges, gathers, and leaves as one channel.
    A reshuffle that still animates would quietly invert the drawing's meaning."""
    delays = {}
    for tier in ("t1", "t2", "t3"):
        grp = next(el for el in animated.iter()
                   if el.tag == f"{SVG}g" and el.get("class") == tier)
        delays[tier] = [float(re.search(r"animation-delay:([\d.]+)s", p.get("style")).group(1))
                        for p in grp if p.tag == f"{SVG}path"]
    outflow = next(el for el in animated.iter()
                   if el.tag == f"{SVG}path" and el.get("class") == "t4")
    delays["t4"] = [float(re.search(r"animation-delay:([\d.]+)s", outflow.get("style")).group(1))]

    assert max(delays["t1"]) < min(delays["t2"])
    assert max(delays["t2"]) < min(delays["t3"])
    assert max(delays["t3"]) < min(delays["t4"])
