"""Command-line interface for mrbet.

Commands:
  mrbet simulate --game <game.yaml> --replay <replay.json>   # replay a sequence
  mrbet run --game <game.yaml> [--provider theodds|manual]   # live / manual loop
  mrbet baseline --game <game.yaml>                          # show pregame anchors
  mrbet notify-test                                          # desktop + push test
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .config import GameConfig, Settings
from .engine import Engine, Result
from .models import Signal
from .notify import Notifier, format_signal
from .odds.base import get_provider
from .storage import Storage

app = typer.Typer(add_completion=False, help="Mean-reversion live betting signals")
console = Console()

DEFAULT_SETTINGS = "config/settings.yaml"


def _load(settings_path: str, game_path: str) -> tuple[Settings, GameConfig]:
    settings = Settings.load(settings_path) if Path(settings_path).exists() else Settings()
    game = GameConfig.load(game_path)
    return settings, game


def _result_row(table: Table, res: Result) -> None:
    e = res.evaluation
    b = e.baseline
    flag = "🔥" if (res.signal and res.signal.strong) else ("✅" if res.signal else "")
    table.add_row(
        f"{(b.team or 'GAME')} {b.period.value}",
        f"{b.line:g}",
        f"{e.live.line:g}",
        f"{e.pct_move*100:+.1f}%",
        e.side.value.upper(),
        f"{e.fair_final:.1f}",
        f"{e.edge_pts:+.1f}",
        f"{e.prob*100:.0f}%",
        f"{e.ev*100:+.1f}%",
        f"${e.kelly_stake:.2f}",
        flag,
    )


def _new_table() -> Table:
    table = Table(show_header=True, header_style="bold")
    for col in ["market", "pre", "live", "move", "side", "fair", "edge", "P", "EV", "stake", ""]:
        table.add_column(col)
    return table


@app.command()
def simulate(
    game: str = typer.Option(..., help="Path to game baseline YAML"),
    replay: str = typer.Option(..., help="Path to replay JSON"),
    settings: str = typer.Option(DEFAULT_SETTINGS, help="Path to settings YAML"),
    notify: bool = typer.Option(False, help="Actually fire notifications for flags"),
):
    """Replay a recorded sequence through the engine and print flagged opportunities."""
    s, g = _load(settings, game)
    provider = get_provider("replay", replay=replay)
    notifier = Notifier(s.notifications) if notify else None
    storage = Storage(event_id=g.event.id)
    engine = Engine(s, g, provider, notifier=notifier, storage=storage)

    flagged: list[Signal] = []

    for snap in provider.snapshots():
        st = snap.state
        console.rule(
            f"[bold]{st.period.value.upper()} {st.minutes_remaining:.1f} min left  "
            f"score {g.event.away_key} {st.away_score} - {st.home_score} {g.event.home_key}"
        )
        table = _new_table()
        for res in engine.process_snapshot(snap):
            _result_row(table, res)
            if storage:
                storage.log(res.evaluation, res.signal)
            if res.signal:
                flagged.append(res.signal)
                if notifier:
                    notifier.maybe_notify(res.signal)
        console.print(table)

    storage.close()
    console.rule("[bold green]Flagged opportunities")
    if not flagged:
        console.print("[yellow]No opportunities crossed all thresholds.")
    for sig in flagged:
        title, body = format_signal(sig)
        console.print(f"[bold]{title}")
        console.print(body + "\n")


@app.command()
def run(
    game: str = typer.Option(..., help="Path to game baseline YAML"),
    provider: str = typer.Option("theodds", help="theodds | manual"),
    settings: str = typer.Option(DEFAULT_SETTINGS, help="Path to settings YAML"),
    replay: Optional[str] = typer.Option(None, help="Replay JSON (for manual provider)"),
    no_notify: bool = typer.Option(False, help="Disable notifications"),
):
    """Run the live loop (The Odds API) or manual entry."""
    s, g = _load(settings, game)
    kwargs: dict = {}
    if provider == "theodds":
        kwargs = dict(
            event=g.event,
            markets=s.engine.markets,
            poll_interval=s.engine.poll_interval_seconds,
            bookmaker=g.event.bookmaker,
        )
    elif provider == "manual":
        kwargs = dict(replay=replay)
    prov = get_provider(provider, **kwargs)
    notifier = None if no_notify else Notifier(s.notifications)
    storage = Storage(event_id=g.event.id)
    engine = Engine(s, g, prov, notifier=notifier, storage=storage)

    def show(res: Result):
        if res.signal:
            title, body = format_signal(res.signal)
            console.print(f"[bold green]{title}")
            console.print(body + "\n")

    try:
        engine.run(on_result=show)
    except KeyboardInterrupt:
        console.print("\n[dim]stopped.")
    finally:
        storage.close()


@app.command()
def baseline(
    game: str = typer.Option(..., help="Path to game baseline YAML"),
):
    """Print the pregame baselines that live lines are compared against."""
    g = GameConfig.load(game)
    console.rule(f"[bold]{g.event.away} @ {g.event.home}")
    table = Table(show_header=True, header_style="bold")
    for col in ["market", "team", "period", "line", "over", "under"]:
        table.add_column(col)
    for b in g.baselines():
        table.add_row(
            b.market_type.value, b.team or "-", b.period.value,
            f"{b.line:g}", f"{b.over_odds:+d}", f"{b.under_odds:+d}",
        )
    console.print(table)


@app.command()
def backtest(
    game: str = typer.Option(..., help="Path to game baseline YAML"),
    db: str = typer.Option("data/runtime/mrbet.sqlite", help="Path to the observations SQLite"),
    results: Optional[str] = typer.Option(None, help="Results YAML/JSON with final scores"),
    all_obs: bool = typer.Option(False, "--all", help="Grade all observations, not just flagged"),
):
    """Grade logged signals against actual results + closing-line value."""
    from . import backtest as bt

    g = GameConfig.load(game)
    finals = bt.load_finals(results, g)
    summary = bt.grade(db, finals=finals, event_id=g.event.id, flagged_only=not all_obs)

    if summary.bets == 0:
        console.print("[yellow]No matching observations in the log. Run `simulate`/`run` first.")
        return

    table = Table(show_header=True, header_style="bold")
    for col in ["market", "side", "line", "odds", "stake", "result", "actual", "profit", "close", "CLV"]:
        table.add_column(col)
    for b in summary.graded:
        color = {"win": "green", "loss": "red", "push": "yellow"}.get(b.outcome or "", "dim")
        table.add_row(
            f"{(b.team or 'GAME')} {b.period}", b.side.upper(), f"{b.line:g}", f"{b.odds:+d}",
            f"${b.stake:.2f}", f"[{color}]{b.outcome}[/{color}]",
            "-" if b.actual is None else f"{b.actual:g}",
            f"${b.profit:+.2f}",
            "-" if b.closing_line is None else f"{b.closing_line:g}",
            "-" if b.clv_pts is None else f"{b.clv_pts:+.1f}",
        )
    console.print(table)

    console.rule("[bold]Summary")
    decided = summary.wins + summary.losses
    console.print(f"Bets: {summary.bets}  |  Record: {summary.wins}-{summary.losses}-{summary.pushes}")
    if decided:
        console.print(
            f"Win rate: {summary.win_rate*100:.1f}%  (model predicted {summary.avg_pred_prob*100:.1f}%)"
        )
    if summary.staked:
        console.print(
            f"Staked: ${summary.staked:.2f}  |  Net: ${summary.profit:+.2f}  |  "
            f"ROI: {summary.roi*100:+.1f}%  (model EV avg {summary.avg_model_ev*100:+.1f}%)"
        )
    else:
        console.print("[dim]No finals supplied — provide --results to grade win/loss/ROI.")
    if summary.clv_graded:
        console.print(
            f"Closing-line value: beat close on {summary.clv_beat}/{summary.clv_graded} "
            f"({summary.clv_beat_rate*100:.0f}%), avg {summary.avg_clv_pts:+.1f} pts"
        )


@app.command("notify-test")
def notify_test():
    """Fire a test desktop + push notification."""
    from .models import (
        Baseline, Evaluation, GameState, MarketLine, MarketType, Period, Side, Signal,
    )

    state = GameState(Period.FULL, 9.0, 39.0, 9, 7)
    base = Baseline(MarketType.GAME_TOTAL, Period.FULL, 219.0, -110, -110)
    live = MarketLine(MarketType.GAME_TOTAL, Period.FULL, 205.0, -110, -110)
    ev = Evaluation(base, live, state, Side.OVER, 213.5, -0.064, 8.5, 0.61, 0.524, 0.05, 4.25)
    sig = Signal(ev, strong=True, reasons=["test"])
    Notifier(Settings().notifications).maybe_notify(sig)
    console.print("[green]Sent test notification (check desktop + push).")


if __name__ == "__main__":
    app()
