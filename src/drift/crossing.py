"""The Crossing Brief, an operating document, computed as a directional query over the graph.

Where the Comparison is analytical ("how do two environments differ?"), the Crossing Brief is
OPERATIONAL: "what must this household change because it is moving?" It is the memo an institution
hands a decision-maker before a transition, its purpose is to COORDINATE, not to educate.

It is DIRECTIONAL (origin → destination is a different brief than destination → origin) and, like
every product here, a thin query over the reasoning graph, it authors no facts and no reasoning.
It reads the two `atlas.build_state_edition` records and re-frames their diff as a transition:

    thesis                 one-sentence executive summary
    environment_changed    only the tax dimensions the move actually changes
    coordination           the destination's coordination priorities (owner · urgency · dependencies),
                           flagged where the move newly opens them
    decisions              which standing decisions the move makes stale (the changed signals)
    opportunities          which reviews the move opens
    actions                the action register, sequenced before · during · after the move
    questions              Questions Worth Asking, to open the client conversation, not close it

Every field projects from the graph (drift.reasoning primitives, now carrying `crossing_phase` and
`crossing_question`); the only crossing-specific text is the mechanics of relocating itself.
"""
from __future__ import annotations

from pathlib import Path

from . import atlas, compare
from .reasoning import PRIORITY_BY_ID, SIGNAL_BY_ID
from .site import BASE_URL
from .statemap import CURRENT_EDITION
from .statepage import state_slug


def crossing_slug(o: str, d: str) -> str:
    """Directional slug: ('IL','FL') -> 'illinois-to-florida'. Order matters, a move has a direction."""
    return f"{state_slug(o)}-to-{state_slug(d)}"


def crossing_path(o: str, d: str, edition: str = CURRENT_EDITION) -> str:
    return f"atlas/{edition}/crossing/{crossing_slug(o, d)}"


def crossing_url(o: str, d: str, edition: str = CURRENT_EDITION) -> str:
    return f"{BASE_URL}/{crossing_path(o, d, edition)}/"


def crossing_index_url(edition: str = CURRENT_EDITION) -> str:
    return f"{BASE_URL}/atlas/{edition}/crossing/"


# The relocation corridors households actually make, directional, high-tax → magnet. Each gets a
# canonical static brief + a sitemap entry; the instrument itself briefs ANY origin → destination.
FEATURED_CROSSINGS: list[tuple[str, str]] = [
    ("IL", "FL"), ("NY", "FL"), ("CA", "TX"), ("CA", "NV"), ("NJ", "FL"), ("CA", "FL"),
    ("NY", "TX"), ("MN", "FL"), ("CT", "FL"), ("MA", "NH"), ("OR", "WA"), ("IL", "TX"),
    ("MD", "FL"), ("VA", "FL"), ("NY", "NC"), ("CA", "AZ"), ("CA", "WA"), ("NJ", "PA"),
]

# Dimension → the label the operating document uses (the household's vocabulary, not the schema's).
_DIM_LABEL = {
    "cg": "Income taxes (capital gains)", "estate": "Estate & inheritance taxes",
    "stepup": "Basis step-up (marital-property regime)", "marriage": "Marriage treatment",
    "loss": "Loss treatment", "muni": "Municipal-bond interest", "qsbs": "QSBS (§1202)",
}
_URGENCY = {1: "Immediate", 2: "Near-term", 3: "Ongoing"}

# How the dominant signal change reads in the one-sentence thesis (direction: down = lower pressure).
_CHANGE_PHRASE = {
    ("estate_exposure", "down"): "materially reduces the household's state estate-tax exposure",
    ("estate_exposure", "up"): "materially raises the household's state estate-tax exposure",
    ("rate_pressure", "down"): "eases the state's drag on every realized gain",
    ("rate_pressure", "up"): "adds meaningful state drag on every realized gain",
    ("harvest_leverage", "down"): "lowers the value a harvested loss carries",
    ("harvest_leverage", "up"): "raises the value a harvested loss carries",
    ("basis_coordination", "down"): "narrows the basis step-up available at the first death",
    ("basis_coordination", "up"): "widens the basis step-up available at the first death",
    ("mobility_value", "down"): "settles the household into a destination others move toward",
    ("mobility_value", "up"): "raises the standing value of where the household is domiciled",
}

# The one during-the-move step, the mechanics of relocating, anchored to the residency priority.
_DURING_ESTABLISH = {
    "id": "establish_domicile", "title": "Establish the new domicile", "owner": "household",
    "references": "residency_planning", "crossing_phase": "during",
    "step": "Take up residence at the destination and begin severing origin-state ties, days present, "
            "the primary home, registrations, and affiliations, so the change of domicile is a fact "
            "pattern, not a mailing address.",
}
# Move-universal questions every crossing raises, appended after the graph-derived ones.
_UNIVERSAL_QUESTIONS = [
    "Which advisors, CPA, estate attorney, custodian, need updated instructions reflecting the new domicile?",
    "Should the timing of charitable gifts or large realizations shift across the move?",
]


def _dep_labels(dims: list[str]) -> str:
    return ", ".join(_DIM_LABEL.get(d, d).split(" (")[0].lower() for d in dims)


def _dominant_change(changed: list[dict]) -> dict | None:
    """The signal whose level moved most, the headline of the move. Mobility is excluded: it is a
    meta-signal about moving itself, circular in a document that already assumes the move."""
    pool = [c for c in changed if c["id"] != "mobility_value"] or changed
    return max(pool, key=lambda c: abs(c["b_score"] - c["a_score"]), default=None)


def _thesis(o_name: str, d_name: str, changed: list[dict], opened: list[dict]) -> str:
    if not changed:
        return (f"Relocating from {o_name} to {d_name} changes little in the household's tax operating "
                f"environment, the coordination priorities carry over largely unchanged.")
    dom = _dominant_change(changed)
    direction = "down" if dom["b_score"] < dom["a_score"] else "up"
    phrase = _CHANGE_PHRASE.get((dom["id"], direction), "changes the household's tax operating environment")
    domains = [p["title"].lower() for p in opened[:3]]
    shift = (f", shifting coordination toward {_join(domains)}" if domains
             else ", with the household's coordination priorities largely carrying over")
    return f"Relocating from {o_name} to {d_name} {phrase}{shift}."


def _join(items: list[str]) -> str:
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + (", and " if len(items) > 2 else " and ") + items[-1]


def build_crossing(origin: str, destination: str, edition: str = CURRENT_EDITION) -> dict:
    """The Crossing Brief query: a directional, operational re-framing of the graph diff between the
    origin and destination environments. Authors nothing, every section is projected from the two
    `atlas.build_state_edition` records and the reasoning primitives."""
    ro = atlas.build_state_edition(origin, edition)
    rd = atlas.build_state_edition(destination, edition)

    # Decision-framework deltas, directional (origin → destination).
    so = {s["id"]: s for s in ro["framework"]}
    sd = {s["id"]: s for s in rd["framework"]}
    signals = [{"id": s["id"], "title": s["title"],
                "from_level": so[s["id"]]["level"], "to_level": sd[s["id"]]["level"],
                "a_score": so[s["id"]]["score"], "b_score": sd[s["id"]]["score"],
                "from_reading": so[s["id"]]["reading"], "to_reading": sd[s["id"]]["reading"]}
               for s in ro["framework"]]
    changed = [s for s in signals if s["from_level"] != s["to_level"]]

    # Coordination priorities: what the destination opens, keeps, and closes relative to the origin.
    po = {c["id"]: c for c in ro["coordination"]}
    pd = {c["id"]: c for c in rd["coordination"]}
    opened = [pd[i] for i in pd if i not in po]
    continuing = [pd[i] for i in pd if i in po]
    closed = [po[i] for i in po if i not in pd]

    # The coordination table (destination's live priorities), flagged where the move opens them.
    def _row(p, is_new):
        return {"id": p["id"], "priority": p["title"], "reason": p["rationale"],
                "urgency": _URGENCY.get(p["priority"], "Ongoing"), "owner": p["coordinate_with"],
                "dependencies": _dep_labels(p["affected_dimensions"]), "new": is_new,
                "domain": p["domain"]}
    coordination = ([_row(p, True) for p in opened] + [_row(p, False) for p in continuing])
    coordination.sort(key=lambda r: (not r["new"], SIGNAL_ORDER.get(r["id"], 9)))

    # Standing decisions the move makes stale, the signals that changed reading (the decision category
    # is the priority each opens).
    decisions = []
    for s in changed:
        opens = SIGNAL_BY_ID[s["id"]]["opens"]
        cat = PRIORITY_BY_ID[opens[0]]["title"] if opens else s["title"]
        decisions.append({"category": cat, "signal": s["title"],
                          "from_level": s["from_level"], "to_level": s["to_level"],
                          "note": s["to_reading"]})

    # Opportunities the move opens (each newly-relevant priority) and simplifications it removes.
    opportunities = [{"opens": p["title"] + " review", "reason": f"the {p['domain'].lower()} environment changed on the move",
                      "kind": "opens", "domain": p["domain"]} for p in opened]
    opportunities += [{"opens": p["title"], "reason": "no longer triggered at the destination, one fewer thing to coordinate",
                       "kind": "closes", "domain": p["domain"]} for p in closed]

    # Action register, sequenced before · during · after, the graph's actions, phased.
    #  · before : the move-planning actions (from origin OR destination, you model the move from where
    #             domicile mattered), e.g. modelling domicile alternatives.
    #  · during : the mechanics of relocating, one step, anchored to the residency priority, present
    #             whenever the move crosses a domicile boundary that mattered on either side.
    #  · after  : setting up what the DESTINATION now makes relevant. The unwinding of what the origin
    #             required is told by "decisions to reconsider", not duplicated here.
    def _act(a):
        return {"title": a["title"], "owner": a["owner"], "step": a["step"], "references": a["references"]}
    seen, before = set(), []
    for a in ro["actions"] + rd["actions"]:
        if a.get("crossing_phase") == "before" and a["id"] not in seen:
            seen.add(a["id"]); before.append(_act(a))
    after = [_act(a) for a in rd["actions"] if a.get("crossing_phase") == "after"]
    residency_relevant = (
        any(c["id"] == "residency_planning" for c in ro["coordination"] + rd["coordination"])
        or "mobility_value" in [s["id"] for s in changed])
    during = [{k: _DURING_ESTABLISH[k] for k in ("title", "owner", "step", "references")}] if residency_relevant else []
    phases = {"before": before, "during": during, "after": after}

    # Questions Worth Asking, the graph's per-priority questions (opened first), then the universals.
    seen, questions = set(), []
    for p in opened + continuing:
        q = p.get("crossing_question")
        if q and q not in seen:
            seen.add(q); questions.append(q)
    questions += [q for q in _UNIVERSAL_QUESTIONS if q not in seen]

    env_changed = compare._environment_diffs(ro["environment"], rd["environment"])
    ia, ib = ro["impact"].get("illustrative_alpha_pct"), rd["impact"].get("illustrative_alpha_pct")

    return {
        "edition": edition, "slug": crossing_slug(origin, destination),
        "origin": {"code": origin, "name": ro["name"]},
        "destination": {"code": destination, "name": rd["name"]},
        "thesis": _thesis(ro["name"], rd["name"], changed, opened),
        "environment_changed": env_changed,
        "signals": signals, "changed_signal_ids": [s["id"] for s in changed],
        "coordination": coordination, "opened_ids": [p["id"] for p in opened],
        "closed_ids": [p["id"] for p in closed],
        "decisions": decisions, "opportunities": opportunities,
        "actions": phases, "questions": questions,
        "impact": {"origin_alpha": ia, "destination_alpha": ib},
    }


# Canonical signal order (for stable sorting of the coordination table by the priority a signal opens).
SIGNAL_ORDER = {p_id: i for i, p_id in enumerate(
    ["residency_planning", "estate_structure", "basis_titling", "harvest_coordination", "asset_location"])}
