"""Core runtime data structures for Driftwood.

These are plain dataclasses (no validation), mirroring mrbet's split: runtime
objects stay light dataclasses so the hot path is cheap and the math modules
(`signal.py`, `sizing.py`) stay dependency-free; config loading/validation lives
in `config.py` (pydantic).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Side(str, Enum):
    """Which direction a position leans."""

    LONG = "long"
    SHORT = "short"
    FLAT = "flat"

    @classmethod
    def from_sign(cls, x: float) -> "Side":
        if x > 0:
            return cls.LONG
        if x < 0:
            return cls.SHORT
        return cls.FLAT

    @property
    def sign(self) -> int:
        return {Side.LONG: 1, Side.SHORT: -1, Side.FLAT: 0}[self]


@dataclass
class Bar:
    """One OHLC(V) observation for an instrument at a point in time.

    `asof` is an opaque ordering key (ISO date string, epoch, or bar index) — the
    engine never parses it, it only preserves order. `high`/`low` default to
    `close` so a close-only series still works for the momentum signal (the
    Donchian breakout simply degenerates to the close path).
    """

    asof: str
    close: float
    high: Optional[float] = None
    low: Optional[float] = None
    volume: Optional[float] = None

    def __post_init__(self) -> None:
        if self.high is None:
            self.high = self.close
        if self.low is None:
            self.low = self.close


@dataclass
class Evaluation:
    """The full model output for one instrument at one timestamp.

    `score` is the volatility-normalized trend strength (a z-score under a
    random-walk null); `breakout` is the Donchian confirmation in {-1, 0, +1};
    `target_weight` is the signed, vol-targeted, fractional-Kelly-capped portfolio
    weight the model would hold. `edge_after_cost` is the expected return over the
    assumed holding horizon net of round-trip cost — the EV analog.
    """

    instrument: str
    asof: str
    side: Side
    score: float              # vol-normalized trailing trend (z-score)
    breakout: int             # -1 / 0 / +1 Donchian channel breakout
    drift_per_bar: float      # trailing log-return per bar (raw drift)
    per_bar_vol: float        # per-bar return stdev
    ann_vol: float            # annualized volatility
    expected_edge: float      # expected per-bar return of the position
    edge_after_cost: float    # expected edge over the hold horizon, net of cost
    target_weight: float      # signed portfolio weight (vol-targeted, capped)
    kelly_leverage: float     # raw continuous-Kelly leverage (pre-fraction), info


@dataclass
class Signal:
    """An Evaluation that cleared every trigger threshold — worth alerting on."""

    evaluation: Evaluation
    strong: bool
    reasons: list[str] = field(default_factory=list)

    @property
    def dedupe_key(self) -> str:
        e = self.evaluation
        return f"{e.instrument}:{e.side.value}"
