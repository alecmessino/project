"""Desktop + push notifications for flagged signals, with de-duplication.

Push uses ntfy.sh by default (free, zero-config: set NTFY_TOPIC and subscribe to
that topic in the ntfy app). Pushover is supported if PUSHOVER_TOKEN/USER are set.
Desktop uses plyer when available, falling back to a console print.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import requests

from .config import NotificationSettings
from .models import Signal


@dataclass
class _Sent:
    ev: float


class Notifier:
    def __init__(self, settings: NotificationSettings):
        self.settings = settings
        self._sent: dict[str, _Sent] = {}

    def maybe_notify(self, signal: Signal) -> bool:
        """Send if this signal is new or its EV improved enough. Returns True if sent."""
        key = signal.dedupe_key
        prev = self._sent.get(key)
        ev = signal.evaluation.ev
        if prev is not None and ev - prev.ev < self.settings.reissue_ev_delta:
            return False
        self._sent[key] = _Sent(ev=ev)
        title, body = format_signal(signal)
        if self.settings.desktop:
            _desktop(title, body)
        if self.settings.push:
            _push(title, body, strong=signal.strong)
        return True


def format_signal(signal: Signal) -> tuple[str, str]:
    e = signal.evaluation
    b = e.baseline
    tgt = b.team or "Game"
    period = b.period.value.upper()
    tag = "🔥 STRONG" if signal.strong else "📈"
    title = f"{tag} {e.side.value.upper()} {tgt} {period} {e.live.line} @ {e.offered_odds:+d}"
    body = (
        f"Pregame {b.line} -> live {e.live.line} ({e.pct_move*100:+.1f}%)\n"
        f"Fair final {e.fair_final:.1f} | edge {e.edge_pts:+.1f} pts\n"
        f"P({e.side.value})={e.prob*100:.1f}% vs implied {e.implied_prob*100:.1f}%\n"
        f"EV {e.ev*100:+.1f}% | stake ${e.kelly_stake:.2f}\n"
        f"score {e.state.away_score}-{e.state.home_score}, "
        f"{e.state.minutes_remaining:.1f} min left"
    )
    return title, body


def _desktop(title: str, body: str) -> None:
    try:
        from plyer import notification  # type: ignore

        notification.notify(title=title, message=body, timeout=15)
        return
    except Exception:
        print(f"[DESKTOP] {title}\n{body}\n")


def _push(title: str, body: str, strong: bool = False) -> None:
    token = os.environ.get("PUSHOVER_TOKEN")
    user = os.environ.get("PUSHOVER_USER")
    if token and user:
        _pushover(title, body, token, user, strong)
        return
    topic = os.environ.get("NTFY_TOPIC")
    if topic:
        _ntfy(title, body, topic, strong)
        return
    print(f"[PUSH:unconfigured] {title}")


def _ntfy(title: str, body: str, topic: str, strong: bool) -> None:
    server = os.environ.get("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
    try:
        requests.post(
            f"{server}/{topic}",
            data=body.encode("utf-8"),
            headers={
                "Title": title,
                "Priority": "high" if strong else "default",
                "Tags": "money_with_wings",
            },
            timeout=10,
        )
    except requests.RequestException as exc:  # pragma: no cover - network
        print(f"[ntfy error] {exc}")


def _pushover(title: str, body: str, token: str, user: str, strong: bool) -> None:
    try:
        requests.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": token,
                "user": user,
                "title": title,
                "message": body,
                "priority": 1 if strong else 0,
            },
            timeout=10,
        )
    except requests.RequestException as exc:  # pragma: no cover - network
        print(f"[pushover error] {exc}")
