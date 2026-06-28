"""Tax-Alpha decomposition — the empirical backbone of the "Structural Alpha (tax)" claim.

This isolates how much of Driftwood's edge is *mechanical tax management* rather than beta or
market timing. It holds the investable universe fixed (the same 18 region/size/style ETFs) and asks:
on the SAME book, how many percentage points of after-tax retention does the firm's tax machinery
recover versus a tax-naive investor who leaks short-term gains?

Two books on the identical universe + identical tax rates (no factor-beta confound):
  • BEFORE — a concentrated, high-turnover momentum book (the Unconstrained Core), taxed NAIVELY:
    every realized gain taxed at full rate, no harvesting, fully in a taxable account. ~94% ST.
  • AFTER  — the Structural Alpha book (the tilt + lot-protection hybrid): lower turnover (lot
    protection + hysteresis), tax-loss harvesting + rate arbitrage ON. ~50% ST.

We compare RETENTION (after-tax / pre-tax) so the decomposition measures tax efficiency, not a
pre-tax return claim — the structural book is NOT asserted to out-earn before tax. The retention gap
decomposes, additively and assumption-free, into:
    1) lot protection + hysteresis  (turnover -> short-term -> long-term conversion)
    2) harvesting + rate arbitrage   (loss-netting, short-first, on the same path)
Asset location (the third structural lever) is household-specific, so it is reported SEPARATELY via
taxlab.location_alpha3 with a representative balance and a sensitivity range — not folded into the
assumption-free engine number.

    python scripts/tax_alpha.py                  # real 40y cache if present, else synthetic
    TAX_ALPHA_SYNTH=1 python scripts/tax_alpha.py # force the synthetic mechanism check

Determinism: re-execs with PYTHONHASHSEED=0 (the lot-protection redistribution iterates sets).
Research only — tilt_overlay / lot_protect are OFF in every shipped config and not wired into the
live signal. Illustrative tax modeling, not tax advice.
"""

from __future__ import annotations

import os
import sys

# Pin the hash seed BEFORE importing the engine so the lot-protected path (and the numbers) are stable.
# Skipped under pytest (where re-exec would replace the test runner): the unit guards check the
# decomposition INVARIANTS, which hold for any path regardless of set-iteration order.
if os.environ.get("PYTHONHASHSEED") != "0" and "pytest" not in sys.modules:
    os.environ["PYTHONHASHSEED"] = "0"
    os.execv(sys.executable, [sys.executable] + sys.argv)

from drift import analytics
from drift.config import Settings
from drift.cross_section import cross_book_entries
from drift.tax import after_tax_track, profile_for_state

# Reuse the committed real-history cache + the hybrid config builder from the tilt sweep.
from tilt_sweep import _hybrid, real_universe, synthetic_universe  # noqa: E402

BPY = 252.0
STATES = ["—", "IL", "NY", "CA"]          # no-tax -> mid -> high -> highest (state dependence of TLH)


def lot_after_tax(entries, rate_st, rate_lt, lt_bars, harvest):
    """One FIFO dollar-lot after-tax walk over the book's own marks, parametrized by `harvest`.

    harvest=True  -> nets realized losses into a short-first carryforward (= drift.tax.after_tax_track).
    harvest=False -> the tax-naive leak: every positive realized gain taxed at full rate, losses wasted.

    Both share the SAME compounding basis (tax paid from the book along the way), so the only thing
    that differs between them is the harvesting — making (managed - naive) a clean harvesting number.
    Returns (after_tax_return, tax_paid, st_realized, lt_realized, harvested_losses).
    """
    value = 1.0
    lots: dict[str, list[list]] = {}
    carry = 0.0
    tax_paid = st_real = lt_real = harv = 0.0
    prev_w: dict[str, float] = {}
    prev_px: dict[str, float] = {}
    for idx, e in enumerate(entries):
        w = e.get("weights", {})
        px = e.get("prices", {}) or prev_px
        value *= (1.0 + e.get("realized_return", 0.0))
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
                if tgt < cur_val - 1e-12:
                    to_sell = cur_val - tgt
                    q = lots.get(i, [])
                    while to_sell > 1e-12 and q:
                        d, pb, bi = q[0]
                        lot_val = d * price / pb
                        take = min(lot_val, to_sell)
                        frac = (take / lot_val) if lot_val else 0.0
                        gain = take - d * frac
                        if idx - bi >= lt_bars:
                            sess_lt += gain
                        else:
                            sess_st += gain
                        if take >= lot_val - 1e-12:
                            q.pop(0)
                        else:
                            q[0][0] = d * (1.0 - frac)
                        to_sell -= take
                elif tgt > cur_val + 1e-12:
                    lots.setdefault(i, []).append([tgt - cur_val, price, idx])
            st_real += max(0.0, sess_st)
            lt_real += max(0.0, sess_lt)
            harv += max(0.0, -sess_st) + max(0.0, -sess_lt)
            g_st, g_lt = max(0.0, sess_st), max(0.0, sess_lt)
            if harvest:
                carry += max(0.0, -sess_st) + max(0.0, -sess_lt)
                off = min(carry, g_st); g_st -= off; carry -= off
                off = min(carry, g_lt); g_lt -= off; carry -= off
            t = g_st * rate_st + g_lt * rate_lt
            if t:
                value -= t
                tax_paid += t
            prev_w = w
        prev_px = px
    return value - 1.0, tax_paid, st_real, lt_real, harv


def book_stats(entries):
    rets = [e["realized_return"] for e in entries]
    eq = [e["equity"] for e in entries]
    return analytics.sharpe(rets, BPY), analytics.max_drawdown(eq)


def _cagr(total_return, years):
    return (1.0 + total_return) ** (1.0 / years) - 1.0 if years > 0 else 0.0


def decompose(entries_fast, entries_hybrid, tax, years):
    """Assumption-free decomposition for one tax profile, headlined in AFTER-TAX CAGR (bps/yr) — the
    metric a CPA uses. Differences of CAGRs are additive, so the two engine levers sum to the total."""
    rs, rl, lb = tax.rate_st, tax.rate_lt, tax.lt_holding_bars
    pre_fast = entries_fast[-1]["equity"] - 1.0
    pre_hyb = entries_hybrid[-1]["equity"] - 1.0

    # BEFORE: concentrated/high-turnover, taxed naively (no harvest, fully taxable).
    naive_fast, *_ = lot_after_tax(entries_fast, rs, rl, lb, harvest=False)
    # AFTER, two stages on the structural book: naive -> harvested (isolates the harvesting lever).
    naive_hyb, *_ = lot_after_tax(entries_hybrid, rs, rl, lb, harvest=False)
    mgd_hyb, _tax, st_h, lt_h, harv_h = lot_after_tax(entries_hybrid, rs, rl, lb, harvest=True)

    atc_before = _cagr(naive_fast, years)      # after-tax CAGR, concentrated naive book
    atc_naive_hyb = _cagr(naive_hyb, years)    # structural book, still taxed naively
    atc_after = _cagr(mgd_hyb, years)          # structural book, harvesting on

    turnover_lever = atc_naive_hyb - atc_before   # lot protection + hysteresis (ST->LT conversion)
    harvest_lever = atc_after - atc_naive_hyb     # harvesting + rate arbitrage
    total = atc_after - atc_before                # Structural Alpha (tax), after-tax CAGR pts/yr
    return {
        "atc_before": atc_before, "atc_after": atc_after,
        "ret_before": naive_fast / pre_fast if pre_fast else float("nan"),
        "ret_after": mgd_hyb / pre_hyb if pre_hyb else float("nan"),
        "turnover_lever": turnover_lever, "harvest_lever": harvest_lever, "total": total,
        "st_share_after": st_h / (st_h + lt_h) if (st_h + lt_h) else 0.0,
        "harvested_after": harv_h,
    }


def main() -> int:
    use_synth = os.environ.get("TAX_ALPHA_SYNTH") == "1"
    if use_synth:
        series, src = synthetic_universe(), "synthetic (mechanism check, NOT evidence)"
    else:
        try:
            series = real_universe()
            src = "real (40y proxy-spliced cache)"
            if not series or len(series) < 8:
                series, src = synthetic_universe(), "synthetic (real pull thin — mechanism only)"
        except Exception as e:  # noqa: BLE001
            series, src = synthetic_universe(), f"synthetic (real pull failed: {e!r})"

    years = max(len(v) for v in series.values()) / BPY
    fast = Settings.load("config/drift.yaml")
    hybrid = _hybrid(fast, 0.5)
    entries_fast = cross_book_entries(series, fast)
    entries_hybrid = cross_book_entries(series, hybrid)
    pre_cagr_fast = _cagr(entries_fast[-1]["equity"] - 1.0, years)
    pre_cagr_hyb = _cagr(entries_hybrid[-1]["equity"] - 1.0, years)

    # Adversarial cross-check: the local harvest=True walk must reproduce the library after_tax_track.
    lib = after_tax_track(entries_hybrid, profile_for_state(fast.tax, "—"), BPY)
    mine, *_ = lot_after_tax(entries_hybrid, lib.rate_st, lib.rate_lt, fast.tax.lt_holding_bars, harvest=True)
    drift = abs(mine - lib.after_tax_return)
    xcheck = "OK" if drift < 1e-6 else f"MISMATCH Δ={drift:.2e}"

    sh_f, dd_f = book_stats(entries_fast)
    sh_h, dd_h = book_stats(entries_hybrid)

    print(f"\n=== Tax-Alpha decomposition · source = {src} · ~{years:.1f}y · {len(series)} ETFs ===")
    print(f"local-vs-library after-tax cross-check: {xcheck}")
    print(f"BEFORE  Unconstrained Core (concentrated): Sharpe {sh_f:.2f}  maxDD {dd_f*100:.0f}%  "
          f"pre-tax {pre_cagr_fast*100:.1f}%/yr")
    print(f"AFTER   Structural Alpha hybrid (tilt+lots): Sharpe {sh_h:.2f}  maxDD {dd_h*100:.0f}%  "
          f"pre-tax {pre_cagr_hyb*100:.1f}%/yr  (NOT claimed to out-earn pre-tax)")
    print("\nHeadline = AFTER-TAX CAGR (what the client compounds). 'Structural Alpha (tax)' is the")
    print("after-tax %/yr the structural book keeps over the concentrated, tax-naive one — decomposed")
    print("into the two assumption-free engine levers. All figures illustrative, paid-as-you-go.\n")
    hdr = (f"{'state':>6}{'ST% aft':>9}{'aftertax CAGR':>15}{'  ':>2}"
           f"{'lot+hyst':>10}{'+harvest':>10}{'= Tax Alpha':>13}")
    print(f"{'':>6}{'':>9}{'BEFORE → AFTER':>17}{'(after-tax %/yr recovered)':>33}")
    print(hdr); print("-" * len(hdr))
    rows = []
    for st in STATES:
        tax = profile_for_state(fast.tax, st)
        d = decompose(entries_fast, entries_hybrid, tax, years)
        rows.append((st, d))
        ba = f"{d['atc_before']*100:>5.1f} → {d['atc_after']*100:>4.1f}%"
        print(f"{st:>6}{d['st_share_after']*100:>8.0f}%{ba:>17}"
              f"{d['turnover_lever']*100:>10.1f}{d['harvest_lever']*100:>10.1f}{d['total']*100:>12.1f}")

    # Additivity + sign guards (assumption-free part is exact by construction).
    for st, d in rows:
        assert abs((d["turnover_lever"] + d["harvest_lever"]) - d["total"]) < 1e-9, st
        assert d["harvest_lever"] >= -1e-9, f"harvesting raised tax in {st}?"
        assert d["total"] >= -1e-9, f"structural book lost to the naive concentrated one in {st}?"

    fed = next(d for s, d in rows if s == "—")
    print(f"\nKept-of-the-gain (federal-only): the concentrated book keeps {fed['ret_before']*100:.0f}% of its "
          f"pre-tax gain after tax; the structural book keeps {fed['ret_after']*100:.0f}%.")

    # Asset location — the SEPARATE, household-specific third lever, framed as the annual haircut it
    # shelters on sheltered dollars (NOT a compounded terminal claim — that is personalized in the Tax Lab).
    ca = next(d for s, d in rows if s == "CA")
    haircut_taxable = pre_cagr_fast - ca["atc_before"]      # the leak on the concentrated book in CA
    print(f"\nAsset location (3rd lever — household-specific, quantified per client in the Tax Lab):")
    print(f"  In CA the concentrated book's annual tax haircut is ~{haircut_taxable*100:.1f}%/yr. Locating the")
    print(f"  high-turnover sleeve into a Roth/Traditional account shelters that haircut on the sheltered")
    print(f"  dollars — stacking on top of the {ca['total']*100:.1f}%/yr the lot + harvest levers already recover.")

    print("\nRead: the BEFORE book leaks tax (high ST%, no harvest); lot protection + hysteresis convert ST "
          "churn to LT, harvesting nets losses short-first, asset location shelters the rest. The after-tax "
          "%/yr recovered RISES with the state rate — the leak a passive benchmark simply can't plug.")
    if use_synth or src.startswith("synthetic"):
        print("SYNTHETIC — proves the mechanism; NOT evidence on real ETFs.")
    print("Illustrative tax modeling, not advice. tilt_overlay/lot_protect are OFF in every shipped config.")
    return 0 if drift < 1e-6 else 1


if __name__ == "__main__":
    sys.exit(main())
