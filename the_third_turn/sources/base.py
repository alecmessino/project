"""Shared dataclasses + async protocol for the three live sources.

Design mirrors mrbet's ``odds/base.py`` (a small Protocol + dataclasses) but async:
every source exposes ``async def fetch(session) -> ...`` and never raises past its
own boundary — a failed/blocked source returns an empty result so one bad book
can't kill the poll loop.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Protocol, runtime_checkable

import aiohttp


@dataclass
class Quote:
    """One book's live game-total (Over/Under) quote for a single game."""

    book: str
    home: str                    # canonical team key (see shared_piping.team_map)
    away: str
    line: float                  # the total (e.g. 8.5)
    over_odds: Optional[int] = None
    under_odds: Optional[int] = None
    ts: Optional[float] = None   # epoch seconds when observed (stamped by caller)
    live_game: Optional[bool] = None  # book flags the event in-play (guards vs the
                                      # same matchup listed pregame for TOMORROW)
    status: Optional[str] = None      # market lifecycle: OPEN / SUSPENDED / ... (quote-lifecycle
                                      # capture — distinguishes a live quote from a suspended one)

    @property
    def game_key(self) -> str:
        """Book-agnostic key to join quotes/state across sources: ``AWY@HOM``."""
        return f"{self.away}@{self.home}"


@dataclass
class LiveGameState:
    """Live pitcher/lineup state for one in-progress game (from MLB Stats API)."""

    game_pk: int
    away: str                    # canonical team key
    home: str
    inning: int                  # current inning number (1-based)
    half: str                    # "top" | "bottom"
    away_score: int
    home_score: int
    pitcher_id: Optional[int] = None
    pitcher_name: Optional[str] = None
    pitch_count: Optional[int] = None        # current pitcher's cumulative pitches
    batting_slot_due: Optional[int] = None   # lineup slot of the batter due up (1-9)
    times_through_order: Optional[int] = None  # TTO for the batter due up vs this pitcher
    status: str = ""             # MLB abstractGameState ("Live", "Final", ...)
    # --- Revision 2 additions ---
    outs: Optional[int] = None               # outs in the current half-inning (0-2)
    on_first: bool = False                    # base occupancy (for RE24)
    on_second: bool = False
    on_third: bool = False
    starter_id: Optional[int] = None          # the game's starting pitcher (this side)
    starter_on_mound: bool = True             # is the current pitcher still the starter?
    starter_tier: str = "Unknown"             # Ace / Mid / Back (season baseline WHIP)
    data_age_seconds: Optional[float] = None  # age of the MLB feed snapshot (latency)
    # --- live velocity (current pitcher; for the in-play velocity-cliff study) ---
    velo_early: Optional[float] = None        # avg startSpeed, first ~15 pitches
    velo_recent: Optional[float] = None       # avg startSpeed, last ~10 pitches
    velo_drop: Optional[float] = None         # velo_early − velo_recent (+ = losing velocity)

    @property
    def game_key(self) -> str:
        return f"{self.away}@{self.home}"

    @property
    def is_live(self) -> bool:
        return self.status.lower() in ("live", "in progress")

    @property
    def total_runs(self) -> int:
        return self.away_score + self.home_score


@dataclass
class SourceResult:
    """Uniform per-source fetch result with diagnostics for connection_check."""

    name: str
    ok: bool
    http_status: Optional[int] = None
    latency_ms: Optional[float] = None
    payload_bytes: Optional[int] = None
    error: Optional[str] = None
    quotes: list[Quote] = field(default_factory=list)
    states: list[LiveGameState] = field(default_factory=list)


@runtime_checkable
class OddsSource(Protocol):
    """A book source yielding live :class:`Quote` objects."""

    name: str

    async def fetch(self, session: aiohttp.ClientSession) -> SourceResult:
        ...


@runtime_checkable
class StateSource(Protocol):
    """A game-state source yielding live :class:`LiveGameState` objects."""

    name: str

    async def fetch(self, session: aiohttp.ClientSession) -> SourceResult:
        ...
