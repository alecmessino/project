"""Walk-forward, cost-aware backtest for the Driftwood momentum model.

No lookahead: at each bar the target weight is computed from history up to and
including that bar, then applied to the *next* bar's return. Transaction cost is
charged on every change in weight. This is the harness that decides whether the
strategy survives frictions, the single most important check from the
feasibility note, so cost is on by default and reported explicitly.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Sequence

from .config import Settings
from .models import Bar
from .triggers import evaluate, to_signal


@dataclass
class BacktestResult:
    instrument: str
    n_bars: int
    n_trades: int
    gross_return: float       # cumulative, gross of cost
    net_return: float         # cumulative, net of cost
    cost_drag: float          # gross - net
    sharpe: float             # annualized, net
    max_drawdown: float       # net, as a positive fraction
    hit_rate: float           # share of active bars with positive net pnl
    turnover: float           # sum of |weight changes|
    avg_exposure: float       # mean |weight| while in a position
    equity_curve: list[float] = field(default_factory=list)
    dates: list[str] = field(default_factory=list)   # per-bar dates parallel to equity_curve

    def to_dict(self) -> dict:
        return asdict(self)


def _sign(x: float) -> int:
    return (x > 1e-9) - (x < -1e-9)


def _next_weight(prev_weight, ev, exit_thresh: float, settings: Settings) -> float:
    """Target weight for the next bar, given the position we already hold.

    Flat -> only a fully gated Signal opens a position. In a position -> keep
    riding (re-sized to the current vol target) while the trend score holds its
    sign and stays above the exit band; a fresh opposite Signal flips us; anything
    else closes to flat. This separation of strict entry from looser exit is the
    standard trend-following fix for whipsaw.
    """
    if ev is None:
        return 0.0
    in_pos = abs(prev_weight) > 1e-9
    if not in_pos:
        return ev.target_weight if to_signal(ev, settings) is not None else 0.0

    same_sign = ev.score != 0 and (prev_weight > 0) == (ev.score > 0)
    if same_sign and abs(ev.score) >= exit_thresh:
        return ev.target_weight              # still trending our way -> keep riding
    if to_signal(ev, settings) is not None:
        return ev.target_weight              # fresh gated signal (e.g. a flip)
    return 0.0                               # trend faded -> exit


def _max_drawdown(equity: Sequence[float]) -> float:
    peak = -math.inf
    mdd = 0.0
    for v in equity:
        peak = max(peak, v)
        if peak > 0:
            mdd = max(mdd, (peak - v) / peak)
    return mdd


@dataclass
class Step:
    """One realized bar of the strategy: weight held into the next bar and the
    returns realized over it. The dated, per-bar record the analytics layer
    (tearsheet, ledger) consumes."""

    asof: str
    weight: float
    dweight: float       # |weight change| this bar (drives cost/turnover)
    net_ret: float       # strategy return net of cost
    asset_ret: float     # the instrument's own (buy-and-hold) return over the bar


def strategy_steps(instrument: str, bars: Sequence[Bar], settings: Settings) -> list[Step]:
    """Walk the gated, hysteresis-held momentum strategy bar by bar (no lookahead).

    Single source of truth for the position logic, `backtest`, the tearsheet, and
    the forward ledger all read these steps so they can never disagree.
    """
    cost = settings.sizing.cost_bps_per_side / 1e4
    exit_thresh = settings.triggers.exit_score_threshold
    # evaluate() depends only on the recent tail, so feed it a bounded window:
    # identical results, but O(n) over the series instead of O(n^2), this is what
    # makes a multi-decade daily backtest tractable.
    window = settings.signal.min_history + settings.signal.lookback
    prev_weight = 0.0
    steps: list[Step] = []
    for i in range(len(bars) - 1):
        lo = max(0, i + 1 - window)
        ev = evaluate(instrument, bars[lo: i + 1], settings)
        weight = _next_weight(prev_weight, ev, exit_thresh, settings)
        dw = abs(weight - prev_weight)
        cur, nxt = bars[i].close, bars[i + 1].close
        asset_ret = (nxt / cur - 1.0) if cur > 0 else 0.0
        steps.append(Step(asof=bars[i + 1].asof, weight=weight, dweight=dw,
                          net_ret=weight * asset_ret - cost * dw, asset_ret=asset_ret))
        prev_weight = weight
    return steps


def current_weight(instrument: str, bars: Sequence[Bar], prev_weight: float,
                   settings: Settings) -> float:
    """The position the live strategy would hold *from the latest bar forward*,
    given the weight currently held (so hysteresis carries across days). This is
    the decision the forward ledger records each session."""
    window = settings.signal.min_history + settings.signal.lookback
    ev = evaluate(instrument, bars[-window:], settings)
    return _next_weight(prev_weight, ev, settings.triggers.exit_score_threshold, settings)


def backtest(instrument: str, bars: Sequence[Bar], settings: Settings) -> BacktestResult:
    """Run the gated momentum strategy over one instrument's bar series."""
    bpy = settings.engine.bars_per_year
    cost = settings.sizing.cost_bps_per_side / 1e4

    steps = strategy_steps(instrument, bars, settings)
    prev_weight = 0.0
    gross_eq, net_eq = 1.0, 1.0
    net_curve: list[float] = []
    net_dates: list[str] = []
    net_rets: list[float] = []
    n_trades = 0
    turnover = 0.0
    active_exposures: list[float] = []
    wins = active = 0

    for st in steps:
        if _sign(st.weight) != _sign(prev_weight):
            n_trades += 1
        turnover += st.dweight
        gross_eq *= (1.0 + st.weight * st.asset_ret)
        net_eq *= (1.0 + st.net_ret)
        net_curve.append(net_eq)
        net_dates.append(st.asof)
        net_rets.append(st.net_ret)
        if abs(st.weight) > 1e-9:
            active += 1
            active_exposures.append(abs(st.weight))
            if st.net_ret > 0:
                wins += 1
        prev_weight = st.weight

    mean = sum(net_rets) / len(net_rets) if net_rets else 0.0
    var = sum((r - mean) ** 2 for r in net_rets) / len(net_rets) if len(net_rets) > 1 else 0.0
    std = math.sqrt(var)
    sharpe = (mean / std * math.sqrt(bpy)) if std > 0 else 0.0

    return BacktestResult(
        instrument=instrument,
        n_bars=len(bars),
        n_trades=n_trades,
        gross_return=gross_eq - 1.0,
        net_return=net_eq - 1.0,
        cost_drag=(gross_eq - net_eq),
        sharpe=sharpe,
        max_drawdown=_max_drawdown(net_curve),
        hit_rate=(wins / active) if active else 0.0,
        turnover=turnover,
        avg_exposure=(sum(active_exposures) / len(active_exposures)) if active_exposures else 0.0,
        equity_curve=[round(v, 6) for v in net_curve],
        dates=net_dates,
    )
