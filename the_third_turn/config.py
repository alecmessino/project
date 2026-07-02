"""Config for The Third Turn — pydantic (validated) like mrbet's config.py.

Revision 3: the single trigger becomes a LIST of independent ``TriggerRule``s so we
capture both TTOP archetypes (weaker arms cliff at the 2nd turn, mid-rotation at the
3rd) plus an opt-in game-script WATCH rule. Rules match ``times_through_order``
EXACTLY so they never overlap. ``EngineSettings`` gains ledger/latency/Discord knobs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field

HERE = Path(__file__).resolve().parent
CONSTRAINTS_PATH = HERE / "output" / "constraints.json"


class TriggerRule(BaseModel):
    """One independent trigger. ``kind='tto'`` = the Time-Through-Order cliff (fires
    ARM + CONFIRM, posts to Discord); ``kind='watch'`` = the experimental low-scoring
    game-script heuristic (console + ledger only, never Discord, off by default)."""

    name: str
    kind: Literal["tto", "watch"] = "tto"
    enabled: bool = True
    # TTO rule params (exact match on the due batter's times-through-order).
    times_through_order: int = 2
    top_of_order_slots: list[int] = Field(default_factory=lambda: [1, 2, 3, 4, 5])
    starter_tier_filter: list[str] = Field(default_factory=lambda: ["Mid", "Back"])
    min_inning: int = 3
    ttop_run_multiplier: float = 1.15
    line_edge_min_runs: Optional[float] = None   # override; else Constraints default
    # WATCH rule params (game-script): fire early when the game is low-scoring.
    watch_max_inning: int = 4
    watch_max_runs: int = 2


def _default_rules() -> list[TriggerRule]:
    """The two validated archetypes (from the 3-season sweep) + a disabled WATCH."""
    return [
        TriggerRule(name="TTO2-Back/Mid", times_through_order=2,
                    top_of_order_slots=[1, 2, 3, 4, 5], starter_tier_filter=["Mid", "Back"],
                    min_inning=3, ttop_run_multiplier=1.15),
        TriggerRule(name="TTO3-Mid/Back", times_through_order=3,
                    top_of_order_slots=[1, 2, 3, 4], starter_tier_filter=["Mid", "Back"],
                    min_inning=5, ttop_run_multiplier=1.15),
        TriggerRule(name="WATCH-low-scoring", kind="watch", enabled=False,
                    starter_tier_filter=["Mid", "Back"], watch_max_inning=4, watch_max_runs=2),
    ]


class Constraints(BaseModel):
    """Global trigger config + the rule list."""

    rules: list[TriggerRule] = Field(default_factory=_default_rules)

    # --- shared line / RE24 params ---
    use_re24: bool = True
    line_edge_min_runs: float = 0.5     # default; a rule may override

    # --- pull risk / bullpen quality (Fix #4) ---
    bullpen_elite_ra9: float = 3.80     # suppress if fielding bullpen RA/9 below this
    require_starter_on_mound: bool = True

    # --- look-ahead / latency buffer (Fix #5) ---
    lookahead_outs: int = 2
    lookahead_slots: list[int] = Field(default_factory=lambda: [8, 9])

    # --- provenance / diagnostics (filled by the backtest) ---
    seasons: list[int] = Field(default_factory=list)
    ra9_vs_true_ra9_r: Optional[float] = None
    top_indicator: Optional[str] = None

    def active_rules(self) -> list[TriggerRule]:
        return [r for r in self.rules if r.enabled]

    def edge_for(self, rule: TriggerRule) -> float:
        return rule.line_edge_min_runs if rule.line_edge_min_runs is not None else self.line_edge_min_runs

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
    # Revision 2 reference tables (written by build_reference.py); missing = graceful.
    bullpen_quality_path: str = str(HERE / "config" / "bullpen_quality.json")
    starter_tiers_path: str = str(HERE / "config" / "starter_tiers.json")
    # Revision 3: ledger, latency, Discord.
    ledger_path: str = str(HERE / "output" / "ledger.jsonl")
    max_data_age_seconds: float = 30.0
    # verify fired alerts against real betable books via The Odds API (1 credit per
    # refresh, 60s cache) — suppresses alerts whose edge dies at the real line, and
    # RESCUES fires the stale scraped feed would silently block (state gates matched
    # but the scrape's line failed). Capped per ET day; raise with a paid key.
    verify_lines: bool = True
    verify_daily_credit_cap: int = 25
    alert_webhook: Optional[str] = None      # overrides $DISCORD_WEBHOOK_URL if set
    discord_ping: Optional[str] = None       # overrides $DISCORD_PING (user id / "everyone")

    def load_bullpen_quality(self) -> dict:
        p = Path(self.bullpen_quality_path)
        return json.loads(p.read_text()) if p.exists() else {}

    def load_starter_tiers(self) -> dict:
        p = Path(self.starter_tiers_path)
        return json.loads(p.read_text()) if p.exists() else {}
