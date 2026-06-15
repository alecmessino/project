# Design — Multi-Game Tracking + Game Selection (College-Basketball Scale)

_Status: design (not yet implemented). Target: NCAAB season. Author handoff doc._

## 1. Problem

Today the system tracks **one game at a time**. The bottleneck is structural:

- `live_game_tracker.yml` uses `concurrency: { group: live-tracker, cancel-in-progress: false }` — only one tracker job ever runs.
- `game_sentinel._detect_live()` returns the **first** live game and dispatches a single tracker for it.
- `scripts/live_run.py` loops over **one** `MRBET_GAME`; `gh_pages_update.py` writes a **single-game** `docs/live_market_state.json`; `docs/forward.json` holds one game and resets when the game changes.

That is fine for the NBA Finals (one game a night). A college slate is **50–100+ simultaneous games**, and most aren't worth chasing. We need (a) concurrent tracking and (b) a selection layer that ranks which games deserve attention — seeded later by team offensive strength (KenPom-style).

## 2. Design principles

1. **One loop, many games — not one job per game.** GitHub Actions caps concurrent jobs and each job is a full checkout+install; 100 jobs all pushing to `master` would be a git-contention storm. A single long-running job that iterates all games per cycle is cheaper and has one writer.
2. **Lean on the feeds we already have.** One Bovada league **coupon** call already returns the *whole slate's* full-game totals (`bovada_feed._coupon_url(slug)`), and one ESPN **scoreboard** call returns every game's clock+score. So per cycle the marginal cost of N games is ~**2 HTTP calls total**, not 2×N — the rest is pure CPU.
3. **Selection is a separate, pluggable layer.** Ranking which games to chase must not entangle the reversion math. Team-strength ratings plug in behind an interface so KenPom (or Torvik, or anything) drops in later without touching the engine.
4. **Reuse the discipline we built.** Per-game execution locks (dedup / hysteresis / hard-cap / cooldown), the volatility gate, CLV capture, and the season ledger are all already per-game-keyed — extend them to a registry, don't rewrite them.
5. **Phase it.** Ship concurrent tracking first (works with zero ratings), then ranking, then the KenPom data source.

## 3. Architecture

### 3.1 The slate loop (`scripts/slate_run.py` — multi-game analog of `live_run.py`)

Per cycle, for each tracked league:

```
coupon   = bovada_feed.fetch_coupon(league)          # 1 call → all games' lines
scoreboard = espn scoreboard(league)                 # 1 call → all clocks/scores
for each game live on BOTH:
    match coupon event ↔ ESPN event ↔ config baseline (exact bovada_event_id first)
    derive GameState (clock/score from ESPN, lines from coupon)
    engine.process_snapshot → evaluations (full / H1 / H2 totals)
    triggers → signals, with the per-game execution lock + volatility gate
selection.rank(all live evaluations, ratings) → chase scores
write docs/live_market_state.json  (MULTI-game payload, below)
fire alerts only for games in the top-K chase set that clear the execution rules
push docs/  (ONE writer → no contention)
grade + archive any game ESPN now reports final (per-game, others keep running)
```

This is the existing `gh_pages_update.py` pipeline lifted from "one game" to "loop over the live set." The reversion/probability/triggers modules are unchanged — they already operate per `(baseline, GameState)`.

### 3.2 HTTP / resource budget

| | Per cycle |
|---|---|
| Bovada coupon | 1 per league |
| ESPN scoreboard | 1 per league |
| Bovada per-event scores | **avoid** — drive the live clock from ESPN scoreboard (already the canonical clock source; see CLAUDE.md gotcha) |

A 100-game slate is ~4 calls/cycle (2 leagues × coupon+scoreboard) + CPU. Cycle stays ~60–90s. A single GitHub Actions job (6h cap) plus the existing **self-re-arm watchdog pattern** (`sentinel_watch.py`) covers a ~12h slate by relaunching itself.

### 3.3 Concurrency control

- Replace the single `live-tracker` slot: the slate runner is **one** job (`concurrency: slate-run`, `cancel-in-progress: true`, same as the watchdog). No per-game jobs.
- The sentinel/watchdog's role shifts from "find the first live game and dispatch a tracker" to "ensure the slate runner is up whenever ≥1 game is live." `_detect_live` becomes `_any_live(league)`.

## 4. Selection / ranking layer (`src/mrbet/selection.py`)

A pure, testable scorer that ranks live games so we chase the best and mute the rest.

```python
@dataclass
class ChaseScore:
    game_id: str
    score: float          # 0..1, higher = chase harder
    components: dict       # for transparency on the dashboard

def rank(evals: list[Evaluation], ratings: "TeamRatings",
         weights: SelectionWeights) -> list[ChaseScore]: ...
```

**Chase score** = weighted blend (weights live in `settings.yaml`, tunable):

| Signal | Source | Rationale |
|---|---|---|
| Line-drop magnitude (`pct_move`) | live vs pregame | the core reversion trigger |
| Model edge / EV | `Evaluation.edge_pts`, `.ev` | the math agrees |
| Time remaining | `GameState` | enough clock for reversion to play out |
| **Offensive strength** | `TeamRatings` (KenPom) | strong offenses regress cold stretches upward more reliably — a higher-confidence OVER prior |
| Volatility (penalty) | rolling CV gate | suppress noisy lines |

The **active chase set** = top-K by score (K in settings, e.g. 12) AND above a floor. Alerts fire only for the chase set; the dashboard shows all live games but sorts/【highlights the chase set.

## 5. Team ratings — the KenPom extension point (build later)

Behind a protocol so the data source is swappable and ships **inert** now:

```python
class TeamRatings(Protocol):
    def adj_offense(self, team_key: str) -> float | None: ...   # KenPom AdjO
    def tempo(self, team_key: str) -> float | None: ...
    def rating(self, team_key: str) -> float | None: ...        # composite

class NeutralRatings:        # default — every team average; selection ignores it
    ...                      # ships now so nothing depends on KenPom existing

class KenPomRatings:         # BUILD LATER
    # load a CSV/snapshot (or scrape) keyed by team; map KenPom names ↔ our team_keys.
    # config: ratings_path, refresh cadence. The name-mapping table is the real work.
```

How ratings feed the system, two levels (start with the first):

1. **Selection only (Phase 3a):** offensive strength is one term in the chase score — it *highlights* games, doesn't change EV. Matches your stated intent ("highlight which games are worth chasing"). Safe.
2. **Baseline prior (Phase 3b, optional):** blend a KenPom-projected total (AdjO×tempo, pace-adjusted, vs opponent) into the pregame baseline `T_pre` / reversion target. More powerful, changes EV — gate behind validation.

## 6. State at scale

- **Live payload** (`docs/live_market_state.json`) becomes multi-game:
  ```json
  { "updated": "...", "chase": ["dukeunc","..."],
    "games": { "<game_id>": { "header": {...}, "rows": [...], "exec": {...},
                              "chase_score": 0.81, "chase_components": {...} } } }
  ```
- **Forward / exec state**: per-game already keyed. Move from one `forward.json` to a registry — `docs/forward/<game_id>.json` (or a dict keyed by `game_id`) so games don't clobber each other (we hit exactly this bug with the single file earlier). The execution `alert_state` becomes `{game_id: {...}}`.
- **Grading**: each game grades at its own buzzer (`espn_is_final` per game); `forward.append_season(..., game_id, ...)` is already idempotent per game, so finished games append independently while others keep streaming.
- **Season ledger + `SEASON_LEDGER.md`**: unchanged — they already roll up per game across leagues.

## 7. Dashboard

`docs/index.html` gains a **slate board**: a sortable table of live games (matchup, clock, line vs pregame, model edge/EV, chase score, exec-lock state), ranked by chase score with the chase set highlighted. Clicking a row drills into the existing single-game detail view (markets table + chart + exec locks), which becomes a per-game sub-render of the multi-game payload.

## 8. Phased rollout

| Phase | Scope | Risk |
|---|---|---|
| **1. Concurrent tracking** | `slate_run.py` one-loop multi-game; multi-game payload; per-game forward/exec registry; dashboard slate board; sentinel → "slate up if any live". Track all live (simple cap). | Med — schema + dashboard change |
| **2. Selection/ranking** | `selection.py` chase score from line-move/edge/EV/time/vol; top-K alert gating; weights in settings. | Low — additive, pure |
| **3a. Ratings hook** | `TeamRatings` protocol + `NeutralRatings`; wire offense term into chase score (inert until data). | Low |
| **3b. KenPom adapter** | `KenPomRatings` loader + team-name mapping; optional baseline prior. _Built in later._ | Med — name mapping, validation |

## 9. Decisions needed before Phase 1

1. **Per-game files vs one dict** for forward/exec state (`docs/forward/<id>.json` vs a keyed `forward.json`). Recommend per-game files — cleaner, no giant single blob, easy to prune.
2. **Alert volume policy**: cap alerts to top-K chase set only, or alert any +EV signal? Recommend top-K to control Discord noise on big slates.
3. **Men's only, or women's (NCAAW) too?** Women's college is 4×10 quarters (different period model — closer to WNBA). Scaffold is men's (halves) today.
4. **Sigma calibration plan**: log a few weeks of NCAAB before trusting EV; until then run in "shadow" (capture + dashboard, no Discord).

## 10. Risks

- **Team identity at scale** — ~360 D1 teams; Bovada↔ESPN↔KenPom name matching ("St." vs "State", abbreviations) is the highest-effort/most-error-prone piece. Needs a maintained mapping table with a fallback + an "unmatched" report.
- **Untuned college sigmas** → mis-stated EV. Mitigate with the shadow period (#9.4).
- **Payload size** — 100 games × full row sets could bloat `live_market_state.json`; trim per-game rows to essentials and keep history client-side.
- **Soft-line noise** — college lines move more; the volatility gate matters more here, not less.
