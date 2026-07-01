#!/usr/bin/env python3
"""OBJECTIVE 2 — The Third Turn live execution engine (headless async daemon).

Polls three sources concurrently every ``poll_interval`` over one aiohttp session:
  * Source A — MLB Stats API : live state, pitch count, lineup slot, TTO, outs, bases,
                               starter-on-mound, starter tier
  * Source B — FanDuel       : live game totals (replaces IP-blocked DraftKings)
  * Source C — Bovada        : live game totals
  (Pinnacle is a fallback book, consulted only when FanDuel returns nothing.)

Revision 2 fires TWO alert types (both pure, offline-tested predicates):

  ARM (look-ahead, Fix #5) — 2 outs, an 8/9 hitter up, and the top of the order due
      for its 3rd turn NEXT inning. Beats the ~10-20s MLB-API latency so we can read
      the odds before the books move at the inning break.

  CONFIRM — the top-of-order 3rd turn is actually at bat.

Both require, beyond the state match:
  * the STARTER is still on the mound (thesis void otherwise, Fix #4),
  * the fielding team's bullpen is NOT elite (else a pull neutralizes the Over, Fix #4),
  * the live total sits below the RE24 expected-final anchor by a margin (Fix #3),
  * (optional) the starter's tier passes ``starter_tier_filter`` (Fix #1).

    python the_third_turn/live_engine.py            # daemon
    python the_third_turn/live_engine.py --once     # single poll, then exit (dry run)
"""

from __future__ import annotations

import argparse
import asyncio
import signal
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

import aiohttp  # noqa: E402
from rich.console import Console  # noqa: E402

from config import Constraints, EngineSettings  # noqa: E402
from shared_piping.run_expectancy import RunEnvAnchor, expected_final_total  # noqa: E402
from sources.base import LiveGameState, Quote  # noqa: E402
from sources.bovada import BovadaSource  # noqa: E402
from sources.fanduel import FanDuelSource  # noqa: E402
from sources.mlb_statsapi import MLBStatsSource  # noqa: E402
from sources.pinnacle import PinnacleSource  # noqa: E402

console = Console()


@dataclass
class Trigger:
    """A fired alert: the state + market + run-env model that cleared every gate."""

    alert_type: str          # "ARM" | "CONFIRM"
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
        # one alert per (type, game, pitcher, inning, half).
        s = self.state
        return f"{self.alert_type}:{self.game_key}:{s.pitcher_id}:{s.inning}:{s.half}"


def _pitching_team(state: LiveGameState) -> str:
    """The fielding (pitching) team key: home pitches in the top half, away in bottom."""
    return state.home if state.half == "top" else state.away


def _line_anchor(state: LiveGameState, pregame_total: float,
                 c: Constraints) -> RunEnvAnchor:
    return expected_final_total(
        pregame_total=pregame_total, runs_so_far=state.total_runs,
        inning=state.inning, half=state.half, outs=state.outs or 0,
        on_first=state.on_first, on_second=state.on_second, on_third=state.on_third,
        home_key=state.home, ttop_mult=c.ttop_run_multiplier, in_window=True)


def _common_gates(state: LiveGameState, quote: Optional[Quote],
                  pregame_total: Optional[float], c: Constraints,
                  bullpen_ra9: Optional[float]) -> Optional[tuple[RunEnvAnchor, list[str]]]:
    """Gates shared by ARM and CONFIRM: starter, bullpen, tier, RE24 line edge."""
    if c.require_starter_on_mound and not state.starter_on_mound:
        return None                              # a reliever is already in — thesis void
    if c.starter_tier_filter and state.starter_tier not in c.starter_tier_filter:
        return None
    if bullpen_ra9 is not None and bullpen_ra9 < c.bullpen_elite_ra9:
        return None                              # elite bullpen — a pull kills the Over
    if quote is None or pregame_total is None:
        return None
    anchor = _line_anchor(state, pregame_total, c)
    if not (quote.line < anchor.expected_final - c.line_edge_min_runs):
        return None                              # market not offering the Over cheaply
    reasons = [
        f"starter still in ({state.pitcher_name})",
        f"bullpen RA/9 {bullpen_ra9:.2f} ≥ elite {c.bullpen_elite_ra9}"
        if bullpen_ra9 is not None else "bullpen quality unknown",
        f"live total {quote.line} < expected {anchor.expected_final:.1f} "
        f"(edge {anchor.expected_final - quote.line:+.1f} ≥ {c.line_edge_min_runs})",
        f"starter tier: {state.starter_tier}",
    ]
    return anchor, reasons


def evaluate_confirm(state: LiveGameState, quote: Optional[Quote],
                     pregame_total: Optional[float], c: Constraints,
                     bullpen_ra9: Optional[float] = None) -> Optional[Trigger]:
    """CONFIRM: the top-of-order 3rd turn is AT BAT now."""
    if state.times_through_order is None:
        return None
    if state.inning < c.min_inning:
        return None
    if state.times_through_order < c.times_through_order:
        return None
    if state.batting_slot_due not in c.top_of_order_slots:
        return None
    gated = _common_gates(state, quote, pregame_total, c, bullpen_ra9)
    if gated is None:
        return None
    anchor, reasons = gated
    reasons = [f"inning {state.inning} ≥ {c.min_inning}",
               f"TTO {state.times_through_order} ≥ {c.times_through_order}",
               f"slot {state.batting_slot_due} in top-of-order"] + reasons
    return Trigger("CONFIRM", state.game_key, state, quote, pregame_total,
                   quote.line, anchor, bullpen_ra9, reasons)


def evaluate_lookahead(state: LiveGameState, quote: Optional[Quote],
                       pregame_total: Optional[float], c: Constraints,
                       bullpen_ra9: Optional[float] = None) -> Optional[Trigger]:
    """ARM: 2 outs, 8/9 hitter up, top-of-order 3rd turn leads off NEXT inning."""
    if state.outs is None or state.times_through_order is None:
        return None
    if state.outs != c.lookahead_outs:
        return None
    if state.batting_slot_due not in c.lookahead_slots:
        return None
    # the current 8/9 hitter at TTO k means the leadoff is TTO k+1 next inning.
    if state.times_through_order != c.times_through_order - 1:
        return None
    if state.inning < c.min_inning - 1:
        return None
    gated = _common_gates(state, quote, pregame_total, c, bullpen_ra9)
    if gated is None:
        return None
    anchor, reasons = gated
    reasons = [f"LOOK-AHEAD: {state.outs} outs, slot {state.batting_slot_due} up, "
               f"top-of-order 3rd turn leads off next inning",
               f"buffer before inning-break line move"] + reasons
    return Trigger("ARM", state.game_key, state, quote, pregame_total,
                   quote.line, anchor, bullpen_ra9, reasons)


class LiveEngine:
    def __init__(self, constraints: Constraints, settings: EngineSettings,
                 date_str: str):
        self.c = constraints
        self.s = settings
        self.bullpen_quality = settings.load_bullpen_quality()
        self.mlb = MLBStatsSource(date=date_str, live_only=True,
                                  starter_tiers=settings.load_starter_tiers())
        self.fanduel = FanDuelSource(state=settings.fanduel_state)
        self.bovada = BovadaSource()
        self.pinnacle = PinnacleSource()
        self.pregame_total: dict[str, float] = {}
        self._alerted: set[str] = set()
        self._stop = asyncio.Event()

    def _merge_quotes(self, *result_lists: list[Quote]) -> dict[str, Quote]:
        merged: dict[str, Quote] = {}
        for quotes in result_lists:
            for q in quotes:
                merged.setdefault(q.game_key, q)
        return merged

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
            if q is not None and st.game_key not in self.pregame_total:
                self.pregame_total[st.game_key] = q.line
            pregame = self.pregame_total.get(st.game_key)
            bullpen = self.bullpen_quality.get(_pitching_team(st))
            for trig in (evaluate_lookahead(st, q, pregame, self.c, bullpen),
                         evaluate_confirm(st, q, pregame, self.c, bullpen)):
                if trig and trig.dedupe_key not in self._alerted:
                    self._alerted.add(trig.dedupe_key)
                    fired.append(trig)
        return fired, state_res.states, quotes

    def _emit(self, trig: Trigger) -> None:
        s = trig.state
        tag = "🟡 ARM" if trig.alert_type == "ARM" else "🔴 CONFIRM"
        console.rule(f"[bold]{tag} · {trig.game_key}")
        console.print(
            f"[bold]{s.away} {s.away_score} — {s.home_score} {s.home}[/]  "
            f"inn {s.inning} {s.half} · {s.pitcher_name} ({s.starter_tier}) · "
            f"slot {s.batting_slot_due} due, TTO {s.times_through_order}, {s.outs} out")
        console.print(f"pregame {trig.pregame_total} → live {trig.live_total} "
                      f"({trig.quote.book}) vs RE24 expected {trig.anchor.expected_final:.1f}"
                      f"  →  [bold green]OVER edge {trig.edge:+.1f}[/]")
        for r in trig.reasons:
            console.print(f"   ✓ {r}")

    async def run(self, once: bool = False) -> None:
        console.print(f"[cyan]The Third Turn engine (v2)[/] · fire on 3rd-turn arrival: "
                      f"inning≥{self.c.min_inning}, TTO≥{self.c.times_through_order}, "
                      f"top {self.c.top_of_order_slots}, RE24 edge≥{self.c.line_edge_min_runs}, "
                      f"suppress bullpen<{self.c.bullpen_elite_ra9} RA/9")
        timeout = aiohttp.ClientTimeout(total=45)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            while not self._stop.is_set():
                t0 = time.monotonic()
                try:
                    fired, states, quotes = await self.poll_once(session)
                except Exception as exc:  # noqa: BLE001 — a poll must never kill the loop
                    console.log(f"[yellow]poll error: {type(exc).__name__}: {exc}[/]")
                    fired, states, quotes = [], [], {}
                console.log(f"polled {len(states)} live game(s), {len(quotes)} quoted; "
                            f"{len(fired)} new alert(s) [{(time.monotonic()-t0)*1000:.0f}ms]")
                for trig in fired:
                    self._emit(trig)
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
    from datetime import date
    constraints, from_file = Constraints.load()
    if not from_file:
        console.print("[yellow]⚠ constraints.json not found — using conservative "
                      "defaults. Run backtest_thesis.py to fit real parameters.[/]")
    settings = EngineSettings()
    engine = LiveEngine(constraints, settings, date_str=date.today().isoformat())

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
