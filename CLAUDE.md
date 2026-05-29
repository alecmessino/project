# CLAUDE.md

Guidance for working in this repo.

## What this is

`mrbet` is a mean-reversion **signal** system for live NBA totals / team totals. It flags
+EV opportunities (with desktop/push alerts) when the live line over-drops vs the pregame
baseline relative to a reversion model. It does **not** place bets.

## Commands

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"          # add ,desktop for native notifications
pytest -q                        # run all tests
mrbet simulate --game config/games/okc_sas_2026-05-28.yaml --replay tests/data/replay_okc_sas.json
```

## Architecture (data flow)

`odds/<provider>` yields `Snapshot(state, lines)` → `engine.Engine.process_snapshot`
matches each live `MarketLine` to its pregame `Baseline`, derives the per-period
`GameState`, and calls `triggers.evaluate_market` → `Evaluation`; `triggers.to_signal`
applies the thresholds → `Signal`. The engine logs every evaluation (`storage`) and
notifies on new/strengthened signals (`notify`).

## Conventions

- **Math modules stay pure** (`reversion.py`, `probability.py`) — no I/O, fully unit-tested.
- **Runtime objects are dataclasses** (`models.py`); **config is pydantic** (`config.py`).
- **Providers are interchangeable** behind the `OddsProvider` protocol (`odds/base.py`);
  add new sources there, don't special-case them in the engine.
- All thresholds/params live in `config/settings.yaml` — don't hardcode them.
- Away/home mapping for team totals comes from the game YAML (`away_key`/`home_key`).

## Gotchas

- The Odds API has no game clock; the live clock/score comes from ESPN's scoreboard.
- Live derivation only supports FULL/H1 and team totals from a cumulative score; per-quarter
  markets need explicit per-period snapshots (replay/manual path).
- `β`, `σ_full`, `σ_team`, and the trigger thresholds are unvalidated defaults — tune them
  against logged data before trusting live output.
