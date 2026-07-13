"""The Atlas reasoning layers — composable knowledge primitives (PUBLISHING_SPEC §16).

The Atlas does not merely describe state tax law; it reasons about it. Every state page answers
"given this environment, how should a sophisticated household think?" through five layers, with the
Decision Framework at the centre:

    environment → household impact → DECISION FRAMEWORK → planning considerations → action register

These layers are NOT page-specific prose. Each Impact, Framework signal, Consideration, and Action is
an ADDRESSABLE OBJECT with a stable id — a reusable knowledge primitive. A primitive is a canonical,
state-independent definition; a state's reasoning is that primitive INSTANTIATED against the state's
environment. The same primitives render on state pages, the comparison spread, Crossing Briefs, the
Opportunity Register, and the Household Record — the reasoning exists once and renders differently by
context. No consumer re-authors it.

Every primitive is organised from EXISTING approved Driftwood thinking — the seven environment
dimensions, the Tax Diagnostic (STATE_ALPHA), the hand-authored State Context, the Moving States
decision ripple, and the coordination philosophy. This increases clarity and actionability; it does
not expand the firm's philosophy.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .state_facts import RATES, ESTATE
from .leakage import STATE_ALPHA

# The reasoning-chain order — the Decision Framework is the centrepiece (§16).
CHAIN = ("environment", "impact", "framework", "considerations", "actions")

_FED_ESTATE_EXEMPTION = 13_990_000  # 2025 federal basic exclusion — the bar state exposure is read against
_ORDER = {lvl: i for i, lvl in enumerate(("none", "low", "moderate", "high", "severe"))}


@dataclass
class _Ctx:
    """The binding context: a state's numeric facts + environment record, plus the signal levels
    accumulated as the framework evaluates (so considerations and actions can read them by id)."""
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


# ── Layer 3 · DECISION FRAMEWORK — the centrepiece: how to evaluate the environment ────────────────
# Each signal is an addressable evaluation lens. `reads` names the environment dimensions it weighs;
# `evaluate` binds it to a state, returning a level (none…severe) and a one-line institutional reading.
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
        # Missouri exempts gains yet still deducts losses — a rare one-sided value the generic
        # no-tax reading would misstate.
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
    {"id": "rate_pressure", "label": "Rate pressure", "reads": ["cg"],
     "question": "How much does the state erode each realized gain?", "evaluate": _s_rate_pressure},
    {"id": "estate_exposure", "label": "Estate exposure", "reads": ["estate"],
     "question": "Does the state tax the estate below the federal threshold, and how steeply?", "evaluate": _s_estate_exposure},
    {"id": "harvest_leverage", "label": "Harvesting leverage", "reads": ["cg", "loss"],
     "question": "How much is a harvested loss worth here?", "evaluate": _s_harvest_leverage},
    {"id": "mobility_value", "label": "Mobility value", "reads": ["cg", "estate"],
     "question": "How much could a change of residency be worth?", "evaluate": _s_mobility_value},
    {"id": "basis_coordination", "label": "Basis coordination", "reads": ["stepup"],
     "question": "What basis-step-up opportunity does the marital-property regime create?", "evaluate": _s_basis_coordination},
]


# ── Layer 4 · PLANNING CONSIDERATIONS — the coordination each signal opens ─────────────────────────
# Addressable coordination areas; `activates` reads the framework signals by id, so a consideration
# is never authored per state — it fires when the state's environment makes it relevant.
CONSIDERATIONS = [
    {"id": "residency_planning", "area": "Residency & domicile", "coordinate": "advisor + CPA",
     "activates": lambda c: c.at_least("mobility_value", "moderate"),
     "note": "Whether — and how — a change of domicile is worth pursuing, and the facts (days, home, ties) that make it real rather than nominal."},
    {"id": "estate_structure", "area": "Estate structure", "coordinate": "estate attorney",
     "activates": lambda c: c.at_least("estate_exposure", "high"),
     "note": "Whether the state's estate exposure warrants credit-shelter / QTIP titling or lifetime gifting to move value below the state threshold."},
    {"id": "basis_titling", "area": "Asset titling for step-up", "coordinate": "estate attorney",
     "activates": lambda c: c.at_least("basis_coordination", "moderate"),
     "note": "Titling assets to capture the fullest basis step-up the marital-property regime allows at the first death."},
    {"id": "harvest_coordination", "area": "Loss harvesting", "coordinate": "advisor + CPA",
     "activates": lambda c: c.at_least("harvest_leverage", "moderate"),
     "note": "Setting a harvesting cadence that captures the state rate a banked loss offsets, sequenced against the state's loss-carryforward rules."},
    {"id": "asset_location", "area": "Asset location", "coordinate": "advisor",
     "activates": lambda c: c.at_least("rate_pressure", "low"),
     "note": "Placing the high-turnover sleeve in tax-advantaged accounts so the state's rate falls on the least of the household's realized gains."},
]


# ── Layer 5 · ACTION REGISTER — the sequenced next steps, each referencing a consideration ─────────
ACTIONS = [
    {"id": "confirm_domicile", "owner": "advisor", "references": "residency_planning",
     "step": "Model the after-tax and estate outcome of the current vs a lower-tax domicile, and list the domicile facts to establish before any move."},
    {"id": "review_estate_titling", "owner": "estate attorney", "references": "estate_structure",
     "step": "Review titling and the credit-shelter / gifting options against the state estate threshold; quantify the exposure at the household's net worth."},
    {"id": "set_basis_titling", "owner": "estate attorney", "references": "basis_titling",
     "step": "Title (or elect the trust) to capture the fullest first-death basis step-up the regime allows."},
    {"id": "set_harvest_cadence", "owner": "advisor", "references": "harvest_coordination",
     "step": "Set the annual loss-harvesting cadence and confirm it clears the state's carryforward rules."},
    {"id": "place_sleeves", "owner": "advisor", "references": "asset_location",
     "step": "Locate the high-turnover sleeve into tax-advantaged accounts and confirm the taxable book is the low-turnover core."},
]

_CONSIDERATION_BY_ID = {c["id"]: c for c in CONSIDERATIONS}


def build_impact(code: str) -> dict:
    """Layer 2 — the Household Impact object: what the environment does to a household's after-tax
    system, sourced from the Tax Diagnostic (STATE_ALPHA). Personalised by the diagnostic; the figure
    here is the illustrative default. An addressable primitive referenced by pages and reports alike."""
    a = STATE_ALPHA.get(code)
    obj = {"id": "after_tax_impact", "inputs": ["state", "bracket", "portfolio"],
           "diagnostic_ref": f"leakage.html?state={code}",
           "illustrative_alpha_pct": a["alpha"] if a else None,
           "before_pct": a["before"] if a else None, "after_pct": a["after"] if a else None}
    obj["reading"] = (
        (f"On an illustrative 30-year path, coordinated tax management recovers about +{a['alpha']:.1f}%/yr "
         f"of after-tax return here — the leak this state's rules put on an uncoordinated book "
         f"({a['before']:.1f}% → {a['after']:.1f}%/yr kept). The household's own figure depends on bracket, "
         f"holdings, and residency; the Tax Diagnostic computes it.") if a else
        "The household's after-tax figure depends on bracket, holdings, and residency; the Tax Diagnostic computes it.")
    return obj


def build_framework(ctx: _Ctx) -> list[dict]:
    """Layer 3 — evaluate every Decision Framework signal against the state, recording each level so
    the downstream layers can read it. Returns a list of instantiated signal objects (by id)."""
    out = []
    for sig in FRAMEWORK_SIGNALS:
        level, reading = sig["evaluate"](ctx)
        ctx.levels[sig["id"]] = level
        out.append({"signal": sig["id"], "label": sig["label"], "question": sig["question"],
                    "reads": sig["reads"], "level": level, "reading": reading})
    return out


def build_considerations(ctx: _Ctx) -> list[dict]:
    """Layer 4 — the considerations whose framework triggers fired for this state (by id)."""
    return [{"consideration": c["id"], "area": c["area"], "coordinate": c["coordinate"], "note": c["note"]}
            for c in CONSIDERATIONS if c["activates"](ctx)]


def build_actions(active_consideration_ids: set[str]) -> list[dict]:
    """Layer 5 — the actions that reference an active consideration, in registry order (by id)."""
    return [{"action": a["id"], "owner": a["owner"], "references": a["references"], "step": a["step"]}
            for a in ACTIONS if a["references"] in active_consideration_ids]


def build_reasoning(code: str, environment: dict) -> dict:
    """Instantiate all four downstream layers for one state from its `environment` record — the
    composable reasoning graph, every entry referencing a primitive by id. Consumed by
    atlas.build_state_edition; the same output renders on pages, comparisons, briefs, and registers."""
    lt = RATES.get(code, (0.0, 0.0))[0]
    ctx = _Ctx(code=code, lt=lt, rate_display=f"{lt * 100:g}%", estate=ESTATE.get(code), env=environment)
    framework = build_framework(ctx)                 # fills ctx.levels
    considerations = build_considerations(ctx)
    active = {c["consideration"] for c in considerations}
    return {
        "impact": build_impact(code),
        "framework": framework,
        "considerations": considerations,
        "actions": build_actions(active),
    }
