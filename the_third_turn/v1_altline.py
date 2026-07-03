#!/usr/bin/env python3
"""Vector 1 — alt-line skew exploitation.

The drop reversion averages +0.69 above the dropped line but is right-skewed
(win-big/lose-small), so a flat -110 Over bleeds. The pivot: buy the Over at HIGHER
alt hooks (plus money) to target the fat upper tail instead of the median.

The rigorous question isn't "does the Over win at hook L+k" (we have the real finals
for that) — it's "is that upper tail FATTER than the market's efficient distribution
implies." If finals are right-skewed, a symmetric price under-rates deep Overs, and
buying them at the market's fair price is +EV before you even get plus-money.

For each hook we show: empirical win%, the efficient-market implied win% (Normal
centered at the live line, empirical σ), the edge, and the EV of buying at the
no-vig fair price and at a realistic 4.5%-hold alt price. Populations: all games and
the drop-context set (line dropped by the 3rd), bet at the end-of-3rd live total.

    python the_third_turn/v1_altline.py
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402
from scipy.stats import norm  # noqa: E402

from features import CACHE, build  # noqa: E402
from investigate_line_edge import wilson_interval  # noqa: E402

console = Console()
HOOKS = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
VIG = 0.045   # typical alt-line hold


def american(dec):
    if dec >= 2:
        return f"+{round((dec-1)*100)}"
    return f"{round(-100/(dec-1))}"


def analyze(rows, title):
    resid = [r["final"] - r["L"] for r in rows]
    mu, sd = statistics.mean(resid), (statistics.pstdev(resid) or 1.0)
    skew = statistics.mean(((x - mu) / sd) ** 3 for x in resid)
    console.print(f"\n[bold]{title}[/]  n={len(rows)} · mean(final−line)={mu:+.2f} "
                  f"· σ={sd:.2f} · skew={skew:+.2f}")
    t = Table()
    for c in ("Over at", "win%", "95% CI", "mkt-fair%", "edge", "fair odds",
              "EV @fair", "EV @-4.5%"):
        t.add_column(c, justify="left" if c == "Over at" else "right")
    out = []
    for k in HOOKS:
        w = sum(1 for r in rows if r["final"] > r["L"] + k)
        n = len(rows)
        emp = w / n if n else 0.0
        lo, hi = wilson_interval(w, n) if n else (0, 0)
        implied = 1.0 - norm.cdf(k / sd)               # efficient market: mean at the line
        implied = min(max(implied, 1e-6), 0.999999)
        fair_dec = 1.0 / implied
        ev_fair = emp * fair_dec - 1.0                 # buy at no-vig fair price
        ev_vig = emp * (fair_dec * (1 - VIG)) - 1.0    # buy at a vig'd alt price
        edge = emp - implied
        col = "[green]" if ev_vig > 0 else "[red]"
        t.add_row(f"line+{k:.1f}", f"{100*emp:.0f}%", f"{100*lo:.0f}-{100*hi:.0f}",
                  f"{100*implied:.0f}%", f"{100*edge:+.0f}%", american(fair_dec),
                  f"{col}{100*ev_fair:+.0f}%[/]", f"{col}{100*ev_vig:+.0f}%[/]")
        out.append({"hook": k, "win": round(emp, 3), "implied": round(implied, 3),
                    "ev_fair": round(ev_fair, 3), "ev_vig": round(ev_vig, 3)})
    console.print(t)
    return {"n": len(rows), "mu": round(mu, 2), "sigma": round(sd, 2),
            "skew": round(skew, 2), "hooks": out}


def main() -> int:
    cache = build()
    recs = []
    for r in cache.values():
        L = r.get("line_by_inn", {}).get("3")
        if r.get("final") is None or L is None or not r.get("closing"):
            continue
        recs.append({"L": L, "final": r["final"], "closing": r["closing"]})
    drop = [r for r in recs if r["L"] < r["closing"]]

    console.rule("[bold]Vector 1 · alt-line skew — is the upper tail underpriced?")
    console.print("[dim]win% = real frequency final beats the hook · mkt-fair% = an efficient "
                  "market's implied prob (symmetric, centered at the line) · edge = win−fair · "
                  "EV = return buying at that price. green = +EV after 4.5% vig.[/]")
    a = analyze(recs, "ALL games")
    b = analyze(drop, "DROP context (line fell by the 3rd) — where the +0.69 lives")
    console.print("\n[dim]A positive skew with green EV cells in the upper hooks = the reversion's "
                  "fat tail is real alpha you can only capture at plus money. Flat/negative = the "
                  "market already prices the tail; the -110 loss was the whole story.[/]")
    (Path(CACHE).parent / "v1_altline.json").write_text(
        json.dumps({"all": a, "drop": b}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
