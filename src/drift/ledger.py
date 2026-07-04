"""Model-portfolio ledger: an append-only HYPOTHETICAL backtest of the strategy.

This is the retroactive application of a quantitative model to historical data — a
hypothetical Model Portfolio, NOT actual trading and NOT any client account. Each
session it (a) marks the positions held from the prior session against the prices that
printed, (b) advances a cumulative equity, and (c) records the next target positions.
It only ever appends — history is never recomputed.

The live book is the **Unconstrained Core Alpha Strategy**: the long-only, fully-invested cross-sectional
momentum rotation — the trending top half of the region/size/style ETF matrix,
inverse-volatility weighted, with NO discretionary factor tilt (a 40-year test of an
EM/value/small overweight showed it added risk, not risk-adjusted return) — marked daily.
No cash and no leverage: always ~100% invested. Its high turnover suits tax-advantaged
accounts; a separate, offline-validated **Tax-Managed Core Strategy**
(12-month drift, asymmetric rank hysteresis, and tax-lot aging — config/slow.yaml) is the
taxable-located companion and is **not** part of this live track. Weekends/holidays fall
out naturally: an instrument is marked from its last close on-or-before the prior ledger
date to its latest close, so a Friday→Monday move lands on the next run.
"""

from __future__ import annotations

import time
from typing import Optional, Sequence

from . import analytics
from . import signal as sig
from . import sizing
from .config import Settings, TaxSettings
from .tax import after_tax_track
from .cross_section import _combined_tilt, _groups_for, _tax_aware_weights, rank_weights
from .models import Bar
from .universes import BENCH_REGION, REGION_OF, STYLE_BOX


def _latest_date(series: dict[str, list[Bar]]) -> str:
    return max((bars[-1].asof for bars in series.values() if bars), default="")


def _close_on_or_before(bars: Sequence[Bar], date10: str) -> Optional[float]:
    """Close of the last bar whose date is <= `date10` (YYYY-MM-DD)."""
    found = None
    for b in bars:
        if b.asof[:10] <= date10:
            found = b.close
        else:
            break
    return found


def new_ledger() -> dict:
    return {"entries": [], "universe": [], "inception": "", "updated": ""}


def update_ledger(ledger: dict, series: dict[str, list[Bar]], settings: Settings,
                  seed: bool = False,
                  benchmarks: Optional[dict[str, list[Bar]]] = None) -> dict:
    """Append one session to the ledger for the latest date. Idempotent: a date
    already recorded (or no fresh bar) is a no-op. `benchmarks` maps a label (e.g.
    "VT", "VTI") to its bars; each is marked buy-and-hold alongside the book for an
    apples-to-apples, total-return comparison."""
    cost = settings.sizing.cost_bps_per_side / 1e4
    insts = sorted(i for i, b in series.items() if len(b) >= settings.signal.min_history)
    if not insts:
        return ledger
    latest = _latest_date({i: series[i] for i in insts})
    entries = ledger.setdefault("entries", [])
    if entries and entries[-1]["date"] >= latest[:10]:
        return ledger  # nothing new to mark

    prev = entries[-1] if entries else None
    prev_w: dict[str, float] = prev["weights"] if prev else {}
    equity = prev["equity"] if prev else 1.0
    prev_bench: dict[str, float] = (prev.get("bench_equity") if prev else None) or {}

    # 1) Realize the previously-held cross-sectional book (weights sum to exposure,
    #    so the portfolio return is the weighted sum — not an average).
    realized = 0.0
    if prev:
        for i in insts:
            p_prev = _close_on_or_before(series[i], prev["date"])
            p_now = series[i][-1].close
            if p_prev and p_now:
                realized += prev_w.get(i, 0.0) * (p_now / p_prev - 1.0)

    # 2) New target = the long-only, fully-invested cross-sectional momentum rotation
    #    (unbiased — tilt multipliers ship neutral), re-ranked on the rebalance cadence
    #    (held between rebalances so turnover stays low). The per-name trend z + vol are computed
    #    EVERY session (not just on rebalances) so they can be persisted as the book's signal strength.
    cs = settings.cross_section
    n_prior = len(entries)
    sg = settings.signal
    scores, vols, closes_now = {}, {}, {}
    for i in insts:
        cl = [b.close for b in series[i]]
        closes_now[i] = cl
        scores[i] = sig.momentum_score(cl, sg.lookback, sg.vol_window)
        vols[i] = sizing.annualize_vol(sig.realized_vol(cl, sg.vol_window),
                                       settings.engine.bars_per_year)
    if prev and (n_prior % max(1, cs.rebalance_bars) != 0):
        new_w = {i: round(prev_w.get(i, 0.0), 4) for i in insts}
    else:
        held = {i for i, w in prev_w.items() if w > 0}
        raw = rank_weights(scores, vols, cs, _groups_for(cs), _combined_tilt(closes_now, cs), held)
        raw = _tax_aware_weights(raw, prev_w, cs)   # no-trade band (taxable sleeve); no-op when off
        new_w = {i: round(raw.get(i, 0.0), 4) for i in insts}
    # Signal strength (trend z) + annualized vol per name — persisted so the dashboard projects them
    # over the book's exact universe/date with no independent fetch (single source of truth).
    signals = {i: {"z": round(scores[i], 4), "vol": round(vols[i], 4)} for i in insts}

    # 3) Cost on rebalance turnover (weights are at portfolio scale).
    turnover = sum(abs(new_w[i] - prev_w.get(i, 0.0)) for i in insts)
    net = realized - cost * turnover
    equity = round(equity * (1.0 + net), 6)

    # 4) Mark each buy-and-hold benchmark over the same span (if provided).
    bench_equity: Optional[dict[str, float]] = None
    if benchmarks:
        bench_equity = {}
        for label, bars in benchmarks.items():
            be = prev_bench.get(label, 1.0) or 1.0
            bench_ret = 0.0
            if prev and bars:
                bp = _close_on_or_before(bars, prev["date"])
                bn = _close_on_or_before(bars, latest[:10])
                if bp and bn:
                    bench_ret = bn / bp - 1.0
            bench_equity[label] = round(be * (1.0 + bench_ret), 6)

    entries.append({
        "date": latest[:10],
        "weights": new_w,
        # Per-name close used to mark this session — the lot basis for after-tax modeling.
        "prices": {i: round(series[i][-1].close, 6) for i in insts},
        # Per-name signal strength (trend z) + annualized vol — the dashboard's Signal-strength column.
        "signals": signals,
        "realized_return": round(net, 6),
        "equity": equity,
        "bench_equity": bench_equity,
        "n_long": sum(1 for v in new_w.values() if v > 0),
        "n_short": sum(1 for v in new_w.values() if v < 0),
        "seed": bool(seed),
    })
    ledger["universe"] = insts
    ledger["inception"] = ledger.get("inception") or entries[0]["date"]
    ledger["cost_bps_per_side"] = settings.sizing.cost_bps_per_side
    ledger["rebalance_bars"] = settings.cross_section.rebalance_bars
    ledger["updated"] = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    return ledger


def seed_ledger(series: dict[str, list[Bar]], settings: Settings, sessions: int = 120,
                benchmarks: Optional[dict[str, list[Bar]]] = None) -> dict:
    """Bootstrap a ledger by replaying the last `sessions` trading days walk-forward.

    This is a faithful out-of-sample replay (each step sees only data up to that
    date — no lookahead), so the inception curve is meaningful rather than empty.
    Live runs append the newest day on top via `update_ledger`.
    """
    ledger = new_ledger()
    all_dates = sorted({b.asof[:10] for bars in series.values() for b in bars})
    for d in all_dates[-sessions:]:
        sub = {i: [b for b in bars if b.asof[:10] <= d] for i, bars in series.items()}
        bench = ({label: [b for b in bars if b.asof[:10] <= d]
                  for label, bars in benchmarks.items()} if benchmarks else None)
        update_ledger(ledger, sub, settings, seed=True, benchmarks=bench)
    return ledger


_REGION_NAME = {"US": "United States", "DEV": "Developed intl", "EM": "Emerging mkts"}
_BENCH_COLORS = {"VT": "#3257c4", "VTI": "#c2790f"}
_BENCH_DIV_YIELD = 0.018   # ~qualified-dividend yield of a broad market index (for after-tax)


def _bench_after_tax(brets: list[float], r_lt: float, bars_per_year: float,
                     div_yield: float = _BENCH_DIV_YIELD) -> float:
    """After-tax total return of a buy-and-hold benchmark, paid-as-you-go.

    A buy-and-hold index realizes no capital gains until it is sold, so its only annual
    drag is tax on qualified dividends at the long-term rate. Apply that as a small per-bar
    reduction and compound; the liquidation tax on the embedded gain is excluded, to match
    the strategy's paid-as-you-go after-tax basis (an apples-to-apples taxable comparison).
    Illustrative."""
    d = div_yield * max(0.0, r_lt) / (bars_per_year or 252.0)
    v = 1.0
    for r in brets:
        v *= (1.0 + r - d)
    return v - 1.0


def _blend_style_box(weights: dict[str, float]) -> dict[str, float]:
    """Blend each holding's underlying 9-cell style-box composition by its weight,
    so the result is the book's true Morningstar-style footprint (not one box per
    fund). Normalized to shares of the classified gross."""
    box: dict[str, float] = {}
    for inst, w in weights.items():
        if w <= 0:
            continue
        comp = STYLE_BOX.get(inst)
        if not comp:
            continue
        csum = sum(comp.values()) or 1.0
        for cell, share in comp.items():
            if share:
                box[cell] = box.get(cell, 0.0) + w * share / csum
    total = sum(box.values()) or 1.0
    return {k: round(v / total, 4) for k, v in box.items()}


def _by_style(style_box: dict[str, float]) -> dict[str, float]:
    out: dict[str, float] = {}
    for cell, v in style_box.items():
        st = cell.split("|")[1]
        out[st] = round(out.get(st, 0.0) + v, 4)
    return out


def _exposure(weights: dict[str, float]) -> dict:
    """Region breakdown + blended 3x3 style box of the current long book, as shares
    of invested gross. Region is one-per-fund (REGION_OF); the style box uses each
    fund's underlying composition (STYLE_BOX), blended by weight."""
    pos = {i: w for i, w in weights.items() if w > 0}
    total = sum(pos.values()) or 1.0
    region: dict[str, float] = {}
    for i, w in pos.items():
        r = REGION_OF.get(i, "?")
        region[r] = region.get(r, 0.0) + w
    style_box = _blend_style_box(pos)
    return {
        "gross": round(total, 4),
        "by_region": {_REGION_NAME.get(k, k): round(v / total, 4) for k, v in region.items()},
        "by_style": _by_style(style_box),
        "style_box": style_box,
    }


def _bench_exposure(label: str) -> dict:
    """Region split + blended style box for a buy-and-hold benchmark."""
    region = BENCH_REGION.get(label, {})
    style_box = _blend_style_box({label: 1.0})
    return {
        "gross": 1.0,
        "by_region": {_REGION_NAME.get(k, k): round(v, 4) for k, v in region.items()},
        "by_style": _by_style(style_box),
        "style_box": style_box,
    }


def _benchmarks_state(entries: list[dict], eq: list[float], idx: list[int],
                      bars_per_year: float, tax: Optional[TaxSettings] = None) -> list[dict]:
    """Per-benchmark equity curve, total/excess return, and risk stats — plus an
    after-tax total return (dividend drag only, buy-and-hold) when a tax profile is given."""
    labels = list((entries[-1].get("bench_equity") or {}).keys())
    out = []
    for label in labels:
        beq = [(e.get("bench_equity") or {}).get(label, 1.0) or 1.0 for e in entries]
        brets = [(beq[i] / beq[i - 1] - 1.0) if beq[i - 1] else 0.0
                 for i in range(1, len(beq))]
        b = {
            "label": label,
            "color": _BENCH_COLORS.get(label, "#9aa0c0"),
            "total_return": round(beq[-1] - 1.0, 6),
            "excess": round((eq[-1] - 1.0) - (beq[-1] - 1.0), 6),
            "sharpe": round(analytics.sharpe(brets, bars_per_year), 2),
            "max_drawdown": round(analytics.max_drawdown(beq), 4),
            "equity": [round(beq[i], 5) for i in idx],
            "exposure": _bench_exposure(label),
        }
        if tax is not None and tax.enabled:
            b["after_tax_return"] = round(_bench_after_tax(brets, tax.rate_lt, bars_per_year), 6)
        out.append(b)
    return out


def _attribution(rets: list[float], brets: list[float], bpy: float) -> Optional[dict]:
    """Decompose the model's return vs a passive benchmark (rf=0 OLS): market beta, annualized
    alpha (the part NOT explained by beta — the strategy's selection/structure edge), R², and the
    information ratio of the active return. Aligns the two series on their last min(len) points."""
    n = min(len(rets), len(brets))
    if n < 8:
        return None
    s, b = rets[-n:], brets[-n:]
    mb, ms = sum(b) / n, sum(s) / n
    var_b = sum((x - mb) ** 2 for x in b) / n
    var_s = sum((x - ms) ** 2 for x in s) / n
    if var_b <= 0:
        return None
    cov = sum((s[i] - ms) * (b[i] - mb) for i in range(n)) / n
    beta = cov / var_b
    alpha = ms - beta * mb                                  # per-bar alpha
    active = [s[i] - b[i] for i in range(n)]
    ma = sum(active) / n
    sd = (sum((x - ma) ** 2 for x in active) / n) ** 0.5
    # Statistical significance of alpha (OLS, rf=0): residual standard error -> t-stat.
    # se(alpha) = s_resid * sqrt(1/n + mean_b^2 / Sxx), with Sxx = sum((b-mb)^2) = n*var_b.
    # A short backtest rarely clears |t|>=1.96, which is exactly what an honest panel needs to see.
    resid = [s[i] - (alpha + beta * b[i]) for i in range(n)]
    dof = n - 2
    alpha_t: Optional[float] = None
    if dof > 0:
        s2 = sum(e * e for e in resid) / dof
        se_alpha = (s2 * (1.0 / n + (mb * mb) / (n * var_b))) ** 0.5
        if se_alpha > 0:
            alpha_t = alpha / se_alpha
    return {
        "benchmark": None,                                 # filled by the caller
        "beta": round(beta, 3),
        "alpha_annual": round(alpha * bpy, 4),             # additive annualized alpha
        "alpha_t": (round(alpha_t, 2) if alpha_t is not None else None),
        "alpha_significant": (bool(abs(alpha_t) >= 1.96) if alpha_t is not None else None),
        "n_obs": n,                                        # sample size behind the estimate
        "r2": round((cov * cov) / (var_b * var_s), 3) if var_s > 0 else 0.0,
        "info_ratio": round((ma / sd) * (bpy ** 0.5), 2) if sd > 0 else 0.0,
        "excess_annual": round((ms - mb) * bpy, 4),
    }


def _turnover_per_session(entries: list[dict]) -> list[float]:
    """Two-sided turnover (sum |Δweight|) booked at each session vs the prior book."""
    prev: dict[str, float] = {}
    out: list[float] = []
    for e in entries:
        w = e.get("weights", {})
        out.append(sum(abs(w.get(k, 0.0) - prev.get(k, 0.0)) for k in set(w) | set(prev)))
        prev = w
    return out


def _after_tax(entries: list[dict], tax: TaxSettings, bars_per_year: float):
    """Illustrative after-tax equity curve (unit-level, tax-managed simulation).

    Not lot accounting: the book is modeled as a single position with a running cost
    basis. Each rebalance realizes a share of the book's accumulated gain proportional
    to its sell-side turnover and pays tax on it from the portfolio (long-term rate if
    the turnover-implied average holding period clears `lt_holding_bars`, else short).
    Conservative — gains are taxed; it does not assume speculative loss-harvest credits
    (the TLH substitute map quantifies that upside separately). Distributions/dividends
    are inside the total-return marks and not taxed separately here.
    """
    turns = _turnover_per_session(entries)
    n = len(entries)
    one_sided = sum(turns) / 2.0
    years = (n / bars_per_year) if bars_per_year else 0.0
    ann_turnover = (one_sided / years) if years > 0 else 0.0
    avg_hold = (bars_per_year / ann_turnover) if ann_turnover > 0 else float("inf")
    rate = tax.rate_lt if avg_hold >= tax.lt_holding_bars else tax.rate_st
    value = basis = 1.0
    tax_paid = 0.0
    curve: list[float] = []
    for e, t in zip(entries, turns):
        value *= (1.0 + e.get("realized_return", 0.0))
        sell = t / 2.0
        if sell > 0 and value > basis:                 # realize gain on the sold slice
            realized = (value - basis) * sell
            paid = realized * rate
            value -= paid
            tax_paid += paid
            basis += realized                           # rebought slice steps up basis
        curve.append(round(value, 6))
    return curve, tax_paid, ann_turnover, avg_hold, rate


def build_ledger_state(ledger: dict, bars_per_year: float = 252.0,
                       tax: Optional[TaxSettings] = None) -> dict:
    """Shape the ledger into the dashboard/exhibit state."""
    entries = ledger.get("entries", [])
    if not entries:
        return {"header": {"days": 0, "inception": "", "total_return": 0.0,
                           "universe": ledger.get("universe", [])},
                "equity": [], "benchmarks": [], "dates": [], "positions": [],
                "recent": [], "exposure": None}
    eq = [e["equity"] for e in entries]
    rets = [e["realized_return"] for e in entries]
    n = len(eq)
    # Embed the full per-session series (small) so the page can re-slice by date
    # period and recompute window stats exactly; downsample only if very long.
    idx = list(range(n)) if n <= 900 else list(range(0, n, max(1, n // 800)))
    last = entries[-1]
    positions = sorted(
        ({"instrument": i, "portfolio_weight": w,
          "leg": "LONG" if w > 0 else "SHORT" if w < 0 else "—"}
         for i, w in last["weights"].items() if abs(w) > 1e-9),   # only active, non-zero allocations
        key=lambda r: -r["portfolio_weight"])
    live = sum(1 for e in entries if not e.get("seed"))
    cost_side = ledger.get("cost_bps_per_side")
    tax = tax or TaxSettings()
    # Lot-aware after-tax needs per-name prices on the entries (current ledgers have them;
    # a pre-`prices` ledger simply shows no after-tax until its next re-seed).
    at = after_tax_track(entries, tax, bars_per_year) if tax.enabled else None
    tax_block = None
    if at is not None:
        tax_block = {
            "state": tax.state, "rate_lt": at.rate_lt, "rate_st": at.rate_st,
            "after_tax_return": at.after_tax_return, "tax_drag": at.tax_drag,
            "tax_paid": at.tax_paid, "annual_turnover": at.annual_turnover,
            "avg_holding_days": at.avg_holding_days, "short_term_share": at.short_term_share,
            "st_realized": at.st_realized, "lt_realized": at.lt_realized,
            "harvested_losses": at.harvested_losses, "embedded_gain": at.embedded_gain,
            "liquidation_tax": at.liquidation_tax, "after_tax_liquidated": at.after_tax_liquidated,
        }
    # Return attribution vs the primary passive benchmark (VT if present): beta / alpha / R² / IR.
    _bl = list((entries[-1].get("bench_equity") or {}).keys())
    _prim = "VT" if "VT" in _bl else (_bl[0] if _bl else None)
    attribution = None
    attribution_oos = None
    if _prim:
        _beq = [(e.get("bench_equity") or {}).get(_prim, 1.0) or 1.0 for e in entries]
        _brets = [(_beq[i] / _beq[i - 1] - 1.0) if _beq[i - 1] else 0.0 for i in range(1, len(_beq))]
        attribution = _attribution(rets[1:], _brets, bars_per_year)
        if attribution:
            attribution["benchmark"] = _prim
        # Out-of-sample only: the live (non-seeded) tail, where the model ran forward with no
        # hindsight. rets[j] aligns with _brets[j-1]; _attribution itself enforces the n>=8 floor,
        # so a short live window simply yields None (an honest "not yet attributable").
        j = n - live
        if 0 < j < n:
            attribution_oos = _attribution(rets[j:], _brets[j - 1:], bars_per_year)
            if attribution_oos:
                attribution_oos["benchmark"] = _prim
    return {
        "header": {
            "days": n,
            "live_days": live,
            "seeded_days": n - live,
            "inception": ledger.get("inception", entries[0]["date"]),
            "updated": ledger.get("updated", ""),
            "total_return": round(eq[-1] - 1.0, 6),
            "sharpe": round(analytics.sharpe(rets, bars_per_year), 2),
            "max_drawdown": round(analytics.max_drawdown(eq), 4),
            "hit_rate": round(analytics.hit_rate(rets), 3),
            "bars_per_year": bars_per_year,
            "cost_bps_per_side": cost_side,
            "cost_bps_roundtrip": (round(cost_side * 2, 1) if cost_side is not None else None),
            "rebalance_bars": ledger.get("rebalance_bars"),
            "universe": ledger.get("universe", []),
            "n_long": last["n_long"],
            "n_short": last["n_short"],
            # Lot-aware after-tax summary (see drift.tax / config.TaxSettings); None if disabled.
            "annual_turnover": (at.annual_turnover if at else None),
            "after_tax_total_return": (at.after_tax_return if at else None),
            "tax_drag": (at.tax_drag if at else None),
            "avg_holding_days": (at.avg_holding_days if at else None),
            "short_term_share": (at.short_term_share if at else None),
            "tax_state": (tax.state if at else None),
        },
        "tax": tax_block,
        "after_tax": ([round(at.curve[i], 5) for i in idx] if at else None),
        "equity": [round(eq[i], 5) for i in idx],
        "benchmarks": _benchmarks_state(entries, eq, idx, bars_per_year, tax),
        "dates": [entries[i]["date"] for i in idx],
        "attribution": attribution,
        "attribution_oos": attribution_oos,
        "split_frac": ((n - live) / n) if n else 0.0,
        "split_idx": next((k for k, i in enumerate(idx) if i >= (n - live)), len(idx)),
        "positions": positions,
        "exposure": _exposure(last["weights"]),
        "recent": [{"date": e["date"], "realized_return": e["realized_return"],
                    "equity": e["equity"]} for e in entries[-20:]][::-1],
    }
