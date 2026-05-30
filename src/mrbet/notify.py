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

# Public dashboard — appended to alerts so the phone push is tappable.
DASHBOARD_URL = os.environ.get("MRBET_DASHBOARD_URL",
                               "https://alecmessino.github.io/project/")


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
        if self.settings.sms:
            _sms_gateway(signal)
        if self.settings.discord:
            _discord(title, body, strong=signal.strong)
        if self.settings.slack:
            _slack(title, body, strong=signal.strong)
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
        f"{e.state.minutes_remaining:.1f} min left\n"
        f"→ {DASHBOARD_URL}"
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
                "Click": DASHBOARD_URL,
                "Tags": "money_with_wings",
            },
            timeout=10,
        )
    except requests.RequestException as exc:  # pragma: no cover - network
        print(f"[ntfy error] {exc}")


def _sms_gateway(signal: Signal) -> None:
    """Send a clean SMS via an email-to-SMS carrier gateway (stdlib only, no new deps).

    Required env vars (set in .env or GitHub Secrets — never hardcode):
      SMS_EMAIL_TARGET  e.g. 2125551234@txt.att.net
      SMTP_USERNAME     sender Gmail / SMTP address
      SMTP_PASSWORD     app-specific password (not your account password)
    Optional:
      SMTP_SERVER       default smtp.gmail.com
      SMTP_PORT         default 587
    """
    target = os.environ.get("SMS_EMAIL_TARGET")
    user   = os.environ.get("SMTP_USERNAME")
    pwd    = os.environ.get("SMTP_PASSWORD")
    if not (target and user and pwd):
        return
    import smtplib
    from email.mime.text import MIMEText

    e = signal.evaluation
    b = e.baseline
    market = f"{b.team or 'Game'} {b.period.value.upper()}"
    body = (
        f"{'🔥 STRONG' if signal.strong else '📈'} MRBET SIGNAL\n"
        f"Market:  {market}\n"
        f"Live Line Entry: {e.live.line} ({e.offered_odds:+d})\n"
        f"Model Edge: {e.edge_pts:+.1f} pts  fair={e.fair_final:.1f}\n"
        f"P({e.side.value})={e.prob*100:.0f}%  EV={e.ev*100:+.1f}%\n"
        f"Suggested Stake: ${e.kelly_stake:.2f}"
    )
    msg = MIMEText(body)
    msg["Subject"] = f"mrbet {e.side.value.upper()} {b.line}"
    msg["From"]    = user
    msg["To"]      = target
    host = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "587"))
    try:
        with smtplib.SMTP(host, port, timeout=10) as s:
            s.ehlo()
            s.starttls()
            s.login(user, pwd)
            s.send_message(msg)
    except Exception as exc:
        print(f"[SMS error] {exc}")


def _discord(title: str, body: str, strong: bool = False) -> None:
    """Post the flagged signal to a Discord channel webhook (phone push via the app).

    Set DISCORD_WEBHOOK_URL in env (.env or GitHub Secrets — never hardcode):
      Discord → Server Settings → Integrations → Webhooks → New Webhook → Copy URL.
    Subscribe to the channel on the Discord mobile app to get a push the moment a
    signal clears every threshold.
    """
    url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not url:
        return
    color = 0xDA3633 if strong else 0x2EA043  # red = STRONG, green = standard flag
    payload = {"embeds": [{"title": title, "url": DASHBOARD_URL,
                           "description": body, "color": color}]}
    try:
        requests.post(url, json=payload, timeout=10)
    except requests.RequestException as exc:  # pragma: no cover - network
        print(f"[discord error] {exc}")


def _slack(title: str, body: str, strong: bool = False) -> None:
    """Post the flagged signal to a Slack incoming webhook (phone push via the app).

    Set SLACK_WEBHOOK_URL in env (.env or GitHub Secrets — never hardcode):
      Slack → Apps → Incoming Webhooks → Add to a channel → Copy the webhook URL.
    """
    url = os.environ.get("SLACK_WEBHOOK_URL")
    if not url:
        return
    color = "#da3633" if strong else "#2ea043"
    payload = {"attachments": [{"color": color, "title": title, "text": body}]}
    try:
        requests.post(url, json=payload, timeout=10)
    except requests.RequestException as exc:  # pragma: no cover - network
        print(f"[slack error] {exc}")


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
