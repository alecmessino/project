"""The mean-reversion projection: where will the period total actually finish?

The thesis: the market shades the live total toward *recent* pace (a cold start
drags the live total down). Mean reversion says remaining scoring reverts toward
the pregame-expected rate. We blend the two with weight `beta` and project the
final total, then let `triggers.py` compare it to the offered line.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .models import GameState, Period


@dataclass
class ReversionParams:
    beta: float = 0.70            # reversion weight toward pregame rate
    sigma_full: float = 11.0      # final-total std for a full game / period
    sigma_team: float = 8.0       # final-total std for a single team
    min_minutes_elapsed: float = 5.0


def projected_final(
    pregame_total: float,
    points_so_far: float,
    state: GameState,
    beta: float,
    min_minutes_elapsed: float = 2.0,
) -> float:
    """Projected final points for the period.

    fair_final = points_so_far + minutes_remaining *
                 [ beta * pregame_rate + (1 - beta) * current_pace ]

    - beta = 1 -> remaining play scores at the pregame rate (full reversion).
    - beta = 0 -> remaining play continues at the current observed pace.

    `points_so_far` is the points relevant to the market being evaluated: combined
    points for a game total, or one team's points for a team total. Before
    `min_minutes_elapsed` the current-pace estimate is too noisy, so the pace term
    falls back to the pregame rate.
    """
    length = state.period.length_minutes
    elapsed = max(0.0, state.minutes_elapsed)
    remaining = max(0.0, state.minutes_remaining)

    pregame_rate = pregame_total / length

    if elapsed >= min_minutes_elapsed and elapsed > 0:
        current_pace = points_so_far / elapsed
    else:
        # Not enough sample yet — anchor the pace term to the baseline.
        current_pace = pregame_rate

    blended_rate = beta * pregame_rate + (1.0 - beta) * current_pace
    return points_so_far + remaining * blended_rate


def sigma_for(state: GameState, base_sigma: float) -> float:
    """Final-total std scaled by the remaining fraction of the period.

    Variance accrues with the remaining fraction of the period: at tip-off the
    full `base_sigma` applies; with little time left, uncertainty collapses.
    """
    length = state.period.length_minutes
    if length <= 0:
        return base_sigma
    remaining_share = max(0.0, min(1.0, state.minutes_remaining / length))
    return base_sigma * math.sqrt(remaining_share)
