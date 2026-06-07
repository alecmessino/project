"""Forward-test ledger: accumulate REAL captured bets into a CLV/ROI report.

The honest, free path to real edge numbers. As the live engine sees flagged
signals (real lines, via the timeout cadence), each (event, market, side) is
recorded once at its *entry* line and then tracked to its latest *close* line.
Closing-line value (close vs entry) needs no final score; win/loss fills in
when a `finals` block is available. The ledger is a plain list of dicts so it
can be persisted to JSON and merged across runs (e.g. the 5-min poll workflow).
"""

from __future__ import annotations

import json
import pathlib
import time
from typing import Optional

from .probability import american_to_profit


def _key(ev) -> str:
    b = ev.baseline
    return f"{b.market_type.value}:{b.period.value}:{b.team or 'game'}:{ev.side.value}"


def _grade(side: str, line: float, actual: float, odds: int):
    if abs(actual - line) < 1e-9:
        return "push", 0.0
    won = actual > line if side == "over" else actual < line
    return ("win", american_to_profit(odds)) if won else ("loss", -1.0)


def merge_signal(ledger: dict, evaluation, ts: str, matchup: str,
                 finals: Optional[dict] = None) -> dict:
    """Record/update one flagged evaluation in the ledger (keyed per market+side).

    Entry line is locked on first sighting; close line tracks the latest. CLV is
    measured in the side's favour. Returns the (mutated) ledger.
    """
    e = evaluation
    b = e.baseline
    k = _key(e)
    entry = ledger.get(k)
    if entry is None:
        entry = {
            "event": b.market_type.value, "matchup": matchup, "market": b.key(),
            "side": e.side.value, "entry_line": e.live.line, "entry_ts": ts,
            "entry_odds": e.offered_odds, "entry_ev": round(e.ev, 4),
            "entry_prob": round(e.prob, 4),
            "close_line": e.live.line, "close_ts": ts,
            "clv_pts": 0.0, "outcome": "pending", "profit": 0.0,
        }
        ledger[k] = entry
    # always advance the close
    entry["close_line"] = e.live.line
    entry["close_ts"] = ts
    entry["clv_pts"] = round(
        (entry["close_line"] - entry["entry_line"]) if e.side.value == "over"
        else (entry["entry_line"] - entry["close_line"]), 1)
    # grade if finals available
    actual = _actual_final(finals, b.market_type.value, b.period.value, b.team) if finals else None
    if actual is not None:
        outcome, profit = _grade(e.side.value, entry["entry_line"], actual, entry["entry_odds"])
        entry["outcome"], entry["profit"] = outcome, round(profit, 3)
    return ledger


def append_capture(path: str | pathlib.Path, event_id: str, snap, results,
                   ts: str, thresholds: Optional[dict] = None) -> dict:
    """Archive one raw cadence-mark snapshot for forward testing.

    Stores every tracked market's full quote — line plus BOTH the over and under
    prices — alongside the model's read (side/fair/edge/ev/flag). With both sides'
    odds preserved you can re-grade OVER or UNDER offline later. Idempotent per
    (event_id, mark) so re-runs of the poll workflow never duplicate a capture.

    `thresholds` (e.g. {"pct_move": 0.10, "edge_pts": 3.0}) is stored at the top
    level so the dashboard's distance-to-trigger chart can draw the live lines.
    """
    p = pathlib.Path(path)
    try:
        hist = json.loads(p.read_text()) if p.exists() else {}
    except (ValueError, OSError):
        hist = {}
    if thresholds is not None:
        hist["thresholds"] = thresholds
    captures = hist.setdefault("captures", [])
    mark = snap.meta.get("cadence_mark")
    if any(c.get("event_id") == event_id and c.get("mark") == mark for c in captures):
        return hist  # already archived this mark

    evals = {
        f"{r.evaluation.baseline.market_type.value}:{r.evaluation.baseline.period.value}:"
        f"{r.evaluation.baseline.team or 'game'}": r
        for r in results
    }
    markets = []
    for ln in snap.lines:
        key = f"{ln.market_type.value}:{ln.period.value}:{ln.team or 'game'}"
        rec = {
            "market": key, "line": ln.line,
            "over_odds": ln.over_odds, "under_odds": ln.under_odds,
            "book": ln.book,
        }
        r = evals.get(key)
        if r is not None:
            e = r.evaluation
            rec.update({
                "model_side": e.side.value,
                "fair_final": round(e.fair_final, 1),
                "pct_move": round(e.pct_move, 4),
                "edge_pts": round(e.edge_pts, 1),
                "ev": round(e.ev, 4), "prob": round(e.prob, 4),
                "flagged": bool(r.signal),
                "strong": bool(r.signal and r.signal.strong),
            })
        markets.append(rec)

    captures.append({
        "event_id": event_id, "ts": ts, "mark": mark,
        "clock": snap.meta.get("clock"), "period": snap.state.period.value,
        "away_score": snap.state.away_score, "home_score": snap.state.home_score,
        "minutes_elapsed": round(snap.state.minutes_elapsed, 1),
        "markets": markets,
    })
    p.write_text(json.dumps(hist, indent=2))
    return hist


def _actual_final(finals, market_type, period, team):
    try:
        if market_type == "team_total":
            return float(finals["team"][team])
        game = finals["game"]
        # 2nd-half total isn't stored directly; derive it from full - 1H (or Q3+Q4).
        if period == "h2" and "h2" not in game:
            if "full" in game and "h1" in game:
                return float(game["full"]) - float(game["h1"])
            if "q3" in game and "q4" in game:
                return float(game["q3"]) + float(game["q4"])
            return None
        return float(game[period])
    except (KeyError, TypeError, ValueError):
        return None


def load_ledger(path: str | pathlib.Path) -> dict:
    """Read the keyed ledger back from a forward.json (empty if absent)."""
    p = pathlib.Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text()).get("ledger", {})
    except (ValueError, OSError):
        return {}


def dump(path: str | pathlib.Path, ledger: dict, scope: Optional[dict] = None) -> None:
    """Persist ledger + rolled-up summary + sorted rows for the dashboard."""
    bets = sorted(ledger.values(), key=lambda b: b["entry_ts"])
    payload = {
        "generated": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()),
        "scope": scope or {},
        "summary": summarize(ledger),
        "bets": bets,
        "ledger": ledger,
    }
    pathlib.Path(path).write_text(json.dumps(payload, indent=2))


def build_from_sqlite(db_path: str | pathlib.Path,
                      finals_by_event: Optional[dict] = None,
                      matchup_by_event: Optional[dict] = None) -> dict:
    """Build a ledger from the observations log written during live runs.

    Entry = first flagged row per (event, market, side); close = last observed
    live line for that market (any row). Outcome graded vs finals when provided.
    """
    import sqlite3

    finals_by_event = finals_by_event or {}
    matchup_by_event = matchup_by_event or {}
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM observations ORDER BY ts ASC").fetchall()
    conn.close()

    closes: dict[tuple, float] = {}
    ledger: dict = {}
    for r in rows:
        mkey = (r["event_id"], r["market_type"], r["period"], r["team"])
        closes[mkey] = r["live_line"]            # ascending ts -> last wins
        if not r["flagged"]:
            continue
        k = f"{r['market_type']}:{r['period']}:{r['team'] or 'game'}:{r['side']}"
        if k in ledger:
            continue
        odds = r["over_odds"] if r["side"] == "over" else r["under_odds"]
        ledger[k] = {
            "event": r["event_id"],
            "matchup": matchup_by_event.get(r["event_id"], r["event_id"]),
            "market": f"{r['market_type']}:{r['period']}:{r['team'] or 'game'}",
            "side": r["side"], "entry_line": r["live_line"],
            "entry_ts": _iso(r["ts"]), "entry_odds": odds,
            "entry_ev": round(r["ev"], 4), "entry_prob": round(r["prob"], 4),
            "close_line": r["live_line"], "close_ts": _iso(r["ts"]),
            "clv_pts": 0.0, "outcome": "pending", "profit": 0.0,
            "_mkey": list(mkey),
        }
    # second pass: set close + clv + outcome
    for k, e in ledger.items():
        mkey = tuple(e.pop("_mkey"))
        close = closes.get(mkey, e["entry_line"])
        e["close_line"] = close
        e["clv_pts"] = round((close - e["entry_line"]) if e["side"] == "over"
                             else (e["entry_line"] - close), 1)
        finals = finals_by_event.get(mkey[0])
        actual = _actual_final(finals, mkey[1], mkey[2], mkey[3]) if finals else None
        if actual is not None:
            outcome, profit = _grade(e["side"], e["entry_line"], actual, e["entry_odds"])
            e["outcome"], e["profit"] = outcome, round(profit, 3)
    return ledger


def _iso(ts: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))


def summarize(ledger: dict) -> dict:
    """Roll the ledger into headline stats for the dashboard panel."""
    bets = list(ledger.values())
    decided = [b for b in bets if b["outcome"] in ("win", "loss")]
    wins = sum(1 for b in bets if b["outcome"] == "win")
    losses = sum(1 for b in bets if b["outcome"] == "loss")
    pushes = sum(1 for b in bets if b["outcome"] == "push")
    profit = sum(b["profit"] for b in bets)
    staked = len(decided)
    clv_vals = [b["clv_pts"] for b in bets]
    clv_beat = sum(1 for v in clv_vals if v > 0)
    return {
        "bets": len(bets), "wins": wins, "losses": losses, "pushes": pushes,
        "pending": sum(1 for b in bets if b["outcome"] == "pending"),
        "win_rate": round(wins / len(decided), 3) if decided else None,
        "roi": round(profit / staked, 3) if staked else None,
        "profit_units": round(profit, 2),
        "clv_beat": clv_beat, "clv_graded": len(clv_vals),
        "clv_beat_rate": round(clv_beat / len(clv_vals), 3) if clv_vals else None,
        "avg_clv_pts": round(sum(clv_vals) / len(clv_vals), 2) if clv_vals else None,
    }
