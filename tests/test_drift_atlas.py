"""Guards for the canonical State Tax Atlas spine.

The Atlas is moving toward ONE canonical {state, edition} data model that every surface
projects from — state pages, the comparison spread, the Crossing Brief, remembered home
state, and future annual editions — with no duplicated logic (PUBLISHING_SPEC §14.3).

Today the state-code enumeration is repeated in several modules (statemap.TILES,
leakage.STATE_NAMES, tax.STATE_RATES, leakage.STATE_ALPHA, statepage.STATE_PAGE_CODES) and
mirrored again in JS (dw-context.js `STATES`). These tests LOCK those enumerations to one
another so a state added to one place but not the others fails loudly — the safety net that
lets the de-duplication proceed one module at a time without silent drift.
"""

import re
import pathlib

import pytest

from drift.statemap import (
    TILES, TERRITORIES, EDITIONS, CURRENT_EDITION,
    AS_OF_LAW, LAST_REVIEWED, _CHANGELOG, build_statemap, _state_record,
)
from drift.leakage import STATE_NAMES, STATE_ALPHA
from drift.tax import STATE_RATES
from drift.statepage import STATE_PAGE_CODES
from drift import atlas

ROOT = pathlib.Path(__file__).resolve().parents[1]

# The canonical enumeration: the real jurisdictions (50 states + DC), i.e. the two-letter
# TILES codes that are not territories. Pseudo-keys the impact tables carry for the workspace
# ("NYC", the federal-only "—") are not part of the geographic atlas and are excluded here.
CANON = {c for c in TILES if c.isalpha() and len(c) == 2} - set(TERRITORIES)


def _real(codes):
    return {c for c in codes if isinstance(c, str) and c.isalpha() and len(c) == 2} - set(TERRITORIES)


def test_the_canonical_enumeration_is_fifty_states_plus_dc():
    assert len(CANON) == 51, f"expected 50 states + DC, got {len(CANON)}"
    assert "DC" in CANON and "CA" in CANON and "TX" in CANON


def test_every_python_state_table_shares_the_one_canonical_code_set():
    # Each per-state table must cover exactly the canonical jurisdictions (no more, no fewer),
    # so no single source can drift ahead of the others.
    for name, codes in [
        ("leakage.STATE_NAMES", STATE_NAMES),
        ("tax.STATE_RATES", STATE_RATES),
        ("leakage.STATE_ALPHA", STATE_ALPHA),
    ]:
        got = _real(codes)
        assert got == CANON, (
            f"{name} real-state codes diverge from the canonical set: "
            f"missing={CANON - got}, extra={got - CANON}"
        )


def test_state_pages_cover_exactly_the_canonical_jurisdictions():
    got = _real(STATE_PAGE_CODES)
    assert got == CANON, f"state pages diverge: missing={CANON - got}, extra={got - CANON}"


def test_the_household_context_js_state_list_matches_the_python_canon():
    # dw-context.js carries its own `STATES` array for the household bar; its code set must
    # track the Python canon so the two never disagree about which jurisdictions exist.
    js = (ROOT / "src" / "drift" / "web" / "dw-context.js").read_text()
    m = re.search(r"var STATES = \[(.*?)\];", js, re.S)
    assert m, "could not find the STATES array in dw-context.js"
    js_codes = _real(re.findall(r'\["([A-Z]{2})"', m.group(1)))
    assert js_codes == CANON, (
        f"dw-context.js STATES diverges from the canon: "
        f"missing={CANON - js_codes}, extra={js_codes - CANON}"
    )


# ── Edition scoping ─────────────────────────────────────────────────────────────────────────────
# The Atlas is versioned by tax-year edition; each carries its own provenance so /atlas/2026/ stays
# citable forever. These guard the backward-compatible scaffold: the flat module aliases must equal
# the current edition, and the default build must reproduce today's output.

def test_the_flat_provenance_aliases_track_the_current_edition():
    ed = EDITIONS[CURRENT_EDITION]
    assert AS_OF_LAW == ed["as_of_law"]
    assert LAST_REVIEWED == ed["last_reviewed"]
    assert _CHANGELOG == ed["changelog"]


def test_default_build_uses_the_current_edition_and_stamps_it():
    default = build_statemap()
    explicit = build_statemap(CURRENT_EDITION)
    assert default["edition"] == CURRENT_EDITION
    assert default["header"]["edition"] == CURRENT_EDITION
    # Provenance carried from the edition registry, unchanged from the flat aliases.
    assert default["header"]["as_of_law"] == AS_OF_LAW
    assert default["header"]["last_reviewed"] == LAST_REVIEWED
    assert default["header"]["changelog"] == _CHANGELOG
    # Default and explicit-current agree on everything except the fresh build timestamp.
    for d in (default, explicit):
        d["header"] = {k: v for k, v in d["header"].items() if k != "generated"}
    assert default == explicit


def test_unknown_edition_is_a_hard_error():
    with pytest.raises(KeyError):
        build_statemap("1999")


# ── The canonical spine (atlas.py) ────────────────────────────────────────────────────────────────
# The {state, edition} record projects the live tax facts as its `environment` layer and declares
# the four downstream reasoning-chain layers as empty-but-typed placeholders. These guard that the
# spine adds no facts of its own and that its shape is stable for consumers.

def test_environment_layer_is_exactly_the_live_state_record():
    # The spine must not re-author facts: its environment layer IS statemap's record, verbatim.
    for code in ("IL", "CA", "TX", "FL", "WY"):
        rec = atlas.build_state_edition(code)
        assert rec["environment"] == _state_record(code)
        assert rec["code"] == code and rec["edition"] == CURRENT_EDITION


def test_the_reasoning_chain_layers_are_present_and_empty():
    rec = atlas.build_state_edition("IL")
    assert atlas.CHAIN == ("environment", "impact", "considerations", "framework", "actions")
    # Downstream layers are declared but unpopulated (filled later, under content authority).
    assert rec["impact"] is None
    assert rec["considerations"] == []
    assert rec["framework"] == {"signals": {}}
    assert rec["actions"] == []


def test_build_edition_covers_every_jurisdiction_with_provenance():
    ed = atlas.build_edition()
    assert ed["edition"] == CURRENT_EDITION
    assert ed["as_of_law"] == AS_OF_LAW and ed["changelog"] == _CHANGELOG
    # Every canonical jurisdiction (and the territories strip) is present.
    assert CANON <= set(ed["states"])
    assert set(ed["states"]) == set(TILES)


def test_spine_rejects_an_unknown_edition():
    with pytest.raises(KeyError):
        atlas.build_state_edition("CA", "1999")
