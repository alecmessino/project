"""After-tax modeling for the forward ledger — lot-aware, personalized by tax profile.

This is the wealth-management layer. The plain ledger reports a pre-tax curve; in a
taxable account what a client keeps is the *after-tax* curve, and that depends on how
fast the book turns over (short- vs long-term gains), the client's bracket and state,
and whether losses are harvested. Brent Sullivan's framing (apres.tax / TaxAlphaInsider)
is the bar: after-tax return, the short↔long **rate arbitrage**, harvested losses worth
"the rate of the gain they offset," and the embedded-gain (pre- vs post-liquidation) view.

`after_tax_track` runs a FIFO dollar-lot simulation over the ledger's own daily marks:
each rebalance ages and values the lots, realizes gains/losses on the names it trims,
splits them short- vs long-term by holding period, nets losses into a carryforward
(the harvesting benefit), and pays tax from the book. It needs per-instrument prices on
each entry (`entry["prices"]`); without them it returns None and the caller falls back.

Illustrative — modeled on the book's marks, NOT the custodian's lot accounting, and not
tax advice. Rates come from `config.TaxSettings` (federal + NIIT + state).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .config import TaxSettings

# State long-/short-term capital-gains rates — top-effective figures a high-income resident pays,
# including millionaire/NIIT surtaxes and long-term exclusions. These are the CANONICAL source of
# truth and now live in drift.state_facts (PUBLISHING_SPEC §15.4); the after-tax calculator projects
# them here so it can never disagree with the Atlas display. Each 2025 figure changed from the prior
# encoding is reconciled to a primary/official source in RECONCILIATION_LOG.md. Illustrative — an
# advisor confirms a client's actual situation. (Mirrors TaxAlphaInsider's point that the value of
# tax-loss harvesting is state-dependent.)
from .state_facts import RATES, TERRITORY_CODES  # noqa: E402

# The calculator's scope is the 50 states + DC (+ NYC overlay + federal-only "—"); territories carry
# display rates in the Atlas but no modeled client resides in one, so they are filtered out here.
STATE_RATES: dict[str, tuple[float, float]] = {
    k: v for k, v in RATES.items() if k not in TERRITORY_CODES
}


def profile_for_state(base: TaxSettings, state: str) -> TaxSettings:
    """A copy of `base` with state rates filled from STATE_RATES (label + rates)."""
    slt, sst = STATE_RATES.get(state, (base.state_lt, base.state_st))
    return base.model_copy(update={"state": state, "state_lt": slt, "state_st": sst})


@dataclass
class AfterTax:
    curve: list[float]                 # after-tax equity curve (paid-as-you-go)
    after_tax_return: float            # final after-tax total return
    pretax_return: float               # final pre-tax total return
    tax_drag: float                    # pretax - after_tax (paid along the way)
    tax_paid: float                    # cumulative tax paid (fraction of $1 start)
    st_realized: float                 # gross short-term gains realized
    lt_realized: float                 # gross long-term gains realized
    harvested_losses: float            # gross losses realized (the harvesting raw material)
    annual_turnover: float             # one-sided, per year
    avg_holding_days: Optional[float]
    short_term_share: float            # ST / (ST+LT) of realized gains — the rate-arb knob
    embedded_gain: float               # unrealized gain still in the book (deferral asset)
    liquidation_tax: float             # tax to fully liquidate today
    after_tax_liquidated: float        # after-tax return if liquidated today (post-liquidation)
    rate_lt: float = 0.0
    rate_st: float = 0.0


def _annual_turnover(entries: list[dict], bars_per_year: float) -> tuple[float, Optional[float]]:
    prev: dict[str, float] = {}
    two_sided = 0.0
    for e in entries:
        w = e.get("weights", {})
        two_sided += sum(abs(w.get(k, 0.0) - prev.get(k, 0.0)) for k in set(w) | set(prev))
        prev = w
    n = len(entries)
    years = (n / bars_per_year) if bars_per_year else 0.0
    one_sided = two_sided / 2.0
    ann = (one_sided / years) if years > 0 else 0.0
    avg_hold = (bars_per_year / ann) if ann > 0 else None
    return ann, avg_hold


def after_tax_track(entries: list[dict], tax: TaxSettings,
                    bars_per_year: float = 252.0) -> Optional[AfterTax]:
    """FIFO dollar-lot after-tax simulation over the ledger entries (needs per-name
    prices on each entry). Returns None if prices are unavailable."""
    if not entries or "prices" not in entries[-1] or not entries[-1].get("prices"):
        return None
    rate_lt, rate_st, lt_bars = tax.rate_lt, tax.rate_st, tax.lt_holding_bars

    value = 1.0                                  # after-tax book value
    lots: dict[str, list[list]] = {}             # inst -> [[dollars, price_buy, idx_buy], ...]
    carry_loss = 0.0                             # loss carryforward (offsets future gains)
    tax_paid = st_real = lt_real = harvested = 0.0
    curve: list[float] = []
    prev_w: dict[str, float] = {}
    prev_px: dict[str, float] = {}

    for idx, e in enumerate(entries):
        w = e.get("weights", {})
        px = e.get("prices", {}) or prev_px
        value *= (1.0 + e.get("realized_return", 0.0))   # grow by the session's net return

        rebalanced = idx == 0 or any(
            abs(w.get(k, 0.0) - prev_w.get(k, 0.0)) > 1e-9 for k in set(w) | set(prev_w))
        if rebalanced:
            sess_st = sess_lt = 0.0
            for i in set(w) | set(lots):
                price = px.get(i) or prev_px.get(i)
                if not price:
                    continue
                cur_val = sum(d * price / pb for d, pb, _ in lots.get(i, []))
                tgt = w.get(i, 0.0) * value
                if tgt < cur_val - 1e-12:                # SELL the excess, FIFO
                    to_sell = cur_val - tgt
                    q = lots.get(i, [])
                    while to_sell > 1e-12 and q:
                        d, pb, bi = q[0]
                        lot_val = d * price / pb
                        take = min(lot_val, to_sell)
                        frac = (take / lot_val) if lot_val else 0.0
                        gain = take - d * frac           # proceeds - basis sold
                        if idx - bi >= lt_bars:
                            sess_lt += gain
                        else:
                            sess_st += gain
                        if take >= lot_val - 1e-12:
                            q.pop(0)
                        else:
                            q[0][0] = d * (1.0 - frac)
                        to_sell -= take
                elif tgt > cur_val + 1e-12:              # BUY -> new lot at today's price
                    lots.setdefault(i, []).append([tgt - cur_val, price, idx])

            st_real += max(0.0, sess_st)
            lt_real += max(0.0, sess_lt)
            harvested += max(0.0, -sess_st) + max(0.0, -sess_lt)
            # Net losses bank into the carryforward; gains are offset (short-term first,
            # the higher rate = the most valuable offset — the rate-arbitrage point),
            # then taxed at the remaining character's rate.
            carry_loss += max(0.0, -sess_st) + max(0.0, -sess_lt)
            g_st, g_lt = max(0.0, sess_st), max(0.0, sess_lt)
            off = min(carry_loss, g_st); g_st -= off; carry_loss -= off
            off = min(carry_loss, g_lt); g_lt -= off; carry_loss -= off
            t = g_st * rate_st + g_lt * rate_lt
            if t:
                value -= t
                tax_paid += t
            prev_w = w
        prev_px = px
        curve.append(round(value, 6))

    # Embedded (unrealized) gain still in the book and the tax to liquidate it today.
    last_px = entries[-1].get("prices", {})
    cur_val = basis = 0.0
    liq_tax = 0.0
    n = len(entries)
    for i, q in lots.items():
        price = last_px.get(i)
        if not price:
            continue
        for d, pb, bi in q:
            v = d * price / pb
            cur_val += v
            basis += d
            gain = v - d
            if gain > 0:
                liq_tax += gain * (rate_lt if (n - 1 - bi) >= lt_bars else rate_st)
    liq_tax = max(0.0, liq_tax - carry_loss * rate_lt)   # remaining losses shield liquidation
    embedded = cur_val - basis

    ann, avg_hold = _annual_turnover(entries, bars_per_year)
    pretax = entries[-1]["equity"] - 1.0
    after = curve[-1] - 1.0
    realized_total = st_real + lt_real
    return AfterTax(
        curve=curve,
        after_tax_return=round(after, 6),
        pretax_return=round(pretax, 6),
        tax_drag=round(pretax - after, 6),
        tax_paid=round(tax_paid, 6),
        st_realized=round(st_real, 6),
        lt_realized=round(lt_real, 6),
        harvested_losses=round(harvested, 6),
        annual_turnover=round(ann, 3),
        avg_holding_days=(round(avg_hold) if avg_hold else None),
        short_term_share=round(st_real / realized_total, 4) if realized_total else 0.0,
        embedded_gain=round(embedded, 6),
        liquidation_tax=round(liq_tax, 6),
        after_tax_liquidated=round(after - liq_tax, 6),
        rate_lt=round(rate_lt, 4),
        rate_st=round(rate_st, 4),
    )


@dataclass
class GainProfile:
    """Rate-INDEPENDENT decomposition of the book's gains on its pre-tax path, so a
    client-side Tax Lab can recompute after-tax / TLH / location alpha for any bracket
    and state. All amounts are per $1 invested at inception."""
    pretax_return: float
    st_realized: float          # gross short-term realized gains
    lt_realized: float          # gross long-term realized gains
    harvested_st: float         # short-term realized losses (harvest material)
    harvested_lt: float         # long-term realized losses
    embedded_st: float          # unrealized gains in lots still < 1y old
    embedded_lt: float          # unrealized gains in lots >= 1y old
    annual_turnover: float
    avg_holding_days: Optional[float]
    short_term_share: float


def gain_profile(entries: list[dict], lt_holding_bars: int = 252,
                 bars_per_year: float = 252.0) -> Optional[GainProfile]:
    """FIFO dollar-lot walk on the PRE-TAX path (no tax deducted), returning the gross
    realized/embedded gains split short- vs long-term. Rate-independent — apply any
    rates downstream. None if the entries carry no per-name prices."""
    if not entries or "prices" not in entries[-1] or not entries[-1].get("prices"):
        return None
    value = 1.0
    lots: dict[str, list[list]] = {}
    st_real = lt_real = harv_st = harv_lt = 0.0
    prev_w: dict[str, float] = {}
    prev_px: dict[str, float] = {}
    for idx, e in enumerate(entries):
        w = e.get("weights", {})
        px = e.get("prices", {}) or prev_px
        value *= (1.0 + e.get("realized_return", 0.0))
        rebalanced = idx == 0 or any(
            abs(w.get(k, 0.0) - prev_w.get(k, 0.0)) > 1e-9 for k in set(w) | set(prev_w))
        if rebalanced:
            for i in set(w) | set(lots):
                price = px.get(i) or prev_px.get(i)
                if not price:
                    continue
                cur_val = sum(d * price / pb for d, pb, _ in lots.get(i, []))
                tgt = w.get(i, 0.0) * value
                if tgt < cur_val - 1e-12:
                    to_sell = cur_val - tgt
                    q = lots.get(i, [])
                    while to_sell > 1e-12 and q:
                        d, pb, bi = q[0]
                        lot_val = d * price / pb
                        take = min(lot_val, to_sell)
                        frac = (take / lot_val) if lot_val else 0.0
                        gain = take - d * frac
                        is_lt = (idx - bi) >= lt_holding_bars
                        if gain >= 0:
                            if is_lt: lt_real += gain
                            else: st_real += gain
                        else:
                            if is_lt: harv_lt += -gain
                            else: harv_st += -gain
                        if take >= lot_val - 1e-12:
                            q.pop(0)
                        else:
                            q[0][0] = d * (1.0 - frac)
                        to_sell -= take
                elif tgt > cur_val + 1e-12:
                    lots.setdefault(i, []).append([tgt - cur_val, price, idx])
            prev_w = w
        prev_px = px

    last_px = entries[-1].get("prices", {})
    n = len(entries)
    emb_st = emb_lt = 0.0
    for i, q in lots.items():
        price = last_px.get(i)
        if not price:
            continue
        for d, pb, bi in q:
            gain = d * price / pb - d
            if gain > 0:
                if (n - 1 - bi) >= lt_holding_bars:
                    emb_lt += gain
                else:
                    emb_st += gain
    ann, avg_hold = _annual_turnover(entries, bars_per_year)
    realized = st_real + lt_real
    return GainProfile(
        pretax_return=round(entries[-1]["equity"] - 1.0, 6),
        st_realized=round(st_real, 6), lt_realized=round(lt_real, 6),
        harvested_st=round(harv_st, 6), harvested_lt=round(harv_lt, 6),
        embedded_st=round(emb_st, 6), embedded_lt=round(emb_lt, 6),
        annual_turnover=round(ann, 3),
        avg_holding_days=(round(avg_hold) if avg_hold else None),
        short_term_share=round(st_real / realized, 4) if realized else 0.0,
    )
