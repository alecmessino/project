"""Driftwood command line: backtest, simulate (stream), and a zero-dependency demo.

Mirrors mrbet's CLI shape. `demo` runs the whole pipeline on a seeded synthetic
trend so the system is inspectable with no data files or network.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .backtest import backtest
from .config import Settings
from .engine import Engine, Result
from .feed.base import get_feed
from .feed.replay import ReplayFeed
from .feed.synthetic import SyntheticFeed

app = typer.Typer(add_completion=False, help="Driftwood — trend-following signal system.")
console = Console()


def _load_settings(config: Optional[str]) -> Settings:
    return Settings.load(config) if config else Settings()


def _print_signal(res: Result) -> None:
    sig = res.signal
    if sig is None:
        return
    e = sig.evaluation
    tag = "[bold red]STRONG[/]" if sig.strong else "[yellow]signal[/]"
    console.print(
        f"{tag} {e.instrument} {e.side.value.upper()} @ {e.asof} — "
        f"weight {e.target_weight:+.2f}  ({'; '.join(sig.reasons)})"
    )


def _print_backtest(res) -> None:
    t = Table(title=f"Driftwood backtest — {res.instrument}", show_header=False)
    t.add_row("bars", str(res.n_bars))
    t.add_row("trades", str(res.n_trades))
    t.add_row("net return", f"{res.net_return*100:+.1f}%")
    t.add_row("gross return", f"{res.gross_return*100:+.1f}%")
    t.add_row("cost drag", f"{res.cost_drag*100:.1f}%")
    t.add_row("sharpe (net, ann.)", f"{res.sharpe:.2f}")
    t.add_row("max drawdown", f"{res.max_drawdown*100:.1f}%")
    t.add_row("hit rate", f"{res.hit_rate*100:.0f}%")
    t.add_row("turnover", f"{res.turnover:.1f}")
    t.add_row("avg exposure", f"{res.avg_exposure:.2f}")
    console.print(t)


@app.command("backtest")
def backtest_cmd(
    series: str = typer.Option(..., "--series", help="CSV: asof,close[,high,low,volume]"),
    instrument: Optional[str] = typer.Option(None, "--instrument"),
    config: Optional[str] = typer.Option(None, "--config"),
    out: Optional[str] = typer.Option(None, "--out", help="Write the result JSON here"),
):
    """Backtest the momentum model on a recorded price series."""
    settings = _load_settings(config)
    feed = ReplayFeed.from_csv(series, instrument=instrument)
    for inst, bars in feed.series.items():
        res = backtest(inst, bars, settings)
        _print_backtest(res)
        if out:
            Path(out).write_text(json.dumps(res.to_dict(), indent=2))
            console.print(f"[dim]wrote {out}[/]")


@app.command()
def simulate(
    replay: str = typer.Option(..., "--replay", help="CSV price series to stream"),
    instrument: Optional[str] = typer.Option(None, "--instrument"),
    config: Optional[str] = typer.Option(None, "--config"),
):
    """Stream a recorded series through the live engine and print fired signals."""
    settings = _load_settings(config)
    feed = ReplayFeed.from_csv(replay, instrument=instrument)
    Engine(settings, feed).run(on_result=_print_signal)


@app.command()
def live(
    source: str = typer.Option("coinbase", "--source", help="coinbase | polygon"),
    instrument: str = typer.Option("BTC-USD", "--instrument", help="comma-separated symbols"),
    config: Optional[str] = typer.Option(None, "--config"),
    backtest_too: bool = typer.Option(False, "--backtest", help="also backtest the pulled history"),
):
    """Pull a live feed (Coinbase crypto / Polygon equities) and print fired signals.

    Coinbase needs no key; Polygon reads POLYGON_API_KEY from .env / the environment.
    """
    settings = _load_settings(config)
    instruments = [s.strip() for s in instrument.split(",") if s.strip()]
    feed = get_feed(source, instruments=instruments)
    console.print(f"[bold]Pulling {source}[/] for {', '.join(instruments)} …")
    Engine(settings, feed).run(on_result=_print_signal)
    if backtest_too:
        for inst in instruments:
            _print_backtest(backtest(inst, feed.fetch(inst), settings))


@app.command()
def demo(
    n_bars: int = typer.Option(750, "--bars"),
    config: Optional[str] = typer.Option(None, "--config"),
):
    """Run the full pipeline on a seeded synthetic trend (no data files needed)."""
    settings = _load_settings(config)
    # Up-trend, chop, down-trend: a momentum model should profit on the trends.
    feed = SyntheticFeed(
        instruments=("DEMO",),
        n_bars=n_bars,
        regimes=[(n_bars // 3, 0.45), (n_bars // 3, 0.0), (n_bars - 2 * (n_bars // 3), -0.45)],
        bars_per_year=settings.engine.bars_per_year,
    )
    console.print("[bold]Streaming signals[/] (synthetic up/chop/down regimes):")
    fired = 0

    def _count(res: Result) -> None:
        nonlocal fired
        if res.signal is not None:
            fired += 1
            _print_signal(res)

    Engine(settings, feed).run(on_result=_count)
    console.print(f"[dim]{fired} signals fired.[/]\n")
    _print_backtest(backtest("DEMO", feed.series("DEMO"), settings))


if __name__ == "__main__":
    app()
