"""Source B — FanDuel public content-managed-page (game totals).

Replaces DraftKings, whose API 403s this datacenter IP at the edge (an IP-level
block that User-Agent rotation cannot defeat — verified at build time).

Endpoint (undocumented, the site's own front-end calls it):
  https://sbapi.<state>.sportsbook.fanduel.com/api/content-managed-page?...&customPageId=mlb

Shape: ``attachments.events`` {id: {name, inPlay, ...}} and ``attachments.markets``
{id: {marketType, eventId, runners:[{runnerName, handicap, winRunnerOdds...}]}}.
Event names look like ``"Away Team (Pitcher) @ Home Team (Pitcher)"``.
The "Total Runs" market (``TOTAL_POINTS_(OVER/UNDER)``) is the game total.
"""

from __future__ import annotations

import re
import time
from typing import Optional

import aiohttp

from shared_piping.headers import rotating_headers
from shared_piping.team_map import resolve
from sources.base import Quote, SourceResult

# ``_ak`` is FanDuel's public front-end API key (visible in-page); state subdomain
# just picks a regulated market — any reachable one returns the same public board.
URL = ("https://sbapi.{state}.sportsbook.fanduel.com/api/content-managed-page"
       "?page=CUSTOM&customPageId=mlb&pbHorizontal=false&_ak=FhMFpcPWXMeyZxOx"
       "&timezone=America%2FNew_York")
REFERER = "https://sportsbook.fanduel.com/"
TOTAL_MARKET_TYPE = "TOTAL_POINTS_(OVER/UNDER)"
_PAREN = re.compile(r"\s*\([^)]*\)")  # strips the "(Pitcher)" annotation


def _teams_from_name(name: str) -> Optional[tuple[str, str]]:
    """'Away (P) @ Home (P)' -> (away_key, home_key), or None if unparseable."""
    if not name or " @ " not in name:
        return None
    away_raw, home_raw = name.split(" @ ", 1)
    away = resolve(_PAREN.sub("", away_raw).strip())
    home = resolve(_PAREN.sub("", home_raw).strip())
    if not away or not home:
        return None
    return away, home


def _american(runner: dict) -> Optional[int]:
    val = (runner.get("winRunnerOdds", {})
           .get("americanDisplayOdds", {})
           .get("americanOdds"))
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


class FanDuelSource:
    name = "fanduel"

    def __init__(self, state: str = "nj", timeout: float = 15.0):
        self.state = state
        self.timeout = aiohttp.ClientTimeout(total=timeout)

    def _parse(self, data: dict, ts: float) -> list[Quote]:
        ats = data.get("attachments", {})
        events = ats.get("events", {})
        markets = ats.get("markets", {})
        quotes: list[Quote] = []
        for m in markets.values():
            if m.get("marketType") != TOTAL_MARKET_TYPE:
                continue
            ev = events.get(str(m.get("eventId")), {})
            teams = _teams_from_name(ev.get("name", ""))
            if not teams:
                continue
            away, home = teams
            over = under = line = None
            for r in m.get("runners", []):
                rn = (r.get("runnerName") or "").lower()
                if rn == "over":
                    over = _american(r)
                    line = r.get("handicap")
                elif rn == "under":
                    under = _american(r)
            if line is None:
                continue
            # the in-play flag lives on the MARKET, not the event (the event object carries no
            # inPlay key at all — reading it there left every live FanDuel quote mislabelled
            # pregame, so the two books were never observed live together).
            quotes.append(Quote(book=self.name, home=home, away=away,
                                line=float(line), over_odds=over, under_odds=under,
                                ts=ts, live_game=bool(m.get("inPlay")),
                                status=m.get("marketStatus")))
        return quotes

    async def fetch(self, session: aiohttp.ClientSession) -> SourceResult:
        t0 = time.monotonic()
        url = URL.format(state=self.state)
        headers = rotating_headers(referer=REFERER)
        try:
            async with session.get(url, headers=headers, timeout=self.timeout) as resp:
                body = await resp.read()
                status = resp.status
                if status != 200:
                    return SourceResult(self.name, ok=False, http_status=status,
                                        latency_ms=(time.monotonic() - t0) * 1000,
                                        payload_bytes=len(body),
                                        error=f"HTTP {status}")
                data = await resp.json(content_type=None)
            quotes = self._parse(data, ts=t0)
            return SourceResult(self.name, ok=True, http_status=status,
                                latency_ms=(time.monotonic() - t0) * 1000,
                                payload_bytes=len(body), quotes=quotes)
        except Exception as exc:  # noqa: BLE001
            return SourceResult(self.name, ok=False,
                                latency_ms=(time.monotonic() - t0) * 1000,
                                error=f"{type(exc).__name__}: {exc}")
