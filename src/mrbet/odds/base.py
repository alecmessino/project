"""Provider protocol shared by all data sources.

A provider yields `Snapshot`s: a live game state (clock/score) paired with the
current live over/under lines for the tracked markets. The engine treats every
provider identically, so a manual/replay source and a real API are
interchangeable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator, Optional, Protocol, runtime_checkable

from ..models import GameState, MarketLine


@dataclass
class Snapshot:
    """One observation: game state + the live lines seen at that moment."""

    state: GameState
    lines: list[MarketLine] = field(default_factory=list)
    # Free-form provider metadata (e.g. API credits remaining), for logging.
    meta: dict = field(default_factory=dict)


@runtime_checkable
class OddsProvider(Protocol):
    """Anything that can stream snapshots for one event."""

    def snapshots(self) -> Iterator[Snapshot]:
        """Yield snapshots. Live providers block/sleep between polls; replay
        providers yield their recorded sequence and stop."""
        ...

    def credits_remaining(self) -> Optional[int]:
        """API credits left, or None if not applicable."""
        ...


def get_provider(name: str, **kwargs) -> OddsProvider:
    """Factory: build a provider by name. Imported lazily to avoid pulling in
    `requests`/network code for the manual path."""
    name = name.lower()
    if name in ("manual", "replay"):
        from .manual import ManualProvider

        return ManualProvider(**kwargs)
    if name in ("theodds", "the-odds-api", "api"):
        from .theodds import TheOddsProvider

        return TheOddsProvider(**kwargs)
    if name in ("bovada", "bodog"):
        from ..bovada_feed import BovadaProvider

        return BovadaProvider(**kwargs)
    raise ValueError(f"unknown provider: {name!r}")
