"""Curated, liquid, Yahoo-available instrument universes.

Single source of truth for what the exhibits trade. The equities side is a
**size × style × region matrix**: three regions (US / developed-international /
emerging) crossed with the size/style box (large / mid / small × value / blend /
growth). This dispersion is exactly what the cross-sectional engine and the
daily-marked book harvest, and it lets the book be neutralized along any one axis
(region, size, or style) to isolate the others.

Ticker selection rule: the longest-history liquid instrument per cell (verified on
Yahoo). A few cells have no liquid instrument and are intentionally omitted:
international small-cap growth, and both emerging-markets growth cells. EM large/mid
value uses FNDE (fundamentally-weighted, value-tilted) since cap-weighted EM value
ETFs are not reliably tradeable.

History varies (the pure-factor funds AVDV/AVEE are younger); the date-aligned books
handle ragged histories — a name simply joins once it has enough bars.
"""

from __future__ import annotations

# Each entry: ticker -> (region, size, style). Regions: US / DEV / EM.
# Sizes: large / mid / small (US split out), largemid (intl & EM combined cells).
MATRIX: dict[str, tuple[str, str, str]] = {
    # --- United States (full 3x3 size x style box) ---
    "IVE": ("US", "large", "value"),  "IVV": ("US", "large", "blend"),  "IVW": ("US", "large", "growth"),
    "IWS": ("US", "mid", "value"),    "IWR": ("US", "mid", "blend"),    "IWP": ("US", "mid", "growth"),
    "IWN": ("US", "small", "value"),  "IJR": ("US", "small", "blend"),  "IWO": ("US", "small", "growth"),
    # --- Developed international ex-US (small-growth omitted: no liquid instrument) ---
    "EFV": ("DEV", "largemid", "value"), "EFA": ("DEV", "largemid", "blend"), "EFG": ("DEV", "largemid", "growth"),
    "AVDV": ("DEV", "small", "value"),   "SCZ": ("DEV", "small", "blend"),
    # --- Emerging markets (both growth cells omitted: no liquid instrument) ---
    "FNDE": ("EM", "largemid", "value"), "VWO": ("EM", "largemid", "blend"),
    "AVEE": ("EM", "small", "value"),    "EWX": ("EM", "small", "blend"),
}

# The traded universe (the matrix cells).
EQUITIES = list(MATRIX)

REGION_OF = {t: v[0] for t, v in MATRIX.items()}
SIZE_OF = {t: v[1] for t, v in MATRIX.items()}
STYLE_OF = {t: v[2] for t, v in MATRIX.items()}

# Broad-market core-beta baselines (longest-history total-market references).
BASELINES = ["VTI", "VEA", "VWO"]

# Passive proxies for the young pure-factor funds, used ONLY to back-fill long
# history before the fund's inception (return-splice). The proxy tracks the cell's
# style closely, so the volatility-normalized z-score stays continuous across the
# join. Live exhibits (2y) use the real fund and never touch these.
PROXY = {
    "AVDV": "DLS",    # Intl small value  <- WisdomTree intl small-cap dividend (2006)
    "AVEE": "EEMS",   # EM small value    <- iShares EM small-cap (2011)
    "FNDE": "EEM",    # EM value          <- iShares EM core (2003)
    "VT": "VTI",      # Global market ref <- US total market before VT's 2008 inception
}

# Region groupings, for display / documentation.
GROUPS = {
    "United States": [t for t in EQUITIES if REGION_OF[t] == "US"],
    "Developed international": [t for t in EQUITIES if REGION_OF[t] == "DEV"],
    "Emerging markets": [t for t in EQUITIES if REGION_OF[t] == "EM"],
}

_REGION_NAME = {"US": "US", "DEV": "Intl", "EM": "EM"}
LABELS = {
    t: f"{_REGION_NAME[r]} {s if s != 'largemid' else 'large/mid'} {st}"
    for t, (r, s, st) in MATRIX.items()
}
LABELS.update({"VTI": "US total market", "VEA": "Intl developed core", "VWO": "EM core"})


# --- Underlying style-box composition -------------------------------------------
# Representative Morningstar-style size×style breakdown for each fund: the share of
# the fund's stock holdings that fall in each of the 9 boxes (large/mid/small ×
# value/blend/growth). Unlike SIZE_OF/STYLE_OF (one nominal cell per fund), these
# spread a fund across the box the way Morningstar actually classifies its holdings
# — e.g. IShares S&P 500 Value (IVE) is not purely "large value", it spills into
# large blend and mid. Blended by current book weight, these give the portfolio's
# true style-box footprint. Values are approximate (exposure shape, not precision)
# and are normalized in code, so they need only be proportional.
#
# Cell keys are "<size>|<style>" with size in {large, mid, small}.
def _sb(lv=0, lb=0, lg=0, mv=0, mb=0, mg=0, sv=0, sb=0, sg=0) -> dict[str, float]:
    return {"large|value": lv, "large|blend": lb, "large|growth": lg,
            "mid|value": mv, "mid|blend": mb, "mid|growth": mg,
            "small|value": sv, "small|blend": sb, "small|growth": sg}


STYLE_BOX: dict[str, dict[str, float]] = {
    # --- US ---
    "IVE": _sb(lv=33, lb=27, lg=4, mv=13, mb=17, mg=3, sv=1, sb=1, sg=1),   # S&P 500 Value
    "IVV": _sb(lv=24, lb=31, lg=33, mv=3, mb=5, mg=3, sb=1),                # S&P 500
    "IVW": _sb(lv=2, lb=15, lg=60, mb=7, mg=13, sb=1, sg=2),                # S&P 500 Growth
    "IWS": _sb(lv=4, lg=2, mv=42, mb=25, mg=3, sv=12, sb=6, sg=2, lb=4),    # Russell Midcap Value
    "IWR": _sb(lv=5, lb=5, lg=5, mv=18, mb=30, mg=22, sv=4, sb=4, sg=7),    # Russell Midcap
    "IWP": _sb(lb=3, lg=8, mv=2, mb=20, mg=50, sv=2, sb=5, sg=10),          # Russell Midcap Growth
    "IWN": _sb(lv=1, mv=15, mb=5, mg=1, sv=50, sb=25, sg=3),                # Russell 2000 Value
    "IJR": _sb(mv=3, mb=3, mg=1, sv=30, sb=38, sg=25),                      # S&P SmallCap 600
    "IWO": _sb(mv=1, mb=4, mg=12, sv=3, sb=25, sg=55),                      # Russell 2000 Growth
    # --- Developed international ---
    "EFV": _sb(lv=45, lb=15, lg=2, mv=25, mb=10, mg=2, sv=1),               # EAFE Value
    "EFA": _sb(lv=25, lb=35, lg=20, mv=7, mb=8, mg=3, sb=2),                # EAFE
    "EFG": _sb(lv=3, lb=18, lg=50, mb=8, mg=15, sb=2, sg=4),                # EAFE Growth
    "AVDV": _sb(mv=18, mb=7, sv=50, sb=20, sg=3, mg=2),                     # Intl small value
    "SCZ": _sb(mv=5, mb=5, mg=2, sv=30, sb=40, sg=18),                      # Intl small blend
    # --- Emerging markets ---
    "FNDE": _sb(lv=45, lb=15, lg=3, mv=22, mb=10, mg=3, sv=2),              # EM value (fundamental)
    "VWO": _sb(lv=22, lb=33, lg=22, mv=8, mb=8, mg=4, sb=2, sg=1),          # EM core
    "AVEE": _sb(mv=18, mb=8, sv=48, sb=22, sg=2, mg=2),                     # EM small value
    "EWX": _sb(mv=7, mb=6, mg=2, sv=30, sb=40, sg=15),                      # EM small blend
    # --- Buy-and-hold benchmarks (cap-weighted total markets) ---
    "VTI": _sb(lv=24, lb=25, lg=24, mv=7, mb=7, mg=6, sv=2, sb=3, sg=2),    # US total market
    "VT": _sb(lv=23, lb=25, lg=24, mv=7, mb=7, mg=6, sv=3, sb=3, sg=2),     # Global total market
}

# Region split for the buy-and-hold benchmarks (the strategy book uses REGION_OF,
# one region per fund). VT is the global market cap split; VTI is all-US.
BENCH_REGION: dict[str, dict[str, float]] = {
    "VT": {"US": 0.65, "DEV": 0.25, "EM": 0.10},
    "VTI": {"US": 1.0},
}


def csv(symbols) -> str:
    return ",".join(symbols)


def group_map(dim: str) -> dict[str, str]:
    """Ticker -> group for a neutralization dimension.

    'region' (US/DEV/EM), 'size' (large/mid/small/largemid), 'style' (value/
    blend/growth). 'factor' is accepted as an alias for 'style'.
    """
    if dim == "region":
        return dict(REGION_OF)
    if dim == "size":
        return dict(SIZE_OF)
    if dim in ("style", "factor"):
        return dict(STYLE_OF)
    return {}
