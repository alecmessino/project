"""Pure run-expectancy model (Fix #3) — no I/O, fully unit-tested.

Replaces the naive ``drop < 1.5`` trigger with a live *expected final total* anchor
so the engine compares the market's live Over against a run-environment estimate that
respects base/out state, innings remaining, the park, and the TTOP bump.

Construction (interpretable, deliberately lightweight):

    base_remaining = pregame_total * fraction_of_game_remaining      # level, park-baked
    re_excess      = RE24(bases, outs) - RE24(empty, outs)           # situational premium
    ttop_bump      = (ttop_mult - 1) * RE24(bases, outs)  if in_window else 0
    expected_final = runs_so_far + base_remaining + park * (re_excess + ttop_bump)

The *level* comes from the book's pregame closing total (already park-inclusive), so
the park factor only amplifies the **marginal** situational/TTOP runs — it is not
double-applied to the base level. Fire the Over when the live total sits below
``expected_final`` by at least a margin (see live_engine).

RE24 = canonical run-expectancy-by-base/out matrix (Tango et al.); park factors are
static published-ish run factors. Both are constants to tune against logged data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# RE24: expected runs scored to the end of the half-inning, keyed by
# (on_first, on_second, on_third, outs). Canonical league-average values.
RE24: dict[tuple[bool, bool, bool, int], float] = {
    (False, False, False, 0): 0.481, (False, False, False, 1): 0.254, (False, False, False, 2): 0.098,
    (True,  False, False, 0): 0.859, (True,  False, False, 1): 0.509, (True,  False, False, 2): 0.224,
    (False, True,  False, 0): 1.100, (False, True,  False, 1): 0.664, (False, True,  False, 2): 0.319,
    (False, False, True,  0): 1.350, (False, False, True,  1): 0.950, (False, False, True,  2): 0.353,
    (True,  True,  False, 0): 1.437, (True,  True,  False, 1): 0.884, (True,  True,  False, 2): 0.429,
    (True,  False, True,  0): 1.784, (True,  False, True,  1): 1.130, (True,  False, True,  2): 0.478,
    (False, True,  True,  0): 1.964, (False, True,  True,  1): 1.376, (False, True,  True,  2): 0.580,
    (True,  True,  True,  0): 2.292, (True,  True,  True,  1): 1.541, (True,  True,  True,  2): 0.752,
}

# Static run park factors (1.00 = neutral). Approximate, tunable against logged data.
PARK_FACTORS: dict[str, float] = {
    "COL": 1.20, "CIN": 1.08, "BOS": 1.06, "KC": 1.05, "BAL": 1.04, "TEX": 1.04,
    "PHI": 1.03, "CWS": 1.03, "DET": 1.02, "LAA": 1.02, "TOR": 1.02, "MIN": 1.01,
    "HOU": 1.01, "WSH": 1.01, "ATL": 1.00, "NYY": 1.00, "STL": 1.00, "PIT": 1.00,
    "MIL": 1.00, "CHC": 1.00, "ARI": 1.02, "SD": 0.98, "NYM": 0.98, "LAD": 0.98,
    "CLE": 0.98, "TB": 0.97, "MIA": 0.97, "OAK": 0.96, "SF": 0.95, "SEA": 0.94,
}
NEUTRAL_PARK = 1.00


def re24(on_first: bool, on_second: bool, on_third: bool, outs: int) -> float:
    """Run expectancy for a base/out state; clamps outs to [0, 2]."""
    outs = max(0, min(2, int(outs)))
    return RE24[(bool(on_first), bool(on_second), bool(on_third), outs)]


def park_factor(home_key: Optional[str]) -> float:
    return PARK_FACTORS.get((home_key or "").upper(), NEUTRAL_PARK)


def fraction_remaining(inning: int, half: str, outs: int) -> float:
    """Fraction of the 9-inning game still to be played (clamped to [0, 1]).

    A half-inning is 3 outs; a full inning is 6 outs = 1/9 of regulation. Extra
    innings clamp to 0 remaining (the pregame total no longer anchors them well).
    """
    half_offset = 0.5 if str(half).lower().startswith("bottom") else 0.0
    innings_elapsed = (inning - 1) + half_offset + (max(0, min(3, outs)) / 6.0)
    return max(0.0, min(1.0, 1.0 - innings_elapsed / 9.0))


@dataclass
class RunEnvAnchor:
    expected_final: float
    base_remaining: float
    situational: float      # park * (re_excess + ttop_bump)
    frac_remaining: float
    park: float


def expected_final_total(
    pregame_total: float,
    runs_so_far: int,
    inning: int,
    half: str,
    outs: int,
    on_first: bool,
    on_second: bool,
    on_third: bool,
    home_key: Optional[str],
    ttop_mult: float = 1.0,
    in_window: bool = False,
) -> RunEnvAnchor:
    """Expected full-game total (both teams) given live state — the Over anchor."""
    frac = fraction_remaining(inning, half, outs)
    base_remaining = pregame_total * frac
    re_here = re24(on_first, on_second, on_third, outs)
    re_excess = re_here - re24(False, False, False, outs)
    ttop_bump = (ttop_mult - 1.0) * re_here if in_window else 0.0
    pk = park_factor(home_key)
    situational = pk * (re_excess + ttop_bump)
    expected = runs_so_far + base_remaining + situational
    return RunEnvAnchor(expected_final=expected, base_remaining=base_remaining,
                        situational=situational, frac_remaining=frac, park=pk)
