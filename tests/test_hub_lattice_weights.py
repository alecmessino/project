"""The Coordination Engine's edge weights must be DERIVED, never asserted.

The lattice draws two stroke weights. A *structural* edge is one whose two systems both appear in
EVERY decision-trace the homepage publishes; a *situational* edge is one that only some decisions
move. That distinction is a claim about the firm's own worked decisions, so it is computed here from
the `TRIG` trace sets and compared against the markup, rather than trusted.

Why this guard exists: a continuous "correlation strength" ramp was proposed and rejected, because
nothing in the repo derives a pairwise correlation between financial systems and inventing one would
put an unfalsifiable quantitative claim on the front page (see FIGURE_PROVENANCE.md). Two weights with
a countable definition are defensible; a gradient is not. Equally, drawing all 21 edges identically is
*also* a claim (that every dependency is equally strong) and one the traces themselves contradict, so
"just make them uniform" is not the safe default either.

If a trace is added, removed, or re-scoped, the structural set changes and this test fails until the
diagram is updated to match. That is the point.
"""
import re
from itertools import combinations
from pathlib import Path

HUB = Path(__file__).resolve().parents[1] / "src" / "drift" / "web" / "hub.html"

_TRIG_SET_RE = re.compile(r"set:\s*\[([\d,\s]+)\]")
# Parse the whole class attribute: edges may carry net--structural, net--rim, or both, in any order.
_EDGE_RE = re.compile(r'<line class="(?P<cls>[^"]*)" data-a="(?P<a>\d)" data-b="(?P<b>\d)"')


def _parse():
    text = HUB.read_text(encoding="utf-8")
    traces = [
        [int(n) for n in re.findall(r"\d+", body)]
        for body in _TRIG_SET_RE.findall(text)
    ]
    edges, rim = {}, set()
    for m in _EDGE_RE.finditer(text):
        classes = m.group("cls").split()
        if "net" not in classes:
            continue
        a, b = int(m.group("a")), int(m.group("b"))
        pair = (min(a, b), max(a, b))
        edges[pair] = "net--structural" in classes
        if "net--rim" in classes:
            rim.add(pair)
    return text, traces, edges, rim


def test_the_lattice_is_a_complete_graph_over_seven_systems():
    """Seven systems, every pair drawn: 7C2 = 21 edges. The 'no decision touches just one' claim
    depends on the graph actually being complete."""
    _, _, edges, _ = _parse()
    assert len(edges) == 21, f"expected 21 edges over 7 systems, found {len(edges)}"
    assert set(edges) == set(combinations(range(7), 2))


def test_structural_edges_are_exactly_those_in_every_published_trace():
    """The derivation. A structural edge's two systems must BOTH appear in every trace."""
    _, traces, edges, _ = _parse()
    assert len(traces) >= 4, f"expected the published decision traces, found {len(traces)}"

    core = set(range(7))
    for t in traces:
        core &= set(t)
    expected = {pair for pair in edges if pair[0] in core and pair[1] in core}
    actual = {pair for pair, structural in edges.items() if structural}

    assert actual == expected, (
        "the lattice's heavy edges no longer match the decisions it publishes.\n"
        f"  systems in every trace: {sorted(core)}\n"
        f"  expected structural edges: {sorted(expected)}\n"
        f"  marked in the markup:      {sorted(actual)}\n"
        "Re-mark the <line class=\"net\"> elements, or adjust the traces."
    )


def test_both_weights_are_actually_used_and_there_are_only_two():
    """Two weights, not a gradient: exactly one extra class, and both tiers non-empty (a diagram
    where every edge is structural, or none is, encodes nothing)."""
    text, _, edges, _ = _parse()
    structural = sum(1 for v in edges.values() if v)
    assert 0 < structural < len(edges), (
        f"{structural}/{len(edges)} edges structural — the distinction carries no information"
    )
    assert "net--structural" in text
    # no continuous ramp snuck in via per-edge inline stroke widths
    assert not re.search(r'<line class="net[^"]*"[^>]*style="[^"]*stroke-width', text), (
        "per-edge inline stroke-width found: weights must stay categorical, not a computed ramp"
    )


def test_the_legend_explains_the_heavier_lines():
    """A visual encoding the reader cannot decode is decoration. The rest-state caption must say what
    the heavier lines mean."""
    text, _, _, _ = _parse()
    caption = re.search(r'<p class="mrest"[^>]*>(.*?)</p>', text, re.S)
    assert caption, "the lattice's rest caption is missing"
    body = caption.group(1)
    assert "heavier" in body.lower(), "the caption must decode the heavier lines for the reader"
