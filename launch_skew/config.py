"""Configuration models for the Launch Skew Monitor.

All thresholds/params live in the project's config YAML — see
`config/launch_skew.yaml`.  This module defines the pydantic schema that
validates it, following the same convention used by the sibling projects
(mrbet `config.py`, drift config).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field


class UniverseSettings(BaseModel):
    min_market_cap: float = 1_000_000
    max_market_cap: float = 50_000_000
    min_liquidity_ratio: float = 0.10
    include_demo_seeds: bool = True


class SourceSettings(BaseModel):
    dune_query_url: str = ""
    dune_api_key: str = ""
    messari_base_url: str = "https://data.messari.io/api/v1"
    messari_api_key: str = ""
    coingecko_base_url: str = "https://api.coingecko.com/api/v3"


class ModuleASettings(BaseModel):
    """Day-1 Liquidity Filter thresholds."""
    turnover_sweet_min: float = 0.30
    turnover_sweet_max: float = 0.60
    turnover_wash_threshold: float = 1.00
    min_dev_active_days: int = 3
    holder_concentration_warn_pct: float = 70.0
    min_protocol_revenue_24h: float = 10_000


class ModuleBSettings(BaseModel):
    """Vesting Wall thresholds."""
    pressure_threshold: float = 2.0
    cliff_warning_days: int = 12
    dilution_warn_pct: float = 0.20
    # Emission-to-Revenue ratio: unlocks_30d_usd / daily_protocol_revenue
    # >50x = dangerous (unlocks dwarf real yield)
    emission_to_revenue_warn: float = 50.0


class ModuleCSettings(BaseModel):
    """Adoption Curve thresholds."""
    fit_window_days: int = 30
    residual_threshold: float = 1.0
    min_active_addresses: int = 100


class StrongThreshold(BaseModel):
    pressure_below: float = 1.0


class SignalGateSettings(BaseModel):
    """Conjunctive trigger gate — all modules must pass for a flag."""
    require_module_a_pass: bool = True
    require_module_b_pass: bool = True
    require_module_c_pass: bool = True
    strong_threshold: StrongThreshold = Field(default_factory=StrongThreshold)


class ServerSettings(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8765
    refresh_seconds: int = 3
    demo_mode: bool = True
    demo_refresh_seconds: int = 15


class SkewSettings(BaseModel):
    """Top-level settings for the Launch Skew Monitor."""
    universe: UniverseSettings = Field(default_factory=UniverseSettings)
    sources: SourceSettings = Field(default_factory=SourceSettings)
    module_a: ModuleASettings = Field(default_factory=ModuleASettings)
    module_b: ModuleBSettings = Field(default_factory=ModuleBSettings)
    module_c: ModuleCSettings = Field(default_factory=ModuleCSettings)
    signal_gate: SignalGateSettings = Field(default_factory=SignalGateSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)


class Settings(BaseModel):
    """Root settings (wraps SkewSettings to mirror the sibling-project pattern)."""
    skew: SkewSettings = Field(default_factory=SkewSettings)

    @classmethod
    def load(cls, path: str | Path | None = None) -> "Settings":
        if path is None or not Path(path).exists():
            return cls()
        data = yaml.safe_load(Path(path).read_text()) or {}
        # The YAML may be bare (top-level keys map directly to SkewSettings)
        # or wrapped under a ``skew:`` key. Auto-normalise so both work.
        if "skew" in data and isinstance(data["skew"], dict):
            return cls(**data)
        return cls(skew=data)
