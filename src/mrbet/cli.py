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

# Load .env (gitignored) so ODDS_API_KEY / THE_ODDS_API_KEY are available locally.
from .envload import load_env  # noqa: E402
load_env()

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
            books=s.engine.books,
            region=s.engine.region,
            fallback_consensus=s.engine.fallback_consensus,
            cadence=s.engine.cadence,
            clock_poll_interval=s.engine.clock_poll_interval,
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
def serve(
    game: str = typer.Option(..., help="Path to game baseline YAML"),
    provider: str = typer.Option("theodds", help="theodds | replay"),
    settings: str = typer.Option(DEFAULT_SETTINGS, help="Path to settings YAML"),
    replay: Optional[str] = typer.Option(None, help="Replay JSON (for replay provider)"),
    host: str = typer.Option("127.0.0.1", help="Bind host"),
    port: int = typer.Option(8000, help="Bind port"),
    no_notify: bool = typer.Option(False, help="Disable notifications"),
):
    """Launch the live web dashboard (auto-polls, no manual entry)."""
    from .web import serve as serve_dashboard

    s, g = _load(settings, game)
    if provider == "theodds":
        kwargs = dict(
            event=g.event, markets=s.engine.markets,
            poll_interval=s.engine.poll_interval_seconds, bookmaker=g.event.bookmaker,
            books=s.engine.books, region=s.engine.region,
            fallback_consensus=s.engine.fallback_consensus,
            cadence=s.engine.cadence, clock_poll_interval=s.engine.clock_poll_interval,
        )
    else:
        kwargs = dict(replay=replay)
    prov = get_provider(provider, **kwargs)
    serve_dashboard(s, g, prov, host=host, port=port, notify=not no_notify)


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


@app.command("reversion-fit")
def reversion_fit_cmd(
    start: str = typer.Option("20260414", help="Start date YYYYMMDD"),
    end: str = typer.Option("20260529", help="End date YYYYMMDD"),
    sample_at: float = typer.Option(6.0, help="Earliest game-minute to sample from"),
):
    """Estimate the TRUE reversion beta from real playoff score paths (no odds).

    The trustworthy calibration: fits the model's blend against realized remaining
    scoring. No line model, so no circularity. Compare the fitted beta to the
    configured `model.beta` to tune it against real outcomes.
    """
    from .espn import ESPNClient
    from .study import load_playoff_games, reversion_fit

    games = load_playoff_games(ESPNClient(), start, end)
    if not games:
        console.print("[yellow]No completed playoff games found in that range.")
        return
    console.print(f"[bold]Fitting reversion on {len(games)} games ({start}..{end})[/bold]\n")
    for fr in reversion_fit(games, sample_at=sample_at):
        flavor = "full reversion" if fr.beta >= 0.85 else ("momentum" if fr.beta <= 0.3 else "partial")
        console.print(f"  {fr}   [dim]({flavor})[/dim]")
    cfg = Settings.load(DEFAULT_SETTINGS) if Path(DEFAULT_SETTINGS).exists() else Settings()
    console.print(f"\nConfigured model.beta = [bold]{cfg.model.beta}[/bold]  "
                  "(beta~1 => raise it toward full reversion)")


@app.command("sweep")
def sweep_cmd(
    start: str = typer.Option("20260414", help="Start date YYYYMMDD"),
    end: str = typer.Option("20260529", help="End date YYYYMMDD"),
    book_beta: float = typer.Option(0.3, help="Assumed book pace-chasing weight (0=naive, 1=sticky)"),
    sample_minutes: float = typer.Option(2.0, help="Sampling cadence in game-minutes"),
    min_bets: int = typer.Option(30, help="Drop threshold combos with fewer bets"),
    top: int = typer.Option(10, help="How many top combos to show"),
):
    """Sweep trigger thresholds across playoff games (line is MODELED — see caveat).

    Efficient grade-once/sweep-many over every market evaluation. WARNING: bets
    are graded against a *modeled* live line, so absolute ROI is sensitive to
    --book-beta and is NOT proof of edge. Use it for relative threshold behavior
    and where/when flags fire; use `reversion-fit` for trustworthy calibration.
    """
    from .espn import ESPNClient
    from .linemodel import game_config_from_history
    from .study import load_playoff_games
    from .sweep import Combo, build_records, evaluate_combo, sweep

    settings = Settings.load(DEFAULT_SETTINGS) if Path(DEFAULT_SETTINGS).exists() else Settings()
    games = [(h, game_config_from_history(h)) for h in load_playoff_games(ESPNClient(), start, end)]
    if not games:
        console.print("[yellow]No completed playoff games found in that range.")
        return
    recs = build_records(games, settings, book_beta=book_beta, sample_minutes=sample_minutes)
    console.print(f"[bold]{len(games)} games, {len(recs)} graded evaluations "
                  f"(book_beta={book_beta})[/bold]")
    console.print("[yellow]NOTE: live line is modeled; ROI below is illustrative, not real edge.[/yellow]\n")

    t = settings.triggers
    cur = Combo(t.pct_move_threshold, t.edge_pts_threshold, t.ev_threshold,
                t.min_minutes_remaining.full)
    crow = evaluate_combo(recs, cur)
    console.print(f"Current config [{cur.label()}]: {crow.bets} bets, "
                  f"{crow.wins}-{crow.losses}-{crow.pushes}, win {crow.win_rate:.1%}, "
                  f"ROI {crow.roi:+.1%}\n")

    table = Table(show_header=True, header_style="bold", title=f"Top {top} threshold combos by ROI")
    for col in ["move", "edge", "ev", "min", "bets", "W-L-P", "win%", "ROI", "by period"]:
        table.add_column(col)
    for r in sweep(recs, min_bets=min_bets)[:top]:
        c = r.combo
        periods = " ".join(f"{k}:{v[0]}" for k, v in sorted(r.by_period.items()))
        table.add_row(
            f"{c.pct_move:.0%}", f"{c.edge_pts:.0f}", f"{c.ev:+.0%}", f"{c.min_minutes_full:.0f}m",
            str(r.bets), f"{r.wins}-{r.losses}-{r.pushes}", f"{r.win_rate:.0%}",
            f"{r.roi:+.1%}", periods,
        )
    console.print(table)


@app.command("backtest-from-file")
def backtest_from_file(
    data: str = typer.Option(..., help="JSON odds dump (see tests/data/sas_okc_historical_sample.json)"),
    game: str = typer.Option(..., help="Game YAML with pregame baselines"),
    settings: str = typer.Option(DEFAULT_SETTINGS, help="Settings YAML"),
    out: str = typer.Option("docs/forward.json", help="Output path for forward panel JSON"),
):
    """Backtest the 9-point cadence against a pre-captured or mock odds JSON file.

    Reads live lines at each cadence mark from the JSON dump, runs the full
    engine pipeline, grades every flagged bet against the embedded finals, and
    writes the result to docs/forward.json so the dashboard panel updates.

    Seed file format: tests/data/sas_okc_historical_sample.json
    """
    from .historical import JsonFileSource, run_cadence_backtest
    from .cadence import timeout_marks
    from . import forward as fwd

    s, g = _load(settings, game)
    source = JsonFileSource(data)

    if g.event.id not in source.game_ids():
        console.print(f"[red]Event ID {g.event.id!r} not found in {data}. "
                      f"Available IDs: {source.game_ids()}")
        raise typer.Exit(1)

    ledger = run_cadence_backtest(source, g, s)

    fwd.dump(out, ledger, scope={
        "source": "json_file_sim",
        "data_file": data,
        "game": g.event.id,
        "matchup": f"{g.event.away_key} @ {g.event.home_key}",
        "cadence": "9-point timeout",
        "marks": timeout_marks(),
        "note": "mock/historical data — overwritten by live capture at tip-off",
    })

    sv = fwd.summarize(ledger)
    console.print(f"[green]Wrote {out}[/green]")
    console.print(
        f"  {sv['bets']} bets flagged  "
        f"[green]{sv['wins']}W[/green]-[red]{sv['losses']}L[/red]-{sv['pushes']}P  "
        f"({sv['pending']} pending)"
        + (f"  ROI [{'green' if sv['roi'] and sv['roi']>0 else 'red'}]"
           f"{sv['roi']:+.1%}[/]" if sv['roi'] is not None else "")
    )
    if sv['bets'] == 0:
        console.print(
            "[yellow]No signals fired. Check that pct_move_threshold vs the "
            "line moves in your data file — live lines must be ≥10% below pregame."
        )


@app.command("forward-export")
def forward_export(
    db: str = typer.Option("data/runtime/mrbet.sqlite", help="Observations SQLite from live runs"),
    out: str = typer.Option("docs/forward.json", help="Output JSON for the dashboard panel"),
    game: Optional[str] = typer.Option(None, help="Game YAML (for finals + matchup label)"),
):
    """Build the forward-test panel JSON from REAL captured bets in the log.

    The honest, free edge readout: real lines captured live -> CLV + record.
    Run after capturing games with `mrbet serve/run`, then commit docs/forward.json.
    """
    from . import forward as fwd

    finals_by_event, matchup_by_event = {}, {}
    if game:
        g = GameConfig.load(game)
        if getattr(g, "finals", None):
            finals_by_event[g.event.id] = g.finals
        matchup_by_event[g.event.id] = f"{g.event.away_key} @ {g.event.home_key}"
    if not Path(db).exists():
        console.print(f"[yellow]No log at {db}. Capture games first with `mrbet serve/run`.")
        ledger = {}
    else:
        ledger = fwd.build_from_sqlite(db, finals_by_event, matchup_by_event)
    fwd.dump(out, ledger, scope={"source": "live capture log", "db": db})
    s = fwd.summarize(ledger)
    console.print(f"[green]Wrote {out}[/green] — {s['bets']} real bets "
                  f"({s['wins']}-{s['losses']}-{s['pushes']}, {s['pending']} pending), "
                  f"CLV beat {s['clv_beat']}/{s['clv_graded']}")


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
