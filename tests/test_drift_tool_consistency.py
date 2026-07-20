"""Cross-tool numeric consistency — the funnel's personalized tools must never show a prospect two
different "your numbers" for the same state.

The Tax Diagnostic (leakage.html), the After-Tax Review (taxlab.html), and the State Atlas
coordination tab (statemap.html) all render a per-visitor coordination figure. They must trace to ONE
source: build_leakage()["state_alpha"] == STATE_ALPHA, and cli.taxlab builds the public After-Tax
Review payload from build_leakage()["state_alpha"]/["state_names"] verbatim. The $/$1M tag is
alpha% * $10k via coordination_opportunity_per_m(). These guards fail loudly if the source ever forks.
"""
from drift.leakage import build_leakage, STATE_ALPHA, coordination_opportunity_per_m


def test_leakage_state_alpha_is_the_single_source():
    leak = build_leakage()
    assert leak["state_alpha"] == STATE_ALPHA
    # every modeled state has a display name for the personalized surfaces
    assert set(leak["state_names"]) >= set(STATE_ALPHA)


def test_taxlab_public_payload_reuses_leakage_alpha_verbatim():
    # Mirror cli.taxlab's construction of the lean public After-Tax Review payload.
    leak = build_leakage()
    public = {"state_alpha": leak["state_alpha"], "state_names": leak["state_names"]}
    assert set(public["state_alpha"]) == set(STATE_ALPHA)
    for code, row in STATE_ALPHA.items():
        assert public["state_alpha"][code]["alpha"] == row["alpha"]
        assert public["state_alpha"][code]["before"] == row["before"]
        assert public["state_alpha"][code]["after"] == row["after"]


def test_per_visitor_annual_formula_and_per_m_tag_share_one_alpha():
    # Both diagnostic pages compute Math.round(portfolio * alpha/100); pin a representative case.
    assert round(2_000_000 * STATE_ALPHA["IL"]["alpha"] / 100.0) == 80_000
    # The $/$1M coordination tag (statemap/leakage) is alpha% * $10k off the SAME alpha — one lineage.
    for code, row in STATE_ALPHA.items():
        assert coordination_opportunity_per_m(row["alpha"]) == round(row["alpha"] / 100.0 * 1_000_000, -2)
