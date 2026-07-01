"""Source A — MLB Stats API: live game state, pitch counts, lineup spot, TTO.

Public, documented-ish endpoints (no key, no bot-blocking):
  * schedule:  /api/v1/schedule?sportId=1&date=YYYY-MM-DD
  * live feed: /api/v1.1/game/{gamePk}/feed/live

From the live feed we read, per in-progress game:
  * inning / half           (liveData.linescore)
  * current pitcher + id    (linescore.defense.pitcher)
  * pitch count             (boxscore ... pitching.numberOfPitches)
  * batter due up + slot    (linescore.offense.batter -> index in battingOrder)
  * times-through-order      derived: the due batter starts PA number
                             ``battersFaced + 1`` for this pitcher, so
                             ``TTO = ceil((BF + 1) / 9)`` assuming order (true for a
                             starter from the 1st inning; documented assumption).

All parsing is defensive: a missing/renamed field yields ``None`` for that datum,
never an exception past ``fetch``.
"""

from __future__ import annotations

import math
import time
from typing import Optional

import aiohttp

from shared_piping.headers import rotating_headers
from shared_piping.team_map import resolve
from sources.base import LiveGameState, SourceResult

SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date}"
FEED_URL = "https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"
REFERER = "https://www.mlb.com/"
LINEUP_SIZE = 9


class MLBStatsSource:
    """Fetches live states for all in-progress MLB games on a given date."""

    name = "mlb_statsapi"

    def __init__(self, date: str, *, live_only: bool = True, timeout: float = 15.0,
                 starter_tiers: Optional[dict] = None):
        self.date = date
        self.live_only = live_only
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        # pitcher MLBAM id -> "Ace"/"Mid"/"Back" (from build_reference.py); optional.
        self.starter_tiers = {int(k): v for k, v in (starter_tiers or {}).items()}

    async def _get_json(self, session: aiohttp.ClientSession, url: str):
        headers = rotating_headers(referer=REFERER)
        async with session.get(url, headers=headers, timeout=self.timeout) as resp:
            resp.raise_for_status()
            return await resp.json(content_type=None), resp.status

    async def _game_pks(self, session: aiohttp.ClientSession) -> tuple[list[int], int]:
        data, status = await self._get_json(session, SCHEDULE_URL.format(date=self.date))
        pks: list[int] = []
        for day in data.get("dates", []):
            for g in day.get("games", []):
                state = g.get("status", {}).get("abstractGameState", "")
                if self.live_only and state != "Live":
                    continue
                pks.append(int(g["gamePk"]))
        return pks, status

    def _parse_feed(self, feed: dict) -> Optional[LiveGameState]:
        game = feed.get("gameData", {})
        live = feed.get("liveData", {})
        teams = game.get("teams", {})
        away = resolve(teams.get("away", {}).get("name", "")) or "?"
        home = resolve(teams.get("home", {}).get("name", "")) or "?"
        game_pk = int(game.get("game", {}).get("pk") or feed.get("gamePk") or 0)
        status = game.get("status", {}).get("abstractGameState", "")

        ls = live.get("linescore", {})
        inning = int(ls.get("currentInning") or 0)
        half = (ls.get("inningHalf") or ls.get("inningState") or "").lower()
        is_top = "top" in half
        ls_teams = ls.get("teams", {})
        away_score = int(ls_teams.get("away", {}).get("runs") or 0)
        home_score = int(ls_teams.get("home", {}).get("runs") or 0)

        defense = ls.get("defense", {})
        offense = ls.get("offense", {})
        pitcher = defense.get("pitcher") or {}
        pitcher_id = pitcher.get("id")
        pitcher_name = pitcher.get("fullName")

        # outs + base occupancy (RE24 inputs). Base keys appear only when occupied.
        cur = live.get("plays", {}).get("currentPlay", {})
        outs = ls.get("outs")
        if outs is None:
            outs = cur.get("count", {}).get("outs")
        outs = int(outs) if outs is not None else None
        on_first = "first" in offense
        on_second = "second" in offense
        on_third = "third" in offense

        # pitch count + battersFaced from the boxscore for the current pitcher.
        pitch_count = batters_faced = None
        box = live.get("boxscore", {}).get("teams", {})
        # The fielding (pitching) team is home in the top half, away in the bottom.
        pitching_side = "home" if is_top else "away"
        if pitcher_id is not None:
            side_box = box.get(pitching_side, {})
            pdata = side_box.get("players", {}).get(f"ID{pitcher_id}", {})
            pstats = pdata.get("stats", {}).get("pitching", {})
            pitch_count = pstats.get("numberOfPitches")
            batters_faced = pstats.get("battersFaced")

        # batting slot of the due batter = index in the offense team's order.
        slot = tto = None
        due_id = (offense.get("batter") or {}).get("id")
        batting_side = "away" if is_top else "home"
        order = box.get(batting_side, {}).get("battingOrder", []) or []
        if due_id is not None and due_id in order:
            slot = order.index(due_id) + 1
        if batters_faced is not None:
            # due batter starts PA number BF+1 for this pitcher.
            pa_number = int(batters_faced) + 1
            tto = math.ceil(pa_number / LINEUP_SIZE)
            if slot is None:
                slot = ((pa_number - 1) % LINEUP_SIZE) + 1

        # starting pitcher (this side) = first entry in the boxscore pitcher list;
        # if a reliever is already on, the TTOP thesis is void (Fix #4).
        pitchers_used = box.get(pitching_side, {}).get("pitchers", []) or []
        starter_id = int(pitchers_used[0]) if pitchers_used else pitcher_id
        starter_on_mound = (pitcher_id == starter_id) if pitcher_id is not None else True
        starter_tier = self.starter_tiers.get(int(starter_id), "Unknown") if starter_id else "Unknown"

        return LiveGameState(
            game_pk=game_pk, away=away, home=home, inning=inning,
            half="top" if is_top else "bottom", away_score=away_score,
            home_score=home_score, pitcher_id=pitcher_id, pitcher_name=pitcher_name,
            pitch_count=int(pitch_count) if pitch_count is not None else None,
            batting_slot_due=slot, times_through_order=tto, status=status,
            outs=outs, on_first=on_first, on_second=on_second, on_third=on_third,
            starter_id=starter_id, starter_on_mound=starter_on_mound,
            starter_tier=starter_tier,
        )

    async def fetch(self, session: aiohttp.ClientSession) -> SourceResult:
        t0 = time.monotonic()
        try:
            pks, sched_status = await self._game_pks(session)
            states: list[LiveGameState] = []
            total_bytes = 0
            for pk in pks:
                try:
                    feed, _ = await self._get_json(session, FEED_URL.format(game_pk=pk))
                    total_bytes += len(str(feed))
                    st = self._parse_feed(feed)
                    if st is not None:
                        states.append(st)
                except Exception:  # one bad game must not sink the source
                    continue
            return SourceResult(
                name=self.name, ok=True, http_status=sched_status,
                latency_ms=(time.monotonic() - t0) * 1000, payload_bytes=total_bytes,
                states=states,
            )
        except aiohttp.ClientResponseError as exc:
            return SourceResult(self.name, ok=False, http_status=exc.status,
                                latency_ms=(time.monotonic() - t0) * 1000, error=str(exc))
        except Exception as exc:  # noqa: BLE001
            return SourceResult(self.name, ok=False,
                                latency_ms=(time.monotonic() - t0) * 1000,
                                error=f"{type(exc).__name__}: {exc}")
