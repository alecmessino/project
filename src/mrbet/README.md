# mrbet — Mean-Reversion Live Betting Signal System

> Part of the [monorepo](../../README.md); sibling projects: [`drift`/Driftwood](../drift/README.md)
> (equity momentum + wealth site) and [`the_third_turn`](../../the_third_turn/README.md) (MLB).
> Paths below are relative to the **repo root** — run the commands from there.

Flags attractive **live** NBA totals / team-totals bets based on mean reversion: when both
teams start cold (poor shooting), the sportsbook over-drops the live total chasing recent
pace. Mean reversion says scoring regresses toward each side's pregame baseline, so a
depressed live total is frequently value on the **OVER** (and a spiked line is value on
the **UNDER**).

The system **flags and recommends** — it never places bets.

> ⚠️ For research / personal decision support. Sports-betting carries financial risk and is
> regulated by jurisdiction. Nothing here is a guarantee of profit; validate before you
> trust it (see *Does it actually have edge?*).

## How it works

For any total market with pregame baseline `T_pre` over a period of length `L` minutes:

```
fair_final = points_so_far + minutes_remaining * [ β·(T_pre/L) + (1-β)·(current_pace) ]
```

- `β` (default **0.7**) is the reversion weight: `β=1` → remaining play scores at the
  pregame rate (full reversion); `β=0` → continues at the current pace.
- The final total is modeled `~ Normal(fair_final, σ·√(remaining_share))`, giving a
  probability for each side, then **EV** at the offered American odds and a
  **fractional-Kelly** stake.

A bet is **flagged** only when *all* hold (configurable in `config/settings.yaml`):

1. the live line moved ≥ **10%** vs pregame *in the helpful direction*,
2. the model independently sees ≥ **3.0 pts** of edge,
3. **EV ≥ 0** at the offered odds (tagged 🔥 STRONG at ≥ +3%),
4. enough time remains in the period (full 6 / half 4 / quarter 3 min).

The big % move alone never fires a bet — the model must agree *and* the price must be
positive EV. That is the guard against chasing noise.

## Install

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,desktop]"      # desktop extra adds native notifications
cp .env.example .env                 # then fill in keys/topics
```

## Usage

```bash
# Show the pregame anchors for a game
mrbet baseline --game config/games/okc_sas_2026-05-28.yaml

# Replay a recorded/synthetic sequence through the engine (no network, no key)
mrbet simulate --game config/games/okc_sas_2026-05-28.yaml \
               --replay tests/data/replay_okc_sas.json

# Live WEB DASHBOARD — auto-polls, no manual entry (open http://127.0.0.1:8000)
mrbet serve --game config/games/okc_sas_2026-05-28.yaml --provider theodds
mrbet serve --game config/games/okc_sas_2026-05-28.yaml \
            --provider replay --replay tests/data/replay_okc_sas.json   # keyless demo

# Live loop via The Odds API (needs ODDS_API_KEY)
mrbet run --game config/games/okc_sas_2026-05-28.yaml --provider theodds

# Manual entry on game night (type lines you see on Bovada)
mrbet run --game config/games/okc_sas_2026-05-28.yaml --provider manual

# Fire a test desktop + push notification
mrbet notify-test

# Grade logged signals against actual results + closing-line value
mrbet backtest --game config/games/okc_sas_2026-05-28.yaml \
               --results config/games/okc_sas_2026-05-28.results.example.yaml

# Calibrate beta against real playoff outcomes (free ESPN data, no odds, no key)
mrbet reversion-fit --start 20260414 --end 20260529

# Sweep trigger thresholds across playoff games (line is MODELED — see caveat below)
mrbet sweep --start 20260414 --end 20260529 --book-beta 0.3
```

### Calibration & backtesting

Two tools pull every completed game from ESPN's free scoreboard (no key) and tune the
model against **real** outcomes:

- **`mrbet reversion-fit`** — the *trustworthy* calibration. It least-squares fits the
  model's own blend (`remaining_rate = β·pregame_rate + (1-β)·elapsed_pace`) against the
  realized remaining scoring of each game. No line model, so **no circularity**. Across the
  2026 playoffs it returns **β ≈ 1.0** (full reversion to the pregame rate) with R² up to
  0.87 vs a momentum baseline — i.e. early pace carries almost no signal for the rest of the
  game, and the configured `β = 0.70` is too conservative.
- **`mrbet sweep`** — grade-once/sweep-many over a threshold grid (move × edge × EV ×
  min-minutes), reporting record/ROI/where-flags-fire per combo. ⚠️ **The live line is
  *modeled*** (we don't have historical in-play book lines), so absolute ROI is an artifact
  of the assumed `--book-beta` and is **not** proof of edge. Use it for *relative* threshold
  behavior; use `reversion-fit` for real calibration.

### Data sources

- **The Odds API** (`theodds` provider) — live over/under prices for totals, team totals,
  and period markets. Set `ODDS_API_KEY`. Requests a whole **region** in one call, then
  picks the line from preferred books in order (default Bovada first), falling back to a
  **consensus** line. Set `engine.cadence: timeout` to spend a paid odds fetch only at the
  timeout/quarter-break marks (watching the free ESPN clock in between) — ~17× fewer credits
  while keeping 86% of opportunities.
- **ESPN scoreboard** (free, no key) — supplies the live game clock + score, which The Odds
  API does not expose.
- **Manual / replay** (`manual` provider) — enter lines by hand, or replay a JSON file.

The provider layer is pluggable (`src/mrbet/odds/base.py`) so Betstamp / OpticOdds / others
can be added without touching the engine.

### Notifications

Push uses **ntfy.sh** by default (free, zero-config): set `NTFY_TOPIC` and subscribe. **Pushover**
is used instead if `PUSHOVER_TOKEN`/`PUSHOVER_USER` are set. Desktop uses `plyer` when
installed, otherwise prints to the console. Each signal alerts once and re-alerts only if
its EV improves materially.

## Does it actually have edge?

Be skeptical — a line dropping 10–15% isn't automatically value (a star may have sat, the
pace may genuinely be slower). Two safeguards are built in:

- **Honest EV, not just % drop.** Every flag requires the model to independently agree
  *and* positive EV at the offered odds.
- **Everything is logged.** `storage.py` writes every evaluation to `data/runtime/mrbet.sqlite`,
  so you can grade flagged bets vs the closing line / result and tune `β`, `σ`, and the
  thresholds against real evidence.
- **`mrbet backtest` grades that log** — realized record / ROI, calibration, and
  **closing-line value** (the most robust evidence of edge vs variance).

## Layout

```
config/settings.yaml          # thresholds, β, σ, bankroll, kelly, markets, poll interval
config/games/*.yaml           # per-game pregame baselines (+ Bovada odds ladder)
src/mrbet/reversion.py        # the projection math
src/mrbet/probability.py      # odds <-> prob, EV, Kelly
src/mrbet/triggers.py         # evaluate a market -> Signal if thresholds clear
src/mrbet/engine.py           # poll -> evaluate -> flag -> notify -> log
src/mrbet/odds/               # provider layer (theodds, manual, base protocol)
src/mrbet/notify.py           # desktop + push, with de-duplication
tests/                        # unit + end-to-end replay tests
```

See [`methodology.md`](./methodology.md) for the modeling notes. Root-level
`efficient_backtest.py` + `backtest_results.json` are a standalone mrbet research artifact.

## Tests

```bash
pytest -q
```
