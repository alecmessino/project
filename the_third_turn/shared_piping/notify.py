"""Async Discord webhook alerts for validated TTOP signals (Revision 3).

Mirrors the embed pattern in ``src/mrbet/notify.py`` (env ``DISCORD_WEBHOOK_URL``,
``DISCORD_PING`` for strong alerts) but async via aiohttp, since the engine loop is
async. ``build_embed`` is a PURE payload builder (unit-tested without network); the
label helpers are shared with the ledger. Only CONFIRM/ARM post here — never WATCH.

The trigger object is read via duck typing (attributes only) to avoid importing
``live_engine`` (which imports this module).
"""

from __future__ import annotations

import os
from typing import Optional

import aiohttp

CONFIRM_COLOR = 0xE02B2B   # red
ARM_COLOR = 0xF1C40F       # gold


def pull_risk_label(bullpen_ra9: Optional[float], elite_ra9: float) -> str:
    """Pull-risk from the fielding bullpen's RA/9 (an elite pen ⇒ quicker hook)."""
    if bullpen_ra9 is None:
        return "UNKNOWN (bullpen quality not loaded)"
    if bullpen_ra9 < elite_ra9:
        return f"HIGH — elite pen ({bullpen_ra9:.2f} RA/9), quick-hook risk"
    if bullpen_ra9 < elite_ra9 + 1.0:
        return f"MED — pen {bullpen_ra9:.2f} RA/9 near elite"
    return f"LOW — weak pen ({bullpen_ra9:.2f} RA/9), unlikely to bail out the Over"


def game_script_tag(away_score: int, home_score: int) -> str:
    """Game-script context — a blowout changes manager behavior vs a tie."""
    diff = abs(away_score - home_score)
    if diff == 0:
        return "tie"
    if diff == 1:
        return "one-run"
    if diff <= 3:
        return "multi-run"
    return "blowout (script risk — coasting / position players)"


def data_age_label(data_age: Optional[float], max_age: float) -> str:
    if data_age is None:
        return "unknown"
    flag = "  ⚠ STALE" if data_age > max_age else ""
    return f"{data_age:.0f}s old{flag}"


_BOOK_ABBR = {"draftkings": "DK", "fanduel": "FD", "betmgm": "MGM", "bovada": "BOV",
              "betrivers": "BR", "mybookieag": "MB", "caesars": "CZR"}


def build_embed(trigger, *, bullpen_elite_ra9: float, max_data_age: float,
                verified: Optional[dict] = None) -> dict:
    """Pure Discord embed payload for a fired CONFIRM/ARM trigger."""
    s = trigger.state
    is_arm = trigger.trigger_type == "ARM"
    emoji = "🟡" if is_arm else "🔴"
    fields = [
        {"name": "Why (rule)", "inline": False,
         "value": f"**{trigger.rule_name}** · {trigger.trigger_type} — "
                  f"{s.starter_tier} starter, {s.times_through_order}× through, "
                  f"slot {s.batting_slot_due} due, {s.outs} out"},
        {"name": "Gap (Over value)", "inline": True,
         "value": f"```Live {trigger.live_total} / Fair {trigger.anchor.expected_final:.1f}"
                  f"\n→ +{trigger.edge:.1f} runs```"},
        {"name": "Pull Risk", "inline": True,
         "value": pull_risk_label(trigger.bullpen_ra9, bullpen_elite_ra9)},
        {"name": "Score", "inline": True,
         "value": f"```{s.away} {s.away_score} – {s.home_score} {s.home}```"
                  f"\n{game_script_tag(s.away_score, s.home_score)}"},
        {"name": "Pitcher", "inline": True,
         "value": f"{s.pitcher_name} ({s.starter_tier}) · {s.pitch_count} pitches"},
        {"name": "Latency", "inline": True,
         "value": f"data {data_age_label(s.data_age_seconds, max_data_age)}"},
    ]
    if verified:
        books = " · ".join(f"{_BOOK_ABBR.get(k, k[:4])} {v}"
                           for k, v in sorted(verified["books"].items())[:5])
        v_edge = trigger.anchor.expected_final - verified["median"]
        fields.append({"name": "Betable line (verified)", "inline": False,
                       "value": f"```median {verified['median']} | {books}```"
                                f"edge vs fair: **{v_edge:+.1f}**"})
    return {
        "title": f"{emoji} {trigger.trigger_type} · {trigger.rule_name} · {s.away} @ {s.home}",
        "description": f"Inning {s.inning} {s.half} · {trigger.quote.book} · **hammer the OVER**",
        "color": ARM_COLOR if is_arm else CONFIRM_COLOR,
        "fields": fields,
        "footer": {"text": "The Third Turn · TTOP live signal"},
    }


class DiscordNotifier:
    """Posts embeds to a Discord webhook. No-op if no URL is configured."""

    def __init__(self, webhook_url: Optional[str] = None, ping: Optional[str] = None,
                 bullpen_elite_ra9: float = 3.80, max_data_age: float = 30.0):
        self.url = webhook_url or os.environ.get("DISCORD_WEBHOOK_URL")
        self.ping = ping or os.environ.get("DISCORD_PING")
        self.bullpen_elite_ra9 = bullpen_elite_ra9
        self.max_data_age = max_data_age

    @property
    def enabled(self) -> bool:
        return bool(self.url)

    def _payload(self, trigger, verified: Optional[dict] = None) -> dict:
        embed = build_embed(trigger, bullpen_elite_ra9=self.bullpen_elite_ra9,
                             max_data_age=self.max_data_age, verified=verified)
        payload = {"embeds": [embed]}
        # ping only on the strong CONFIRM alerts, mirroring mrbet's behavior.
        if trigger.trigger_type == "CONFIRM" and self.ping:
            p = self.ping.strip().lstrip("@")
            if p.isdigit():
                payload["content"] = f"<@{p}> 🔴 **THIRD TURN** — {trigger.rule_name}"
                payload["allowed_mentions"] = {"users": [p]}
            elif p.lower() == "everyone":
                payload["content"] = "@everyone 🔴 **THIRD TURN**"
                payload["allowed_mentions"] = {"parse": ["everyone"]}
        return payload

    async def post(self, session: aiohttp.ClientSession, trigger,
                   verified: Optional[dict] = None) -> bool:
        """POST the embed; returns True on success. Never raises past here."""
        if not self.enabled:
            return False
        try:
            async with session.post(self.url, json=self._payload(trigger, verified),
                                    timeout=aiohttp.ClientTimeout(total=10)) as resp:
                return resp.status < 300
        except Exception as exc:  # noqa: BLE001 — a webhook failure must not kill the loop
            print(f"[discord error] {type(exc).__name__}: {exc}")
            return False
