"""Synthetic feed: deterministic geometric-Brownian-motion price paths.

Lets `drift demo` and the test suite exercise the full pipeline with zero external
dependencies or network access. Paths are seeded so runs are reproducible, and an
optional regime schedule injects persistent trends — exactly the structure a
momentum model should profit from, which makes it a useful sanity check (a
trend-follower that loses money on a trending series is broken).
"""

from __future__ import annotations

import math
import random
from typing import Iterator, Optional, Sequence

from ..models import Bar
from .base import Snapshot


class SyntheticFeed:
    """Generate GBM bars with optional trend regimes.

    `regimes` is a list of (length_bars, annualized_drift) segments; the per-bar
    drift switches between them, so the series trends up, chops, then trends down,
    etc. With no regimes the path is a driftless random walk (a momentum model
    should make ~nothing on it net of cost — the null check).
    """

    def __init__(
        self,
        instruments: Sequence[str] = ("SYN",),
        n_bars: int = 750,
        start_price: float = 100.0,
        bar_vol: float = 0.012,
        bars_per_year: float = 252.0,
        regimes: Optional[Sequence[tuple[int, float]]] = None,
        seed: int = 7,
    ):
        self.instruments = list(instruments)
        self.n_bars = n_bars
        self.start_price = start_price
        self.bar_vol = bar_vol
        self.bars_per_year = bars_per_year
        self.regimes = list(regimes) if regimes else [(n_bars, 0.0)]
        self.seed = seed
        self._series: dict[str, list[Bar]] = {}
        self._build()

    def _drift_schedule(self) -> list[float]:
        """Per-bar drift for each bar index, expanded from the regime list."""
        per_bar: list[float] = []
        for length, ann_drift in self.regimes:
            mu = ann_drift / self.bars_per_year
            per_bar.extend([mu] * length)
        if len(per_bar) < self.n_bars:
            per_bar.extend([per_bar[-1] if per_bar else 0.0] * (self.n_bars - len(per_bar)))
        return per_bar[: self.n_bars]

    def _build(self) -> None:
        schedule = self._drift_schedule()
        for k, inst in enumerate(self.instruments):
            rng = random.Random(self.seed + k)
            price = self.start_price
            bars: list[Bar] = []
            for i in range(self.n_bars):
                mu = schedule[i]
                shock = rng.gauss(0.0, self.bar_vol)
                ret = mu - 0.5 * self.bar_vol ** 2 + shock
                new_price = price * math.exp(ret)
                hi = max(price, new_price) * (1.0 + abs(rng.gauss(0.0, self.bar_vol / 3)))
                lo = min(price, new_price) * (1.0 - abs(rng.gauss(0.0, self.bar_vol / 3)))
                bars.append(Bar(asof=str(i), close=round(new_price, 4),
                                high=round(hi, 4), low=round(lo, 4)))
                price = new_price
            self._series[inst] = bars

    def series(self, instrument: Optional[str] = None) -> list[Bar]:
        """Materialized bar list for one instrument (default: the first)."""
        inst = instrument or self.instruments[0]
        return self._series[inst]

    def snapshots(self) -> Iterator[Snapshot]:
        for i in range(self.n_bars):
            bars = {inst: self._series[inst][i] for inst in self.instruments}
            yield Snapshot(asof=str(i), bars=bars)
