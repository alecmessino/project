"""Render docs/season.json into a detailed, human-readable Markdown ledger.

League-agnostic by design: it reads the `league` off each game, so the same
report carries the NBA Finals record forward through the college-basketball
season (NCAAB) and any other league the engine tracks. Run standalone or let
live_run.grade_and_sync regenerate it after every settled game.

  python scripts/season_ledger.py              # -> docs/SEASON_LEDGER.md
"""

from __future__ import annotations

import json
import pathlib
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
SEASON = ROOT / "docs" / "season.json"
MANUAL = ROOT / "docs" / "manual_bets.json"
OUT = ROOT / "docs" / "SEASON_LEDGER.md"

_PERIOD = {"full": "Full", "h1": "1H", "h2": "2H",
           "q1": "Q1", "q2": "Q2", "q3": "Q3", "q4": "Q4"}


def _market_label(market: str) -> str:
    """'game_total:full:game' -> 'Game Total · Full';
       'team_total:full:NYK'  -> 'NYK Total · Full'."""
    parts = (market or "").split(":")
    if len(parts) < 3:
        return market or "?"
    mtype, period, who = parts[0], parts[1], parts[2]
    per = _PERIOD.get(period, period.upper())
    if mtype == "team_total":
        return f"{who} Total · {per}"
    if mtype == "game_total":
        return f"Game Total · {per}"
    return f"{mtype} · {per}"


def _won_pct(w: int, losses: int) -> str:
    decided = w + losses
    return f"{(w / decided * 100):.1f}%" if decided else "—"


def _signed(x: float, nd: int = 2) -> str:
    return f"{x:+.{nd}f}"


def _bet_row(b: dict, running: float) -> tuple[str, float]:
    side = (b.get("side") or "").upper()
    entry = b.get("entry_line")
    odds = b.get("entry_odds")
    close = b.get("close_line")
    clv = b.get("clv_pts")
    prob = b.get("entry_prob")
    ev = b.get("entry_ev")
    outcome = (b.get("outcome") or "pending").upper()
    profit = b.get("profit")
    running += (profit or 0.0)
    prob_s = f"{prob * 100:.0f}%" if isinstance(prob, (int, float)) else "—"
    ev_s = f"{ev * 100:+.1f}%" if isinstance(ev, (int, float)) else "—"
    clv_s = _signed(clv, 1) if isinstance(clv, (int, float)) else "—"
    close_s = f"{close:g}" if isinstance(close, (int, float)) else "—"
    pl_s = _signed(profit, 3) if isinstance(profit, (int, float)) else "—"
    mark = {"WIN": "✅", "LOSS": "❌", "PUSH": "➖"}.get(outcome, "•")
    row = (f"| {_market_label(b.get('market',''))} | {side} | "
           f"{entry:g} @ {odds:+d} | {close_s} | {clv_s} | {prob_s} | {ev_s} | "
           f"{mark} {outcome.title()} | {pl_s} | {running:+.3f} |")
    return row, running


def render() -> str:
    season = json.loads(SEASON.read_text()) if SEASON.exists() else {}
    games = season.get("games", [])
    t = season.get("totals", {})
    now = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())

    out: list[str] = []
    out.append("# Season Ledger — Mean-Reversion Forward Test")
    out.append("")
    out.append(f"_Generated {now} from `docs/season.json`. Flat 1u stake per bet; "
               "P/L and ROI in units. CLV in points (positive = line moved your way)._")
    out.append("")

    # ---- headline totals ----
    w, l, p = t.get("wins", 0), t.get("losses", 0), t.get("pushes", 0)
    units = t.get("profit_units", 0.0)
    roi = t.get("roi")
    clv = t.get("avg_clv_pts")
    nbets = w + l + p
    out.append("## Overall")
    out.append("")
    out.append("| Games | Bets | Record | Win% | Units | ROI | Avg CLV |")
    out.append("|------:|-----:|:------:|:----:|------:|----:|--------:|")
    out.append(f"| {t.get('games', 0)} | {nbets} | {w}-{l}-{p} | {_won_pct(w, l)} | "
               f"{_signed(units, 3)}u | {roi*100:.1f}% | "
               f"{_signed(clv,2) if isinstance(clv,(int,float)) else '—'} |")
    out.append("")

    # ---- per-league rollup (forward-useful once NCAAB joins) ----
    leagues: dict[str, dict] = {}
    for g in games:
        lg = leagues.setdefault(g.get("league", "?"),
                                {"games": 0, "w": 0, "l": 0, "p": 0, "u": 0.0})
        lg["games"] += 1
        lg["w"] += g.get("wins", 0); lg["l"] += g.get("losses", 0); lg["p"] += g.get("pushes", 0)
        lg["u"] += sum(b.get("profit", 0.0) for b in g.get("bets", [])
                       if b.get("outcome") in ("win", "loss", "push"))
    if len(leagues) > 1:
        out.append("## By League")
        out.append("")
        out.append("| League | Games | Record | Win% | Units |")
        out.append("|:-------|------:|:------:|:----:|------:|")
        for lg, s in sorted(leagues.items()):
            out.append(f"| {lg} | {s['games']} | {s['w']}-{s['l']}-{s['p']} | "
                       f"{_won_pct(s['w'], s['l'])} | {_signed(s['u'],3)}u |")
        out.append("")

    # ---- per-game detail ----
    out.append("## Games")
    out.append("")
    running = 0.0
    for g in games:
        gw, gl, gp = g.get("wins", 0), g.get("losses", 0), g.get("pushes", 0)
        gu = sum(b.get("profit", 0.0) for b in g.get("bets", [])
                 if b.get("outcome") in ("win", "loss", "push"))
        out.append(f"### {g.get('date','?')} · {g.get('league','?')} · {g.get('matchup','?')}")
        out.append("")
        out.append(f"`{g.get('game','')}` — **{gw}-{gl}-{gp}**, "
                   f"**{_signed(gu,3)}u**, avg CLV {_signed(g.get('avg_clv_pts',0.0),2)}")
        out.append("")
        out.append("| Market | Side | Entry @ Odds | Close | CLV | Model P | EV | Result | P/L | Bankroll |")
        out.append("|:-------|:----:|:------------:|:-----:|:---:|:-------:|:--:|:------:|----:|---------:|")
        bets = sorted(g.get("bets", []), key=lambda b: b.get("entry_ts", ""))
        for b in bets:
            row, running = _bet_row(b, running)
            out.append(row)
        out.append("")

    # ---- manual bets appendix (kept separate from the forward-test record) ----
    if MANUAL.exists():
        try:
            mbets = json.loads(MANUAL.read_text()).get("bets", [])
        except (ValueError, OSError):
            mbets = []
        if mbets:
            out.append("## Manual Bets (personal — outside the forward test)")
            out.append("")
            out.append("| Date | League | Matchup | Market | Side | Entry @ Odds | Final | Result | P/L |")
            out.append("|:-----|:------:|:--------|:-------|:----:|:------------:|:-----:|:------:|----:|")
            for b in mbets:
                ts = (b.get("entry_ts", "") or "")[:10]
                odds = b.get("entry_odds")
                final = b.get("actual_final")
                prof = b.get("profit")
                out.append(
                    f"| {ts} | {b.get('league','?')} | {b.get('matchup','?')} | "
                    f"{_market_label(b.get('market',''))} | {(b.get('side') or '').upper()} | "
                    f"{b.get('entry_line')} @ {odds:+d} | "
                    f"{final if final is not None else '—'} | "
                    f"{(b.get('outcome') or 'pending').title()} | "
                    f"{_signed(prof,3) if isinstance(prof,(int,float)) else '—'} |")
            out.append("")

    return "\n".join(out).rstrip() + "\n"


def main() -> None:
    OUT.write_text(render())
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
