"""Robust fuzzy MLB team-name resolver across MLB Stats API, FanDuel, and Bovada.

Each book spells teams differently — "D-Backs" vs "Arizona Diamondbacks" vs
"ARI", "Athletics" vs "Oakland Athletics" vs "A's". To join a live game state
(MLB API) with odds (FanDuel/Bovada) we need one canonical key per club.

``resolve(name)`` returns the canonical 3-letter key (matching MLB Stats API's
``teamCode``-style abbreviations, e.g. ``ARI``) or ``None`` if nothing matches.
Resolution order: normalize -> exact alias hit -> difflib fuzzy fallback.
"""

from __future__ import annotations

import difflib
import re
from typing import Optional

# canonical key -> set of lowercase aliases (city, nickname, abbreviations, quirks).
# The canonical key itself is always an implicit alias.
_TEAMS: dict[str, set[str]] = {
    "ARI": {"arizona", "diamondbacks", "d-backs", "dbacks", "d backs", "az", "arizona diamondbacks"},
    "ATL": {"atlanta", "braves", "atlanta braves"},
    "BAL": {"baltimore", "orioles", "os", "baltimore orioles"},
    "BOS": {"boston", "red sox", "redsox", "bosox", "boston red sox"},
    "CHC": {"chicago cubs", "cubs", "chi cubs", "chc"},
    "CWS": {"chicago white sox", "white sox", "whitesox", "chi white sox", "cws", "chw", "cha"},
    "CIN": {"cincinnati", "reds", "cincinnati reds"},
    "CLE": {"cleveland", "guardians", "cleveland guardians", "indians"},
    "COL": {"colorado", "rockies", "colorado rockies"},
    "DET": {"detroit", "tigers", "detroit tigers"},
    "HOU": {"houston", "astros", "houston astros"},
    "KC": {"kansas city", "royals", "kansas city royals", "kcr", "kan"},
    "LAA": {"los angeles angels", "angels", "la angels", "anaheim", "laa", "ana"},
    "LAD": {"los angeles dodgers", "dodgers", "la dodgers", "lad"},
    "MIA": {"miami", "marlins", "florida marlins", "miami marlins", "fla"},
    "MIL": {"milwaukee", "brewers", "milwaukee brewers"},
    "MIN": {"minnesota", "twins", "minnesota twins"},
    "NYM": {"new york mets", "mets", "ny mets", "nym"},
    "NYY": {"new york yankees", "yankees", "ny yankees", "nyy"},
    "OAK": {"oakland", "athletics", "a's", "as", "oakland athletics", "ath"},
    "PHI": {"philadelphia", "phillies", "philadelphia phillies"},
    "PIT": {"pittsburgh", "pirates", "bucs", "pittsburgh pirates"},
    "SD": {"san diego", "padres", "san diego padres", "sdp"},
    "SF": {"san francisco", "giants", "san francisco giants", "sfg"},
    "SEA": {"seattle", "mariners", "seattle mariners"},
    "STL": {"st louis", "st. louis", "cardinals", "cards", "st louis cardinals", "sln"},
    "TB": {"tampa bay", "rays", "devil rays", "tampa bay rays", "tbr"},
    "TEX": {"texas", "rangers", "texas rangers"},
    "TOR": {"toronto", "blue jays", "bluejays", "jays", "toronto blue jays"},
    "WSH": {"washington", "nationals", "nats", "washington nationals", "wsn", "was"},
}

# Flattened lookup built once at import: alias -> canonical key.
_ALIAS_TO_KEY: dict[str, str] = {}
for _key, _aliases in _TEAMS.items():
    _ALIAS_TO_KEY[_key.lower()] = _key
    for _a in _aliases:
        _ALIAS_TO_KEY[_a] = _key


def _normalize(name: str) -> str:
    """Lowercase, strip punctuation-ish noise, collapse whitespace."""
    n = (name or "").strip().lower()
    n = n.replace("&", "and")
    # keep apostrophes/hyphens (they distinguish "a's" / "d-backs") but drop the rest
    n = re.sub(r"[^\w'\-\s]", " ", n)
    n = re.sub(r"\s+", " ", n).strip()
    return n


def resolve(name: str, *, cutoff: float = 0.72) -> Optional[str]:
    """Resolve a fuzzy team name to its canonical key, or ``None`` if unresolved.

    1. Exact alias match on the normalized string.
    2. Nickname/word match — if any alias appears as a whole token in the input
       (handles "Over 8.5 - Arizona Diamondbacks" style descriptors).
    3. ``difflib`` closest-alias fallback above ``cutoff``.
    """
    if not name:
        return None
    norm = _normalize(name)
    if not norm:
        return None

    # 1. exact
    if norm in _ALIAS_TO_KEY:
        return _ALIAS_TO_KEY[norm]

    # 2. token / substring containment — longest alias first so "white sox" wins
    #    over "sox" and "red sox" isn't misread.
    for alias in sorted(_ALIAS_TO_KEY, key=len, reverse=True):
        if len(alias) < 3:
            continue
        if re.search(rf"(?<![\w']){re.escape(alias)}(?![\w'])", norm):
            return _ALIAS_TO_KEY[alias]

    # 3. fuzzy fallback
    match = difflib.get_close_matches(norm, list(_ALIAS_TO_KEY), n=1, cutoff=cutoff)
    if match:
        return _ALIAS_TO_KEY[match[0]]
    return None


def canonical_keys() -> list[str]:
    """All 30 canonical team keys (sorted)."""
    return sorted(_TEAMS)
