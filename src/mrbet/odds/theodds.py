"""Live provider: The Odds API (Bovada lines) + ESPN scoreboard (clock/score).

The Odds API supplies live over/under prices for Bovada across totals, team
totals, and period markets, but its scores endpoint does not expose the game
clock. ESPN's public scoreboard JSON (free, no key) provides period + clock +
score, which we use to build the live `GameState`.

Network failures are swallowed into empty snapshots so the engine's poll loop
keeps running; credit usage is read from response headers and surfaced in meta.
"""

from __future__ import annotations

import os
import time
from typing import Iterator, Optional

import requests

from ..models import GameState, MarketLine, MarketType, Period
from .base import Snapshot

ODDS_BASE = "https://api.the-odds-api.com/v4"
ESPN_SCOREBOARD = (
    "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
)
SPORT = "basketball_nba"

# Engine market key -> The Odds API market key.
MARKET_KEYS = {
    "total_full": "totals",
    "total_h1": "totals_h1",
    "total_q1": "totals_q1",
    "total_q2": "totals_q2",
    "total_q3": "totals_q3",
    "total_q4": "totals_q4",
    "team_total": "team_totals",
}
# Reverse map to recover the Period / type from an API market key.
_PERIOD_FOR_KEY = {
    "totals": Period.FULL,
    "totals_h1": Period.H1,
    "totals_q1": Period.Q1,
    "totals_q2": Period.Q2,
    "totals_q3": Period.Q3,
    "totals_q4": Period.Q4,
    "team_totals": Period.FULL,
}


class TheOddsProvider:
    def __init__(
        self,
        event,                      # config.EventMeta
        markets: list[str],
        poll_interval: int = 60,
        api_key: Optional[str] = None,
        bookmaker: str = "bovada",
        max_polls: Optional[int] = None,
        **_ignored,
    ):
        self.event = event
        self.api_key = api_key or os.environ.get("ODDS_API_KEY", "")
        if not self.api_key:
            raise RuntimeError("ODDS_API_KEY not set (env or --api-key)")
        self.bookmaker = bookmaker
        self.market_keys = [MARKET_KEYS[m] for m in markets if m in MARKET_KEYS]
        self.poll_interval = poll_interval
        self.max_polls = max_polls
        self._credits: Optional[int] = None
        self._event_id: Optional[str] = None

    def credits_remaining(self) -> Optional[int]:
        return self._credits

    # --- streaming -------------------------------------------------------- #
    def snapshots(self) -> Iterator[Snapshot]:
        polls = 0
        while self.max_polls is None or polls < self.max_polls:
            polls += 1
            state = self._fetch_state()
            lines = self._fetch_lines()
            yield Snapshot(
                state=state,
                lines=lines,
                meta={"credits_remaining": self._credits, "source": "theodds"},
            )
            if state is not None and state.minutes_remaining <= 0:
                return
            time.sleep(self.poll_interval)

    # --- The Odds API ----------------------------------------------------- #
    def _resolve_event_id(self) -> Optional[str]:
        if self._event_id:
            return self._event_id
        try:
            r = requests.get(
                f"{ODDS_BASE}/sports/{SPORT}/events",
                params={"apiKey": self.api_key},
                timeout=15,
            )
            r.raise_for_status()
            for ev in r.json():
                if self._matches(ev):
                    self._event_id = ev["id"]
                    return self._event_id
        except requests.RequestException:
            return None
        return None

    def _matches(self, ev: dict) -> bool:
        names = {ev.get("home_team", ""), ev.get("away_team", "")}
        want = {self.event.home, self.event.away}
        return names == want or all(
            any(w.split()[-1] in n for n in names) for w in want
        )

    def _fetch_lines(self) -> list[MarketLine]:
        event_id = self._resolve_event_id()
        if not event_id or not self.market_keys:
            return []
        try:
            r = requests.get(
                f"{ODDS_BASE}/sports/{SPORT}/events/{event_id}/odds",
                params={
                    "apiKey": self.api_key,
                    "regions": "us",
                    "markets": ",".join(self.market_keys),
                    "bookmakers": self.bookmaker,
                    "oddsFormat": "american",
                },
                timeout=15,
            )
            self._credits = _credits_from(r)
            r.raise_for_status()
        except requests.RequestException:
            return []
        return self._parse_lines(r.json())

    def _parse_lines(self, payload: dict) -> list[MarketLine]:
        lines: list[MarketLine] = []
        for bk in payload.get("bookmakers", []):
            if bk.get("key") != self.bookmaker:
                continue
            for mkt in bk.get("markets", []):
                key = mkt.get("key")
                period = _PERIOD_FOR_KEY.get(key)
                if period is None:
                    continue
                lines.extend(self._lines_from_market(key, period, mkt.get("outcomes", [])))
        return lines

    def _lines_from_market(self, key: str, period: Period, outcomes: list[dict]) -> list[MarketLine]:
        if key == "team_totals":
            return self._team_total_lines(outcomes)
        # Game total: a single Over/Under pair.
        over = next((o for o in outcomes if o.get("name") == "Over"), None)
        under = next((o for o in outcomes if o.get("name") == "Under"), None)
        if not over or not under:
            return []
        return [
            MarketLine(
                MarketType.GAME_TOTAL,
                period,
                float(over.get("point")),
                int(over.get("price")),
                int(under.get("price")),
            )
        ]

    def _team_total_lines(self, outcomes: list[dict]) -> list[MarketLine]:
        # team_totals outcomes carry a `description` (team name) + Over/Under name.
        by_team: dict[str, dict] = {}
        for o in outcomes:
            team = o.get("description", "")
            by_team.setdefault(team, {})[o.get("name")] = o
        out: list[MarketLine] = []
        for team, ou in by_team.items():
            over, under = ou.get("Over"), ou.get("Under")
            if not over or not under:
                continue
            key = self._team_key(team)
            out.append(
                MarketLine(
                    MarketType.TEAM_TOTAL,
                    Period.FULL,
                    float(over.get("point")),
                    int(over.get("price")),
                    int(under.get("price")),
                    team=key,
                )
            )
        return out

    def _team_key(self, team_name: str) -> str:
        if self.event.home in team_name or team_name in self.event.home:
            return self.event.home_key
        if self.event.away in team_name or team_name in self.event.away:
            return self.event.away_key
        return team_name

    # --- ESPN game state -------------------------------------------------- #
    def _fetch_state(self) -> Optional[GameState]:
        try:
            r = requests.get(ESPN_SCOREBOARD, timeout=15)
            r.raise_for_status()
            data = r.json()
        except requests.RequestException:
            return None
        for ev in data.get("events", []):
            comp = (ev.get("competitions") or [{}])[0]
            competitors = comp.get("competitors", [])
            teams = {c.get("homeAway"): c for c in competitors}
            home = teams.get("home", {}).get("team", {}).get("displayName", "")
            away = teams.get("away", {}).get("team", {}).get("displayName", "")
            if not self._espn_matches(home, away):
                continue
            teams["_status"] = comp.get("status", {})
            return self._espn_state(teams)
        return None

    def _espn_matches(self, home: str, away: str) -> bool:
        return (self.event.home.split()[-1] in home and self.event.away.split()[-1] in away)

    def _espn_state(self, teams: dict) -> Optional[GameState]:
        try:
            home_c, away_c = teams["home"], teams["away"]
            home_score = int(home_c.get("score", 0))
            away_score = int(away_c.get("score", 0))
        except (KeyError, ValueError):
            return None
        status = teams.get("_status", {})
        period = int(status.get("period", 0) or 0)
        clock = float(status.get("clock", 0.0) or 0.0)  # seconds left in period
        # Full-game elapsed (regulation), capped at 48.
        reg_period = min(period, 4) if period else 0
        elapsed = max(0.0, (reg_period - 1) * 12 + (12 - clock / 60.0)) if period else 0.0
        elapsed = min(elapsed, 48.0)
        remaining = max(0.0, 48.0 - elapsed)
        return GameState(
            period=Period.FULL,
            minutes_elapsed=elapsed,
            minutes_remaining=remaining,
            home_score=home_score,
            away_score=away_score,
        )


def _credits_from(resp: requests.Response) -> Optional[int]:
    val = resp.headers.get("x-requests-remaining")
    try:
        return int(val) if val is not None else None
    except ValueError:
        return None
