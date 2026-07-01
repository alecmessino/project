"""Config for The Third Turn — pydantic (validated) like mrbet's config.py.

Two objects:
  * ``Constraints`` — the backtested trigger parameters. Loaded from
    ``output/constraints.json`` (written by ``backtest_thesis.py``). If that file
    is missing, safe conservative defaults are used and the engine logs a warning:
    the engine must never crash just because the backtest hasn't run yet.
  * ``EngineSettings`` — runtime knobs (poll interval, FanDuel state, book toggles).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

HERE = Path(__file__).resolve().parent
CONSTRAINTS_PATH = HERE / "output" / "constraints.json"


class Constraints(BaseModel):
    """Trigger parameters — the live analogue of mrbet's threshold settings.

    Defaults are deliberately conservative placeholders; the backtest overwrites
    them with empirically-fit values. ``line_drop_max_runs`` encodes the market
    condition: fire only while the live total is still within this many runs of the
    pregame total (i.e. the Over hasn't already been faded away).
    """

    min_inning: int = 6
    top_of_order_slots: list[int] = Field(default_factory=lambda: [1, 2, 3, 4])
    times_through_order: int = 3
    pitch_count_threshold: int = 90
    line_drop_max_runs: float = 1.5
    # provenance / diagnostics (filled by the backtest, optional at runtime)
    expected_whip_lift: Optional[float] = None
    expected_ra9_lift: Optional[float] = None
    seasons: list[int] = Field(default_factory=list)
    sample_bf: Optional[int] = None
    ra9_to_era_r: Optional[float] = None

    @classmethod
    def load(cls, path: Path | str = CONSTRAINTS_PATH) -> tuple["Constraints", bool]:
        """Return ``(constraints, from_file)``. Falls back to defaults if absent."""
        p = Path(path)
        if p.exists():
            return cls.model_validate_json(p.read_text()), True
        return cls(), False

    def save(self, path: Path | str = CONSTRAINTS_PATH) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.model_dump(), indent=2))


class EngineSettings(BaseModel):
    poll_interval_seconds: float = 30.0
    fanduel_state: str = "nj"
    use_bovada: bool = True
    use_fanduel: bool = True
    use_pinnacle_fallback: bool = True
    # optional webhook for alerts (ntfy.sh / Discord / Slack style); stdout always on.
    alert_webhook: Optional[str] = None
