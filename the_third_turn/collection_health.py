#!/usr/bin/env python3
"""Collection health report — OPERATIONS, not analysis.

Monitors the integrity of the live collection pipeline. It answers "is the collector
healthy?", never "is there a market edge?". Meant to run after every checkpoint; writes
output/health_report.txt (human) + output/health_report.json (machine) and prints the text.

    python the_third_turn/collection_health.py

Tracks: live quotes per book, simultaneous live pairs, overlap games, books reporting live,
median sync lag, OPEN/SUSPENDED counts, duplicate rows, stale timestamps, missing fields,
coverage by game/inning, and the SR-1 gate vs threshold (same definition as
microstructure_probe.py / protocol/stopping_rules.md).
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "output"
try:
    sys.path.insert(0, str(HERE))
    from version import VERSIONS
except Exception:  # noqa: BLE001
    VERSIONS = {"protocol": "?", "collector": "?", "benchmark_dataset": "?"}

REQUIRED_BOOK_FIELDS = ("ts", "game", "book", "line")
STALE_MIN = 30          # a book with no new row in this many minutes (while games are live) is stale
NOW = datetime.now(timezone.utc)


def _read(name):
    p = OUT / name
    if not p.exists():
        return []
    rows = []
    for ln in p.open():
        ln = ln.strip()
        if ln:
            try:
                rows.append(json.loads(ln))
            except json.JSONDecodeError:
                rows.append({"__malformed__": True})
    return rows


def _T(s):
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def bar(frac, width=18):
    frac = max(0.0, min(1.0, frac))
    n = int(round(frac * width))
    return "█" * n + "·" * (width - n)


def analyse():
    bp = _read("book_panel.jsonl")
    gs = _read("game_state_panel.jsonl")
    tt = _read("team_total_panel.jsonl")
    R = {"generated": NOW.isoformat(timespec="seconds"), "versions": VERSIONS}

    # ── integrity ────────────────────────────────────────────────────────────
    malformed = sum(1 for r in bp if r.get("__malformed__"))
    clean = [r for r in bp if not r.get("__malformed__")]
    missing = sum(1 for r in clean if any(r.get(k) in (None, "") for k in REQUIRED_BOOK_FIELDS))
    seen, dups = set(), 0
    for r in clean:
        key = (r.get("ts"), r.get("game"), r.get("book"), r.get("line"),
               r.get("over_odds"), r.get("under_odds"))
        if key in seen:
            dups += 1
        seen.add(key)
    future = sum(1 for r in clean if (t := _T(r.get("ts"))) and t > NOW + timedelta(minutes=2))
    R["integrity"] = {"rows": len(bp), "malformed_json": malformed,
                      "missing_required_fields": missing, "duplicate_rows": dups,
                      "future_timestamps": future}

    # ── per-book counts + freshness ──────────────────────────────────────────
    books = sorted({r["book"] for r in clean if r.get("book")})
    today = NOW.date()
    per = {}
    for b in books:
        rows_b = [r for r in clean if r.get("book") == b]
        live_b = [r for r in rows_b if r.get("live")]
        tsb = [t for r in rows_b if (t := _T(r.get("ts")))]
        last = max(tsb) if tsb else None
        per[b] = {
            "rows_total": len(rows_b), "live_total": len(live_b),
            "live_today": sum(1 for r in live_b if (t := _T(r.get("ts"))) and t.date() == today),
            "last_row_age_min": round((NOW - last).total_seconds() / 60, 1) if last else None,
        }
    R["by_book"] = per
    R["books_reporting_live"] = sorted(b for b in books if per[b]["live_total"] > 0)

    # ── market status (quote lifecycle) ──────────────────────────────────────
    R["market_status"] = dict(Counter(
        (r.get("status") or "unset") for r in clean if r.get("live")))

    # ── simultaneous live overlap (same definition as SR-1 gate) ─────────────
    series = defaultdict(lambda: defaultdict(list))
    for r in clean:
        t = _T(r.get("ts"))
        if t and r.get("game") and r.get("book"):
            series[r["game"]][r["book"]].append((t, bool(r.get("live"))))
    for g in series:
        for b in series[g]:
            series[g][b].sort()

    def ff(sl, t):
        v = vt = None
        for (tt_, liv) in sl:
            if tt_ <= t:
                v, vt = liv, tt_
            else:
                break
        return v, vt

    pairs = pairs_today = 0
    overlap_games = set()
    lags = []
    per_game_books_live = {}
    for g, bysrc in series.items():
        if len(bysrc) < 2:
            per_game_books_live[g] = sum(1 for b in bysrc if any(l for _, l in bysrc[b]))
            continue
        times = sorted({t for b in bysrc for (t, _) in bysrc[b]})
        gpairs = 0
        for t in times:
            fills = [(b,) + ff(bysrc[b], t) for b in bysrc]
            live_now = [(b, vt) for (b, v, vt) in fills if v and vt is not None]
            if len(live_now) >= 2:
                pairs += 1
                gpairs += 1
                overlap_games.add(g)
                if t.date() == today:
                    pairs_today += 1
                vts = [vt for _, vt in live_now]
                lags.append((max(vts) - min(vts)).total_seconds())
        per_game_books_live[g] = max(
            (sum(1 for b in bysrc if ff(bysrc[b], t)[0]) for t in times), default=0)
    med_lag = sorted(lags)[len(lags) // 2] if lags else None
    dist = Counter(per_game_books_live.values())
    R["overlap"] = {
        "simultaneous_pairs_total": pairs, "simultaneous_pairs_today": pairs_today,
        "overlap_games": len(overlap_games),
        "median_sync_lag_s": round(med_lag, 1) if med_lag is not None else None,
        "games_by_books_live": {f"{k}_books": v for k, v in sorted(dist.items())},
    }

    # ── Priority-1 fix verification (behaviour, not elapsed time) ─────────────
    # The collector v1.1 live-overlap fix is VERIFIED IN PRODUCTION only once the banked
    # data itself demonstrates simultaneous live collection — not after N hours.
    status_populated = any(s not in (None, "unset") for s in R["market_status"])
    conds = {
        "fanduel_live_quotes > 0": per.get("fanduel", {}).get("live_total", 0) > 0,
        "simultaneous_live_pairs > 0": pairs > 0,
        "overlap_games > 0": len(overlap_games) > 0,
        "marketStatus populated": status_populated,
        "median_sync_lag computed": med_lag is not None,
    }
    R["fix_verification"] = {"target": "collector v1.1 · live-overlap fix",
                             "conditions": conds, "verified": all(conds.values())}

    # ── live coverage (game_state panel) ─────────────────────────────────────
    gs_clean = [r for r in gs if not r.get("__malformed__")]
    live_games = {r.get("game") for r in gs_clean}
    inning_cov = Counter(r.get("inning") for r in gs_clean if r.get("inning"))
    R["coverage"] = {
        "live_games_seen": len(live_games),
        "book_panel_games": len({r.get("game") for r in clean}),
        "team_total_rows": len([r for r in tt if not r.get("__malformed__")]),
        "innings_seen": sorted(int(i) for i in inning_cov if i),
    }

    # ── SR-1 gate (protocol/stopping_rules.md) ───────────────────────────────
    live_books = R["books_reporting_live"]
    gate = [
        ("simultaneous live quote pairs", pairs, 2000),
        ("games with live overlap", len(overlap_games), 100),
        ("median sync lag < 15s", med_lag if med_lag is not None else 1e9, 15),
        ("books quoting live", len(live_books), 3),
    ]
    def prog(name, cur, tgt):
        if "lag" in name:
            ok = cur < tgt
            pct = 1.0 if ok else min(1.0, tgt / cur) if cur else 0.0
        else:
            ok = cur >= tgt
            pct = min(1.0, cur / tgt) if tgt else 1.0
        return ok, pct
    sr1 = []
    for name, cur, tgt in gate:
        ok, pct = prog(name, cur, tgt)
        sr1.append({"criterion": name, "current": (round(cur, 1) if isinstance(cur, float) else cur),
                    "target": tgt, "pass": ok, "progress": round(pct, 3)})
    R["SR1_gate"] = {"criteria": sr1, "cleared": all(c["pass"] for c in sr1),
                     "overall_progress": round(sum(c["progress"] for c in sr1) / len(sr1), 3)}
    return R


def render(R):
    v = R["versions"]
    L = []
    L.append("═" * 66)
    L.append(f" THE THIRD TURN — collection health   {R['generated']}")
    L.append(f" protocol v{v['protocol']} · collector v{v['collector']} · dataset {v['benchmark_dataset']}")
    L.append("═" * 66)

    fv = R["fix_verification"]
    L.append(f"\nFIX VERIFICATION — {fv['target']}")
    L.append(f"  → {'✅ VERIFIED IN PRODUCTION' if fv['verified'] else '⏳ PENDING — awaiting live overlap'}")
    for name, ok in fv["conditions"].items():
        L.append(f"    [{'✅' if ok else '  '}] {name}")

    L.append("\nBOOKS (live quotes)")
    mx = max((b["live_total"] for b in R["by_book"].values()), default=1) or 1
    for name, b in R["by_book"].items():
        age = f"{b['last_row_age_min']}m ago" if b["last_row_age_min"] is not None else "—"
        flag = " ⚠STALE" if (b["last_row_age_min"] or 0) > STALE_MIN and R["coverage"]["live_games_seen"] else ""
        L.append(f"  {name:9s} {bar(b['live_total']/mx)}  live={b['live_total']:5d} "
                 f"(today {b['live_today']:4d})  last {age}{flag}")
    L.append(f"  books reporting live: {', '.join(R['books_reporting_live']) or 'NONE'}")

    o = R["overlap"]
    L.append("\nOVERLAP (the scarce resource)")
    L.append(f"  simultaneous live pairs : {o['simultaneous_pairs_total']:6d}  (today {o['simultaneous_pairs_today']})")
    L.append(f"  overlap games           : {o['overlap_games']}")
    L.append(f"  median sync lag         : {o['median_sync_lag_s'] if o['median_sync_lag_s'] is not None else '—'} s")
    L.append(f"  games by #books live     : {o['games_by_books_live'] or '—'}")

    L.append("\nQUOTE LIFECYCLE (live rows)")
    L.append(f"  market status: {R['market_status'] or '—'}")

    c = R["coverage"]
    L.append("\nCOVERAGE")
    L.append(f"  live games seen: {c['live_games_seen']}   book-panel games: {c['book_panel_games']}"
             f"   team-total rows: {c['team_total_rows']}")
    L.append(f"  innings seen: {c['innings_seen'] or '—'}")

    ig = R["integrity"]
    warn = [k for k, val in (("malformed", ig["malformed_json"]), ("missing-fields", ig["missing_required_fields"]),
                             ("duplicates", ig["duplicate_rows"]), ("future-ts", ig["future_timestamps"])) if val]
    L.append("\nINTEGRITY")
    L.append(f"  rows={ig['rows']}  malformed={ig['malformed_json']}  missing-fields={ig['missing_required_fields']}"
             f"  duplicates={ig['duplicate_rows']}  future-ts={ig['future_timestamps']}")
    L.append("  status: " + ("✅ clean" if not warn else "⚠ " + ", ".join(warn)))

    g = R["SR1_gate"]
    L.append("\nSR-1 GATE (leadership analysis — blocked until all pass)")
    for cr in g["criteria"]:
        mark = "✅" if cr["pass"] else "  "
        L.append(f"  {mark} {bar(cr['progress'])} {cr['criterion']:32s} {cr['current']} / {cr['target']}")
    L.append(f"  overall: {int(g['overall_progress']*100)}%  →  "
             f"{'CLEARED' if g['cleared'] else 'BLOCKED — keep collecting'}")
    L.append("═" * 66)
    return "\n".join(L)


def summary(R):
    g, ig, o = R["SR1_gate"], R["integrity"], R["overlap"]
    warn = [k for k, v in (("malformed", ig["malformed_json"]), ("missing", ig["missing_required_fields"]),
                           ("dupes", ig["duplicate_rows"]), ("future-ts", ig["future_timestamps"])) if v]
    fv = "VERIFIED" if R["fix_verification"]["verified"] else "PENDING"
    return (f"fix-v1.1 {fv} · SR-1 {int(g['overall_progress']*100)}% · "
            f"books-live {','.join(R['books_reporting_live']) or 'none'} · "
            f"pairs {o['simultaneous_pairs_total']} · "
            f"integrity {'clean' if not warn else '/'.join(warn)}")


def main():
    R = analyse()
    (OUT / "health_report.json").write_text(json.dumps(R, indent=2, default=str))
    (OUT / "health_report.txt").write_text(render(R) + "\n")
    print(summary(R) if "--summary" in sys.argv else render(R))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
