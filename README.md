# Driftwood & siblings — a signals monorepo

This repository holds **three independent "signal systems" that share one design**: an
interchangeable data-feed protocol → a streaming engine → a conjunctive trigger gate →
signals, plus a cost-aware backtest. They do **not** share business logic, and each can be
built, tested, and deployed on its own.

The headline project is **Driftwood**. The other two are its structural siblings applied to
sports markets.

| Project | What it is | Lives in | README |
|---|---|---|---|
| **🪵 Driftwood** | Equity-ETF **momentum** signal engine **+** the wealth-management research **website** (the front door, After-Tax Review, State Tax Atlas, Tax Diagnostic, Insights). | `src/drift/` (+ site source `src/drift/web/`) | **[src/drift/README.md](src/drift/README.md)** |
| 🏀 mrbet | Live **NBA totals** mean-reversion betting signals. | `src/mrbet/` | [src/mrbet/README.md](src/mrbet/README.md) |
| ⚾ the_third_turn | Live **MLB** pitcher-fatigue (TTOP) betting signals — self-contained, own deps/runtime. | `the_third_turn/` | [the_third_turn/README.md](the_third_turn/README.md) |

> The two betting projects **flag and recommend** — they never place bets. Driftwood
> publishes **illustrative modeling / research** — not investment, tax, or legal advice.

---

## Repository map

```
├── src/
│   ├── drift/          🪵 Driftwood — momentum engine + wealth site
│   │   ├── web/           site source: *.html templates + driftwood.css  →  built into docs/
│   │   ├── feed/          keyless price feeds (Yahoo, Polygon)
│   │   └── README.md
│   └── mrbet/          🏀 NBA mean-reversion engine
│       ├── odds/          pluggable odds providers
│       └── README.md
├── the_third_turn/     ⚾ MLB TTOP service (isolated: own README, config, tests, deps)
├── docs/               GitHub Pages site root (shared) — Driftwood pages + the mrbet
│                       betting dashboard (docs/mrbet.html); .nojekyll, committed build
├── config/             per-project config — see config/README.md
│   ├── drift.yaml         🪵 Driftwood
│   └── settings.yaml, games/, slow.yaml   🏀 mrbet
├── scripts/            build/ops helpers, mixed by project — see scripts/README.md
├── .github/workflows/  17 scheduled/CI workflows, mixed by project — see workflows/README.md
├── OPERATIONS.md       🪵 Driftwood operational runbook (build, deploy, compliance gates)
├── CLAUDE.md           contributor/agent guide to the whole monorepo
├── pyproject.toml      one package tree (src/), two console scripts: `drift`, `mrbet`
├── efficient_backtest.py, backtest_results.json   🏀 standalone mrbet research artifact
└── package.json        Node deps for the site's OG-card / screenshot scripts only
```

Both Python projects install from the **same** `pyproject.toml` (`packages.find` over
`src/`), exposing two CLIs — `drift` and `mrbet`. `the_third_turn` runs from its own folder
with its own `requirements.txt`.

## Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"          # installs both `drift` and `mrbet`
pytest -q                        # full suite (tests/)
```

**🪵 Driftwood** — engine + site (see [src/drift/README.md](src/drift/README.md), ops in
[OPERATIONS.md](OPERATIONS.md)):

```bash
drift rank      --config config/drift.yaml         # current cross-sectional ranking
drift tearsheet --config config/drift.yaml         # long-history, OOS, vs buy&hold
python scripts/sync_docs.py                         # re-render docs/ from src/drift/web templates
```

**🏀 mrbet** — NBA signals (see [src/mrbet/README.md](src/mrbet/README.md)):

```bash
mrbet simulate --game config/games/okc_sas_2026-05-28.yaml \
               --replay tests/data/replay_okc_sas.json     # keyless demo
```

**⚾ the_third_turn** — MLB service (see [the_third_turn/README.md](the_third_turn/README.md)):

```bash
cd the_third_turn && pip install -r requirements.txt && python live_engine.py
```

## Why one repo?

The three systems are the same harness pointed at different markets, so keeping them
together makes the shared design legible and lets improvements to the pattern flow between
them. They are deliberately decoupled — no cross-imports — so this is a monorepo of
siblings, not one program. If Driftwood ever needs to ship on its own, `src/drift/` + `docs/`
+ its `config`/`scripts`/workflows are a clean extraction.
