"""Verify notification secrets are present and fire a real test alert.

Run inside a GitHub Actions job where the secrets are injected as env vars (see
.github/workflows/notify_test.yml). It NEVER prints a secret value — only whether
each is set and its length — then sends one test "strong" alert through every
channel whose secret is present, using the exact production notify functions.
"""

from __future__ import annotations

import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mrbet.models import (   # noqa: E402
    Baseline, Evaluation, GameState, MarketLine, MarketType, Period, Side, Signal,
)
from mrbet.notify import (   # noqa: E402
    _discord, _discord_fields, _push, _slack, _sms_gateway, format_signal,
)


def _mask(name: str) -> bool:
    """Print presence (set + length only, never the value). Returns True if set."""
    v = os.environ.get(name)
    if v:
        print(f"  ✓ {name:<22} set (len {len(v)})")
        return True
    print(f"  ✗ {name:<22} unset")
    return False


def main() -> int:
    print("=== Notification secret presence (values never shown) ===")
    discord = _mask("DISCORD_WEBHOOK_URL")
    _mask("DISCORD_PING")
    ntfy = _mask("NTFY_TOPIC")
    _mask("NTFY_SERVER")
    pover = _mask("PUSHOVER_TOKEN") & _mask("PUSHOVER_USER")
    slack = _mask("SLACK_WEBHOOK_URL")
    sms = _mask("SMS_EMAIL_TARGET") & _mask("SMTP_USERNAME") & _mask("SMTP_PASSWORD")
    _mask("ODDS_API_KEY")   # not a channel, but useful to confirm it's wired

    # A representative "strong" signal so the alert looks like the real thing.
    state = GameState(Period.FULL, 9.0, 39.0, 9, 7)
    base = Baseline(MarketType.GAME_TOTAL, Period.FULL, 218.0, -110, -110)
    live = MarketLine(MarketType.GAME_TOTAL, Period.FULL, 205.0, -110, -110)
    ev = Evaluation(base, live, state, Side.OVER, 213.5, -0.060, 8.5, 0.61, 0.524, 0.05, 4.25)
    sig = Signal(ev, strong=True, reasons=["notify-test"])
    title, body = format_signal(sig)
    title = "🧪 TEST — " + title
    body = "This is a mrbet notification test (not a real signal).\n" + body

    print("\n=== Sending test alert to each configured channel ===")
    sent = []
    if discord:
        _discord(title, body, strong=True, fields=_discord_fields(sig))
        sent.append("Discord")
    if pover or ntfy:
        _push(title, body, strong=True)
        sent.append("Pushover" if pover else "ntfy")
    if slack:
        _slack(title, body, strong=True)
        sent.append("Slack")
    if sms:
        _sms_gateway(sig)
        sent.append("SMS")

    if sent:
        print(f"  → attempted: {', '.join(sent)}  (check your phone/desktop)")
    else:
        print("  → NO channels configured — set DISCORD_WEBHOOK_URL or NTFY_TOPIC in repo Secrets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
