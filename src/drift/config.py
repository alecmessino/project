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
    # the time-series overlay that controls drawdown without going market-neutral. Off in
    # the headline book, which stays long-only and fully invested (no cash, no leverage).
    trend_throttle: bool = False
    exposure_floor: float = 0.0     # minimum exposure even in a broad bear (0 = fully defensive ok)
    # Strategic forward-looking tilt (applied to the long book, fully invested): each
    # held name's risk-balanced weight is multiplied by the PRODUCT of its region/size/
    # style factors below, then the long leg is renormalized back to full gross — so the
    # tilt redistributes capital toward favored segments without adding cash or leverage.
    # Empty dicts (or a missing segment key) = neutral (factor 1.0). Tilting toward EM /
    # international / value / small expresses a forward valuation view, anchored by the
    # cross-sectional momentum selection (only the trending top half is eligible to hold).
    tilt_region: dict[str, float] = Field(default_factory=dict)  # US / DEV / EM
    tilt_size: dict[str, float] = Field(default_factory=dict)    # large / mid / small / largemid
    tilt_style: dict[str, float] = Field(default_factory=dict)   # value / blend / growth
    # Dynamic valuation dial. The static tilt above is the long-run ANCHOR (the value/
    # size/region premia that persist across decades and regions). This dial makes the
    # tilt TIME-VARYING: it scales each name's anchor by how cheap the segment looks
    # right now — proxied by long-horizon relative reversal (a segment that has LAGGED
    # the cross-section over `tilt_reversion_bars` reads as cheap and is leaned into;
    # one that has LED strongly is faded back toward market weight). So the book tilts
    # hard when a favored segment is beaten down and drifts to neutral as the spread
    # compresses — and if the richly-priced corner gets cheap, its underweight eases
    # toward market weight too. 0 strength = pure static anchor; the dial is bounded to
    # [1/cap, cap] so it leans, never lurches. (Value × momentum, cf. AMP 2013.)
    tilt_dynamic: bool = False            # off by default; the headline YAML book turns it on
    tilt_reversion_bars: int = 756        # ~3y lookback for the cheapness (long-term reversal) dial
    tilt_reversion_strength: float = 0.5  # how hard the dial leans on cheapness (0 = anchor only)
    tilt_dial_cap: float = 1.8            # bound the per-name dial multiplier to [1/cap, cap]
    # Tax-aware rebalancing (taxable accounts). The plain book chases the momentum target
    # every rebalance, which churns hard (short-term gains). When `tax_aware`, a no-trade
    # band suppresses small target changes (only act when a name's target moves more than
    # `no_trade_band`, or it leaves the held set entirely), cutting turnover so more gains
    # age into long-term treatment. The bigger lever is a slower `rebalance_bars`; this
    # band trims the residual churn on top. Off by default — turn on for a taxable sleeve.
    tax_aware: bool = False
    no_trade_band: float = 0.03           # min target-weight change to act on a held name
    # "Meaningful turnover" — conviction (rank-hysteresis) selection. A held name is KEPT
    # while it stays within the top (quantile + buffer); a new name ENTERS only if it clears
    # the stricter top (quantile - buffer), so the book reacts to a real signal but ignores
    # boundary noise. It works as intended (turnover 349%->187%, holds 72->135 days,
    # short-term share 96%->63%) but, like a slower cadence, it LOWERS after-tax return on
    # the 40-yr backtest (vanilla +947% vs +843-889% after-tax) — this momentum signal's
    # alpha is inseparable from its turnover, so trading less can't help after-tax in ANY
    # form. Kept OFF. The after-tax levers are asset location + TLH; native tax-efficiency
    # would need a slower / longer-half-life base SIGNAL, not a rebalance gate.
    conviction: bool = False
    conviction_buffer: float = 0.15       # rank hysteresis as a fraction of the universe
    # Slow / multi-factor tax-efficient sleeve (taxable accounts). This is NOT a gate bolted
    # onto the fast book — it is a different, natively-slow base signal. When `slow_sleeve_mode`
    # is on: (1) the trend score is measured over a longer `slow_lookback` (12-month drift)
    # instead of `signal.lookback`, blended natively with the same region/size/style tilt so the
    # cross-sectional ranking is stable and turns over slowly by construction; (2) selection uses
    # ASYMMETRIC rank hysteresis — a name ENTERS only in the top `buy_quantile` (top 40%) but a
    # HELD name is kept until it falls out of the top `hold_quantile` (top 60%), so boundary noise
    # never churns the book; (3) a tax-lot holding-period cushion (the execution layer below)
    # delays liquidating a winner that is within `lt_protection_window_bars` of the 365-day
    # long-term mark, unless its rank breaks down catastrophically (bottom `catastrophic_quantile`),
    # pushing the realized gain into long-term treatment. Off by default — the headline fast book
    # is unaffected.
    slow_sleeve_mode: bool = False
    buy_quantile: float = 0.40            # enter only if ranked in the top this fraction
    hold_quantile: float = 0.60           # hold a held name until it leaves the top this fraction
    slow_lookback: int = 252              # 12-month drift horizon for the slow-sleeve trend score
    lt_protection_window_bars: int = 30   # delay a sale within this many bars of the LT threshold
    catastrophic_quantile: float = 0.10   # a held name in the bottom this fraction is sold anyway
    # Neutralize the ranking within a grouping before ranking: "none", "region",
    # or "factor". Region-neutral isolates which STYLE is trending (controlling for
    # region); factor-neutral isolates which REGION is trending. Demeaning trend
    # scores within each group removes the group-level tilt from the long/short book.
    neutralize: str = "none"


class TaxSettings(BaseModel):
    """Client tax profile driving the after-tax modeling on the ledger.

    Rates are decomposed into federal + NIIT + state so the Tax Lab can personalize by
    bracket and state of residence. The effective `rate_lt`/`rate_st` are derived. This
    is illustrative modeling (lot-level on the book's own marks), NOT a substitute for
    the custodian's cost basis or tax advice. Defaults are top-bracket federal, no state.
    """

    enabled: bool = True
    fed_lt: float = 0.20        # federal long-term cap-gains top bracket
    fed_st: float = 0.37        # federal short-term = ordinary income top bracket
    niit: float = 0.038         # net investment income tax (applies to both)
    state_lt: float = 0.0       # state rate on long-term gains (often = ordinary)
    state_st: float = 0.0       # state rate on short-term gains
    state: str = "—"            # label only (e.g. "CA", "TX"); rates are the source of truth
    lt_holding_bars: int = 252  # trading days a lot must be held to qualify as long-term

    @property
    def rate_lt(self) -> float:
        """Effective long-term rate: federal LT + NIIT + state."""
        return self.fed_lt + self.niit + self.state_lt

    @property
    def rate_st(self) -> float:
        """Effective short-term rate: federal ordinary + NIIT + state."""
        return self.fed_st + self.niit + self.state_st


class Settings(BaseModel):
    signal: SignalSettings = Field(default_factory=SignalSettings)
    triggers: TriggerSettings = Field(default_factory=TriggerSettings)
    tax: TaxSettings = Field(default_factory=TaxSettings)
    sizing: SizingSettings = Field(default_factory=SizingSettings)
    engine: EngineSettings = Field(default_factory=EngineSettings)
    cross_section: CrossSectionSettings = Field(default_factory=CrossSectionSettings)

    @classmethod
    def load(cls, path: str | Path) -> "Settings":
        data = yaml.safe_load(Path(path).read_text()) or {}
        return cls(**data)
