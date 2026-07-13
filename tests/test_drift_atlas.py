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

from drift.statemap import TILES, TERRITORIES
from drift.leakage import STATE_NAMES, STATE_ALPHA
from drift.tax import STATE_RATES
from drift.statepage import STATE_PAGE_CODES

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
