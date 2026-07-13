"""The Household Record — the operating file for one household, an INDEX over the graph's artifacts.

The other products render the reasoning; the Household Record BINDS it to a household and answers one
question: *if someone needed to understand this family's financial operating system, where would they
begin?* Everything flows from that.

Its governing design principle is **reference, not duplicate**. The Record is the institutional index
and the permanent context; the underlying artifacts stay authoritative in their own right:

    the tax environment in force        → the state's Atlas page
    a move under consideration          → the Crossing Brief (and the Comparison)
    the coordination priorities         → the reasoning graph (Atlas)
    the standing decisions              → the Decision Register
    the opportunities open              → the Opportunity Register
    the annual review                   → the Annual Wealth Operating Review

So this module authors no reasoning: it composes a household's identity + states with the graph
records and hands back the references. A household is illustrative sample data (no real client data).
"""
from __future__ import annotations

from . import atlas, compare, crossing
from .site import BASE_URL
from .statemap import CURRENT_EDITION

# Illustrative sample households — no real client data. "The Harris Family" is the same household the
# Annual Wealth Operating Review (awor.html) is prepared for, so the Record indexes a real artifact.
SAMPLE_HOUSEHOLDS = [
    {"id": "harris", "name": "The Harris Family", "current": "IL", "potential": "FL", "as_of": "2026",
     "sketch": "A two-generation Illinois household weighing a move to Florida — the estate cliff is the "
               "pressure, the domicile question is live.", "annual_review": "awor.html"},
    {"id": "bennett", "name": "The Bennett Family", "current": "TX", "potential": None, "as_of": "2026",
     "sketch": "A settled Texas household — no state income or estate tax; the operating file is about "
               "titling and asset location, not relocation.", "annual_review": None},
]
HOUSEHOLD_BY_ID = {h["id"]: h for h in SAMPLE_HOUSEHOLDS}

_ROOT = f"{BASE_URL}/"
# The standing governing documents (the Record family) — authored elsewhere, referenced here.
_GOVERNING_DOCS = [
    ("Household Constitution", "constitution.html", "how the family decides"),
    ("Capital Allocation Policy", "capital-allocation.html", "how capital is deployed"),
    ("Wealth Operating Manual", "manual.html", "how the system runs"),
]


def build_household_record(hh: dict, edition: str = CURRENT_EDITION) -> dict:
    """Compose one household's operating file: its identity + states bound to the graph records, and
    the references to every authoritative artifact. Authors no reasoning — it indexes it."""
    cur = atlas.build_state_edition(hh["current"], edition)
    pot = atlas.build_state_edition(hh["potential"], edition) if hh.get("potential") else None
    xing = crossing.build_crossing(hh["current"], hh["potential"], edition) if pot else None

    # Standing decisions: the coordination priorities in force in the current environment, read as the
    # decisions the household has settled. Summarised here; the Decision Register stays authoritative.
    standing = [{"id": c["id"], "domain": c["domain"], "title": c["title"],
                 "held": c["rationale"], "owner": c["coordinate_with"]} for c in cur["coordination"]]

    refs = {
        "atlas_current": {"label": f"{cur['name']} — the tax environment in force", "url": _atlas_url(hh["current"], edition)},
        "decision_register": {"label": "Decision Register — the standing decisions in full", "url": f"{_ROOT}decision-register.html"},
        "opportunity_register": {"label": "Opportunity Register — the open opportunities in full", "url": f"{_ROOT}opportunity-register.html"},
        "governing": [{"label": lbl, "sub": sub, "url": f"{_ROOT}{href}"} for lbl, href, sub in _GOVERNING_DOCS],
    }
    if pot:
        refs["atlas_potential"] = {"label": f"{pot['name']} — the environment under consideration", "url": _atlas_url(hh["potential"], edition)}
        refs["comparison"] = {"label": f"{cur['name']} vs {pot['name']} — weighed side by side", "url": compare.compare_url(hh["current"], hh["potential"], edition)}
        refs["crossing"] = {"label": f"Crossing Brief — {cur['name']} → {pot['name']}", "url": crossing.crossing_url(hh["current"], hh["potential"], edition)}
    if hh.get("annual_review"):
        refs["annual_review"] = {"label": "Annual Wealth Operating Review — the latest", "url": f"{_ROOT}{hh['annual_review']}"}

    return {
        "id": hh["id"], "edition": edition, "name": hh["name"], "as_of": hh["as_of"],
        "sketch": hh.get("sketch", ""),
        "current": {"code": hh["current"], "name": cur["name"]},
        "potential": ({"code": hh["potential"], "name": pot["name"]} if pot else None),
        "coordination": cur["coordination"],       # summary; referenced to the Atlas
        "standing_decisions": standing,
        "crossing": ({"thesis": xing["thesis"], "changed": len(xing["changed_signal_ids"]),
                      "opened": len(xing["opened_ids"]), "closed": len(xing["closed_ids"])} if xing else None),
        "opportunities": (xing["opportunities"] if xing else []),
        "impact": cur["impact"],
        "references": refs,
    }


def _atlas_url(code: str, edition: str) -> str:
    from .statepage import atlas_url
    return atlas_url(code, edition)


def household_path(hid: str, edition: str = CURRENT_EDITION) -> str:
    return f"atlas/{edition}/household/{hid}"


def household_url(hid: str, edition: str = CURRENT_EDITION) -> str:
    return f"{BASE_URL}/{household_path(hid, edition)}/"


def household_index_url(edition: str = CURRENT_EDITION) -> str:
    return f"{BASE_URL}/atlas/{edition}/household/"
