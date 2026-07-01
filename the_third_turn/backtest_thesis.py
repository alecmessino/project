#!/usr/bin/env python3
"""OBJECTIVE 1 — Historical Validator for the Time-Through-Order Penalty (TTOP).

Thesis: a starting pitcher facing the top of the order for the 3rd time degrades
enough to make the live Over +EV. This script measures that edge from MLB Statcast
pitch-by-pitch data and emits the exact constraint parameters the live engine uses.

What it computes, per starter, from raw pitches:
  * starter identity     = pitcher at the minimum at_bat_number on each pitching side
  * lineup slot          = order of first appearance vs the starter (top 4 = slots 1-4)
  * times-through-order  = per-batter PA rank vs the starter
  * entering pitch count = starter's cumulative pitches before each PA
  * per-PA outcomes      = H / BB / outs (from `events`) and runs (post_bat_score-bat_score)

Windows compared (WHIP exact, RA/9 from runs):
  innings 1-3 (baseline)  vs  {3rd-time-thru top-4}  and that split by PC>75/85/90.

Decision matrix answers: "is the edge higher when PC>75 OR PC>90?" (bigger lift wins).

ERA calibration (second source): season RA/9 (from Statcast) vs true ERA + WHIP
(FanGraphs via pybaseball.pitching_stats) -> Pearson r, R^2, regression, so we know
how reliably the quick RA/9 proxy tracks true ERA before the engine leans on it.

    python the_third_turn/backtest_thesis.py --seasons 2025
    python the_third_turn/backtest_thesis.py --seasons 2024 2025 2026
    python the_third_turn/backtest_thesis.py --start 2025-04-01 --end 2025-05-15   # fast slice
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402

from config import Constraints  # noqa: E402

console = Console()
HERE = Path(__file__).resolve().parent
OUT = HERE / "output"

LINEUP_SIZE = 9
TOP_OF_ORDER = [1, 2, 3, 4]
PITCH_CUTS = [75, 85, 90]

# events -> outs recorded (only terminal PA events appear on the last pitch row).
OUTS_BY_EVENT = {
    "strikeout": 1, "field_out": 1, "force_out": 1, "sac_fly": 1, "sac_bunt": 1,
    "fielders_choice_out": 1, "other_out": 1, "caught_stealing_2b": 0,
    "grounded_into_double_play": 2, "double_play": 2, "strikeout_double_play": 2,
    "sac_fly_double_play": 2, "triple_play": 3, "fielders_choice": 1,
}
HIT_EVENTS = {"single", "double", "triple", "home_run"}
WALK_EVENTS = {"walk", "intent_walk"}
HBP_EVENTS = {"hit_by_pitch"}


# --------------------------------------------------------------------------- #
# Data loading                                                                #
# --------------------------------------------------------------------------- #
def _seasons_to_ranges(seasons: list[int]) -> list[tuple[str, str]]:
    """Regular-season-ish date ranges per year (Statcast has no offseason rows)."""
    ranges = []
    for yr in seasons:
        # 2026 is YTD; cap the end at 'today' via a generous bound Statcast clips.
        ranges.append((f"{yr}-03-15", f"{yr}-11-15"))
    return ranges


def load_statcast(ranges: list[tuple[str, str]]) -> pd.DataFrame:
    """Pull Statcast pitch data in monthly chunks with pybaseball's disk cache."""
    import pybaseball
    pybaseball.cache.enable()
    from pybaseball import statcast

    frames = []
    for start, end in ranges:
        months = pd.date_range(start=start, end=end, freq="MS").union(
            pd.to_datetime([start, end]))
        months = sorted(set(months))
        for i in range(len(months) - 1):
            s = months[i].strftime("%Y-%m-%d")
            e = (months[i + 1]).strftime("%Y-%m-%d")
            console.log(f"pulling Statcast {s} … {e}")
            try:
                df = statcast(start_dt=s, end_dt=e, verbose=False)
            except Exception as exc:  # noqa: BLE001
                console.log(f"[yellow]chunk {s}..{e} failed: {exc}[/]")
                continue
            if df is not None and len(df):
                frames.append(df)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


# --------------------------------------------------------------------------- #
# Per-PA feature derivation                                                    #
# --------------------------------------------------------------------------- #
def build_pa_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse pitch rows to one row per starter plate appearance with features."""
    need = ["game_pk", "inning_topbot", "at_bat_number", "pitch_number", "pitcher",
            "batter", "inning", "events", "bat_score", "post_bat_score"]
    df = df.dropna(subset=["game_pk", "inning_topbot", "at_bat_number",
                           "pitcher", "batter"]).copy()
    for c in ["at_bat_number", "pitch_number", "inning", "pitcher", "batter"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["at_bat_number", "pitcher", "batter"])

    # Starter per pitching side = pitcher at the smallest at_bat_number.
    key = ["game_pk", "inning_topbot"]
    starter_idx = df.groupby(key)["at_bat_number"].idxmin()
    starters = df.loc[starter_idx, key + ["pitcher"]].rename(
        columns={"pitcher": "starter"})
    df = df.merge(starters, on=key, how="left")
    df = df[df["pitcher"] == df["starter"]].copy()   # starter's pitches only

    # pitches per PA + entering pitch count (cumulative before the PA).
    df.sort_values(key + ["at_bat_number", "pitch_number"], inplace=True)
    pitches = df.groupby(key + ["at_bat_number"]).size().rename("pa_pitches")

    # last pitch of each PA carries the terminal `events` + final score.
    pa = df.groupby(key + ["at_bat_number"]).tail(1).merge(
        pitches, on=key + ["at_bat_number"], how="left")
    pa.sort_values(key + ["at_bat_number"], inplace=True)
    pa["entering_pc"] = (pa.groupby(key)["pa_pitches"].cumsum() - pa["pa_pitches"])

    # lineup slot = order of first appearance vs the starter.
    first_ab = pa.groupby(key + ["batter"])["at_bat_number"].transform("min")
    pa["_first_ab"] = first_ab
    slot = (pa.drop_duplicates(key + ["batter"])
              .sort_values(key + ["_first_ab"])
              .groupby(key).cumcount() + 1)
    slot_map = pa.drop_duplicates(key + ["batter"]).assign(slot=slot.values)[
        key + ["batter", "slot"]]
    pa = pa.merge(slot_map, on=key + ["batter"], how="left")

    # times-through-order = per-batter PA rank vs the starter.
    pa["tto"] = pa.groupby(key + ["batter"])["at_bat_number"].rank("dense").astype(int)

    # outcomes
    ev = pa["events"].fillna("").astype(str)
    pa["is_hit"] = ev.isin(HIT_EVENTS).astype(int)
    pa["is_bb"] = ev.isin(WALK_EVENTS).astype(int)
    pa["is_hbp"] = ev.isin(HBP_EVENTS).astype(int)
    pa["outs"] = ev.map(OUTS_BY_EVENT).fillna(0).astype(int)
    runs = pd.to_numeric(pa["post_bat_score"], errors="coerce") - pd.to_numeric(
        pa["bat_score"], errors="coerce")
    pa["runs"] = runs.fillna(0).clip(lower=0).astype(int)
    return pa


# --------------------------------------------------------------------------- #
# Window metrics                                                               #
# --------------------------------------------------------------------------- #
def window_metrics(pa: pd.DataFrame, mask) -> dict:
    w = pa[mask]
    bf = len(w)
    outs = int(w["outs"].sum())
    ip = outs / 3.0
    h, bb, hbp = int(w["is_hit"].sum()), int(w["is_bb"].sum()), int(w["is_hbp"].sum())
    runs = int(w["runs"].sum())
    whip = (h + bb) / ip if ip else float("nan")
    ra9 = 9.0 * runs / ip if ip else float("nan")
    return {"BF": bf, "IP": round(ip, 1), "H": h, "BB": bb, "HBP": hbp,
            "R": runs, "WHIP": whip, "RA9": ra9}


def decision_matrix(pa: pd.DataFrame) -> pd.DataFrame:
    top = pa["slot"].isin(TOP_OF_ORDER)
    tto3 = pa["tto"] == 3
    rows = {
        "Innings 1-3 (baseline)": pa["inning"] <= 3,
        "3rd time thru, top 4": top & tto3,
    }
    for cut in PITCH_CUTS:
        rows[f"3rd/top4 & PC>{cut}"] = top & tto3 & (pa["entering_pc"] > cut)
    data = {name: window_metrics(pa, mask) for name, mask in rows.items()}
    mdf = pd.DataFrame(data).T
    base = mdf.loc["Innings 1-3 (baseline)"]
    mdf["WHIP_lift"] = mdf["WHIP"] - base["WHIP"]
    mdf["RA9_lift"] = mdf["RA9"] - base["RA9"]
    return mdf


# --------------------------------------------------------------------------- #
# ERA calibration (second source = MLB Stats API season pitching)             #
# --------------------------------------------------------------------------- #
# FanGraphs (403) and the Chadwick register (download blocked) are unreachable
# from this environment, so the "true ERA" second source is the MLB Stats API,
# which serves season ERA/WHIP/ER keyed by MLBAM id — a direct join to Statcast's
# `pitcher` id, no fragile name-matching.
STATS_URL = ("https://statsapi.mlb.com/api/v1/stats?stats=season&group=pitching"
             "&season={season}&sportId=1&gameType=R&playerPool=all&limit=500&offset={offset}")


def _ip_to_float(ip) -> float:
    """Baseball IP notation ('187.2' = 187 + 2/3) -> decimal innings."""
    try:
        whole, _, frac = str(ip).partition(".")
        return float(whole or 0) + (float(frac[:1] or 0) / 3.0)
    except (TypeError, ValueError):
        return 0.0


def _fetch_true_pitching(seasons: list[int]) -> pd.DataFrame:
    """Combined true ER/R/IP per MLBAM pitcher id across the seasons (statsapi)."""
    import urllib.request
    from shared_piping.headers import rotating_headers

    rows: dict[int, dict] = {}
    for season in seasons:
        offset = 0
        while True:
            url = STATS_URL.format(season=season, offset=offset)
            req = urllib.request.Request(url, headers=rotating_headers())
            try:
                data = json.loads(urllib.request.urlopen(req, timeout=30).read())
            except Exception as exc:  # noqa: BLE001
                console.log(f"[yellow]stats {season}@{offset} failed: {exc}[/]")
                break
            splits = data.get("stats", [{}])[0].get("splits", [])
            if not splits:
                break
            for sp in splits:
                pid = sp.get("player", {}).get("id")
                st = sp.get("stat", {})
                ip = _ip_to_float(st.get("inningsPitched"))
                if pid is None or ip <= 0:
                    continue
                agg = rows.setdefault(int(pid), {"ER": 0.0, "R": 0.0, "IP": 0.0,
                                                 "H": 0.0, "BB": 0.0})
                agg["ER"] += float(st.get("earnedRuns", 0) or 0)
                agg["R"] += float(st.get("runs", 0) or 0)
                agg["IP"] += ip
                agg["H"] += float(st.get("hits", 0) or 0)
                agg["BB"] += float(st.get("baseOnBalls", 0) or 0)
            if len(splits) < 500:
                break
            offset += 500
    if not rows:
        return pd.DataFrame()
    out = pd.DataFrame([{"pitcher": k, **v} for k, v in rows.items()])
    out["ERA_true"] = 9.0 * out["ER"] / out["IP"]
    out["RA9_true"] = 9.0 * out["R"] / out["IP"]
    out["WHIP_true"] = (out["H"] + out["BB"]) / out["IP"]
    return out


def era_calibration(pa: pd.DataFrame, seasons: list[int]) -> dict:
    """Season RA/9 (Statcast) vs true ERA + WHIP (MLB Stats API) -> correlation."""
    from scipy import stats

    agg = pa.groupby("pitcher").agg(outs=("outs", "sum"), R=("runs", "sum"),
                                    H=("is_hit", "sum"), BB=("is_bb", "sum")).reset_index()
    agg = agg[agg["outs"] >= 90]  # >= 30 IP as a starter, to reduce noise
    agg["IP"] = agg["outs"] / 3.0
    agg["RA9_statcast"] = 9.0 * agg["R"] / agg["IP"]
    agg["WHIP_statcast"] = (agg["H"] + agg["BB"]) / agg["IP"]
    agg["pitcher"] = agg["pitcher"].astype(int)

    truth = _fetch_true_pitching(seasons)
    if truth.empty:
        return {"error": "could not fetch true pitching stats from MLB Stats API"}
    merged = agg.merge(truth, on="pitcher", how="inner").dropna(
        subset=["RA9_statcast", "ERA_true"])
    if len(merged) < 5:
        return {"n": int(len(merged)), "note": "insufficient overlap for calibration"}

    r, p = stats.pearsonr(merged["RA9_statcast"], merged["ERA_true"])
    slope, intercept = np.polyfit(merged["RA9_statcast"], merged["ERA_true"], 1)
    ra9_r, _ = stats.pearsonr(merged["RA9_statcast"], merged["RA9_true"])
    whip_r, _ = stats.pearsonr(merged["WHIP_statcast"], merged["WHIP_true"])
    return {
        "n_pitchers": int(len(merged)),
        "true_source": "MLB Stats API season pitching (earnedRuns/IP)",
        "ra9_to_era_pearson_r": round(float(r), 4),
        "ra9_to_era_r_squared": round(float(r) ** 2, 4),
        "ra9_to_era_p_value": float(f"{p:.3e}"),
        "regression": {"slope": round(float(slope), 4),
                       "intercept": round(float(intercept), 4),
                       "formula": "true_ERA ≈ slope * RA9_statcast + intercept"},
        "statcast_ra9_vs_true_ra9_r": round(float(ra9_r), 4),
        "statcast_whip_vs_true_whip_r": round(float(whip_r), 4),
        "interpretation": (
            "RA/9 from Statcast is a reliable proxy for true ERA" if r >= 0.8 else
            "RA/9 tracks ERA only moderately — treat window RA/9 as directional"),
    }


# --------------------------------------------------------------------------- #
# Orchestration                                                                #
# --------------------------------------------------------------------------- #
def render_matrix(mdf: pd.DataFrame) -> None:
    table = Table(title="TTOP decision matrix (starter, per plate appearance)")
    table.add_column("Window", overflow="fold")
    for col in ["BF", "IP", "H", "BB", "R", "WHIP", "RA9", "WHIP_lift", "RA9_lift"]:
        table.add_column(col, justify="right")
    for name, row in mdf.iterrows():
        table.add_row(name, f"{int(row['BF'])}", f"{row['IP']:.1f}", f"{int(row['H'])}",
                      f"{int(row['BB'])}", f"{int(row['R'])}", f"{row['WHIP']:.3f}",
                      f"{row['RA9']:.2f}", f"{row['WHIP_lift']:+.3f}",
                      f"{row['RA9_lift']:+.2f}")
    console.print(table)


def choose_cliff(mdf: pd.DataFrame) -> tuple[int, str]:
    """Answer '>75 vs >90': the cut with the larger WHIP lift over baseline."""
    lift75 = mdf.loc["3rd/top4 & PC>75", "WHIP_lift"]
    lift90 = mdf.loc["3rd/top4 & PC>90", "WHIP_lift"]
    if lift90 >= lift75:
        return 90, (f"Edge is HIGHER at PC>90 (WHIP lift {lift90:+.3f}) "
                    f"than PC>75 ({lift75:+.3f}).")
    return 75, (f"Edge is HIGHER at PC>75 (WHIP lift {lift75:+.3f}) "
                f"than PC>90 ({lift90:+.3f}).")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="TTOP historical validator")
    ap.add_argument("--seasons", type=int, nargs="+", default=[2025],
                    help="season years to analyze (e.g. 2024 2025 2026)")
    ap.add_argument("--start", help="explicit start date YYYY-MM-DD (overrides seasons)")
    ap.add_argument("--end", help="explicit end date YYYY-MM-DD (overrides seasons)")
    args = ap.parse_args(argv)

    if args.start and args.end:
        ranges = [(args.start, args.end)]
        seasons = [int(args.start[:4])]
    else:
        ranges = _seasons_to_ranges(args.seasons)
        seasons = args.seasons

    console.rule("[bold]The Third Turn · TTOP backtest")
    df = load_statcast(ranges)
    if df.empty:
        console.print("[red]No Statcast data pulled — check connectivity / dates.[/]")
        return 1
    console.log(f"loaded {len(df):,} pitch rows")

    pa = build_pa_frame(df)
    console.log(f"derived {len(pa):,} starter plate appearances")

    mdf = decision_matrix(pa)
    render_matrix(mdf)
    OUT.mkdir(parents=True, exist_ok=True)
    mdf.to_csv(OUT / "ttop_decision_matrix.csv")

    cliff, verdict = choose_cliff(mdf)
    console.print(f"\n[bold cyan]CONSTRAINT FINDING:[/] {verdict}")

    tto3_top4 = pa[pa["slot"].isin(TOP_OF_ORDER) & (pa["tto"] == 3)]
    min_inning = int(tto3_top4["inning"].median()) if len(tto3_top4) else 6

    console.rule("[bold]ERA calibration (RA/9 proxy vs true ERA)")
    try:
        calib = era_calibration(pa, seasons)
        console.print_json(data=calib)
    except Exception as exc:  # noqa: BLE001
        console.print(f"[yellow]calibration skipped: {type(exc).__name__}: {exc}[/]")
        calib = {"error": f"{type(exc).__name__}: {exc}"}
    (OUT / "era_calibration_report.json").write_text(json.dumps(calib, indent=2))

    row = mdf.loc[f"3rd/top4 & PC>{cliff}"]
    constraints = Constraints(
        min_inning=min_inning, top_of_order_slots=TOP_OF_ORDER, times_through_order=3,
        pitch_count_threshold=cliff, line_drop_max_runs=1.5,
        expected_whip_lift=round(float(row["WHIP_lift"]), 3),
        expected_ra9_lift=round(float(row["RA9_lift"]), 2),
        seasons=seasons, sample_bf=int(row["BF"]),
        ra9_to_era_r=calib.get("ra9_to_era_pearson_r"),
    )
    constraints.save()
    console.print(f"\n[green]Wrote {OUT/'constraints.json'}[/] — engine will trigger at "
                  f"inning≥{min_inning}, TTO≥3, top-4, PC>{cliff}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
