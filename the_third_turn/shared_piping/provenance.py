"""Feed-provenance probe: does a book tell us when IT generated the price?

Paper 2's binding assumption (A4) needs the publication stage pinned by something other
than our own poll clock. Two candidates exist for an outside observer:

  1. the HTTP ``Date`` response header, which is the server's clock at response generation.
     This bounds network transport but does NOT separate the bookmaker's pricing decision
     from its feed's publication.
  2. a timestamp carried inside the payload (``lastUpdated``, ``updatedAt``, ``marketTime``
     and friends). If one exists and tracks price revisions, it pins the publication stage
     directly and A4 becomes testable.

We do not guess field names. ``scan_timestamps`` walks the decoded payload and reports every
key that either *looks* like a time field or *holds* a plausible epoch/ISO value, so a field
we failed to anticipate cannot be missed. A run that finds nothing is itself the evidence for
the paper's Outcome C, which is why the probe records absence as explicitly as presence.

Everything here is best-effort and swallows its own exceptions: the collector must never fail
because a diagnostic did.
"""

from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Short abbreviations must match a WHOLE token: a bare substring test flags "numMarkets"
# and "hasAttachments" on the "ts" inside them, which is exactly how the first run of this
# probe polluted its own candidate list. Longer words are distinctive enough to match anywhere.
_EXACT_TOKENS = {"ts", "time", "times", "date", "dates", "timestamp", "timestamps",
                 "epoch", "millis", "asof"}
_SUBSTR_WORDS = ("timestamp", "updated", "modified", "created", "generated", "published",
                 "lastchange", "refreshed", "revised", "asof")
_TOKEN_SPLIT = re.compile(r"[^A-Za-z0-9]+|(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")


def key_is_timeish(key: str) -> bool:
    """True when a key NAME suggests a time, without firing on incidental substrings."""
    k = str(key)
    toks = [x.lower() for x in _TOKEN_SPLIT.split(k) if x]
    if any(tk in _EXACT_TOKENS for tk in toks):
        return True
    kl = k.lower()
    return any(w in kl for w in _SUBSTR_WORDS)
# Epoch seconds / milliseconds within a plausible window (2020-01-01 .. 2035-01-01).
_EPOCH_S = (1577836800, 2051222400)
_EPOCH_MS = (_EPOCH_S[0] * 1000, _EPOCH_S[1] * 1000)
_ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}")

MAX_HITS = 40          # cap the report; a schema does not need exhaustive enumeration
MAX_DEPTH = 12


def _value_is_timeish(v: Any) -> Optional[str]:
    """Return a tag describing how the value reads as a time, or None."""
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        if _EPOCH_S[0] <= v <= _EPOCH_S[1]:
            return "epoch_s"
        if _EPOCH_MS[0] <= v <= _EPOCH_MS[1]:
            return "epoch_ms"
        return None
    if isinstance(v, str):
        if _ISO_RE.match(v):
            return "iso8601"
        if v.isdigit():
            n = int(v)
            if _EPOCH_S[0] <= n <= _EPOCH_S[1]:
                return "epoch_s_str"
            if _EPOCH_MS[0] <= n <= _EPOCH_MS[1]:
                return "epoch_ms_str"
    return None


def scan_timestamps(payload: Any) -> list[dict]:
    """Walk a decoded JSON payload and report every plausible time field.

    Returns a list of ``{path, key, kind, sample}``. ``kind`` records *why* the field was
    flagged: by name, by value, or both. Paths use ``[]`` for list elements so repeated
    array members collapse to one reported path.
    """
    hits: list[dict] = []
    seen: set[str] = set()

    def walk(node: Any, path: str, depth: int) -> None:
        if len(hits) >= MAX_HITS or depth > MAX_DEPTH:
            return
        if isinstance(node, dict):
            for k, v in node.items():
                p = f"{path}.{k}" if path else str(k)
                by_name = key_is_timeish(k)
                by_value = _value_is_timeish(v)
                if (by_name or by_value) and not isinstance(v, (dict, list)):
                    if p not in seen:
                        seen.add(p)
                        hits.append({
                            "path": p, "key": str(k),
                            "kind": ("name+value" if by_name and by_value
                                     else "name" if by_name else "value"),
                            "value_kind": by_value,
                            "sample": v if isinstance(v, (int, float)) else str(v)[:40],
                        })
                walk(v, p, depth + 1)
        elif isinstance(node, list):
            for item in node[:3]:          # a few members suffice to learn the shape
                walk(item, f"{path}[]", depth + 1)

    try:
        walk(payload, "", 0)
    except Exception:  # noqa: BLE001 - a diagnostic must never break collection
        pass
    return hits


def server_date(headers: Any) -> Optional[float]:
    """Parse the HTTP ``Date`` response header into epoch seconds."""
    try:
        raw = headers.get("Date") or headers.get("date")
        if not raw:
            return None
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except Exception:  # noqa: BLE001
        return None


def capture(book: str, headers: Any, payload: Any, recv_wall: Optional[float] = None,
            quotes: Any = None) -> dict:
    """Build one provenance record for a single fetch.

    ``quotes`` (the parsed result) is used only to record which market states this fetch
    actually observed. Coverage, not volume, is what licenses a claim about the schema:
    a payload shape we never sampled cannot be ruled out by any number of fetches of the
    shapes we did.
    """
    recv = time.time() if recv_wall is None else recv_wall
    sd = server_date(headers)
    n_q = n_live = 0
    try:
        if quotes:
            n_q = len(quotes)
            n_live = sum(1 for q in quotes if getattr(q, "live_game", False))
    except Exception:  # noqa: BLE001
        pass
    return {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "book": book,
        "n_quotes": n_q,
        "n_live": n_live,
        "state": ("live" if n_live else ("pregame" if n_q else "empty")),
        "server_date": sd,
        # Positive means the server's clock reads behind our receive time. With `Date`
        # granularity of one second this bounds transport only coarsely, which is the point:
        # it is a bound, not an estimate.
        "recv_minus_server_s": (round(recv - sd, 3) if sd is not None else None),
        "payload_time_fields": scan_timestamps(payload),
    }


def record(path: Path, rec: dict) -> None:
    """Append one record. Never raises."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a") as fh:
            fh.write(json.dumps(rec) + "\n")
    except Exception:  # noqa: BLE001
        pass
