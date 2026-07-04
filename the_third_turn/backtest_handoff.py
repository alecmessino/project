#!/usr/bin/env python3
"""Backtest the STARTER→BULLPEN HANDOFF as an Over trigger in itself.

Hypothesis (user): a starter exiting to a WEAK bullpen raises expected remaining
scoring — if the market doesn't fully reprice on the pitching change, betting the
Over AT the handoff moment is +EV.

Test on the harvested trajectories (real live lines) + play-by-play:
  per game side: find the starter's exit → record the live total at that minute,
  the fielding team's bullpen RA/9, opponent runs after the exit, and whether the
  game finished OVER the at-exit line. Segment by bullpen quality.

    python the_third_turn/backtest_handoff.py
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402

from calibrate_decay import line_lookup  # noqa: E402
from config import EngineSettings  # noqa: E402
from shared_piping.team_map import resolve  # noqa: E402

console = Console()
HERE = Path(__file__).resolve().parent
TRAJ = HERE / "data" / "trajectories.jsonl"
FEED = "https://statsapi.mlb.com/api/v1.1/game/{pk}/feed/live"
LEAGUE_PEN_RA9 = 4.3


def _get(url):
    return json.loads(urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": "the-third-turn/1.0"}),
        timeout=30).read())


def handoffs(feed: dict):
    """Per side: (exit_ts, inning, opp_runs_at_exit, total_at_exit, opp_runs_after,
    remaining_opp_innings, pen_team_key, final_total)."""
    gd, ld = feed.get("gameData", {}), feed.get("liveData", {})
    away = resolve(gd["teams"]["away"]["name"]) or "?"
    home = resolve(gd["teams"]["home"]["name"]) or "?"
    box = ld["boxscore"]["teams"]
    starters = {"away": (box["away"].get("pitchers") or [None])[0],
                "home": (box["home"].get("pitchers") or [None])[0]}
    plays = ld.get("plays", {}).get("allPlays", [])
    if not plays:
        return []
    final_away = final_home = 0
    events = {}
    ascore = hscore = 0
    opp_innings = {"away": 0.0, "home": 0.0}
    for p in plays:
        about, res, match = p.get("about", {}), p.get("result", {}), p.get("matchup", {})
        is_top = bool(about.get("isTopInning"))
        side = "home" if is_top else "away"          # fielding/pitching side
        pid = (match.get("pitcher") or {}).get("id")
        ts = about.get("startTime")
        if side not in events and pid and starters[side] and pid != starters[side]:
            events[side] = {"ts": ts, "inning": int(about.get("inning") or 0),
                            "runs_total": ascore + hscore,
                            "opp_runs_at": ascore if side == "home" else hscore}
        ascore = int(res.get("awayScore") or ascore)
        hscore = int(res.get("homeScore") or hscore)
    final_away, final_home = ascore, hscore
    out = []
    for side, ev in events.items():
        opp_final = final_away if side == "home" else final_home
        pen_team = home if side == "home" else away
        out.append({**ev, "side": side, "pen_team": pen_team,
                    "opp_runs_after": opp_final - ev["opp_runs_at"],
                    "final_total": final_away + final_home})
    return out


def main() -> int:
    games = [json.loads(l) for l in TRAJ.read_text().splitlines() if l.strip()]
    pen = EngineSettings().load_bullpen_quality()
    rows = []
    for g in games:
        try:
            feed = _get(FEED.format(pk=g["game_pk"]))
        except Exception:  # noqa: BLE001
            continue
        fn = line_lookup(g["points"])
        for h in handoffs(feed):
            line = fn(h["ts"] or "")
            ra9 = pen.get(h["pen_team"])
            if line is None or ra9 is None or h["inning"] < 4 or h["inning"] > 8:
                continue   # focus on mid-game handoffs (the actionable window)
            rows.append({**h, "line_at_exit": line, "pen_ra9": ra9,
                         "over": h["final_total"] > line,
                         "push": h["final_total"] == line})
    console.rule(f"[bold]Handoff backtest · {len(rows)} mid-game handoffs (real lines)")

    def seg(name, sub):
        dec = [r for r in sub if not r["push"]]
        if not dec:
            return
        hr = 100 * sum(r["over"] for r in dec) / len(dec)
        opp = sum(r["opp_runs_after"] for r in sub) / len(sub)
        table.add_row(name, str(len(dec)), f"{hr:.1f}%",
                      f"{hr * (100/110)/100 - (1 - hr/100):+.1%}", f"{opp:.2f}")

    table = Table(title="Bet Over AT the handoff line, by bullpen quality (−110 BE 52.4%)")
    for col in ("segment", "n", "Over hit %", "ROI/u", "opp runs after (avg)"):
        table.add_column(col, justify="right" if col != "segment" else "left")
    seg("ALL handoffs", rows)
    seg("WEAK pen (RA/9 ≥ 4.6)", [r for r in rows if r["pen_ra9"] >= 4.6])
    seg("MID pen (4.2–4.6)", [r for r in rows if 4.2 <= r["pen_ra9"] < 4.6])
    seg("STRONG pen (< 4.2)", [r for r in rows if r["pen_ra9"] < 4.2])
    # the sharpest cut: weak pen AND early exit (starter chased) — more pen innings
    seg("WEAK pen & exit ≤ inn 5", [r for r in rows if r["pen_ra9"] >= 4.6 and r["inning"] <= 5])
    console.print(table)
    (HERE / "output" / "handoff_backtest.json").write_text(json.dumps(rows, indent=1, default=str))
    console.print(f"[green]Wrote output/handoff_backtest.json[/] ({len(rows)} events)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
