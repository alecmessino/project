"""Turn (instrument history, settings) into an Evaluation, then a Signal if it
clears every configured threshold.

The gate is deliberately conjunctive, exactly like mrbet's: a strong trend score
alone never fires. The breakout must independently confirm the direction AND the
expected edge must survive the round-trip transaction cost. That is the guard
against chasing noise, a big move is necessary but not sufficient.
"""

from __future__ import annotations

from typing import Optional, Sequence

from . import signal as sig
from . import sizing
from .config import Settings
from .models import Bar, Evaluation, Side, Signal


def evaluate(instrument: str, history: Sequence[Bar], settings: Settings) -> Optional[Evaluation]:
    """Run the momentum model for one instrument. Returns None before warmup."""
    s = settings.signal
    if len(history) < s.min_history:
        return None

    closes = [b.close for b in history]
    highs = [b.high for b in history]
    lows = [b.low for b in history]

    score = sig.momentum_score(closes, s.lookback, s.vol_window)
    breakout = sig.donchian_breakout(highs, lows, closes, s.breakout_channel)
    per_bar_vol = sig.realized_vol(closes, s.vol_window)
    drift = sig.drift_per_bar(closes, s.lookback)

    side = Side.from_sign(score)
    ann_vol = sizing.annualize_vol(per_bar_vol, settings.engine.bars_per_year)

    # Expected edge points the way the trend points; the position follows it.
    expected_edge = sizing.expected_edge_per_bar(drift, settings.signal.continuation)
    edge_after_cost = sizing.edge_net_of_cost(
        expected_edge, settings.sizing.hold_bars, settings.sizing.cost_bps_per_side
    )

    raw_weight = sizing.vol_target_weight(
        side.sign, ann_vol, settings.sizing.target_vol, settings.sizing.max_leverage
    )
    target_weight = raw_weight * settings.sizing.kelly_fraction
    kelly_lev = sizing.kelly_leverage(
        abs(expected_edge), per_bar_vol ** 2, settings.sizing.max_leverage
    )

    return Evaluation(
        instrument=instrument,
        asof=history[-1].asof,
        side=side,
        score=score,
        breakout=breakout,
        drift_per_bar=drift,
        per_bar_vol=per_bar_vol,
        ann_vol=ann_vol,
        expected_edge=expected_edge,
        edge_after_cost=edge_after_cost,
        target_weight=target_weight,
        kelly_leverage=kelly_lev,
    )


def to_signal(ev: Evaluation, settings: Settings) -> Optional[Signal]:
    """Return a Signal if the Evaluation clears every threshold, else None."""
    t = settings.triggers
    reasons: list[str] = []

    # 1. Trend strong enough relative to the instrument's own noise.
    if abs(ev.score) < t.score_threshold:
        return None
    reasons.append(f"trend z={ev.score:+.2f}")

    # 2. Independent breakout confirmation in the same direction.
    if t.require_breakout and not sig.trend_agrees(ev.score, ev.breakout):
        return None
    if t.require_breakout:
        reasons.append(f"{ev.breakout:+d} donchian breakout")

    # 3. Expected edge survives the round-trip cost over the hold horizon.
    if ev.edge_after_cost < t.min_edge_after_cost:
        return None
    reasons.append(f"net edge {ev.edge_after_cost*1e4:+.1f}bps over {settings.sizing.hold_bars} bars")

    # 4. The vol-targeted position is non-negligible.
    if abs(ev.target_weight) < t.min_weight:
        return None
    reasons.append(f"weight {ev.target_weight:+.2f} @ {ev.ann_vol*100:.0f}% vol")

    strong = abs(ev.score) >= t.strong_score_threshold
    return Signal(evaluation=ev, strong=strong, reasons=reasons)
