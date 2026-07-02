#!/usr/bin/env python3
"""Same-day trigger replay from the MLB Stats API play-by-play.

Statcast (Baseball Savant) publishes a day behind, so the Statcast-based
`simulate_execution.py` can't check *today's* games until tomorrow. This tool
reconstructs per-plate-appearance state from `feed/live` `allPlays` (available in
real time) for a given date's completed/in-progress games and runs the EXACT engine
rules, so we can see what would have fired today. Uses real collected pregame lines
(`data/closing_lines.csv`) where available, else a park-adjusted proxy.

Approximations (documented): base/out RE24 premium uses bases-empty (conservative —
slightly lowers the fair anchor); tiers come from `config/starter_tiers.json`.

    python the_third_turn/replay_today.py                 # today
    python the_third_turn/replay_today.py --date 2026-07-01
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import urllib.request
from collections import defaultdict
from datetime import date as date_cls
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rich.console import Console  # noqa: E402

from config import Constraints, EngineSettings  # noqa: E402
from live_engine import Trigger, _pitching_team, evaluate_rule  # noqa: E402
from shared_piping.envload import load_env  # noqa: E402
from shared_piping.run_expectancy import park_factor  # noqa: E402
from shared_piping.team_map import resolve  # noqa: E402
from sources.base import LiveGameState, Quote  # noqa: E402

console = Console()
HERE = Path(__file__).resolve().parent
UA = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
SCHEDULE = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date}"
FEED = "https://statsapi.mlb.com/api/v1.1/game/{pk}/feed/live"
LEAGUE_AVG = 8.6


def _get(url: str):
    return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read())


def _real_lines() -> dict[int, float]:
    p = HERE / "data" / "closing_lines.csv"
    if not p.exists():
        return {}
    with p.open() as fh:
        return {int(r["game_pk"]): float(r["pregame_total"]) for r in csv.DictReader(fh)
                if r.get("game_pk")}


def replay_game(feed: dict, c: Constraints, bullpen: dict, tiers: dict,
                pregame: float, line_fn=None) -> list[Trigger]:
    """Replay the engine rules over a game's play-by-play.

    ``line_fn(iso_ts) -> float|None`` supplies the LIVE total at each plate
    appearance (e.g. from a harvested trajectory) — the honest-backtest mode.
    Without it, the pregame total stands in as the live line (same approximation
    as simulate_execution).
    """
    gd, ld = feed.get("gameData", {}), feed.get("liveData", {})
    away = resolve(gd.get("teams", {}).get("away", {}).get("name", "")) or "?"
    home = resolve(gd.get("teams", {}).get("home", {}).get("name", "")) or "?"
    game_pk = int(gd.get("game", {}).get("pk") or 0)
    box = ld.get("boxscore", {}).get("teams", {})
    order = {"away": box.get("away", {}).get("battingOrder", []) or [],
             "home": box.get("home", {}).get("battingOrder", []) or []}
    starter = {s: (box.get(s, {}).get("pitchers", []) or [None])[0] for s in ("away", "home")}

    cum_pitches: dict[int, int] = defaultdict(int)
    faced: dict[tuple[int, int], int] = defaultdict(int)
    running_outs = 0
    away_sc = home_sc = 0
    cur_half = None
    seen: set[str] = set()
    fired: list[Trigger] = []

    for play in ld.get("plays", {}).get("allPlays", []):
        about, match, res = play.get("about", {}), play.get("matchup", {}), play.get("result", {})
        if res.get("type") != "atBat" or not match.get("batter"):
            continue
        is_top = bool(about.get("isTopInning"))
        half = "top" if is_top else "bottom"
        if (about.get("inning"), half) != cur_half:
            running_outs = 0
            cur_half = (about.get("inning"), half)

        pitching_side = "home" if is_top else "away"
        batting_side = "away" if is_top else "home"
        pitcher_id = match.get("pitcher", {}).get("id")
        batter_id = match.get("batter", {}).get("id")
        sid = starter[pitching_side]
        faced[(pitcher_id, batter_id)] += 1
        tto = faced[(pitcher_id, batter_id)]
        slot = order[batting_side].index(batter_id) + 1 if batter_id in order[batting_side] else None

        state = LiveGameState(
            game_pk=game_pk, away=away, home=home, inning=int(about.get("inning") or 0),
            half=half, away_score=away_sc, home_score=home_sc, pitcher_id=pitcher_id,
            pitcher_name=match.get("pitcher", {}).get("fullName"),
            pitch_count=cum_pitches[pitcher_id], batting_slot_due=slot,
            times_through_order=tto, status="Live", outs=running_outs,
            on_first=False, on_second=False, on_third=False, starter_id=sid,
            starter_on_mound=(pitcher_id == sid),
            starter_tier=tiers.get(str(sid), "Unknown"), data_age_seconds=None)
        live_line = pregame
        if line_fn is not None:
            live_line = line_fn(play.get("about", {}).get("startTime") or "")
            if live_line is None:
                cum_pitches[pitcher_id] += sum(
                    1 for ev in play.get("playEvents", []) if ev.get("isPitch"))
                running_outs = int(play.get("count", {}).get("outs") or running_outs)
                away_sc = int(res.get("awayScore") or away_sc)
                home_sc = int(res.get("homeScore") or home_sc)
                continue   # no market at this moment — skip evaluation, keep state
        book = "market-verified" if line_fn is not None else "statsapi-replay"
        quote = Quote(book=book, home=home, away=away, line=live_line, live_game=True)
        pen = bullpen.get(_pitching_team(state))
        for rule in c.rules:
            for trig in evaluate_rule(rule, state, quote, pregame, c, pen):
                if trig.dedupe_key not in seen:
                    seen.add(trig.dedupe_key)
                    fired.append(trig)

        # advance running state AFTER evaluating the PA
        cum_pitches[pitcher_id] += sum(1 for ev in play.get("playEvents", []) if ev.get("isPitch"))
        running_outs = int(play.get("count", {}).get("outs") or running_outs)
        away_sc = int(res.get("awayScore") or away_sc)
        home_sc = int(res.get("homeScore") or home_sc)
    return fired


def main(argv=None) -> int:
    load_env()
    ap = argparse.ArgumentParser(description="Same-day trigger replay (MLB Stats API)")
    ap.add_argument("--date", default=date_cls.today().isoformat())
    args = ap.parse_args(argv)

    constraints, _ = Constraints.load()
    settings = EngineSettings()
    bullpen = settings.load_bullpen_quality()
    tiers = settings.load_starter_tiers()
    real = _real_lines()

    sched = _get(SCHEDULE.format(date=args.date))
    games = [g for d in sched.get("dates", []) for g in d.get("games", [])
             if g["status"]["abstractGameState"] in ("Live", "Final")]
    console.rule(f"[bold]Same-day replay · {args.date} · {len(games)} live/final game(s)")

    all_fired = []
    fired_games_over = 0     # games that fired AND finished Over their line
    fired_games_final = 0    # games that fired AND are Final (outcome known)
    for g in games:
        pk = int(g["gamePk"])
        home_key = resolve(g["teams"]["home"]["team"]["name"])
        pregame = real.get(pk) or round(park_factor(home_key) * LEAGUE_AVG * 2) / 2.0
        src = "real" if pk in real else "proxy"
        try:
            fired = replay_game(_get(FEED.format(pk=pk)), constraints, bullpen, tiers, pregame)
        except Exception as exc:  # noqa: BLE001
            console.log(f"[yellow]{pk} failed: {type(exc).__name__}: {exc}[/]")
            continue
        a, h = g["teams"]["away"], g["teams"]["home"]
        final_tot = (a.get("score") or 0) + (h.get("score") or 0)
        is_final = g["status"]["abstractGameState"] == "Final"
        outcome = ""
        if fired and is_final:
            fired_games_final += 1
            over = final_tot > pregame
            fired_games_over += int(over)
            outcome = "  →  " + ("✅ OVER hit" if over else "❌ Under")
        mark = "🔥" if fired else "  "
        console.print(f"{mark} {a['team']['name']} {a.get('score')} @ {h['team']['name']} "
                      f"{h.get('score')} (tot {final_tot}) · line {pregame} ({src}) · "
                      f"{len(fired)} trigger(s) "
                      + ", ".join(sorted({f'{t.trigger_type}/{t.rule_name}' for t in fired}))
                      + outcome)
        all_fired.extend(fired)

    console.rule("[bold]Summary")
    console.print(f"Total triggers: [bold]{len(all_fired)}[/] across "
                  f"{len({t.game_key for t in all_fired})} game(s).")
    if fired_games_final:
        console.print(f"Of games that fired and are Final: [bold]{fired_games_over}/"
                      f"{fired_games_final}[/] went OVER their line.")
    console.print("[dim]Note: base/out RE24 premium approximated bases-empty; the full "
                  "Statcast simulate_execution replay runs tomorrow once today is published.[/]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
