"""The homepage lattice, as decided — not as an old handoff document described it.

The Brief-5 design handoff README specified a *static* lattice: no interaction, no hover, no
animation, all twenty-one edges equal graphite, hub labelled "Coordination". The implementation that
actually emerged is interactive, carries derived two-tier edge weights, and publishes five decision
traces. Those are not cosmetic differences. The static version *illustrates* the claim "seven
systems, no decision touches just one"; the live version *demonstrates* it — a visitor picks a
decision and watches six systems light up.

The decision (2026-07-31) was to keep the implementation and treat the README as superseded. This
file is that decision in executable form, because the risk is specific and real: someone finds the
handoff README, reads it as the spec, and "fixes" the homepage back to a picture. Every assertion
here is something that document would have removed.

The one correction taken FROM the review: the hub is labelled COORDINATION, not GOVERNANCE.
Governance is the operating principle the practice runs by, not an eighth system, so it keeps its
own home in Plate III (the Governance Register) rather than sitting at the centre of the diagram.
"""
import re
from pathlib import Path

HUB = Path(__file__).resolve().parents[1] / "src" / "drift" / "web" / "hub.html"


def _src() -> str:
    return HUB.read_text(encoding="utf-8")


# ── the hub label ─────────────────────────────────────────────────────────────────────────────

def test_the_hub_is_labelled_coordination_not_governance():
    """Governance at the centre of a systems diagram quietly promotes it to an eighth system. It is
    a process, not a system, and it belongs to the register."""
    t = _src()
    assert '<text class="hub" x="320" y="246" text-anchor="middle">COORDINATION</text>' in t
    assert 'var HUB0 = "COORDINATION";' in t
    svg = re.search(r'<svg class="net-svg".*?</svg>', t, re.S)
    if svg:
        assert "GOVERNANCE" not in svg.group(0), "GOVERNANCE is back inside the diagram"


def test_governance_keeps_its_own_home_in_the_register():
    """Removing the word from the hub must not delete the concept — Plate III is where the review
    said it belongs, and it is the page's climax."""
    t = _src()
    assert 'id="governance"' in t
    assert "Governance Register" in t


def test_the_lattice_still_has_exactly_seven_systems():
    """Seven, not eight. The 8th-node proposal was rejected on geometry: K8 puts four diameters
    through the centre, straight through the hub label."""
    t = _src()
    nodes = re.findall(r'<g class="node"[^>]*data-i="(\d)"', t)
    assert sorted(nodes) == [str(i) for i in range(7)], f"node set is {sorted(nodes)}"


# ── what the superseded README would have deleted ─────────────────────────────────────────────

def test_the_five_decision_traces_survive():
    """The most important interaction on the homepage: pick a decision, watch six systems move.
    A static diagram cannot make that argument, it can only assert it."""
    t = _src()
    sets = re.findall(r"set:\s*\[([\d,\s]+)\]", t)
    assert len(sets) == 5, f"expected five published decision traces, found {len(sets)}"
    for s in sets:
        touched = [int(n) for n in re.findall(r"\d+", s)]
        assert len(touched) >= 5, f"a trace touching {len(touched)} systems undercuts the claim"
        assert len(set(touched)) == len(touched), "a trace repeats a system"


def test_the_lattice_is_interactive():
    """Interaction here is explanatory, not decorative — it is how the claim gets demonstrated."""
    t = _src()
    assert "addEventListener" in t
    assert 'class="node"' in t and "cursor:pointer" in t
    # and it stays accessible to the keyboard, not mouse-only
    assert 'tabindex="0"' in t or "keydown" in t


def test_the_two_tier_edge_weights_survive():
    """Derived from the published traces (see test_hub_lattice_weights.py), so the diagram reads as
    researched rather than illustrated. Flattening all 21 edges to one weight is itself a claim —
    that every dependency is equally strong — and the traces contradict it."""
    t = _src()
    assert "net--structural" in t and "net--rim" in t
    assert len(re.findall(r'<line class="[^"]*net[^"]*"', t)) == 21


def test_the_rest_state_is_graphite_with_a_single_blue_accent():
    """No second accent colour. The blue budget is spent on the flow/trace only."""
    t = _src()
    stage = re.search(r"\.sysstage\.seeded[^}]*\}(?:[^.]|\.(?!sysstage))*", t, re.S)
    assert stage, "the seeded rest state is missing"
    block = re.search(r"(\.sysstage\.seeded.*?)\n\n", t, re.S)
    assert block
    # the rest state paints with the accent + the ghost line, and introduces no new hue
    assert "--accent-strike" in block.group(1)
    assert "--ghost-line" in block.group(1)
    hexes = set(re.findall(r"#[0-9a-fA-F]{6}", block.group(1)))
    assert not hexes, f"the rest state hardcodes colour instead of using tokens: {hexes}"


def test_reduced_motion_is_respected():
    """Explanatory motion still has to be optional."""
    assert "prefers-reduced-motion" in _src()


def test_the_homepage_still_states_the_claim_the_lattice_demonstrates():
    """The diagram and the sentence have to agree — the lattice is the proof of a specific claim,
    not a generic illustration."""
    t = _src()
    assert "Seven" in t or "seven" in t
    assert re.search(r"no decision touches just one", t, re.I), \
        "the claim the lattice exists to demonstrate is missing from the page"


# ── the rest state shows the whole figure ─────────────────────────────────────────────────────

def test_every_edge_is_visible_at_rest():
    """All twenty-one, not a subset.

    Two passes shipped a diagram that contradicted its own headline. The first hid every situational
    edge; the second drew a dashed hairline on the seven PERIMETER pairs only, leaving the eight
    interior situational edges at opacity:0. Either way Estate, Protection and Business Ownership
    rendered as loose dots — a reader counting connected nodes against the words "seven systems"
    found four. Nothing in CSS may zero an edge at rest again.
    """
    t = _src()
    rest = re.search(r"\.sysstage\.seeded \.net\{([^}]*)\}", t)
    assert rest, "the lattice rest state is missing"
    body = rest.group(1)
    op = re.search(r"opacity:\s*([\d.]+)", body)
    assert op and float(op.group(1)) > 0, f"situational edges are invisible at rest: {body!r}"
    # and no later rule may re-hide a subset of them
    for m in re.finditer(r"\.sysstage\.seeded \.net--[a-z]+[^{]*\{([^}]*)\}", t):
        o = re.search(r"opacity:\s*([\d.]+)", m.group(1))
        assert not o or float(o.group(1)) > 0, f"an edge class is hidden at rest: {m.group(0)[:80]}"


def test_the_two_tiers_are_still_clearly_different():
    """Complete does not mean flat. The derived structural claim needs to stay readable."""
    t = _src()
    base = re.search(r"\.sysstage\.seeded \.net\{([^}]*)\}", t).group(1)
    stru = re.search(r"\.sysstage\.seeded \.net--structural\{([^}]*)\}", t).group(1)
    bw = float(re.search(r"stroke-width:\s*([\d.]+)", base).group(1))
    sw = float(re.search(r"stroke-width:\s*([\d.]+)", stru).group(1))
    assert sw >= bw * 1.8, f"structural {sw} vs situational {bw} — the tiers are not distinguishable"
    assert "--accent-strike" in stru and "--ghost-line" in base


# ── the headline claim is derived, not asserted ───────────────────────────────────────────────

def test_every_trace_lead_matches_the_size_of_its_own_set():
    """The count moved from the headline into the demonstration, and got stronger for it.

    The section used to assert "One decision moves at least six" above the diagram — one claim, made
    before the reader had any reason to believe it. The headline now states the reader's problem, and
    each trace states its own result ("One sale. Seven systems.") at the moment the diagram proves
    it. So there are five claims to check instead of one, and each is checked against the set the
    animation actually walks. Add a trace whose lead says six while its set touches five, and this
    fails.
    """
    t = _src()
    words = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven"}
    traces = re.findall(r"set:\s*\[([\d,\s]+)\][^}]*?lead:\s*\"([^\"]+)\"", t, re.S)
    assert len(traces) == 5, f"expected five traces with leads, parsed {len(traces)}"
    for raw, lead in traces:
        n = len(set(int(x) for x in re.findall(r"\d+", raw)))
        assert words[n] in lead.lower(), (
            f"trace lead {lead!r} does not state its own size — the set touches {n} systems"
        )
        assert "system" in lead.lower()


def test_the_section_leads_with_the_readers_problem_not_the_ontology():
    """Progressive disclosure: the page stopped opening with Driftwood's vocabulary.

    "Seven systems" as a headline asks a first-time reader to learn an ontology before being given a
    reason to care. The seven systems are now what the reader DISCOVERS by using the diagram — the
    heading states the consequence they already worry about."""
    t = _src()
    h2 = re.search(r'<h2 class="sb-h">(.*?)</h2>', t, re.S)
    assert h2, "the lattice heading is missing"
    head = h2.group(1)
    assert "consequences" in head.lower()
    assert not re.search(r"seven systems", head, re.I), (
        f"the heading leads with the ontology again: {head!r}"
    )
    # and the subhead must follow the headline, not precede it — "Driftwood maps them" needs an
    # antecedent, and it ran before the sentence naming what "them" was, twice.
    assert t.index('class="sb-h"') < t.index('class="sb-lead"'), \
        "the subhead sits above the headline, so its pronoun has no antecedent"


def test_the_folio_plate_labels_are_gone():
    """"Plate I · The Constraint" named the page's own structure — something the reader had to read
    past to reach the argument. Removed along with its CSS."""
    t = _src()
    assert 'class="plate"' not in t
    for n in ("Plate I", "Plate II", "Plate III", "Plate IV"):
        assert f">{n}<" not in t, f"the {n} folio label is back"
