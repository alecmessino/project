#!/usr/bin/env python3
"""Execution Simulation — replay the LIVE engine logic over historical play-by-play.

Turns the discovery backtest into a "how often does it fire / how often does it win"
report by reconstructing full game state at every starter plate appearance and calling
the SAME predicates the live engine uses (`evaluate_rule` + RE24 + rules + bullpen/tier
tables). It then marks each game Over/Under vs a pre-game total and reports density +
hit rate + conditional hit rate by rule.

Data-gap caveat: no historical live-odds feed is reachable, so the pre-game total is a
**park-adjusted league-average proxy** by default (measures "does firing predict
above-park-average scoring"), or real closing lines via ``--totals-csv game_pk,total``.
Proxy-line profitability is DIRECTIONAL — real lines are needed for true EV.

    python the_third_turn/simulate_execution.py --seasons 2024 2025 2026
    python the_third_turn/simulate_execution.py --seasons 2025 --totals-csv lines.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402

from backtest_thesis import _seasons_to_ranges, assign_tiers, build_pa_frame, load_statcast  # noqa: E402
from config import Constraints, EngineSettings  # noqa: E402
from live_engine import Trigger, _pitching_team, evaluate_rule  # noqa: E402
from shared_piping.ledger import build_row  # noqa: E402
from shared_piping.run_expectancy import park_factor  # noqa: E402
from shared_piping.team_map import resolve  # noqa: E402
from sources.base import LiveGameState, Quote  # noqa: E402

console = Console()
HERE = Path(__file__).resolve().parent
OUT = HERE / "output"
LEAGUE_AVG_TOTAL = 8.6   # MLB average game total (proxy pregame line base)


def _final_totals(df: pd.DataFrame) -> dict[int, float]:
    """Final total runs per game = max(post_bat_score + post_fld_score) over all pitches."""
    tot = (pd.to_numeric(df["post_bat_score"], errors="coerce").fillna(0)
           + pd.to_numeric(df["post_fld_score"], errors="coerce").fillna(0))
    return df.assign(_t=tot).groupby("game_pk")["_t"].max().to_dict()


def _pregame_totals(pa: pd.DataFrame, override: dict[int, float]) -> dict[int, float]:
    """Real closing lines where supplied, else a park-adjusted league-average proxy."""
    homes = pa.groupby("game_pk")["home_team"].first().to_dict()
    out = {}
    for gp, home in homes.items():
        if int(gp) in override:
            out[int(gp)] = override[int(gp)]
        else:
            pk = park_factor(resolve(str(home)))
            out[int(gp)] = round(pk * LEAGUE_AVG_TOTAL * 2) / 2.0
    return out


def _row_to_state(r: dict) -> LiveGameState:
    is_top = str(r["inning_topbot"]).lower().startswith("top")
    return LiveGameState(
        game_pk=int(r["game_pk"]),
        away=resolve(str(r["away_team"])) or "?", home=resolve(str(r["home_team"])) or "?",
        inning=int(r["inning"]), half="top" if is_top else "bottom",
        away_score=int(r.get("away_score") or 0), home_score=int(r.get("home_score") or 0),
        pitcher_id=int(r["pitcher"]), pitcher_name=str(r.get("player_name") or "starter"),
        pitch_count=int(r["entering_pc"]),
        batting_slot_due=int(r["slot"]) if pd.notna(r.get("slot")) else None,
        times_through_order=int(r["tto"]) if pd.notna(r.get("tto")) else None, status="Live",
        outs=int(r["outs_when_up"]) if pd.notna(r.get("outs_when_up")) else None,
        on_first=pd.notna(r.get("on_1b")), on_second=pd.notna(r.get("on_2b")),
        on_third=pd.notna(r.get("on_3b")),
        starter_id=int(r["pitcher"]), starter_on_mound=True,
        starter_tier=str(r.get("tier", "Unknown")), data_age_seconds=None)


def _candidate_mask(pa: pd.DataFrame, rules) -> pd.Series:
    """Cheap vectorized pre-filter so we only build states for rows that could fire."""
    total_runs = (pd.to_numeric(pa["away_score"], errors="coerce").fillna(0)
                  + pd.to_numeric(pa["home_score"], errors="coerce").fillna(0))
    mask = pd.Series(False, index=pa.index)
    for r in rules:
        if r.kind == "watch":
            mask |= (pa["inning"].between(2, r.watch_max_inning)) & (total_runs <= r.watch_max_runs)
        else:
            top = pa["slot"] <= max(r.top_of_order_slots)
            mask |= top & (pa["tto"] == r.times_through_order)              # CONFIRM
            mask |= (pa["outs_when_up"] == 2) & pa["slot"].isin([8, 9]) \
                & (pa["tto"] == r.times_through_order - 1)                  # ARM
    return mask


def simulate(pa: pd.DataFrame, rules, c: Constraints, bullpen: dict,
             pregame: dict[int, float], finals: dict[int, float]) -> list[dict]:
    cand = pa[_candidate_mask(pa, rules)]
    console.log(f"evaluating {len(cand):,} candidate states (of {len(pa):,} PAs)")
    seen: set[str] = set()
    ledger_rows: list[dict] = []
    for r in cand.to_dict("records"):
        gp = int(r["game_pk"])
        pg = pregame.get(gp)
        if pg is None:
            continue
        state = _row_to_state(r)
        quote = Quote(book="sim", home=state.home, away=state.away, line=pg)
        pen = bullpen.get(_pitching_team(state))
        for rule in rules:
            for trig in evaluate_rule(rule, state, quote, pg, c, pen):
                if trig.dedupe_key in seen:
                    continue
                seen.add(trig.dedupe_key)
                final = finals.get(gp)
                outcome = ("Over" if final > pg else "Under" if final < pg else "Push") \
                    if final is not None else "Unknown"
                ledger_rows.append(build_row(
                    trig, bullpen_elite_ra9=c.bullpen_elite_ra9, ts=str(r.get("game_date")),
                    extra={"final_total": final, "outcome": outcome}))
    return ledger_rows


def report(rows: list[dict], n_game_days: int, n_games: int) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    lines = []
    def hit_rate(sub):
        decided = sub[sub["outcome"].isin(["Over", "Under"])]
        return (100.0 * (decided["outcome"] == "Over").mean()) if len(decided) else float("nan")

    overall = {
        "rule_name": "ALL", "trigger_type": "*", "fires": len(df),
        "fires_per_game_day": round(len(df) / n_game_days, 2) if n_game_days else 0,
        "fires_per_game": round(len(df) / n_games, 3) if n_games else 0,
        "hit_rate_over_%": round(hit_rate(df), 1) if len(df) else float("nan"),
    }
    lines.append(overall)
    for (rule, ttype), sub in df.groupby(["rule_name", "trigger_type"]):
        lines.append({
            "rule_name": rule, "trigger_type": ttype, "fires": len(sub),
            "fires_per_game_day": round(len(sub) / n_game_days, 2) if n_game_days else 0,
            "fires_per_game": round(len(sub) / n_games, 3) if n_games else 0,
            "hit_rate_over_%": round(hit_rate(sub), 1),
        })
    return pd.DataFrame(lines)


def _load_override(path: str | None) -> dict[int, float]:
    if not path:
        return {}
    out = {}
    with open(path) as fh:
        for row in csv.DictReader(fh):
            try:
                out[int(row["game_pk"])] = float(row["pregame_total"])
            except (KeyError, ValueError):
                continue
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Execution simulation")
    ap.add_argument("--seasons", type=int, nargs="+", default=[2025])
    ap.add_argument("--start"); ap.add_argument("--end")
    ap.add_argument("--totals-csv", help="game_pk,pregame_total closing lines (optional)")
    args = ap.parse_args(argv)

    ranges = ([(args.start, args.end)] if args.start and args.end
              else _seasons_to_ranges(args.seasons))

    console.rule("[bold]The Third Turn · Execution Simulation")
    df = load_statcast(ranges)
    if df.empty:
        console.print("[red]No Statcast data pulled.[/]"); return 1
    finals = _final_totals(df)
    pa = assign_tiers(build_pa_frame(df))

    constraints, from_file = Constraints.load()
    if not from_file:
        console.print("[yellow]No constraints.json — using default rules.[/]")
    rules = constraints.rules   # include disabled WATCH so its hit-rate is measured
    settings = EngineSettings()
    bullpen = settings.load_bullpen_quality()
    pregame = _pregame_totals(pa, _load_override(args.totals_csv))
    proxy = not args.totals_csv

    rows = simulate(pa, rules, constraints, bullpen, pregame, finals)
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "simulation_ledger.jsonl").open("w") as fh:
        for r in rows:
            import json
            fh.write(json.dumps(r) + "\n")

    n_games = pa["game_pk"].nunique()
    n_game_days = pa["game_date"].nunique() if "game_date" in pa.columns else 1
    rep = report(rows, n_game_days, n_games)
    rep.to_csv(OUT / "report.csv", index=False)

    table = Table(title=f"Execution simulation — {n_games} games, {n_game_days} game-days"
                        + ("  [PROXY LINE]" if proxy else "  [REAL LINES]"))
    for col in rep.columns:
        table.add_column(col, justify="left" if col == "rule_name" else "right")
    for _, r in rep.iterrows():
        table.add_row(*[str(r[c]) for c in rep.columns])
    console.print(table)
    if proxy:
        console.print("[yellow]NOTE:[/] pregame totals are a park-adjusted league-average "
                      "PROXY — hit rates measure 'fires → above-average scoring', not true "
                      "closing-line edge. Supply --totals-csv real lines for EV.")
    console.print(f"[green]Wrote {OUT/'report.csv'} and {OUT/'simulation_ledger.jsonl'}[/]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
