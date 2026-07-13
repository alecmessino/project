"""The canonical {state, edition} spine for the State Tax Atlas.

One record per jurisdiction per edition; every Atlas surface projects from it — state pages, the
comparison spread, the Crossing Brief, remembered home state, and future annual editions — so no
fact is authored twice (PUBLISHING_SPEC §14.3 / §15).

The record models the reasoning chain of §14.3 as five layers:

    environment    → the settled tax facts, per dimension   (LIVE today, from statemap)
    impact         → household-specific dollar impact        (needs the household profile)
    considerations → what a household should weigh           (planning content)
    framework      → ranked decision signals                 (drives the comparison spread)
    actions        → the sequenced execution register        (the Crossing Brief)

Only `environment` is populated today; the other four are declared as empty-but-typed structures
so every consumer can rely on the record's shape while the layers are filled in — the planning
content under the RIA principal's authority — one reviewable step at a time. This module adds no
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

# The reasoning-chain layer keys, in order. Consumers walk these; renderers render them in order.
CHAIN = ("environment", "impact", "considerations", "framework", "actions")


def _empty_downstream_layers() -> dict:
    """The four not-yet-populated reasoning-chain layers, as empty-but-typed structures so every
    consumer can rely on the shape before the layers are filled (under content authority)."""
    return {
        "impact": None,                # {inputs, model_ref, ...} — household-specific dollar impact
        "considerations": [],          # [{dimension, trigger, note, applies_when}] — planning
        "framework": {"signals": {}},  # {signals: {name: score}} — ranked decision signals
        "actions": [],                 # [{step, owner, dimension, decision_ref}] — action register
    }


def build_state_edition(code: str, edition: str = CURRENT_EDITION) -> dict:
    """One jurisdiction's canonical record for one edition. `environment` is the live tax facts
    (``statemap._state_record``); the downstream layers are present but empty for now."""
    if edition not in EDITIONS:
        raise KeyError(edition)
    rec = {
        "code": code,
        "edition": edition,
        "name": NAMES.get(code, code),
        "environment": _state_record(code),
    }
    rec.update(_empty_downstream_layers())
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
