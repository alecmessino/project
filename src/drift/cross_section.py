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
) -> dict[str, float]:
    """Portfolio weights from a cross-sectional ranking of trend scores.

    Long the top `quantile` of the universe, short the bottom `quantile` (when
    `long_short`), each leg distributed by `weighting` and capped at `max_weight`.
    Returns a weight for every key in `scores` (0.0 for un-held names). Below
    `min_universe` ranked names, everything is flat.

    When `cs.neutralize` is set and `groups` is supplied, trend scores are demeaned
    within each group first, so the long/short book is neutral to that grouping.
    """
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

    cap_k = n // 2 if cs.long_short else n
    k = max(1, min(round(n * cs.quantile), cap_k))
    longs = ranked[:k]
    shorts = ranked[-k:] if cs.long_short else []

    long_budget = cs.gross_exposure / 2 if cs.long_short else cs.gross_exposure
    short_budget = cs.gross_exposure / 2 if cs.long_short else 0.0

    for key, w in _leg_weights(longs, long_budget, +1, vols, cs.weighting).items():
        out[key] = w
    for key, w in _leg_weights(shorts, short_budget, -1, vols, cs.weighting).items():
        out[key] = w

    # Per-name cap (keeps a single low-vol name from dominating the book).
    for key in out:
        if out[key] > cs.max_weight:
            out[key] = cs.max_weight
        elif out[key] < -cs.max_weight:
            out[key] = -cs.max_weight
    return out


def _groups_for(cs: CrossSectionSettings) -> Optional[dict[str, str]]:
    """Ticker->group map for the configured neutralization dimension, or None."""
    if cs.neutralize in ("region", "factor"):
        from .universes import group_map
        return group_map(cs.neutralize)
    return None


@dataclass
class RankRow:
    instrument: str
    score: float
    ann_vol: float
    weight: float
    leg: str  # "LONG" / "SHORT" / "—"


def rank_snapshot(series: dict[str, list[Bar]], settings: Settings) -> list[RankRow]:
    """Current cross-sectional ranking from the latest bar of each series."""
    s = settings.signal
    scores: dict[str, float] = {}
    vols: dict[str, float] = {}
    for inst, bars in series.items():
        if len(bars) < s.min_history:
            continue
        closes = [b.close for b in bars]
        scores[inst] = sig.momentum_score(closes, s.lookback, s.vol_window)
        vols[inst] = sizing.annualize_vol(
            sig.realized_vol(closes, s.vol_window), settings.engine.bars_per_year
        )
    weights = rank_weights(scores, vols, settings.cross_section, _groups_for(settings.cross_section))
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
    prev: dict[str, float] = {inst: 0.0 for inst in instruments}
    gross_eq = net_eq = 1.0
    net_curve: list[float] = []
    net_rets: list[float] = []
    turnover = 0.0
    held_counts: list[int] = []

    for i in range(length - 1):
        scores: dict[str, float] = {}
        vols: dict[str, float] = {}
        for inst in instruments:
            hist = series[inst][: i + 1]
            if len(hist) < s.min_history:
                continue
            closes = [b.close for b in hist]
            scores[inst] = sig.momentum_score(closes, s.lookback, s.vol_window)
            vols[inst] = sizing.annualize_vol(sig.realized_vol(closes, s.vol_window), bpy)

        weights = rank_weights(scores, vols, cs, groups) if scores else {inst: 0.0 for inst in instruments}

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
