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
# Re-alert the same market/side only on a BIG EV improvement AND after a cooldown —
# the dedup key is market|side (NOT the live line), so a moving line no longer fires
# a fresh alert every cycle. This is the main lever for alert frequency.
EV_REALERT_JUMP = 12.0       # EV must improve at least this much (percentage points)
ALERT_COOLDOWN_SEC = 360.0   # ...and at least this long since the last alert (6 min)
EDGE_MIN_REMAINING = 3.0     # require this many minutes left in the game
# Execution-logic layer (Discord only — the dashboard always shows raw rows):
ALERTS_PER_GAME_MAX = 6      # hard cap of alerts fired per game id
COOLDOWN_CLOCK_MIN = 3.0     # min GAME-CLOCK minutes between any two alerts
LINE_SHIFT_MIN = 4.0         # re-alert same market+side only if the line moved this far
HYSTERESIS_EDGE = 3.0        # opposite side of an alerted market needs this much extra edge

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
_prev_scope = prev_fwd.get("scope", {})
# Capture state (which cadence marks are done, the started heartbeat, edge-alert
# dedup) belongs to ONE game. If forward.json is from a different game, start fresh
# so a new game doesn't inherit the prior game's "already captured" marks (which
# would suppress every capture and leave the table + chart empty).
_same_game = _prev_scope.get("game") == game.event.id
# The forward ledger keys aren't event-scoped (game_total:full:game:over is the same
# key every game), so a new game must start with a FRESH ledger — otherwise games
# clobber each other and the Forward Test shows a mix of the wrong game's bets.
ledger = prev_fwd.get("ledger", {}) if _same_game else {}
captured = set(_prev_scope.get("captured_marks", [])) if _same_game else set()
# One-time "game has started, live data flowing" heartbeat (persists across runs).
started_notified = bool(_prev_scope.get("game_started_notified", False)) if _same_game else False
# Edge-alert dedup map: "market|side|live" -> last EV alerted.
edge_alerted = dict(_prev_scope.get("edge_alerted", {})) if _same_game else {}
# Stateful execution tracker (per game id): how many alerts fired, the game clock at
# the last alert, and the last-alerted side/line/edge per market — drives the dedup,
# hysteresis, hard-cap and cooldown rules below.
alert_state = (_prev_scope.get("alert_state") if _same_game else None) or \
    {"count": 0, "last_elapsed": None, "markets": {}}
# Settled H1 final [away, home], captured once at halftime so the engine can derive
# the 2nd-half (H2) slice. Persists across cycles in the forward scope.
h1_final = _prev_scope.get("h1_final") if _same_game else None
# Rolling per-market line history [[ts, line], ...] for the volatility gate.
line_hist = dict(_prev_scope.get("line_hist", {})) if _same_game else {}
finals = getattr(game, "finals", None) or None

# Volatility gate: a strict rolling coefficient-of-variation filter on each market's
# line history. When the line is jumping (CV of the last VOL_WINDOW_SEC of quotes
# >= VOL_CV_MAX), the edge readout is least trustworthy exactly when it looks
# biggest — so Discord alerts for that market are SUPPRESSED, while the row stays
# on the dashboard flagged "High Volatility — Paused" for live monitoring.
VOL_WINDOW_SEC = 300.0    # rolling window (5 min)
VOL_CV_MAX = 0.005        # CV (std/mean) >= 0.5% of the line -> high volatility
VOL_MIN_POINTS = 3        # need >= this many distinct quotes to judge


def _vol_cv(market: str, now: float) -> float | None:
    """Rolling CV (std/mean) of a market's line over the window; None if too few."""
    pts = [v for t, v in line_hist.get(market, []) if now - t <= VOL_WINDOW_SEC]
    if len(pts) < VOL_MIN_POINTS:
        return None
    mean = sum(pts) / len(pts)
    if not mean:
        return None
    var = sum((v - mean) ** 2 for v in pts) / len(pts)
    return (var ** 0.5) / abs(mean)


def _update_volatility(rows: list) -> None:
    """Append current lines to the history and stamp vol_paused/vol_cv on each row."""
    now = time.time()
    for r in rows:
        m, live = r.get("market"), r.get("live")
        if m is None or live is None:
            continue
        hist = line_hist.setdefault(m, [])
        if not hist or hist[-1][1] != live:      # record only real line changes
            hist.append([now, float(live)])
        line_hist[m] = [p for p in hist if now - p[0] <= VOL_WINDOW_SEC * 2][-40:]
        cv = _vol_cv(m, now)
        r["vol_cv"] = round(cv, 5) if cv is not None else None
        r["vol_paused"] = bool(cv is not None and cv >= VOL_CV_MAX)
        if r["vol_paused"]:
            print(f"volatility gate: {m} CV={cv:.4f} >= {VOL_CV_MAX} — alerts paused")

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
projections = {}   # model's projected period totals (full / 1H / 2H) for the dashboard


def run_edge_alerts() -> None:
    """Fire Discord edge alerts through the EXECUTION-LOGIC layer (the dashboard rows
    always show raw data; only the webhook is filtered):
      * volatility gate — suppress while the line is jumping (high rolling CV),
      * dedup — same market+side re-alerts only if the line moved >= LINE_SHIFT_MIN,
      * hysteresis — the opposite side needs +HYSTERESIS_EDGE extra edge (anti flip-flop),
      * hard cap — at most ALERTS_PER_GAME_MAX alerts per game,
      * cooldown — >= COOLDOWN_CLOCK_MIN of GAME CLOCK between any two alerts.
    """
    h = state.header
    if h.get("minutes_remaining", 0) < EDGE_MIN_REMAINING:
        return
    elapsed = h.get("minutes_elapsed") or 0.0
    mkts = alert_state.setdefault("markets", {})
    for r in state.rows:
        edge, ev = r.get("edge", 0), r.get("ev", 0)
        if edge < EDGE_MIN or ev < EV_MIN:
            continue
        if r.get("vol_paused"):
            print(f"exec: {r['market']} {r['side']} suppressed — high volatility "
                  f"(CV {r.get('vol_cv')})")
            continue
        market, side = r["market"], r["side"]
        try:
            live = float(r["live"])
        except (TypeError, ValueError):
            continue
        last = mkts.get(market)
        # Rule 2 — hysteresis: opposite side of an already-alerted market needs extra edge.
        if last and last.get("side") != side:
            if edge < EDGE_MIN + HYSTERESIS_EDGE:
                print(f"exec: {market} {side} held — opp of alerted {last['side']}, "
                      f"edge {edge} < {EDGE_MIN + HYSTERESIS_EDGE} (hysteresis)")
                continue
        # Rule 1 — dedup: same side re-alerts only if the line moved far enough.
        elif last and last.get("side") == side:
            if abs(live - last.get("line", live)) < LINE_SHIFT_MIN:
                print(f"exec: {market} {side} held — line {live} within "
                      f"{LINE_SHIFT_MIN} of last alert {last.get('line')}")
                continue
        # Rule 3a — hard cap of alerts per game.
        if alert_state.get("count", 0) >= ALERTS_PER_GAME_MAX:
            print(f"exec: {market} {side} held — hard cap {ALERTS_PER_GAME_MAX} reached")
            continue
        # Rule 3b — minimum game-clock cooldown between any two alerts.
        le = alert_state.get("last_elapsed")
        if le is not None and (elapsed - le) < COOLDOWN_CLOCK_MIN:
            print(f"exec: {market} {side} held — {elapsed - le:.1f}m < "
                  f"{COOLDOWN_CLOCK_MIN}m game-clock cooldown")
            continue
        # ---- passes the execution layer: FIRE ----
        tag = "🔥 STRONG EDGE" if ev >= 30 else "📈 EDGE"
        _discord(
            f"{tag}: {market} {side} {r['live']}",
            f"fair {r['fair']} · edge {r['edge']:+} pts · EV {r['ev']:+}% · "
            f"win {r.get('prob','?')}% @ {r['odds']:+} · stake ${r.get('stake',0):.2f}\n"
            f"{h.get('clock','?')} · {h.get('away','away')} {h.get('away_score')} "
            f"{h.get('home','home')} {h.get('home_score')} "
            f"({h.get('minutes_remaining','?')} min left)",
            strong=ev >= 30,
        )
        alert_state["count"] = alert_state.get("count", 0) + 1
        alert_state["last_elapsed"] = elapsed
        mkts[market] = {"side": side, "line": live, "edge": edge}
        print(f"edge alert [{alert_state['count']}/{ALERTS_PER_GAME_MAX}]: "
              f"{market} {side} EV {ev}% @ line {live}")


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
    # Once the 2nd half is underway, capture the settled H1 final (Q1+Q2 from ESPN,
    # exact) so the engine can derive the H2 total. Fetch once, then carry it via the
    # forward scope. Stamp it onto the live state so derive_state(H2) can split scores.
    _reg = espn.minutes_elapsed + espn.minutes_remaining
    _half_len = (_reg / 2.0) if _reg > 0 else 24.0
    if elapsed >= _half_len:
        if not h1_final:
            from mrbet.espn import live_h1_final
            away_tag = str(game.event.away).split()[-1]
            home_tag = str(game.event.home).split()[-1]
            got = live_h1_final(_league, away_tag, home_tag)
            if got:
                h1_final = list(got)   # [away_h1, home_h1]
                print(f"captured H1 final {away_tag} {got[0]} - {got[1]} {home_tag}")
        if h1_final:
            espn.h1_away, espn.h1_home = int(h1_final[0]), int(h1_final[1])

    # Model PROJECTIONS for combined-total periods (full / 1H / 2H). Bovada's coupon
    # only carries the live FULL line, so for the halves we surface the model's
    # projected total — you compare it to the book's live 1H/2H O/U on your phone.
    from mrbet.engine import derive_state as _derive
    from mrbet.reversion import projected_final as _proj
    from mrbet.models import Period as _P, MarketType as _MT
    for _pk, _per in (("full", _P.FULL), ("h1", _P.H1), ("h2", _P.H2)):
        _pst = _derive(espn, _per)
        _base = game.baseline_for(_MT.GAME_TOTAL, _per)
        if _pst is None or _base is None:
            continue
        projections[_pk] = round(_proj(_base.line, _pst.total_score, _pst,
                                       settings.model.beta, settings.model.min_minutes_elapsed), 1)
    if projections:
        print(f"projections: {projections}")

    # Earliest uncaptured cadence mark for the ARCHIVE (the clean forward-test record).
    # Marks we're already well past (a mid-game restart) are retired without capturing,
    # so we never label current lines as a stale elapsed point.
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

    # Bovada lines are FREE, so refresh the DISPLAY (markets table) EVERY cycle — the
    # live total now tracks the book within one cycle (~75s) instead of going stale
    # between cadence marks. The paid Odds-API fallback still only fetches at a mark.
    is_free = isinstance(provider, BovadaProvider)
    lines = provider._fetch_lines() if (is_free or due is not None) else None

    if lines:
        from mrbet.odds.base import Snapshot
        snap = Snapshot(state=espn, lines=lines, meta={
            "credits_remaining": provider.credits_remaining(),
            "clock": provider._clock, "cadence_mark": due})
        results = Engine(settings, game, provider=None).process_snapshot(snap)
        state.update(snap, results)                 # fresh rows + header every cycle
        _update_volatility(state.rows)              # rolling-CV gate per market
        for r in results:
            if r.signal:
                state.add_signal(r.signal)
                notifier.maybe_notify(r.signal)      # reversion push the moment it flags
        # Append to the forward-test ARCHIVE only at a cadence mark (keeps the record
        # clean), even though the live table refreshes every cycle.
        if due is not None:
            ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            for r in results:
                fwd.merge_signal(ledger, r.evaluation, ts, matchup, finals)
            fwd.append_capture(ODDS_HISTORY, game.event.id, snap, results, ts, thresholds={
                "pct_move": settings.triggers.pct_move_threshold,
                "edge_pts": settings.triggers.edge_pts_threshold,
                "ev": settings.triggers.ev_threshold,
            })
            captured.add(due)
            captured_now = due
            print(f"archived cadence mark m{due:.0f}")
        else:
            full = next((r.evaluation.live.line for r in results
                         if r.evaluation.baseline.market_type.value == "game_total"
                         and r.evaluation.baseline.period.value == "full"), "?")
            print(f"display refresh at {elapsed:.1f}m — live game total {full}")
    else:
        # Paid feed between marks (or fetch failed) — keep prior rows, refresh clock.
        state.header.update({
            "status": "live", "period": espn.period.value,
            "clock": provider._clock, "away_score": espn.away_score,
            "home_score": espn.home_score,
            "minutes_remaining": round(espn.minutes_remaining, 1),
            "minutes_elapsed": round(espn.minutes_elapsed, 1),
            "updated": time.strftime("%H:%M:%S"),
        })
        state.rows = prev_state.get("rows", [])
        print(f"between marks at {elapsed:.1f}m — no fresh lines, keeping prior rows")

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
live_payload["projections"] = projections   # model full/1H/2H projected totals
# Execution-layer state for the UI's lock pills. Embedded in the live payload so the
# rows and lock states always come from the SAME cycle (no client/server desync);
# docs/alert_state.json is the same snapshot as a standalone payload for debugging.
exec_payload = {
    "game": game.event.id,
    "updated": time.strftime("%H:%M:%S"),
    "elapsed": state.header.get("minutes_elapsed"),
    "count": alert_state.get("count", 0),
    "max": ALERTS_PER_GAME_MAX,
    "cooldown_min": COOLDOWN_CLOCK_MIN,
    "line_shift_min": LINE_SHIFT_MIN,
    "hysteresis_edge": HYSTERESIS_EDGE,
    "edge_min": EDGE_MIN,
    "ev_min": EV_MIN,
    "last_elapsed": alert_state.get("last_elapsed"),
    "markets": alert_state.get("markets", {}),
}
live_payload["exec"] = exec_payload
(ROOT / "docs" / "alert_state.json").write_text(json.dumps(exec_payload))
LIVE_STATE_JSON.write_bytes(json.dumps(live_payload).encode())
STATE_JSON.write_bytes(state.to_json())   # legacy alias, kept for older deploys

fwd.dump(FORWARD_JSON, ledger, scope={
    "matchup": matchup, "game": game.event.id,
    "cadence": "9-point timeout", "marks": MARKS,
    "captured_marks": sorted(captured),
    "game_started_notified": started_notified,
    "edge_alerted": edge_alerted,
    "alert_state": alert_state,
    "h1_final": h1_final,
    "line_hist": line_hist,
})
print(f"Wrote {LIVE_STATE_JSON.name} ({len(state.rows)} rows, "
      f"{len(live_payload.get('chart',{}).get('move',[]))} chart pts) and {FORWARD_JSON.name} "
      f"({len(ledger)} bets, {len(captured)}/{len(MARKS)} marks captured)"
      + (f" [+m{captured_now:.0f}]" if captured_now is not None else ""))
