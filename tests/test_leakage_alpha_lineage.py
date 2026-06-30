"""Performance-claim regression guards for the Tax-Leakage Diagnostic (Rule 206(4)-1 substantiation).

`drift.leakage.STATE_ALPHA` is the hardcoded, committed output of `scripts/tax_alpha.all_state_alpha`
over the 30-year proxy-spliced cache. It drives the public "+3.7–4.7%/yr Structural Alpha" claim on
`leakage.html?state=...`. If someone hand-edits a figure (a 4.7 -> 3.7 typo, or an over-statement),
nothing else in the suite catches it — these tests do.

Two guards:
  • a cheap internal-consistency check (the published headline range == the table's own min/max), and
  • a real-cache recompute that re-derives the table from the engine and asserts it still matches.

The recompute uses a tolerance: the lot-protection redistribution iterates sets, so without
PYTHONHASHSEED=0 (skipped under pytest) the rounded figures can jitter ~0.1 at a rounding boundary.
0.2 absorbs that jitter while still catching any material drift (a typo/over-statement is >= 0.3).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import pytest

from drift import leakage as L

TOL = 0.2  # %/yr — wider than seed jitter (~0.1), tighter than any material mis-statement (>= 0.3)


def test_headline_band_is_the_representative_states_range():
    """The published headline band (alpha_low/alpha_high) is the range across the four DISPLAYED
    representative jurisdictions (Federal -> IL -> NY -> CA), not the full 56-state min/max — those
    are what the banner summarizes. Pinning it here means the banner can't drift from the rows shown."""
    state = L.build_leakage()
    display_alphas = [L.STATE_ALPHA[code]["alpha"] for _label, code in L._DISPLAY]
    assert state["headline"]["alpha_low"] == pytest.approx(min(display_alphas), abs=1e-9)
    assert state["headline"]["alpha_high"] == pytest.approx(max(display_alphas), abs=1e-9)


def test_published_headline_never_overstates_the_table():
    """No-overstatement guard (Marketing Rule): the headline ceiling must not exceed the best figure
    any real jurisdiction actually computes, and the floor must not sit below the worst — i.e. the
    advertised band stays inside the substantiated per-state range."""
    state = L.build_leakage()
    alphas = [v["alpha"] for v in L.STATE_ALPHA.values()]
    assert state["headline"]["alpha_high"] <= max(alphas) + 1e-9, "headline high overstates the table"
    assert state["headline"]["alpha_low"] >= min(alphas) - 1e-9, "headline low understates below the table"


def test_display_rows_are_sourced_from_the_state_table():
    """The four visible exhibit rows must be the literal STATE_ALPHA entries (no separate copy to drift)."""
    state = L.build_leakage()
    by_label = {r["state"]: r for r in state["states"]}
    for label, code in L._DISPLAY:
        assert by_label[label]["before"] == L.STATE_ALPHA[code]["before"]
        assert by_label[label]["after"] == L.STATE_ALPHA[code]["after"]
        assert by_label[label]["alpha"] == L.STATE_ALPHA[code]["alpha"]


def test_state_alpha_matches_tax_alpha_recompute():
    """Re-derive the per-state table from scripts/tax_alpha on the committed real cache and assert it
    still matches the hardcoded STATE_ALPHA. Skips (does not fail) if only synthetic/thin data is
    available, so it never asserts the claim against a non-real path."""
    import tax_alpha as TA
    from tilt_sweep import real_universe, _hybrid
    from drift.config import Settings
    from drift.cross_section import cross_book_entries

    series = TA.slice_recent_years(real_universe(), TA.WINDOW_YEARS)
    if not series or len(series) < 8:
        pytest.skip("real proxy-spliced cache unavailable (synthetic/thin) — recompute not meaningful")
    years = max(len(v) for v in series.values()) / TA.BPY
    if years < 25:
        pytest.skip(f"cache spans only ~{years:.0f}y (<25) — not the 30y window the claim is calibrated to")

    fast = Settings.load("config/drift.yaml")
    hybrid = _hybrid(fast, 0.5)
    ef = cross_book_entries(series, fast)
    eh = cross_book_entries(series, hybrid)
    got = TA.all_state_alpha(ef, eh, years)

    assert set(got) == set(L.STATE_ALPHA), (
        f"state coverage drifted: recompute has {set(got) ^ set(L.STATE_ALPHA)} not in the other")

    drifted = []
    for st, want in L.STATE_ALPHA.items():
        g = got[st]
        for key in ("before", "after", "alpha"):
            if abs(g[key] - want[key]) > TOL:
                drifted.append(f"{st}.{key}: committed {want[key]} vs recompute {g[key]}")
    assert not drifted, "STATE_ALPHA no longer matches scripts/tax_alpha output:\n  " + "\n  ".join(drifted)
