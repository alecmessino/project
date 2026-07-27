# Launch Skew Monitor

> *Harvesting skew in the digital asset tail*

A dashboard + monitoring harness for identifying the structural characteristics of the ~1-2% of crypto token launches that drive all net wealth — the "right tail" in a power-law distribution where 98% of tokens decay to zero.

This project is a **third sibling** to [`drift`](../src/drift) (equity-ETF momentum) and [`mrbet`](../src/mrbet) (NBA betting). It follows the same design pattern: **data source → processing engine → conjunctive trigger gate → signals + cost-aware evaluation**. It lives in its own directory, runs from its own `requirements.txt`, and does **not** cross-import from `drift` or `mrbet`.

---

## The Thesis

The **"4% Rule"** (derived from Hendrik Bessembinder's finding that 4% of stocks create all net wealth) applies with even greater extremity to cryptocurrency due to lower barriers to entry and higher variance. In crypto, this figure is likely closer to **1-2%**, with the remaining 98% of tokens decaying to zero (as seen in the 80-94% collapse of the 2025 launch cohort).

The goal is not to "pick winners" but to **"harvest the skew"** by identifying the structural characteristics of the 1-2% that survive.

> **Recent academic validation (2026):** Updated research applying Bessembinder's framework to digital assets confirms the thesis — cryptocurrency markets exhibit extreme positive skewness in the cross-section of buy-and-hold returns, with long-term wealth creation concentrated in a tiny minority of tokens.

### 1. The Theoretical Anchor: Extreme Positive Skewness

Cryptocurrency returns follow a Power Law distribution more aggressive than equities. Where Bessembinder found 57.4% of global stocks underperform T-bills, we hypothesize that **>95% of crypto assets fail to beat a benchmark of Bitcoin/ETH held in cold storage**.

### 2. The Crypto "Factors" (The DFA Translation)

We replace Fama-French equity factors with on-chain equivalents:

| Traditional Factor | Crypto Equivalent | Dashboard Metric |
|---|---|---|
| **Size** | Liquidity-Adjusted Cap | Market Cap < $50M, Liquidity > $5M |
| **Value** | MVRV Z-Score | MVRV < 1.0 → Capitulation Zone |
| **Quality** | Fee/Revenue + Holder Decentralization | Real Yield > Inflationary · Top-10 < 50% |
| **Investment** | Token Dilution Rate | (FDV − MC) / MC > 20% |
| **Momentum** | On-Chain Attention | Δ Active Addresses (Metcalfe's Law) |

### 3. The Empirical Filters (Launch Success)

- **Liquidity Depth**: Tokens with Day-1 liquidity > 10% of market cap.
- **Developer Activity**: Consistent code commits (GitHub) prior to TGE.
- **Vesting Cliffs**: Absence of massive VC unlock cliffs in the first 12 months.
- **Holder Decentralization**: Top-10 wallets < 70% of circulating supply.

---

## Dashboard Architecture: The "Launch Skew" Monitor v0.2

The dashboard is organized to **surface the 1-2% winners first**, with the three evidence modules below serving as supporting proof. At the top is a weighted **Conviction Score (0-100)** that ranks every tracked token by its structural probability of survival.

### Conviction Score (Top of Funnel)

A weighted 0-100 score where only tokens passing **all three gates** are eligible for flagging:

| Module | Weight | Key Metrics |
|---|---|---|
| **A — Day-1 Liquidity** | 40% | Turnover 30-60%, Holder Top-10 < 70%, Dev active, MVRV < 1.0 |
| **B — Vesting Wall** | 35% | Pressure < 2x, Emission/Revenue < 50x, Dilution < 20% |
| **C — Adoption Curve** | 25% | Power-law residual < −1σ, MVRV capitulation, User growth > 2x |

**STRIPE flag** at 70+ → the token clears all gates with strong metrics.

### Module A — Day-1 Liquidity Filter

**Metric**: Day-1 Turnover Ratio = 24h Volume / Initial Circulating Supply

- **>100%**: wash trading or weak hands → **AVOID**
- **30-60%**: organic turnover → **SWEET SPOT**
- **<30%**: illiquid → skip

**Actionable upgrade**: tracks **holder concentration** (top-10 wallet share) and **MVRV** alongside turnover. A token with 60% turnover but 85% holder concentration is a distribution trap.

```
Day-1 Turnover = (24h Trading Volume) / (Initial Circulating Supply × Launch Price)
Holder Concentration = % of supply in top-10 wallets
```

### Module B — Vesting Wall (Inflation Pressure Radar)

**Metric**: Next 30 Days Unlocks / Daily Average Volume

- **>2x daily volume**: sell-side pressure → **AVOID**

**Actionable upgrade**: adds **Emission-to-Revenue ratio** = (30d unlocks USD) / (24h protocol revenue). A 2x pressure is fine if protocol revenue is growing 3x — it's deadly if users are flat and unlocks dwarf real yield.

```
Inflation Pressure = Σ(Upcoming Unlocks in USD) / (Daily Average Volume in USD)
Emission-to-Revenue = (30d Unlocks USD) / (24h Protocol Revenue)
```

### Module C — Adoption Curve (Power Law + Cohort)

**Metric**: Plot `log(Active Addresses)` vs `log(Price)`. Fit a trendline (least-squares on log-log).

- **Below trendline**: trading undervalued relative to adoption → **BUY**
- **Above trendline**: overvalued relative to adoption → **SELL**

**Actionable upgrade**: overlays **MVRV Z-Score capitulation depth** (MVRV < 1.0 = average holder underwater) and a **historical cohort overlay** showing the trajectory of past survivors (the 1-2% that made it) vs. deadcoin averages.

```
Residual = log(Price) − (slope × log(Addresses) + intercept)
```

### Historical Cohort Overlay

The chart includes reference trajectories from **survivor tokens** (ETH L2 winner, DeFi blue chip, infra token) and a **deadcoin average** trajectory. A current token trading below the survivor trendline with a negative power-law residual is a potential skew-harvest candidate.

---

## Quick Start

```bash
# From repo root — demo mode, no API keys needed
python -m launch_skew.web
# → Dashboard at http://127.0.0.1:8765
```

The server ships with a **demo data provider** that synthesizes realistic token-launch metrics, including institutional market context from the EY-Parthenon / Coinbase 2026 Institutional Investor Survey. To use real APIs, set the keys in `config/launch_skew.yaml` and set `demo_mode: false`.

### Dependencies

```bash
pip install pyyaml pydantic
```

---

## File Layout

```
launch_skew/
├── __init__.py           # package root
├── config.py             # pydantic schema for config/launch_skew.yaml
├── config/
│   └── launch_skew.yaml  # all thresholds + source URLs
└── web/
    ├── __init__.py       # exports serve()
    ├── __main__.py       # entry point: python -m launch_skew.web
    ├── server.py         # stdlib HTTP server + demo provider (mirrors mrbet web/server.py)
    └── launch_skew.html  # the dashboard SPA (single file, vanilla JS)
```

---

## Configuration

All thresholds live in [`config/launch_skew.yaml`](config/launch_skew.yaml) — the dashboard and engine read from it. The schema is defined in [`config.py`](config.py) (pydantic).

| Section | Parameter | Default | Description |
|---|---|---|---|
| `module_a` | `turnover_sweet_min/max` | 0.30 / 0.60 | Day-1 turnover band for organic volume |
| `module_a` | `holder_concentration_warn_pct` | 70.0 | Top-10 wallet share above which = distribution trap |
| `module_a` | `min_protocol_revenue_24h` | 10000 | Min daily protocol fees for "real yield" |
| `module_b` | `pressure_threshold` | 2.0 | Unlock-to-volume ratio triggering sell pressure |
| `module_b` | `emission_to_revenue_warn` | 50.0 | Unlocks vs. daily protocol revenue (danger >50x) |
| `module_c` | `residual_threshold` | 1.0 | Std-dev threshold for undervalued/overvalued |
| `signal_gate` | `require_module_a/b/c_pass` | true | Conjunctive gate — all must pass |
| `signal_gate.strong_threshold` | `pressure_below` | 1.0 | <1x daily volume for STRONG tag |

---

## Status

This is an **active research project** at v0.2. The dashboard currently runs in **demo mode** with synthetic data. Real data integration (Dune/Messari/CoinGecko) is scaffolded in the config but requires API keys.

**Built with**: Python stdlib (HTTP server) + vanilla JS (dashboard). Zero frontend dependencies.

**Run tests**: `pytest tests/test_launch_skew.py -v`
