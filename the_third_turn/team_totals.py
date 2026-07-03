#!/usr/bin/env python3
"""Pinnacle per-team implied run distribution — the team-total signal, free & sharp.

Retail books don't expose live team-total O/U lines, but Pinnacle prices a per-team
"Exact Total Runs" market (a 9-way moneyline over run buckets 0,1,…,7,8+). De-vigged,
that IS a full probability distribution — richer than a single O/U hook: it yields the
implied team mean (the "true line"), spread, and skew. If the TTOP velocity cliff isn't
already baked into this sharp distribution, that's structural alpha.

    from team_totals import fetch_team_totals   # daemon capture
    python the_third_turn/team_totals.py         # one-shot dump of current team lines
"""

from __future__ import annotations

import asyncio
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import aiohttp  # noqa: E402

from shared_piping.headers import rotating_headers  # noqa: E402
from shared_piping.team_map import resolve  # noqa: E402
from sources.pinnacle import MARKETS_URL, MATCHUPS_URL  # noqa: E402

REFERER = "https://www.pinnacle.com/"
_SUFFIX = re.compile(r"\s+Exact Total Runs$", re.I)
OPEN_BUCKET_CENTROID = 8.5   # centroid assumed for the open "8+" bucket (approx)


@dataclass
class TeamTotal:
    game_key: str
    team: str
    implied_line: float          # de-vigged implied mean runs (the sharp "true line")
    sd: float
    skew: float
    live: bool
    probs: dict = field(default_factory=dict)
    ts: float = 0.0


def _american_to_prob(american: float) -> float:
    dec = 1.0 + (american / 100.0 if american > 0 else 100.0 / abs(american))
    return 1.0 / dec


def implied_distribution(american_by_bucket: dict, open_centroid: float = OPEN_BUCKET_CENTROID) -> dict:
    """De-vig a bucket→American map into a run distribution: mean, sd, skew, probs.

    Keys are run counts ('0'..'7') or an open bucket ('8+'). Pure — unit-tested.
    """
    raw = {k: _american_to_prob(a) for k, a in american_by_bucket.items() if a is not None}
    tot = sum(raw.values())
    if not tot:
        return {}
    p = {k: v / tot for k, v in raw.items()}                     # remove the overround

    def val(k: str) -> float:
        return open_centroid if k.endswith("+") else float(k)

    mean = sum(p[k] * val(k) for k in p)
    var = sum(p[k] * (val(k) - mean) ** 2 for k in p)
    sd = var ** 0.5
    skew = sum(p[k] * ((val(k) - mean) / sd) ** 3 for k in p) if sd else 0.0
    return {"mean": round(mean, 3), "sd": round(sd, 3), "skew": round(skew, 3),
            "probs": {k: round(p[k], 4) for k in sorted(p, key=val)}}


def parse_team_totals(matchups: list, markets: list, ts: float) -> list[TeamTotal]:
    games = {m["id"]: m for m in matchups if m.get("type") == "matchup" and not m.get("parentId")}
    mkt_by_mu: dict = {}
    for m in markets:
        mkt_by_mu.setdefault(m.get("matchupId"), []).append(m)

    out: list[TeamTotal] = []
    for m in matchups:
        sp = (m.get("special") or {}).get("description") or ""
        if not sp.lower().endswith("exact total runs") or m.get("parentId") not in games:
            continue
        if any(w in sp.lower() for w in ("half", "range", "odd", "even", "1st", "inning")):
            continue
        team_str = _SUFFIX.sub("", sp).strip()
        team = resolve(team_str)
        g = games[m["parentId"]]
        keys = {p.get("name"): resolve(p.get("name", "")) for p in g.get("participants", [])}
        away = next((v for k, v in keys.items() if p_align(g, k) == "away"), None)
        home = next((v for k, v in keys.items() if p_align(g, k) == "home"), None)
        if not team or team not in (away, home) or not away or not home:
            continue
        bucket_of = {p["id"]: p.get("name") for p in m.get("participants", [])}
        mkts = [mm for mm in mkt_by_mu.get(m["id"], []) if mm.get("type") == "moneyline"]
        if not mkts:
            continue
        prices = {bucket_of.get(pr.get("participantId")): pr.get("price")
                  for pr in mkts[0].get("prices", []) if pr.get("participantId") in bucket_of}
        dist = implied_distribution({k: v for k, v in prices.items() if k})
        if not dist:
            continue
        out.append(TeamTotal(game_key=f"{away}@{home}", team=team,
                             implied_line=dist["mean"], sd=dist["sd"], skew=dist["skew"],
                             live=bool(m.get("isLive") or g.get("isLive")), probs=dist["probs"], ts=ts))
    return out


def p_align(game: dict, name: str) -> str:
    for p in game.get("participants", []):
        if p.get("name") == name:
            return p.get("alignment", "")
    return ""


async def fetch_team_totals(session: aiohttp.ClientSession) -> list[TeamTotal]:
    """Pull Pinnacle matchups+markets and derive per-team implied run distributions."""
    h = rotating_headers(referer=REFERER)
    to = aiohttp.ClientTimeout(total=15)
    ts = time.time()
    async with session.get(MATCHUPS_URL, headers=h, timeout=to) as r:
        matchups = await r.json(content_type=None)
    async with session.get(MARKETS_URL, headers=h, timeout=to) as r:
        markets = await r.json(content_type=None)
    return parse_team_totals(matchups, markets, ts)


async def _main() -> int:
    async with aiohttp.ClientSession() as s:
        tts = await fetch_team_totals(s)
    print(f"{len(tts)} team totals derived from Pinnacle:")
    for t in sorted(tts, key=lambda x: x.game_key)[:24]:
        print(f"  {t.game_key:>10} {t.team:>5}  line={t.implied_line:5.2f}  σ={t.sd:.2f}  "
              f"skew={t.skew:+.2f}  {'LIVE' if t.live else 'pre'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
