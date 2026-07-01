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

Revision 2 (methodology hardening):
  * Fix #1 — the signal is the TTO3-top-4 ARRIVAL; NO pitch-count gate (that filter
    weakened the edge via survivorship bias). A dynamic indicator SWEEP ranks
    candidate splits by run-lift reliability (Welch t vs baseline), and starters are
    bucketed into Ace/Mid/Back tiers so we can see which tier carries the edge.
  * Fix #2 — calibrate to RUNS, not ERA (the Over pays on total runs). The report
    validates Statcast RA/9 against true RA/9 (runs) from the MLB Stats API.
The decision matrix (with PC buckets) is retained only to DOCUMENT the survivorship
effect. The emitted constraint is the raw TTO3-top-4 window + a fitted TTOP run
multiplier the live RE24 model uses.

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


def run_environment_report(pa: pd.DataFrame, seasons: list[int]) -> dict:
    """Fix #2: calibrate to RUNS, not ERA. Validate Statcast RA/9 vs true RA/9
    (total runs from the MLB Stats API) — what a live Over actually pays on."""
    from scipy import stats

    agg = pa.groupby("pitcher").agg(outs=("outs", "sum"), R=("runs", "sum"),
                                    H=("is_hit", "sum"), BB=("is_bb", "sum")).reset_index()
    agg = agg[agg["outs"] >= 90]  # >= 30 IP as a starter, to reduce noise
    agg["IP"] = agg["outs"] / 3.0
    agg["RA9_statcast"] = 9.0 * agg["R"] / agg["IP"]
    agg["WHIP_statcast"] = (agg["H"] + agg["BB"]) / agg["IP"]
    agg["pitcher"] = agg["pitcher"].astype(int)

    overall_runs_per_pa = float(pa["runs"].mean())
    truth = _fetch_true_pitching(seasons)
    if truth.empty:
        return {"overall_runs_per_pa": round(overall_runs_per_pa, 4),
                "error": "could not fetch true pitching stats from MLB Stats API"}
    merged = agg.merge(truth, on="pitcher", how="inner").dropna(
        subset=["RA9_statcast", "RA9_true"])
    if len(merged) < 5:
        return {"overall_runs_per_pa": round(overall_runs_per_pa, 4),
                "n": int(len(merged)), "note": "insufficient overlap"}

    ra9_r, ra9_p = stats.pearsonr(merged["RA9_statcast"], merged["RA9_true"])
    slope, intercept = np.polyfit(merged["RA9_statcast"], merged["RA9_true"], 1)
    whip_r, _ = stats.pearsonr(merged["WHIP_statcast"], merged["WHIP_true"])
    return {
        "metric": "total runs (RA/9), not ERA — the Over pays on all runs",
        "true_source": "MLB Stats API season pitching (runs/IP)",
        "n_pitchers": int(len(merged)),
        "overall_runs_per_pa": round(overall_runs_per_pa, 4),
        "statcast_ra9_vs_true_ra9_pearson_r": round(float(ra9_r), 4),
        "statcast_ra9_vs_true_ra9_r_squared": round(float(ra9_r) ** 2, 4),
        "p_value": float(f"{ra9_p:.3e}"),
        "regression": {"slope": round(float(slope), 4),
                       "intercept": round(float(intercept), 4),
                       "formula": "true_RA9 ≈ slope * RA9_statcast + intercept"},
        "statcast_whip_vs_true_whip_r": round(float(whip_r), 4),
        "interpretation": (
            "Statcast run-attribution is a reliable proxy for actual runs allowed"
            if ra9_r >= 0.8 else "RA/9 tracks actual runs only moderately"),
    }


# --------------------------------------------------------------------------- #
# Starter tiers (Fix #1) + dynamic indicator sweep                            #
# --------------------------------------------------------------------------- #
ACE_WHIP, MID_WHIP = 1.10, 1.30


def assign_tiers(pa: pd.DataFrame) -> pd.DataFrame:
    """Tag each PA with the starter's tier from his OWN innings-1-3 baseline WHIP."""
    base = pa[pa["inning"] <= 3]
    g = base.groupby("pitcher").agg(H=("is_hit", "sum"), BB=("is_bb", "sum"),
                                    outs=("outs", "sum"))
    whip = (g["H"] + g["BB"]) / (g["outs"] / 3.0).replace(0, np.nan)
    tier = whip.apply(lambda w: "Ace" if w <= ACE_WHIP else
                      ("Mid" if w <= MID_WHIP else "Back"))
    pa = pa.copy()
    pa["tier"] = pa["pitcher"].map(tier).fillna("Unknown")
    return pa


def indicator_sweep(pa: pd.DataFrame) -> pd.DataFrame:
    """Sweep candidate splits and rank by run-lift reliability (Welch t vs baseline).

    Keeps the methodology DYNAMIC: as data grows, the most robust run-scoring
    indicators re-surface at the top rather than being hardcoded.
    """
    from scipy import stats

    baseline = pa[pa["inning"] <= 3]
    base_runs = baseline["runs"].to_numpy()
    base_rpp = float(base_runs.mean())
    base_ra9 = 9.0 * baseline["runs"].sum() / (baseline["outs"].sum() / 3.0)

    rows = []
    for tto in (2, 3, 4):
        for top_n in (3, 4, 5):
            for pc_label, pc_mask in (("all", pd.Series(True, index=pa.index)),
                                      ("PC>75", pa["entering_pc"] > 75),
                                      ("PC>90", pa["entering_pc"] > 90)):
                for tier in ("All", "Ace", "Mid", "Back"):
                    tier_mask = True if tier == "All" else (pa["tier"] == tier)
                    mask = (pa["slot"] <= top_n) & (pa["tto"] == tto) & pc_mask & tier_mask
                    w = pa[mask]
                    if len(w) < 100:  # skip too-thin cells
                        continue
                    wr = w["runs"].to_numpy()
                    ip = w["outs"].sum() / 3.0
                    t, p = stats.ttest_ind(wr, base_runs, equal_var=False)
                    rows.append({
                        "indicator": f"TTO{tto} top{top_n} {pc_label} {tier}",
                        "BF": len(w), "IP": round(ip, 1),
                        "runs_per_pa": round(float(wr.mean()), 4),
                        "rpp_lift": round(float(wr.mean()) - base_rpp, 4),
                        "RA9": round(9.0 * w["runs"].sum() / ip, 2) if ip else float("nan"),
                        "RA9_lift": round((9.0 * w["runs"].sum() / ip) - base_ra9, 2) if ip else float("nan"),
                        "WHIP": round((w["is_hit"].sum() + w["is_bb"].sum()) / ip, 3) if ip else float("nan"),
                        "welch_t": round(float(t), 2), "welch_p": float(f"{p:.2e}"),
                    })
    sweep = pd.DataFrame(rows)
    # rank: most reliable POSITIVE run lift first (positive t, small p, decent sample).
    sweep["reliable"] = (sweep["rpp_lift"] > 0) & (sweep["welch_p"] < 0.05)
    sweep = sweep.sort_values(["reliable", "welch_t"], ascending=[False, False]).reset_index(drop=True)
    return sweep


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


def render_sweep(sweep: pd.DataFrame, n: int = 12) -> None:
    table = Table(title=f"Dynamic indicator sweep — top {n} by run-lift reliability")
    for col in ("indicator", "BF", "runs_per_pa", "rpp_lift", "RA9_lift", "WHIP", "welch_t", "welch_p"):
        table.add_column(col, justify="right" if col != "indicator" else "left", overflow="fold")
    for _, r in sweep.head(n).iterrows():
        table.add_row(r["indicator"], f"{int(r['BF'])}", f"{r['runs_per_pa']:.3f}",
                      f"{r['rpp_lift']:+.3f}", f"{r['RA9_lift']:+.2f}", f"{r['WHIP']:.3f}",
                      f"{r['welch_t']:.1f}", f"{r['welch_p']:.1e}")
    console.print(table)


def parse_indicator(name: str) -> tuple[int, int, str, str]:
    """'TTO2 top5 all Back' -> (tto=2, top_n=5, pc='all', tier='Back')."""
    parts = name.split()
    return int(parts[0][3:]), int(parts[1][3:]), parts[2], parts[3]


def choose_trigger(pa: pd.DataFrame, sweep: pd.DataFrame) -> dict:
    """Follow the sweep's #1 robust signal automatically (Fix #1, dynamic).

    Adopts the top reliable, NON-pitch-gated, NON-ace indicator as the live trigger
    (its TTO + top-of-order size), fits ``min_inning`` and the TTOP run multiplier to
    that window, and narrows the tier filter to the tiers that actually score above
    baseline there (always excluding aces). Falls back to the canonical 3rd-turn top-4
    thesis if nothing clears the robustness gate.
    """
    base = pa[pa["inning"] <= 3]
    base_rpp = float(base["runs"].mean())
    base_ra9 = 9.0 * base["runs"].sum() / (base["outs"].sum() / 3.0)

    # live-eligible candidates: reliable, no PC gate ("all"), not an Ace-only split.
    cand = sweep[sweep["reliable"] & sweep["indicator"].str.contains(" all ")
                 & ~sweep["indicator"].str.endswith(" Ace")]
    # robustness gate for pivoting off the canonical thesis.
    canonical = (3, 4, "TTO3 top4 all All")
    if len(cand):
        top = cand.iloc[0]
        tto, top_n, _, tier = parse_indicator(top["indicator"])
        undeniable = bool(top["welch_p"] < 1e-6 and top["BF"] >= 2000)
        chosen = (tto, top_n, top["indicator"]) if undeniable else canonical
    else:
        chosen = canonical
    tto, top_n, indicator = chosen

    # which non-ace tiers actually score above baseline at this window (the edge is
    # earlier for weaker arms) — that's what the engine will fire on.
    window = pa[(pa["slot"] <= top_n) & (pa["tto"] == tto)]
    tier_filter = [t for t in ("Mid", "Back")
                   if len(window[window["tier"] == t])
                   and float(window[window["tier"] == t]["runs"].mean()) > base_rpp]
    tier_filter = tier_filter or ["Mid", "Back"]

    # report lift + multiplier for the ACTUAL fired population (window ∩ tier_filter).
    fired = window[window["tier"].isin(tier_filter)]
    fired = fired if len(fired) else window
    win_rpp = float(fired["runs"].mean())
    win_ra9 = 9.0 * fired["runs"].sum() / (fired["outs"].sum() / 3.0)
    return {
        "times_through_order": tto,
        "top_of_order_slots": list(range(1, top_n + 1)),
        "min_inning": int(fired["inning"].median()) if len(fired) else 5,
        "ttop_run_multiplier": round(win_ra9 / base_ra9, 3) if base_ra9 else 1.0,
        "starter_tier_filter": tier_filter,
        "top_indicator": indicator,
        "pivoted": indicator != canonical[2],
        "sample_bf": int(len(fired)),
        "win_ra9": round(win_ra9, 2), "base_ra9": round(base_ra9, 2),
        "expected_ra9_lift": round(win_ra9 - base_ra9, 2),
        "expected_runs_per_pa_lift": round(win_rpp - base_rpp, 4),
    }


def render_tier_lift(pa: pd.DataFrame) -> None:
    base_rpp = float(pa[pa["inning"] <= 3]["runs"].mean())
    window = pa[pa["slot"].isin(TOP_OF_ORDER) & (pa["tto"] == 3)]
    table = Table(title="3rd-turn top-4 run lift by starter tier (ace vs back-of-rotation)")
    for col in ("tier", "BF", "runs_per_pa", "rpp_lift vs baseline"):
        table.add_column(col, justify="right" if col != "tier" else "left")
    for tier in ("Ace", "Mid", "Back", "Unknown"):
        w = window[window["tier"] == tier]
        if not len(w):
            continue
        rpp = float(w["runs"].mean())
        table.add_row(tier, f"{len(w)}", f"{rpp:.3f}", f"{rpp - base_rpp:+.3f}")
    console.print(table)


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

    console.rule("[bold]The Third Turn · TTOP backtest (Revision 2)")
    df = load_statcast(ranges)
    if df.empty:
        console.print("[red]No Statcast data pulled — check connectivity / dates.[/]")
        return 1
    console.log(f"loaded {len(df):,} pitch rows")

    pa = assign_tiers(build_pa_frame(df))
    console.log(f"derived {len(pa):,} starter plate appearances")
    OUT.mkdir(parents=True, exist_ok=True)

    # Documentation matrix (keeps the PC buckets so the survivorship effect is visible).
    mdf = decision_matrix(pa)
    render_matrix(mdf)
    mdf.to_csv(OUT / "ttop_decision_matrix.csv")

    # Fix #1 (dynamic): sweep the indicator grid + tier breakdown.
    console.rule("[bold]Dynamic indicator sweep")
    sweep = indicator_sweep(pa)
    render_sweep(sweep)
    sweep.to_csv(OUT / "indicator_sweep.csv", index=False)
    render_tier_lift(pa)

    # Follow the sweep's #1 robust signal automatically (fall back to canonical).
    trig = choose_trigger(pa, sweep)
    if trig["pivoted"]:
        console.print(f"\n[bold magenta]PIVOT:[/] sweep's #1 signal "
                      f"[bold]{trig['top_indicator']}[/] beats the canonical 3rd-turn "
                      f"thesis — adopting it as the live trigger.")
    else:
        console.print(f"\n[cyan]Canonical 3rd-turn top-4 remains the live trigger[/] "
                      f"(top sweep signal: {trig['top_indicator']}).")

    # Fix #2: calibrate to RUNS, not ERA.
    console.rule("[bold]Run-environment validation (RA/9 vs true runs allowed)")
    try:
        report = run_environment_report(pa, seasons)
        console.print_json(data=report)
    except Exception as exc:  # noqa: BLE001
        console.print(f"[yellow]validation skipped: {type(exc).__name__}: {exc}[/]")
        report = {"error": f"{type(exc).__name__}: {exc}"}
    (OUT / "run_environment_report.json").write_text(json.dumps(report, indent=2))

    constraints = Constraints(
        min_inning=trig["min_inning"], top_of_order_slots=trig["top_of_order_slots"],
        times_through_order=trig["times_through_order"],
        ttop_run_multiplier=trig["ttop_run_multiplier"],
        starter_tier_filter=trig["starter_tier_filter"], pitch_count_reference=None,
        expected_ra9_lift=trig["expected_ra9_lift"],
        expected_runs_per_pa_lift=trig["expected_runs_per_pa_lift"],
        expected_whip_lift=round(float(mdf.loc["3rd time thru, top 4", "WHIP_lift"]), 3),
        seasons=seasons, sample_bf=trig["sample_bf"], top_indicator=trig["top_indicator"],
        ra9_vs_true_ra9_r=report.get("statcast_ra9_vs_true_ra9_pearson_r"),
    )
    constraints.save()
    slots = trig["top_of_order_slots"]
    console.print(f"\n[green]Wrote {OUT/'constraints.json'}[/] — trigger: TTO≥"
                  f"{trig['times_through_order']}, slots {slots[0]}-{slots[-1]}, inning≥"
                  f"{trig['min_inning']}, tiers {trig['starter_tier_filter']}; TTOP "
                  f"multiplier {trig['ttop_run_multiplier']}× "
                  f"(RA/9 {trig['base_ra9']}→{trig['win_ra9']}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
