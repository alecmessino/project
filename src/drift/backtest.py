"""Walk-forward, cost-aware backtest for the Driftwood momentum model.

No lookahead: at each bar the target weight is computed from history up to and
including that bar, then applied to the *next* bar's return. Transaction cost is
charged on every change in weight. This is the harness that decides whether the
strategy survives frictions — the single most important check from the
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


def backtest(instrument: str, bars: Sequence[Bar], settings: Settings) -> BacktestResult:
    """Run the gated momentum strategy over one instrument's bar series."""
    bpy = settings.engine.bars_per_year
    cost = settings.sizing.cost_bps_per_side / 1e4

    exit_thresh = settings.triggers.exit_score_threshold
    prev_weight = 0.0
    gross_eq, net_eq = 1.0, 1.0
    gross_curve: list[float] = []
    net_curve: list[float] = []
    net_rets: list[float] = []
    n_trades = 0
    turnover = 0.0
    active_exposures: list[float] = []
    wins = active = 0

    # Decide the weight at bar i from history[:i+1], realize it over (i -> i+1).
    # Entry is strict (a gated Signal); holding is governed by hysteresis so a
    # live trend isn't churned in and out around the entry threshold.
    for i in range(len(bars) - 1):
        hist = bars[: i + 1]
        ev = evaluate(instrument, hist, settings)
        weight = _next_weight(prev_weight, ev, exit_thresh, settings)

        dw = abs(weight - prev_weight)
        # Count a trade only on a genuine entry/exit/flip — not every vol-resize
        # (the per-bar re-sizing cost is captured by `turnover` instead).
        if _sign(weight) != _sign(prev_weight):
            n_trades += 1
        turnover += dw

        nxt = bars[i + 1].close
        cur = bars[i].close
        asset_ret = (nxt / cur - 1.0) if cur > 0 else 0.0

        gross_pnl = weight * asset_ret
        net_pnl = gross_pnl - cost * dw

        gross_eq *= (1.0 + gross_pnl)
        net_eq *= (1.0 + net_pnl)
        gross_curve.append(gross_eq)
        net_curve.append(net_eq)
        net_rets.append(net_pnl)

        if abs(weight) > 1e-9:
            active += 1
            active_exposures.append(abs(weight))
            if net_pnl > 0:
                wins += 1

        prev_weight = weight

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
    )
