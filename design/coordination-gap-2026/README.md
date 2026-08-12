# Coordination Gap 2026 · evidence register and COI collateral

Working set for the corridor-professional leave-behind (Wierenga, and the Lauren Sanuw email written
to be forwardable to Rich Campbell) and the prospect-facing sheet that follows it.

**This is collateral, not site content.** It deliberately lives outside `src/drift/web/` so it is
never deployed and never one `<img src>` away from a page. Section 05 of the register is the plan for
moving individual figures onto the site; nothing here ships to `docs/` as-is.

## Files

| File | What it is |
|---|---|
| `evidence-register.html` | The working document: verification verdicts, the ranked register, both sheet rationales, and the website implementation plan. Read this first. |
| `onepager-a-coordination-gap.html` | Sheet A, two pages. Estate attorneys and CPAs. Forwardable by an attorney to their own client. |
| `onepager-b-outlast-the-handoff.html` | Sheet B, one page. Prospects evaluating advisors, and adult children of existing relationships. |
| `_print.css` | Shared sheet spec. US Letter, 40pt margin, limestone field, hairline rules, zero radius, no shadow. |
| `build.py` | Inlines the fonts, lints the copy, renders the PDFs. |
| `collateral/` | Build output. Self-contained HTML plus the two PDFs. Regenerated, not hand-edited. |

## Build

```bash
python3 design/coordination-gap-2026/build.py
```

Two things the build does on purpose:

1. **Inlines Satoshi and Erode as data URIs** from `src/drift/web/fonts/`. These sheets get emailed,
   forwarded, and printed on someone else's machine. A silent fallback to Helvetica would change the
   one thing the layout is built around. Same pattern as `design/hero-watershed-2026/inline-fonts.py`.
2. **Refuses to build if an em dash or en dash survives in the copy.** The house voice does not use
   them, and a stray one arrives by paste rather than by decision, so failing the build is cheaper
   than proofreading two pages of dense type on every figure revision.

Both sheets are laid out to a fixed 8.5in by 11in box with `overflow:hidden`, so copy that grows past
the trim is clipped rather than reflowed onto a third page. After any copy edit, re-measure:

```bash
cd design/coordination-gap-2026/collateral && python3 - <<'EOF'
import glob, os
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(args=["--no-sandbox"])
    pg = b.new_page(viewport={"width": 816, "height": 1056})
    for f in sorted(glob.glob("onepager-*.html")):
        pg.goto("file://" + os.path.abspath(f)); pg.emulate_media(media="print")
        print(f, pg.evaluate("""() => [...document.querySelectorAll('.sheet')].map((s,i)=>{
            const padB=parseFloat(getComputedStyle(s).paddingBottom), sr=s.getBoundingClientRect();
            let c=0; for (const ch of s.children){ if(ch.classList.contains('foot')) continue;
              c=Math.max(c, ch.getBoundingClientRect().bottom - sr.top);}
            return {sheet:i+1, over:+(c-(sr.height-padB)).toFixed(1)};})"""))
    b.close()
EOF
```

Every sheet must report `over: 0`. Anything above zero is text sitting in the bottom margin.

## Sourcing rules this set follows

- **Level 1 leads.** Every Tier 1 item in the register is statute, regulation, or a regulator's own
  publication. The load-bearing figures on Sheet A are the Illinois Attorney General's published
  computation examples, not a third-party summary of them.
- **Illustrations are labeled.** The 36-to-820 arithmetic carries `Illustration, not a research
  finding` on the sheet itself, never a citation line that would let it read as a study.
- **Affiliations are disclosed at the point of claim.** The mutual fund and ETF tax-cost figures are
  Morningstar data reported by American Century, which is Avantis's parent. That is stated in the
  citation, not a footnote.

## Open items before distribution

Section 06 of the register carries the full list. The two that block a send:

1. **Disclosure conflict.** Site pages carry a Park Avenue Securities disclosure; these sheets carry
   "not currently a registered investment adviser." Both cannot be current. See
   `tests/test_drift_disclosures.py`.
2. **Illinois figures need re-verification** against 35 ILCS 405 and the Attorney General's current
   fact sheet, which is revised without announcement, plus a check that HB2601 has not moved.
