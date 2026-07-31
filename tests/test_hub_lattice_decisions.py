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


def test_the_rest_state_is_entirely_graphite():
    """The diagram at rest carries no accent at all — the accent belongs to the demonstration.

    This guard used to REQUIRE the accent in the rest state, which is how the lattice ended up with
    six blue edges painting a four-node shape across a seven-node figure. Reserving the colour for a
    traced decision does two things at once: the resting web reads as one object, and a trace reads
    as something happening rather than as a recolouring of what was already there.
    """
    t = _src()
    rules = re.findall(r"\.sysstage\.seeded [^{]*\{[^}]*\}", t)
    assert rules, "the seeded rest state is missing"
    for rule in rules:
        assert "--accent-strike" not in rule, f"the accent is back in the rest state: {rule[:90]}"
    joined = "".join(rules)
    assert "--ghost-line" in joined and "--dim" in joined, "the rest state lost its graphite tokens"
    hexes = set(re.findall(r"#[0-9a-fA-F]{6}", joined))
    assert not hexes, f"the rest state hardcodes colour instead of using tokens: {hexes}"


def test_the_accent_is_still_used_by_the_traces():
    """Reserved, not removed. A traced decision is where the one colour is spent."""
    t = _src()
    trace = re.search(r"\.trace\{([^}]*)\}", t)
    assert trace and "--accent-strike" in trace.group(1), \
        "the trace overlay lost the accent, so a decision no longer reads as an event"


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
    # Weight, not colour. Painting the structural six in the accent drew a lopsided quadrilateral
    # over a regular heptagon and that shape became the figure — see the rest-state comment in
    # hub.html. Both tiers are graphite tokens; neither may reach for the accent.
    for block, name in ((base, "situational"), (stru, "structural")):
        assert "--accent-strike" not in block, f"the {name} tier is painted in the accent at rest"
        assert "var(--" in block, f"the {name} tier hardcodes a colour instead of using a token"


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
    """Progressive disclosure: the page does not open with Driftwood's vocabulary.

    "Seven systems" as a headline asks a first-time reader to learn an ontology before being given a
    reason to care. The seven systems are what the reader DISCOVERS by using the diagram.

    This guard briefly required the heading to POINT AT the diagram instead ("trace", "watch",
    "move"). That was a mistake worth naming: a rule requiring a headline to behave like a control
    label reliably produces control-label prose in the headline slot — two stacked imperatives in
    product-tour register, vague where the rest of the page is specific. The affordance belongs to
    the picker's own label (see test_the_decision_picker_carries_a_visible_control_label), which
    frees this slot to make a claim. The constraint here is back to the simple one.
    """
    t = _src()
    h2 = re.search(r'<h2 class="sb-h">(.*?)</h2>', t, re.S)
    assert h2, "the lattice section lost its heading"
    head = h2.group(1).strip()
    assert not re.search(r"seven systems", head, re.I), (
        f"the heading leads with the ontology again: {head!r}"
    )
    # It must not re-close the hero. These are the headline's own words.
    for echo in ("consequences", "expensive", "leak what you keep", "uncoordinated"):
        assert echo not in head.lower(), (
            f"the lattice heading recycles the hero headline ({echo!r}): {head!r}"
        )
    # One line. The subhead went with the closer and may not return unnoticed.
    assert 'class="sb-lead"' not in t, "a second line is back under the lattice heading"


def test_the_lattice_headings_count_is_derived_from_the_published_traces():
    """The heading claims a quantity, so the quantity has to come from the traces, not from taste.

    The five published traces touch 7, 7, 6, 6 and 6 systems, which makes "at least six" the
    strongest true form — "four" would have understated it and "seven" would have overstated three
    of the five. Edit a trace set without following the sentence and this fails.
    """
    t = _src()
    words = {4: "four", 5: "five", 6: "six", 7: "seven"}
    sizes = [len(set(int(x) for x in re.findall(r"\d+", raw)))
             for raw in re.findall(r"set:\s*\[([\d,\s]+)\]", t)]
    assert sizes, "no traces parsed"
    head = re.search(r'<h2 class="sb-h">(.*?)</h2>', t, re.S).group(1).lower()
    claimed = [n for n, w in words.items() if w in head]
    assert claimed, f"the heading states no quantity to check: {head!r}"
    assert len(claimed) == 1, f"the heading states more than one quantity: {claimed}"
    n = claimed[0]
    assert n == min(sizes), (
        f"the heading claims {words[n]} systems but the smallest published trace touches "
        f"{min(sizes)} — the claim and the demonstration disagree"
    )
    assert "at least" in head or "or more" in head, (
        "a bare number reads as exact while the traces range "
        f"{min(sizes)}-{max(sizes)}; qualify it"
    )


def test_the_decision_picker_carries_a_visible_control_label():
    """The affordance lives here, not in the heading.

    The lattice is the only interactive thing on the page, and for a long time nothing visible said
    so — the instruction sat in the SVG's aria-label, so sighted readers got none. The fix is a
    control label on the picker, in the page's small-caps utility register, which reads as operable
    without a sentence selling the interaction.

    It must also BE the group's accessible name, so what a screen reader announces and what the eye
    sees are the same string.
    """
    t = _src()
    lab = re.search(r'<p class="trig-lab" id="([^"]+)">([^<]+)</p>', t)
    assert lab, "the decision picker has no visible control label"
    lab_id, text = lab.group(1), lab.group(2).strip()
    assert text, "the control label is empty"
    assert len(text.split()) <= 4, f"a control label, not a sentence: {text!r}"
    assert not text.endswith("."), f"a control label takes no full stop: {text!r}"
    trig = re.search(r'<div class="trig"[^>]*>', t).group(0)
    assert f'aria-labelledby="{lab_id}"' in trig, (
        "the picker does not use its visible label as its accessible name"
    )
    assert "aria-label=" not in trig, (
        "the picker carries a separate aria-label, so the announced name and the visible label can "
        "drift apart"
    )


def test_the_folio_plate_labels_are_gone():
    """"Plate I · The Constraint" named the page's own structure — something the reader had to read
    past to reach the argument. Removed along with its CSS."""
    t = _src()
    assert 'class="plate"' not in t
    for n in ("Plate I", "Plate II", "Plate III", "Plate IV"):
        assert f">{n}<" not in t, f"the {n} folio label is back"


# ── the spokes: coordination is drawn, not asserted (2026-08-01) ──────────────────────────────

def test_seven_spokes_run_from_the_centre_to_every_system():
    """The plate's whole argument is that everything routes through coordination, and until now the
    centre was a floating word with no lines touching it — the one claim the diagram did NOT draw.
    Seven spokes, one per system, indexed so a renamed or reordered system cannot silently orphan
    one."""
    t = _src()
    spokes = re.findall(r'<line class="spoke" data-i="(\d)" x1="(\d+)" y1="(\d+)" '
                        r'x2="(\d+)" y2="(\d+)"></line>', t)
    assert len(spokes) == 7, f"{len(spokes)} spokes, expected one per system"
    assert [s[0] for s in spokes] == list("0123456"), "spokes are not indexed to the seven systems"
    # every spoke starts at the centre...
    for s in spokes:
        assert (s[1], s[2]) == ("320", "240"), f"spoke {s[0]} does not start at the hub"
    # ...and lands exactly on its node's dot, so no spoke points into empty space
    dots = {i: (cx, cy) for i, cx, cy in re.findall(
        r'<g class="node" data-i="(\d)"[^>]*>\s*<circle class="hit"[^>]*></circle>'
        r'<circle class="dot" cx="(\d+)" cy="(\d+)"', t)}
    assert len(dots) == 7, f"could not read the seven node positions: {dots}"
    for s in spokes:
        assert dots[s[0]] == (s[3], s[4]), f"spoke {s[0]} misses its node"


def test_the_spokes_are_drawn_before_the_hub_mask_that_clips_them():
    """The paper rectangle behind COORDINATION is what keeps the label legible where seven lines
    converge. SVG has no z-index: if the spokes were emitted after the mask they would cross the
    word. This is a paint-order dependency, so it is pinned rather than left to a future reorder."""
    t = _src()
    assert t.index('class="spoke"') < t.index('class="hub-bg"') < t.index('<text class="hub"')


def test_the_spokes_are_the_only_bold_figure_at_rest():
    """Two emphasised figures cannot share one diagram — that is the failure this lattice already
    shipped three times, most recently as six accented chords painting a lopsided quadrilateral over
    a regular heptagon. The spokes now carry the emphasis, so the rim must stay quieter than they
    are: heavier than the spokes, or equal to them, and the eye has two drawings to reconcile."""
    t = _src()
    def rule(sel):
        return re.search(r"\.sysstage\.seeded %s\{([^}]*)\}" % re.escape(sel), t).group(1)
    def num(block, prop):
        return float(re.search(prop + r":\s*([\d.]+)", block).group(1))
    spoke = rule(".spoke")
    for sel in (".net", ".net--structural"):
        rim = rule(sel)
        assert num(rim, "stroke-width") < num(spoke, "stroke-width"), \
            f"{sel} is as heavy as the spokes at rest"
        assert num(rim, "opacity") < num(spoke, "opacity"), \
            f"{sel} is as prominent as the spokes at rest"


def test_the_centre_is_lit_at_rest_and_never_goes_out():
    """"The operating system is always running." A hub that rests at --muted and reaches --ink only
    during a trace tells a non-interacting visitor the opposite: that the centre is the faintest
    thing in a diagram built to say the centre is where everything meets."""
    t = _src()
    hub = re.search(r"\n  \.hub\{([^}]*)\}", t).group(1)
    assert "fill:var(--ink)" in hub, f"the hub does not rest in ink: {hub}"
    assert not re.search(r"\.hub\.on\{[^}]*fill", t), \
        "a .hub.on fill rule is back — the centre's lit state must not be conditional"


def test_the_spokes_follow_the_interaction():
    """A spoke layer that never changes is wallpaper. Hovering a system lights its own route to the
    centre; a traced decision lights the route of every system in its set."""
    t = _src()
    assert "function paintSpokes(" in t
    assert re.search(r"paintSpokes\(function\(j\)\{ return j === i; \}\)", t), \
        "a hovered system does not light its own spoke"
    assert "paintSpokes(inSet)" in t, "a traced decision does not light its systems' spokes"
    assert 'spokes.forEach(function(sp){ sp.classList.remove("lit","dim"); });' in t, \
        "clearing the plate leaves spokes stuck lit or dimmed"


def test_the_caption_decodes_the_spokes_it_now_describes():
    """The caption used to read "the heavier lines are the ones that move in all of them", which
    decoded the structural rim tier. The heavy lines are the spokes now, so the sentence had to move
    with the encoding or it would be actively describing the wrong marks."""
    t = _src()
    body = re.search(r'<p class="mrest"[^>]*>(.*?)</p>', t, re.S).group(1)
    assert "heavier" in body.lower()
    assert "centre" in body.lower() or "center" in body.lower(), \
        f"the caption still points at the rim rather than the spokes: {body!r}"
    assert "move in all of them" not in body, "the caption still decodes the retired encoding"


def test_the_survey_rail_carries_one_finding_not_three():
    """Two of the three restated the paragraph above it.

    "Nothing falls through / every open matter has a named owner" and "One record / every adviser
    works from the same one" are the paragraph's own claims in fewer words — the seams, and the
    single party responsible for them. Only "Open until finished / not until the meeting ends" says
    something the paragraph did not: how long a decision stays open, which is a promise a prospect
    has not been made before.
    """
    t = _src()
    rail = re.search(r'<div class="rail[^"]*">(.*?)</div>\s*<div class="sysband"', t, re.S)
    assert rail, "the survey rail is gone or no longer sits above the lattice"
    body = rail.group(1)
    findings = re.findall(r'<span class="mono rk">([^<]+)</span>', body)
    assert findings == ["Open until finished"], (
        f"the rail is back to restating the paragraph: {findings}"
    )
    # A lone cell in the three-column grid would read as two things that failed to load.
    assert 'class="rail rail--one"' in t, "the single-finding rail keeps the three-column grid"


def test_the_booking_cta_is_never_decorated_with_household_parameters():
    """The one URL a visitor copies, shares, or hands to Calendly as a referrer.

    coordination-review.html reads none of these params — there is not a single qp.get() on it — so
    ?state=IL&bracket=37&port=250000 was noise that carried a household's tax bracket and portfolio
    size into analytics, referrer headers, and anyone's clipboard. The page loads dw-context.js like
    every other, so if it ever needs the household it reads dwTaxContext.get() in the browser.
    """
    ctx = (HUB.with_name("dw-context.js")).read_text(encoding="utf-8")
    consumers = re.search(r"var CONSUMERS = \[(.*?)\n  \];", ctx, re.S)
    assert consumers, "the CONSUMERS list moved"
    decorated = re.findall(r'\{\s*prefix:\s*"([^"]+)"', consumers.group(1))
    assert "coordination-review.html" not in decorated, (
        "the booking CTA is decorated with household parameters again"
    )
    booking = (HUB.with_name("coordination-review.html")).read_text(encoding="utf-8")
    assert "qp.get(" not in booking, (
        "the booking page now reads URL params — if that is intended, the privacy tradeoff above "
        "needs revisiting deliberately"
    )
