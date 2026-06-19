"""Strategic forward tilt: long-only, fully invested, overweight favored segments."""

from drift.config import CrossSectionSettings
from drift.cross_section import _tilt_for, rank_weights


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
