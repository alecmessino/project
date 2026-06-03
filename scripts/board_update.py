"""Discover a whole league's Bovada slate and write docs/board.json.

No per-game YAML needed — this enumerates every game Bovada lists for the league
and extracts the pre-game Total / Spread / Moneyline so the dashboard can show
tonight's full board the moment it loads (before any tip-off). Re-run on a cron
or before tip:

    python scripts/board_update.py --league wnba
    python scripts/board_update.py --league nba
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mrbet.bovada_feed import (   # noqa: E402
    BovadaProvider, _american, _handicap, board_events, event_from_bovada,
)

OUT = ROOT / "docs" / "board.json"


def _game_markets(raw: dict):
    """Pull pre-game Total / Spread / Moneyline (period G) from a raw event."""
    total = spread = None
    ml_home = ml_away = None
    home_name = next((c.get("name", "") for c in raw.get("competitors", []) if c.get("home")), "")
    for dg in raw.get("displayGroups", []):
        for m in dg.get("markets", []):
            if (m.get("period", {}) or {}).get("abbreviation") != "G":
                continue
            key = m.get("key")
            outs = m.get("outcomes", [])
            if key == "2W-OU":
                over = next((o for o in outs if o.get("description", "").lower() == "over"), None)
                if over:
                    total = _handicap(over.get("price", {}))
            elif key == "2W-HCAP":
                ho = next((o for o in outs
                           if home_name.split()[-1].lower() in o.get("description", "").lower()), None)
                if ho:
                    spread = _handicap(ho.get("price", {}))
            elif key == "2W-12":
                for o in outs:
                    is_home = home_name.split()[-1].lower() in o.get("description", "").lower()
                    price = _american(o.get("price", {}))
                    if is_home:
                        ml_home = price
                    else:
                        ml_away = price
    return total, spread, ml_home, ml_away


def _write_config(ev, league, total, spread, ml_home, ml_away, tip_ms) -> str:
    """Auto-generate a config/games/*.yaml from the discovered board entry."""
    date = (time.strftime("%Y-%m-%d", time.localtime(tip_ms / 1000))
            if isinstance(tip_ms, (int, float)) else time.strftime("%Y-%m-%d"))
    iso = (time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(tip_ms / 1000))
           if isinstance(tip_ms, (int, float)) else "")
    gid = f"{ev.away_key.lower()}_{ev.home_key.lower()}_{date}"
    h1 = round(total * 0.51 * 2) / 2.0 if total else 0.0
    s = spread if spread is not None else 0.0
    home_tt = round((total - s) / 2.0 * 2) / 2.0 if total else 0.0
    away_tt = round((total + s) / 2.0 * 2) / 2.0 if total else 0.0
    body = f"""# Auto-generated from the live Bovada board (scripts/board_update.py --write-configs).
# {league.upper()} — {'40' if league == 'wnba' else '48'}-min regulation. FULL total/spread/ML are
# REAL Bovada lines; 1H and team totals are DERIVED (1H ~= 51% of full; team TT =
# (total +/- spread)/2). Refine from the book at tip if needed.

event:
  id: {gid}
  league: {league.upper()}
  away: {ev.away}
  home: {ev.home}
  away_key: {ev.away_key}
  home_key: {ev.home_key}
  commence_time: "{iso}"
  bookmaker: bovada

totals:
  full:    {{ line: {total}, over: -110, under: -110 }}
  h1:      {{ line: {h1}, over: -110, under: -110 }}

team_totals:
  {ev.home_key}: {{ line: {home_tt}, over: -110, under: -110 }}
  {ev.away_key}: {{ line: {away_tt}, over: -110, under: -110 }}

sides:
  spread:    {{ {ev.home_key}: {s:+g}, {ev.away_key}: {-s:+g}, over: -110, under: -110 }}
  moneyline: {{ {ev.home_key}: {ml_home if ml_home is not None else 0}, {ev.away_key}: {ml_away if ml_away is not None else 0} }}
"""
    path = ROOT / "config" / "games" / f"{gid}.yaml"
    path.write_text(body)
    return str(path.relative_to(ROOT))


def _live_pace(provider, raw, stage, total):
    """For a LIVE game, classify pace vs pregame expectation (league-aware).

    Returns (pace, proj) where pace in {'slow','fast','even', None} and proj is the
    model's projected final total. 'slow' (a red ▼ on the board) means the live
    scoring rate is well under the pregame pace — the total is trending UNDER.
    """
    from mrbet.reversion import projected_final
    if stage != "live" or not total:
        return None, None
    provider._raw_event = raw                 # use this discovered game directly
    st = provider._fetch_state()
    if st is None or st.minutes_elapsed <= 0:
        return None, None
    live_rate = st.total_score / st.minutes_elapsed
    pregame_rate = total / provider.regulation_min        # 40 (WNBA) / 48 (NBA)
    ratio = live_rate / pregame_rate if pregame_rate else 1.0
    pace = "slow" if ratio < 0.92 else ("fast" if ratio > 1.08 else "even")
    proj = round(projected_final(total, st.total_score, st, beta=0.9, min_minutes_elapsed=5.0), 1)
    return pace, proj


def _refresh_config_lines(path, events) -> bool:
    """Lock the latest Bovada lines into an EXISTING unified config, in place.

    Finds the discovered board event matching the file's event.bovada_event_id
    (falling back to team-name match) and rewrites only the totals / team_totals /
    sides line values — the event block (id, keys, bovada_event_id, bookmaker) is
    preserved. Returns True if the file was updated. Comments may be dropped on
    rewrite; the values are what the engine reads.
    """
    import yaml
    p = pathlib.Path(path)
    if not p.exists():
        print(f"  refresh-config: {path} not found — skipping")
        return False
    cfg = yaml.safe_load(p.read_text()) or {}
    ev_block = cfg.get("event", {})
    want_id = str(ev_block.get("bovada_event_id") or "")
    home_tag = str(ev_block.get("home", "")).split()[-1].lower()
    away_tag = str(ev_block.get("away", "")).split()[-1].lower()
    hk, ak = ev_block.get("home_key"), ev_block.get("away_key")

    raw = None
    for e in events:
        if want_id and str(e.get("id")) == want_id:
            raw = e
            break
        hay = (" ".join(c.get("name", "") for c in e.get("competitors", []))
               + " " + e.get("description", "")).lower()
        if home_tag and away_tag and home_tag in hay and away_tag in hay:
            raw = e
    if raw is None:
        print(f"  refresh-config: no board match for {path} (id={want_id or 'n/a'}) — kept as-is")
        return False

    total, spread, ml_home, ml_away = _game_markets(raw)
    if total is None:
        print(f"  refresh-config: board has no total yet — kept {path} as-is")
        return False

    cfg.setdefault("totals", {})["full"] = {"line": total, "over": -110, "under": -110}
    cfg["totals"]["h1"] = {"line": round(total * 0.51 * 2) / 2, "over": -110, "under": -110}
    if spread is not None:
        home_tt = round((total - spread) / 2.0 * 2) / 2.0
        away_tt = round((total + spread) / 2.0 * 2) / 2.0
        cfg.setdefault("team_totals", {})[hk] = {"line": home_tt, "over": -110, "under": -110}
        cfg["team_totals"][ak] = {"line": away_tt, "over": -110, "under": -110}
        cfg.setdefault("sides", {})["spread"] = {hk: spread, ak: -spread, "over": -110, "under": -110}
    cfg.setdefault("sides", {})["moneyline"] = {hk: ml_home or 0, ak: ml_away or 0}

    header = ("# Auto-refreshed closing lines (scripts/board_update.py --refresh-config).\n"
              "# Event block preserved; line values are Bovada's latest pregame numbers.\n")
    p.write_text(header + yaml.safe_dump(cfg, sort_keys=False))
    print(f"  refresh-config: locked closing lines into {path} "
          f"(total {total}, {hk} {spread:+g})" if spread is not None
          else f"  refresh-config: locked total {total} into {path}")
    return True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Write docs/board.json for a league's slate")
    ap.add_argument("--league", default="wnba")
    ap.add_argument("--write-configs", action="store_true",
                    help="also auto-generate config/games/*.yaml for each game")
    ap.add_argument("--refresh-config", metavar="PATH", default=None,
                    help="lock latest Bovada lines into an existing unified config "
                         "in place (preserves its event block / bovada_event_id)")
    args = ap.parse_args(argv)

    events = board_events(args.league)
    if args.refresh_config:
        _refresh_config_lines(args.refresh_config, events)
    games = []
    for raw in events:
        ev = event_from_bovada(raw)
        p = BovadaProvider(ev, league=args.league, max_polls=1)
        stage = p._classify_stage(raw)
        total, spread, ml_home, ml_away = _game_markets(raw)
        tip_ms = raw.get("startTime")
        tip = (time.strftime("%-I:%M %p", time.localtime(tip_ms / 1000))
               if isinstance(tip_ms, (int, float)) else "—")
        cfg_path = None
        if args.write_configs and total is not None:
            cfg_path = _write_config(ev, args.league, total, spread, ml_home, ml_away, tip_ms)

        # Live pace vs pregame expectation, using the league-aware clock + model.
        pace, proj = _live_pace(p, raw, stage, total)

        games.append({
            "config": cfg_path,
            "matchup": f"{ev.away} @ {ev.home}",
            "away": ev.away, "home": ev.home,
            "away_key": ev.away_key, "home_key": ev.home_key,
            "tip": tip, "stage": stage,
            "total": total,
            "pace": pace, "proj": proj,
            "spread": (f"{ev.home_key} {spread:+g}" if spread is not None else None),
            "ml_away": ml_away, "ml_home": ml_home,
        })

    payload = {
        "league": args.league.upper(),
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "count": len(games),
        "games": games,
    }
    OUT.write_text(json.dumps(payload, indent=2))
    print(f"wrote {OUT} — {len(games)} {args.league.upper()} games")
    for g in games:
        print(f"  {g['stage']:5} {g['matchup']:42} tot {g['total']} | {g['spread']} | "
              f"ML {g['ml_away']}/{g['ml_home']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
