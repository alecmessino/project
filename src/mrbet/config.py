"""Load and validate settings + per-game baselines (pydantic)."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field

from .models import Baseline, MarketType, Period
from .reversion import ReversionParams


# --------------------------------------------------------------------------- #
# settings.yaml schema
# --------------------------------------------------------------------------- #
class LeagueSigma(BaseModel):
    """Per-league sigma override (either field optional; missing → use the default)."""
    sigma_full: Optional[float] = None
    sigma_team: Optional[float] = None


class ModelSettings(BaseModel):
    beta: float = 0.70
    sigma_full: float = 11.0
    sigma_team: float = 8.0
    min_minutes_elapsed: float = 5.0
    # Per-league sigma overrides keyed by lowercase league (e.g. "wnba"). The
    # top-level sigma_full/sigma_team stay the default (NBA); a league entry scales
    # them for that league's lower totals/variance.
    leagues: dict[str, LeagueSigma] = {}

    def sigmas_for(self, league: Optional[str]) -> tuple[float, float]:
        """(sigma_full, sigma_team) for a league, falling back to the defaults."""
        sf, st = self.sigma_full, self.sigma_team
        if league:
            o = self.leagues.get(league.lower())
            if o is not None:
                sf = o.sigma_full if o.sigma_full is not None else sf
                st = o.sigma_team if o.sigma_team is not None else st
        return sf, st

    def to_params(self) -> ReversionParams:
        return ReversionParams(
            beta=self.beta,
            sigma_full=self.sigma_full,
            sigma_team=self.sigma_team,
            min_minutes_elapsed=self.min_minutes_elapsed,
        )


class MinMinutesRemaining(BaseModel):
    full: float = 6.0
    half: float = 4.0
    quarter: float = 3.0

    def for_kind(self, kind: str) -> float:
        return getattr(self, kind, self.full)


class TriggerSettings(BaseModel):
    pct_move_threshold: float = 0.10
    edge_pts_threshold: float = 3.0
    ev_threshold: float = 0.0
    ev_strong_threshold: float = 0.03
    min_minutes_remaining: MinMinutesRemaining = Field(default_factory=MinMinutesRemaining)


class StakingSettings(BaseModel):
    bankroll: float = 100.0
    kelly_fraction: float = 0.25
    max_stake_fraction: float = 0.05


class EngineSettings(BaseModel):
    poll_interval_seconds: int = 60
    markets: list[str] = Field(default_factory=lambda: ["total_full", "total_h1", "team_total"])
    # Per-league market override. WNBA team totals aren't reliably offered for live
    # wagering, so focus WNBA on combined game totals. Falls back to `markets`.
    league_markets: dict[str, list[str]] = Field(
        default_factory=lambda: {"wnba": ["total_full", "total_h1"]})
    min_api_credits: int = 50
    region: str = "us"
    books: list[str] = Field(default_factory=lambda: ["bovada"])
    fallback_consensus: bool = True
    # Live sampling cadence: "interval" polls every poll_interval_seconds;
    # "timeout" watches the free ESPN clock and spends a paid odds fetch only at
    # the ~6:00/3:00 marks of Q1-Q3 (~25x fewer credits).
    cadence: str = "interval"
    clock_poll_interval: int = 45

    def markets_for(self, league: Optional[str]) -> list[str]:
        """Tracked market keys for a league (per-league override, else the default)."""
        if league and league.lower() in self.league_markets:
            return self.league_markets[league.lower()]
        return self.markets


class NotificationSettings(BaseModel):
    desktop: bool = True
    push: bool = True
    sms: bool = False      # email-to-SMS gateway; configure via env (see .env.example)
    discord: bool = False  # Discord webhook; set DISCORD_WEBHOOK_URL in env (see .env.example)
    slack: bool = False    # Slack webhook; set SLACK_WEBHOOK_URL in env (see .env.example)
    reissue_ev_delta: float = 0.02


class Settings(BaseModel):
    model: ModelSettings = Field(default_factory=ModelSettings)
    triggers: TriggerSettings = Field(default_factory=TriggerSettings)
    staking: StakingSettings = Field(default_factory=StakingSettings)
    engine: EngineSettings = Field(default_factory=EngineSettings)
    notifications: NotificationSettings = Field(default_factory=NotificationSettings)

    @classmethod
    def load(cls, path: str | Path) -> "Settings":
        data = yaml.safe_load(Path(path).read_text()) or {}
        return cls(**data)


# --------------------------------------------------------------------------- #
# game baseline schema
# --------------------------------------------------------------------------- #
class EventMeta(BaseModel):
    id: str
    league: str = "NBA"
    away: str
    home: str
    away_key: str
    home_key: str
    commence_time: Optional[str] = None
    bookmaker: str = "bovada"
    # Bovada's numeric event id (from the coupon/board). When set, the live feed
    # maps to the game deterministically instead of fuzzy team-name matching.
    bovada_event_id: Optional[str] = None


class OverUnder(BaseModel):
    line: float
    over: int
    under: int


class GameConfig(BaseModel):
    """Pregame baselines for a single event."""

    event: EventMeta
    totals: dict[str, OverUnder] = Field(default_factory=dict)
    team_totals: dict[str, OverUnder] = Field(default_factory=dict)
    sides: dict = Field(default_factory=dict)
    total_ladder: dict[float, dict[str, int]] = Field(default_factory=dict)
    # Optional actual results for backtesting, e.g.
    #   finals: { game: { full: 224, h1: 110 }, team: { OKC: 112, SAS: 112 } }
    finals: dict = Field(default_factory=dict)

    @classmethod
    def load(cls, path: str | Path) -> "GameConfig":
        data = yaml.safe_load(Path(path).read_text()) or {}
        return cls(**data)

    def baselines(self) -> list[Baseline]:
        """Flatten the config into the Baseline objects the engine consumes."""
        out: list[Baseline] = []
        period_map = {
            "full": Period.FULL,
            "h1": Period.H1,
            "q1": Period.Q1,
            "q2": Period.Q2,
            "q3": Period.Q3,
            "q4": Period.Q4,
        }
        for pkey, ou in self.totals.items():
            period = period_map.get(pkey)
            if period is None:
                continue
            out.append(
                Baseline(
                    market_type=MarketType.GAME_TOTAL,
                    period=period,
                    line=ou.line,
                    over_odds=ou.over,
                    under_odds=ou.under,
                )
            )
        for team, ou in self.team_totals.items():
            out.append(
                Baseline(
                    market_type=MarketType.TEAM_TOTAL,
                    period=Period.FULL,
                    line=ou.line,
                    over_odds=ou.over,
                    under_odds=ou.under,
                    team=team,
                )
            )
        return out

    def baseline_for(self, market_type: MarketType, period: Period, team: Optional[str] = None) -> Optional[Baseline]:
        for b in self.baselines():
            if b.market_type == market_type and b.period == period and b.team == team:
                return b
        return None
