"""Source C — Bovada internal MLB coupon feed (game totals).

Async port of mrbet's ``bovada_feed.py`` logic, narrowed to MLB game totals. Same
undocumented endpoint the Bovada front-end calls; same caveats: schema can change,
the board is geo/Cloudflare-fronted, and this is for personal low-rate polling only.

Coupon shape: ``[{events:[{description, competitors:[{name, home}], displayGroups:[
{markets:[{key:"2W-OU", period:{abbreviation:"G"}, outcomes:[{description:"Over"/
"Under", price:{handicap, american}}]}]}]}]}]``.
"""

from __future__ import annotations

import time
from typing import Optional

import aiohttp

from shared_piping.headers import rotating_headers
from shared_piping.team_map import resolve
from sources.base import Quote, SourceResult

URL = ("https://www.bovada.lv/services/sports/event/coupon/events/A/description/"
       "baseball/mlb?marketFilterId=def&preMatchOnly=false&lang=en")
REFERER = "https://www.bovada.lv/sports/baseball/mlb"
KEY_TOTAL = "2W-OU"
FULL_GAME = "G"


def _american(price: dict) -> Optional[int]:
    raw = (price or {}).get("american")
    if raw in (None, ""):
        return None
    raw = str(raw).strip().upper()
    if raw in ("EVEN", "EV"):
        return 100
    try:
        return int(raw.replace("+", ""))
    except ValueError:
        return None


def _handicap(price: dict) -> Optional[float]:
    try:
        return float((price or {}).get("handicap"))
    except (TypeError, ValueError):
        return None


class BovadaSource:
    name = "bovada"

    def __init__(self, timeout: float = 20.0):
        self.timeout = aiohttp.ClientTimeout(total=timeout)

    def _teams(self, ev: dict) -> Optional[tuple[str, str]]:
        home = away = None
        for c in ev.get("competitors", []):
            key = resolve(c.get("name", ""))
            if c.get("home"):
                home = key
            else:
                away = key
        if not home or not away:
            return None
        return away, home

    def _parse(self, coupon: list, ts: float) -> list[Quote]:
        quotes: list[Quote] = []
        for group in coupon or []:
            for ev in group.get("events", []):
                teams = self._teams(ev)
                if not teams:
                    continue
                away, home = teams
                for dg in ev.get("displayGroups", []):
                    for m in dg.get("markets", []):
                        if m.get("key") != KEY_TOTAL:
                            continue
                        if (m.get("period", {}).get("abbreviation") or "").upper() != FULL_GAME:
                            continue
                        over = under = line = None
                        for o in m.get("outcomes", []):
                            desc = (o.get("description") or "").lower()
                            price = o.get("price", {})
                            if desc == "over":
                                over = _american(price)
                                line = _handicap(price)
                            elif desc == "under":
                                under = _american(price)
                        if line is None:
                            continue
                        quotes.append(Quote(book=self.name, home=home, away=away,
                                            line=line, over_odds=over,
                                            under_odds=under, ts=ts))
        return quotes

    async def fetch(self, session: aiohttp.ClientSession) -> SourceResult:
        t0 = time.monotonic()
        headers = rotating_headers(referer=REFERER)
        try:
            async with session.get(URL, headers=headers, timeout=self.timeout) as resp:
                body = await resp.read()
                status = resp.status
                if status != 200:
                    return SourceResult(self.name, ok=False, http_status=status,
                                        latency_ms=(time.monotonic() - t0) * 1000,
                                        payload_bytes=len(body), error=f"HTTP {status}")
                data = await resp.json(content_type=None)
            quotes = self._parse(data, ts=t0)
            return SourceResult(self.name, ok=True, http_status=status,
                                latency_ms=(time.monotonic() - t0) * 1000,
                                payload_bytes=len(body), quotes=quotes)
        except Exception as exc:  # noqa: BLE001
            return SourceResult(self.name, ok=False,
                                latency_ms=(time.monotonic() - t0) * 1000,
                                error=f"{type(exc).__name__}: {exc}")
