"""A dependency-free live dashboard.

A background thread drives the engine over a provider's snapshot stream and keeps
the latest per-market evaluations + a signal history in a thread-safe
`DashboardState`. A stdlib HTTP server serves a single auto-refreshing page
(`index.html`) plus a JSON endpoint (`/api/state`) the page polls.

Run via `mrbet serve`. Works with any provider: `theodds` for live, `replay`
for a keyless demo.
"""

from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional

from ..config import GameConfig, Settings
from ..engine import Engine, Result
from ..models import Signal
from ..notify import Notifier, format_signal
from ..odds.base import OddsProvider, Snapshot
from ..storage import Storage

HTML_PATH = Path(__file__).with_name("index.html")


class DashboardState:
    """Thread-safe latest-state + signal log for the dashboard."""

    def __init__(self, game: GameConfig):
        self._lock = threading.Lock()
        self.game = game
        self.header: dict = {
            "away": game.event.away_key,
            "home": game.event.home_key,
            "away_name": game.event.away,
            "home_name": game.event.home,
            "status": "waiting",
        }
        self.rows: list[dict] = []
        self.signals: list[dict] = []

    def update(self, snap: Snapshot, results: list[Result]) -> None:
        with self._lock:
            st = snap.state
            self.header.update(
                {
                    "status": "live",
                    "period": st.period.value,
                    "clock": snap.meta.get("clock"),
                    "away_score": st.away_score,
                    "home_score": st.home_score,
                    "minutes_remaining": round(st.minutes_remaining, 1),
                    "minutes_elapsed": round(st.minutes_elapsed, 1),
                    "credits": snap.meta.get("credits_remaining"),
                    "updated": time.strftime("%H:%M:%S"),
                }
            )
            self.rows = [self._row(r) for r in results]

    def add_signal(self, signal: Signal) -> None:
        title, body = format_signal(signal)
        with self._lock:
            self.signals.insert(
                0,
                {
                    "time": time.strftime("%H:%M:%S"),
                    "title": title,
                    "body": body,
                    "strong": signal.strong,
                },
            )
            self.signals = self.signals[:50]

    def set_status(self, status: str) -> None:
        with self._lock:
            self.header["status"] = status

    def to_json(self) -> bytes:
        with self._lock:
            return json.dumps({"header": self.header, "rows": self.rows, "signals": self.signals}).encode()

    @staticmethod
    def _row(res: Result) -> dict:
        e = res.evaluation
        b = e.baseline
        return {
            "market": f"{b.team or 'GAME'} {b.period.value}",
            "pre": b.line,
            "live": e.live.line,
            "move_pct": round(e.pct_move * 100, 1),
            "side": e.side.value.upper(),
            "fair": round(e.fair_final, 1),
            "edge": round(e.edge_pts, 1),
            "prob": round(e.prob * 100),
            "ev": round(e.ev * 100, 1),
            "odds": e.offered_odds,
            "stake": e.kelly_stake,
            "flagged": res.signal is not None,
            "strong": bool(res.signal and res.signal.strong),
        }


def _poller(state: DashboardState, engine: Engine, provider: OddsProvider,
            notifier: Optional[Notifier], log: bool) -> None:
    # Create the SQLite connection inside this thread (sqlite is not shareable
    # across threads), and close it when polling ends.
    storage = Storage(event_id=engine.game.event.id) if log else None
    try:
        for snap in provider.snapshots():
            results = engine.process_snapshot(snap)
            state.update(snap, results)
            for r in results:
                if storage:
                    storage.log(r.evaluation, r.signal)
                if r.signal:
                    state.add_signal(r.signal)
                    if notifier:
                        notifier.maybe_notify(r.signal)
    except Exception as exc:  # pragma: no cover - keep server alive
        state.header["error"] = str(exc)
    finally:
        if storage:
            storage.close()
        state.set_status("stopped")


def _make_handler(state: DashboardState):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):  # silence default logging
            pass

        def do_GET(self):
            if self.path.startswith("/api/state"):
                self._send(200, "application/json", state.to_json())
            elif self.path in ("/", "/index.html"):
                self._send(200, "text/html; charset=utf-8", HTML_PATH.read_bytes())
            else:
                self._send(404, "text/plain", b"not found")

        def _send(self, code, ctype, body):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler


def serve(
    settings: Settings,
    game: GameConfig,
    provider: OddsProvider,
    host: str = "127.0.0.1",
    port: int = 8000,
    notify: bool = True,
) -> None:
    state = DashboardState(game)
    engine = Engine(settings, game, provider)
    notifier = Notifier(settings.notifications) if notify else None

    thread = threading.Thread(
        target=_poller, args=(state, engine, provider, notifier, True), daemon=True
    )
    thread.start()

    httpd = ThreadingHTTPServer((host, port), _make_handler(state))
    print(f"Dashboard live at http://{host}:{port}  (Ctrl-C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping.")
    finally:
        httpd.server_close()
