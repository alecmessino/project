"""Optional fallback book — Pinnacle guest API (sharp full-game totals).

Used only when FanDuel yields nothing. Pinnacle is the sharpest public book, so it
is a good sanity reference. Two endpoints on the public "guest" API (no login):
  * /0.1/leagues/246/matchups          -> games + participants (home/away, over/under)
  * /0.1/leagues/246/markets/straight  -> prices (key "s;0;ou" = main total)

We keep only ``type=="total"``, ``period==0``, ``key=="s;0;ou"`` markets whose
``matchupId`` is a **top-level game** (derivative props like "run in the 1st,
O/U 0.5" are separate sub-matchups and are filtered out). Prices carry no explicit
over/under ``designation``; Pinnacle lists Over first, then Under (documented
best-effort ordering). Prices are already American.
"""

from __future__ import annotations

import time
from typing import Optional

import aiohttp

from shared_piping.headers import rotating_headers
from shared_piping.team_map import resolve
from sources.base import Quote, SourceResult

# Public guest key embedded in Pinnacle's own web client.
API_KEY = "CmX2KcMrXuFmNg6YFbmTxE0y9CIrOi0R"
LEAGUE_MLB = 246
MATCHUPS_URL = f"https://guest.api.arcadia.pinnacle.com/0.1/leagues/{LEAGUE_MLB}/matchups"
MARKETS_URL = f"https://guest.api.arcadia.pinnacle.com/0.1/leagues/{LEAGUE_MLB}/markets/straight"
REFERER = "https://www.pinnacle.com/"


class PinnacleSource:
    name = "pinnacle"

    def __init__(self, timeout: float = 25.0):
        self.timeout = aiohttp.ClientTimeout(total=timeout)

    def _headers(self):
        h = rotating_headers(referer=REFERER)
        h["X-API-Key"] = API_KEY
        return h

    def _game_teams(self, matchups: list) -> dict[int, tuple[str, str]]:
        """Top-level game matchupId -> (away_key, home_key)."""
        out: dict[int, tuple[str, str]] = {}
        for m in matchups:
            if m.get("parentId"):
                continue
            away = home = None
            for p in m.get("participants", []):
                key = resolve(p.get("name", ""))
                if p.get("alignment") == "home":
                    home = key
                elif p.get("alignment") == "away":
                    away = key
            if away and home:
                out[m["id"]] = (away, home)
        return out

    @staticmethod
    def _implied(american) -> Optional[float]:
        try:
            a = float(american)
        except (TypeError, ValueError):
            return None
        return (-a) / (-a + 100) if a < 0 else 100 / (a + 100)

    def _parse(self, matchups: list, markets: list, ts: float) -> list[Quote]:
        # Full-game totals live on the game matchupId, keyed ``s;0;ou;<line>`` with
        # over/under designations. Each game lists several alt lines; the MAIN line
        # is the balanced one (min |P(over) - P(under)|) — alts are heavily juiced.
        game_teams = self._game_teams(matchups)
        best: dict[int, tuple[float, Quote]] = {}  # matchupId -> (imbalance, quote)
        for mk in markets:
            if mk.get("type") != "total" or mk.get("period") != 0:
                continue
            key = mk.get("key", "")
            if not key.startswith("s;0;ou;"):  # the ;<line> suffix = full-game total
                continue
            teams = game_teams.get(mk.get("matchupId"))
            if not teams:
                continue
            away, home = teams
            over = under = line = None
            for p in mk.get("prices", []):
                if p.get("designation") == "over":
                    over, line = p.get("price"), p.get("points")
                elif p.get("designation") == "under":
                    under = p.get("price")
            if line is None or over is None or under is None:
                continue
            po, pu = self._implied(over), self._implied(under)
            imbalance = abs(po - pu) if (po is not None and pu is not None) else 1.0
            q = Quote(book=self.name, home=home, away=away, line=float(line),
                      over_odds=over, under_odds=under, ts=ts)
            mid = mk["matchupId"]
            if mid not in best or imbalance < best[mid][0]:
                best[mid] = (imbalance, q)
        return [q for _, q in best.values()]

    async def _get(self, session: aiohttp.ClientSession, url: str):
        async with session.get(url, headers=self._headers(), timeout=self.timeout) as resp:
            body = await resp.read()
            if resp.status != 200:
                raise aiohttp.ClientResponseError(resp.request_info, resp.history,
                                                  status=resp.status, message=f"HTTP {resp.status}")
            return await resp.json(content_type=None), len(body)

    async def fetch(self, session: aiohttp.ClientSession) -> SourceResult:
        t0 = time.monotonic()
        try:
            matchups, b1 = await self._get(session, MATCHUPS_URL)
            markets, b2 = await self._get(session, MARKETS_URL)
            quotes = self._parse(matchups, markets, ts=t0)
            return SourceResult(self.name, ok=True, http_status=200,
                                latency_ms=(time.monotonic() - t0) * 1000,
                                payload_bytes=b1 + b2, quotes=quotes)
        except aiohttp.ClientResponseError as exc:
            return SourceResult(self.name, ok=False, http_status=exc.status,
                                latency_ms=(time.monotonic() - t0) * 1000, error=str(exc))
        except Exception as exc:  # noqa: BLE001
            return SourceResult(self.name, ok=False,
                                latency_ms=(time.monotonic() - t0) * 1000,
                                error=f"{type(exc).__name__}: {exc}")
