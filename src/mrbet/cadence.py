"""Sparse sampling cadence for the live loop.

The Odds API charges per poll; ESPN's clock is free. So we watch the (free)
game clock and spend a (paid) odds fetch only at a few high-value game-clock
marks — by default the timeout windows + quarter breaks of Q1-Q3, where the
reversion signal is both meaningful and still actionable (enough time left).
Past the last mark we stop. ~17x fewer odds calls than 60s polling, retaining
86% of opportunities on a 79-game playoff backtest.

`CadenceGate` is pure and unit-tested; the provider just feeds it the elapsed
clock and fetches odds when it says "due".
"""

from __future__ import annotations

from dataclasses import dataclass, field


def timeout_marks(quarters: int = 3, offsets: tuple[float, ...] = (6.0, 9.0, 12.0)) -> list[float]:
    """Full-game minutes-elapsed at the natural stoppages of the first `quarters`.

    Default: Q1-Q3 at 6, 9 and 12 minutes elapsed within each quarter -> the
    ~6:00 and ~3:00 mandatory-timeout windows plus the quarter break:
    [6, 9, 12, 18, 21, 24, 30, 33, 36]. On 79 real playoff games this retained
    86% of the opportunities dense 1-min sampling found at ~17x fewer odds calls
    (vs 60s polling) — the efficiency/coverage sweet spot.
    """
    marks: list[float] = []
    for q in range(1, quarters + 1):
        start = (q - 1) * 12.0
        for off in offsets:
            marks.append(start + off)
    return sorted(marks)


def interval_marks(step: float = 6.0, last: float = 42.0) -> list[float]:
    """Evenly spaced marks (a simpler alternative to timeout windows)."""
    marks, m = [], step
    while m <= last:
        marks.append(round(m, 2))
        m += step
    return marks


@dataclass
class CadenceGate:
    """Fires at most once per mark as the game clock crosses it."""

    marks: list[float] = field(default_factory=timeout_marks)
    fired: set = field(default_factory=set)

    def __post_init__(self):
        self.marks = sorted(self.marks)

    def due(self, minutes_elapsed: float) -> bool:
        """True when the clock has reached an unfired mark. Collapses catch-up
        (several missed marks at once) into a single fetch."""
        pending = [m for m in self.marks if m <= minutes_elapsed and m not in self.fired]
        if not pending:
            return False
        self.fired.update(pending)
        return True

    @property
    def done(self) -> bool:
        return bool(self.marks) and all(m in self.fired for m in self.marks)


def build_marks(cadence: str) -> list[float]:
    """Map a cadence name to its sampling marks."""
    if cadence in ("timeout", "timeouts"):
        return timeout_marks()
    if cadence == "interval":
        return interval_marks()
    raise ValueError(f"unknown cadence: {cadence!r}")
