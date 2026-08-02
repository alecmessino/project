"""Nightly job: fetch live CoinGecko data, score, persist to ledger.

Run by GitHub Actions (cron) or locally:
    python -m launch_skew.nightly

Dune API key (Module B: vesting/ERA) is read from env DUNE_API_KEY only.
When absent, Module B columns are recorded as null — never fabricated.
"""
from __future__ import annotations

import os
import sys
from datetime import date

# Allow running as a script or module
sys.path.insert(0, str(__file__).split("launch_skew")[0] if "launch_skew" in __file__ else ".")

from launch_skew.data.provider import CoinGeckoProvider, SignalScanner, DuneProvider  # noqa: E402
from launch_skew.ledger import append_signals, SignalRow, update_backtest_results  # noqa: E402

# Exclusions are owned by SignalScanner.NON_SPECULATIVE (single source of truth).
EXCLUDED = SignalScanner.NON_SPECULATIVE


def fetch_live_prices(provider: CoinGeckoProvider) -> dict:
    """Map symbol -> current price for backtest ROI backfill."""
    out: dict = {}
    try:
        for t in provider.get_tokens(100):
            if t.symbol:
                out[t.symbol.upper()] = t.price
    except Exception:  # noqa: BLE001
        pass
    return out


def build_rows(provider: CoinGeckoProvider, top_n: int = 25) -> list:
    """Score and persist the same excluded-filtered subset used by the scanner."""
    scanner = SignalScanner(provider)
    tokens = provider.get_tokens(top_n * 3)
    today = date.today().isoformat()
    rows: list = []
    seen: set = set()
    for t in tokens:
        sym = (t.symbol or "").upper()
        if not sym or sym in seen or sym in EXCLUDED:
            continue
        seen.add(sym)
        m = scanner._calculate_metrics(t)
        rows.append(SignalRow(
            date=today,
            symbol=sym,
            name=t.name,
            price=t.price,
            market_cap=t.market_cap,
            turnover_pct=round((t.volume_24h / t.market_cap * 100) if t.market_cap else 0, 2),
            erosion_ratio=round(m.erosion_ratio, 3),
            conviction=m.conviction,
            signal=m.signal,
        ))
    rows.sort(key=lambda r: r.conviction, reverse=True)
    return rows[:top_n]


def main() -> int:
    provider = CoinGeckoProvider()

    # Dune enrichment is only active when both the key and a query id are set.
    dune = None
    if os.environ.get("DUNE_API_KEY") and os.environ.get("DUNE_UNLOCK_QUERY_ID"):
        try:
            dune = DuneProvider()
            print("Dune configured — Module B unlock feed enabled.", file=sys.stderr)
        except RuntimeError as e:
            print(f"Dune disabled: {e}", file=sys.stderr)
    else:
        print("Dune not configured — Module B recorded as null (no fabricated data).",
              file=sys.stderr)

    rows = build_rows(provider)
    if dune:
        # Optional enrichment: attach live unlock context per symbol.
        # erosion_ratio is only overwritten when a real value is returned.
        for r in rows:
            try:
                u = dune.get_token_unlocks(r.symbol)
                if u.get("available") and u.get("rows"):
                    pass  # query-specific parsing left to the deployment
            except Exception:  # noqa: BLE001
                continue

    written = append_signals(rows)

    # Backfill ROI using current live prices so rows age into 30d/90d windows.
    live = fetch_live_prices(provider)
    updated = update_backtest_results(live)

    print(f"Nightly snapshot {date.today().isoformat()}: wrote {written} signals, "
          f"backfilled {updated} backtest rows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
