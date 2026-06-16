"""Replay feed: stream recorded bars from memory or a CSV.

This is the offline workhorse — it makes the live engine and the backtest run off
the exact same code path (mrbet's "forward capture" idea: record real bars, then
replay them deterministically).
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterator

from ..models import Bar
from .base import Snapshot


class ReplayFeed:
    """Yield aligned snapshots from per-instrument bar series.

    `series` maps an instrument key to its time-ordered list of `Bar`s. Series are
    emitted by index position: snapshot *i* carries each instrument that has an
    *i*-th bar. Ragged series are fine — shorter ones simply stop contributing.
    """

    def __init__(self, series: dict[str, list[Bar]]):
        self.series = series

    def snapshots(self) -> Iterator[Snapshot]:
        if not self.series:
            return
        length = max(len(bars) for bars in self.series.values())
        for i in range(length):
            bars: dict[str, Bar] = {}
            asof = ""
            for inst, seq in self.series.items():
                if i < len(seq):
                    bars[inst] = seq[i]
                    asof = seq[i].asof
            if bars:
                yield Snapshot(asof=asof, bars=bars)

    @classmethod
    def from_csv(cls, path: str | Path, instrument: str | None = None) -> "ReplayFeed":
        """Build from a CSV with columns: asof, close[, high, low, volume[, instrument]].

        If an `instrument` column is present each row is routed to its instrument;
        otherwise every row belongs to `instrument` (default: the file stem).
        """
        path = Path(path)
        default_inst = instrument or path.stem
        series: dict[str, list[Bar]] = {}
        with path.open(newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                inst = row.get("instrument") or default_inst
                bar = Bar(
                    asof=row.get("asof") or row.get("date") or "",
                    close=float(row["close"]),
                    high=float(row["high"]) if row.get("high") else None,
                    low=float(row["low"]) if row.get("low") else None,
                    volume=float(row["volume"]) if row.get("volume") else None,
                )
                series.setdefault(inst, []).append(bar)
        return cls(series)
