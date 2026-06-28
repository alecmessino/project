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

from . import universes as _universes
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
    source: str = typer.Option("yahoo", "--source", help="yahoo | polygon"),
    instrument: str = typer.Option("SPY,QQQ,IWM,EFA,EEM", "--instrument", help="comma-separated symbols"),
    config: Optional[str] = typer.Option(None, "--config"),
    backtest_too: bool = typer.Option(False, "--backtest", help="also backtest the pulled history"),
):
    """Pull a live equity feed (Yahoo, keyless; or Polygon with a key) and print fired signals."""
    settings = _load_settings(config)
    instruments = [s.strip() for s in instrument.split(",") if s.strip()]
    feed = get_feed(source, instruments=instruments)
    console.print(f"[bold]Pulling {source}[/] for {', '.join(instruments)} …")
    Engine(settings, feed).run(on_result=_print_signal)
    if backtest_too:
        for inst in instruments:
            _print_backtest(backtest(inst, feed.fetch(inst), settings))


def _universe(source: str, instruments: list[str], series_csv: Optional[str],
              pause: float = 13.0) -> dict:
    """Build a per-instrument series dict from a CSV or a feed source.

    Live sources use the resilient universe pulls (skip a symbol that fails);
    Polygon paces requests by `pause` seconds to respect the free-tier rate limit.
    """
    if series_csv:
        return ReplayFeed.from_csv(series_csv).series
    if source in ("yahoo", "yf", "equity", "equities", "stocks"):
        from .case_studies import equity_universe
        return equity_universe(instruments, source="yahoo", pause=0.3)
    if source == "polygon":
        from .case_studies import equity_universe
        return equity_universe(instruments, source="polygon", pause=pause)
    return collect_series(get_feed(source, instruments=instruments))


@app.command()
def rank(
    source: str = typer.Option("yahoo", "--source", help="yahoo | polygon | synthetic"),
    instrument: str = typer.Option(_universes.csv(_universes.EQUITIES), "--instrument", help="comma-separated universe"),
    series: Optional[str] = typer.Option(None, "--series", help="multi-instrument CSV (overrides --source)"),
    neutralize: str = typer.Option("none", "--neutralize", help="none | region | size | style"),
    config: Optional[str] = typer.Option(None, "--config"),
):
    """Show the current cross-sectional ranking (relative-strength momentum)."""
    settings = _load_settings(config)
    settings.cross_section.neutralize = neutralize
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
    source: str = typer.Option("yahoo", "--source", help="yahoo | polygon | synthetic"),
    instrument: str = typer.Option(_universes.csv(_universes.EQUITIES), "--instrument"),
    series: Optional[str] = typer.Option(None, "--series", help="multi-instrument CSV"),
    neutralize: str = typer.Option("none", "--neutralize", help="none | region | size | style"),
    config: Optional[str] = typer.Option(None, "--config"),
    out: Optional[str] = typer.Option(None, "--out", help="Write the result JSON here"),
):
    """Cross-sectional (long-strong / short-weak) backtest over a universe."""
    settings = _load_settings(config)
    settings.cross_section.neutralize = neutralize
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
    source: str = typer.Option("yahoo", "--source", help="yahoo | polygon | synthetic"),
    instrument: str = typer.Option(_universes.csv(_universes.EQUITIES), "--instrument"),
    series: Optional[str] = typer.Option(None, "--series", help="multi-instrument CSV"),
    config: Optional[str] = typer.Option(None, "--config"),
    out: str = typer.Option("docs/equities.html", "--out", help="static HTML exhibit path"),
):
    """Build a self-contained static dashboard HTML (shareable, no server)."""
    from .exhibit import export_html
    settings = _load_settings(config)
    instruments = [s.strip() for s in instrument.split(",") if s.strip()]
    series_dict = _universe(source, instruments, series)
    if not series_dict and source != "synthetic":
        console.print("[yellow]no data pulled (rate-limited?) — keeping existing exhibit.[/]")
        raise typer.Exit()
    path = export_html(series_dict, settings, out, source=source)
    console.print(f"[green]wrote[/] {path}  ({len(series_dict)} instruments)")


@app.command()
def studies(
    source: str = typer.Option("yahoo", "--source", help="yahoo | polygon | synthetic"),
    instrument: str = typer.Option(_universes.csv(_universes.EQUITIES), "--instrument"),
    config: Optional[str] = typer.Option(None, "--config"),
    out: str = typer.Option("docs/equities_case_studies.html", "--out", help="static report HTML path"),
    pause: float = typer.Option(13.0, "--pause", help="seconds between Polygon fetches (free-tier rate limit)"),
):
    """Run the multi-case-study backtest report and write a clean static HTML.

    Keyless via Yahoo (`--source yahoo`); Polygon optional with POLYGON_API_KEY.
    Without a usable source it still runs the synthetic control study so the report
    is never empty.
    """
    from .case_studies import build_report
    from .exhibit import export_report
    settings = _load_settings(config)
    instruments = [s.strip() for s in instrument.split(",") if s.strip()]
    _src = "source chain (tiingo→stooq→yahoo)" if source in ("yahoo", "yf", "equity", "equities", "stocks") else source
    console.print(f"[dim]pulling {len(instruments)} symbols via {_src} …[/]")
    series = _universe(source, instruments, None, pause=pause)
    if not series and source != "synthetic":
        console.print("[yellow]no data pulled (rate-limited?) — keeping existing report.[/]")
        raise typer.Exit()
    report = build_report(series, settings, source=source)
    path = export_report(report, out)
    # Console digest of every study.
    for st in report["studies"]:
        line = "  ".join(f"{m['label']}: {m['value']}" for m in st["metrics"])
        console.print(f"[bold]{st['name']}[/]\n  {line}")
    console.print(f"[green]wrote[/] {path}  ({report['header']['n_instruments']} instruments)")


@app.command()
def thesis(
    docs: str = typer.Option("docs", "--docs", help="directory holding the exhibits"),
    out: str = typer.Option("docs/thesis.html", "--out", help="thesis page"),
):
    """Build the equities-first thesis page (live figures from the tearsheet & ledger)."""
    from .thesis import build_thesis
    from .exhibit import export_thesis
    state = build_thesis(docs)
    path = export_thesis(state, out)
    eq = state.get("equities")
    if eq:
        console.print(f"thesis: equities {eq['span']} maxDD "
                      f"{eq['strat_maxdd']*100:.1f}% vs {eq['bench_maxdd']*100:.1f}% buy&hold")
    console.print(f"[green]wrote[/] {path}")


@app.command()
def taxlab(
    docs: str = typer.Option("docs", "--docs", help="directory holding the exhibits"),
    out: str = typer.Option("docs/taxlab.html", "--out", help="Tax Lab page"),
):
    """Build the interactive Tax Lab (after-tax / TLH / asset location) from the ledger."""
    from .taxlab import build_taxlab
    from .exhibit import export_taxlab
    state = build_taxlab(docs)
    path = export_taxlab(state, out)
    p = state.get("profile")
    if p:
        console.print(f"taxlab: pretax {p['pretax_return']*100:+.1f}%  "
                      f"ST realized {p['st_realized']*100:.1f}%  harvested {p['harvested_st']*100:.1f}%")
    console.print(f"[green]wrote[/] {path}")


@app.command()
def leakage(
    out: str = typer.Option("docs/leakage.html", "--out", help="Tax-Leakage Diagnostic page"),
):
    """Build the Tax-Leakage Diagnostic — the one-page Before/After pitch artifact."""
    from .leakage import build_leakage
    from .exhibit import export_leakage
    state = build_leakage()
    path = export_leakage(state, out)
    h = state["headline"]
    console.print(f"[green]wrote[/] {path}  (Structural Alpha (tax) +{h['alpha_low']}–{h['alpha_high']}%/yr)")


@app.command()
def statemap(
    out: str = typer.Option("docs/statemap.html", "--out", help="State Tax Map exhibit"),
):
    """Build the multi-dimension State Tax Map (cap-gains / marriage / estate / step-up / Structural Alpha)."""
    from .statemap import build_statemap
    from .exhibit import export_statemap
    state = build_statemap()
    path = export_statemap(state, out)
    console.print(f"[green]wrote[/] {path}  ({len(state['states'])} states · {len(state['dimensions'])} dimensions)")


@app.command()
def hub(
    docs: str = typer.Option("docs", "--docs", help="directory holding the exhibits"),
    out: str = typer.Option("docs/index.html", "--out", help="hub landing page"),
):
    """Build the markets-only landing hub (links every exhibit + live headlines)."""
    from .hub import build_hub
    from .exhibit import export_hub
    state = build_hub(docs)
    path = export_hub(state, out)
    present = sum(1 for e in state["exhibits"] if e["present"])
    console.print(f"[green]wrote[/] {path}  ({present}/{len(state['exhibits'])} exhibits linked, "
                  f"{len(state['headline'])} headline stats)")


@app.command()
def ledger(
    equities: str = typer.Option(_universes.csv(_universes.EQUITIES), "--equities"),
    state: str = typer.Option("docs/ledger.json", "--state", help="append-only ledger JSON"),
    out: str = typer.Option("docs/ledger.html", "--out", help="ledger exhibit HTML"),
    seed_sessions: int = typer.Option(504, "--seed-sessions", help="walk-forward seed length on first run (~2y of sessions)"),
    config: Optional[str] = typer.Option(None, "--config"),
    min_coverage: float = typer.Option(0.6, "--min-coverage", help="abort (exit 1) if fewer than this fraction of symbols fetch — a rate-limit/outage guard"),
    pause: float = typer.Option(0.25, "--pause", help="jittered seconds between per-symbol fetches to dodge 429 choking (0 disables)"),
):
    """Advance the forward paper-trade ledger by one session and render it.

    The headline book is the equities region/factor rotation only — crypto is too
    thin to rank cross-sectionally, so it's not in this book. First run seeds from a
    walk-forward replay (no lookahead); later runs append the newest session. Keyless.
    """
    import json as _json
    from .ledger import build_ledger_state, seed_ledger, update_ledger
    from .exhibit import export_ledger
    settings = _load_settings(config)
    syms = [s.strip() for s in equities.split(",") if s.strip()]
    console.print(f"[dim]pulling daily history for {len(syms)} instruments + VT/VTI benchmarks …[/]")
    from .feed.resolve import equity_feeds, pull_universe, pull_symbol
    feeds = equity_feeds()
    console.print(f"[dim]source chain: {', '.join(n for n, _ in feeds)}[/]")
    series = pull_universe(syms, feeds, min_bars=settings.signal.min_history, pause=pause)
    # Buy-and-hold benchmarks, total return: VT (global, ~62/28/10 US/dev/EM — US ~62% as of mid-2026) and
    # VTI (US total market). Both fetched on the same adjusted-close basis as the book.
    benchmarks: dict = {}
    for label in ("VT", "VTI"):
        b = pull_symbol(label, feeds, settings.signal.min_history)
        if b is not None:
            benchmarks[label] = b
    benchmarks = benchmarks or None

    # Loud-failure gate: a rate-limited/outage run must NOT silently rewrite the ledger as a
    # "success". Abort with a non-zero exit when symbol coverage is too thin to trust.
    coverage = (len(series) / len(syms)) if syms else 0.0
    if coverage < min_coverage:
        console.print(f"[red]ledger: only {len(series)}/{len(syms)} symbols fetched "
                      f"({coverage:.0%} < {min_coverage:.0%} required) — likely rate-limited or an outage. "
                      f"Aborting WITHOUT writing.[/]")
        raise typer.Exit(code=1)

    path = Path(state)
    if path.exists() and _json.loads(path.read_text() or "{}").get("entries"):
        led = _json.loads(path.read_text())
        n_before = len(led.get("entries", []))
        update_ledger(led, series, settings, benchmarks=benchmarks)
        if len(led["entries"]) > n_before:
            console.print(f"appended one session ({len(led['entries'])} total)")
        else:
            console.print("no new session — healthy fetch, latest close already recorded (clean no-op)")
    else:
        led = seed_ledger(series, settings, sessions=seed_sessions, benchmarks=benchmarks)
        console.print(f"seeded {len(led['entries'])} sessions (walk-forward)")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_json.dumps(led, indent=0))
    st = build_ledger_state(led, bars_per_year=settings.engine.bars_per_year, tax=settings.tax)
    export_ledger(st, out)
    h = st["header"]
    console.print(f"[bold]ledger[/] {h['days']} sessions ({h['live_days']} live), "
                  f"total return {h['total_return']*100:+.2f}%, "
                  f"book {h['n_long']}L/{h['n_short']}S")
    console.print(f"[green]wrote[/] {state} + {out}")


@app.command()
def tearsheet(
    equities: str = typer.Option(_universes.csv(_universes.EQUITIES), "--equities"),
    years: float = typer.Option(40.0, "--years", help="how many years of daily history to pull"),
    train_frac: float = typer.Option(0.6, "--train-frac", help="in-sample fraction"),
    config: Optional[str] = typer.Option(None, "--config"),
    out: str = typer.Option("docs/tearsheet.html", "--out"),
):
    """Long-history tearsheet: strategy vs buy-and-hold, in-sample/out-of-sample."""
    from .tearsheet import build_tearsheet
    from .exhibit import export_tearsheet
    settings = _load_settings(config)
    eq = [s.strip() for s in equities.split(",") if s.strip()]
    console.print(f"[dim]pulling daily history (~{years:.0f}y) for {len(eq)} equities …[/]")
    report = build_tearsheet(settings, equities=eq, years=years, train_frac=train_frac)
    if not report["books"]:
        console.print("[yellow]no data pulled (rate-limited?) — keeping existing tearsheet.[/]")
        raise typer.Exit()
    path = export_tearsheet(report, out)
    for bk in report["books"]:
        s, b, o = bk["strategy"], bk["benchmark"], bk["oos"]
        console.print(
            f"[bold]{bk['name']}[/] ({bk['span'][0]}→{bk['span'][1]}, fit L={bk['fit']['lookback']}/"
            f"c={bk['fit']['continuation']})\n"
            f"  strategy: CAGR {s['cagr']*100:+.1f}%  Sharpe {s['sharpe']:.2f}  maxDD {s['max_drawdown']*100:.1f}%"
            f"   |  buy&hold: CAGR {b['cagr']*100:+.1f}%  Sharpe {b['sharpe']:.2f}  maxDD {b['max_drawdown']*100:.1f}%\n"
            f"  out-of-sample: Sharpe {o['test']['sharpe']:.2f}  CAGR {o['test']['cagr']*100:+.1f}%")
    console.print(f"[green]wrote[/] {path}  ({len(report['books'])} books)")


@app.command()
def serve(
    source: str = typer.Option("yahoo", "--source", help="yahoo | polygon | synthetic"),
    instrument: str = typer.Option(_universes.csv(_universes.EQUITIES), "--instrument"),
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
