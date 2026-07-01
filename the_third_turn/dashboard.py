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


st.title("⚾ The Third Turn · Control Center")
if st.button("🔄 Refresh"):
    st.rerun()

ledger = load_ledger()

# ---- Metrics cards ----------------------------------------------------------
total = len(ledger)
by_type = ledger["trigger_type"].value_counts().to_dict() if total else {}
base = baseline_hit_rate()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total alerts fired", total)
c2.metric("🔴 CONFIRM", by_type.get("CONFIRM", 0))
c3.metric("🟡 ARM", by_type.get("ARM", 0))
c4.metric("🔵 WATCH", by_type.get("WATCH", 0))
if base is not None:
    c5.metric("Historical edge (matchup proxy)", f"{base:.1f}%",
              delta=f"{base - BREAKEVEN:+.1f}% vs breakeven")
else:
    c5.metric("Historical edge", "run backtest")

st.caption("Alerts are read live from `output/ledger.jsonl`; the edge is the deflated "
           "matchup-proxy baseline from `output/report.csv` (breakeven at -110 is 52.4%).")

tab_ledger, tab_market = st.tabs(["📋 Live Ledger", "💹 Market Audit"])

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

        cols = [c for c in ["ts", "trigger_type", "rule_name", "game_key", "inning", "half",
                            "pitcher", "starter_tier", "tto", "slot", "live_total", "fair",
                            "edge", "pull_risk", "outcome", "data_age_s"] if c in view.columns]
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
