#!/usr/bin/env python3
"""OBJECTIVE 2 — The Third Turn live execution engine (headless async daemon).

Polls three sources concurrently every ``poll_interval`` over one aiohttp session:
  * Source A — MLB Stats API : live game state, pitch count, lineup slot, TTO
  * Source B — FanDuel       : live game totals (replaces IP-blocked DraftKings)
  * Source C — Bovada        : live game totals
  (Pinnacle is a fallback book, consulted only when FanDuel returns nothing.)

It fires an alert for a game the moment its LIVE STATE matches the backtested
constraints AND the market still offers the Over cheaply:

    inning >= min_inning
    AND times_through_order >= constraints.times_through_order
    AND batting_slot_due in top_of_order_slots
    AND pitch_count > pitch_count_threshold
    AND (pregame_total - live_total) < line_drop_max_runs

The trigger predicate (:func:`evaluate`) is a PURE function of state+quote+constraints
so it is unit-tested offline. The pregame total is captured as the first line we see
for a game (or supplied via config/pregame_totals.yaml).

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
from sources.base import LiveGameState, Quote  # noqa: E402
from sources.bovada import BovadaSource  # noqa: E402
from sources.fanduel import FanDuelSource  # noqa: E402
from sources.mlb_statsapi import MLBStatsSource  # noqa: E402
from sources.pinnacle import PinnacleSource  # noqa: E402

console = Console()


@dataclass
class Trigger:
    """A fired alert: the state + market that satisfied every constraint."""

    game_key: str
    state: LiveGameState
    quote: Quote
    pregame_total: float
    live_total: float
    drop: float
    reasons: list[str]

    @property
    def dedupe_key(self) -> str:
        # one alert per (game, pitcher, inning, half) — avoids re-firing every poll.
        return f"{self.game_key}:{self.state.pitcher_id}:{self.state.inning}:{self.state.half}"


def evaluate(state: LiveGameState, quote: Optional[Quote], pregame_total: Optional[float],
             c: Constraints) -> Optional[Trigger]:
    """PURE trigger test. Returns a Trigger if every constraint holds, else None."""
    if state.pitch_count is None or state.times_through_order is None:
        return None
    if state.inning < c.min_inning:
        return None
    if state.times_through_order < c.times_through_order:
        return None
    if state.batting_slot_due not in c.top_of_order_slots:
        return None
    if state.pitch_count <= c.pitch_count_threshold:
        return None
    if quote is None or pregame_total is None:
        return None
    drop = pregame_total - quote.line
    # Over still cheap: market hasn't already faded the total by >= the bound.
    if not (drop < c.line_drop_max_runs):
        return None
    reasons = [
        f"inning {state.inning} ≥ {c.min_inning}",
        f"TTO {state.times_through_order} ≥ {c.times_through_order}",
        f"slot {state.batting_slot_due} in top-of-order",
        f"pitch count {state.pitch_count} > {c.pitch_count_threshold}",
        f"line drop {drop:+.1f} < {c.line_drop_max_runs} (Over still live)",
    ]
    return Trigger(game_key=state.game_key, state=state, quote=quote,
                   pregame_total=pregame_total, live_total=quote.line, drop=drop,
                   reasons=reasons)


class LiveEngine:
    def __init__(self, constraints: Constraints, settings: EngineSettings,
                 date_str: str):
        self.c = constraints
        self.s = settings
        self.mlb = MLBStatsSource(date=date_str, live_only=True)
        self.fanduel = FanDuelSource(state=settings.fanduel_state)
        self.bovada = BovadaSource()
        self.pinnacle = PinnacleSource()
        self.pregame_total: dict[str, float] = {}   # game_key -> first-seen total
        self._alerted: set[str] = set()
        self._stop = asyncio.Event()

    def _merge_quotes(self, *result_lists: list[Quote]) -> dict[str, Quote]:
        """One quote per game_key. First non-empty book wins (FanDuel, then Bovada)."""
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
        results = await asyncio.gather(*tasks, return_exceptions=False)

        state_res = results[0]
        book_results = results[1:]
        quote_lists = [r.quotes for r in book_results if r.ok]
        quotes = self._merge_quotes(*quote_lists)

        # Fallback to Pinnacle only if the primary books gave us nothing.
        if not quotes and self.s.use_pinnacle_fallback:
            pin = await self.pinnacle.fetch(session)
            if pin.ok:
                quotes = self._merge_quotes(pin.quotes)

        fired: list[Trigger] = []
        for st in state_res.states:
            q = quotes.get(st.game_key)
            # capture pregame anchor the first time we see any line for this game.
            if q is not None and st.game_key not in self.pregame_total:
                self.pregame_total[st.game_key] = q.line
            trig = evaluate(st, q, self.pregame_total.get(st.game_key), self.c)
            if trig and trig.dedupe_key not in self._alerted:
                self._alerted.add(trig.dedupe_key)
                fired.append(trig)
        return fired, state_res.states, quotes

    def _emit(self, trig: Trigger) -> None:
        s = trig.state
        console.rule(f"[bold red]⚾ THIRD-TURN ALERT · {trig.game_key}")
        console.print(
            f"[bold]{s.away} {s.away_score} — {s.home_score} {s.home}[/]  "
            f"inn {s.inning} {s.half} · {s.pitcher_name} facing slot "
            f"{s.batting_slot_due} for the {s.times_through_order}rd time")
        console.print(f"pregame total {trig.pregame_total} → live {trig.live_total} "
                      f"({trig.quote.book}, drop {trig.drop:+.1f})  →  [bold green]hammer the OVER[/]")
        for r in trig.reasons:
            console.print(f"   ✓ {r}")

    async def run(self, once: bool = False) -> None:
        console.print(f"[cyan]The Third Turn engine[/] · constraints: inning≥"
                      f"{self.c.min_inning}, TTO≥{self.c.times_through_order}, "
                      f"top-of-order {self.c.top_of_order_slots}, PC>"
                      f"{self.c.pitch_count_threshold}, drop<{self.c.line_drop_max_runs}")
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
