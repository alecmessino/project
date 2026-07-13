"""The Comparison instrument — a query over the reasoning graph (PUBLISHING_SPEC §16–17).

Comparison is a PRODUCT, and a product is a thin query over the graph: it authors no facts and no
reasoning of its own. It takes two `atlas.build_state_edition` records and computes the *difference*
between two operating environments — which Decision Framework signals read differently, which
Coordination Priorities are unique to each, which Actions follow, and the environment facts that
drive each difference.

It is deliberately SYMMETRIC — it weighs two environments, it does not say which is "better" and it
does not imply a move. The directional "your household operating system is changing" reading is the
Crossing Brief's job (drift.crossing, planned); both will build on this same engine.

    build_comparison(a, b) -> a structured diff over the two graph records — every entry references a
    reasoning primitive by id, so the Comparison, the state pages, and the Crossing Brief all render
    the same reasoning. Nothing here re-derives a fact or a signal level.
"""
from __future__ import annotations

from . import atlas
from .site import BASE_URL
from .statemap import CURRENT_EDITION
from .statepage import state_slug, STATE_PAGE_CODES


# The canonical pair ordering: a comparison of two environments is order-independent, so a pair has
# ONE canonical URL. We order by slug so /compare/california-vs-texas/ is the single home for the
# pair and the reverse request redirects to it (no duplicate content).
def canonical_pair(a: str, b: str) -> tuple[str, str]:
    """Return (a, b) reordered so the pair is canonical (by state slug). Order-independent."""
    return (a, b) if state_slug(a) <= state_slug(b) else (b, a)


def compare_slug(a: str, b: str) -> str:
    """The canonical pair slug, e.g. ('IL','FL') -> 'florida-vs-illinois'. Order-independent."""
    a, b = canonical_pair(a, b)
    return f"{state_slug(a)}-vs-{state_slug(b)}"


def compare_path(a: str, b: str, edition: str = CURRENT_EDITION) -> str:
    """Editioned directory path (no domain): 'atlas/2026/compare/florida-vs-illinois'."""
    return f"atlas/{edition}/compare/{compare_slug(a, b)}"


def compare_url(a: str, b: str, edition: str = CURRENT_EDITION) -> str:
    """Canonical editioned URL, trailing slash."""
    return f"{BASE_URL}/{compare_path(a, b, edition)}/"


def compare_index_url(edition: str = CURRENT_EDITION) -> str:
    return f"{BASE_URL}/atlas/{edition}/compare/"


# High-intent comparison corridors — the pairs households actually weigh (relocation routes and
# high-tax/no-tax contrasts). These get their own canonical, crawlable pages and sit in the sitemap;
# the instrument itself compares ANY two jurisdictions. Ordered by real search intent (origin→magnet);
# the rendered page is symmetric, and the URL is canonicalised regardless.
FEATURED_CORRIDORS: list[tuple[str, str]] = [
    ("CA", "TX"), ("CA", "FL"), ("CA", "NV"), ("CA", "WA"), ("CA", "AZ"),
    ("NY", "FL"), ("NY", "TX"), ("NY", "NC"), ("NJ", "FL"), ("NJ", "PA"),
    ("IL", "FL"), ("IL", "TX"), ("IL", "IN"), ("MN", "FL"), ("MA", "NH"),
    ("OR", "WA"), ("CT", "FL"), ("MD", "FL"), ("VA", "FL"), ("CO", "TX"),
    ("HI", "NV"), ("WA", "TX"), ("TX", "FL"), ("NY", "NJ"),
]


def _delta_signal(a_node: dict, b_node: dict) -> dict:
    """Align one Decision Framework signal across the two environments — its level on each side and the
    signed score delta. The signal definition (id/title/question) is canonical; only the reading and
    level are state-bound, so a comparison never re-evaluates — it reads both already-decided nodes."""
    return {
        "id": a_node["id"], "title": a_node["title"], "question": a_node["question"],
        "a_level": a_node["level"], "b_level": b_node["level"],
        "a_score": a_node["score"], "b_score": b_node["score"],
        "delta": b_node["score"] - a_node["score"],   # >0 ⇒ B reads higher pressure on this lens
        "changed": a_node["level"] != b_node["level"],
        "a_reading": a_node["reading"], "b_reading": b_node["reading"],
    }


# The environment dimensions worth diffing on a comparison, in reading order (matches the state-page
# dimension cards). alpha is the illustrative impact, handled separately.
_DIFF_DIMS = [
    ("cg", "Capital-gains rate"), ("estate", "Estate & inheritance"), ("stepup", "Basis step-up"),
    ("marriage", "Marriage treatment"), ("loss", "Loss treatment"), ("muni", "Municipal bonds"),
    ("qsbs", "QSBS (§1202)"),
]


def _environment_diffs(env_a: dict, env_b: dict) -> list[dict]:
    """The settled tax FACTS that differ between the two environments — the evidence under the signal
    deltas. A dimension is included only when the two states' tag or regime actually diverges; the
    citations come straight off the canonical dimensions (an edge to the Facts layer)."""
    out = []
    for key, label in _DIFF_DIMS:
        da, db = env_a.get(key) or {}, env_b.get(key) or {}
        if not da and not db:
            continue
        same = (da.get("tag") == db.get("tag")) and (da.get("regime") == db.get("regime"))
        if same:
            continue
        out.append({
            "dim": key, "label": label,
            "a_tag": da.get("tag", ""), "a_note": da.get("note", ""),
            "b_tag": db.get("tag", ""), "b_note": db.get("note", ""),
            "a_citations": da.get("citation") or [], "b_citations": db.get("citation") or [],
        })
    return out


def build_comparison(a: str, b: str, edition: str = CURRENT_EDITION) -> dict:
    """The Comparison query: a structured, symmetric diff of two operating environments, computed
    entirely from the reasoning graph. Nothing is authored here — every field is projected from the
    two `atlas.build_state_edition` records, so the Comparison can never disagree with a state page.

    The pair is canonicalised (order-independent), so build_comparison(a, b) == build_comparison(b, a)
    up to the canonical A/B assignment.
    """
    a, b = canonical_pair(a, b)
    ra = atlas.build_state_edition(a, edition)
    rb = atlas.build_state_edition(b, edition)

    # Decision Framework — align all five canonical lenses (same order every state is read through).
    sb = {s["id"]: s for s in rb["framework"]}
    signals = [_delta_signal(sa, sb[sa["id"]]) for sa in ra["framework"]]
    changed = [s for s in signals if s["changed"]]

    # Coordination Priorities — a set-diff by id: shared, unique-to-A, unique-to-B. These are the
    # household's operating-system domains, so "which priorities change" is the instrument's headline.
    pa = {c["id"]: c for c in ra["coordination"]}
    pb = {c["id"]: c for c in rb["coordination"]}
    shared = [pa[i] for i in pa if i in pb]
    only_a = [pa[i] for i in pa if i not in pb]
    only_b = [pb[i] for i in pb if i not in pa]

    # Action Register — follows the priorities, same set-diff.
    xa = {x["id"]: x for x in ra["actions"]}
    xb = {x["id"]: x for x in rb["actions"]}
    act_shared = [xa[i] for i in xa if i in xb]
    act_only_a = [xa[i] for i in xa if i not in xb]
    act_only_b = [xb[i] for i in xb if i not in xa]

    ia, ib = ra["impact"], rb["impact"]
    aa, ab = ia.get("illustrative_alpha_pct"), ib.get("illustrative_alpha_pct")

    return {
        "edition": edition,
        "slug": compare_slug(a, b),
        "a": {"code": a, "name": ra["name"]},
        "b": {"code": b, "name": rb["name"]},
        "signals": signals,
        "changed_signal_ids": [s["id"] for s in changed],
        "signals_changed": len(changed),
        "signals_total": len(signals),
        "coordination": {"shared": shared, "only_a": only_a, "only_b": only_b},
        "priorities_changed": len(only_a) + len(only_b),
        "actions": {"shared": act_shared, "only_a": act_only_a, "only_b": act_only_b},
        "impact": {"a_alpha": aa, "b_alpha": ab,
                   "delta": (round(ab - aa, 1) if (aa is not None and ab is not None) else None)},
        "environment_diffs": _environment_diffs(ra["environment"], rb["environment"]),
    }


def index_dataset(edition: str = CURRENT_EDITION) -> dict:
    """The data the browser instrument LAYS OUT to weigh any two states live — the canonical Decision
    Framework and Coordination Priority definitions, plus every state's ALREADY-DECIDED reasoning
    (levels, readings, active priorities). The browser presents this; it does not reason. Every level
    and reading here was decided in Python (drift.reasoning), so the live instrument and the static
    corridor pages render the identical graph — the diff is a set operation over decided outputs, not
    a re-evaluation of the rules."""
    from .reasoning import FRAMEWORK_SIGNALS, COORDINATION_PRIORITIES
    signals = [{"id": s["id"], "title": s["title"], "question": s["question"]} for s in FRAMEWORK_SIGNALS]
    priorities = {p["id"]: {"title": p["title"], "coordinate_with": p["coordinate_with"],
                            "rationale": p["rationale"]} for p in COORDINATION_PRIORITIES}
    states = {}
    for code in STATE_PAGE_CODES:
        rec = atlas.build_state_edition(code, edition)
        states[code] = {
            "name": rec["name"], "slug": state_slug(code),
            "signals": {s["id"]: {"level": s["level"], "score": s["score"], "reading": s["reading"]}
                        for s in rec["framework"]},
            "priorities": [c["id"] for c in rec["coordination"]],
            "alpha": rec["impact"].get("illustrative_alpha_pct"),
        }
    order = sorted(STATE_PAGE_CODES, key=lambda c: states[c]["name"])
    return {"signals": signals, "priorities": priorities, "states": states, "order": order,
            "featured": [list(canonical_pair(a, b)) for a, b in FEATURED_CORRIDORS]}
