"""A dependency-free dashboard server.

Serves the single `index.html` plus a `/api/state` JSON endpoint the page polls.
State is computed once up front from the universe (a full pull through the feed)
and cached; hitting refresh re-reads the cached state. This mirrors mrbet's
dashboard server but for the trend-following research view.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from ..config import Settings
from ..exhibit import build_state
from ..models import Bar

HTML_PATH = Path(__file__).with_name("index.html")


def _make_handler(state_json: bytes):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):  # silence default logging
            pass

        def do_GET(self):
            if self.path.startswith("/api/state"):
                self._send(200, "application/json", state_json)
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
    series: dict[str, list[Bar]],
    settings: Settings,
    source: str = "—",
    host: str = "127.0.0.1",
    port: int = 8000,
) -> None:
    state = build_state(series, settings, source=source)
    state_json = json.dumps(state).encode()
    httpd = ThreadingHTTPServer((host, port), _make_handler(state_json))
    print(f"Driftwood dashboard live at http://{host}:{port}  (Ctrl-C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping.")
    finally:
        httpd.server_close()
