"""Turn (baseline, live line, game state) into an Evaluation, then into a Signal
if it crosses every configured threshold.

The trigger guard is deliberately conjunctive: a big line move alone never fires
a bet. The model must independently agree the line is mispriced (`edge_pts`) AND
the wager must carry positive EV at the *offered* odds. That is the guard against
chasing noise — the % move is necessary but not sufficient.
"""

from __future__ import annotations

from typing import Optional

from . import probability as prob
from .config import Settings
from .models import (
    Baseline,
    Evaluation,
    GameState,
    MarketLine,
    MarketType,
    Side,
    Signal,
)
from .reversion import projected_final, sigma_for


def evaluate_market(
    baseline: Baseline,
    live: MarketLine,
    state: GameState,
    points_so_far: float,
    settings: Settings,
) -> Evaluation:
    """Run the mean-reversion model for one market and price both sides."""
    m = settings.model
    base_sigma = m.sigma_team if baseline.market_type == MarketType.TEAM_TOTAL else m.sigma_full

    fair_final = projected_final(
        pregame_total=baseline.line,
        points_so_far=points_so_far,
        state=state,
        beta=m.beta,
        min_minutes_elapsed=m.min_minutes_elapsed,
    )
    sigma = sigma_for(state, base_sigma)

    # Mean reversion favors whichever side the projected final sits on relative to
    # the live line. fair_final above the line -> OVER has value, and vice versa.
    side = Side.OVER if fair_final >= live.line else Side.UNDER

    if side is Side.OVER:
        win_prob = prob.prob_over(live.line, fair_final, sigma)
        odds = live.over_odds
        edge_pts = fair_final - live.line
    else:
        win_prob = prob.prob_under(live.line, fair_final, sigma)
        odds = live.under_odds
        edge_pts = live.line - fair_final

    push_p = prob.push_prob(live.line, fair_final, sigma)
    ev = prob.expected_value(win_prob, odds, push_p)
    implied = prob.american_to_implied_prob(odds)

    # Fractional, bankroll-capped Kelly.
    full_kelly = prob.kelly_fraction(win_prob, odds, push_p)
    frac = full_kelly * settings.staking.kelly_fraction
    frac = min(frac, settings.staking.max_stake_fraction)
    stake = round(max(0.0, frac) * settings.staking.bankroll, 2)

    pct_move = (live.line - baseline.line) / baseline.line if baseline.line else 0.0

    return Evaluation(
        baseline=baseline,
        live=live,
        state=state,
        side=side,
        fair_final=fair_final,
        pct_move=pct_move,
        edge_pts=edge_pts,
        prob=win_prob,
        implied_prob=implied,
        ev=ev,
        kelly_stake=stake,
    )


def to_signal(ev: Evaluation, settings: Settings) -> Optional[Signal]:
    """Return a Signal if the Evaluation clears every threshold, else None."""
    t = settings.triggers
    reasons: list[str] = []

    # 1. Line moved meaningfully, in the direction that helps our side.
    #    OVER thesis wants a DROP (negative pct_move); UNDER wants a spike.
    move_helps = ev.pct_move <= 0 if ev.side is Side.OVER else ev.pct_move >= 0
    if not (move_helps and abs(ev.pct_move) >= t.pct_move_threshold):
        return None
    reasons.append(f"line moved {ev.pct_move*100:+.1f}% vs pregame")

    # 2. Model independently sees enough points of edge.
    if ev.edge_pts < t.edge_pts_threshold:
        return None
    reasons.append(f"model edge {ev.edge_pts:+.1f} pts")

    # 3. Positive EV at the offered odds.
    if ev.ev < t.ev_threshold:
        return None
    reasons.append(f"EV {ev.ev*100:+.1f}% @ {ev.offered_odds:+d}")

    # 4. Enough time left in the period for reversion to play out.
    min_rem = t.min_minutes_remaining.for_kind(ev.baseline.period.kind)
    if ev.state.minutes_remaining < min_rem:
        return None
    reasons.append(f"{ev.state.minutes_remaining:.1f} min left")

    strong = ev.ev >= t.ev_strong_threshold
    return Signal(evaluation=ev, strong=strong, reasons=reasons)
