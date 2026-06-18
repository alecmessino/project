"""Load and validate Driftwood settings (pydantic).

Every threshold and model parameter lives here / in the YAML — nothing is
hardcoded in the engine or the math modules, mirroring mrbet's convention.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class SignalSettings(BaseModel):
    """Trend-measurement parameters (units: bars)."""

    lookback: int = 60          # bars over which trend strength is measured
    vol_window: int = 30        # bars for the per-bar volatility estimate
    breakout_channel: int = 40  # Donchian channel length for breakout confirmation
    continuation: float = 0.10  # fraction of recent drift assumed to persist (UNVALIDATED)

    @property
    def min_history(self) -> int:
        """Bars required before the signal is well-defined (warmup)."""
        return max(self.lookback, self.vol_window, self.breakout_channel) + 1


class TriggerSettings(BaseModel):
    """The conjunctive gate: a position fires only if every condition holds."""

    score_threshold: float = 1.0        # min |trend z-score| to ENTER
    require_breakout: bool = True       # demand an agreeing Donchian breakout to enter
    min_edge_after_cost: float = 0.0    # min net expected edge over the hold horizon
    strong_score_threshold: float = 2.0  # |score| at/above this is tagged STRONG
    min_weight: float = 0.05            # ignore negligible target weights
    # Exit band: once in a position, keep holding while the trend score keeps its
    # sign and |score| stays above this (looser than entry -> hysteresis that stops
    # a noisy series from whipsawing in and out around the entry threshold).
    exit_score_threshold: float = 0.25


class SizingSettings(BaseModel):
    """Position-sizing and cost parameters."""

    target_vol: float = 0.15        # annualized volatility target per position
    max_leverage: float = 2.0       # hard cap on |weight|
    kelly_fraction: float = 0.50    # fractional-Kelly scaler on the vol-target weight
    cost_bps_per_side: float = 5.0  # transaction cost per side, in basis points
    hold_bars: int = 10             # assumed holding horizon for the cost hurdle


class EngineSettings(BaseModel):
    """Universe and calendar."""

    instruments: list[str] = Field(default_factory=list)  # empty -> track all seen
    bars_per_year: float = 252.0    # 252 daily, 52 weekly, 35040 15-min crypto, etc.


class CrossSectionSettings(BaseModel):
    """The cross-sectional (relative-strength) momentum variant.

    Instead of trading each instrument on its own absolute trend (time-series
    momentum), rank the universe each bar and go long the strongest / short the
    weakest names — classic Jegadeesh-Titman cross-sectional momentum.
    """

    quantile: float = 0.50          # top/bottom fraction of the universe per leg (sweep-best)
    long_short: bool = False        # False -> long-only top (default); True -> dollar-neutral L/S
    gross_exposure: float = 1.0     # total |weight| budget across both legs
    weighting: str = "inv_vol"      # "equal" | "inv_vol" | "score"
    min_universe: int = 3           # need at least this many ranked names to trade
    max_weight: float = 0.50        # per-name |weight| cap
    # Turnover controls — keep the book agile without churning it (and paying for it):
    rebalance_bars: int = 21        # re-rank only every N bars (1 = every bar); cuts turnover ~Nx
    min_score: float = 0.0          # only hold a name whose (demeaned) trend z clears this —
                                    # when nothing is trending the book lightens up rather than
                                    # holding the "least-bad", i.e. flexible vs a static index
    # Trend throttle: scale total invested exposure by the breadth of POSITIVE absolute
    # trend across the universe (full in a broad uptrend, light in a broad bear). This is
    # the time-series overlay that controls drawdown without going market-neutral.
    trend_throttle: bool = False
    exposure_floor: float = 0.0     # minimum exposure even in a broad bear (0 = fully defensive ok)
    # Neutralize the ranking within a grouping before ranking: "none", "region",
    # or "factor". Region-neutral isolates which STYLE is trending (controlling for
    # region); factor-neutral isolates which REGION is trending. Demeaning trend
    # scores within each group removes the group-level tilt from the long/short book.
    neutralize: str = "none"


class Settings(BaseModel):
    signal: SignalSettings = Field(default_factory=SignalSettings)
    triggers: TriggerSettings = Field(default_factory=TriggerSettings)
    sizing: SizingSettings = Field(default_factory=SizingSettings)
    engine: EngineSettings = Field(default_factory=EngineSettings)
    cross_section: CrossSectionSettings = Field(default_factory=CrossSectionSettings)

    @classmethod
    def load(cls, path: str | Path) -> "Settings":
        data = yaml.safe_load(Path(path).read_text()) or {}
        return cls(**data)
