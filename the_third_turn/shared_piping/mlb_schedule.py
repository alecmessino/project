"""Date-aware MLB schedule matching — the ONLY safe way to map odds events to game_pk.

Most MLB games are consecutive-day series (same matchup 2-4 nights running), so a
team-pair-only lookup silently tags a total with an adjacent game's game_pk. Match on
(team pair, ET schedule date): MLB schedule dates are US/Eastern, so a UTC commence
time after midnight (e.g. 01:41Z) belongs to the PREVIOUS ET date's slate.
"""

from __future__ import annotations

import json
import urllib.request
from datetime import datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from shared_piping.headers import rotating_headers
from shared_piping.team_map import resolve

SCHEDULE = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate={s}&endDate={e}"
ET = ZoneInfo("America/New_York")


def et_date(commence_iso: str) -> Optional[str]:
    """UTC commence timestamp -> the MLB (US/Eastern) schedule date."""
    if not commence_iso:
        return None
    try:
        dt = datetime.fromisoformat(str(commence_iso).replace("Z", "+00:00"))
        return dt.astimezone(ET).date().isoformat()
    except ValueError:
        return None


def pair_date_map(start: str, end: str) -> dict[tuple, int]:
    """(frozenset(away,home), schedule_date) -> game_pk over [start-1, end+1]."""
    lo = (datetime.fromisoformat(start) - timedelta(days=1)).date().isoformat()
    hi = (datetime.fromisoformat(end) + timedelta(days=1)).date().isoformat()
    req = urllib.request.Request(SCHEDULE.format(s=lo, e=hi), headers=rotating_headers())
    data = json.loads(urllib.request.urlopen(req, timeout=30).read())
    out: dict[tuple, int] = {}
    for day in data.get("dates", []):
        for g in day.get("games", []):
            a = resolve(g["teams"]["away"]["team"]["name"])
            h = resolve(g["teams"]["home"]["team"]["name"])
            if a and h:
                # doubleheaders: keep the first game of the day (best-effort)
                out.setdefault((frozenset((a, h)), day["date"]), int(g["gamePk"]))
    return out


def match_game_pk(sched: dict[tuple, int], team1: str, team2: str,
                  commence_iso: str) -> Optional[int]:
    """game_pk for a matchup at a UTC commence time. ET date first, ±1 day fallback."""
    a, b = resolve(team1), resolve(team2)
    if not a or not b:
        return None
    pair = frozenset((a, b))
    d = et_date(commence_iso)
    if d is None:
        return None
    for delta in (0, -1, 1):
        day = (datetime.fromisoformat(d) + timedelta(days=delta)).date().isoformat()
        pk = sched.get((pair, day))
        if pk is not None:
            return pk
    return None
