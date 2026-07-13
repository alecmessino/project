"""Canonical per-jurisdiction tax facts — the single source of truth (PUBLISHING_SPEC §15.4).

Every surface projects from here: the after-tax calculator (``tax.STATE_RATES``), the Atlas
display (``statemap._income``), the state pages, the templates, and the JS. No rate or threshold
is authored anywhere else — that is the whole point of this module.

2026 edition (2025 tax-year law). RATES are TOP-OF-BRACKET *effective* capital-gains rates a
high-income resident ($1M+ of gains) actually pays — INCLUDING any millionaire / net-investment
surtax and reflecting any long-term exclusion — so the calculator and the Atlas headline agree by
construction. Each figure changed from the prior encoding is reconciled against a primary/official
source in RECONCILIATION_LOG.md (previous value → adopted value → authority → effective date);
the per-state citations for the 2025 reconciliation live in RATE_SOURCES below.
"""
from __future__ import annotations

# code -> (long_term, short_term) top-effective capital-gains rate, as a decimal.
# Most states tax gains as ordinary income (lt == st). The exceptions are encoded exactly:
# no-income-tax states (0); long-term EXCLUSION states (lt < st); millionaire/NIIT SURTAX states
# (the surtax is folded into the top-effective figure); Washington's long-term-only excise; and
# states that changed for 2025 (rate cuts, new exemptions, repealed exclusions).
RATES: dict[str, tuple[float, float]] = {
    "—": (0.0, 0.0),  # federal only / no state assumed
    # No income tax → no tax on capital gains.
    "AK": (0.0, 0.0), "FL": (0.0, 0.0), "NV": (0.0, 0.0), "NH": (0.0, 0.0),
    "SD": (0.0, 0.0), "TN": (0.0, 0.0), "TX": (0.0, 0.0), "WY": (0.0, 0.0),
    "WA": (0.099, 0.0),   # excise on LONG-TERM gains only: 7% + a 2.9% tier over ~$1M (SB 5813, 2025)
    # Ordinary-income states (lt == st unless a surtax/exclusion applies).
    "AL": (0.05, 0.05), "AZ": (0.0188, 0.025),   # AZ: 2.5% flat, 25% LT subtraction → 1.88% effective LT
    "CO": (0.044, 0.044), "GA": (0.0519, 0.0519),  # GA: HB 111 cut to 5.19% for TY2025
    "IA": (0.038, 0.038),   # IA: flat 3.8% from 2025
    "ID": (0.053, 0.053),   # ID: HB 40 cut to 5.3% for 2025
    "IL": (0.0495, 0.0495), "IN": (0.03, 0.03),   # IN: 3.0% flat for 2025
    "KS": (0.0558, 0.0558),   # KS: two-bracket top 5.58%
    "KY": (0.04, 0.04), "LA": (0.03, 0.03),   # LA: flat 3% from 2025, cap-gains deduction repealed
    "MA": (0.09, 0.125),   # MA: 5%/8.5% + 4% millionaire surtax → LT 9%, ST 12.5%
    "MD": (0.085, 0.065),   # MD: 6.5% top + 2% cap-gains surtax on LT (net cap gain) → LT 8.5%, ST 6.5%
    "MI": (0.0425, 0.0425), "MS": (0.044, 0.044),   # MS: flat 4.4% for 2025
    "NC": (0.0425, 0.0425),   # NC: flat 4.25% for 2025
    "PA": (0.0307, 0.0307), "UT": (0.045, 0.045),   # UT: HB 106 cut to 4.5% for 2025
    "AR": (0.0195, 0.039),   # AR ~50% LT exclusion
    "CA": (0.133, 0.133), "CT": (0.0699, 0.0699), "DE": (0.066, 0.066),
    "DC": (0.1075, 0.1075), "HI": (0.0725, 0.11),   # HI caps LT at 7.25%
    "ME": (0.0715, 0.0715), "MN": (0.1085, 0.1085),   # MN: 9.85% + 1% NIIT surtax → 10.85%
    "MO": (0.0, 0.0),   # MO: capital gains fully exempt from 2025 (HB 594)
    "MT": (0.041, 0.059),   # MT lower LT rate
    "NE": (0.052, 0.052),   # NE: LB 754 cut to 5.2% for 2025
    "NJ": (0.1075, 0.1075),
    "NM": (0.059, 0.059),   # NM: general 40% LT exclusion repealed for 2025 (HB 252)
    "NY": (0.109, 0.109), "ND": (0.015, 0.025),   # ND 40% LT exclusion
    "NYC": (0.1478, 0.1478),   # NY 10.9% + NYC ~3.88% local
    "OH": (0.03125, 0.03125),   # OH: top rate 3.125% for 2025 (flat 2.75% in 2026)
    "OK": (0.0475, 0.0475), "OR": (0.099, 0.099),
    "RI": (0.0599, 0.0599), "SC": (0.0336, 0.06),   # SC 44% LT deduction; 2025 top rate 6.0% → LT 3.36%, ST 6.0%
    "VT": (0.0875, 0.0875),   # VT: 40% LT exclusion is unavailable for listed securities → full 8.75%
    "VA": (0.0575, 0.0575),
    "WV": (0.0482, 0.0482),   # WV: triggered cut to 4.82% for 2025
    "WI": (0.0536, 0.0765),   # WI 30% LT exclusion
    # Territories (own/mirror codes; the rate is the total tax replacing federal).
    "AS": (0.20, 0.20), "GU": (0.20, 0.20), "MP": (0.20, 0.20), "PR": (0.15, 0.15), "VI": (0.20, 0.20),
}


# The five U.S. territories carry rates for the Atlas display but are out of scope for the after-tax
# calculator (no modeled client resides in one). Canonical here so statemap and tax share one set.
TERRITORY_CODES = frozenset({"AS", "GU", "MP", "PR", "VI"})


def rate_display(code: str) -> str:
    """The Atlas headline: the top-effective LONG-TERM rate, formatted (e.g. 0.0519 -> '5.19%')."""
    lt = RATES.get(code, (0.0, 0.0))[0]
    return f"{lt * 100:g}%"


# Per-state reconciliation record for every value changed in the 2025 reconciliation: the previous
# in-repo encodings, the adopted top-effective (lt, st), and the primary/official authority. Drives
# RECONCILIATION_LOG.md and is asserted by tests/test_drift_atlas.py so a citation can't be dropped.
RATE_SOURCES: dict[str, dict] = {
    "AZ": {"prev_tax": "2.50/2.50", "prev_map": "1.88%", "adopted": "1.88/2.50",
           "authority": "A.R.S. §43-1022 (25% LT subtraction) + AZDOR 2.5% flat",
           "url": "https://www.azleg.gov/ars/43/01022.htm", "effective": "TY2025"},
    "GA": {"prev_tax": "5.39/5.39", "prev_map": "5.19%", "adopted": "5.19/5.19",
           "authority": "GA HB 111 (2025), retroactive to Jan 1 2025",
           "url": "https://taxnews.ey.com/news/2025-0930-georgia-law-lowers-personal-income-tax-retroactive-to-january-1-2025-allows-for-future-tax-cuts", "effective": "Jan 1 2025"},
    "IA": {"prev_tax": "5.70/5.70", "prev_map": "3.80%", "adopted": "3.80/3.80",
           "authority": "Iowa DOR — 2025 flat 3.8% individual rate",
           "url": "https://revenue.iowa.gov/press-release/2024-10-16/idr-announces-2025-individual-income-tax-brackets-and-interest-rates", "effective": "Jan 1 2025"},
    "ID": {"prev_tax": "5.80/5.80", "prev_map": "5.30%", "adopted": "5.30/5.30",
           "authority": "Idaho HB 40 (2025), retroactive to Jan 1 2025",
           "url": "https://legislature.idaho.gov/wp-content/uploads/sessioninfo/2025/legislation/H0040.pdf", "effective": "Jan 1 2025"},
    "IN": {"prev_tax": "3.05/3.05", "prev_map": "3%", "adopted": "3.00/3.00",
           "authority": "Indiana DOR — 3.0% flat for 2025",
           "url": "https://www.in.gov/dor/resources/tax-rates-and-reports/rates-fees-and-penalties/", "effective": "TY2025"},
    "KS": {"prev_tax": "5.70/5.70", "prev_map": "5.58%", "adopted": "5.58/5.58",
           "authority": "Kansas DOR — two-bracket top 5.58% (2024 SB 1)",
           "url": "https://www.ksrevenue.gov/taxrates.html", "effective": "TY2025"},
    "LA": {"prev_tax": "4.25/4.25", "prev_map": "3%", "adopted": "3.00/3.00",
           "authority": "Louisiana DOR RIB 25-012 — flat 3%, cap-gains deduction repealed",
           "url": "https://revenue.louisiana.gov/tax-education-and-faqs/faqs/income-tax-reform/what-are-the-individual-income-tax-rates-and-brackets/", "effective": "Jan 1 2025"},
    "MA": {"prev_tax": "5.00/8.50", "prev_map": "9%", "adopted": "9.00/12.50",
           "authority": "Mass.gov — 4% surtax over $1,083,150 on LT (5%) and ST (8.5%)",
           "url": "https://www.mass.gov/info-details/massachusetts-4-surtax-on-taxable-income", "effective": "TY2025"},
    "MD": {"prev_tax": "5.75/5.75", "prev_map": "8.50%", "adopted": "8.50/6.50",
           "authority": "MD Comptroller TB-58 + 2025 Budget Recon. Act (6.5% top + 2% cap-gains surtax on LT)",
           "url": "https://www.marylandcomptroller.gov/content/dam/mdcomp/tax/legal-publications/technical-bulletins/tb-58.pdf", "effective": "TY2025"},
    "MN": {"prev_tax": "9.85/9.85", "prev_map": "10.8%", "adopted": "10.85/10.85",
           "authority": "MN DOR — 9.85% top + 1% NIIT surtax over $1M",
           "url": "https://www.revenue.state.mn.us/net-investment-income-tax-niit", "effective": "TY2024+"},
    "MO": {"prev_tax": "4.80/4.80", "prev_map": "0%", "adopted": "0.00/0.00",
           "authority": "MO HB 594 (2025) — 100% capital-gains exemption",
           "url": "https://dor.mo.gov/news/newsitem/uuid/15044650-59dd-48f4-975a-01988d485255", "effective": "Jan 1 2025"},
    "MS": {"prev_tax": "4.70/4.70", "prev_map": "4.40%", "adopted": "4.40/4.40",
           "authority": "MS DOR — flat 4.4% for 2025",
           "url": "https://www.dor.ms.gov/general-information", "effective": "TY2025"},
    "NC": {"prev_tax": "4.50/4.50", "prev_map": "4.25%", "adopted": "4.25/4.25",
           "authority": "NCDOR — flat 4.25% for 2025",
           "url": "https://www.ncdor.gov/taxes-forms/individual-income-tax/tax-rate-schedules", "effective": "TY2025"},
    "NE": {"prev_tax": "5.84/5.84", "prev_map": "5.20%", "adopted": "5.20/5.20",
           "authority": "Nebraska LB 754 / R.S. 77-2715.03 — 5.20% top for 2025",
           "url": "https://www.nebraskalegislature.gov/laws/statutes.php?statute=77-2715.03", "effective": "TY2025"},
    "NM": {"prev_tax": "3.54/5.90", "prev_map": "5.90%", "adopted": "5.90/5.90",
           "authority": "NM Stat. 7-2-34 (eff. 1/1/2025, HB 252) — general 40% LT exclusion repealed",
           "url": "https://law.justia.com/codes/new-mexico/chapter-7/article-2/section-7-2-34/", "effective": "Jan 1 2025"},
    "OH": {"prev_tax": "3.50/3.50", "prev_map": "3.13%", "adopted": "3.125/3.125",
           "authority": "Ohio Dept. of Taxation — 3.125% top for 2025 (flat 2.75% in 2026)",
           "url": "https://tax.ohio.gov/individual/resources/annual-tax-rates", "effective": "TY2025"},
    "SC": {"prev_tax": "3.47/6.20", "prev_map": "3.36%", "adopted": "3.36/6.00",
           "authority": "SC DOR — 2025 top rate 6.0%; 44% LT deduction (§12-6-1150) → LT 3.36%",
           "url": "https://dor.sc.gov/iit", "effective": "TY2025"},
    "UT": {"prev_tax": "4.55/4.55", "prev_map": "4.50%", "adopted": "4.50/4.50",
           "authority": "Utah HB 106 (2025) — flat 4.50%, retroactive to Jan 1 2025",
           "url": "https://incometax.utah.gov/paying/tax-rates", "effective": "Jan 1 2025"},
    "VT": {"prev_tax": "5.25/8.75", "prev_map": "8.75%", "adopted": "8.75/8.75",
           "authority": "VT Dept. of Taxes / Reg. 1.5811(21)(B)(ii) — 40% LT exclusion unavailable for listed securities",
           "url": "https://tax.vermont.gov/individuals/personal-income-tax/taxable-income", "effective": "TY2025"},
    "WA": {"prev_tax": "7.00/0.00", "prev_map": "9.90%", "adopted": "9.90/0.00",
           "authority": "WA DOR — SB 5813 added a 2.9% tier over $1M to the 7% LT excise",
           "url": "https://dor.wa.gov/forms-publications/publications-subject/special-notices/new-tiered-rates-washingtons-capital-gains-tax", "effective": "Jan 1 2025"},
    "WV": {"prev_tax": "5.12/5.12", "prev_map": "4.82%", "adopted": "4.82/4.82",
           "authority": "WV Tax Division — 2025 IT-140 top rate 4.82% (triggered cut)",
           "url": "https://tax.wv.gov/Documents/PIT/2025/it140.TaxRateSchedules.2025.pdf", "effective": "Jan 1 2025"},
}
