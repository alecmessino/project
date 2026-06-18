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
