"""Empirical live-line decay — teach the fair how the market prices revealed pace.

Measured from 60 games of in-play Pinnacle trajectories (calibrate_decay.py →
output/decay_surface.json): the market's remaining-total sits at
``ratio × pregame × frac_remaining`` where ratio depends on game progress and
revealed pace. Early it's ~1.0; in mid/late COLD games the market discounts to
0.83-0.94 — the structural bias our RE24 fair carried when it assumed ratio ≈ 1
(night one: fair −1.77 runs vs finals while the market sat at −1.04).

``decay_ratio()`` is pure given a surface; the module ships the measured surface
as defaults and prefers the JSON artifact when present (re-fit as data grows).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from shared_piping.run_expectancy import fraction_remaining

SURFACE_PATH = Path(__file__).resolve().parents[1] / "output" / "decay_surface.json"

# measured 2026-07-02 on 60 games (see harvest_trajectories.py); JSON overrides.
DEFAULT_SURFACE = {
    "early|cold": 0.966, "early|hot": 0.995, "early|normal": 1.017,
    "mid|cold": 0.943, "mid|hot": 0.897, "mid|normal": 0.960,
    "late|cold": 0.828, "late|hot": 0.706, "late|normal": 0.900,
}
PACE_BAND = 1.5          # runs above/below expected-so-far => hot/cold
CLAMP = (0.60, 1.10)


def load_surface(path: Path | str = SURFACE_PATH) -> dict[str, float]:
    p = Path(path)
    if p.exists():
        try:
            raw = json.loads(p.read_text())
            out = {k: (v["median"] if isinstance(v, dict) else float(v))
                   for k, v in raw.items()}
            if out:
                return out
        except (ValueError, KeyError, TypeError):
            pass
    return dict(DEFAULT_SURFACE)


def bucket_of(pregame: float, inning: int, half: str, outs: int,
              runs: int) -> tuple[str, str]:
    """(progress, pace) bucket — MUST match calibrate_decay.py's binning."""
    frac = fraction_remaining(inning, half, outs)
    progress = "early" if frac > 0.66 else ("mid" if frac > 0.33 else "late")
    expected_so_far = pregame * (1 - frac)
    pace = ("cold" if runs < expected_so_far - PACE_BAND else
            "hot" if runs > expected_so_far + PACE_BAND else "normal")
    return progress, pace


def decay_ratio(pregame: float, inning: int, half: str, outs: int, runs: int,
                surface: Optional[dict[str, float]] = None) -> float:
    """Market-calibrated multiplier on the naive remaining total (clamped)."""
    surf = surface if surface is not None else load_surface()
    prog, pace = bucket_of(pregame, inning, half, outs, runs)
    r = surf.get(f"{prog}|{pace}", 1.0)
    return max(CLAMP[0], min(CLAMP[1], float(r)))
