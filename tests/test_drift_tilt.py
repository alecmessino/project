"""Strategic forward tilt: long-only, fully invested, overweight favored segments."""

from drift.config import CrossSectionSettings
from drift.cross_section import _cheapness_dial, _combined_tilt, _tilt_for, rank_weights


def _cs(**kw):
    base = dict(quantile=0.5, long_short=False, min_score=-99,
                trend_throttle=False, weighting="inv_vol")
    base.update(kw)
    return CrossSectionSettings(**base)


def test_tilt_map_is_product_of_segment_factors():
    cs = _cs(tilt_region={"EM": 1.5}, tilt_size={"small": 1.2}, tilt_style={"value": 1.3})
    tilt = _tilt_for(cs)
    # AVEE is EM / small / value -> 1.5 * 1.2 * 1.3; IVV is US / large / blend -> 1.0.
    assert abs(tilt["AVEE"] - 1.5 * 1.2 * 1.3) < 1e-9
    assert abs(tilt["IVV"] - 1.0) < 1e-9


def test_no_tilt_configured_returns_none():
    assert _tilt_for(_cs()) is None


def test_tilt_keeps_book_fully_invested_and_overweights_favored():
    # quantile 1.0 holds the whole (positive) top so the per-name cap doesn't bind —
    # isolating the tilt's redistribution. (In the live 18-name book the top half is
    # ~9 names, so the 0.50 cap likewise never binds and gross stays ~1.0.)
    vols = {"AVEE": 0.2, "IVV": 0.2, "IWO": 0.2, "IVW": 0.2}
    scores = {"AVEE": 2.0, "IVV": 1.5, "IWO": 1.0, "IVW": 0.5}
    cs = _cs(quantile=1.0, max_weight=1.0,
             tilt_region={"US": 1.0, "DEV": 1.3, "EM": 1.55},
             tilt_size={"small": 1.3}, tilt_style={"value": 1.3, "growth": 0.8})

    plain = rank_weights(scores, vols, _cs(quantile=1.0, max_weight=1.0))   # no tilt
    tilted = rank_weights(scores, vols, cs, tilt=_tilt_for(cs))

    # Still fully invested (gross ~ 1.0), still long-only (no negatives).
    assert abs(sum(tilted.values()) - 1.0) < 1e-6
    assert all(w >= 0 for w in tilted.values())
    # EM small value (AVEE) is overweighted vs the untilted book; US large growth (IVW)
    # is underweighted — the forward tilt redistributes, it does not add cash.
    assert tilted["AVEE"] > plain["AVEE"]
    assert tilted["IVW"] < plain["IVW"]


def test_cheapness_dial_leans_into_laggards_and_fades_leaders():
    # Two names: A compounded up over the window (multi-year leader), B lagged.
    cs = _cs(tilt_dynamic=True, tilt_reversion_bars=50,
             tilt_reversion_strength=0.5, tilt_dial_cap=1.8)
    A = [100.0 * (1.02 ** k) for k in range(60)]   # strong long-run leader
    B = [100.0 * (0.99 ** k) for k in range(60)]   # long-run laggard (cheap proxy)
    C = [100.0 for _ in range(60)]                  # flat (mid)
    dial = _cheapness_dial({"A": A, "B": B, "C": C}, cs)
    assert dial["B"] > dial["C"] > dial["A"]        # cheap > neutral > rich
    assert dial["A"] < 1.0 < dial["B"]              # straddle market weight


def test_dynamic_off_returns_plain_static_anchor():
    cs = _cs(tilt_region={"EM": 1.5}, tilt_dynamic=False)
    closes = {"AVEE": [1.0, 2.0, 3.0]}
    assert _combined_tilt(closes, cs) == _tilt_for(cs)


def test_combined_tilt_is_anchor_times_dial():
    cs = _cs(tilt_region={"US": 1.0, "EM": 1.5}, tilt_dynamic=True,
             tilt_reversion_bars=50, tilt_reversion_strength=0.5)
    # IVV (US) is a long-run leader; AVEE (EM) lagged -> AVEE keeps its EM overweight
    # AND gets a cheapness boost; IVV's neutral anchor is faded below 1.0. (Need at
    # least min_universe names for the cross-sectional dial to engage.)
    closes = {"IVV": [100.0 * (1.02 ** k) for k in range(60)],
              "AVEE": [100.0 * (0.99 ** k) for k in range(60)],
              "EWX": [100.0 for _ in range(60)]}
    ct = _combined_tilt(closes, cs)
    assert ct["AVEE"] > 1.5      # EM anchor (1.5) lifted further by cheapness
    assert ct["IVV"] < 1.0       # US neutral anchor (1.0) faded by richness


def test_conviction_hysteresis_keeps_held_boundary_names():
    cs = CrossSectionSettings(quantile=0.5, min_score=-99, conviction=True, conviction_buffer=0.15)
    scores = {c: float(10 - i) for i, c in enumerate("abcdefghij")}   # a best .. j worst
    vols = {c: 0.2 for c in scores}
    # 'f' (rank 6) sits outside the strict enter band but inside the exit band: kept only
    # if already held, dropped if fresh — that's the hysteresis that suppresses churn.
    held = rank_weights(scores, vols, cs, held={"f"})
    fresh = rank_weights(scores, vols, cs, held=set())
    assert held["f"] > 0
    assert fresh["f"] == 0.0
