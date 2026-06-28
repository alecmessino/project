"""Cross-sectional (relative-strength) momentum: rank the universe, hold the
extremes.

The time-series model in `triggers.py` trades each instrument on its *own*
absolute trend. This is the other classic momentum form (Jegadeesh & Titman,
1993): at each bar, rank every instrument by trend score and go long the top
quantile / short the bottom quantile. The bet is *relative* — the strongest names
beat the weakest — which is naturally dollar-neutral and sheds market direction.

`rank_weights` is pure; `cross_backtest` walks a multi-instrument universe forward
with no lookahead and charges transaction cost on every per-name weight change.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from statistics import median
from typing import Optional, Sequence

from . import signal as sig
from . import sizing
from .config import CrossSectionSettings, Settings
from .models import Bar


def _leg_weights(
    members: Sequence[tuple[str, float]],
    budget: float,
    sign: int,
    vols: dict[str, float],
    weighting: str,
) -> dict[str, float]:
    """Distribute a signed budget across one leg by the chosen weighting scheme."""
    if not members or budget <= 0:
        return {}
    keys = [k for k, _ in members]
    if weighting == "equal":
        raw = {k: 1.0 for k in keys}
    elif weighting == "score":
        raw = {k: abs(s) for k, s in members}
    else:  # inv_vol: risk-balanced, the managed-futures default
        med = median([v for v in vols.values() if v > 0] or [1.0])
        raw = {k: 1.0 / (vols.get(k) or med) for k in keys}
    total = sum(raw.values()) or 1.0
    return {k: sign * budget * raw[k] / total for k in keys}


def _demean_within_groups(scores: dict[str, float], groups: dict[str, str]) -> dict[str, float]:
    """Subtract each group's mean trend score, so the ranking reflects within-group
    relative strength only — i.e. neutral to the group-level (region or factor) tilt."""
    members: dict[str, list[str]] = {}
    for k, s in scores.items():
        if s is not None:
            members.setdefault(groups.get(k, "_other"), []).append(k)
    out = dict(scores)
    for keys in members.values():
        mean = sum(scores[k] for k in keys) / len(keys)
        for k in keys:
            out[k] = scores[k] - mean
    return out


def rank_weights(
    scores: dict[str, float],
    vols: dict[str, float],
    cs: CrossSectionSettings,
    groups: Optional[dict[str, str]] = None,
    tilt: Optional[dict[str, float]] = None,
    held: Optional[set[str]] = None,
    current_weights: Optional[dict[str, float]] = None,
) -> dict[str, float]:
    """Portfolio weights from a cross-sectional ranking of trend scores.

    Long the top `quantile` of the universe, short the bottom `quantile` (when
    `long_short`), each leg distributed by `weighting` and capped at `max_weight`.
    Returns a weight for every key in `scores` (0.0 for un-held names). Below
    `min_universe` ranked names, everything is flat.

    When `cs.neutralize` is set and `groups` is supplied, trend scores are demeaned
    within each group first, so the long/short book is neutral to that grouping.

    When `tilt` (a per-name multiplier) is supplied, the long leg's risk-balanced
    weights are scaled by it and renormalized back to the long budget — a strategic
    overweight of favored segments that keeps the book fully invested (no cash added).
    """
    # Breadth of POSITIVE absolute trend (pre-demean) drives the exposure throttle.
    raw_valid = [s for s in scores.values() if s is not None]
    breadth = (sum(1 for s in raw_valid if s > 0) / len(raw_valid)) if raw_valid else 0.0
    if cs.neutralize and cs.neutralize != "none" and groups:
        scores = _demean_within_groups(scores, groups)
    out = {k: 0.0 for k in scores}
    ranked = sorted(
        ((k, s) for k, s in scores.items() if s is not None),
        key=lambda kv: kv[1],
        reverse=True,
    )
    n = len(ranked)
    if n < cs.min_universe:
        return out

    # Continuous tilt overlay (offline research): hold the whole universe, weight = base·(1 + k·z),
    # floored long-only, capped, renormalized to gross. No top-quantile selection — a different book
    # entirely. Returns early so none of the selection logic below runs.
    if cs.tilt_overlay:
        mu = sum(s for _, s in ranked) / n
        sd = (sum((s - mu) ** 2 for _, s in ranked) / n) ** 0.5 or 1.0
        base = cs.gross_exposure / n
        raw = {key: max(0.0, base * (1.0 + cs.tilt_strength * (s - mu) / sd)) for key, s in ranked}
        tot = sum(raw.values())
        if tot <= 0:
            return out
        for key, w in raw.items():
            out[key] = min(cs.max_weight, w * cs.gross_exposure / tot)
        tot2 = sum(out.values())                     # one renormalize pass after the cap
        if tot2 > 0:
            for key in out:
                out[key] *= cs.gross_exposure / tot2
        return out

    cap_k = n // 2 if cs.long_short else n
    k = max(1, min(round(n * cs.quantile), cap_k))
    # A name is only held if its (demeaned) trend clears min_score — so when nothing
    # is trending the book lightens up rather than holding the least-bad name.
    if cs.slow_sleeve_mode:
        # Asymmetric rank hysteresis (the slow sleeve): a name ENTERS only in the top
        # `buy_quantile`, but a HELD name is kept until it leaves the top `hold_quantile`
        # — so boundary names never churn the book by construction. The held set is the
        # last period's positions (`current_weights`), unioned with any explicit `held`.
        held_set = {k for k, w in (current_weights or {}).items() if w > 0} | (held or set())
        enter_k = max(1, min(round(n * cs.buy_quantile), cap_k))
        exit_k = max(enter_k, min(round(n * cs.hold_quantile), cap_k))
        longs = [(key, s) for rank_i, (key, s) in enumerate(ranked[:exit_k])
                 if s >= cs.min_score and (rank_i < enter_k or key in held_set)]
    elif cs.conviction and held:
        # Rank hysteresis: enter only in the stricter top (q - buffer); keep a held name
        # while it stays within the looser top (q + buffer) — suppresses boundary churn.
        buf = cs.conviction_buffer
        enter_k = max(1, min(round(n * (cs.quantile - buf)), cap_k))
        exit_k = max(k, min(round(n * (cs.quantile + buf)), cap_k))
        longs = [(key, s) for rank_i, (key, s) in enumerate(ranked[:exit_k])
                 if s >= cs.min_score and (rank_i < enter_k or key in held)]
    else:
        longs = [(key, s) for key, s in ranked[:k] if s >= cs.min_score]
    shorts = [(key, s) for key, s in ranked[-k:] if s <= -cs.min_score] if cs.long_short else []

    long_budget = cs.gross_exposure / 2 if cs.long_short else cs.gross_exposure
    short_budget = cs.gross_exposure / 2 if cs.long_short else 0.0

    for key, w in _leg_weights(longs, long_budget, +1, vols, cs.weighting).items():
        out[key] = w
    for key, w in _leg_weights(shorts, short_budget, -1, vols, cs.weighting).items():
        out[key] = w

    # Strategic forward tilt: redistribute the long leg toward favored segments
    # (e.g. EM / international / value / small) by multiplying each long weight by
    # its per-name factor, then renormalizing the leg back to its budget — so the
    # book stays fully invested rather than parking the tilt difference in cash.
    if tilt and long_budget > 0:
        tilted = {key: out[key] * tilt.get(key, 1.0) for key in out if out[key] > 0}
        tot = sum(tilted.values())
        if tot > 0:
            scale = long_budget / tot
            for key, w in tilted.items():
                out[key] = w * scale

    # Per-name cap (keeps a single low-vol name from dominating the book).
    for key in out:
        if out[key] > cs.max_weight:
            out[key] = cs.max_weight
        elif out[key] < -cs.max_weight:
            out[key] = -cs.max_weight

    # Trend throttle: scale total exposure by positive-trend breadth (full in a broad
    # uptrend, light in a broad bear) — the time-series overlay for drawdown control.
    if cs.trend_throttle:
        expo = max(cs.exposure_floor, min(1.0, breadth))
        out = {key: w * expo for key, w in out.items()}
    return out


def _groups_for(cs: CrossSectionSettings) -> Optional[dict[str, str]]:
    """Ticker->group map for the configured neutralization dimension, or None."""
    if cs.neutralize in ("region", "size", "style", "factor"):
        from .universes import group_map
        return group_map(cs.neutralize) or None
    return None


def _tilt_for(cs: CrossSectionSettings) -> Optional[dict[str, float]]:
    """Per-ticker strategic tilt multiplier = region × size × style factor.

    Built from the configured `tilt_region`/`tilt_size`/`tilt_style` maps and the
    universe's segment classification. Returns None when no tilt is configured (so
    the book is plain inverse-vol). A name absent from the matrix gets factor 1.0.
    """
    if not (cs.tilt_region or cs.tilt_size or cs.tilt_style):
        return None
    from .universes import MATRIX
    out: dict[str, float] = {}
    for tkr, (region, size, style) in MATRIX.items():
        out[tkr] = (cs.tilt_region.get(region, 1.0)
                    * cs.tilt_size.get(size, 1.0)
                    * cs.tilt_style.get(style, 1.0))
    return out


def _cheapness_dial(closes: dict[str, list[float]], cs: CrossSectionSettings) -> dict[str, float]:
    """Per-name valuation dial from LONG-horizon relative reversal (a value proxy).

    Each name's trailing `tilt_reversion_bars` return is z-scored across the cross
    section. A laggard (z<0) reads as cheap → dial >1 (lean in); a strong multi-year
    leader (z>0) reads as rich → dial <1 (fade toward market weight). Bounded to
    [1/cap, cap] and scaled by `tilt_reversion_strength`. Empty until enough history.
    """
    H = max(2, cs.tilt_reversion_bars)
    rets = {i: cl[-1] / cl[-H - 1] - 1.0
            for i, cl in closes.items() if len(cl) > H and cl[-H - 1] > 0}
    if len(rets) < cs.min_universe:
        return {}
    vals = list(rets.values())
    mean = sum(vals) / len(vals)
    std = (sum((r - mean) ** 2 for r in vals) / len(vals)) ** 0.5 or 1.0
    cap = max(1.0, cs.tilt_dial_cap)
    dial: dict[str, float] = {}
    for i, r in rets.items():
        z = max(-2.0, min(2.0, (r - mean) / std))
        d = 1.0 - cs.tilt_reversion_strength * (z / 2.0)   # cheap -> >1, rich -> <1
        dial[i] = max(1.0 / cap, min(cap, d))
    return dial


def _combined_tilt(closes: dict[str, list[float]], cs: CrossSectionSettings) -> Optional[dict[str, float]]:
    """The tilt actually applied: the static anchor, optionally scaled by the dynamic
    valuation dial. `closes` is each instrument's close series up to the rebalance date."""
    anchor = _tilt_for(cs)
    if not cs.tilt_dynamic:
        return anchor
    dial = _cheapness_dial(closes, cs)
    if not dial:
        return anchor
    keys = set(anchor or {}) | set(dial)
    return {k: (anchor.get(k, 1.0) if anchor else 1.0) * dial.get(k, 1.0) for k in keys}


def _slow_signal(cs: CrossSectionSettings, s) -> tuple[int, int]:
    """(lookback, min_history) for the active sleeve. The slow sleeve measures trend over
    a longer 12-month `slow_lookback`, which also lengthens the warmup gate (a name isn't
    rankable until it has `slow_lookback + 1` bars). The fast book is unchanged."""
    if cs.slow_sleeve_mode:
        lb = cs.slow_lookback
        return lb, max(s.min_history, lb + 1)
    return s.lookback, s.min_history


def _lot_protected_weights(target: dict[str, float], prev: dict[str, float],
                           scores: dict[str, float], held_bars: dict[str, int],
                           cs: CrossSectionSettings, lt_bars: int) -> dict[str, float]:
    """Tax-lot capital-gains protection (execution layer, slow sleeve only).

    A name the ranking wants to LIQUIDATE/REDUCE is held back when its lot is within
    `lt_protection_window_bars` of the 365-day long-term threshold — letting the gain age
    into long-term treatment — UNLESS its rank has broken down catastrophically (it has
    fallen into the bottom `catastrophic_quantile` of the cross-section), in which case it
    is sold regardless. Frozen names keep their prior weight; the rest of the long book is
    renormalized to fill the residual gross budget so the book stays fully invested (mirrors
    the residual logic in `_tax_aware_weights`). No-op unless (`slow_sleeve_mode` or `lot_protect`)
    and `prev` — the latter lets the continuous-tilt hybrid reuse this protection without the rest of
    the slow sleeve."""
    if not ((cs.slow_sleeve_mode or cs.lot_protect) and prev):
        return target
    ranked = sorted((k for k, v in scores.items() if v is not None),
                    key=lambda k: scores[k], reverse=True)
    n = len(ranked)
    if n == 0:
        return target
    rank_of = {k: i for i, k in enumerate(ranked)}
    cutoff = n * (1.0 - cs.catastrophic_quantile)   # ranks at/after this are the bottom decile
    lo = lt_bars - cs.lt_protection_window_bars
    frozen: dict[str, float] = {}
    for k, p in prev.items():
        if p <= 0 or target.get(k, 0.0) >= p:        # only protect names being cut
            continue
        near_lt = lo <= held_bars.get(k, 0) < lt_bars
        catastrophic = rank_of.get(k, n) >= cutoff
        if near_lt and not catastrophic:
            frozen[k] = p
    if not frozen:
        return target
    resid = cs.gross_exposure - sum(frozen.values())
    others = {k: v for k, v in target.items() if v > 0 and k not in frozen}
    tot = sum(others.values())
    scale = (resid / tot) if (tot > 0 and resid > 0) else (1.0 if tot > 0 else 0.0)
    out = dict(frozen)
    for k, v in others.items():
        out[k] = v * scale
    return out


def _tax_aware_weights(target: dict[str, float], prev: dict[str, float],
                       cs: CrossSectionSettings) -> dict[str, float]:
    """No-trade band for taxable accounts: hold the previous weight on a name whose
    target barely moved, so small rebalancing trades don't churn gains into short-term
    realizations. A name that leaves the held set (target 0) is still exited in full,
    and a genuinely new/large target is taken. The kept book is renormalized back to the
    same gross. No-op when `tax_aware` is off (returns the target unchanged)."""
    if not cs.tax_aware or not prev:
        return target
    band = cs.no_trade_band
    kept: dict[str, float] = {}      # continuing names whose target barely moved -> no trade
    traded: dict[str, float] = {}    # names entering/exiting or moving beyond the band
    for k in set(target) | set(prev):
        t = target.get(k, 0.0)
        p = prev.get(k, 0.0)
        if t > 0 and p > 0 and abs(t - p) <= band:
            kept[k] = p
        else:
            traded[k] = t
    # Hold the kept names exactly (zero turnover); fill the remaining gross budget with
    # the traded names, rescaled — so only names that actually move incur a trade.
    resid = cs.gross_exposure - sum(kept.values())
    traded_sum = sum(v for v in traded.values() if v > 0)
    out = dict(kept)
    scale = (resid / traded_sum) if (traded_sum > 0 and resid > 0) else 1.0
    for k, v in traded.items():
        out[k] = v * scale if v > 0 else 0.0
    return out


@dataclass
class RankRow:
    instrument: str
    score: float
    ann_vol: float
    weight: float
    leg: str  # "LONG" / "SHORT" / "—"


def cross_book_streams(series: dict[str, list[Bar]], settings: Settings) -> list[tuple[str, float]]:
    """Dated net returns of the cross-sectional rotation over the FULL history.

    Unlike `cross_backtest` (which aligns to the shortest series), this handles
    ragged histories — at each rebalance it ranks only the instruments that have
    enough history by that date — so the book spans the whole period (incl. 2008)
    rather than truncating to the youngest name. Long-only/L-S, rebalance cadence,
    min_score gate, and neutralization all apply via `rank_weights`.
    """
    s = settings.signal
    cs = settings.cross_section
    cost = settings.sizing.cost_bps_per_side / 1e4
    bpy = settings.engine.bars_per_year
    rebalance = max(1, cs.rebalance_bars)
    groups = _groups_for(cs)

    price = {inst: {b.asof: b.close for b in bars} for inst, bars in series.items()}
    seq = {inst: [b.close for b in bars] for inst, bars in series.items()}
    pos = {inst: {b.asof: i for i, b in enumerate(bars)} for inst, bars in series.items()}
    all_dates = sorted({b.asof for bars in series.values() for b in bars})

    lb, min_hist = _slow_signal(cs, s)
    lt_bars = settings.tax.lt_holding_bars
    weights = {inst: 0.0 for inst in series}
    prev = dict(weights)
    entry_idx: dict[str, int] = {}          # bar index a held name was entered (for lot aging)
    out: list[tuple[str, float]] = []
    for di in range(len(all_dates) - 1):
        d, dn = all_dates[di], all_dates[di + 1]
        if di % rebalance == 0:
            scores: dict[str, float] = {}
            vols: dict[str, float] = {}
            closes_now: dict[str, list[float]] = {}
            for inst in series:
                i = pos[inst].get(d)
                if i is not None and i + 1 >= min_hist:
                    cl = seq[inst][: i + 1]
                    closes_now[inst] = cl
                    scores[inst] = sig.momentum_score(cl, lb, s.vol_window)
                    vols[inst] = sizing.annualize_vol(sig.realized_vol(cl, s.vol_window), bpy)
            tilt = _combined_tilt(closes_now, cs)
            held = {i for i, w in weights.items() if w > 0}
            held_bars = {k: di - e for k, e in entry_idx.items()}
            target = rank_weights(scores, vols, cs, groups, tilt, held, weights) if scores else dict(weights)
            target = _lot_protected_weights(target, weights, scores, held_bars, cs, lt_bars)
            weights = _tax_aware_weights(target, weights, cs)
            for inst in series:
                if weights.get(inst, 0.0) > 0 and inst not in entry_idx:
                    entry_idx[inst] = di
                elif weights.get(inst, 0.0) <= 0:
                    entry_idx.pop(inst, None)
        port = dw_tot = 0.0
        for inst in series:
            w = weights.get(inst, 0.0)
            pd, pn = price[inst].get(d), price[inst].get(dn)
            port += w * ((pn / pd - 1.0) if (pd and pn) else 0.0)
            dw_tot += abs(w - prev[inst])
            prev[inst] = w
        out.append((dn, port - cost * dw_tot))
    return out


def cross_book_entries(series: dict[str, list[Bar]], settings: Settings) -> list[dict]:
    """Like `cross_book_streams`, but records the full per-session book (date, weights,
    per-name prices, net return, equity) over the whole ragged history — the same shape
    the forward ledger stores, so `drift.tax.after_tax_track` can run an after-tax
    simulation over decades. Efficient single pass (no O(n^2) sub-slicing)."""
    s = settings.signal
    cs = settings.cross_section
    cost = settings.sizing.cost_bps_per_side / 1e4
    bpy = settings.engine.bars_per_year
    rebalance = max(1, cs.rebalance_bars)
    groups = _groups_for(cs)

    price = {inst: {b.asof: b.close for b in bars} for inst, bars in series.items()}
    seq = {inst: [b.close for b in bars] for inst, bars in series.items()}
    pos = {inst: {b.asof: i for i, b in enumerate(bars)} for inst, bars in series.items()}
    all_dates = sorted({b.asof for bars in series.values() for b in bars})

    lb, min_hist = _slow_signal(cs, s)
    lt_bars = settings.tax.lt_holding_bars
    weights = {inst: 0.0 for inst in series}
    prev = dict(weights)
    entry_idx: dict[str, int] = {}          # bar index a held name was entered (for lot aging)
    equity = 1.0
    entries: list[dict] = []
    for di in range(len(all_dates) - 1):
        d, dn = all_dates[di], all_dates[di + 1]
        if di % rebalance == 0:
            scores, vols, closes_now = {}, {}, {}
            for inst in series:
                i = pos[inst].get(d)
                if i is not None and i + 1 >= min_hist:
                    cl = seq[inst][: i + 1]
                    closes_now[inst] = cl
                    scores[inst] = sig.momentum_score(cl, lb, s.vol_window)
                    vols[inst] = sizing.annualize_vol(sig.realized_vol(cl, s.vol_window), bpy)
            tilt = _combined_tilt(closes_now, cs)
            held = {i for i, w in weights.items() if w > 0}
            held_bars = {k: di - e for k, e in entry_idx.items()}
            target = rank_weights(scores, vols, cs, groups, tilt, held, weights) if scores else dict(weights)
            target = _lot_protected_weights(target, weights, scores, held_bars, cs, lt_bars)
            weights = _tax_aware_weights(target, weights, cs)
            for inst in series:
                if weights.get(inst, 0.0) > 0 and inst not in entry_idx:
                    entry_idx[inst] = di
                elif weights.get(inst, 0.0) <= 0:
                    entry_idx.pop(inst, None)
        port = dw_tot = 0.0
        prices_now: dict[str, float] = {}
        for inst in series:
            w = weights.get(inst, 0.0)
            pd, pn = price[inst].get(d), price[inst].get(dn)
            if pd:
                prices_now[inst] = pd
            port += w * ((pn / pd - 1.0) if (pd and pn) else 0.0)
            dw_tot += abs(w - prev[inst])
            prev[inst] = w
        net = port - cost * dw_tot
        equity = round(equity * (1.0 + net), 6)
        entries.append({
            "date": dn[:10],
            "weights": {i: round(w, 4) for i, w in weights.items() if w != 0.0},
            "prices": {i: round(p, 6) for i, p in prices_now.items()},
            "realized_return": round(net, 6),
            "equity": equity,
            "seed": True,
        })
    return entries


def rank_snapshot(series: dict[str, list[Bar]], settings: Settings) -> list[RankRow]:
    """Current cross-sectional ranking from the latest bar of each series."""
    s = settings.signal
    lb, min_hist = _slow_signal(settings.cross_section, s)
    scores: dict[str, float] = {}
    vols: dict[str, float] = {}
    closes_now: dict[str, list[float]] = {}
    for inst, bars in series.items():
        if len(bars) < min_hist:
            continue
        closes = [b.close for b in bars]
        closes_now[inst] = closes
        scores[inst] = sig.momentum_score(closes, lb, s.vol_window)
        vols[inst] = sizing.annualize_vol(
            sig.realized_vol(closes, s.vol_window), settings.engine.bars_per_year
        )
    weights = rank_weights(scores, vols, settings.cross_section,
                           _groups_for(settings.cross_section),
                           _combined_tilt(closes_now, settings.cross_section))
    rows = [
        RankRow(
            instrument=inst,
            score=round(scores[inst], 3),
            ann_vol=round(vols[inst], 4),
            weight=round(weights[inst], 4),
            leg="LONG" if weights[inst] > 0 else "SHORT" if weights[inst] < 0 else "—",
        )
        for inst in scores
    ]
    rows.sort(key=lambda r: r.score, reverse=True)
    return rows


@dataclass
class CrossBacktestResult:
    instruments: list[str]
    n_bars: int
    net_return: float
    gross_return: float
    cost_drag: float
    sharpe: float
    max_drawdown: float
    turnover: float
    avg_names_held: float
    equity_curve: list[float] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _max_drawdown(equity: Sequence[float]) -> float:
    peak, mdd = float("-inf"), 0.0
    for v in equity:
        peak = max(peak, v)
        if peak > 0:
            mdd = max(mdd, (peak - v) / peak)
    return mdd


def cross_backtest(series: dict[str, list[Bar]], settings: Settings) -> CrossBacktestResult:
    """Walk-forward cross-sectional backtest over an aligned universe.

    Series are aligned by bar index up to the shortest one. At each bar the
    universe is ranked from history-to-date, the resulting weights are realized
    over the next bar, and cost is charged on every per-name weight change.
    """
    s = settings.signal
    cs = settings.cross_section
    groups = _groups_for(cs)
    cost = settings.sizing.cost_bps_per_side / 1e4
    bpy = settings.engine.bars_per_year
    instruments = list(series)
    if not instruments:
        return CrossBacktestResult(instruments, 0, 0, 0, 0, 0, 0, 0, 0, [])

    length = min(len(bars) for bars in series.values())
    rebalance = max(1, cs.rebalance_bars)
    lb, min_hist = _slow_signal(cs, s)
    lt_bars = settings.tax.lt_holding_bars
    prev: dict[str, float] = {inst: 0.0 for inst in instruments}
    weights: dict[str, float] = {inst: 0.0 for inst in instruments}
    entry_idx: dict[str, int] = {}          # bar index a held name was entered (for lot aging)
    gross_eq = net_eq = 1.0
    net_curve: list[float] = []
    net_rets: list[float] = []
    turnover = 0.0
    held_counts: list[int] = []

    for i in range(length - 1):
        # Re-rank only on the rebalance cadence; hold the target weights in between
        # so no turnover (and no cost) is incurred on the off-bars.
        if i % rebalance == 0:
            scores: dict[str, float] = {}
            vols: dict[str, float] = {}
            closes_now: dict[str, list[float]] = {}
            for inst in instruments:
                hist = series[inst][: i + 1]
                if len(hist) < min_hist:
                    continue
                closes = [b.close for b in hist]
                closes_now[inst] = closes
                scores[inst] = sig.momentum_score(closes, lb, s.vol_window)
                vols[inst] = sizing.annualize_vol(sig.realized_vol(closes, s.vol_window), bpy)
            tilt = _combined_tilt(closes_now, cs)
            held = {k for k, w in weights.items() if w > 0}
            held_bars = {k: i - e for k, e in entry_idx.items()}
            target = rank_weights(scores, vols, cs, groups, tilt, held, weights) if scores else {inst: 0.0 for inst in instruments}
            target = _lot_protected_weights(target, weights, scores, held_bars, cs, lt_bars)
            weights = _tax_aware_weights(target, weights, cs)
            for inst in instruments:
                if weights.get(inst, 0.0) > 0 and inst not in entry_idx:
                    entry_idx[inst] = i
                elif weights.get(inst, 0.0) <= 0:
                    entry_idx.pop(inst, None)

        gross_pnl = net_pnl = 0.0
        held = 0
        for inst in instruments:
            w = weights.get(inst, 0.0)
            cur, nxt = series[inst][i].close, series[inst][i + 1].close
            asset_ret = (nxt / cur - 1.0) if cur > 0 else 0.0
            dw = abs(w - prev[inst])
            gross_pnl += w * asset_ret
            net_pnl += w * asset_ret - cost * dw
            turnover += dw
            if abs(w) > 1e-9:
                held += 1
            prev[inst] = w

        gross_eq *= (1.0 + gross_pnl)
        net_eq *= (1.0 + net_pnl)
        net_curve.append(net_eq)
        net_rets.append(net_pnl)
        held_counts.append(held)

    mean = sum(net_rets) / len(net_rets) if net_rets else 0.0
    var = sum((r - mean) ** 2 for r in net_rets) / len(net_rets) if len(net_rets) > 1 else 0.0
    std = var ** 0.5
    sharpe = (mean / std * (bpy ** 0.5)) if std > 0 else 0.0

    return CrossBacktestResult(
        instruments=instruments,
        n_bars=length,
        net_return=net_eq - 1.0,
        gross_return=gross_eq - 1.0,
        cost_drag=gross_eq - net_eq,
        sharpe=sharpe,
        max_drawdown=_max_drawdown(net_curve),
        turnover=turnover,
        avg_names_held=(sum(held_counts) / len(held_counts)) if held_counts else 0.0,
        equity_curve=[round(v, 6) for v in net_curve],
    )
