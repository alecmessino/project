"""The multi-dimension State Tax Map dataset — single source of truth for the cartogram.

Seven *factual* regime dimensions per state (each colored on the map, with original detail copy written
fresh from the facts) plus a HIGHLIGHTED Structural-Alpha synthesis tab:

  1. Income & gains  — top effective long-term rate + conformity (no-tax / conforming / non-conforming /
                       expiring / long-term-only).
  2. Marriage        — filing-status regime (brackets double / partial penalty / one schedule /
                       flat / no income tax).
  3. Death           — state estate / inheritance / both / none, with top rate + exemption (2025 law).
  4. Munis           — municipal-bond interest: all exempt / in-state exempt only / taxes all / n/a.
  5. QSBS            — IRC §1202 conformity: conforms / decoupled / n/a.
  6. Losses          — capital-loss carryforward: federal §1212 / expires / none / no-tax / n/a.
  7. Basis step-up   — marital-property regime (community / opt-in trust / common law + UDCPRDA /
                       common law) governing the IRC 1014 step-up.
  ★ Structural Alpha — the HIGHLIGHTED synthesis: `leakage.STATE_ALPHA`, the illustrative recoverable
                       tax leakage our engine targets given everything above. Diagnostic-gated.

Per-state classifications, effective rates, and exemptions are settled public-domain tax facts
(tax year 2025); they are stated here in our own words. A per-dimension "Prove it" statutory citation
is attached ONLY where the exact code section has been independently verified (Illinois today); every
other state carries a generic source line until its statute is checked — we do not fabricate cites.
Structural-Alpha values trace to our own `STATE_ALPHA`; that dimension is illustrative/hypothetical.
"""

from __future__ import annotations

import time

from .leakage import STATE_ALPHA, STATE_NAMES

# ── Cartogram layout (our own tile grid; 50 states + DC + a territories strip) ───────────────────
TILES = {
    "AK": [0, 0], "ME": [11, 0],
    "VT": [10, 1], "NH": [11, 1],
    "WA": [0, 2], "ID": [1, 2], "MT": [2, 2], "ND": [3, 2], "MN": [4, 2], "WI": [5, 2], "IL": [6, 2],
    "MI": [7, 2], "NY": [9, 2], "MA": [10, 2], "CT": [11, 2],
    "OR": [0, 3], "NV": [1, 3], "WY": [2, 3], "SD": [3, 3], "IA": [4, 3], "IN": [5, 3], "OH": [6, 3],
    "PA": [7, 3], "NJ": [8, 3], "RI": [10, 3],
    "CA": [0, 4], "UT": [1, 4], "CO": [2, 4], "NE": [3, 4], "MO": [4, 4], "KY": [5, 4], "WV": [6, 4],
    "VA": [7, 4], "MD": [8, 4], "DE": [9, 4],
    "AZ": [1, 5], "NM": [2, 5], "KS": [3, 5], "AR": [4, 5], "TN": [5, 5], "NC": [6, 5], "SC": [7, 5],
    "DC": [8, 5],
    "OK": [3, 6], "LA": [4, 6], "MS": [5, 6], "AL": [6, 6], "GA": [7, 6],
    "HI": [0, 7], "TX": [3, 7], "FL": [7, 7],
    "AS": [5, 8], "GU": [6, 8], "MP": [7, 8], "PR": [8, 8], "VI": [9, 8],
}
TERRITORIES = {"AS", "GU", "MP", "PR", "VI"}

NAMES = dict(STATE_NAMES)
NAMES.update({"AS": "American Samoa", "GU": "Guam", "MP": "N. Mariana Islands",
              "PR": "Puerto Rico", "VI": "U.S. Virgin Islands"})

# ── 1 · Income & gains: harvested-loss conformity + top effective LT rate + quirk ─────────────────
# (regime, top_effective_lt_rate, quirk). regime ∈ notax/conforming/nonconforming/expiring/lt_only.
_INCOME = {
    "AK": ("notax", "0%", ""), "AL": ("nonconforming", "5%", "losses offset income same year only — no carryforward"),
    "AR": ("conforming", "1.95%", "50% long-term exclusion; net gain over $10M fully exempt"),
    "AZ": ("conforming", "1.88%", "25% long-term subtraction (post-2011 lots)"),
    "CA": ("conforming", "13.3%", "12.3% + a 1% surtax over $1M"),
    "CO": ("conforming", "4.40%", "a TABOR surplus can cut the rate in a given year"),
    "CT": ("conforming", "6.99%", "recapture: a flat rate on all income over ~$1.08M"),
    "DC": ("conforming", "10.8%", ""), "DE": ("conforming", "6.60%", ""), "FL": ("notax", "0%", ""),
    "GA": ("conforming", "5.19%", "drops to 4.99% in 2026"),
    "HI": ("expiring", "7.25%", "7.25% long-term cap; loss carryforward dies after 5 years"),
    "IA": ("conforming", "3.80%", "local school surtax can add up to +20% of tax"),
    "ID": ("conforming", "5.30%", ""), "IL": ("conforming", "4.95%", ""),
    "IN": ("conforming", "3%", "+ county tax; 2.95% in 2026"), "KS": ("conforming", "5.58%", ""),
    "KY": ("conforming", "4%", "drops to 3.5% in 2026"), "LA": ("conforming", "3%", ""),
    "MA": ("conforming", "9%", "5% long-term + a 4% surtax over ~$1.1M; short-term taxed 8.5%"),
    "MD": ("conforming", "8.50%", "6.5% + a 2% gain surtax (cliff at $350K) + county tax"),
    "ME": ("conforming", "7.15%", ""), "MI": ("conforming", "4.25%", "+ city tax (Detroit 2.4%)"),
    "MN": ("conforming", "10.8%", "9.85% + a 1% net-investment surtax over $1M"),
    "MO": ("notax", "0%", "gains exempt from 2025; losses still deduct (up to 4.7%)"),
    "MS": ("conforming", "4.40%", "4.0% in 2026, stepping toward 3.0% by 2030"),
    "MT": ("conforming", "4.10%", "a separate, lower long-term schedule (3.0 / 4.1%)"),
    "NC": ("conforming", "4.25%", "3.99% in 2026"), "ND": ("conforming", "1.50%", "40% long-term exclusion"),
    "NE": ("conforming", "5.20%", "4.55% in 2026"), "NH": ("notax", "0%", ""),
    "NJ": ("nonconforming", "10.8%", "no carryforward — banked losses never reach the NJ bill"),
    "NM": ("conforming", "5.90%", "the 40% exclusion was repealed in 2025 ($2,500 cap)"),
    "NV": ("notax", "0%", ""),
    "NY": ("conforming", "10.9%", "+ NYC ~3.88% (~14.8% combined); flat-on-all-income recapture"),
    "OH": ("conforming", "3.13%", "school districts can add ~0.25–2%"),
    "OK": ("conforming", "4.75%", "4.5% in 2026"),
    "OR": ("conforming", "9.90%", "+ Portland-metro tax up to 4% (~13.9% combined)"),
    "PA": ("nonconforming", "3.07%", "no carryforward; losses locked to the year, the class, and the spouse"),
    "RI": ("conforming", "5.99%", ""), "SC": ("conforming", "3.36%", "44% net-gain deduction"),
    "SD": ("notax", "0%", ""), "TN": ("notax", "0%", ""), "TX": ("notax", "0%", ""),
    "UT": ("conforming", "4.50%", ""), "VA": ("conforming", "5.75%", ""),
    "VT": ("conforming", "8.75%", "listed securities get only a $5K exclusion; a 3%-of-AGI floor"),
    "WA": ("lt_only", "9.90%", "a 7% + 2.9% excise on long-term gains only, gross of short-term losses"),
    "WI": ("conforming", "5.36%", "30% long-term exclusion"),
    "WV": ("conforming", "4.82%", "4.58% in 2026"), "WY": ("notax", "0%", ""),
    "AS": ("conforming", "20%", "IRC frozen at 12/31/2000; the rate is the total tax, replacing federal"),
    "GU": ("conforming", "20%", "federal mirror code; the rate is the total tax, replacing federal"),
    "MP": ("conforming", "20%", "federal mirror code; the rate is the total tax, replacing federal"),
    "PR": ("expiring", "15%", "own code: 15% is the total tax; carryforward 7 years as short-term, 90% cap"),
    "VI": ("conforming", "20%", "federal mirror code; the rate is the total tax, replacing federal"),
}
_INC_TAG = {"notax": "0%"}
_INCOME_NOTE = {
    "notax": "No state tax on capital gains — and a harvested loss is worth only the federal rate here.",
    "conforming": "Loss treatment conforms to federal: capital losses net against gains and carry forward. Top effective long-term rate {rate}.",
    "nonconforming": "Non-conforming loss treatment — {quirk}. A harvested loss may never reach the state bill. Top effective long-term rate {rate}.",
    "expiring": "Loss carryforward is time-limited — {quirk}. Top effective long-term rate {rate}.",
    "lt_only": "Taxes long-term gains only — {quirk}. Top effective long-term rate {rate}.",
}


def _income(code):
    if code not in _INCOME:
        return None
    regime, rate, quirk = _INCOME[code]
    if regime == "notax" and quirk:
        # A no-income-tax state can still have loss quirks (e.g. MO: gains exempt but losses deduct);
        # the generic "loss worth only the federal rate" line would be FALSE, so state the quirk instead.
        note = f"No state tax on realized capital gains. {quirk[0].upper() + quirk[1:]}."
    else:
        note = _INCOME_NOTE[regime].format(rate=rate, quirk=quirk)
        if regime == "conforming" and quirk:
            note += f" Quirk: {quirk}."
    return {"regime": regime, "tag": rate, "note": note,
            "source": "State revenue departments, tax year 2025 — verify with a tax advisor."}


# ── 2 · Marriage: filing-status regime ───────────────────────────────────────────────────────────
_MARRIAGE = {
    "AK": "notax", "AL": "double", "AR": "one", "AZ": "flat", "CA": "double", "CO": "flat",
    "CT": "partial", "DC": "one", "DE": "one", "FL": "notax", "GA": "flat", "HI": "double",
    "IA": "flat", "ID": "flat", "IL": "flat", "IN": "flat", "KS": "double", "KY": "flat", "LA": "flat",
    "MA": "flat", "MD": "partial", "ME": "double", "MI": "flat", "MN": "partial", "MO": "one",
    "MS": "flat", "MT": "double", "NC": "flat", "ND": "partial", "NE": "double", "NH": "notax",
    "NJ": "partial", "NM": "partial", "NV": "notax", "NY": "partial", "OH": "one", "OK": "partial",
    "OR": "double", "PA": "flat", "RI": "one", "SC": "one", "SD": "notax", "TN": "notax", "TX": "notax",
    "UT": "flat", "VA": "one", "VT": "partial", "WA": "one", "WI": "partial", "WV": "one", "WY": "notax",
    "AS": "partial", "GU": "partial", "MP": "partial", "PR": "one", "VI": "partial",
}
_MARRIAGE_TAG = {"notax": "", "flat": "flat", "double": "2x", "partial": "~2x", "one": "1x"}
_MARRIAGE_NOTE = {
    "notax": "No state income tax — no marriage penalty on the state return.",
    "flat": "A single flat rate regardless of filing status — marriage-neutral on rate; watch fixed-dollar exemptions and AGI thresholds.",
    "double": "Joint brackets are double the single brackets — generally marriage-neutral.",
    "partial": "Joint brackets widen for couples, but by less than 2× — a partial marriage penalty that bites on higher incomes.",
    "one": "One bracket schedule applies to both single and joint filers — a structural marriage penalty for two earners.",
}

# ── 3 · Estate / inheritance (2025 law) — regime + top rate + exemption + quirk ───────────────────
# (regime, top_rate, exemption, quirk). regime ∈ none/estate/inheritance/both.
_ESTATE = {
    "CT": ("estate", "12%", "$15M", ""), "DC": ("estate", "16%", "$4.99M", ""),
    "HI": ("estate", "20%", "$5.49M", ""), "IL": ("estate", "16%", "$4M", ""),
    "MA": ("estate", "16%", "$2M", ""), "ME": ("estate", "12%", "$7.16M", ""),
    "MN": ("estate", "16%", "$3M", ""), "NY": ("estate", "16%", "$7.35M", "a cliff: clear the exemption by >5% and the whole estate is taxed"),
    "OR": ("estate", "16%", "$1M", ""), "RI": ("estate", "16%", "$1.84M", ""),
    "VT": ("estate", "16%", "$5M", ""), "WA": ("estate", "35%", "$3M", ""),
    "KY": ("inheritance", "16%", "", ""), "NE": ("inheritance", "15%", "", ""),
    "NJ": ("inheritance", "16%", "", ""), "PA": ("inheritance", "15%", "", ""),
    "MD": ("both", "16%", "$5M", ""),
}
_ESTATE_TAG = {"estate": "estate", "inheritance": "inher.", "both": "estate+inh", "none": ""}
_ESTATE_NOTE_IL = ("Illinois estate tax: a $4,000,000 exemption (not indexed — a taxable threshold, not a "
                   "credit; SB 2970 to $6,000,000 is pending, not enacted). Top rate ~16% (the tax equals the "
                   "IRC 2011 state death-tax credit frozen at 12/31/2001, 0.8–16% over 21 brackets), with "
                   "soft-cliff mechanics: once the estate clears $4M the table applies to the whole taxable "
                   "estate. Administered by the Attorney General, not IDOR; no portability. Confirm with counsel.")


def _estate(code):
    if code == "IL":
        return {"regime": "estate", "tag": "estate", "note": _ESTATE_NOTE_IL,
                "source": "State estate/inheritance statutes, tax year 2025 — confirm with counsel."}
    regime, rate, exm, quirk = (_ESTATE.get(code) or ("none", "", "", ""))
    notes = {
        "none": "No state estate or inheritance tax — only the federal estate tax applies.",
        "estate": f"State estate tax (paid by the estate): top rate ~{rate}, exemption ~{exm}."
                  + (f" {quirk[0].upper()+quirk[1:]}." if quirk else " Confirm the figure with counsel."),
        "inheritance": f"State inheritance tax (paid by beneficiaries; the rate depends on the heir's relationship), top rate ~{rate}.",
        "both": f"Both a state estate tax (~{rate}, exemption ~{exm}) and an inheritance tax can apply — coordinate with counsel.",
    }
    return {"regime": regime, "tag": _ESTATE_TAG[regime], "note": notes[regime],
            "source": "State estate/inheritance statutes, tax year 2025 — confirm with counsel."}


# ── 4 · Basis step-up: marital-property regime ───────────────────────────────────────────────────
_STEPUP = {
    "AK": "optin", "AL": "common", "AR": "udcprda", "AZ": "community", "CA": "community",
    "CO": "udcprda", "CT": "udcprda", "DC": "common", "DE": "common", "FL": "optin", "GA": "common",
    "HI": "udcprda", "IA": "common", "ID": "community", "IL": "common", "IN": "common", "KS": "common",
    "KY": "optin", "LA": "community", "MA": "common", "MD": "common", "ME": "common", "MI": "udcprda",
    "MN": "udcprda", "MO": "common", "MS": "common", "MT": "udcprda", "NC": "udcprda", "ND": "common",
    "NE": "common", "NH": "common", "NJ": "common", "NM": "community", "NV": "community", "NY": "udcprda",
    "OH": "common", "OK": "common", "OR": "udcprda", "PA": "common", "RI": "common", "SC": "common",
    "SD": "optin", "TN": "optin", "TX": "community", "UT": "udcprda", "VA": "udcprda", "VT": "common",
    "WA": "community", "WI": "community", "WV": "common", "WY": "udcprda",
    "AS": "common", "GU": "community", "MP": "common", "PR": "community", "VI": "common",
}
_STEPUP_TAG = {"common": "", "udcprda": "UDCPRDA", "optin": "opt-in", "community": "CP"}
_STEPUP_NOTE = {
    "common": "Common-law (separate-property) state: at the first spouse's death only the decedent's "
              "half of jointly-held property steps up; the survivor keeps carryover basis on their half "
              "(IRC 1014(b)(9), 2040(b)).",
    "udcprda": "Common-law state that has adopted the UDCPRDA — it preserves the community-property "
               "character (and the potential full step-up) of assets a couple brought from a CP state.",
    "optin": "Offers an elective community-property trust: a couple can opt in to obtain a full "
             "(double) basis step-up at the first death.",
    "community": "Community-property state: BOTH halves of community property step up to fair market "
                 "value at the first spouse's death (IRC 1014(b)(6)) — a major basis advantage.",
}

# ── 5 · Municipal-bond interest: home-state exemption regime ──────────────────────────────────────
# regime ∈ allexempt (in- and out-of-state exempt) / instate (only in-state exempt) / taxall / na.
_MUNI = {
    "AK": "allexempt", "AL": "instate", "AR": "instate", "AZ": "instate", "CA": "instate", "CO": "instate", "CT": "instate", "DC": "instate",
    "DE": "instate", "FL": "allexempt", "GA": "instate", "HI": "instate", "IA": "taxall", "ID": "instate", "IL": "taxall", "IN": "instate",
    "KS": "instate", "KY": "instate", "LA": "instate", "MA": "instate", "MD": "instate", "ME": "instate", "MI": "instate", "MN": "instate",
    "MO": "instate", "MS": "instate", "MT": "instate", "NC": "instate", "ND": "allexempt", "NE": "instate", "NH": "allexempt", "NJ": "instate",
    "NM": "instate", "NV": "allexempt", "NY": "instate", "OH": "instate", "OK": "instate", "OR": "instate", "PA": "instate", "RI": "instate",
    "SC": "instate", "SD": "allexempt", "TN": "allexempt", "TX": "allexempt", "UT": "instate", "VA": "instate", "VT": "instate", "WA": "allexempt",
    "WI": "taxall", "WV": "instate", "WY": "allexempt", "AS": "na", "GU": "na", "MP": "na", "PR": "na", "VI": "na",
}
_MUNI_TAG = {"allexempt": "exempt", "instate": "in-state", "taxall": "taxed", "na": ""}
_MUNI_NOTE = {
    "allexempt": "Municipal-bond interest is exempt from state tax whether the issuer is in-state or out-of-state — the broadest muni preference (states with no tax on investment income, plus a few that exempt all munis by statute).",
    "instate": "Only in-state municipal-bond interest escapes state tax; bonds from other states are taxed. The classic in-state muni preference that rewards a home-state ladder.",
    "taxall": "Taxes municipal-bond interest from every issuer — in-state and out-of-state alike. One of the few states with no muni-interest preference at all.",
    "na": "No separate state treatment applies here — the jurisdiction taxes under its own or a mirror-federal code.",
}

# ── 6 · QSBS (IRC §1202) conformity ───────────────────────────────────────────────────────────────
# regime ∈ conforms (§1202 exclusion flows to the state return) / decoupled (state still taxes it) / na.
_QSBS = {
    "AK": "na", "AL": "decoupled", "AR": "conforms", "AZ": "conforms", "CA": "decoupled", "CO": "conforms", "CT": "conforms", "DC": "decoupled",
    "DE": "conforms", "FL": "na", "GA": "conforms", "HI": "na", "IA": "conforms", "ID": "conforms", "IL": "conforms", "IN": "conforms",
    "KS": "conforms", "KY": "conforms", "LA": "conforms", "MA": "conforms", "MD": "conforms", "ME": "na", "MI": "conforms", "MN": "na",
    "MO": "conforms", "MS": "decoupled", "MT": "conforms", "NC": "conforms", "ND": "conforms", "NE": "conforms", "NH": "na", "NJ": "decoupled",
    "NM": "conforms", "NV": "na", "NY": "conforms", "OH": "conforms", "OK": "conforms", "OR": "conforms", "PA": "decoupled", "RI": "conforms",
    "SC": "conforms", "SD": "na", "TN": "na", "TX": "na", "UT": "conforms", "VA": "conforms", "VT": "conforms", "WA": "conforms",
    "WI": "conforms", "WV": "conforms", "WY": "na", "AS": "na", "GU": "conforms", "MP": "conforms", "PR": "decoupled", "VI": "conforms",
}
_QSBS_TAG = {"conforms": "§1202 ok", "decoupled": "decoupled", "na": "no §1202"}
_QSBS_NOTE = {
    "conforms": "Conforms to IRC §1202 — the federal qualified small business stock gain exclusion carries through to the state return.",
    "decoupled": "Decoupled from IRC §1202 — the state does not follow the federal QSBS exclusion, so gain excluded on the federal return can still be taxed by the state.",
    "na": "No distinct state QSBS position applies here — either the jurisdiction levies no tax on the gain, or it does not separately recognize the §1202 exclusion. Confirm with a tax advisor.",
}

# ── 7 · Capital-loss carryforward ─────────────────────────────────────────────────────────────────
# regime ∈ fed (federal §1212 carryforward) / expires (time-limited) / none (no carryforward) / notax / na.
_LOSS = {
    "AK": "notax", "AL": "none", "AR": "fed", "AZ": "fed", "CA": "fed", "CO": "fed", "CT": "fed", "DC": "fed",
    "DE": "fed", "FL": "notax", "GA": "fed", "HI": "expires", "IA": "fed", "ID": "fed", "IL": "fed", "IN": "fed",
    "KS": "fed", "KY": "fed", "LA": "fed", "MA": "fed", "MD": "fed", "ME": "fed", "MI": "fed", "MN": "fed",
    "MO": "notax", "MS": "fed", "MT": "fed", "NC": "fed", "ND": "fed", "NE": "fed", "NH": "notax", "NJ": "none",
    "NM": "fed", "NV": "notax", "NY": "fed", "OH": "fed", "OK": "fed", "OR": "fed", "PA": "none", "RI": "fed",
    "SC": "fed", "SD": "notax", "TN": "notax", "TX": "notax", "UT": "fed", "VA": "fed", "VT": "fed", "WA": "fed",
    "WI": "fed", "WV": "fed", "WY": "notax", "AS": "na", "GU": "na", "MP": "na", "PR": "expires", "VI": "na",
}
_LOSS_TAG = {"fed": "federal", "expires": "expires", "none": "none", "notax": "", "na": ""}
_LOSS_QUIRK = {  # only where the regime has a state-specific caveat
    "HI": "the Hawaii carryforward dies after 5 years", "PR": "Puerto Rico allows a 7-year carryforward, taxed as short-term and capped at 90%",
    "AL": "Alabama allows a loss only against same-year income", "NJ": "New Jersey has no carryforward — banked losses never reach the NJ bill",
    "PA": "Pennsylvania locks a loss to the year, the income class, and the spouse",
}
_LOSS_NOTE = {
    "fed": "Capital losses carry forward under the federal Section 1212 rules — a harvested loss nets against gains and rolls forward until used.",
    "expires": "Loss carryforward is time-limited and expires — {quirk}. Harvest before the clock runs out.",
    "none": "No loss carryforward — a capital loss must be used the year it is realized or it is lost, so harvesting only helps against same-year gains ({quirk}).",
    "notax": "No state tax on capital gains, so a harvested loss carries no state benefit; its value here is only the federal offset.",
    "na": "Taxed under the jurisdiction's own or mirror-federal code; no separate state loss-carryforward rule applies.",
}


def _categorical(code, table, tags, notes, source, quirks=None):
    """Build a record for a categorical dimension (muni/qsbs/loss) from its regime table."""
    if code not in table:
        return None
    regime = table[code]
    note = notes[regime]
    if "{quirk}" in note:
        note = note.format(quirk=(quirks or {}).get(code, "see the state's rule"))
    return {"regime": regime, "tag": tags[regime], "note": note, "source": source}


# ── Primary-source statutory citations ("Prove it") — ONLY where independently verified ───────────
# Today that is Illinois; every other state shows the generic source line until its statute is checked.
# NEVER add an entry here that has not been verified against the actual code section — a fabricated
# legal citation on an RIA site is a real liability. (url, label) pairs; a dimension may cite several.
_ILGA_ITA = "https://www.ilga.gov/legislation/ilcs/ilcs3.asp?ActID=591&ChapterID=8"
_CITATIONS = {
    ("IL", "cg"): [(_ILGA_ITA, "35 ILCS 5/201(b)(1) (Illinois Income Tax Act)")],
    ("IL", "marriage"): [(_ILGA_ITA, "35 ILCS 5/201(b)(1) (Illinois Income Tax Act)")],
    ("IL", "estate"): [
        ("https://ilga.gov/Documents/legislation/ilcs/documents/003504050K3.htm", "35 ILCS 405/3 (Illinois Estate & GST Tax Act)"),
        ("https://ilga.gov/Documents/legislation/ilcs/documents/003504050K2.htm", "35 ILCS 405/2 (Illinois Estate & GST Tax Act)"),
    ],
    ("IL", "muni"): [(_ILGA_ITA, "35 ILCS 5/203(a)(2)(A) and (N); 86 Ill. Adm. Code 100.2470")],
    ("IL", "qsbs"): [(_ILGA_ITA, "35 ILCS 5/102 (Illinois Income Tax Act)")],
    ("IL", "loss"): [(_ILGA_ITA, "35 ILCS 5/201(b)(1) (Illinois Income Tax Act)")],
}


def _attach_citations(code, rec):
    """Add a `citation` list to any dimension record for which a verified statute exists."""
    for dim, r in rec.items():
        cites = _CITATIONS.get((code, dim))
        if cites:
            r["citation"] = [{"url": u, "label": l} for u, l in cites]
    return rec


# ── 8 · Structural Alpha (highlighted) ────────────────────────────────────────────────────────────
_ALPHA_BUCKETS = [(3.8, "a"), (4.0, "b"), (4.3, "c"), (4.5, "d"), (99, "e")]


def _alpha_bucket(a):
    for hi, key in _ALPHA_BUCKETS:
        if a < hi:
            return key
    return "e"


DIMENSIONS = [
    {"key": "cg", "label": "Income & gains", "title": "Where a harvested loss lands",
     "legend": [("notax", "#d8cfbc", "No tax on gains"), ("conforming", "#7faa97", "Conforming"),
                ("nonconforming", "#9b4439", "Non-conforming"), ("expiring", "#c1a35b", "Expiring"),
                ("lt_only", "#15806a", "Long-term only")]},
    {"key": "marriage", "label": "Marriage", "title": "The marriage penalty, state by state",
     "legend": [("notax", "#d8cfbc", "No income tax"), ("double", "#15806a", "Brackets double"),
                ("flat", "#7faa97", "Flat rate"), ("partial", "#c1a35b", "Partial penalty"),
                ("one", "#9b4439", "One schedule")]},
    {"key": "estate", "label": "Death", "title": "Estate & inheritance tax at death",
     "legend": [("none", "#d8cfbc", "None"), ("estate", "#15806a", "Estate tax"),
                ("inheritance", "#c1a35b", "Inheritance tax"), ("both", "#9b4439", "Both")]},
    {"key": "muni", "label": "Munis", "title": "How each state taxes municipal-bond interest",
     "legend": [("allexempt", "#d8cfbc", "All munis exempt"), ("instate", "#7faa97", "In-state exempt only"),
                ("taxall", "#9b4439", "Taxes all munis"), ("na", "#cdc7ba", "n/a")]},
    {"key": "qsbs", "label": "QSBS", "title": "Does the state follow the §1202 QSBS exclusion?",
     "legend": [("conforms", "#7faa97", "Conforms to §1202"), ("decoupled", "#9b4439", "Decoupled"),
                ("na", "#cdc7ba", "n/a")]},
    {"key": "loss", "label": "Losses", "title": "What happens to a capital loss you carry forward",
     "legend": [("fed", "#7faa97", "Federal carryforward"), ("expires", "#c1a35b", "Expires"),
                ("none", "#9b4439", "No carryforward"), ("notax", "#d8cfbc", "No tax on gains"),
                ("na", "#cdc7ba", "n/a")]},
    {"key": "stepup", "label": "Basis step-up", "title": "Marital property & the basis step-up",
     "legend": [("common", "#d8cfbc", "Common law"), ("udcprda", "#7faa97", "Common law + UDCPRDA"),
                ("optin", "#c1a35b", "Opt-in community trust"), ("community", "#15806a", "Community property")]},
    {"key": "alpha", "label": "Structural Alpha", "title": "What our engine recovers from all of it",
     "highlight": True,
     "legend": [("a", "#cfe0d6", "lower"), ("b", "#9ec9b6", ""), ("c", "#5ea98c", ""),
                ("d", "#2f8467", ""), ("e", "#15604a", "higher recovery")]},
]


def _state_record(code):
    rec = {}
    rec["cg"] = _income(code)
    if code in _MARRIAGE:
        r = _MARRIAGE[code]
        rec["marriage"] = {"regime": r, "tag": _MARRIAGE_TAG[r], "note": _MARRIAGE_NOTE[r],
                           "source": "State income-tax filing schedules, tax year 2025 — verify with a tax advisor."}
    rec["estate"] = _estate(code)
    rec["muni"] = _categorical(
        code, _MUNI, _MUNI_TAG, _MUNI_NOTE,
        "State income-tax statutes on municipal-bond interest, tax year 2025 — verify with a tax advisor.")
    rec["qsbs"] = _categorical(
        code, _QSBS, _QSBS_TAG, _QSBS_NOTE,
        "State IRC-conformity statutes on §1202, tax year 2025 — verify with a tax advisor.")
    rec["loss"] = _categorical(
        code, _LOSS, _LOSS_TAG, _LOSS_NOTE,
        "State capital-loss carryforward rules, tax year 2025 — verify with a tax advisor.", quirks=_LOSS_QUIRK)
    if code in _STEPUP:
        r = _STEPUP[code]
        rec["stepup"] = {"regime": r, "tag": _STEPUP_TAG[r], "note": _STEPUP_NOTE[r],
                         "source": "State marital-property law / IRS Pub. 555; IRC 1014 — verify with counsel."}
    a = STATE_ALPHA.get(code)
    if a is not None:
        nm = NAMES.get(code, code)
        rec["alpha"] = {
            "regime": _alpha_bucket(a["alpha"]), "tag": f"+{a['alpha']:.1f}",
            "value": a["alpha"], "before": a["before"], "after": a["after"],
            "note": (f"Illustrative recoverable tax leakage for a portfolio in {nm}: up to ~+{a['alpha']:.1f}%/yr "
                     f"after tax in our modeling (a concentrated, naive book keeps ~{a['before']:.1f}%/yr vs "
                     f"~{a['after']:.1f}%/yr tax-managed). Your actual figure depends on your holdings — the "
                     f"diagnostic computes it."),
            "source": "scripts/tax_alpha.py · 30y window (1996–2026). Illustrative, hypothetical — diagnostic-gated.",
            "deeplink": f"leakage.html?state={code}",
        }
    return _attach_citations(code, {k: v for k, v in rec.items() if v is not None})


def build_statemap() -> dict:
    """Assemble the State Tax Map state: dimension metadata + per-state records + cartogram layout."""
    codes = list(TILES)
    states = {c: _state_record(c) for c in codes}
    return {
        "header": {
            "generated": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "asof": "Tax year 2025 · compiled from state statutes and revenue-department sources.",
        },
        "dimensions": DIMENSIONS,
        "tiles": TILES,
        "territories": sorted(TERRITORIES),
        "names": {c: NAMES.get(c, c) for c in codes},
        "states": states,
    }
