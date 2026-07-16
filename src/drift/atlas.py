"""The canonical {state, edition} spine for the State Tax Atlas.

One record per jurisdiction per edition; every Atlas surface projects from it, state pages, the
comparison spread, the Crossing Brief, remembered home state, and future annual editions, so no
fact is authored twice (PUBLISHING_SPEC §14.3 / §15).

The record models the reasoning chain of §14.3 as five layers:

    environment    → the settled tax facts, per dimension   (LIVE today, from statemap)
    impact         → household-specific dollar impact        (needs the household profile)
    considerations → what a household should weigh           (planning content)
    framework      → ranked decision signals                 (drives the comparison spread)
    actions        → the sequenced execution register        (the Crossing Brief)

Only `environment` is populated today; the other four are declared as empty-but-typed structures
so every consumer can rely on the record's shape while the layers are filled in, the planning
content under the RIA principal's authority, one reviewable step at a time. This module adds no
facts of its own: it composes what `statemap` already owns.
"""
from __future__ import annotations

from .statemap import (
    EDITIONS,
    CURRENT_EDITION,
    TILES,
    TERRITORIES,
    NAMES,
    _state_record,
)
from . import reasoning

# The reasoning-chain layer keys, in order, the Decision Framework is the centrepiece (§16).
CHAIN = ("environment", "impact", "framework", "coordination", "actions")


def build_state_edition(code: str, edition: str = CURRENT_EDITION) -> dict:
    """One jurisdiction's canonical record for one edition: the environment (live tax facts) plus the
    four reasoning layers instantiated from it as composable primitives (drift.reasoning). Every
    downstream entry references a primitive by id, so pages, comparisons, briefs, and registers all
    render the same reasoning."""
    if edition not in EDITIONS:
        raise KeyError(edition)
    env = _state_record(code)
    rec = {
        "code": code,
        "edition": edition,
        "name": NAMES.get(code, code),
        "environment": env,
    }
    rec.update(reasoning.build_reasoning(code, env))  # impact, framework, considerations, actions
    return rec


def build_edition(edition: str = CURRENT_EDITION) -> dict:
    """The whole Atlas for one edition: provenance + a canonical record per jurisdiction. This is
    the single spine every surface projects from; defaults to the current edition."""
    ed = EDITIONS[edition]
    codes = list(TILES)
    return {
        "edition": edition,
        "as_of_law": ed["as_of_law"],
        "last_reviewed": ed["last_reviewed"],
        "changelog": ed["changelog"],
        "territories": sorted(TERRITORIES),
        "states": {c: build_state_edition(c, edition) for c in codes},
    }
