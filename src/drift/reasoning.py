"""The Atlas reasoning graph, composable knowledge primitives (PUBLISHING_SPEC §16–17).

Driftwood is three layers: FACTS (drift.state_facts) → REASONING (this module) → OUTPUTS (Atlas pages,
comparisons, Crossing Briefs, the Opportunity Register, the Household Record, the Annual Review, future
AI). Everything derives from the first two.

The reasoning layer is a GRAPH, not a chain. Each Impact, Decision Signal, Coordination Priority, and
Action is an ADDRESSABLE, STRUCTURED object, a node carrying typed reference edges to the other layers
(never prose). A node is a canonical, state-independent definition; a state's reasoning is that node
INSTANTIATED against its environment, with a stable per-state id (e.g. "IL:signal:estate_exposure").
Presented top-to-bottom on a page,

    environment → household impact → DECISION FRAMEWORK → coordination priorities → action register

but it is stored as a graph so any consumer can traverse it: a page renders the objects, the Household
Record references them by id, an AI walks the edges. No consumer re-authors the reasoning.

Every node is organised from EXISTING approved Driftwood thinking (the environment dimensions, the Tax
Diagnostic, the State Context, the Moving States ripple, the coordination philosophy), clarity, not
new philosophy.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .state_facts import RATES, ESTATE
from .leakage import STATE_ALPHA, coordination_opportunity_per_m, fmt_usd

# The reasoning-chain order, the Decision Framework is the centrepiece (§16).
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


# ── Layer 3 · DECISION FRAMEWORK, signals (the centrepiece: how to evaluate the environment) ──────
# Each signal is a structured node: it reads environment dimensions, evaluates to a level + reading,
# and edges to the coordination priority it opens. `evaluate` returns (level, reading).
def _s_rate_pressure(ctx: _Ctx):
    if ctx.lt <= 0:
        return "none", "No state tax on gains, every realized gain keeps its full federal-only outcome."
    lvl = "low" if ctx.lt < 0.04 else "moderate" if ctx.lt < 0.07 else "high" if ctx.lt < 0.10 else "severe"
    return lvl, f"The state takes {ctx.rate_display} of every long-term gain at the top, {lvl} drag on what a realized return keeps."


def _s_estate_exposure(ctx: _Ctx):
    e = ctx.estate
    if not e:
        return "none", "No state estate or inheritance tax, only the federal estate tax reaches the estate."
    if e["regime"] == "inheritance":
        return "moderate", ("An inheritance tax applies by the heir's relationship, not the estate's size, "
                            "exposure turns on who inherits, and close heirs are usually exempt.")
    exm = e.get("exemption_usd") or 0
    steep = bool(e.get("cliff")) or exm <= 4_000_000
    lvl = "severe" if steep else "high" if exm < _FED_ESTATE_EXEMPTION else "moderate"
    cliff = " a cliff then taxes the whole estate, not just the excess;" if e.get("cliff") else ""
    return lvl, (f"A state estate tax exempts only {e['exemption_display']}, far below the federal "
                 f"~$15M;{cliff} {lvl} exposure at death that federal-only planning misses.")


def _s_harvest_leverage(ctx: _Ctx):
    if ctx.lt <= 0:
        if "losses still deduct" in (ctx.env.get("cg") or {}).get("note", ""):
            return "moderate", ("Gains are exempt here, yet a capital loss still deducts against income, "
                                "a rare one-sided value that keeps harvesting worthwhile.")
        return "low", "With no state tax on gains, a harvested loss recovers only its federal value, the state adds no rate for it to offset."
    loss_regime = (ctx.env.get("loss") or {}).get("regime")
    if loss_regime in ("nonconforming", "none"):
        return "moderate", ("The rate rewards harvesting, but non-conforming loss rules can strand a banked "
                            "loss before it reaches the state bill, the timing has to be coordinated.")
    lvl = "high" if ctx.lt >= 0.06 else "moderate"
    return lvl, f"A harvested loss is worth the {ctx.rate_display} state rate it offsets, on top of federal, {lvl} harvesting leverage."


def _s_mobility_value(ctx: _Ctx):
    if ctx.lt <= 0 and not ctx.estate:
        return "none", "Already a no-income-tax, no-estate-tax state, the destination other households move toward, not from."
    if ctx.lt >= 0.09 or (ctx.estate and (ctx.estate.get("cliff") or (ctx.estate.get("exemption_usd") or 0) < _FED_ESTATE_EXEMPTION)):
        return "high", "Both the rate and the estate regime make relocation genuinely valuable, but domicile is a fact pattern, not a mailing address."
    if ctx.lt >= 0.05:
        return "moderate", "The rate makes a change of residency worth modelling against the life and family cost of moving."
    return "low", "The rate is modest, residency is unlikely to be the lever that moves the household's outcome."


def _s_basis_coordination(ctx: _Ctx):
    su = (ctx.env.get("stepup") or {}).get("regime")
    if su == "community":
        return "high", "Community-property state: community assets get a FULL step-up at the first death, title them so the survivor keeps that basis."
    if su == "optin":
        return "moderate", "An elective community-property trust can unlock a full first-death step-up here, worth electing before it is needed."
    if su == "udcprda":
        return "low", "Adopted the UDCPRDA, community-property basis treatment can be imported by trust for couples who plan for it."
    return "low", "Common-law basis: only the decedent's half steps up at the first death, plan titling so the survivor is not left with low-basis lots."


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

# ── Layer 4 · COORDINATION PRIORITIES, the operating-system domains each signal opens ─────────────
# Structured nodes with edges: `trigger` (which signal at what level activates it), `related_signals`,
# `related_actions`, `affected_dimensions`, and a `priority` rank. Not advisor copy, the household's
# coordination map. Renamed from "planning considerations" (§17).
COORDINATION_PRIORITIES = [
    {"id": "residency_planning", "title": "Residency & domicile", "domain": "Residency", "coordinate_with": "advisor + CPA",
     "trigger": ("mobility_value", "moderate"), "affected_dimensions": ["cg", "estate"], "priority": 1,
     "related_signals": ["mobility_value"], "related_actions": ["confirm_domicile"],
     "rationale": "Whether, and how, a change of domicile is worth pursuing, and the facts (days, home, ties) that make it real rather than nominal.",
     "crossing_question": "Which domicile facts, days present, primary home, the ties that follow you, will substantiate the move if a former state examines it?"},
    {"id": "estate_structure", "title": "Estate structure", "domain": "Estate", "coordinate_with": "estate attorney",
     "trigger": ("estate_exposure", "high"), "affected_dimensions": ["estate"], "priority": 1,
     "related_signals": ["estate_exposure"], "related_actions": ["review_estate_titling"],
     "rationale": "Whether the state's estate exposure warrants credit-shelter / QTIP titling or lifetime gifting to move value below the state threshold.",
     "crossing_question": "Does the existing estate plan still assume the prior state's exemption and rate, and should any trust now be governed elsewhere?"},
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

# ── Layer 5 · ACTION REGISTER, sequenced next steps, each edged to a coordination priority ────────
# `crossing_phase` sequences an action relative to a relocation (before · during · after the move),
# structured timing the Crossing Brief reads; state pages and the Comparison ignore it.
# ── Layer 5 · ACTIONS ─────────────────────────────────────────────────────────────────────────────
#
# Each of these used to be one static sentence of ownership ("Review titling and the credit-shelter
# / gifting options against the state estate threshold"), identical in all 51 states. True, and not
# something a reader could start. They are now a concrete first move, and every one is phrased as
# OBTAINING INFORMATION rather than taking a position, for two reasons: it is what a household can
# actually do inside a week, and Driftwood does not give tax or legal advice, so an action register
# that told a reader what to do would be the page contradicting its own disclosure.
#
# `step` is a callable so a state's own published figures can appear in it. It interpolates only
# facts the page already prints higher up (the rate, the estate threshold, the state's name). No
# action asserts a rule, and none introduces a fact the record does not carry.
#
# `bring` is the artifact the request needs to be answerable. It is the difference between "ask your
# attorney about titling" and a conversation that reaches an answer on the first pass.

def _a_domicile(ctx: _Ctx) -> str:
    return (f"Ask for this year's after-tax result on the current holdings in {_nm(ctx)}, set beside "
            f"the same holdings in a no-income-tax state, and for the list of facts a state examines "
            f"when it tests domicile. Both are inputs to a decision rather than the decision.")


def _a_estate_titling(ctx: _Ctx) -> str:
    thr = (ctx.estate or {}).get("exemption_display")
    against = f" against {_nm(ctx)}'s {thr} threshold" if thr else f" against {_nm(ctx)}'s threshold"
    return (f"Ask your attorney what the estate is currently worth for state purposes{against}, and "
            f"which assets are counted toward it. One page is enough to know whether anything further "
            f"is warranted this year.")


def _a_basis_titling(ctx: _Ctx) -> str:
    return (f"Ask how each taxable account is titled today, and what {_nm(ctx)} law does to basis at "
            f"a first death for that form of ownership. Titling is recorded on custodial paperwork, "
            f"so this is a document check rather than an opinion.")


def _a_harvest_cadence(ctx: _Ctx) -> str:
    return (f"Ask when losses were last harvested in the taxable book, and what loss carryforward is "
            f"on file. {_nm(ctx)} taxes long-term gains at a top effective {ctx.rate_display}, which "
            f"is the figure that answer has to be read against.")


def _a_place_sleeves(ctx: _Ctx) -> str:
    return ("Ask which holdings sit in taxable accounts and which sit in tax-deferred ones today, "
            "and what turnover each produces. Placement cannot be assessed until both lists are on "
            "one page, including the accounts nobody currently manages.")


ACTIONS = [
    {"id": "confirm_domicile", "title": "Price the domicile question", "owner": "advisor",
     "priority_ref": "residency_planning", "related_signals": ["mobility_value"],
     "crossing_phase": "before", "step": _a_domicile,
     "bring": "Last year's full return, and a current statement for each account."},
    {"id": "review_estate_titling", "title": "Size the estate against the state threshold",
     "owner": "estate attorney", "priority_ref": "estate_structure",
     "related_signals": ["estate_exposure"], "crossing_phase": "after", "step": _a_estate_titling,
     "bring": "The estate documents as executed, and a current net-worth figure."},
    {"id": "set_basis_titling", "title": "Check how each account is titled",
     "owner": "estate attorney", "priority_ref": "basis_titling",
     "related_signals": ["basis_coordination"], "crossing_phase": "after", "step": _a_basis_titling,
     "bring": "The registration page of each taxable account."},
    {"id": "set_harvest_cadence", "title": "Establish the harvesting record", "owner": "advisor",
     "priority_ref": "harvest_coordination", "related_signals": ["harvest_leverage"],
     "crossing_phase": "after", "step": _a_harvest_cadence,
     "bring": "This year's realized gain and loss report, and last year's Schedule D."},
    {"id": "place_sleeves", "title": "Put every account on one page", "owner": "advisor",
     "priority_ref": "asset_location", "related_signals": ["rate_pressure"],
     "crossing_phase": "after", "step": _a_place_sleeves,
     "bring": "A position list for every account, including the ones held elsewhere."},
]


# Registries, every primitive is addressable by id (the canonical definition consumers reference).
SIGNAL_BY_ID = {s["id"]: s for s in FRAMEWORK_SIGNALS}
PRIORITY_BY_ID = {p["id"]: p for p in COORDINATION_PRIORITIES}
ACTION_BY_ID = {a["id"]: a for a in ACTIONS}


def build_impact(ctx: _Ctx) -> dict:
    """Layer 2, the Household Impact node: what the environment does to a household's after-tax
    system, sourced from the Tax Diagnostic (STATE_ALPHA), edged to the dimensions it summarises."""
    a = STATE_ALPHA.get(ctx.code)
    reading = (
        (f"This environment leaks after-tax return on an uncoordinated book; coordinating how the portfolio is "
         f"built and run against it is the opportunity. On an illustrative 30-year path that is worth about "
         f"~{fmt_usd(coordination_opportunity_per_m(a['alpha']))}/yr for every $1M of taxable assets here, "
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
    """Layer 3, evaluate every Decision Framework signal, recording each level so downstream nodes can
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
    """Layer 4, the coordination priorities whose signal triggers fired, as structured nodes with
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
    """Layer 5, the actions whose coordination priority fired, as structured nodes edged back to the
    priority and the signals that drove them, in registry order."""
    return [{"node_id": ctx.node_id("action", a["id"]), "id": a["id"], "kind": "action", "title": a["title"],
             "owner": a["owner"], "references": a["priority_ref"], "related_signals": a["related_signals"],
             "crossing_phase": a["crossing_phase"], "step": a["step"](ctx), "bring": a["bring"]}
            for a in ACTIONS if a["priority_ref"] in active_priority_ids]


def build_reasoning(code: str, environment: dict) -> dict:
    """Instantiate the reasoning graph for one state from its `environment` record, structured nodes
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


# ── Layer 3b · COLLISIONS ── STAGED, NOT PUBLISHED. Read this before wiring it up. ────────────────
#
# WHY IT IS NOT RENDERED. Two full adversarial reviews, three independent lenses each, both refused
# it. Round two was not a near miss: it found defects the first round had not, and two of those were
# introduced by the round-one fixes (Maryland's inheritance tax described as stacking on the estate
# tax when 7-309 credits it, and Pennsylvania's 0% spousal rate omitted from a card whose whole
# thesis is that the beneficiary form sets the rate). A generator that produces a NEW false tax
# claim each time it is corrected is not one bad paragraph away from shipping.
#
# THE ROOT CAUSE IS THE DATA LAYER, NOT THE PROSE. Each archetype below wants a fact the per-state
# record does not carry, so the copy reaches for it and gets it wrong:
#   * estate_and_realization implies the state estate tax bites at the FIRST death. All twelve of
#     those states allow an unlimited marital deduction, so for a married couple it does not. The
#     record has no marital-deduction field.
#   * heir_class_form needs per-class exemptions (PA spouse 0%, NJ's $25k Class C, NE's $100k
#     Class 1), not just rate ranges.
#   * qsbs_state_only_sale asserts prior-year losses reach the state bill; that is false in AL, NJ
#     and PA, which the SAME PAGE says two cards below. It also needs the 1202 cap, and MS and DC
#     conformity both need re-verification against statute.
#   * no_muni_shelter says "no matter who issued it"; all three states exempt specific in-state
#     issues, and Treasuries stay state-exempt, which the closing sentence steers away from.
#   * loss_meets_gain rests, for Hawaii, on an uncited five-year expiry that looks like the
#     1212(a) CORPORATE carryover applied to an individual.
#   * community_basis states the elective community-property trust step-up as settled; the federal
#     1014(b)(6) consequence has never been ruled on.
#   * The statute lines are worse than none on two cards: citations_for pulls any citation attached
#     to any dimension the card reads, so a QSBS card cited California's rate section.
#
# WHAT HAS TO HAPPEN FIRST. Close the data gaps above as structured fields with citations, narrow
# the set to archetypes whose every claim resolves to one, and route the copy through PAS/OSJ as
# the compliance headers on every professional-education page in this repo already require. Then
# re-run the verification and wire build_collisions back into build_reasoning.
#
# tests/test_statepages.py::test_no_collision_block_is_published enforces the withholding.
#
# Every other node on an Atlas page restates one rule. A collision states the CONTRADICTION between
# two of a state's own rules: a step that reduces one tax and increases another. It is the only
# place the coordination argument stops being a claim about the firm and becomes a checkable fact
# about the reader's state, which is why it is worth the care below.
#
# THREE RULES, learned from an adversarial review that refused the first draft outright:
#
#   1. COVERAGE IS NOT THE PRODUCT. The first draft required every one of the 51 states to render
#      two cards, and to reach that it invented two archetypes that were false or vacuous outside
#      their showcase state. A collision block cannot be forced to fire where nothing collides.
#      The minimum is zero and _collisions_html renders nothing for an empty list.
#   2. ONE CLOSER PER DIMENSION. Each archetype declares the dimension it closes; a page never
#      states the same basis or loss fact twice in two different voices.
#   3. THE WEAKER TRUE CLAIM WINS. Where a sharper sentence needed a fact the record does not
#      carry, the sentence was cut rather than reconstructed. Specific casualties, recorded so they
#      are not "improved" back in:
#        - "no state return follows a death here" was FALSE in 24 of the 33 states it would have
#          shipped on: no death tax does not mean no final individual or fiduciary return.
#        - a which-spouse-holds-the-lot archetype denied its own headline, because on a joint
#          return the holder does not change the income answer. Deleted, not softened.
#        - the muni card quoted the long-term capital-gains rate for an ordinary-income decision,
#          and read as "municipal bonds buy nothing here" while omitting that the FEDERAL exemption
#          is untouched. It now quotes the ordinary rate and says so.
#
# Nothing here is advice. Each card states a mechanism and names the desks it sits across.

MAX_COLLISIONS = 2

_ROOM_ORDER = ("advisor", "CPA", "estate attorney")


def _room(*who: str) -> str:
    """The desks a collision sits across, in one fixed order so the same set always reads the same."""
    seen = [w for w in _ROOM_ORDER if w in who]
    return " + ".join(seen)


def _reg(env: dict, dim: str) -> str:
    return (env.get(dim) or {}).get("regime") or ""


def _nm(ctx: _Ctx) -> str:
    from .leakage import STATE_NAMES
    return STATE_NAMES.get(ctx.code, ctx.code)


def _fires(arch: dict, ctx: _Ctx) -> bool:
    for dim, allowed in arch.get("requires", {}).items():
        if _reg(ctx.env, dim) not in allowed:
            return False
    for dim, banned in arch.get("excludes", {}).items():
        if _reg(ctx.env, dim) in banned:
            return False
    guard = arch.get("guard")
    return guard(ctx) if guard else True


# How the first death treats basis, per marital-property regime. Phrased so each is true on its own
# and none overstates: the UDCPRDA line keeps its precondition, which the first draft dropped.
_RESET = {
    "community": "community property takes a full reset at the first death, both halves",
    "optin": "a full reset at the first death is available, but only for property the couple has "
             "placed in the state's elective community-property trust",
    "common": "only the decedent's half of jointly held property resets, and the survivor carries "
              "their original basis on the other half",
    "udcprda": "only the decedent's half resets, unless the property was brought from a "
               "community-property state and keeps that character under the state's UDCPRDA adoption",
}


def _x_estate_and_realization(ctx: _Ctx) -> str:
    nm, e = _nm(ctx), (ctx.estate or {})
    lead = "A long-term gain" if _reg(ctx.env, "cg") == "lt_only" else "A gain"
    how = " as a state excise" if _reg(ctx.env, "cg") == "lt_only" else ""
    cliff = {
        "hard": ", and once an estate clears that figure the tax reaches essentially the whole "
                "estate rather than only the excess",
        "phaseout": ", and an estate more than 5% over that figure loses the exclusion altogether, "
                    "so the tax then reaches the whole estate rather than only the excess",
    }.get(e.get("cliff_kind"), "")
    return (f"{lead} realized in {nm} is taxed at a top effective {ctx.rate_display}{how}. The same "
            f"dollar meets a second {nm} tax if it is still in the estate at death, because the state "
            f"taxes estates above {e.get('exemption_display')}, well below the federal exclusion{cliff}. "
            f"Realizing reduces the second exposure and pays the first; holding does the reverse, and "
            f"{_RESET[_reg(ctx.env, 'stepup')]}.")


def _x_heir_class_form(ctx: _Ctx) -> str:
    nm, e = _nm(ctx), (ctx.estate or {})
    return (f"{nm} taxes what people RECEIVE at death, by their relationship to the deceased, rather "
            f"than only the estate by its size: {e.get('heir_detail')}. Which class a given account "
            f"falls into therefore follows whoever is named on it, and beneficiary designations sit "
            f"on custodial paperwork that is updated on a different schedule from the will. The "
            f"instrument that records the intention and the form that controls the account are held "
            f"by two different people.")


def _x_no_muni_shelter(ctx: _Ctx) -> str:
    nm = _nm(ctx)
    ordinary = RATES.get(ctx.code, (0.0, 0.0))[1] * 100
    return (f"Municipal-bond interest is ordinary income, and {nm} taxes it at up to {ordinary:g}% no "
            f"matter who issued it, in state or out. The federal exemption is unaffected, so municipal "
            f"bonds still do their usual federal work; what {nm} removes is the in-state preference a "
            f"home-state ladder is normally built to capture. The remaining question is where a holding "
            f"sits rather than what it is, which is an account-structure question rather than a "
            f"bond-selection one.")


def _x_qsbs_state_only_sale(ctx: _Ctx) -> str:
    nm = _nm(ctx)
    return (f"{nm} does not follow the federal §1202 exclusion, so a qualifying small-business sale "
            f"can be fully exempt on the federal return and taxed at up to {ctx.rate_display} on the "
            f"state one. It is one of the few transactions where the two answers diverge this far, "
            f"and the federal exemption is what usually removes the reason to plan for it at all. "
            f"Losses banked in earlier years carry forward under the federal rules, so the harvesting "
            f"record of the years BEFORE a sale is one of the few things still able to reach the "
            f"state bill by the time it lands.")


def _x_loss_meets_gain(ctx: _Ctx) -> str:
    nm = _nm(ctx)
    if _reg(ctx.env, "loss") == "expires":
        window = (f"{nm} lets a capital loss carry forward, but not indefinitely, so a loss banked "
                  f"today has a date after which it is worth nothing")
    else:
        window = (f"{nm} provides no carryforward for a capital loss, so a loss and the gain it is "
                  f"meant to offset have to land in the same tax year")
    return (f"{window}. The basis rule runs the other way: the positions carrying the largest "
            f"embedded gains are the ones with the lowest basis, and {_RESET[_reg(ctx.env, 'stepup')]}, "
            f"so the gain best placed to use the loss is also the one with the most waiting for it. "
            f"The harvesting calendar and the holding decision are set on different desks.")


def _x_community_basis(ctx: _Ctx) -> str:
    nm = _nm(ctx)
    return (f"{nm} imposes no estate or inheritance tax, so nothing at death sets a state "
            f"transfer-tax deadline and nothing forces the basis question onto a calendar. State law "
            f"still decides its answer: {_RESET[_reg(ctx.env, 'stepup')]}. Whether a given account "
            f"qualifies is a titling question settled long before the death it matters at, and the "
            f"absence of a state death tax is exactly what keeps anyone from checking it.")


def _x_harvest_into_basis(ctx: _Ctx) -> str:
    nm = _nm(ctx)
    return (f"A harvested loss in {nm} recovers the {ctx.rate_display} state rate it offsets, on top "
            f"of its federal value, and it is bought by carrying a lower basis on whatever replaces "
            f"the position. That deferred gain meets the state rate again on a later sale, or it "
            f"reaches the first death, where {_RESET[_reg(ctx.env, 'stepup')]}. The desk that decides "
            f"the harvest and the desk that decides what is held until death are rarely the same one.")


# rank orders the ladder: largest dollar consequence first, structural and correctable last.
# closes_on is the dimension a card spends, so no page states the same fact twice (see rule 2).
COLLISION_ARCHETYPES = [
    {"id": "estate_and_realization", "rank": 1, "closes_on": "stepup",
     "title": "The gain decision and the estate decision are the same decision.",
     "requires": {"estate": ("estate", "both")}, "excludes": {"cg": ("notax",)},
     # Connecticut's exemption IS the federal exclusion, so the "second, lower threshold" this card
     # is entirely about does not exist there. Gating on the number rather than the regime.
     "guard": lambda c: 0 < ((c.estate or {}).get("exemption_usd") or 0) < _FED_ESTATE_EXEMPTION,
     "reads": ("cg", "estate", "stepup"), "room": _room("advisor", "CPA", "estate attorney"),
     "body": _x_estate_and_realization},
    {"id": "qsbs_state_only_sale", "rank": 3, "closes_on": "qsbs",
     "title": "The sale that is exempt federally is a full-rate state event.",
     "requires": {"qsbs": ("decoupled",)}, "excludes": {"cg": ("notax",)},
     "reads": ("qsbs", "cg", "loss"), "room": _room("advisor", "CPA"),
     "body": _x_qsbs_state_only_sale},
    {"id": "loss_meets_gain", "rank": 4, "closes_on": "loss",
     "title": "The loss and the gain it offsets have to meet, and basis keeps them apart.",
     "requires": {"loss": ("none", "expires")},
     "reads": ("loss", "cg", "stepup"), "room": _room("advisor", "CPA"),
     "body": _x_loss_meets_gain},
    {"id": "no_muni_shelter", "rank": 5, "closes_on": "muni",
     "title": "The usual shelter for ordinary income is the one the state withholds.",
     "requires": {"muni": ("taxall",)}, "excludes": {"cg": ("notax",)},
     "reads": ("muni", "cg"), "room": _room("advisor", "CPA"),
     "body": _x_no_muni_shelter},
    # Second, not fifth. On dollar magnitude alone this ranks lower: for a spouse-and-children
    # estate the tax is zero in KY, NE, NJ and MD and 4.5% in PA, which is why the copy leads with
    # the close-heir exemption. It is ranked here on coordination value instead. In New Jersey and
    # Pennsylvania a fifth-place rank let the QSBS and loss cards take both slots, so the two
    # states whose death tax is decided on a custodial beneficiary form rather than in the will
    # were the two states that never said so.
    {"id": "heir_class_form", "rank": 2, "closes_on": "estate",
     "title": "The rate at death is set on a beneficiary form.",
     "requires": {"estate": ("inheritance", "both")},
     "guard": lambda c: bool((c.estate or {}).get("heir_detail")),
     "reads": ("estate", "stepup"), "room": _room("advisor", "estate attorney"),
     "body": _x_heir_class_form},
    # Only where the state's own marital-property law creates a real choice. The common-law and
    # UDCPRDA states are deliberately excluded: there the "choice" is largely federal, and the
    # first draft's version of this card shipped a false claim about state returns to reach them.
    {"id": "community_basis", "rank": 6, "closes_on": "stepup",
     "title": "No death tax is not the same as no decision at death.",
     "requires": {"estate": ("none",), "stepup": ("community", "optin")},
     "reads": ("estate", "stepup"), "room": _room("advisor", "estate attorney"),
     "body": _x_community_basis},
    {"id": "harvest_into_basis", "rank": 7, "closes_on": "stepup",
     "title": "Harvesting spends basis, and the step-up is where the deferral lands.",
     "requires": {"loss": ("fed",)}, "excludes": {"cg": ("notax", "lt_only")},
     "reads": ("loss", "cg", "stepup"), "room": _room("advisor", "estate attorney"),
     "body": _x_harvest_into_basis},
]


def build_collisions(ctx: _Ctx, limit: int = MAX_COLLISIONS) -> list[dict]:
    """The collisions that actually fire for this state, at most `limit`, possibly none."""
    out, closed = [], set()
    for arch in sorted(COLLISION_ARCHETYPES, key=lambda a: (a["rank"], a["id"])):
        if arch["closes_on"] in closed or not _fires(arch, ctx):
            continue
        closed.add(arch["closes_on"])
        out.append({"node_id": ctx.node_id("collision", arch["id"]), "id": arch["id"],
                    "kind": "collision", "title": arch["title"], "body": arch["body"](ctx),
                    "room": arch["room"], "closes_on": arch["closes_on"],
                    "reads": list(arch["reads"]), "citations": ctx.citations_for(arch["reads"])})
        if len(out) >= limit:
            break
    return out
