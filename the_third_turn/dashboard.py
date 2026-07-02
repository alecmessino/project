#!/usr/bin/env python3
"""The Third Turn — Streamlit control center.

Interactive view of what the engine is caching and alerting:
  * Metrics cards — total alerts + CONFIRM/ARM/WATCH breakdown + historical edge
    (vs the deflated matchup-proxy baseline from output/report.csv).
  * Live Ledger tab — output/ledger.jsonl, filterable by team and signal type.
  * Market Audit tab — data/closing_lines.csv (real + collected pregame lines).

    streamlit run the_third_turn/dashboard.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

HERE = Path(__file__).resolve().parent
LEDGER = HERE / "output" / "ledger.jsonl"
LINES = HERE / "data" / "closing_lines.csv"
REPORT = HERE / "output" / "report.csv"
BREAKEVEN = 52.38   # -110 juice breakeven %

st.set_page_config(page_title="The Third Turn · Control Center", layout="wide")


def load_ledger() -> pd.DataFrame:
    if not LEDGER.exists():
        return pd.DataFrame()
    rows = []
    for line in LEDGER.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return pd.DataFrame(rows)


def baseline_hit_rate() -> float | None:
    if not REPORT.exists():
        return None
    rep = pd.read_csv(REPORT)
    row = rep[rep["rule_name"] == "ALL"]
    return float(row.iloc[0]["hit_rate_over_%"]) if len(row) else None


@st.cache_data(ttl=120)
def fetch_finals(dates: tuple[str, ...]) -> dict[int, float]:
    """Final total runs per game_pk for the ledger's game dates (MLB Stats API)."""
    import urllib.request
    finals: dict[int, float] = {}
    for d in dates:
        url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={d}"
        try:
            data = json.loads(urllib.request.urlopen(
                urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}),
                timeout=15).read())
        except Exception:
            continue
        for day in data.get("dates", []):
            for g in day.get("games", []):
                if g["status"]["abstractGameState"] == "Final":
                    a = g["teams"]["away"].get("score") or 0
                    h = g["teams"]["home"].get("score") or 0
                    finals[int(g["gamePk"])] = float(a + h)
    return finals


def with_outcomes(ledger: pd.DataFrame) -> pd.DataFrame:
    """Join finals -> W/L/Push/Pending + units at -110 per DELIVERED alert."""
    if ledger.empty:
        return ledger
    df = ledger.copy()
    # a fire's game date: alerts after midnight UTC belong to the previous ET slate
    dates = tuple(sorted({(pd.Timestamp(ts) - pd.Timedelta(hours=9)).date().isoformat()
                          for ts in df["ts"].dropna()}))
    finals = fetch_finals(dates)
    bet_line = df.get("verified_line").fillna(df["live_total"]) \
        if "verified_line" in df.columns else df["live_total"]
    df["bet_line"] = bet_line
    df["final_total"] = df["game_pk"].map(finals)
    df["suppressed"] = df.get("suppressed_stale_feed", False)
    df["suppressed"] = df["suppressed"].fillna(False).astype(bool)

    def outcome(r):
        if pd.isna(r["final_total"]):
            return "Pending"
        if r["final_total"] > r["bet_line"]:
            return "Win"
        if r["final_total"] < r["bet_line"]:
            return "Loss"
        return "Push"

    df["result"] = df.apply(outcome, axis=1)
    df["units"] = df.apply(
        lambda r: 0.0 if (r["suppressed"] or r["result"] in ("Pending", "Push"))
        else (100 / 110 if r["result"] == "Win" else -1.0), axis=1)
    return df


st.title("⚾ The Third Turn · Control Center")
if st.button("🔄 Refresh"):
    st.rerun()

ledger = with_outcomes(load_ledger())

# ---- Metrics cards ----------------------------------------------------------
total = len(ledger)
delivered = ledger[~ledger["suppressed"]] if total else ledger
by_type = ledger["trigger_type"].value_counts().to_dict() if total else {}
base = baseline_hit_rate()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total alerts fired", total)
c2.metric("🔴 CONFIRM", by_type.get("CONFIRM", 0))
c3.metric("🟡 ARM", by_type.get("ARM", 0))
c4.metric("⛔ Suppressed", int(ledger["suppressed"].sum()) if total else 0)
if base is not None:
    c5.metric("Historical edge (matchup proxy)", f"{base:.1f}%",
              delta=f"{base - BREAKEVEN:+.1f}% vs breakeven")
else:
    c5.metric("Historical edge", "run backtest")

# ---- LIVE P&L (the truth row: real alerts vs real finals) --------------------
if total:
    decided = delivered[delivered["result"].isin(["Win", "Loss"])]
    wins = int((decided["result"] == "Win").sum())
    losses = int((decided["result"] == "Loss").sum())
    units = float(delivered["units"].sum())
    live_hr = 100 * wins / len(decided) if len(decided) else float("nan")
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Live record (delivered)", f"{wins}–{losses}")
    p2.metric("Live hit rate", f"{live_hr:.0f}%" if len(decided) else "—",
              delta=(f"{live_hr - BREAKEVEN:+.1f}% vs breakeven" if len(decided) else None))
    p3.metric("Units (flat 1u @ −110)", f"{units:+.2f}")
    p4.metric("Pending", int((delivered["result"] == "Pending").sum()))
    st.caption("LIVE results vs real finals — the number that matters. The proxy edge above "
               "is model-vs-model; this row is model-vs-market.")

tab_ledger, tab_market, tab_suppressed = st.tabs(
    ["📋 Live Ledger", "💹 Market Audit", "⛔ Suppressed (saves)"])

# ---- Live Ledger ------------------------------------------------------------
with tab_ledger:
    if ledger.empty:
        st.info("No alerts logged yet. `output/ledger.jsonl` populates on the first fire "
                "once `live_engine.py` is running (or after `simulate_execution.py`).")
    else:
        teams = sorted(set(ledger.get("away", pd.Series(dtype=str)).dropna())
                       | set(ledger.get("home", pd.Series(dtype=str)).dropna()))
        types = sorted(ledger["trigger_type"].dropna().unique())
        f1, f2 = st.columns(2)
        pick_types = f1.multiselect("Signal type", types, default=types)
        pick_teams = f2.multiselect("Team (away or home)", teams, default=[])

        view = ledger[ledger["trigger_type"].isin(pick_types)] if pick_types else ledger
        if pick_teams:
            view = view[view["away"].isin(pick_teams) | view["home"].isin(pick_teams)]

        cols = [c for c in ["ts", "result", "units", "trigger_type", "rule_name", "game_key",
                            "inning", "half", "pitcher", "starter_tier", "tto", "slot",
                            "bet_line", "verified_line", "fair", "edge", "final_total",
                            "pull_risk", "data_age_s"] if c in view.columns]
        st.dataframe(view[cols].sort_values("ts", ascending=False) if "ts" in cols else view[cols],
                     use_container_width=True, height=460)
        st.caption(f"{len(view)} of {total} alerts shown.")

# ---- Market Audit -----------------------------------------------------------
with tab_market:
    if not LINES.exists():
        st.info("`data/closing_lines.csv` not found — run `odds_collector.py` (forward) or "
                "`odds_papi_history.py` (historical) to populate real pregame lines.")
    else:
        lines = pd.read_csv(LINES)
        src_col = "source" if "source" in lines.columns else None
        cc1, cc2 = st.columns(2)
        cc1.metric("Cached pregame lines", len(lines))
        if src_col:
            cc2.metric("Sources", ", ".join(sorted(lines[src_col].dropna().unique())) or "—")
        st.dataframe(lines.sort_values("commence_time", ascending=False)
                     if "commence_time" in lines.columns else lines,
                     use_container_width=True, height=460)
        st.caption("Verify these are updating: `odds_collector.py` appends upcoming lines "
                   "(1 credit), `odds_papi_history.py` backfills real closing lines.")

# ---- Suppressed (saves) -------------------------------------------------------
with tab_suppressed:
    if ledger.empty or not ledger["suppressed"].any():
        st.info("No suppressed alerts yet. Each row here is a phantom/thin edge the "
                "verification layer kept off your phone — and what it would have done.")
    else:
        sup = ledger[ledger["suppressed"]].copy()
        # what would the phantom have done? score it like a bet to measure the saves.
        saved = int((sup["result"] == "Loss").sum())
        cost = int((sup["result"] == "Win").sum())
        s1, s2, s3 = st.columns(3)
        s1.metric("Alerts suppressed", len(sup))
        s2.metric("Would-be LOSSES avoided", saved)
        s3.metric("Would-be wins missed", cost)
        cols = [c for c in ["ts", "rule_name", "game_key", "pitcher", "live_total",
                            "verified_line", "verified_edge", "fair", "result",
                            "final_total"] if c in sup.columns]
        st.dataframe(sup[cols].sort_values("ts", ascending=False),
                     use_container_width=True, height=380)
