# fair-value-territory

MLB sibling of the NBA `mrbet` project — a mean-reversion **signal** engine for
live baseball totals. Flags +EV opportunities when the live total has dropped /
spiked far enough vs the pregame Vegas run line that the reversion model
disagrees with the book.

## Layout

```
.github/workflows/deploy.yml   GitHub Pages: serves docs/ to the public site
settings.yaml                  Live thresholds + model params (single source of truth)
triggers.py                    Core engine: state, math, evaluate_market, to_signal
scripts/build_chart_history.py Precompute Move%/Edge trajectories for the chart
docs/index.html                Dashboard UI (Chart.js dual-axis + polish)
docs/chart_history.json        Static data the chart reads (built by the script)
```

## State model

A standard regulation game has 18 half-innings. State is
`(inning, half, outs, away_runs, home_runs)`; `half_innings_elapsed()` blends
completed halves with a fractional credit for in-progress outs. The reversion
math anchors to the pregame total, scaled per half-inning.

## Getting started

```bash
# Generate the static chart data (and re-run any time settings.yaml changes):
pip install pyyaml
python scripts/build_chart_history.py
# -> docs/chart_history.json

# Push to a fresh GitHub repo, then enable Pages → Build from a branch →
#   Branch: master  Folder: /docs
# The .github/workflows/deploy.yml workflow takes over from there.
```

## Adapting from `mrbet`

| NBA concept (mrbet)                  | MLB equivalent (fair-value-territory) |
|--------------------------------------|----------------------------------------|
| 48-minute continuous clock           | 18 discrete half-innings               |
| Timeout cadence (6/9/12/18/21/24…)   | End of each half-inning                |
| points / total                       | runs / total                           |
| sigma_full = 11, sigma_team = 8 pts  | sigma_full = 2.6, sigma_team = 1.8 runs|
| pct_move 10%, edge 3 pts             | pct_move 12%, edge 2.5 runs            |
| H1 total (24 min)                    | F5 total (10 half-innings)             |

## Status

Scaffold. The engine math + dashboard framework are in place; a live poller
(MLB Stats API + odds source) is the next step.
