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
from .cross_section import cross_backtest, rank_snapshot
from .engine import Engine, Result
from .feed.base import collect_series, get_feed
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


def _universe(source: str, instruments: list[str], series_csv: Optional[str]) -> dict:
    """Build a per-instrument series dict from a CSV or a feed source."""
    if series_csv:
        return ReplayFeed.from_csv(series_csv).series
    return collect_series(get_feed(source, instruments=instruments))


@app.command()
def rank(
    source: str = typer.Option("coinbase", "--source", help="coinbase | polygon | synthetic"),
    instrument: str = typer.Option("BTC-USD,ETH-USD,LTC-USD", "--instrument", help="comma-separated universe"),
    series: Optional[str] = typer.Option(None, "--series", help="multi-instrument CSV (overrides --source)"),
    config: Optional[str] = typer.Option(None, "--config"),
):
    """Show the current cross-sectional ranking (relative-strength momentum)."""
    settings = _load_settings(config)
    instruments = [s.strip() for s in instrument.split(",") if s.strip()]
    rows = rank_snapshot(_universe(source, instruments, series), settings)
    if not rows:
        console.print("[yellow]Not enough history to rank the universe.[/]")
        raise typer.Exit()
    t = Table(title="Driftwood cross-sectional ranking")
    t.add_column("instrument"); t.add_column("score", justify="right")
    t.add_column("ann vol", justify="right"); t.add_column("leg"); t.add_column("weight", justify="right")
    for r in rows:
        colour = {"LONG": "green", "SHORT": "red"}.get(r.leg, "dim")
        t.add_row(r.instrument, f"{r.score:+.2f}", f"{r.ann_vol*100:.0f}%",
                  f"[{colour}]{r.leg}[/]", f"{r.weight:+.2f}")
    console.print(t)


@app.command()
def xbacktest(
    source: str = typer.Option("synthetic", "--source", help="coinbase | polygon | synthetic"),
    instrument: str = typer.Option("BTC-USD,ETH-USD,LTC-USD,BCH-USD", "--instrument"),
    series: Optional[str] = typer.Option(None, "--series", help="multi-instrument CSV"),
    config: Optional[str] = typer.Option(None, "--config"),
    out: Optional[str] = typer.Option(None, "--out", help="Write the result JSON here"),
):
    """Cross-sectional (long-strong / short-weak) backtest over a universe."""
    settings = _load_settings(config)
    instruments = [s.strip() for s in instrument.split(",") if s.strip()]
    res = cross_backtest(_universe(source, instruments, series), settings)
    t = Table(title=f"Driftwood cross-sectional backtest — {len(res.instruments)} names", show_header=False)
    t.add_row("universe", ", ".join(res.instruments))
    t.add_row("bars", str(res.n_bars))
    t.add_row("net return", f"{res.net_return*100:+.1f}%")
    t.add_row("gross return", f"{res.gross_return*100:+.1f}%")
    t.add_row("cost drag", f"{res.cost_drag*100:.1f}%")
    t.add_row("sharpe (net, ann.)", f"{res.sharpe:.2f}")
    t.add_row("max drawdown", f"{res.max_drawdown*100:.1f}%")
    t.add_row("turnover", f"{res.turnover:.1f}")
    t.add_row("avg names held", f"{res.avg_names_held:.1f}")
    console.print(t)
    if out:
        Path(out).write_text(json.dumps(res.to_dict(), indent=2))
        console.print(f"[dim]wrote {out}[/]")


@app.command()
def export(
    source: str = typer.Option("coinbase", "--source", help="coinbase | polygon | synthetic"),
    instrument: str = typer.Option("BTC-USD,ETH-USD,LTC-USD,BCH-USD", "--instrument"),
    series: Optional[str] = typer.Option(None, "--series", help="multi-instrument CSV"),
    config: Optional[str] = typer.Option(None, "--config"),
    out: str = typer.Option("docs/drift.html", "--out", help="static HTML exhibit path"),
):
    """Build a self-contained static dashboard HTML (shareable, no server)."""
    from .exhibit import export_html
    settings = _load_settings(config)
    instruments = [s.strip() for s in instrument.split(",") if s.strip()]
    series_dict = _universe(source, instruments, series)
    path = export_html(series_dict, settings, out, source=source)
    console.print(f"[green]wrote[/] {path}  ({len(series_dict)} instruments)")


@app.command()
def studies(
    source: str = typer.Option("coinbase", "--source", help="coinbase | synthetic"),
    instrument: str = typer.Option(
        "BTC-USD,ETH-USD,LTC-USD,BCH-USD,ETC-USD,LINK-USD,ADA-USD,XLM-USD", "--instrument"),
    config: Optional[str] = typer.Option(None, "--config"),
    out: str = typer.Option("docs/case_studies.html", "--out", help="static report HTML path"),
):
    """Run the multi-case-study backtest report and write a clean static HTML."""
    from .case_studies import build_report, crypto_universe
    from .exhibit import export_report
    settings = _load_settings(config)
    instruments = [s.strip() for s in instrument.split(",") if s.strip()]
    if source in ("coinbase", "crypto"):
        console.print(f"[dim]pulling {len(instruments)} crypto symbols …[/]")
        series = crypto_universe(instruments)
    else:
        series = _universe(source, instruments, None)
    report = build_report(series, settings, source=source)
    path = export_report(report, out)
    # Console digest of every study.
    for st in report["studies"]:
        line = "  ".join(f"{m['label']}: {m['value']}" for m in st["metrics"])
        console.print(f"[bold]{st['name']}[/]\n  {line}")
    console.print(f"[green]wrote[/] {path}  ({report['header']['n_instruments']} instruments)")


@app.command()
def serve(
    source: str = typer.Option("coinbase", "--source", help="coinbase | polygon | synthetic"),
    instrument: str = typer.Option("BTC-USD,ETH-USD,LTC-USD,BCH-USD", "--instrument"),
    series: Optional[str] = typer.Option(None, "--series", help="multi-instrument CSV"),
    config: Optional[str] = typer.Option(None, "--config"),
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8000, "--port"),
):
    """Serve the live dashboard for a universe."""
    from .web.server import serve as serve_dashboard
    settings = _load_settings(config)
    instruments = [s.strip() for s in instrument.split(",") if s.strip()]
    series_dict = _universe(source, instruments, series)
    serve_dashboard(series_dict, settings, source=source, host=host, port=port)


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
