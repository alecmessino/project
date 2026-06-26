"""Information-Discreteness (Frog-in-the-Pan) validation sweep — INTERNAL R&D.

Tests whether the FIP effect (Da, Gurun & Warachka 2014) — continuous-information winners
keep trending, discrete-information winners do not — shows up in Driftwood's actual
cross-sectional ETF book. At each rebalance we rank the universe by the live momentum
score, take the long half, split it by information discreteness (drift.signal.
information_discreteness) at the median, and compare the two buckets' forward returns.

    python scripts/id_sweep.py              # synthetic universe (mechanism check only)
    ID_SWEEP_REAL=1 python scripts/id_sweep.py   # real 40y proxy-spliced MATRIX (the real test)

IMPORTANT — this is a research artifact, not a result to ship. FIP is documented on
individual stocks; an 18-ETF book averages away the idiosyncratic information paths the
effect rides on, and 18 names is thin for a median split. The synthetic run only proves the
harness discriminates continuous from discrete; it is NOT evidence the edge exists. Nothing
here is wired into the live signal — promote it to "The Institutional Edge" ONLY if the real
run shows a robust, persistent continuous-minus-discrete spread.
"""

from __future__ import annotations

import os
import random
import statistics as st
import sys

from drift.config import Settings
from drift.signal import information_discreteness, momentum_score
from drift.universes import MATRIX

BPY = 252.0
YEARS = 40
N_BARS = YEARS * int(BPY)


def synthetic_universe() -> dict[str, list[float]]:
    """Half continuous-drift names, half discrete-jump names (same average drift), so the
    harness has something to discriminate. Deterministic. A mechanism check, NOT real history."""
    rng = random.Random(17)
    tickers = list(MATRIX)
    series: dict[str, list[float]] = {}
    for t, tkr in enumerate(tickers):
        discrete = (t % 2 == 1)
        px, closes = 100.0, []
        for k in range(N_BARS):
            if discrete:
                # mostly tiny noise, with rare large jumps -> high information discreteness
                step = rng.gauss(0.0002, 0.004) + (rng.gauss(0.06, 0.02) if rng.random() < 0.01 else 0.0)
            else:
                # steady small positive drift + small noise -> continuous
                step = rng.gauss(0.0007, 0.006)
            px *= (1.0 + step)
            closes.append(px)
        series[tkr] = closes
    return series


def real_universe() -> dict[str, list[float]]:
    """Best-effort 40-year proxy-spliced close series from the Yahoo feed (the real test)."""
    from drift.tearsheet import _pull
    series, applied = _pull(list(MATRIX), years=float(YEARS), proxies=True)
    if applied:
        print(f"  (proxy-spliced: {', '.join(f'{k}<-{v}' for k, v in applied.items())})")
    return {k: [b.close for b in bars] for k, bars in series.items()}


def fip_test(series: dict[str, list[float]], settings: Settings) -> dict:
    """Walk-forward: rank by momentum, take the long half, bucket by ID at the median, and
    collect each bucket's forward return to the next rebalance."""
    sg, cs = settings.signal, settings.cross_section
    L, vw, H = sg.lookback, sg.vol_window, max(1, cs.rebalance_bars)
    insts = sorted(series)
    n = min(len(series[i]) for i in insts)
    closes = {i: series[i][-n:] for i in insts}            # align on a common tail length
    cont, disc, base = [], [], []
    t = L + 1
    while t + H < n:
        scores = {i: momentum_score(closes[i][:t], L, vw) for i in insts}
        ids = {i: information_discreteness(closes[i][:t], L) for i in insts}
        ranked = sorted(insts, key=lambda i: scores[i], reverse=True)
        longs = [i for i in ranked[: max(1, len(ranked) // 2)] if scores[i] > 0]
        if len(longs) < 2:
            t += H
            continue
        fwd = {i: closes[i][t + H] / closes[i][t] - 1.0 for i in longs}
        med = st.median(ids[i] for i in longs)
        for i in longs:
            base.append(fwd[i])
            (cont if ids[i] <= med else disc).append(fwd[i])   # low ID = continuous
        t += H

    def stat(xs: list[float]) -> dict:
        if not xs:
            return {"mean": 0.0, "ir": 0.0, "n": 0}
        m = st.fmean(xs)
        s = st.pstdev(xs) if len(xs) > 1 else 0.0
        return {"mean": m, "ir": (m / s if s else 0.0), "n": len(xs)}

    return {"continuous": stat(cont), "discrete": stat(disc), "all_longs": stat(base), "H": H}


def main() -> int:
    use_real = os.environ.get("ID_SWEEP_REAL") == "1"
    src = "real (Yahoo, proxy-spliced)"
    series = None
    if use_real:
        try:
            print("Pulling real 40-year history …")
            series = real_universe()
            if not series or len(series) < 8:
                print(f"  only {len(series or {})} names — falling back to synthetic")
                series = None
        except Exception as e:  # noqa: BLE001 — network is best-effort
            print(f"  real pull failed ({e!r}) — falling back to synthetic")
            series = None
    if series is None:
        series = synthetic_universe()
        src = "synthetic (deterministic — mechanism check, NOT evidence)"

    settings = Settings.load("config/drift.yaml")
    yrs = max(len(v) for v in series.values()) / BPY
    print(f"\nUniverse: {len(series)} ETFs · ~{yrs:.0f}y · source = {src}")
    print(f"Signal: lookback {settings.signal.lookback}, vol {settings.signal.vol_window}, "
          f"rebalance {settings.cross_section.rebalance_bars} bars\n")

    res = fip_test(series, settings)
    c, d, a = res["continuous"], res["discrete"], res["all_longs"]
    hdr = f"{'long bucket':<26}{'mean fwd ret':>14}{'info ratio':>12}{'obs':>7}"
    print(hdr); print("-" * len(hdr))
    for name, s in (("Continuous (low ID)", c), ("Discrete (high ID)", d), ("All longs (baseline)", a)):
        print(f"{name:<26}{s['mean']*100:>13.3f}%{s['ir']:>12.3f}{s['n']:>7}")
    spread = (c["mean"] - d["mean"]) * 100
    print(f"\nContinuous − Discrete forward-return spread: {spread:+.3f}% per {res['H']}-bar hold "
          f"(FIP predicts this is positive).")
    if not use_real:
        print("\nSYNTHETIC RUN — proves the harness discriminates; NOT evidence the edge exists on real ETFs.")
    print("Research only — not wired into the live signal. Do not present to clients until the real run "
          "shows a robust, persistent spread across sub-periods.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
