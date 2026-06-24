"""Guards for the SEC-grade hypothetical-performance framing.

The performance exhibits (the Model Portfolio ledger and the long-history tearsheet)
present *backtested* results. The Marketing Rule requires those be clearly labeled as
hypothetical, with prominent disclosure near the numbers. These tests fail loudly if the
disclosure language or the Model-Portfolio framing is ever dropped, or if the old
"live track record" framing creeps back in.
"""

from drift.exhibit import (
    LEDGER_TEMPLATE,
    TEARSHEET_TEMPLATE,
    HUB_TEMPLATE,
    THESIS_TEMPLATE,
    TEMPLATE,  # index.html / dashboard
)

# The three pillars the Marketing Rule wants stated for hypothetical performance.
_REQUIRED_PHRASES = [
    "retroactive application",          # these are a model applied after the fact
    "no client capital was invested",   # not actual client capital
    "does not guarantee future results",  # past performance caveat
]


def _read(p):
    return p.read_text()


def test_ledger_carries_hypothetical_disclosure_near_the_numbers():
    t = _read(LEDGER_TEMPLATE)
    assert 'class="disclaimer"' in t                      # the styled banner exists
    for phrase in _REQUIRED_PHRASES:
        assert phrase in t, f"ledger disclosure missing: {phrase!r}"
    # The banner is injected at the top of the body, above the metrics block.
    assert t.index("disclaimerHTML") < t.index('<div class="metrics">${stats}</div>')


def test_ledger_is_framed_as_a_model_portfolio_not_a_live_track():
    t = _read(LEDGER_TEMPLATE)
    assert "Model Portfolio" in t
    assert "HYPOTHETICAL" in t
    # The abandoned "live / seeded 2-day" framing must be gone.
    assert "seed / live divider" not in t
    assert "live forward ledger" not in t


def test_ledger_renders_alpha_beta_attribution_panel():
    t = _read(LEDGER_TEMPLATE)
    assert "Return attribution" in t
    assert "attribHTML" in t
    assert "s.attribution" in t


def test_tearsheet_carries_hypothetical_disclosure():
    t = _read(TEARSHEET_TEMPLATE)
    assert 'class="disclaimer"' in t
    assert "Hypothetical" in t
    for phrase in _REQUIRED_PHRASES:
        assert phrase in t, f"tearsheet disclosure missing: {phrase!r}"


def test_cross_pages_drop_the_live_track_framing():
    # Landing/hub/thesis should point at the Model Portfolio, not a "live forward ledger".
    for tmpl in (HUB_TEMPLATE, THESIS_TEMPLATE, TEMPLATE):
        t = _read(tmpl)
        assert "live forward ledger" not in t, f"{tmpl.name} still says 'live forward ledger'"
