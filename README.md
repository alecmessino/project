# mrbet — Mean-Reversion Live Betting Signal System

Flags attractive **live** NBA totals / team-totals bets based on mean reversion: when
both teams start cold (poor shooting), the sportsbook over-drops the live total chasing
recent pace. Mean reversion says scoring regresses toward each side's pregame baseline,
so a depressed live total is frequently value on the **OVER** (and a spiked line is value
on the **UNDER**).

The system **flags and recommends** — it never places bets.

> ⚠️ For research / personal decision support. Sports-betting carries financial risk and
> is regulated by jurisdiction. Nothing here is a guarantee of profit; validate before you
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

# Live loop via The Odds API (needs ODDS_API_KEY)
mrbet run --game config/games/okc_sas_2026-05-28.yaml --provider theodds

# Manual entry on game night (type lines you see on Bovada)
mrbet run --game config/games/okc_sas_2026-05-28.yaml --provider manual

# Fire a test desktop + push notification
mrbet notify-test

# Grade logged signals against actual results + closing-line value
mrbet backtest --game config/games/okc_sas_2026-05-28.yaml \
               --results config/games/okc_sas_2026-05-28.results.example.yaml
```

### Data sources

- **The Odds API** (`theodds` provider) — live Bovada over/under prices for totals,
  team totals, and period markets. Set `ODDS_API_KEY`. Costs `markets × regions` credits
  per poll; the engine reads `x-requests-remaining` and warns when low.
- **ESPN scoreboard** (free, no key) — supplies the live game clock + score, which The
  Odds API does not expose.
- **Manual / replay** (`manual` provider) — enter lines by hand, or replay a JSON file.
  Robust fallback if the API's in-play coverage lags.

The provider layer is pluggable (`src/mrbet/odds/base.py`) so Betstamp / OpticOdds /
others can be added without touching the engine.

### Notifications

Push uses **ntfy.sh** by default (free, zero-config): set `NTFY_TOPIC` and subscribe to
that topic in the ntfy app. **Pushover** is used instead if `PUSHOVER_TOKEN`/`PUSHOVER_USER`
are set. Desktop uses `plyer` when installed, otherwise prints to the console.

## Does it actually have edge?

Be skeptical — a line dropping 10–15% isn't automatically value (a star may have sat, the
pace may genuinely be slower). Two safeguards are built in:

- **Honest EV, not just % drop.** Every flag requires the model to independently agree
  *and* positive EV at the offered odds.
- **Everything is logged.** `storage.py` writes every evaluation (flagged or not) to
  `data/runtime/mrbet.sqlite`, so you can grade flagged bets vs the closing line / result
  and tune `β`, `σ`, and the thresholds against real evidence before trusting it.
- **`mrbet backtest` grades that log.** It reports realized record / ROI vs the model's
  average EV, calibration (predicted win prob vs actual win rate), and **closing-line
  value** — whether you flagged a better number than the market closed at. CLV needs no
  final score and is the most robust evidence that the rule has edge rather than variance.

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

## Tests

```bash
pytest -q
```
