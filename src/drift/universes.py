"""Curated, liquid, Yahoo-available instrument universes.

Single source of truth for what the exhibits trade. The equities side deliberately
spans BOTH regions (US / developed-international / emerging) and factors (value,
growth, small, small-value, momentum, quality, min-vol), including regional×factor
sleeves (e.g. international small-cap value). Region and factor leadership rotates
over time, so this dispersion is exactly what the cross-sectional (relative-
strength) engine and the daily-marked book are built to harvest.

History/inception varies (newer factor ETFs start later); the date-aligned books
handle ragged histories — a name simply joins once it has enough bars.
"""

from __future__ import annotations

# US — region core + factor tilts.
US = ["SPY", "IWM", "VTV", "VUG", "VBR", "MTUM", "QUAL", "USMV"]
# Developed international — core + factor tilts (incl. small-cap value via DLS).
DEV_INTL = ["EFA", "EFV", "EFG", "SCZ", "DLS", "IMTM"]
# Emerging markets — core + small-cap value (DGS).
EM = ["EEM", "DGS"]
# Cross-asset diversifiers that lead at different times (long bonds, gold).
DIVERSIFIERS = ["TLT", "GLD"]

# Region × factor equity book (the default equities universe for the exhibits).
EQUITIES = US + DEV_INTL + EM + DIVERSIFIERS

# Crypto majors (Coinbase for the live dashboard; Yahoo for long history).
CRYPTO = ["BTC-USD", "ETH-USD", "LTC-USD", "BCH-USD"]

# Labeled groups, for display / documentation.
GROUPS = {
    "US (region + factors)": US,
    "Developed international (region + factors)": DEV_INTL,
    "Emerging markets": EM,
    "Cross-asset diversifiers": DIVERSIFIERS,
}

# What each ticker is, so exhibits can annotate the cross-section.
LABELS = {
    "SPY": "US large", "IWM": "US small", "VTV": "US large value",
    "VUG": "US large growth", "VBR": "US small value", "MTUM": "US momentum",
    "QUAL": "US quality", "USMV": "US min-vol",
    "EFA": "Intl developed", "EFV": "Intl value", "EFG": "Intl growth",
    "SCZ": "Intl small", "DLS": "Intl small value", "IMTM": "Intl momentum",
    "EEM": "Emerging mkts", "DGS": "EM small value",
    "TLT": "Long Treasuries", "GLD": "Gold",
    "BTC-USD": "Bitcoin", "ETH-USD": "Ethereum", "LTC-USD": "Litecoin", "BCH-USD": "Bitcoin Cash",
}


def csv(symbols) -> str:
    return ",".join(symbols)


# --- Group maps for neutralized cross-sections ------------------------------ #
# Region/asset bucket per ticker (US / developed-intl / emerging / diversifier).
REGION_OF = {
    **{t: "US" for t in US}, **{t: "DEV" for t in DEV_INTL},
    **{t: "EM" for t in EM}, **{t: "DIV" for t in DIVERSIFIERS},
}
# Style/factor bucket per ticker (core = broad market, no tilt).
FACTOR_OF = {
    "SPY": "core", "IWM": "size", "VTV": "value", "VUG": "growth", "VBR": "smallvalue",
    "MTUM": "momentum", "QUAL": "quality", "USMV": "minvol",
    "EFA": "core", "EFV": "value", "EFG": "growth", "SCZ": "size",
    "DLS": "smallvalue", "IMTM": "momentum",
    "EEM": "core", "DGS": "smallvalue", "TLT": "bond", "GLD": "gold",
}


def group_map(dim: str) -> dict[str, str]:
    """Ticker -> group for a neutralization dimension ('region' or 'factor')."""
    return dict(REGION_OF if dim == "region" else FACTOR_OF)

