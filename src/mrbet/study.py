"""Empirical calibration from real score paths (free ESPN data, no odds).

`reversion_fit` answers the question underneath the whole system — *does live
NBA scoring revert to the pregame rate, and by how much?* — by least-squares
fitting the model's own blend against realized remaining scoring:

    remaining_rate = beta * pregame_rate + (1 - beta) * elapsed_pace

beta ~ 1 => remaining play reverts fully to the pregame rate (early pace is
noise); beta ~ 0 => momentum continues. This is the honest way to tune the core
`beta`: outcomes are real and no line model is involved, so there is no
circularity (unlike a modeled-line ROI backtest).
"""

from __future__ import annotations

from dataclasses import dataclass

from .espn import ESPNClient, GameHistory, playoff_dates


@dataclass
class FitResult:
    label: str
    beta: float        # best-fit reversion weight
    n: int             # samples
    r2: float          # variance explained vs the beta=0 (momentum) baseline

    def __str__(self) -> str:
        return f"{self.label:26s}  beta={self.beta:+.2f}  n={self.n:4d}  R^2 vs momentum={self.r2:+.2f}"


def _fit(samples: list[tuple[float, float]]) -> tuple[float, float]:
    """beta = Sxy/Sxx for y = beta*x; R^2 measured against the beta=0 baseline."""
    sxx = sum(x * x for x, _ in samples)
    sxy = sum(x * y for x, y in samples)
    if sxx == 0:
        return float("nan"), 0.0
    beta = sxy / sxx
    sse = sum((y - beta * x) ** 2 for x, y in samples)
    sse0 = sum(y * y for _, y in samples)
    r2 = 1 - sse / sse0 if sse0 else 0.0
    return beta, r2


def load_playoff_games(client: ESPNClient, start: str, end: str) -> list[GameHistory]:
    ids = client.playoff_game_ids(playoff_dates(start, end))
    return [h for h in (client.game_history(eid) for eid, _ in ids) if h]


def reversion_fit(games: list[GameHistory], sample_at: float = 6.0) -> list[FitResult]:
    """Fit beta for full-game (at several cutoffs) and team totals."""
    out: list[FitResult] = []

    def full_samples(cutoff: float) -> list[tuple[float, float]]:
        s = []
        for h in games:
            T, F = h.pregame_total, h.finals.get("game", {}).get("full")
            if not T or F is None:
                continue
            rate_pre = T / 48.0
            for tp in h.timeline:
                e = tp.minutes_elapsed
                if e < cutoff or e > 46:
                    continue
                pace = tp.total / e
                rem = (F - tp.total) / (48.0 - e)
                s.append((rate_pre - pace, rem - pace))
                break
        return s

    for cutoff in (sample_at, 12.0, 24.0):
        b, r2 = _fit(full_samples(cutoff))
        out.append(FitResult(f"full-game @>={cutoff:.0f}min", b, len(full_samples(cutoff)), r2))

    # team totals: each team is an independent sample
    team_s: list[tuple[float, float]] = []
    for h in games:
        pre = h.pregame_team_totals()
        for team, is_home in ((h.away, False), (h.home, True)):
            T, F = pre.get(team), h.finals.get("team", {}).get(team)
            if not T or F is None:
                continue
            rate_pre = T / 48.0
            for tp in h.timeline:
                e = tp.minutes_elapsed
                if e < sample_at or e > 46:
                    continue
                pts = tp.home_score if is_home else tp.away_score
                pace = pts / e
                rem = (F - pts) / (48.0 - e)
                team_s.append((rate_pre - pace, rem - pace))
                break
    b, r2 = _fit(team_s)
    out.append(FitResult("team-total @>=" + f"{sample_at:.0f}min", b, len(team_s), r2))
    return out
