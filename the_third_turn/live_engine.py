#!/usr/bin/env python3
"""OBJECTIVE 2 — The Third Turn live execution engine (headless async daemon).

Polls three sources concurrently every ``poll_interval`` over one aiohttp session
(MLB Stats API state + FanDuel/Bovada odds, Pinnacle fallback) and evaluates a LIST
of independent trigger rules against each live game (Revision 3):

  * TTO rules (kind="tto") fire ARM (look-ahead) + CONFIRM, and post to Discord.
      - ARM      : 2 outs, 8/9 hitter up, top-of-order target turn leads off next inning
      - CONFIRM  : the top-of-order target turn is at bat now
    Rules match ``times_through_order`` EXACTLY, so a TTO2 rule and a TTO3 rule never
    overlap — a Mid starter can fire both (2nd turn and 3rd turn) as distinct bets.
  * A WATCH rule (kind="watch") — the opt-in low-scoring game-script heuristic — logs
    to console with a [WATCH_RULE] prefix and NEVER posts to Discord.

Every fired signal (CONFIRM/ARM/WATCH) is appended to the JSONL ledger for post-season
hit-rate analysis. Each alert also carries the MLB feed's data age (latency check).

Common gates for every rule: starter still on the mound, fielding bullpen not elite,
and the live total below the RE24 expected-final anchor by the rule's edge margin.

    python the_third_turn/live_engine.py            # daemon
    python the_third_turn/live_engine.py --once     # single poll, then exit (dry run)
"""

from __future__ import annotations

import argparse
import asyncio
import os
import signal
import statistics
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

import aiohttp  # noqa: E402
from rich.console import Console  # noqa: E402

from config import Constraints, EngineSettings, TriggerRule  # noqa: E402
from shared_piping.ledger import Ledger  # noqa: E402
from shared_piping.notify import DiscordNotifier, data_age_label, pull_risk_label  # noqa: E402
from shared_piping.run_expectancy import RunEnvAnchor, expected_final_total  # noqa: E402
from shared_piping.team_map import resolve  # noqa: E402
from sources.base import LiveGameState, Quote  # noqa: E402
from sources.bovada import BovadaSource  # noqa: E402
from sources.fanduel import FanDuelSource  # noqa: E402
from sources.mlb_statsapi import MLBStatsSource  # noqa: E402
from sources.pinnacle import PinnacleSource  # noqa: E402

console = Console()


@dataclass
class Trigger:
    """A fired signal: the rule, state, market, and run-env model that cleared it."""

    trigger_type: str        # "CONFIRM" | "ARM" | "WATCH"
    rule_name: str
    game_key: str
    state: LiveGameState
    quote: Quote
    pregame_total: float
    live_total: float
    anchor: RunEnvAnchor
    bullpen_ra9: Optional[float]
    reasons: list[str]

    @property
    def edge(self) -> float:
        return self.anchor.expected_final - self.live_total

    @property
    def dedupe_key(self) -> str:
        s = self.state
        return f"{self.trigger_type}:{self.rule_name}:{self.game_key}:{s.pitcher_id}:{s.inning}:{s.half}"


def _pitching_team(state: LiveGameState) -> str:
    """Fielding (pitching) team key: home pitches in the top half, away in the bottom."""
    return state.home if state.half == "top" else state.away


def merge_quotes(*result_lists: list[Quote]) -> dict[str, Quote]:
    """One quote per game_key; an IN-PLAY quote always beats a pregame one.

    Books list the same matchup for TOMORROW's series game under the same key —
    without the live preference, a pregame line for the next game could be read as
    today's live total.
    """
    merged: dict[str, Quote] = {}
    for quotes in result_lists:
        for q in quotes:
            cur = merged.get(q.game_key)
            if cur is None or (q.live_game and not cur.live_game):
                merged[q.game_key] = q
    return merged


def verification_verdict(fair: float, verified_line: float, min_edge: float) -> tuple[float, bool]:
    """(verified_edge, suppress?) — the alert dies if the REAL betable line kills the edge.

    Scraped in-play feeds can serve stale totals (observed: Bovada coupon 8.5 while
    every betable book sat 9.5-10.5). The trigger edge is recomputed against the
    verified consensus; if it no longer clears the gate, the alert is suppressed.
    """
    v_edge = fair - verified_line
    return round(v_edge, 2), v_edge < min_edge


class LineVerifier:
    """Fire-time line verification against REAL betable books (The Odds API).

    One credit per refresh, cached ``ttl`` seconds so multiple fires in a poll share
    a call — used only when an alert is about to post, so cost is a few credits per
    game night. Only games already commenced are indexed (excludes the next series
    game's pregame listing under the same matchup).
    """

    URL = ("https://api.the-odds-api.com/v4/sports/baseball_mlb/odds"
           "?apiKey={key}&regions=us&markets=totals&oddsFormat=american")

    def __init__(self, api_key: str, ttl: float = 60.0, daily_cap: int = 25):
        self.key = api_key
        self.ttl = ttl
        self.daily_cap = daily_cap        # hard credit budget per (ET) day
        self.fetches_today = 0
        self._day = None
        self.credits_remaining: Optional[str] = None
        self._board: Optional[dict] = None
        self._at = 0.0

    def _budget_ok(self) -> bool:
        from zoneinfo import ZoneInfo
        day = datetime.now(ZoneInfo("America/New_York")).date()
        if day != self._day:
            self._day, self.fetches_today = day, 0
        return self.fetches_today < self.daily_cap

    @staticmethod
    def parse_board(data: list) -> dict[str, dict]:
        """game_key -> {median, books} for COMMENCED games only."""
        out: dict[str, dict] = {}
        now = datetime.now(timezone.utc)
        for e in data if isinstance(data, list) else []:
            try:
                commenced = datetime.fromisoformat(
                    str(e.get("commence_time", "")).replace("Z", "+00:00")) <= now
            except ValueError:
                continue
            if not commenced:
                continue
            away = resolve(e.get("away_team", ""))
            home = resolve(e.get("home_team", ""))
            if not away or not home:
                continue
            books: dict[str, float] = {}
            for b in e.get("bookmakers", []):
                for m in b.get("markets", []):
                    if m.get("key") != "totals":
                        continue
                    for o in m.get("outcomes", []):
                        if o.get("name") == "Over" and o.get("point") is not None:
                            books[b.get("key", "?")] = float(o["point"])
            if books:
                out[f"{away}@{home}"] = {"median": statistics.median(books.values()),
                                         "books": books}
        return out

    async def lookup(self, session: aiohttp.ClientSession, game_key: str) -> Optional[dict]:
        now = time.monotonic()
        if self._board is None or now - self._at > self.ttl:
            if not self._budget_ok():
                # budget spent: serve the stale board rather than nothing
                return self._board.get(game_key) if self._board else None
            try:
                async with session.get(self.URL.format(key=self.key),
                                       timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status != 200:
                        return None
                    self.credits_remaining = resp.headers.get("x-requests-remaining")
                    data = await resp.json(content_type=None)
            except Exception:  # noqa: BLE001 — verification is best-effort
                return None
            self.fetches_today += 1
            self._board = self.parse_board(data)
            self._at = now
        return self._board.get(game_key)


def load_closing_lines(path) -> dict[int, float]:
    """game_pk -> real pregame total from data/closing_lines.csv (collector output)."""
    import csv
    p = Path(path)
    if not p.exists():
        return {}
    with p.open() as fh:
        out = {}
        for r in csv.DictReader(fh):
            try:
                out[int(r["game_pk"])] = float(r["pregame_total"])
            except (KeyError, TypeError, ValueError):
                continue
        return out


def _line_anchor(state: LiveGameState, pregame_total: float,
                 rule: TriggerRule) -> RunEnvAnchor:
    return expected_final_total(
        pregame_total=pregame_total, runs_so_far=state.total_runs,
        inning=state.inning, half=state.half, outs=state.outs or 0,
        on_first=state.on_first, on_second=state.on_second, on_third=state.on_third,
        home_key=state.home, ttop_mult=rule.ttop_run_multiplier, in_window=True)


def _common_gates(state: LiveGameState, quote: Optional[Quote],
                  pregame_total: Optional[float], rule: TriggerRule, c: Constraints,
                  bullpen_ra9: Optional[float]) -> Optional[tuple[RunEnvAnchor, list[str]]]:
    """Starter, bullpen, tier, and RE24 line-edge gates shared by all rules."""
    if c.require_starter_on_mound and not state.starter_on_mound:
        return None                              # a reliever is already in — thesis void
    if rule.starter_tier_filter and state.starter_tier not in rule.starter_tier_filter:
        return None
    if bullpen_ra9 is not None and bullpen_ra9 < c.bullpen_elite_ra9:
        return None                              # elite bullpen — a pull kills the Over
    if quote is None or pregame_total is None:
        return None
    anchor = _line_anchor(state, pregame_total, rule)
    edge_min = c.required_edge(rule, quote.line)
    if not (quote.line < anchor.expected_final - edge_min):
        return None                              # market not offering the Over cheaply
    reasons = [
        f"starter still in ({state.pitcher_name}, {state.starter_tier})",
        pull_risk_label(bullpen_ra9, c.bullpen_elite_ra9),
        f"live {quote.line} < fair {anchor.expected_final:.1f} "
        f"(edge {anchor.expected_final - quote.line:+.1f} ≥ {edge_min})",
    ]
    return anchor, reasons


def evaluate_confirm(state: LiveGameState, quote: Optional[Quote],
                     pregame_total: Optional[float], rule: TriggerRule, c: Constraints,
                     bullpen_ra9: Optional[float] = None) -> Optional[Trigger]:
    """CONFIRM: the top-of-order target turn is AT BAT now (exact TTO match)."""
    if state.times_through_order is None:
        return None
    if state.inning < rule.min_inning:
        return None
    if state.times_through_order != rule.times_through_order:
        return None
    if state.batting_slot_due not in rule.top_of_order_slots:
        return None
    gated = _common_gates(state, quote, pregame_total, rule, c, bullpen_ra9)
    if gated is None:
        return None
    anchor, reasons = gated
    reasons = [f"inning {state.inning} ≥ {rule.min_inning}",
               f"TTO {state.times_through_order} == {rule.times_through_order}",
               f"slot {state.batting_slot_due} in {rule.top_of_order_slots}"] + reasons
    return Trigger("CONFIRM", rule.name, state.game_key, state, quote, pregame_total,
                   quote.line, anchor, bullpen_ra9, reasons)


def evaluate_lookahead(state: LiveGameState, quote: Optional[Quote],
                       pregame_total: Optional[float], rule: TriggerRule, c: Constraints,
                       bullpen_ra9: Optional[float] = None) -> Optional[Trigger]:
    """ARM: 2 outs, 8/9 hitter up, target turn leads off NEXT inning (exact TTO-1)."""
    if state.outs is None or state.times_through_order is None:
        return None
    if state.outs != c.lookahead_outs:
        return None
    if state.batting_slot_due not in c.lookahead_slots:
        return None
    if state.times_through_order != rule.times_through_order - 1:
        return None
    if state.inning < rule.min_inning - 1:
        return None
    gated = _common_gates(state, quote, pregame_total, rule, c, bullpen_ra9)
    if gated is None:
        return None
    anchor, reasons = gated
    reasons = [f"LOOK-AHEAD: {state.outs} outs, slot {state.batting_slot_due} up, "
               f"TTO{rule.times_through_order} leads off next inning (buffer vs line move)"] + reasons
    return Trigger("ARM", rule.name, state.game_key, state, quote, pregame_total,
                   quote.line, anchor, bullpen_ra9, reasons)


def evaluate_watch(state: LiveGameState, quote: Optional[Quote],
                   pregame_total: Optional[float], rule: TriggerRule, c: Constraints,
                   bullpen_ra9: Optional[float] = None) -> Optional[Trigger]:
    """WATCH: experimental low-scoring game-script play (console + ledger only)."""
    if state.inning is None:
        return None
    if not (2 <= state.inning <= rule.watch_max_inning):
        return None
    if state.total_runs > rule.watch_max_runs:
        return None
    gated = _common_gates(state, quote, pregame_total, rule, c, bullpen_ra9)
    if gated is None:
        return None
    anchor, reasons = gated
    reasons = [f"WATCH: {state.total_runs} run(s) through inning {state.inning} "
               f"(≤ {rule.watch_max_runs}) — low-scoring regression watch"] + reasons
    return Trigger("WATCH", rule.name, state.game_key, state, quote, pregame_total,
                   quote.line, anchor, bullpen_ra9, reasons)


def evaluate_rule(rule: TriggerRule, state: LiveGameState, quote: Optional[Quote],
                  pregame_total: Optional[float], c: Constraints,
                  bullpen_ra9: Optional[float]) -> list[Trigger]:
    """All triggers a single rule produces for one state (shared by live + sim)."""
    args = (state, quote, pregame_total, rule, c, bullpen_ra9)
    if rule.kind == "watch":
        t = evaluate_watch(*args)
        return [t] if t else []
    out = [evaluate_lookahead(*args), evaluate_confirm(*args)]
    return [t for t in out if t]


class LiveEngine:
    def __init__(self, constraints: Constraints, settings: EngineSettings, date_str: str):
        self.c = constraints
        self.s = settings
        self.bullpen_quality = settings.load_bullpen_quality()
        self.mlb = MLBStatsSource(date=date_str, live_only=True,
                                  starter_tiers=settings.load_starter_tiers())
        self.fanduel = FanDuelSource(state=settings.fanduel_state)
        self.bovada = BovadaSource()
        self.pinnacle = PinnacleSource()
        self.ledger = Ledger(settings.ledger_path, constraints.bullpen_elite_ra9)
        self.discord = DiscordNotifier(settings.alert_webhook, settings.discord_ping,
                                       constraints.bullpen_elite_ra9,
                                       settings.max_data_age_seconds)
        # REAL pregame anchors first (collector/backfill output); first-seen is only
        # the fallback — for games already live at daemon start, first-seen would be
        # an in-play line, not the pregame total.
        self.closing_lines = load_closing_lines(
            Path(__file__).resolve().parent / "data" / "closing_lines.csv")
        # fire-time verification against betable books (needs ODDS_API_KEY).
        odds_key = os.environ.get("ODDS_API_KEY")
        self.verifier = (LineVerifier(odds_key, daily_cap=settings.verify_daily_credit_cap)
                         if (settings.verify_lines and odds_key) else None)
        self.pregame_total: dict[str, float] = {}
        self._alerted: set[str] = set()
        self._stop = asyncio.Event()

    def _merge_quotes(self, *result_lists: list[Quote]) -> dict[str, Quote]:
        return merge_quotes(*result_lists)

    async def poll_once(self, session: aiohttp.ClientSession):
        """Return ``(fired_triggers, live_states, merged_quotes)`` for this poll."""
        tasks = [self.mlb.fetch(session)]
        if self.s.use_fanduel:
            tasks.append(self.fanduel.fetch(session))
        if self.s.use_bovada:
            tasks.append(self.bovada.fetch(session))
        results = await asyncio.gather(*tasks)

        state_res = results[0]
        quote_lists = [r.quotes for r in results[1:] if r.ok]
        quotes = self._merge_quotes(*quote_lists)
        if not quotes and self.s.use_pinnacle_fallback:
            pin = await self.pinnacle.fetch(session)
            if pin.ok:
                quotes = self._merge_quotes(pin.quotes)

        fired: list[Trigger] = []
        for st in state_res.states:
            q = quotes.get(st.game_key)
            if st.game_key not in self.pregame_total:
                seeded = self.closing_lines.get(st.game_pk)
                if seeded is not None:
                    self.pregame_total[st.game_key] = seeded   # true pregame line
                elif q is not None and not q.live_game:
                    self.pregame_total[st.game_key] = q.line   # fallback: first-seen pregame
                elif q is not None:
                    # last resort: first-seen while already in-play — log the caveat
                    self.pregame_total[st.game_key] = q.line
                    console.log(f"[yellow]{st.game_key}: no real pregame line — "
                                f"anchoring to first-seen in-play total {q.line}[/]")
            pregame = self.pregame_total.get(st.game_key)
            bullpen = self.bullpen_quality.get(_pitching_team(st))
            for rule in self.c.active_rules():
                trigs = evaluate_rule(rule, st, q, pregame, self.c, bullpen)
                if not trigs and rule.kind == "tto":
                    # RESCUE PASS: the scraped line may be stale-HIGH (or missing),
                    # silently blocking a real fire. If the STATE gates match (probe
                    # with a free line), re-gate on the VERIFIED market median.
                    trigs = await self._rescue(session, rule, st, q, pregame, bullpen)
                for trig in trigs:
                    if trig.dedupe_key not in self._alerted:
                        self._alerted.add(trig.dedupe_key)
                        fired.append(trig)
        return fired, state_res.states, quotes

    async def _rescue(self, session, rule, st, q, pregame, bullpen) -> list[Trigger]:
        """Re-gate a state-matched window on the verified market line (budgeted)."""
        if self.verifier is None or pregame is None:
            return []
        # probe: line=0 always clears the line gate, so a fire here means every
        # STATE gate (inning/TTO/slot/tier/starter/bullpen) passed.
        probe = Quote(book="probe", home=st.home, away=st.away, line=0.0, live_game=True)
        if not evaluate_rule(rule, st, probe, pregame, self.c, bullpen):
            return []
        verified = await self.verifier.lookup(session, st.game_key)
        if not verified:
            return []
        vq = Quote(book="market-verified", home=st.home, away=st.away,
                   line=verified["median"], live_game=True)
        return evaluate_rule(rule, st, vq, pregame, self.c, bullpen)

    async def _handle(self, session: aiohttp.ClientSession, trig: Trigger) -> None:
        # verify the live line against REAL betable books before alerting (Fix for
        # stale scraped in-play quotes — a Bovada 8.5 while DK/FD sat at 9.5-10.5).
        verified = suppressed = None
        extra = None
        if trig.trigger_type != "WATCH" and self.verifier:
            verified = await self.verifier.lookup(session, trig.game_key)
            if verified:
                rule = next((r for r in self.c.rules if r.name == trig.rule_name), None)
                min_edge = (self.c.required_edge(rule, verified["median"]) if rule
                            else self.c.line_edge_min_runs)
                v_edge, suppressed = verification_verdict(
                    trig.anchor.expected_final, verified["median"], min_edge)
                extra = {"verified_line": verified["median"], "verified_edge": v_edge,
                         "verified_books": verified["books"],
                         "suppressed_stale_feed": bool(suppressed)}
        self.ledger.record(trig, extra=extra)    # every signal, always (with verification)
        self._emit(trig, verified=verified, suppressed=bool(suppressed))
        if trig.trigger_type != "WATCH" and not suppressed:  # WATCH never hits Discord
            await self.discord.post(session, trig, verified=verified)

    def _emit(self, trig: Trigger, verified: Optional[dict] = None,
              suppressed: bool = False) -> None:
        s = trig.state
        tag = {"ARM": "🟡 ARM", "CONFIRM": "🔴 CONFIRM",
               "WATCH": "[WATCH_RULE] 🔵 WATCH"}[trig.trigger_type]
        if suppressed:
            tag = f"⛔ SUPPRESSED {tag}"
        console.rule(f"[bold]{tag} · {trig.rule_name} · {trig.game_key}")
        if verified:
            vb = " · ".join(f"{k}:{v}" for k, v in sorted(verified["books"].items())[:5])
            note = ("stale feed line — edge dies at the real books" if suppressed
                    else "edge holds at the real books")
            console.print(f"   verified live line: median {verified['median']} ({vb}) — {note}")
        console.print(
            f"[bold]{s.away} {s.away_score} — {s.home_score} {s.home}[/]  "
            f"inn {s.inning} {s.half} · {s.pitcher_name} ({s.starter_tier}) · "
            f"slot {s.batting_slot_due} due, TTO {s.times_through_order}, {s.outs} out · "
            f"data {data_age_label(s.data_age_seconds, self.s.max_data_age_seconds)}")
        console.print(f"pregame {trig.pregame_total} → live {trig.live_total} "
                      f"({trig.quote.book}) vs RE24 fair {trig.anchor.expected_final:.1f}"
                      f"  →  [bold green]OVER edge {trig.edge:+.1f}[/]")
        for r in trig.reasons:
            console.print(f"   ✓ {r}")

    async def run(self, once: bool = False) -> None:
        rules = self.c.active_rules()
        console.print(f"[cyan]The Third Turn engine (v3)[/] · {len(rules)} rule(s): "
                      + ", ".join(f"{r.name}(TTO{r.times_through_order},{r.kind})" for r in rules))
        console.print(f"[cyan]pregame anchors:[/] {len(self.closing_lines)} real closing "
                      f"line(s) loaded from data/closing_lines.csv")
        if self.verifier:
            console.print(f"[green]Line verification ON[/] — trigger gating + alerts use "
                          f"the betable-book median (The Odds API, cap "
                          f"{self.verifier.daily_cap} credits/day).")
        else:
            console.print("[yellow]Line verification OFF (no ODDS_API_KEY) — feed "
                          "lines are unverified.[/]")
        if self.discord.enabled:
            console.print("[green]Discord alerts ON[/] for CONFIRM/ARM.")
        else:
            console.print("[dim]Discord off (set DISCORD_WEBHOOK_URL) — console + ledger only.[/]")
        timeout = aiohttp.ClientTimeout(total=45)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            while not self._stop.is_set():
                t0 = time.monotonic()
                try:
                    fired, states, quotes = await self.poll_once(session)
                except Exception as exc:  # noqa: BLE001 — a poll must never kill the loop
                    console.log(f"[yellow]poll error: {type(exc).__name__}: {exc}[/]")
                    fired, states, quotes = [], [], {}
                stale = [s for s in states if (s.data_age_seconds or 0) > self.s.max_data_age_seconds]
                cred = (f" · verify {self.verifier.fetches_today}/{self.verifier.daily_cap}"
                        + (f" (API rem {self.verifier.credits_remaining})"
                           if self.verifier.credits_remaining else "")) if self.verifier else ""
                console.log(f"polled {len(states)} live game(s), {len(quotes)} quoted; "
                            f"{len(fired)} new alert(s) [{(time.monotonic()-t0)*1000:.0f}ms]"
                            + (f" [yellow]⚠ {len(stale)} stale feed(s)[/]" if stale else "")
                            + cred)
                for trig in fired:
                    await self._handle(session, trig)
                if once:
                    if not states:
                        console.print("[dim]no live games right now (nothing to evaluate).[/]")
                    break
                try:
                    await asyncio.wait_for(self._stop.wait(),
                                           timeout=self.s.poll_interval_seconds)
                except asyncio.TimeoutError:
                    pass

    def request_stop(self, *_):
        self._stop.set()


async def _amain(once: bool) -> int:
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from shared_piping.envload import load_env
    load_env()   # pick up DISCORD_WEBHOOK_URL / DISCORD_PING from the_third_turn/.env
    constraints, from_file = Constraints.load()
    if not from_file:
        console.print("[yellow]⚠ constraints.json not found — using default rules. "
                      "Run backtest_thesis.py to fit them.[/]")
    settings = EngineSettings()
    # MLB schedule dates are US/Eastern — a UTC date would flip to "tomorrow" at
    # 8pm ET and lose the evening slate mid-game.
    et_today = datetime.now(ZoneInfo("America/New_York")).date().isoformat()
    engine = LiveEngine(constraints, settings, date_str=et_today)

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, engine.request_stop)
        except NotImplementedError:  # pragma: no cover (non-unix)
            pass
    await engine.run(once=once)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="The Third Turn live engine")
    ap.add_argument("--once", action="store_true",
                    help="run a single poll and exit (dry run)")
    args = ap.parse_args(argv)
    return asyncio.run(_amain(args.once))


if __name__ == "__main__":
    raise SystemExit(main())
