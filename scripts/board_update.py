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
import glob
import json
import pathlib
import sys
import time
from typing import Optional

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mrbet.bovada_feed import (   # noqa: E402
    BovadaProvider, _american, _handicap, board_events, event_from_bovada,
)

OUT = ROOT / "docs" / "board.json"
UPCOMING_OUT = ROOT / "docs" / "upcoming.json"

try:
    from zoneinfo import ZoneInfo
    _ET = ZoneInfo("America/New_York")
except Exception:                       # pragma: no cover
    _ET = None


def _et(tip_ms, fmt: str) -> str:
    """Format a Bovada startTime (ms) in US Eastern, matching the dashboard's label."""
    from datetime import datetime
    if not isinstance(tip_ms, (int, float)):
        return "—"
    dt = datetime.fromtimestamp(tip_ms / 1000, _ET) if _ET else datetime.fromtimestamp(tip_ms / 1000)
    return dt.strftime(fmt)


def _merge_board(this_league: str, fresh: list) -> list:
    """Merge freshly-discovered `this_league` games with other leagues already on the
    board, so refreshing one league never clobbers another (NBA Finals + WNBA coexist).

    - This league's games are fully replaced by `fresh` (a finished game that Bovada
      no longer lists simply drops out).
    - Other leagues persist, except games whose tip is >6h in the past — that retires
      yesterday's finished games over time without a separate cleanup job.
    """
    now = time.time()
    STALE_SECONDS = 6 * 3600
    try:
        prev = json.loads(OUT.read_text()).get("games", []) if OUT.exists() else []
    except (ValueError, OSError):
        prev = []
    kept = []
    for g in prev:
        if str(g.get("league", "")).upper() == this_league.upper():
            continue   # this league is fully refreshed from `fresh`
        tms = g.get("tip_ms")
        if isinstance(tms, (int, float)) and tms / 1000 < now - STALE_SECONDS:
            continue   # stale finished game from another league — retire it
        kept.append(g)
    merged = kept + fresh
    merged.sort(key=lambda x: (x.get("tip_ms") or 0))
    return merged


def _write_upcoming(games: list) -> None:
    """Auto-generate docs/upcoming.json from the discovered slate (no hand-edits).

    Shows games that haven't tipped yet (stage 'pre'), sorted by tip time, in the
    shape the Upcoming Games table renders. 'round'/series labels aren't in the
    Bovada feed, so we use the league as light context.
    """
    # "Upcoming" = tips in the future. The coupon's stage flag is unreliable
    # (it can read 'live' pre-tip), so trust Bovada's scheduled startTime instead.
    now = time.time()
    future = [x for x in games
              if isinstance(x.get("tip_ms"), (int, float)) and x["tip_ms"] / 1000 > now]
    upcoming = []
    for g in sorted(future, key=lambda x: x["tip_ms"]):
        # City = team name minus the nickname (last word), best-effort.
        away_city = " ".join(str(g["away"]).split()[:-1]) or g["away"]
        home_city = " ".join(str(g["home"]).split()[:-1]) or g["home"]
        cfg = g.get("config")
        upcoming.append({
            "date": g.get("date", "—"),
            "matchup": f"{away_city} @ {home_city}",
            "tip": g.get("tip", "—"),
            "total": (f"{g['total']:g}" if g.get("total") is not None else "—"),
            "spread": g.get("spread") or "—",
            "round": g.get("league", ""),
            "config": (cfg.split("/")[-1] if cfg else "—"),
        })
    UPCOMING_OUT.write_text(json.dumps({"games": upcoming}, indent=2))
    print(f"wrote {UPCOMING_OUT} — {len(upcoming)} upcoming game(s)")


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
  bovada_event_id: "{ev.id}"

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


def _find_existing_config(eid: str, ev, league: str) -> Optional[str]:
    """A config matching this Bovada game — by bovada_event_id, else by team names +
    league. Returns its repo-relative path, or None (so we know to auto-generate)."""
    away_tag = str(ev.away).split()[-1].lower()
    home_tag = str(ev.home).split()[-1].lower()
    for p in glob.glob(str(ROOT / "config" / "games" / "*.yaml")):
        try:
            block = (yaml.safe_load(pathlib.Path(p).read_text()) or {}).get("event", {})
        except Exception:
            continue
        if str(block.get("bovada_event_id") or "") == str(eid):
            return str(pathlib.Path(p).relative_to(ROOT))
        if str(block.get("league", "")).lower() != league.lower():
            continue
        a = str(block.get("away", "")).split()[-1].lower()
        h = str(block.get("home", "")).split()[-1].lower()
        if a and h and a == away_tag and h == home_tag:
            return str(pathlib.Path(p).relative_to(ROOT))
    return None


def ensure_live_config(league: str) -> Optional[tuple]:
    """If a Bovada game in `league` is LIVE, return (config_relpath, detail, created)
    — generating a config from the discovered Bovada metadata when none exists, so
    the tracker can attach to ANY live game without a hand-made config. Pre-built
    configs are always reused if present (hand-tuning still wins). None if nothing live.
    """
    for raw in board_events(league):
        ev = event_from_bovada(raw)
        provider = BovadaProvider(ev, league=league, max_polls=1)
        provider._raw_event = raw
        st = provider._fetch_state()            # scores endpoint — None unless truly live
        if st is None:
            continue
        eid = str(raw.get("id"))
        detail = f"{provider._clock} {ev.away_key} {st.away_score}-{st.home_score} {ev.home_key}"
        existing = _find_existing_config(eid, ev, league)
        if existing:
            return existing, detail, False      # hand-tuned / prior config wins
        total, spread, ml_home, ml_away = _game_markets(raw)
        if total is None:
            print(f"  live {ev.away_key}@{ev.home_key} but no total posted yet — skip")
            continue
        path = _write_config(ev, league, total, spread, ml_home, ml_away, raw.get("startTime"))
        print(f"  auto-generated config {path} for live {ev.away_key}@{ev.home_key}")
        return path, detail + " (auto-config)", True
    return None


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


def _nearest_upcoming_config(league: str) -> Optional[str]:
    """Path to the league's config whose tip is nearest in the FUTURE (the next game
    to lock), so a pregame refresh never has to hardcode a filename."""
    from datetime import datetime
    now = time.time()
    best, best_dt = None, None
    for p in glob.glob(str(ROOT / "config" / "games" / "*.yaml")):
        try:
            ev = (yaml.safe_load(pathlib.Path(p).read_text()) or {}).get("event", {})
        except Exception:
            continue
        if str(ev.get("league", "")).lower() != league.lower():
            continue
        ct = str(ev.get("commence_time", "") or "")
        epoch = None
        for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"):
            try:
                epoch = datetime.strptime(ct.replace("Z", "+0000"), fmt).timestamp(); break
            except ValueError:
                continue
        if epoch is None or epoch <= now - 6 * 3600:   # skip games already well past
            continue
        if best_dt is None or epoch < best_dt:
            best, best_dt = p, epoch
    return best


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Write docs/board.json for a league's slate")
    ap.add_argument("--league", default="wnba")
    ap.add_argument("--write-configs", action="store_true",
                    help="also auto-generate config/games/*.yaml for each game")
    ap.add_argument("--refresh-config", metavar="PATH", default=None,
                    help="lock latest Bovada lines into an existing unified config "
                         "in place (preserves its event block / bovada_event_id)")
    ap.add_argument("--refresh-upcoming", action="store_true",
                    help="auto-find the league's nearest UPCOMING config and refresh "
                         "its lines (no hardcoded filename)")
    args = ap.parse_args(argv)

    events = board_events(args.league)
    target = args.refresh_config
    if args.refresh_upcoming and not target:
        target = _nearest_upcoming_config(args.league)
        print(f"refresh-upcoming: nearest {args.league.upper()} config -> {target or 'none found'}")
    if target:
        _refresh_config_lines(target, events)
    games = []
    for raw in events:
        ev = event_from_bovada(raw)
        p = BovadaProvider(ev, league=args.league, max_polls=1)
        total, spread, ml_home, ml_away = _game_markets(raw)
        tip_ms = raw.get("startTime")
        tip = _et(tip_ms, "%-I:%M %p")              # ET (matches the dashboard label)
        date = _et(tip_ms, "%a %b %-d, %Y")
        stage = p._classify_stage(raw)
        # The coupon's live flag can fire before tip; a game can't be live before its
        # scheduled start, so force 'pre' when the tip is still in the future.
        if isinstance(tip_ms, (int, float)) and tip_ms / 1000 > time.time():
            stage = "pre"
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
            "tip": tip, "date": date, "tip_ms": tip_ms,
            "league": args.league.upper(), "stage": stage,
            "total": total,
            "pace": pace, "proj": proj,
            "spread": (f"{ev.home_key} {spread:+g}" if spread is not None else None),
            "ml_away": ml_away, "ml_home": ml_home,
        })

    merged = _merge_board(args.league, games)
    leagues = sorted({str(g.get("league", "")).upper() for g in merged if g.get("league")})
    payload = {
        "league": " + ".join(leagues) or args.league.upper(),
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "count": len(merged),
        "games": merged,
    }
    OUT.write_text(json.dumps(payload, indent=2))
    print(f"wrote {OUT} — {len(games)} fresh {args.league.upper()} + "
          f"{len(merged) - len(games)} kept = {len(merged)} games ({'+'.join(leagues)})")
    _write_upcoming(merged)   # keep docs/upcoming.json self-maintained (all leagues)
    for g in merged:
        print(f"  {g.get('league',''):4} {g['stage']:5} {g['matchup']:42} tot {g['total']} | {g['spread']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
