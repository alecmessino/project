"""Rotating browser-like HTTP headers to avoid trivial User-Agent bot filters.

Undocumented public sportsbook feeds (Bovada, FanDuel, ...) reject the default
``aiohttp``/``python-requests`` User-Agent, so every request goes out looking like
a real desktop browser. We rotate across a small pool so a run doesn't hammer a
book with one identical fingerprint.

IMPORTANT — what this does NOT do: UA rotation only defeats *header*-based
filtering. It cannot get past an **IP-level** block (e.g. DraftKings' Akamai edge
returns 403 to this datacenter IP no matter the User-Agent). For those you need a
residential IP / proxy; rotating headers is not a workaround.
"""

from __future__ import annotations

import itertools
from typing import Optional

# A small pool of realistic, current-ish desktop browser User-Agents. Kept short
# on purpose — enough to vary the fingerprint, not so many that it looks synthetic.
USER_AGENTS = [
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
     "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
    ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
     "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"),
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
     "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0"),
    ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) "
     "Gecko/20100101 Firefox/125.0"),
    ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
     "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
]

BASE_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}


class HeaderRotator:
    """Round-robins through :data:`USER_AGENTS`, returning full header dicts.

    Deterministic (round-robin, not random) so behaviour is reproducible in tests
    and logs — ``Date.now``/``random`` are intentionally avoided.
    """

    def __init__(self, user_agents: Optional[list[str]] = None) -> None:
        self._agents = list(user_agents or USER_AGENTS)
        self._cycle = itertools.cycle(self._agents)

    def random(self, *, referer: Optional[str] = None) -> dict[str, str]:
        """Return the next header dict (name kept as ``random`` per the plan API)."""
        headers = dict(BASE_HEADERS)
        headers["User-Agent"] = next(self._cycle)
        if referer:
            headers["Referer"] = referer
        return headers

    # Explicit alias — clearer intent at call sites that want the round-robin.
    next = random


# Module-level default rotator for callers that don't want to hold their own.
_DEFAULT = HeaderRotator()


def rotating_headers(referer: Optional[str] = None) -> dict[str, str]:
    """Convenience: one rotated header dict from the shared default rotator."""
    return _DEFAULT.random(referer=referer)
