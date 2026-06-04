"""Cadence-aware forward-capture poller -> docs/state.json + docs/forward.json.

Runs as the 5-minute GitHub Actions cron OR inside scripts/live_run.py's loop.
Every run it checks the FREE ESPN clock; it spends a (paid) Odds API fetch ONLY
when the game clock has crossed an uncaptured 9-point cadence mark (Q1-Q3
timeouts + breaks: 6,9,12,18,21,24,30,33,36). Captured marks persist across runs
in docs/forward.json, so the whole game costs ~9 odds calls. Between marks it
just refreshes the clock/score for free.

Two alert paths fire to Discord (both deduped):
  1. Reversion trigger — the conjunctive gate in triggers.to_signal (via Notifier).
  2. Edge alert — any market with edge >= EDGE_MIN pts AND EV >= EV_MIN%, regardless
     of line move/direction. Catches high-confidence plays the move-gate suppresses.

Active game: MRBET_GAME env (default sas_okc_2026-05-30.yaml). Key from the
ODDS_API_KEY secret (CI) or .env (local).
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mrbet import forward as fwd
from mrbet.cadence import timeout_marks
from mrbet.config import GameConfig, Settings
from mrbet.engine import Engine
from mrbet.envload import load_env
from mrbet.notify import Notifier, _discord
from mrbet.bovada_feed import BovadaProvider
from mrbet.odds.theodds import TheOddsProvider   # fallback if Bovada is unreachable
from mrbet.web.server import DashboardState

load_env()

GAME_YAML = pathlib.Path(os.environ.get(
    "MRBET_GAME", ROOT / "config" / "games" / "sas_okc_2026-05-30.yaml"))
STATE_JSON = ROOT / "docs" / "state.json"           # legacy alias (older deploys)
LIVE_STATE_JSON = ROOT / "docs" / "live_market_state.json"  # the hot stream file
FORWARD_JSON = ROOT / "docs" / "forward.json"
ODDS_HISTORY = ROOT / "docs" / "odds_history.json"   # raw both-sides quote archive
# Capture at the opening tip (~1 min in) plus the 9-point timeout cadence, so the
# first half is fully auditable from the very first live line. Bovada lines are
# free, so the extra opening capture costs nothing.
OPENING_MARK = 1.0
MARKS = sorted({OPENING_MARK, *timeout_marks()})   # [1,6,9,12,18,21,24,30,33,36]
# Don't archive a mark we're already well past: on a mid-game (re)start the current
# lines would be mislabeled as an old elapsed point, corrupting the audit trail.
BACKFILL_WINDOW = 4.0

# The full-game total market key the Distance-to-Trigger chart tracks.
FULL_MARKET_KEY = "game_total:full:game"


def _chart_series(captures, thresholds=None, event_id=None) -> dict:
    """Compact full-game (move%, edge-pts) time series for the stress chart.

    Mirrors the dashboard's extractFull() so the embedded series renders without
    a second fetch — one live_market_state.json drives both the table and chart.
    The capture archive accumulates ACROSS games (one list, deduped per
    event_id+mark), so we filter to `event_id` to avoid drawing a prior game's
    curve onto tonight's chart.
    """
    move, edge = [], []
    for cap in sorted(captures or [], key=lambda c: (c.get("minutes_elapsed")
                                                      or c.get("mark") or 0)):
        if event_id is not None and cap.get("event_id") != event_id:
            continue
        m = next((x for x in cap.get("markets", [])
                  if x.get("market") == FULL_MARKET_KEY), None)
        if not m or m.get("pct_move") is None:
            continue
        t = cap.get("minutes_elapsed")
        if t is None:
            t = cap.get("mark")
        move.append({"x": t, "y": round(abs(m["pct_move"]) * 100, 1)})
        edge.append({"x": t, "y": round(m.get("edge_pts") or 0, 1)})
    out = {"move": move, "edge": edge}
    if thresholds:
        out["thresholds"] = thresholds
    return out

# Edge-alert thresholds (parallel to the reversion trigger). The edge here is the
# directional model edge for whichever side the model favors (e.row['side'] is
# OVER or UNDER), so a hot start that inflates the line above fair fires a
# symmetric UNDER alert exactly like a cold-start OVER. Lowered 3.0 -> 2.0 to match
# the config net for the higher-variance NBA Finals env (EV_MIN keeps it selective).
EDGE_MIN = 2.0       # model edge in points (directional: OVER or UNDER)
EV_MIN = 15.0        # EV percent
EV_REALERT_JUMP = 8.0  # re-alert same market/side/line only if EV jumps this much
EDGE_MIN_REMAINING = 3.0  # require this many minutes left in the game

settings = Settings.load(ROOT / "config" / "settings.yaml")
game = GameConfig.load(GAME_YAML)
matchup = f"{game.event.away_key} @ {game.event.home_key}"

# Fires desktop/push/SMS/Discord/Slack per settings.notifications, but only on a
# real Signal (every threshold cleared). Webhook URLs come from env (secrets).
notifier = Notifier(settings.notifications)

# Restore prior dashboard state + forward ledger + captured marks. Prefer the new
# live stream file, falling back to the legacy state.json if a deploy predates it.
_prev_path = LIVE_STATE_JSON if LIVE_STATE_JSON.exists() else STATE_JSON
prev_state = json.loads(_prev_path.read_text()) if _prev_path.exists() else {}
prev_fwd = json.loads(FORWARD_JSON.read_text()) if FORWARD_JSON.exists() else {}
ledger = prev_fwd.get("ledger", {})
captured = set(prev_fwd.get("scope", {}).get("captured_marks", []))
# One-time "game has started, live data flowing" heartbeat (persists across runs).
started_notified = bool(prev_fwd.get("scope", {}).get("game_started_notified", False))
# Edge-alert dedup map: "market|side|live" -> last EV alerted.
edge_alerted = dict(prev_fwd.get("scope", {}).get("edge_alerted", {}))
finals = getattr(game, "finals", None) or None

state = DashboardState(game)
state.signals = prev_state.get("signals", [])

# --- THE FLIP: live Bovada feed is now primary --------------------------- #
# League comes from the game config (NBA full=48 / WNBA full=40); BovadaProvider
# auto-detects pre->live and pulls clock+score+lines from one source.
_league = str(getattr(game.event, "league", "nba")).lower()
provider = BovadaProvider(event=game.event, league=_league, max_polls=1)

# Safety net: Bovada is geo/Cloudflare-fronted and a GitHub Actions IP may be
# blocked even though it works from a residential host. If we can't reach/match
# the game on Bovada, fall back to the Odds API so the dashboard never goes dark.
if provider._refresh() is None:
    print("[poller] Bovada unreachable/no match — falling back to TheOddsProvider",
          file=sys.stderr)
    provider = TheOddsProvider(
        event=game.event, markets=settings.engine.markets, poll_interval=0,
        books=settings.engine.books, region=settings.engine.region,
        fallback_consensus=settings.engine.fallback_consensus, max_polls=1,
    )

espn = provider._fetch_state()            # live clock/score (Bovada or ESPN fallback)
captured_now = None


def run_edge_alerts() -> None:
    """Fire a Discord edge alert for any high-confidence market (deduped)."""
    h = state.header
    if h.get("minutes_remaining", 0) < EDGE_MIN_REMAINING:
        return
    for r in state.rows:
        edge, ev = r.get("edge", 0), r.get("ev", 0)
        if edge < EDGE_MIN or ev < EV_MIN:
            continue
        key = f"{r['market']}|{r['side']}|{r['live']}"
        prev = edge_alerted.get(key)
        if prev is not None and ev < prev + EV_REALERT_JUMP:
            continue
        edge_alerted[key] = ev
        tag = "🔥 STRONG EDGE" if ev >= 30 else "📈 EDGE"
        _discord(
            f"{tag}: {r['market']} {r['side']} {r['live']}",
            f"fair {r['fair']} · edge {r['edge']:+} pts · EV {r['ev']:+}% · "
            f"win {r.get('prob','?')}% @ {r['odds']:+} · stake ${r.get('stake',0):.2f}\n"
            f"{h.get('clock','?')} · SA {h.get('away_score')} OKC {h.get('home_score')} "
            f"({h.get('minutes_remaining','?')} min left)",
            strong=ev >= 30,
        )
        print(f"edge alert: {r['market']} {r['side']} EV {ev}%")


if espn is None:
    # Game not live yet (or finished/not found) — refresh header, spend nothing.
    state.header.update({
        "status": "waiting", "updated": time.strftime("%H:%M:%S"),
        "error": "game not live on ESPN scoreboard (pre-tip or finished)",
    })
    state.rows = []   # no live markets before tip / after final
else:
    # ESPN lists the game as "live" at 0-0 / 48:00 even pre-tip, so gate the
    # heartbeat on real progress — the clock has ticked off the opening 48:00 or
    # points are on the board. That's the true tip-off / data-flowing moment.
    game_underway = espn.minutes_elapsed > 0 or (espn.away_score + espn.home_score) > 0
    if game_underway and not started_notified:
        _discord(
            "🏀 Game started — live data flowing",
            f"{matchup} is live on the ESPN scoreboard and the poller is now "
            f"receiving score/clock data. Mean-reversion + edge alerts are armed; "
            f"you'll get a push here the moment a play qualifies.\n"
            f"Score {espn.away_score}-{espn.home_score} · "
            f"{round(espn.minutes_remaining, 1)} min remaining.",
        )
        started_notified = True
        print("sent game-started heartbeat to Discord")

    elapsed = espn.minutes_elapsed
    # Earliest uncaptured mark the clock has reached (one capture per run). Marks we
    # are already well past (a mid-game restart) are retired without capturing, so we
    # never label current lines as a stale elapsed point.
    due = None
    for m in MARKS:
        if m in captured:
            continue
        if m > elapsed:
            break
        if elapsed - m <= BACKFILL_WINDOW:
            due = m
            break
        captured.add(m)   # too far behind to capture accurately — retire it

    if due is not None:
        lines = provider._fetch_lines()    # PAID — only at a cadence mark
        from mrbet.odds.base import Snapshot
        snap = Snapshot(state=espn, lines=lines, meta={
            "credits_remaining": provider.credits_remaining(),
            "clock": provider._clock, "cadence_mark": due})
        results = engine = Engine(settings, game, provider=None).process_snapshot(snap)
        state.update(snap, results)
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        for r in results:
            if r.signal:
                state.add_signal(r.signal)
                notifier.maybe_notify(r.signal)   # reversion push the moment it flags
            fwd.merge_signal(ledger, r.evaluation, ts, matchup, finals)
        # Archive the raw quote (all markets, BOTH sides' prices) for forward testing.
        fwd.append_capture(ODDS_HISTORY, game.event.id, snap, results, ts, thresholds={
            "pct_move": settings.triggers.pct_move_threshold,
            "edge_pts": settings.triggers.edge_pts_threshold,
            "ev": settings.triggers.ev_threshold,
        })
        captured.add(due)
        captured_now = due
        print(f"captured cadence mark m{due:.0f} "
              f"(credits remaining: {provider.credits_remaining()})")
    else:
        # Between marks — free clock refresh, keep prior rows.
        state.header.update({
            "status": "live", "period": espn.period.value,
            "clock": provider._clock, "away_score": espn.away_score,
            "home_score": espn.home_score,
            "minutes_remaining": round(espn.minutes_remaining, 1),
            "minutes_elapsed": round(espn.minutes_elapsed, 1),
            "updated": time.strftime("%H:%M:%S"),
        })
        state.rows = prev_state.get("rows", [])
        print(f"between marks at {elapsed:.1f}m elapsed — no odds call (captured: {sorted(captured)})")

    # Parallel edge alert over whatever rows we have (fresh at a mark, else cached).
    run_edge_alerts()

# The hot stream payload: current table + signals + an embedded chart series so a
# single ~20s fetch advances both the "Live markets" table and the chart. Built by
# attaching the full-game move/edge series (from the capture archive) to the state.
live_payload = json.loads(state.to_json().decode())
try:
    _hist = json.loads(ODDS_HISTORY.read_text()) if ODDS_HISTORY.exists() else {}
    live_payload["chart"] = _chart_series(_hist.get("captures"), _hist.get("thresholds"),
                                          event_id=game.event.id)
except Exception as exc:   # never let a chart-build hiccup drop the live update
    print(f"[chart-series skipped] {exc}")
LIVE_STATE_JSON.write_bytes(json.dumps(live_payload).encode())
STATE_JSON.write_bytes(state.to_json())   # legacy alias, kept for older deploys

fwd.dump(FORWARD_JSON, ledger, scope={
    "matchup": matchup, "game": game.event.id,
    "cadence": "9-point timeout", "marks": MARKS,
    "captured_marks": sorted(captured),
    "game_started_notified": started_notified,
    "edge_alerted": edge_alerted,
})
print(f"Wrote {LIVE_STATE_JSON.name} ({len(state.rows)} rows, "
      f"{len(live_payload.get('chart',{}).get('move',[]))} chart pts) and {FORWARD_JSON.name} "
      f"({len(ledger)} bets, {len(captured)}/{len(MARKS)} marks captured)"
      + (f" [+m{captured_now:.0f}]" if captured_now is not None else ""))
