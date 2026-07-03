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
import statistics
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


# --- Option C: matchup-based proxy line (starter RA/9 + bullpen RA/9 × park) ---
SP_IP, RP_IP = 5.3, 3.7   # avg starter / bullpen innings split over a 9-inning game


def _starter_ra9(pa: pd.DataFrame) -> dict[int, float]:
    """Pitcher id -> season RA/9 as a starter, from the cached PA frame."""
    g = pa.groupby("pitcher").agg(runs=("runs", "sum"), outs=("outs", "sum"))
    g = g[g["outs"] >= 90]                     # >= 30 IP; thinner samples fall back to league
    return (9.0 * g["runs"] / (g["outs"] / 3.0)).to_dict()


def _game_starters(pa: pd.DataFrame) -> dict[int, tuple]:
    """game_pk -> (away_sp_id, home_sp_id, away_key, home_key). Home pitches the top half."""
    out = {}
    for gp, sub in pa.groupby("game_pk"):
        top = sub[sub["inning_topbot"].astype(str).str.lower().str.startswith("top")]
        bot = sub[sub["inning_topbot"].astype(str).str.lower().str.startswith("bot")]
        home_sp = int(top["pitcher"].iloc[0]) if len(top) else None
        away_sp = int(bot["pitcher"].iloc[0]) if len(bot) else None
        out[int(gp)] = (away_sp, home_sp, resolve(str(sub["away_team"].iloc[0])),
                        resolve(str(sub["home_team"].iloc[0])))
    return out


def _matchup_pregame_totals(pa: pd.DataFrame, override: dict[int, float],
                            bullpen: dict) -> dict[int, float]:
    """Game-specific line: each side's runs-allowed (starter+bullpen blend), park-scaled.

    total = park · (away_side_RA + home_side_RA), where a side's RA/game is
    (SP_RA9·SP_IP + PEN_RA9·RP_IP)/9. Good-pitching matchups get lower lines, so the
    RE24 gate clears less often — deflating the phantom edge. Real lines still win.
    """
    sra = _starter_ra9(pa)
    starters = _game_starters(pa)
    lg_sp = statistics.median(sra.values()) if sra else 4.4
    lg_pen = statistics.median(bullpen.values()) if bullpen else 4.3
    out = {}
    for gp, (asp, hsp, away, home) in starters.items():
        if gp in override:
            out[gp] = override[gp]
            continue
        away_side = (sra.get(asp, lg_sp) * SP_IP + bullpen.get(away, lg_pen) * RP_IP) / 9.0
        home_side = (sra.get(hsp, lg_sp) * SP_IP + bullpen.get(home, lg_pen) * RP_IP) / 9.0
        total = park_factor(home) * (away_side + home_side)
        out[gp] = round(total * 2) / 2.0
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
             pregame: dict[int, float], finals: dict[int, float],
             real_keys: set[int], real_only: bool = False) -> list[dict]:
    cand = pa[_candidate_mask(pa, rules)]
    console.log(f"evaluating {len(cand):,} candidate states (of {len(pa):,} PAs)")
    seen: set[str] = set()
    ledger_rows: list[dict] = []
    for r in cand.to_dict("records"):
        gp = int(r["game_pk"])
        pg = pregame.get(gp)
        if pg is None:
            continue
        source = "real" if gp in real_keys else "proxy"
        if real_only and source != "real":
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
                    extra={"final_total": final, "outcome": outcome, "line_source": source}))
    return ledger_rows


def report(rows: list[dict], n_game_days: int, n_games: int) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    lines = []
    def hit_rate(sub):
        decided = sub[sub["outcome"].isin(["Over", "Under"])]
        return (100.0 * (decided["outcome"] == "Over").mean()) if len(decided) else float("nan")

    def summary(name, ttype, sub):
        return {
            "rule_name": name, "trigger_type": ttype, "fires": len(sub),
            "fires_per_game_day": round(len(sub) / n_game_days, 2) if n_game_days else 0,
            "fires_per_game": round(len(sub) / n_games, 3) if n_games else 0,
            "hit_rate_over_%": round(hit_rate(sub), 1) if len(sub) else float("nan"),
        }

    lines.append(summary("ALL", "*", df))
    # honest split: true (real closing line) vs proxy (park-average).
    if "line_source" in df.columns and df["line_source"].nunique() > 1:
        for src, sub in df.groupby("line_source"):
            lines.append(summary(f"ALL ({src})", "*", sub))
    for (rule, ttype), sub in df.groupby(["rule_name", "trigger_type"]):
        lines.append(summary(rule, ttype, sub))
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
    ap.add_argument("--real-only", action="store_true",
                    help="restrict to games with a real closing line (true hit rate)")
    ap.add_argument("--proxy", choices=["matchup", "park"], default="matchup",
                    help="pregame line model when no real line: matchup (starter+bullpen×park) "
                         "or park (flat league-avg×park)")
    ap.add_argument("--edge-floor", type=float, default=None,
                    help="override every rule's line_edge_min_runs (e.g. -99 to record "
                         "ALL state-matched windows for an edge-threshold sweep)")
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
    if args.edge_floor is not None:
        # record every state-matched window regardless of line edge (threshold sweep)
        constraints.line_edge_min_runs = args.edge_floor
        for r in rules:
            r.line_edge_min_runs = args.edge_floor
        console.log(f"[yellow]edge gate floored at {args.edge_floor} — sweep mode[/]")
    settings = EngineSettings()
    bullpen = settings.load_bullpen_quality()
    override = _load_override(args.totals_csv)
    pregame = (_matchup_pregame_totals(pa, override, bullpen) if args.proxy == "matchup"
               else _pregame_totals(pa, override))
    real_keys = set(override)
    proxy = not override

    rows = simulate(pa, rules, constraints, bullpen, pregame, finals,
                    real_keys=real_keys, real_only=args.real_only)
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "simulation_ledger.jsonl").open("w") as fh:
        for r in rows:
            import json
            fh.write(json.dumps(r) + "\n")

    n_games = pa["game_pk"].nunique()
    n_game_days = pa["game_date"].nunique() if "game_date" in pa.columns else 1
    rep = report(rows, n_game_days, n_games)
    rep.to_csv(OUT / "report.csv", index=False)

    base_tag = ("[PROXY]" if proxy else (f"[REAL-ONLY: {len(real_keys)}]" if args.real_only
                                         else f"[MIXED: {len(real_keys)} real]"))
    table = Table(title=f"Execution simulation — {n_games} games, {n_game_days} game-days  "
                        f"{base_tag} · {args.proxy} proxy")
    for col in rep.columns:
        table.add_column(col, justify="left" if col == "rule_name" else "right")
    for _, r in rep.iterrows():
        table.add_row(*[str(r[c]) for c in rep.columns])
    console.print(table)
    if proxy:
        model = ("matchup model (starter+bullpen RA/9 × park)" if args.proxy == "matchup"
                 else "flat park-average")
        console.print(f"[yellow]NOTE:[/] pregame totals are a {model} PROXY, not a market "
                      "line — hit rates are directional, not true closing-line EV. Supply "
                      "--totals-csv real lines (collected forward by odds_collector.py) for EV.")
    console.print(f"[green]Wrote {OUT/'report.csv'} and {OUT/'simulation_ledger.jsonl'}[/]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
