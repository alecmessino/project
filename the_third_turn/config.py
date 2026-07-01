"""Config for The Third Turn — pydantic (validated) like mrbet's config.py.

Two objects:
  * ``Constraints`` — the backtested trigger parameters. Loaded from
    ``output/constraints.json`` (written by ``backtest_thesis.py``). If that file
    is missing, safe conservative defaults are used and the engine logs a warning:
    the engine must never crash just because the backtest hasn't run yet.
  * ``EngineSettings`` — runtime knobs (poll interval, FanDuel state, book toggles,
    reference-data paths).

Revision 2: the pitch-count gate is gone (survivorship bias); the line trigger is
RE24-based (``line_edge_min_runs`` + ``ttop_run_multiplier``); pull-risk and
look-ahead parameters are added.
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

    Defaults are conservative placeholders; the backtest overwrites them with
    empirically-fit values.
    """

    # --- arrival of the 3rd turn through the top of the order (no PC gate) ---
    min_inning: int = 5
    top_of_order_slots: list[int] = Field(default_factory=lambda: [1, 2, 3, 4])
    times_through_order: int = 3

    # --- RE24 line trigger (Fix #3) ---
    use_re24: bool = True
    line_edge_min_runs: float = 0.5     # fire when live_total < expected_final - this
    ttop_run_multiplier: float = 1.15   # in-window scoring bump (fit by backtest)

    # --- pull risk / bullpen quality (Fix #4) ---
    bullpen_elite_ra9: float = 3.80     # suppress if fielding bullpen RA/9 below this
    require_starter_on_mound: bool = True

    # --- look-ahead / latency buffer (Fix #5) ---
    lookahead_outs: int = 2
    lookahead_slots: list[int] = Field(default_factory=lambda: [8, 9])

    # --- starter tier (Fix #1) — never fire on aces (they have the arsenal to
    # neutralize the TTOP). Default excludes Ace; the backtest may narrow further. ---
    starter_tier_filter: list[str] = Field(default_factory=lambda: ["Mid", "Back"])

    # --- informational (not a gate) ---
    pitch_count_reference: Optional[int] = None

    # --- provenance / diagnostics (filled by the backtest) ---
    expected_ra9_lift: Optional[float] = None
    expected_runs_per_pa_lift: Optional[float] = None
    expected_whip_lift: Optional[float] = None   # secondary diagnostic only
    seasons: list[int] = Field(default_factory=list)
    sample_bf: Optional[int] = None
    ra9_vs_true_ra9_r: Optional[float] = None
    top_indicator: Optional[str] = None          # best split from the sweep

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
    alert_webhook: Optional[str] = None
    # Revision 2 reference tables (written by build_reference.py); missing = graceful.
    bullpen_quality_path: str = str(HERE / "config" / "bullpen_quality.json")
    starter_tiers_path: str = str(HERE / "config" / "starter_tiers.json")

    def load_bullpen_quality(self) -> dict:
        p = Path(self.bullpen_quality_path)
        return json.loads(p.read_text()) if p.exists() else {}

    def load_starter_tiers(self) -> dict:
        p = Path(self.starter_tiers_path)
        return json.loads(p.read_text()) if p.exists() else {}
