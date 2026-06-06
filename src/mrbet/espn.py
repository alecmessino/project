"""ESPN scoreboard/summary client for backtesting (free, no key).

Turns a finished NBA game into a `GameHistory`: the pregame baseline (derived
from ESPN's consensus total + spread), a sampled in-game score timeline (from
play-by-play), and the real period/team finals (from quarter linescores). This
is the raw material the line model + threshold sweep consume — outcomes are
*real*, only the live line is later modeled.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import requests

SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
SUMMARY = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary"


def espn_urls(league: str = "nba") -> tuple[str, str]:
    """(scoreboard, summary) ESPN endpoints for a basketball league (nba | wnba)."""
    lg = (league or "nba").lower()
    base = f"https://site.api.espn.com/apis/site/v2/sports/basketball/{lg}"
    return f"{base}/scoreboard", f"{base}/summary"

# ESPN season types: 2 = regular, 3 = postseason.
POSTSEASON = 3

CACHE_DIR = Path("data/espn_cache")


@dataclass
class TimelinePoint:
    """Cumulative score at a moment, expressed on the full-game clock."""

    minutes_elapsed: float   # full-game minutes elapsed (0..48)
    away_score: int
    home_score: int

    @property
    def total(self) -> int:
        return self.away_score + self.home_score


@dataclass
class GameHistory:
    event_id: str
    date: str                # YYYYMMDD
    away: str                # short key, e.g. "OKC"
    home: str                # short key, e.g. "SA"
    away_name: str
    home_name: str
    pregame_total: float
    pregame_spread_home: float        # negative = home favored
    timeline: list[TimelinePoint] = field(default_factory=list)
    finals: dict = field(default_factory=dict)   # {game:{full,h1,q1..q4}, team:{AWAY,HOME}}

    # ---- derived pregame baselines -------------------------------------- #
    def pregame_team_totals(self) -> dict[str, float]:
        """Split the pregame total by the spread into per-team expected points."""
        half = self.pregame_total / 2.0
        # home margin = -spread_home (home favored by |spread| when spread<0)
        margin = -self.pregame_spread_home
        return {self.home: half + margin / 2.0, self.away: half - margin / 2.0}


def _parse_clock(disp: str) -> float:
    """'10:09' -> 10.15 minutes; '0.3' / ':23' tolerated."""
    disp = (disp or "").strip()
    if ":" in disp:
        mm, ss = disp.split(":")
        return (int(mm or 0)) + (float(ss or 0) / 60.0)
    try:
        return float(disp) / 60.0
    except ValueError:
        return 0.0


def _full_elapsed(period: int, clock_min: float) -> float:
    """Full-game minutes elapsed given period number + minutes left in period."""
    reg = min(period, 4)
    # minutes elapsed in regulation; OT (period>4) clamps at 48.
    elapsed = (reg - 1) * 12 + (12 - clock_min)
    return max(0.0, min(48.0, elapsed))


class ESPNClient:
    def __init__(self, use_cache: bool = True, league: str = "nba"):
        self.use_cache = use_cache
        self.league = (league or "nba").lower()
        self.scoreboard, self.summary = espn_urls(self.league)
        if use_cache:
            CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _get(self, url: str, params: dict, cache_key: str) -> Optional[dict]:
        cache = CACHE_DIR / f"{cache_key}.json"
        if self.use_cache and cache.exists():
            return json.loads(cache.read_text())
        try:
            r = requests.get(url, params=params, timeout=25)
            r.raise_for_status()
            data = r.json()
        except (requests.RequestException, ValueError):
            return None
        if self.use_cache:
            cache.write_text(json.dumps(data))
        return data

    def playoff_game_ids(self, dates: list[str]) -> list[tuple[str, str]]:
        """Return (event_id, shortName) for completed postseason games on the dates."""
        out: list[tuple[str, str]] = []
        for d in dates:
            data = self._get(self.scoreboard, {"dates": d}, f"sb_{self.league}_{d}")
            if not data:
                continue
            for ev in data.get("events", []):
                if ev.get("season", {}).get("type") != POSTSEASON:
                    continue
                comp = (ev.get("competitions") or [{}])[0]
                if not comp.get("status", {}).get("type", {}).get("completed"):
                    continue
                out.append((ev["id"], ev.get("shortName", ev["id"])))
        return out

    def game_history(self, event_id: str) -> Optional[GameHistory]:
        data = self._get(self.summary, {"event": event_id}, f"sum_{self.league}_{event_id}")
        if not data:
            return None
        header = data.get("header", {})
        comp = (header.get("competitions") or [{}])[0]
        competitors = {c.get("homeAway"): c for c in comp.get("competitors", [])}
        home_c, away_c = competitors.get("home", {}), competitors.get("away", {})
        if not home_c or not away_c:
            return None

        pre_total, pre_spread = self._pregame_odds(data)
        if pre_total is None:
            return None  # can't backtest a total market without a pregame total

        hist = GameHistory(
            event_id=str(event_id),
            date=str(header.get("season", {}).get("year", "")),
            away=away_c.get("team", {}).get("abbreviation", "AWAY"),
            home=home_c.get("team", {}).get("abbreviation", "HOME"),
            away_name=away_c.get("team", {}).get("displayName", "Away"),
            home_name=home_c.get("team", {}).get("displayName", "Home"),
            pregame_total=pre_total,
            pregame_spread_home=pre_spread,
        )
        hist.timeline = self._timeline(data.get("plays") or [])
        hist.finals = self._finals(competitors)
        return hist if hist.timeline and hist.finals else None

    def _pregame_odds(self, data: dict) -> tuple[Optional[float], float]:
        """Pull the consensus pregame total + home spread from pickcenter/odds."""
        for block in ("pickcenter", "odds"):
            for o in (data.get(block) or []):
                ou = o.get("overUnder")
                spread = o.get("spread")
                if ou is not None:
                    try:
                        return float(ou), float(spread if spread is not None else 0.0)
                    except (TypeError, ValueError):
                        continue
        return None, 0.0

    def _timeline(self, plays: list[dict]) -> list[TimelinePoint]:
        pts: list[TimelinePoint] = []
        last_elapsed = -1.0
        for p in plays:
            period = int((p.get("period") or {}).get("number") or 0)
            if period <= 0:
                continue
            clock_min = _parse_clock((p.get("clock") or {}).get("displayValue", ""))
            elapsed = _full_elapsed(period, clock_min)
            try:
                away, home = int(p["awayScore"]), int(p["homeScore"])
            except (KeyError, TypeError, ValueError):
                continue
            # keep one (the latest) point per distinct elapsed-minute bucket
            if elapsed > last_elapsed:
                pts.append(TimelinePoint(round(elapsed, 2), away, home))
                last_elapsed = elapsed
            elif pts:
                pts[-1] = TimelinePoint(pts[-1].minutes_elapsed, away, home)
        return pts

    def _finals(self, competitors: dict) -> dict:
        home_c, away_c = competitors.get("home", {}), competitors.get("away", {})
        try:
            h = [int(float(x.get("displayValue", x.get("value", 0))))
                 for x in home_c.get("linescores", [])]
            a = [int(float(x.get("displayValue", x.get("value", 0))))
                 for x in away_c.get("linescores", [])]
        except (TypeError, ValueError):
            return {}
        if len(h) < 4 or len(a) < 4:
            return {}
        q = [h[i] + a[i] for i in range(4)]   # combined per-quarter totals
        away_key = away_c.get("team", {}).get("abbreviation", "AWAY")
        home_key = home_c.get("team", {}).get("abbreviation", "HOME")
        return {
            "game": {
                "full": sum(q), "h1": q[0] + q[1],
                "q1": q[0], "q2": q[1], "q3": q[2], "q4": q[3],
            },
            "team": {away_key: sum(a), home_key: sum(h)},
        }

    def find_completed_game(
        self, date: str, home_name: str, away_name: str
    ) -> Optional[tuple[str, str]]:
        """Return (event_id, shortName) if a completed postseason game matching
        the team names (by last word) is found on *date* (YYYYMMDD).

        Returns None if the game is not found OR if it has not yet completed —
        both cases mean the grader should skip this run.
        """
        data = self._get(self.scoreboard, {"dates": date}, f"sb_{self.league}_{date}")
        if not data:
            return None
        home_last = home_name.split()[-1].lower()
        away_last = away_name.split()[-1].lower()
        for ev in data.get("events", []):
            if ev.get("season", {}).get("type") != POSTSEASON:
                continue
            comp = (ev.get("competitions") or [{}])[0]
            competitors = comp.get("competitors", [])
            names = {c.get("team", {}).get("displayName", "").lower()
                     for c in competitors}
            if not (any(home_last in n for n in names) and
                    any(away_last in n for n in names)):
                continue
            if not comp.get("status", {}).get("type", {}).get("completed"):
                return None   # right game, not finished yet
            return ev["id"], ev.get("shortName", ev["id"])
        return None

    def fetch_finals(
        self, event_id: str
    ) -> Optional[tuple[str, str, dict]]:
        """Return (away_abbr, home_abbr, finals_dict) for a completed game.

        Unlike game_history(), does not require play-by-play to be present.
        finals_dict mirrors the structure produced by _finals().
        """
        data = self._get(self.summary, {"event": event_id}, f"sum_{self.league}_{event_id}")
        if not data:
            return None
        header = data.get("header", {})
        comp = (header.get("competitions") or [{}])[0]
        competitors = {c.get("homeAway"): c
                       for c in comp.get("competitors", [])}
        home_c = competitors.get("home", {})
        away_c = competitors.get("away", {})
        if not home_c or not away_c:
            return None
        away_abbr = away_c.get("team", {}).get("abbreviation", "AWAY")
        home_abbr = home_c.get("team", {}).get("abbreviation", "HOME")
        finals = self._finals(competitors)
        if not finals:
            return None
        return away_abbr, home_abbr, finals


def playoff_dates(start: str, end: str) -> list[str]:
    """Inclusive list of YYYYMMDD date strings between start and end."""
    from datetime import datetime, timedelta

    d0 = datetime.strptime(start, "%Y%m%d")
    d1 = datetime.strptime(end, "%Y%m%d")
    out = []
    while d0 <= d1:
        out.append(d0.strftime("%Y%m%d"))
        d0 += timedelta(days=1)
    return out
