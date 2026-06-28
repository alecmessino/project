# Disclosure Placement Change Log — for RIA Principal Sign-Off

**Date:** 2026-06-28 · **Requested by:** CWS Planning principal · **Change:** make disclosures
"maximal subtle" while remaining defensibly compliant with SEC Marketing Rule 206(4)-1.

This records exactly what was de-emphasized so the principal can review and sign off. **No required
disclosure language was removed** — every Marketing-Rule element remains present and legible on the
page; what changed is *placement and visual weight*.

## What changed

### Performance exhibits (ledger.html "Model Portfolio", tearsheet.html "long history")
| Element | Before | After |
|---|---|---|
| Full hypothetical-performance disclosure | Prominent banner (brass/red left-border box) **above the metrics** | Quiet **small-print footnote at the foot** of the page (10.5px, muted grey, top-rule separator). Same words. |
| Point-of-performance label | (the banner) | **Kept**: the `HYPOTHETICAL` header pill (ledger) / header tag (tearsheet) **and** the summary card's "Hypothetical backtest — not advice" line stay at the top, beside the numbers. |
| Footer (RIA identity, audience, data, methodology) | 12.5px | Smaller/lighter (11px, muted) |

### All required language retained (verified by guard tests)
- "retroactive application", "no client capital was invested", "does not guarantee future results"
- "Hypothetical / backtested performance — not a real track record"
- RIA identity + "registered investment adviser" + Form ADV/CRS + adviserinfo.sec.gov (every page)
- Audience statement: "Intended for sophisticated investors … may not be relevant to your situation"
- Alpha significance / out-of-sample honesty framing (unchanged)
- Tax Lab print/PDF disclosure block + running footer (unchanged)

## Compliance rationale (and the residual risk the principal is accepting)
- The Marketing Rule does **not** mandate that the hypothetical-performance disclosure sit *above* the
  numbers; it requires the disclosure be present and the presentation not be misleading. Keeping a
  clear **"HYPOTHETICAL" label at the point of performance** while placing the full disclosure as
  legible small print at the foot is a recognized, defensible footnote pattern.
- **Residual risk being accepted:** an examiner could prefer the prior above-the-numbers prominence.
  The mitigation is the retained point-of-performance label + the full, unaltered language at the
  foot in legible (not hidden, not collapsed) form. The principal has chosen the more subtle posture
  with this understanding.

## What was NOT done (held the line here)
- Did **not** remove or shorten any required language.
- Did **not** hide disclosures behind a click/expander or make them illegibly small.
- Did **not** touch the Tax Lab client-PDF disclosure block or running footer (those stay full).

## Guard tests updated
- `tests/test_drift_disclosures.py::test_ledger_hypothetical_disclosure_present_with_point_of_performance_marker`
  now asserts the disclosure is present with all required phrases, the `HYPOTHETICAL` header marker +
  "Hypothetical backtest" summary marker are present, and the full disclosure renders **after** the
  metrics (foot). All other disclosure guards (RIA identity, audience, phrases, PDF block) unchanged
  and passing.
