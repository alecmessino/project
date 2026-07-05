"""The "Single asset risk" dataset — de-risking a concentrated, low-basis stock position.

A concentrated single-stock holding is one of the hardest problems in taxable wealth: sell and a low
basis triggers a heavy tax bill; hold and you carry idiosyncratic risk the market never pays you to bear.
Every approach trades off along the same six axes, and the strategies sort into five families.

This module is the single source of truth for the interactive heatmap (`concentration.html`):

  * AXES     — the six scored tradeoffs (higher score = more favorable on that axis).
  * BUCKETS  — the five strategy families (selling / harvesting / hedging / deferring / giving).
  * STRATEGIES — 22 approaches, each with a 1–5 score + human label per axis, a factual "how it works"
                 blurb (written from the mechanics, no fabricated specifics), and filter tags
                 (primary goals, suitable timelines, turnkey-simple flag, insider-safe flag).

The per-axis scores are one analyst's read of *typical* tradeoffs — orientation, not advice, and not a
statement about any specific holding. The page carries the not-advice disclosure.
"""

from __future__ import annotations

# ── the six scored axes (higher = better on that axis) ────────────────────────────────────────────
AXES = [
    {"key": "liq", "label": "Liquidity", "hint": "How much spendable cash it frees up"},
    {"key": "spd", "label": "Time to de-risk", "hint": "How quickly it cuts the single-stock risk"},
    {"key": "cost", "label": "Fees", "hint": "Implementation and ongoing cost (higher score = cheaper)"},
    {"key": "tax", "label": "Tax cost", "hint": "Tax drag of the approach (higher score = less tax)"},
    {"key": "cust", "label": "Customization", "hint": "How much it can be tailored to your situation"},
    {"key": "simp", "label": "Simplicity", "hint": "How simple it is to set up and run"},
]

# ── the five strategy families ────────────────────────────────────────────────────────────────────
BUCKETS = [
    {"key": "selling", "label": "Selling", "color": "#9b4439", "blurb": "Sell outright or in stages."},
    {"key": "harvesting", "label": "Harvesting", "color": "#a9853f",
     "blurb": "Bank capital losses to fund a tax-neutral exit."},
    {"key": "hedging", "label": "Hedging", "color": "#4a6d8c",
     "blurb": "Cap or offset the price risk with options or forwards."},
    {"key": "deferring", "label": "Deferring", "color": "#15806a",
     "blurb": "Diversify in-kind and defer the gain."},
    {"key": "giving", "label": "Giving", "color": "#6b4e8c",
     "blurb": "Give the shares to family, a foundation, or charity."},
]

# ── filter dimensions (goal / timeline / complexity / insider) ────────────────────────────────────
GOALS = [
    {"key": "tax", "label": "Minimize tax"}, {"key": "hedge", "label": "Hedge price risk"},
    {"key": "liq", "label": "Keep high liquidity"}, {"key": "give", "label": "Donate to charity"},
]
TIMELINES = [
    {"key": "now", "label": "Immediate de-risking"}, {"key": "staged", "label": "Staged / gradual exit"},
    {"key": "lock", "label": "No immediate liquidity needs"},
]

# score, human label per axis in AXES order: (liq, spd, cost, tax, cust, simp); scores from the supplied
# survey. goals/timelines/simple/insider are our own factual tags used only for filtering.
_S = "score"
STRATEGIES = [
    {"key": "sellall", "name": "Sell it all", "bucket": "selling",
     "scores": {"liq": (5, "High"), "spd": (5, "Immediate"), "cost": (5, "Low"), "tax": (1, "Very High"),
                "cust": (1, "Low"), "simp": (5, "Simple")},
     "goals": ["liq"], "timelines": ["now"], "simple": True, "insider_ok": True,
     "blurb": "Liquidate the whole position at once — the cleanest, cheapest, most immediate way to remove "
              "single-stock risk. A low basis means the entire gain is realized and taxed in one year."},
    {"key": "staged", "name": "Staged selling", "bucket": "selling",
     "scores": {"liq": (4, "Above average"), "spd": (2, "Slow"), "cost": (5, "Low"), "tax": (3, "Moderate"),
                "cust": (3, "Moderate"), "simp": (5, "Simple")},
     "goals": ["liq", "tax"], "timelines": ["staged"], "simple": True, "insider_ok": True,
     "blurb": "Sell in planned tranches over several years, often through a 10b5-1 plan, spreading the gain "
              "across tax years to manage brackets. You carry the concentrated risk longer while you exit."},
    {"key": "lolh", "name": "Long-only harvesting", "bucket": "harvesting",
     "scores": {"liq": (5, "High"), "spd": (2, "Slow"), "cost": (3, "Moderate"), "tax": (3, "Moderate"),
                "cust": (5, "High"), "simp": (4, "Above average")},
     "goals": ["tax", "liq"], "timelines": ["staged", "lock"], "simple": False, "insider_ok": True,
     "blurb": "Hold the position inside a tax-managed separate account that continuously harvests losses "
              "elsewhere, banking them to offset the gain as you trim. Slow, but keeps you fully invested."},
    {"key": "tals", "name": "Tax-aware long/short", "bucket": "harvesting",
     "scores": {"liq": (4, "Above average"), "spd": (3, "Staged"), "cost": (2, "High"), "tax": (5, "Low"),
                "cust": (5, "High"), "simp": (1, "Complex")},
     "goals": ["tax"], "timelines": ["staged"], "simple": False, "insider_ok": True,
     "blurb": "A long/short extension (e.g. 130/30) that manufactures capital losses through short-side "
              "turnover to offset the gains from selling the stock. Tax-efficient and flexible, but complex "
              "and higher-fee."},
    {"key": "vpf", "name": "Variable prepaid forward", "bucket": "hedging",
     "scores": {"liq": (4, "Above average"), "spd": (5, "Immediate"), "cost": (3, "Moderate"), "tax": (4, "Below average"),
                "cust": (5, "High"), "simp": (1, "Complex")},
     "goals": ["hedge", "tax"], "timelines": ["now", "lock"], "simple": False, "insider_ok": False,
     "blurb": "A forward that advances cash today (typically 75–90% of value) against shares delivered "
              "later, capping upside and buffering downside. Defers the gain and frees liquidity, but it's a "
              "complex, negotiated derivative."},
    {"key": "collar", "name": "Option collar", "bucket": "hedging",
     "scores": {"liq": (4, "Above average"), "spd": (5, "Immediate"), "cost": (3, "Moderate"), "tax": (3, "Moderate"),
                "cust": (5, "High"), "simp": (2, "Below average")},
     "goals": ["hedge"], "timelines": ["now"], "simple": False, "insider_ok": False,
     "blurb": "Buy a put and sell a call to bracket the stock inside a price range, hedging downside for "
              "little or no net premium. Immediate protection with high flexibility; you give up upside "
              "above the call strike."},
    {"key": "proxycollar", "name": "Proxy collar", "bucket": "hedging",
     "scores": {"liq": (4, "Above average"), "spd": (5, "Immediate"), "cost": (3, "Moderate"), "tax": (4, "Below average"),
                "cust": (5, "High"), "simp": (1, "Complex")},
     "goals": ["hedge"], "timelines": ["now"], "simple": False, "insider_ok": True,
     "blurb": "A collar written on a correlated index or ETF rather than the single stock — useful when "
              "options on the stock are illiquid or restricted. Hedges market risk but leaves the "
              "idiosyncratic, company-specific risk in place."},
    {"key": "covcall", "name": "Covered call", "bucket": "hedging",
     "scores": {"liq": (4, "Above average"), "spd": (1, "Gradual"), "cost": (3, "Moderate"), "tax": (2, "High"),
                "cust": (4, "Above average"), "simp": (3, "Moderate")},
     "goals": ["hedge", "liq"], "timelines": ["staged", "lock"], "simple": False, "insider_ok": False,
     "blurb": "Sell call options against the shares for premium income, nudging you toward a gradual exit "
              "if the stock is called away. Simple and income-producing, but it caps upside and does little "
              "for downside risk."},
    {"key": "protput", "name": "Protective put", "bucket": "hedging",
     "scores": {"liq": (3, "Moderate"), "spd": (5, "Immediate"), "cost": (3, "Moderate"), "tax": (3, "Moderate"),
                "cust": (4, "Above average"), "simp": (4, "Above average")},
     "goals": ["hedge"], "timelines": ["now"], "simple": True, "insider_ok": False,
     "blurb": "Buy put options as insurance against a decline while keeping full upside. Immediate, "
              "tailored downside protection — but the premium is a recurring cost and it offers no tax "
              "deferral."},
    {"key": "exrep", "name": "Synthetic exchange fund", "bucket": "hedging",
     "scores": {"liq": (4, "Above average"), "spd": (5, "Immediate"), "cost": (3, "Moderate"), "tax": (4, "Below average"),
                "cust": (5, "High"), "simp": (1, "Complex")},
     "goals": ["hedge", "tax"], "timelines": ["now", "lock"], "simple": False, "insider_ok": False,
     "blurb": "Replicate an exchange-fund-style diversified exposure with derivatives while keeping the "
              "shares, hedging concentration without a taxable sale. Flexible and tax-deferring, but "
              "structurally complex."},
    {"key": "collarls", "name": "SMA collar + long/short", "bucket": "hedging",
     "scores": {"liq": (4, "Above average"), "spd": (5, "Immediate"), "cost": (2, "High"), "tax": (5, "Low"),
                "cust": (5, "High"), "simp": (1, "Complex")},
     "goals": ["hedge", "tax"], "timelines": ["now"], "simple": False, "insider_ok": False,
     "blurb": "Combine an option collar with a tax-aware long/short sleeve, hedging the position while "
              "harvesting offsetting losses to fund a tax-efficient exit. Powerful and highly customizable, "
              "but complex and higher-fee."},
    {"key": "collarbox", "name": "Collar + box spread", "bucket": "hedging",
     "scores": {"liq": (4, "Above average"), "spd": (5, "Immediate"), "cost": (2, "High"), "tax": (4, "Below average"),
                "cust": (5, "High"), "simp": (1, "Complex")},
     "goals": ["hedge", "tax"], "timelines": ["now", "lock"], "simple": False, "insider_ok": False,
     "blurb": "Pair a collar with a box-spread financing trade to borrow against the hedged position at "
              "attractive implied rates. Frees liquidity and defers gains, at the cost of considerable "
              "structural complexity."},
    {"key": "completion", "name": "Completion portfolio", "bucket": "hedging",
     "scores": {"liq": (3, "Moderate"), "spd": (2, "Slow"), "cost": (2, "High"), "tax": (4, "Below average"),
                "cust": (4, "Above average"), "simp": (2, "Below average")},
     "goals": ["hedge"], "timelines": ["staged", "lock"], "simple": False, "insider_ok": True,
     "blurb": "Build a diversifying portfolio around the concentrated stock so the total book tracks a "
              "broad benchmark, reducing the position's marginal risk without selling it. Gradual, and it "
              "doesn't remove the underlying gain."},
    {"key": "351", "name": "351 conversion", "bucket": "deferring",
     "scores": {"liq": (4, "Above average"), "spd": (5, "Immediate"), "cost": (3, "Moderate"), "tax": (5, "Low"),
                "cust": (1, "Low"), "simp": (2, "Below average")},
     "goals": ["tax"], "timelines": ["now", "lock"], "simple": False, "insider_ok": True,
     "blurb": "Contribute the appreciated shares, alongside other assets, into a new fund in a tax-free "
              "§351 exchange, emerging with a diversified, tax-deferred stake. Immediate diversification "
              "with low tax cost, but little customization and strict qualification rules."},
    {"key": "exfund", "name": "Exchange fund", "bucket": "deferring",
     "scores": {"liq": (1, "Low"), "spd": (5, "Immediate"), "cost": (2, "High"), "tax": (5, "Low"),
                "cust": (1, "Low"), "simp": (3, "Moderate")},
     "goals": ["tax"], "timelines": ["lock"], "simple": False, "insider_ok": True,
     "blurb": "Swap the shares into a commingled partnership of many contributors' concentrated stocks, "
              "receiving a pro-rata diversified interest with the gain deferred. Diversifies without a sale, "
              "but typically requires a ~7-year lock-up and offers little liquidity or control."},
    {"key": "qof", "name": "Opportunity fund (QOF)", "bucket": "deferring",
     "scores": {"liq": (1, "Low"), "spd": (5, "Immediate"), "cost": (2, "High"), "tax": (4, "Below average"),
                "cust": (3, "Moderate"), "simp": (2, "Below average")},
     "goals": ["tax"], "timelines": ["lock"], "simple": False, "insider_ok": True,
     "blurb": "Roll the realized gain into a Qualified Opportunity Fund to defer (and potentially reduce) "
              "the tax while investing in designated projects. Defers the gain, but capital is illiquid for "
              "years and returns depend on the underlying real assets."},
    {"key": "margin", "name": "Margin loan", "bucket": "deferring",
     "scores": {"liq": (5, "High"), "spd": (1, "Gradual"), "cost": (3, "Moderate"), "tax": (5, "Low"),
                "cust": (2, "Below average"), "simp": (4, "Above average")},
     "goals": ["liq", "tax"], "timelines": ["lock"], "simple": True, "insider_ok": True,
     "blurb": "Borrow against the position instead of selling, accessing cash while the shares — and the "
              "unrealized gain — stay in place. Highly liquid and tax-free at inception, but it leaves the "
              "concentration risk intact and adds leverage."},
    {"key": "crut", "name": "Charitable remainder unitrust", "bucket": "giving",
     "scores": {"liq": (3, "Moderate"), "spd": (5, "Immediate"), "cost": (3, "Moderate"), "tax": (3, "Moderate"),
                "cust": (5, "High"), "simp": (2, "Below average")},
     "goals": ["give", "tax"], "timelines": ["now", "lock"], "simple": False, "insider_ok": True,
     "blurb": "Gift the shares to a CRUT, which sells them tax-free and pays you an income stream for life, "
              "with the remainder to charity. Diversifies immediately and yields an upfront deduction, but "
              "the gift is irrevocable."},
    {"key": "daf", "name": "Donor-advised fund", "bucket": "giving",
     "scores": {"liq": (1, "Low"), "spd": (5, "Immediate"), "cost": (4, "Below average"), "tax": (5, "Low"),
                "cust": (3, "Moderate"), "simp": (4, "Above average")},
     "goals": ["give", "tax"], "timelines": ["now"], "simple": True, "insider_ok": True,
     "blurb": "Donate appreciated shares to a donor-advised fund for an immediate fair-market-value "
              "deduction and no capital-gains tax, then recommend grants over time. Tax-efficient and "
              "simple, but the assets are permanently earmarked for charity."},
    {"key": "directgift", "name": "Direct gift", "bucket": "giving",
     "scores": {"liq": (1, "Low"), "spd": (5, "Immediate"), "cost": (5, "Low"), "tax": (5, "Low"),
                "cust": (1, "Low"), "simp": (5, "Simple")},
     "goals": ["give", "tax"], "timelines": ["now"], "simple": True, "insider_ok": True,
     "blurb": "Give the appreciated shares directly to a public charity, avoiding the gain entirely and "
              "deducting fair market value. The simplest, lowest-cost charitable route — but you part with "
              "the asset and get no income back."},
    {"key": "famgift", "name": "Family or foundation gift", "bucket": "giving",
     "scores": {"liq": (2, "Restricted"), "spd": (5, "Immediate"), "cost": (4, "Below average"), "tax": (4, "Below average"),
                "cust": (4, "Above average"), "simp": (3, "Moderate")},
     "goals": ["give"], "timelines": ["now", "lock"], "simple": False, "insider_ok": True,
     "blurb": "Transfer shares to family members (or a private foundation) to shift future appreciation and "
              "use gift/estate exemptions. Removes concentration from your estate, though carryover basis "
              "and gift-tax limits apply."},
    {"key": "uslit", "name": "Pooled income fund", "bucket": "giving",
     "scores": {"liq": (3, "Moderate"), "spd": (5, "Immediate"), "cost": (4, "Below average"), "tax": (5, "Low"),
                "cust": (1, "Low"), "simp": (4, "Above average")},
     "goals": ["give", "tax"], "timelines": ["now", "lock"], "simple": True, "insider_ok": True,
     "blurb": "Contribute shares to a charity-run pooled income fund that sells them tax-free, pays you a "
              "share of the pool's income for life, and directs the remainder to the charity. Tax-efficient "
              "lifetime income, but little control and an irrevocable gift."},
]

# Investment-committee "fit" notes — how a large, tax-aware holder would think about each approach:
# when it's typically on the table, where it fits, and where it doesn't. Qualitative orientation drawn
# from each strategy's mechanics (the same "one analyst's read" caveat as the scores) — not a
# recommendation about any specific holding.
FIT = {
    "sellall": {
        "inst": "Rarely — only when the position no longer fits the mandate at any tax cost.",
        "when": "The risk has to be gone now and the basis is high, so little gain is taxed.",
        "less": "The basis is low and realizing the whole gain in one year is punitive."},
    "staged": {
        "inst": "The default for winding down a large holding, usually under a written 10b5-1 plan.",
        "when": "You can exit over several years and want to spread the gain across tax years.",
        "less": "The single-stock risk is acute and can't wait for a multi-year exit."},
    "lolh": {
        "inst": "Standard practice inside tax-managed separate accounts for taxable investors.",
        "when": "You want to stay invested while losses are banked to offset the exit.",
        "less": "You need to be fully out quickly, or the account is too small to harvest efficiently."},
    "tals": {
        "inst": "Used by large taxable portfolios to manufacture offsetting losses at scale.",
        "when": "The gain is large, the horizon is multi-year, and fees and complexity are acceptable.",
        "less": "The position is small, or you want a simple, low-cost approach."},
    "vpf": {
        "inst": "A treasury tool for executives monetizing a restricted holding without selling.",
        "when": "You want cash and downside protection now and can defer the sale.",
        "less": "You're an insider or affiliate, or you want to keep the full upside."},
    "collar": {
        "inst": "Common for hedging a concentrated public position over a defined window.",
        "when": "You want immediate, low-cost downside protection and can give up some upside.",
        "less": "You're restricted from trading the stock's options, or want unlimited upside."},
    "proxycollar": {
        "inst": "Used when direct options are illiquid, restricted, or too costly.",
        "when": "You want market-risk protection and the stock tracks a liquid index.",
        "less": "The company-specific risk is the real worry — a proxy won't hedge it."},
    "covcall": {
        "inst": "An income overlay, not a primary de-risking tool, for large holders.",
        "when": "You're comfortable being called away gradually and want premium income.",
        "less": "You need real downside protection or a fast exit."},
    "protput": {
        "inst": "Straightforward insurance to cap downside ahead of a known event.",
        "when": "You want to keep full upside and will pay a premium for downside cover.",
        "less": "The recurring premium is too costly to carry for a long holding period."},
    "exrep": {
        "inst": "A bespoke derivative solution for very large, sophisticated holders.",
        "when": "You want diversified exposure without selling and can handle the complexity.",
        "less": "You want simplicity, low cost, or a clean, transparent structure."},
    "collarls": {
        "inst": "A combined overlay large taxable accounts use to hedge and harvest at once.",
        "when": "You want both downside protection and offsetting losses to fund an exit.",
        "less": "The position is modest, or fees and complexity outweigh the benefit."},
    "collarbox": {
        "inst": "A financing structure for borrowing against a hedged position.",
        "when": "You want liquidity and gain deferral and can manage a complex trade.",
        "less": "You want simplicity, or don't need to borrow against the position."},
    "completion": {
        "inst": "A core technique — build the rest of the book around the position's risk.",
        "when": "You'll hold the stock a while and want to cut its marginal risk without selling.",
        "less": "You need the underlying gain resolved, not just diluted."},
    "351": {
        "inst": "Used to seed a diversified fund tax-free from concentrated contributions.",
        "when": "You want immediate diversification at low tax cost and accept little control.",
        "less": "You need customization, or can't meet the strict qualification rules."},
    "exfund": {
        "inst": "A long-standing route for executives to diversify without a taxable sale.",
        "when": "You can lock up capital for years to diversify with the gain deferred.",
        "less": "You need liquidity, control, or a shorter horizon."},
    "qof": {
        "inst": "Used to defer a realized gain while funding designated long-horizon projects.",
        "when": "You've realized a gain and want to defer it in a patient investment.",
        "less": "You need liquidity, or don't want project-level real-asset risk."},
    "margin": {
        "inst": "Treasury-style borrowing against securities to raise cash without selling.",
        "when": "You need liquidity now and intend to keep the position.",
        "less": "You want the concentration reduced — this leaves it intact and adds leverage."},
    "crut": {
        "inst": "A classic planned-giving vehicle for appreciated, low-basis stock.",
        "when": "You're charitably inclined and want lifetime income plus an upfront deduction.",
        "less": "You may need the principal back — the gift is irrevocable."},
    "daf": {
        "inst": "The simplest institutional-grade way to donate appreciated shares.",
        "when": "You plan to give and want the deduction now, with grants made over time.",
        "less": "You might want the assets back — they're permanently earmarked for charity."},
    "directgift": {
        "inst": "The plainest charitable route — shares straight to a public charity.",
        "when": "You want to give a set amount simply and avoid the gain entirely.",
        "less": "You want income back or ongoing control of the gift."},
    "famgift": {
        "inst": "An estate technique to shift future appreciation out of the estate.",
        "when": "You want to move concentration and future growth to heirs or a foundation.",
        "less": "You need the value yourself, or gift and estate limits bind."},
    "uslit": {
        "inst": "A charity-run vehicle for lifetime income from donated appreciated stock.",
        "when": "You want tax-efficient lifetime income and will give the remainder to charity.",
        "less": "You want control of the assets, or a revocable arrangement."},
}

# Article lede shown above the interactive guide (our own copy).
ARTICLE = {
    "eyebrow": "Too much of a good thing",
    "title": "How to de-risk a concentrated stock position",
    "lead": "A concentrated, low-basis position is one of the hardest problems in taxable wealth. "
            "Every way to de-risk it, scored on the tradeoffs that matter.",
    "body": [
        "A single stock that dominates your net worth puts you in a bind. "
        "Sell, and a low cost basis means a heavy tax bill. Hold, and you carry idiosyncratic risk the "
        "market never compensates you for bearing.",
        "There is no clean answer, only tradeoffs. Every approach moves you along the same handful of "
        "axes: how much liquidity it frees, how quickly it cuts the risk, what it costs in fees and tax "
        "drag, how much you can tailor it, and how complex it is to run.",
        "The strategies sort into five families. Sell outright or in stages. Harvest losses to fund a "
        "tax-neutral exit. Hedge the position with options or forwards. Defer the gain by diversifying "
        "in-kind. Or give the shares away — to family, a foundation, or charity.",
        "The interactive guide below scores each strategy across those tradeoffs. Filter to what matters "
        "to you, sort by any column, and tap a row to read how it works.",
    ],
}

_BUCKET_ORDER = {b["key"]: i for i, b in enumerate(BUCKETS)}


def build_concentration() -> dict:
    """Assemble the concentration-tool state: axes, buckets, filter options, and the scored strategies."""
    # validate coverage as we build (every strategy scores every axis and names a real bucket).
    axis_keys = [a["key"] for a in AXES]
    bucket_keys = {b["key"] for b in BUCKETS}
    strategies = []
    for s in sorted(STRATEGIES, key=lambda s: (_BUCKET_ORDER[s["bucket"]], s["name"])):
        assert s["bucket"] in bucket_keys, s["key"]
        assert set(s["scores"]) == set(axis_keys), f"{s['key']} missing an axis score"
        fit = FIT.get(s["key"])
        assert fit and {"inst", "when", "less"} <= set(fit), f"{s['key']} missing a fit note"
        strategies.append({
            "key": s["key"], "name": s["name"], "bucket": s["bucket"], "blurb": s["blurb"],
            "scores": {k: {"n": v[0], "label": v[1]} for k, v in s["scores"].items()},
            "goals": s["goals"], "timelines": s["timelines"],
            "simple": s["simple"], "insider_ok": s["insider_ok"], "fit": fit,
        })
    return {
        "axes": AXES, "buckets": BUCKETS, "goals": GOALS, "timelines": TIMELINES,
        "article": ARTICLE, "strategies": strategies,
    }
