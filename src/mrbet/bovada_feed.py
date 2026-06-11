"""Bovada live NBA odds adapter -> mrbet GameState + MarketLines.

Bovada has NO official/public API. This pulls its INTERNAL coupon JSON — the same
undocumented endpoint the site's own front-end calls. Treat it accordingly:

  * Schema is undocumented and can change without notice.
  * Bovada is geo-restricted and Cloudflare-fronted; a datacenter/CI IP may be
    blocked even though it works from a residential IP. Always run the dry run
    (``python -m mrbet.bovada_feed --game <yaml> --dry-run``) from the target host
    before trusting it.
  * Respect Bovada's Terms of Service; this is for personal, low-rate polling.

Design: this implements the same ``OddsProvider`` surface as ``theodds.py`` —
``_fetch_state()`` (clock/score -> GameState) and ``_fetch_lines()`` (MarketLines)
— so the existing Engine + DashboardState produce ``docs/state.json`` UNCHANGED.
The clock->GameState math is copied verbatim from the ESPN path so the Pace
Tracker (reversion.projected_final) behaves identically.

VALIDATION STATUS (2026-06-02):
  * Pre-match parsing (Total / Spread / Moneyline, team-total derivation): VERIFIED
    against the live Bovada board (Finals G1).
  * Live clock + live score parsing: CODED to Bovada's known in-play schema but
    NOT yet verified against a live game (none was in-play at build time). The dry
    run prints exactly what it sees so you can confirm on the first live tip.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from typing import Iterator, Optional

from .espn import live_h1_final
from .models import GameState, MarketLine, MarketType, Period
from .odds.base import Snapshot

NBA_COUPON_URL = (
    "https://www.bovada.lv/services/sports/event/coupon/events/A/description/"
    "basketball/nba?marketFilterId=def&preMatchOnly=false&lang=en"
)
# Browser-like headers — Bovada rejects default urllib/curl user agents.
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.bovada.lv/sports/basketball/nba",
}

QUARTER_MIN = 12.0
REGULATION_MIN = 48.0

# Per-league dimensions. NBA = 4x12min; WNBA = 4x10min. The coupon path differs
# only by the sport slug. Add a league here to support it everywhere.
LEAGUES = {
    "nba": {
        "slug": "nba",
        "quarter_min": 12.0,
        "regulation_min": 48.0,
        "referer": "https://www.bovada.lv/sports/basketball/nba",
    },
    "wnba": {
        "slug": "wnba",
        "quarter_min": 10.0,
        "regulation_min": 40.0,
        "referer": "https://www.bovada.lv/sports/basketball/wnba",
    },
}


def _coupon_url(slug: str) -> str:
    return ("https://www.bovada.lv/services/sports/event/coupon/events/A/description/"
            f"basketball/{slug}?marketFilterId=def&preMatchOnly=false&lang=en")


# Live clock + score live here, NOT in the coupon (the coupon omits the game clock
# for in-play games — that was the WNBA verification failure).
def _scores_url(event_id) -> str:
    return f"https://www.bovada.lv/services/sports/results/api/v1/scores/{event_id}"


# AllOrigins is a free CORS/proxy that fetches a URL server-side — a geo-block
# escape hatch. BOVADA_PROXY: "" = direct-first then proxy fallback (default),
# "allorigins" = force proxy, "off"/"none" = direct only.
def _allorigins(url: str) -> str:
    return "https://api.allorigins.win/raw?url=" + urllib.parse.quote(url, safe="")


def _http_get_json(url: str, referer: str):
    """GET JSON, trying direct then the AllOrigins proxy (per BOVADA_PROXY)."""
    headers = {**HEADERS, "Referer": referer}
    mode = os.environ.get("BOVADA_PROXY", "").lower().strip()
    if mode == "allorigins":
        attempts = [("allorigins", _allorigins(url))]
    elif mode in ("off", "none", "direct"):
        attempts = [("direct", url)]
    else:                                   # default: direct first, proxy fallback
        attempts = [("direct", url), ("allorigins", _allorigins(url))]
    for name, u in attempts:
        try:
            req = urllib.request.Request(u, headers=headers)
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.loads(r.read())
        except Exception as exc:            # network / geo-block / schema
            print(f"[bovada] {name} fetch failed: {type(exc).__name__}: {exc}", file=sys.stderr)
    return None

# Bovada market keys (period abbreviation distinguishes game vs half).
KEY_TOTAL = "2W-OU"      # Over/Under
KEY_SPREAD = "2W-HCAP"   # Point spread
KEY_MONEYLINE = "2W-12"


# --------------------------------------------------------------------------- #
# Small parse helpers                                                         #
# --------------------------------------------------------------------------- #
def _american(price: dict) -> Optional[int]:
    """Bovada price.american -> int. Handles '+165', '-110', 'EVEN', strings."""
    if not price:
        return None
    raw = price.get("american")
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
    if not price:
        return None
    h = price.get("handicap")
    try:
        return float(h)
    except (TypeError, ValueError):
        return None


def _period_from_abbrev(abbrev: str) -> Optional[Period]:
    """Map Bovada market period abbreviation -> mrbet Period (totals we track)."""
    a = (abbrev or "").upper()
    return {
        "G": Period.FULL,
        "1H": Period.H1, "H1": Period.H1,
        "2H": Period.H2, "H2": Period.H2,
        "1Q": Period.Q1, "Q1": Period.Q1,
        "2Q": Period.Q2, "Q2": Period.Q2,
        "3Q": Period.Q3, "Q3": Period.Q3,
        "4Q": Period.Q4, "Q4": Period.Q4,
    }.get(a)


# --------------------------------------------------------------------------- #
# The provider                                                                #
# --------------------------------------------------------------------------- #
class BovadaProvider:
    """Streams Snapshots for one event off Bovada's internal NBA coupon feed.

    `event` is the mrbet game-config event (needs .away, .home, .away_key,
    .home_key) so we can locate the right game and key team totals.
    """

    def __init__(self, event, league: str = "nba", poll_interval: float = 60.0,
                 max_polls: Optional[int] = 1):
        self.event = event
        self.league = league.lower()
        cfg = LEAGUES.get(self.league, LEAGUES["nba"])
        self.quarter_min = cfg["quarter_min"]
        self.regulation_min = cfg["regulation_min"]
        self.coupon_url = _coupon_url(cfg["slug"])
        self._referer = cfg["referer"]
        self.poll_interval = poll_interval
        self.max_polls = max_polls
        self._clock: Optional[str] = None
        self._raw_event: Optional[dict] = None
        self._stage: str = "pre"   # auto-detected: "pre" -> "live" -> "final"
        self._h1: Optional[tuple[int, int]] = None   # settled (away_h1, home_h1)

    # ---- network ---------------------------------------------------------- #
    def _fetch_coupon(self) -> list:
        data = _http_get_json(self.coupon_url, self._referer)
        if data is None:
            raise RuntimeError("coupon fetch failed (direct + proxy)")
        return data

    def _fetch_scores(self, event_id) -> Optional[dict]:
        """Live clock + score from Bovada's scores endpoint (proxy-aware)."""
        if not event_id:
            return None
        return _http_get_json(_scores_url(event_id), self._referer)

    def _bovada_id(self) -> Optional[str]:
        """The configured Bovada numeric event id, if any (deterministic mapping)."""
        bid = getattr(self.event, "bovada_event_id", None)
        return str(bid) if bid else None

    def _find_event(self, coupon: list) -> Optional[dict]:
        """Locate our game in the coupon.

        Prefer an exact match on the configured Bovada numeric event id (set in the
        game YAML) so mapping is deterministic; fall back to fuzzy team-name match.
        """
        want_id = self._bovada_id()
        if want_id:
            for group in coupon or []:
                for ev in group.get("events", []):
                    if str(ev.get("id")) == want_id:
                        return ev
        home_tag = self.event.home.split()[-1].lower()
        away_tag = self.event.away.split()[-1].lower()
        for group in coupon or []:
            for ev in group.get("events", []):
                names = " ".join(c.get("name", "") for c in ev.get("competitors", [])).lower()
                desc = ev.get("description", "").lower()
                hay = names + " " + desc
                if home_tag in hay and away_tag in hay:
                    return ev
        return None

    def _refresh(self) -> Optional[dict]:
        try:
            coupon = self._fetch_coupon()
        except Exception as exc:  # network / geo-block / schema
            print(f"[bovada] fetch failed: {type(exc).__name__}: {exc}", file=sys.stderr)
            return None
        self._raw_event = self._find_event(coupon)
        return self._raw_event

    # ---- pre/live/final auto-detection ----------------------------------- #
    def _classify_stage(self, ev: dict) -> str:
        """Classify an event as 'pre', 'live', or 'final' from MULTIPLE signals.

        Bovada's `live` boolean can lag the actual tip by a minute or more, so we
        treat the game as live the moment ANY independent signal appears:
          * a running clock (clock.periodNumber present), or
          * a non-null / non-zero score, or
          * a status that has moved off 'U' (unstarted) to an in-play code, or
          * the explicit `live` flag.
        Final is detected from end-of-game status/flags so we don't re-arm.
        """
        status = str(ev.get("status") or "").upper()
        clock = ev.get("clock") or {}
        away, home = self._scores(ev)
        has_score = (away + home) > 0
        has_clock = bool(clock.get("periodNumber"))

        if status in ("F", "FT", "ENDED", "FINAL") or ev.get("gameEnded") or ev.get("finalized"):
            return "final"
        if ev.get("live") or has_clock or has_score or (status and status not in ("U", "")):
            return "live"
        return "pre"

    def detect_mode(self, ev: Optional[dict] = None) -> str:
        """Auto-detect and latch the current stage; logs the pre->live flip once.

        This is the single source of truth for 'are we live?'. Call it (or read
        `self._stage`) instead of trusting `ev['live']` directly.
        """
        ev = ev if ev is not None else (self._raw_event or self._refresh())
        if ev is None:
            return self._stage   # no data this poll — keep the last known stage
        new = self._classify_stage(ev)
        # Monotonic latch: a game only moves forward pre -> live -> final. This
        # stops one stale/odd poll from reverting us (e.g. live -> pre).
        rank = {"pre": 0, "live": 1, "final": 2}
        if rank[new] > rank[self._stage]:
            prev, self._stage = self._stage, new
            if prev == "pre" and new == "live":
                away, home = self._scores(ev)
                pn = (ev.get("clock") or {}).get("periodNumber")
                print(f"[bovada] AUTO-DETECT: {self.event.away_key}@{self.event.home_key} "
                      f"PRE->LIVE (score {away}-{home}, period {pn}, "
                      f"live_flag={ev.get('live')}, status={ev.get('status')})",
                      file=sys.stderr)
        return self._stage

    def is_live(self) -> bool:
        """True once the game has been auto-detected as in-play."""
        return self.detect_mode() == "live"

    # ---- game state (clock/score) ---------------------------------------- #
    def _fetch_state(self) -> Optional[GameState]:
        """Live clock/score -> GameState, sourced from the SCORES endpoint.

        The coupon omits the in-play clock, so we read clock+score from
        /services/sports/results/api/v1/scores/{id}. Returns None until the game
        is actually IN_PROGRESS with a ticking clock. Mapping (league-aware):
            elapsed = (periodNumber-1)*quarter + (quarter - gameTime_remaining)
        """
        ev = self._raw_event or self._refresh()
        # Prefer the configured Bovada id so the live clock can be polled even if a
        # transient coupon miss left us without the matched event this cycle.
        event_id = self._bovada_id() or (ev.get("id") if ev else None)
        if not event_id:
            return None
        sc = self._fetch_scores(event_id)
        if not sc:
            return None
        status = str(sc.get("gameStatus", "")).upper()
        clock = sc.get("clock") or {}
        period_num = int(clock.get("periodNumber") or 0)

        if status in ("GAME_END", "FINAL", "ENDED", "COMPLETE"):
            self._stage = "final"
            return None
        # Truly live only when the scores feed has a real period + ticking clock.
        ticking = bool(clock.get("isTicking")) or (clock.get("relativeGameTimeInSecs", -1) or -1) >= 0
        if period_num < 1 or status == "PRE_GAME" or not (status == "IN_PROGRESS" or ticking):
            print(f"[bovada] not in-play yet (status={status or 'n/a'}, "
                  f"period={period_num}, ticking={ticking}) — awaiting live clock",
                  file=sys.stderr)
            return None

        # gameTime is time REMAINING in the current period, "M:SS".
        gt = str(clock.get("gameTime") or "0:00")
        try:
            mm, ss = (gt.split(":") + ["0"])[:2]
            mins, secs = float(mm or 0), float(ss or 0)
        except (TypeError, ValueError):
            mins, secs = 0.0, 0.0
        remaining_in_q = mins + secs / 60.0
        q = self.quarter_min
        elapsed = max(0.0, (period_num - 1) * q + (q - remaining_in_q))
        elapsed = min(elapsed, self.regulation_min)
        remaining = max(0.0, self.regulation_min - elapsed)
        self._clock = f"Q{period_num} {int(mins)}:{int(secs):02d}"

        ls = sc.get("latestScore") or {}
        try:
            away_pts = int(ls.get("visitor", 0) or 0)
            home_pts = int(ls.get("home", 0) or 0)
        except (TypeError, ValueError):
            away_pts = home_pts = 0
        if self._stage == "pre":            # latch forward now that we're truly live
            self._stage = "live"
        h1_away, h1_home = self._h1_final(elapsed)
        return GameState(
            period=Period.FULL,
            minutes_elapsed=elapsed,
            minutes_remaining=remaining,
            home_score=home_pts,
            away_score=away_pts,
            h1_home=h1_home,
            h1_away=h1_away,
        )

    def _h1_final(self, elapsed: float) -> tuple[Optional[int], Optional[int]]:
        """Settled (away_h1, home_h1), or (None, None) until known.

        Bovada's scores endpoint only carries a cumulative score, so the H1-final
        needed to derive live 2nd-half (H2) markets comes from ESPN's free
        scoreboard. Fetched once the clock is past halftime, then cached — it
        never changes after Q2 closes.
        """
        if self._h1 is None and elapsed >= self.regulation_min / 2.0:
            away_words = (self.event.away or "").split()
            home_words = (self.event.home or "").split()
            if away_words and home_words:
                self._h1 = live_h1_final(self.league, away_words[-1], home_words[-1])
        return self._h1 if self._h1 else (None, None)

    def _scores(self, ev: dict) -> tuple[int, int]:
        """Best-effort live score (away, home). Bovada exposes score in-play."""
        score = ev.get("score") or {}
        # Common shapes: {"home": "55", "away": "60"} or nested under competitors.
        try:
            if "home" in score or "away" in score:
                return int(score.get("away", 0) or 0), int(score.get("home", 0) or 0)
        except (TypeError, ValueError):
            pass
        away = home = 0
        for c in ev.get("competitors", []):
            try:
                pts = int(c.get("score", 0) or 0)
            except (TypeError, ValueError):
                pts = 0
            if c.get("home"):
                home = pts
            else:
                away = pts
        return away, home

    # ---- lines ------------------------------------------------------------ #
    def _fetch_lines(self) -> list[MarketLine]:
        ev = self._raw_event or self._refresh()
        if not ev:
            return []
        lines: list[MarketLine] = []
        game_total: Optional[float] = None
        home_spread: Optional[float] = None

        for dg in ev.get("displayGroups", []):
            for m in dg.get("markets", []):
                key = m.get("key")
                period = _period_from_abbrev(m.get("period", {}).get("abbreviation"))
                if key == KEY_TOTAL and period is not None:
                    ml = self._total_line(m, period)
                    if ml:
                        lines.append(ml)
                        if period is Period.FULL:
                            game_total = ml.line
                elif key == KEY_SPREAD and _period_from_abbrev(
                        m.get("period", {}).get("abbreviation")) is Period.FULL:
                    home_spread = self._home_spread(m)

        # Bovada rarely posts explicit team totals pre-match; derive from
        # total +/- spread so the team-total markets are always populated.
        if game_total is not None and home_spread is not None and not any(
                l.market_type is MarketType.TEAM_TOTAL for l in lines):
            lines.extend(self._derived_team_totals(game_total, home_spread))
        return lines

    def _total_line(self, market: dict, period: Period) -> Optional[MarketLine]:
        over = under = None
        for o in market.get("outcomes", []):
            if o.get("description", "").lower() == "over":
                over = o
            elif o.get("description", "").lower() == "under":
                under = o
        if not over or not under:
            return None
        line = _handicap(over.get("price", {}))
        oo, uo = _american(over.get("price", {})), _american(under.get("price", {}))
        if line is None or oo is None or uo is None:
            return None
        return MarketLine(MarketType.GAME_TOTAL, period, line, oo, uo)

    def _home_spread(self, market: dict) -> Optional[float]:
        for o in market.get("outcomes", []):
            name = o.get("description", "")
            if self.event.home.split()[-1].lower() in name.lower():
                return _handicap(o.get("price", {}))
        return None

    def _derived_team_totals(self, total: float, home_spread: float) -> list[MarketLine]:
        # home_pts = (total - home_spread)/2 ; away_pts = (total + home_spread)/2
        home_tt = round((total - home_spread) / 2.0 * 2) / 2.0   # round to nearest 0.5
        away_tt = round((total + home_spread) / 2.0 * 2) / 2.0
        return [
            MarketLine(MarketType.TEAM_TOTAL, Period.FULL, home_tt, -110, -110,
                       team=self.event.home_key),
            MarketLine(MarketType.TEAM_TOTAL, Period.FULL, away_tt, -110, -110,
                       team=self.event.away_key),
        ]

    # ---- provider protocol ----------------------------------------------- #
    def credits_remaining(self) -> Optional[int]:
        return None   # Bovada is unmetered — no credit budget to track.

    def snapshots(self) -> Iterator[Snapshot]:
        polls = 0
        while self.max_polls is None or polls < self.max_polls:
            self._refresh()
            state = self._fetch_state()
            if state is not None:
                yield Snapshot(state=state, lines=self._fetch_lines(),
                               meta={"source": "bovada", "clock": self._clock,
                                     "stage": self._stage})
            polls += 1
            if self.max_polls is not None and polls >= self.max_polls:
                break
            time.sleep(self.poll_interval)


# --------------------------------------------------------------------------- #
# Board discovery (enumerate a whole league's slate, no game YAML needed)      #
# --------------------------------------------------------------------------- #
from types import SimpleNamespace   # noqa: E402


def _team_key(name: str) -> str:
    """Cheap, stable 3-letter-ish key from a team name (display/grouping only)."""
    last = (name or "").split()[-1]
    return last[:3].upper() if last else "???"


def event_from_bovada(raw: dict) -> SimpleNamespace:
    """Build the minimal event object BovadaProvider needs from a raw Bovada event."""
    home = away = ""
    for c in raw.get("competitors", []):
        if c.get("home"):
            home = c.get("name", "")
        else:
            away = c.get("name", "")
    return SimpleNamespace(
        id=str(raw.get("id", "")), away=away, home=home,
        away_key=_team_key(away), home_key=_team_key(home),
    )


def board_events(league: str = "nba") -> list[dict]:
    """Fetch a league's whole coupon and return its raw event dicts (may be [])."""
    p = BovadaProvider(SimpleNamespace(home="", away="", home_key="", away_key=""),
                       league=league, max_polls=1)
    try:
        coupon = p._fetch_coupon()
    except Exception as exc:
        print(f"[bovada] board fetch failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return []
    return [e for g in (coupon or []) for e in g.get("events", [])]


# --------------------------------------------------------------------------- #
# Dry run                                                                      #
# --------------------------------------------------------------------------- #
def dry_run(game_yaml: str) -> int:
    """Fetch Bovada once for the given game and print exactly what we parsed."""
    from .config import GameConfig
    game = GameConfig.load(game_yaml)
    p = BovadaProvider(game.event, max_polls=1)

    print(f"DRY RUN · {game.event.away} @ {game.event.home}  ({game.event.id})")
    print(f"endpoint: {p.coupon_url}\n")

    ev = p._refresh()
    if ev is None:
        print("❌ event not found on Bovada's NBA board (not posted yet, or fetch blocked).")
        print("   If this host is geo-blocked, run from the target environment instead.")
        return 1

    stage = p.detect_mode(ev)
    print(f"✓ matched event id={ev.get('id')}  live={ev.get('live')}  "
          f"status={ev.get('status')}  auto-detected stage={stage.upper()}")
    state = p._fetch_state()
    if state is None:
        print("  clock: not in-play yet (pre-match) — live GameState available once tipped.")
    else:
        print(f"  clock: {p._clock} | elapsed {state.minutes_elapsed:.1f}m | "
              f"remaining {state.minutes_remaining:.1f}m | score "
              f"{game.event.away_key} {state.away_score}-{state.home_score} {game.event.home_key}")

    lines = p._fetch_lines()
    if not lines:
        print("  no totals parsed.")
    else:
        print(f"  parsed {len(lines)} market line(s):")
        for ml in lines:
            tag = ml.team or "GAME"
            print(f"    {ml.market_type.value:11} {ml.period.value:4} {tag:4} "
                  f"line={ml.line:<6} O {ml.over_odds:+} / U {ml.under_odds:+}")
    print("\nNote: live clock/score parsing is unvalidated until a real in-play game; "
          "re-run --dry-run at tip to confirm before trusting live output.")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Bovada NBA odds adapter")
    ap.add_argument("--game", required=True, help="path to a config/games/*.yaml")
    ap.add_argument("--dry-run", action="store_true", help="fetch once and print what we see")
    args = ap.parse_args(argv)
    if args.dry_run:
        return dry_run(args.game)
    print("Nothing to do without --dry-run yet (provider is import-ready for the engine).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
