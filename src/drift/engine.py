"""Orchestration: stream snapshots -> maintain per-instrument history -> evaluate
-> gate -> emit results.

Mirrors mrbet's Engine: the feed is interchangeable, the engine just consumes
snapshots and runs the model on each tracked instrument. It keeps a bounded
rolling window of bars per instrument so memory stays flat on a long live run.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Callable, Optional

from .config import Settings
from .feed.base import PriceFeed, Snapshot
from .models import Bar, Evaluation, Signal
from .triggers import evaluate, to_signal


@dataclass
class Result:
    evaluation: Evaluation
    signal: Optional[Signal]


class Engine:
    def __init__(self, settings: Settings, feed: PriceFeed):
        self.settings = settings
        self.feed = feed
        # Keep a little more than warmup so the signal always has its full window.
        self._maxlen = settings.signal.min_history + settings.signal.lookback
        self._history: dict[str, deque[Bar]] = {}

    def _tracked(self, instrument: str) -> bool:
        allowed = self.settings.engine.instruments
        return not allowed or instrument in allowed

    def process_snapshot(self, snap: Snapshot) -> list[Result]:
        results: list[Result] = []
        for inst, bar in snap.bars.items():
            if not self._tracked(inst):
                continue
            hist = self._history.setdefault(inst, deque(maxlen=self._maxlen))
            hist.append(bar)
            ev = evaluate(inst, list(hist), self.settings)
            if ev is None:
                continue
            sig = to_signal(ev, self.settings)
            results.append(Result(evaluation=ev, signal=sig))
        return results

    def run(self, on_result: Optional[Callable[[Result], None]] = None) -> None:
        """Consume the feed end to end, invoking `on_result` for each evaluation."""
        for snap in self.feed.snapshots():
            for res in self.process_snapshot(snap):
                if on_result:
                    on_result(res)
