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
import sys
import time
import urllib.request
from typing import Iterator, Optional

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

    def __init__(self, event, poll_interval: float = 60.0, max_polls: Optional[int] = 1):
        self.event = event
        self.poll_interval = poll_interval
        self.max_polls = max_polls
        self._clock: Optional[str] = None
        self._raw_event: Optional[dict] = None

    # ---- network ---------------------------------------------------------- #
    def _fetch_coupon(self) -> list:
        req = urllib.request.Request(NBA_COUPON_URL, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())

    def _find_event(self, coupon: list) -> Optional[dict]:
        """Locate our game in the coupon by matching both team names (last word)."""
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

    # ---- game state (clock/score) ---------------------------------------- #
    def _fetch_state(self) -> Optional[GameState]:
        """Live clock/score -> GameState. Returns None pre-tip or if not live.

        Mirrors the ESPN mapping verbatim:
            elapsed = (period-1)*12 + (12 - clock_remaining_min), capped at 48.
        """
        ev = self._raw_event or self._refresh()
        if not ev or not ev.get("live"):
            return None
        clock = ev.get("clock") or {}
        period_num = clock.get("periodNumber")
        if not period_num:
            return None
        # Bovada gives time REMAINING in the current quarter (may be int or str).
        try:
            mins = float(clock.get("minutes", 0) or 0)
            secs = float(clock.get("seconds", 0) or 0)
        except (TypeError, ValueError):
            mins, secs = 0.0, 0.0
        remaining_in_q = mins + secs / 60.0
        reg_period = int(period_num)
        elapsed = max(0.0, (reg_period - 1) * QUARTER_MIN + (QUARTER_MIN - remaining_in_q))
        elapsed = min(elapsed, REGULATION_MIN)
        remaining = max(0.0, REGULATION_MIN - elapsed)
        self._clock = f"Q{reg_period} {int(mins)}:{int(secs):02d}"
        away_pts, home_pts = self._scores(ev)
        return GameState(
            period=Period.FULL,
            minutes_elapsed=elapsed,
            minutes_remaining=remaining,
            home_score=home_pts,
            away_score=away_pts,
        )

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
                               meta={"source": "bovada", "clock": self._clock})
            polls += 1
            if self.max_polls is not None and polls >= self.max_polls:
                break
            time.sleep(self.poll_interval)


# --------------------------------------------------------------------------- #
# Dry run                                                                      #
# --------------------------------------------------------------------------- #
def dry_run(game_yaml: str) -> int:
    """Fetch Bovada once for the given game and print exactly what we parsed."""
    from .config import GameConfig
    game = GameConfig.load(game_yaml)
    p = BovadaProvider(game.event, max_polls=1)

    print(f"DRY RUN · {game.event.away} @ {game.event.home}  ({game.event.id})")
    print(f"endpoint: {NBA_COUPON_URL}\n")

    ev = p._refresh()
    if ev is None:
        print("❌ event not found on Bovada's NBA board (not posted yet, or fetch blocked).")
        print("   If this host is geo-blocked, run from the target environment instead.")
        return 1

    print(f"✓ matched event id={ev.get('id')}  live={ev.get('live')}  status={ev.get('status')}")
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
