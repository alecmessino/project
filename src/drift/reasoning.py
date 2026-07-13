"""The Atlas reasoning graph — composable knowledge primitives (PUBLISHING_SPEC §16–17).

Driftwood is three layers: FACTS (drift.state_facts) → REASONING (this module) → OUTPUTS (Atlas pages,
comparisons, Crossing Briefs, the Opportunity Register, the Household Record, the Annual Review, future
AI). Everything derives from the first two.

The reasoning layer is a GRAPH, not a chain. Each Impact, Decision Signal, Coordination Priority, and
Action is an ADDRESSABLE, STRUCTURED object — a node carrying typed reference edges to the other layers
(never prose). A node is a canonical, state-independent definition; a state's reasoning is that node
INSTANTIATED against its environment, with a stable per-state id (e.g. "IL:signal:estate_exposure").
Presented top-to-bottom on a page —

    environment → household impact → DECISION FRAMEWORK → coordination priorities → action register

— but stored as a graph so any consumer can traverse it: a page renders the objects, the Household
Record references them by id, an AI walks the edges. No consumer re-authors the reasoning.

Every node is organised from EXISTING approved Driftwood thinking (the environment dimensions, the Tax
Diagnostic, the State Context, the Moving States ripple, the coordination philosophy) — clarity, not
new philosophy.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .state_facts import RATES, ESTATE
from .leakage import STATE_ALPHA, coordination_opportunity_per_m, fmt_usd

# The reasoning-chain order — the Decision Framework is the centrepiece (§16).
CHAIN = ("environment", "impact", "framework", "coordination", "actions")

_FED_ESTATE_EXEMPTION = 13_990_000
_ORDER = {lvl: i for i, lvl in enumerate(("none", "low", "moderate", "high", "severe"))}


@dataclass
class _Ctx:
    """The binding context: a state's numeric facts + environment record, plus the signal levels
    accumulated as the framework evaluates (so priorities and actions can read them by id)."""
    code: str
    lt: float
    rate_display: str
    estate: dict | None
    env: dict
    levels: dict = field(default_factory=dict)

    def level(self, signal_id: str) -> str:
        return self.levels.get(signal_id, "none")

    def at_least(self, signal_id: str, level: str) -> bool:
        return _ORDER.get(self.level(signal_id), 0) >= _ORDER[level]

    def node_id(self, kind: str, prim_id: str) -> str:
        return f"{self.code}:{kind}:{prim_id}"

    def citations_for(self, dims) -> list[dict]:
        """Traverse to the canonical citations on the environment dimensions a node reads (an edge to
        the Facts layer), so a reasoning object carries provenance without restating it."""
        out = []
        for d in dims:
            for c in (self.env.get(d) or {}).get("citation") or []:
                if c not in out:
                    out.append(c)
        return out


# ── Layer 3 · DECISION FRAMEWORK — signals (the centrepiece: how to evaluate the environment) ──────
# Each signal is a structured node: it reads environment dimensions, evaluates to a level + reading,
# and edges to the coordination priority it opens. `evaluate` returns (level, reading).
def _s_rate_pressure(ctx: _Ctx):
    if ctx.lt <= 0:
        return "none", "No state tax on gains — every realized gain keeps its full federal-only outcome."
    lvl = "low" if ctx.lt < 0.04 else "moderate" if ctx.lt < 0.07 else "high" if ctx.lt < 0.10 else "severe"
    return lvl, f"The state takes {ctx.rate_display} of every long-term gain at the top — {lvl} drag on what a realized return keeps."


def _s_estate_exposure(ctx: _Ctx):
    e = ctx.estate
    if not e:
        return "none", "No state estate or inheritance tax — only the federal estate tax reaches the estate."
    if e["regime"] == "inheritance":
        return "moderate", ("An inheritance tax applies by the heir's relationship, not the estate's size — "
                            "exposure turns on who inherits, and close heirs are usually exempt.")
    exm = e.get("exemption_usd") or 0
    steep = bool(e.get("cliff")) or exm <= 4_000_000
    lvl = "severe" if steep else "high" if exm < _FED_ESTATE_EXEMPTION else "moderate"
    cliff = " a cliff then taxes the whole estate, not just the excess;" if e.get("cliff") else ""
    return lvl, (f"A state estate tax exempts only {e['exemption_display']} — far below the federal "
                 f"~$14M;{cliff} {lvl} exposure at death that federal-only planning misses.")


def _s_harvest_leverage(ctx: _Ctx):
    if ctx.lt <= 0:
        if "losses still deduct" in (ctx.env.get("cg") or {}).get("note", ""):
            return "moderate", ("Gains are exempt here, yet a capital loss still deducts against income — "
                                "a rare one-sided value that keeps harvesting worthwhile.")
        return "low", "With no state tax on gains, a harvested loss recovers only its federal value — the state adds no rate for it to offset."
    loss_regime = (ctx.env.get("loss") or {}).get("regime")
    if loss_regime in ("nonconforming", "none"):
        return "moderate", ("The rate rewards harvesting, but non-conforming loss rules can strand a banked "
                            "loss before it reaches the state bill — the timing has to be coordinated.")
    lvl = "high" if ctx.lt >= 0.06 else "moderate"
    return lvl, f"A harvested loss is worth the {ctx.rate_display} state rate it offsets, on top of federal — {lvl} harvesting leverage."


def _s_mobility_value(ctx: _Ctx):
    if ctx.lt <= 0 and not ctx.estate:
        return "none", "Already a no-income-tax, no-estate-tax state — the destination other households move toward, not from."
    if ctx.lt >= 0.09 or (ctx.estate and (ctx.estate.get("cliff") or (ctx.estate.get("exemption_usd") or 0) < _FED_ESTATE_EXEMPTION)):
        return "high", "Both the rate and the estate regime make relocation genuinely valuable — but domicile is a fact pattern, not a mailing address."
    if ctx.lt >= 0.05:
        return "moderate", "The rate makes a change of residency worth modelling against the life and family cost of moving."
    return "low", "The rate is modest — residency is unlikely to be the lever that moves the household's outcome."


def _s_basis_coordination(ctx: _Ctx):
    su = (ctx.env.get("stepup") or {}).get("regime")
    if su == "community":
        return "high", "Community-property state: community assets get a FULL step-up at the first death — title them so the survivor keeps that basis."
    if su == "optin":
        return "moderate", "An elective community-property trust can unlock a full first-death step-up here — worth electing before it is needed."
    if su == "udcprda":
        return "low", "Adopted the UDCPRDA — community-property basis treatment can be imported by trust for couples who plan for it."
    return "low", "Common-law basis: only the decedent's half steps up at the first death — plan titling so the survivor is not left with low-basis lots."


FRAMEWORK_SIGNALS = [
    {"id": "rate_pressure", "title": "Rate pressure", "reads": ["cg"], "opens": ["asset_location"],
     "question": "How much does the state erode each realized gain?", "evaluate": _s_rate_pressure},
    {"id": "estate_exposure", "title": "Estate exposure", "reads": ["estate"], "opens": ["estate_structure"],
     "question": "Does the state tax the estate below the federal threshold, and how steeply?", "evaluate": _s_estate_exposure},
    {"id": "harvest_leverage", "title": "Harvesting leverage", "reads": ["cg", "loss"], "opens": ["harvest_coordination"],
     "question": "How much is a harvested loss worth here?", "evaluate": _s_harvest_leverage},
    {"id": "mobility_value", "title": "Mobility value", "reads": ["cg", "estate"], "opens": ["residency_planning"],
     "question": "How much could a change of residency be worth?", "evaluate": _s_mobility_value},
    {"id": "basis_coordination", "title": "Basis coordination", "reads": ["stepup"], "opens": ["basis_titling"],
     "question": "What basis-step-up opportunity does the marital-property regime create?", "evaluate": _s_basis_coordination},
]

# ── Layer 4 · COORDINATION PRIORITIES — the operating-system domains each signal opens ─────────────
# Structured nodes with edges: `trigger` (which signal at what level activates it), `related_signals`,
# `related_actions`, `affected_dimensions`, and a `priority` rank. Not advisor copy — the household's
# coordination map. Renamed from "planning considerations" (§17).
COORDINATION_PRIORITIES = [
    {"id": "residency_planning", "title": "Residency & domicile", "domain": "Residency", "coordinate_with": "advisor + CPA",
     "trigger": ("mobility_value", "moderate"), "affected_dimensions": ["cg", "estate"], "priority": 1,
     "related_signals": ["mobility_value"], "related_actions": ["confirm_domicile"],
     "rationale": "Whether — and how — a change of domicile is worth pursuing, and the facts (days, home, ties) that make it real rather than nominal.",
     "crossing_question": "Which domicile facts — days present, primary home, the ties that follow you — will substantiate the move if a former state examines it?"},
    {"id": "estate_structure", "title": "Estate structure", "domain": "Estate", "coordinate_with": "estate attorney",
     "trigger": ("estate_exposure", "high"), "affected_dimensions": ["estate"], "priority": 1,
     "related_signals": ["estate_exposure"], "related_actions": ["review_estate_titling"],
     "rationale": "Whether the state's estate exposure warrants credit-shelter / QTIP titling or lifetime gifting to move value below the state threshold.",
     "crossing_question": "Does the existing estate plan still assume the prior state's exemption and rate — and should any trust now be governed elsewhere?"},
    {"id": "basis_titling", "title": "Asset titling for step-up", "domain": "Estate", "coordinate_with": "estate attorney",
     "trigger": ("basis_coordination", "moderate"), "affected_dimensions": ["stepup"], "priority": 2,
     "related_signals": ["basis_coordination"], "related_actions": ["set_basis_titling"],
     "rationale": "Titling assets to capture the fullest basis step-up the marital-property regime allows at the first death.",
     "crossing_question": "Is the household titled to capture the fullest first-death step-up the new marital-property regime allows?"},
    {"id": "harvest_coordination", "title": "Loss harvesting", "domain": "Portfolio", "coordinate_with": "advisor + CPA",
     "trigger": ("harvest_leverage", "moderate"), "affected_dimensions": ["cg", "loss"], "priority": 2,
     "related_signals": ["harvest_leverage"], "related_actions": ["set_harvest_cadence"],
     "rationale": "Setting a harvesting cadence that captures the state rate a banked loss offsets, sequenced against the state's loss-carryforward rules.",
     "crossing_question": "Does the harvesting cadence still fit the new state's rate and loss-carryforward rules?"},
    {"id": "asset_location", "title": "Asset location", "domain": "Portfolio", "coordinate_with": "advisor",
     "trigger": ("rate_pressure", "low"), "affected_dimensions": ["cg"], "priority": 3,
     "related_signals": ["rate_pressure"], "related_actions": ["place_sleeves"],
     "rationale": "Placing the high-turnover sleeve in tax-advantaged accounts so the state's rate falls on the least of the household's realized gains.",
     "crossing_question": "Does the investment policy statement still assume the prior tax environment when it places the high-turnover sleeve?"},
]

# ── Layer 5 · ACTION REGISTER — sequenced next steps, each edged to a coordination priority ────────
# `crossing_phase` sequences an action relative to a relocation (before · during · after the move) —
# structured timing the Crossing Brief reads; state pages and the Comparison ignore it.
ACTIONS = [
    {"id": "confirm_domicile", "title": "Model domicile alternatives", "owner": "advisor", "priority_ref": "residency_planning",
     "related_signals": ["mobility_value"], "crossing_phase": "before",
     "step": "Model the after-tax and estate outcome of the current vs a lower-tax domicile, and list the domicile facts to establish before any move."},
    {"id": "review_estate_titling", "title": "Review estate titling", "owner": "estate attorney", "priority_ref": "estate_structure",
     "related_signals": ["estate_exposure"], "crossing_phase": "after",
     "step": "Review titling and the credit-shelter / gifting options against the state estate threshold; quantify the exposure at the household's net worth."},
    {"id": "set_basis_titling", "title": "Set basis titling", "owner": "estate attorney", "priority_ref": "basis_titling",
     "related_signals": ["basis_coordination"], "crossing_phase": "after",
     "step": "Title (or elect the trust) to capture the fullest first-death basis step-up the regime allows."},
    {"id": "set_harvest_cadence", "title": "Set harvesting cadence", "owner": "advisor", "priority_ref": "harvest_coordination",
     "related_signals": ["harvest_leverage"], "crossing_phase": "after",
     "step": "Set the annual loss-harvesting cadence and confirm it clears the state's carryforward rules."},
    {"id": "place_sleeves", "title": "Place the sleeves", "owner": "advisor", "priority_ref": "asset_location",
     "related_signals": ["rate_pressure"], "crossing_phase": "after",
     "step": "Locate the high-turnover sleeve into tax-advantaged accounts and confirm the taxable book is the low-turnover core."},
]

# Registries — every primitive is addressable by id (the canonical definition consumers reference).
SIGNAL_BY_ID = {s["id"]: s for s in FRAMEWORK_SIGNALS}
PRIORITY_BY_ID = {p["id"]: p for p in COORDINATION_PRIORITIES}
ACTION_BY_ID = {a["id"]: a for a in ACTIONS}


def build_impact(ctx: _Ctx) -> dict:
    """Layer 2 — the Household Impact node: what the environment does to a household's after-tax
    system, sourced from the Tax Diagnostic (STATE_ALPHA), edged to the dimensions it summarises."""
    a = STATE_ALPHA.get(ctx.code)
    reading = (
        (f"This environment leaks after-tax return on an uncoordinated book; coordinating how the portfolio is "
         f"built and run against it is the opportunity. On an illustrative 30-year path that is worth about "
         f"~{fmt_usd(coordination_opportunity_per_m(a['alpha']))}/yr for every $1M of taxable assets here — "
         f"about +{a['alpha']:.1f}%/yr modeled ({a['before']:.1f}% → {a['after']:.1f}%/yr kept). The household's "
         f"own figure depends on bracket, holdings, and residency; the Tax Diagnostic computes it.") if a else
        "The household's after-tax figure depends on bracket, holdings, and residency; the Tax Diagnostic computes it.")
    return {"node_id": ctx.node_id("impact", "after_tax"), "id": "after_tax_impact", "kind": "impact",
            "title": "After-tax impact", "inputs": ["state", "bracket", "portfolio"],
            "affected_dimensions": ["cg", "loss"], "diagnostic_ref": f"leakage.html?state={ctx.code}",
            "illustrative_alpha_pct": a["alpha"] if a else None,
            "before_pct": a["before"] if a else None, "after_pct": a["after"] if a else None,
            "reading": reading}


def build_framework(ctx: _Ctx) -> list[dict]:
    """Layer 3 — evaluate every Decision Framework signal, recording each level so downstream nodes can
    read it, and returning structured signal nodes with their edges + traversed citations."""
    out = []
    for sig in FRAMEWORK_SIGNALS:
        level, reading = sig["evaluate"](ctx)
        ctx.levels[sig["id"]] = level
        out.append({"node_id": ctx.node_id("signal", sig["id"]), "id": sig["id"], "kind": "signal",
                    "title": sig["title"], "question": sig["question"], "reads": sig["reads"],
                    "opens": sig["opens"], "level": level, "score": _ORDER[level], "reading": reading,
                    "citations": ctx.citations_for(sig["reads"])})
    return out


def build_coordination(ctx: _Ctx) -> list[dict]:
    """Layer 4 — the coordination priorities whose signal triggers fired, as structured nodes with
    their edges (related signals/actions, affected dimensions, priority rank)."""
    out = []
    for p in COORDINATION_PRIORITIES:
        sig_id, min_level = p["trigger"]
        if ctx.at_least(sig_id, min_level):
            out.append({"node_id": ctx.node_id("priority", p["id"]), "id": p["id"], "kind": "coordination",
                        "title": p["title"], "domain": p["domain"], "coordinate_with": p["coordinate_with"],
                        "priority": p["priority"], "rationale": p["rationale"],
                        "affected_dimensions": p["affected_dimensions"], "related_signals": p["related_signals"],
                        "related_actions": p["related_actions"], "crossing_question": p["crossing_question"],
                        "citations": ctx.citations_for(p["affected_dimensions"])})
    return sorted(out, key=lambda x: x["priority"])


def build_actions(ctx: _Ctx, active_priority_ids: set[str]) -> list[dict]:
    """Layer 5 — the actions whose coordination priority fired, as structured nodes edged back to the
    priority and the signals that drove them, in registry order."""
    return [{"node_id": ctx.node_id("action", a["id"]), "id": a["id"], "kind": "action", "title": a["title"],
             "owner": a["owner"], "references": a["priority_ref"], "related_signals": a["related_signals"],
             "crossing_phase": a["crossing_phase"], "step": a["step"]}
            for a in ACTIONS if a["priority_ref"] in active_priority_ids]


def build_reasoning(code: str, environment: dict) -> dict:
    """Instantiate the reasoning graph for one state from its `environment` record — structured nodes
    with typed edges, every entry addressable by id. Consumed by atlas.build_state_edition; the same
    graph renders on pages, comparisons, briefs, and registers, and can be traversed by an AI."""
    lt = RATES.get(code, (0.0, 0.0))[0]
    ctx = _Ctx(code=code, lt=lt, rate_display=f"{lt * 100:g}%", estate=ESTATE.get(code), env=environment)
    framework = build_framework(ctx)                 # fills ctx.levels
    coordination = build_coordination(ctx)
    active = {p["id"] for p in coordination}
    return {
        "impact": build_impact(ctx),
        "framework": framework,
        "coordination": coordination,
        "actions": build_actions(ctx, active),
    }
