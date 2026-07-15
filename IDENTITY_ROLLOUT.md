# Identity System v1 — rollout

The Driftwood Wealth visual identity, frozen July 2026. The mark is the **Streams
confluence** — five tributaries (Investments · Taxes · Estate · Liquidity ·
Relationships) gathering gradually into one coordinated river ("what you keep"),
the outflow one step heavier so coordination, not direction, reads first.

Full standard: **[`src/drift/web/brand.html`](src/drift/web/brand.html)** (open with `driftwood.css` alongside).
Working sandbox: `src/drift/web/mark-sandbox.html` (not deployed).

## The mark (frozen)

`viewBox 0 0 46 30`, straight geometry, no curves, single ink via `currentColor`:

```
M1.5 1  H4.5 L27 15      ┐ tributaries — outer bend soonest, inner later,
M1.5 8  H8   L27 15      │ so coordination builds gradually (not one sudden node)
M1.5 15 H27              │ middle tributary + outflow are collinear
M1.5 22 H8   L27 15      │
M1.5 29 H4.5 L27 15      ┘ stroke-width 1.4 (fine) / 2.4 (nav) / 2.4 (favicon cut)
M27 15  H44.5              outflow / river — one step heavier (2.2 / 3.4 / 3.2)
```

Canonical files: `brand/mark.svg` (editorial blue), `brand/mark-reversed.svg`
(light-on-dark), `brand/favicon-cut.svg` (heavier, ≤ 32px).

## Lockups

| Lockup | Contents | Use |
|---|---|---|
| **Primary** | mark · hairline · `DRIFTWOOD WEALTH` / `PRIVATE WEALTH ADVISORY` | hero, reports, PDFs, proposals |
| **Secondary** | mark · hairline · `DRIFTWOOD WEALTH` | site navigation, headers, email |
| **Micro** | mark · `DRIFTWOOD WEALTH` (no divider) | browser chrome, dashboard, Advisor Workspace, mobile, footers |
| **Avatar** | mark only (favicon cut ≤ 32px) | favicon, social, app/workspace icon |
| **Signature** | `DRIFTWOOD WEALTH` / *Private Wealth Advisory* / Fee-Only Fiduciary · Austin, Texas | document colophon — proposals, letters, AWOR, Operating Manual |

Metrics live in `driftwood.css` `:root` as `--logo-*` tokens (gap, mark, rule,
word size, word spacing). Clear-space = the mark's height on every side. Below the
minimum lockup width the lockup falls back to the Avatar; on mobile the nav drops
the divider (Micro).

## Colours & type

- Mark & descriptor: **editorial blue** `--accent-strike` `#2c5878`.
- Wordmark: **slate-navy ink** `--ink` `#1e2833` (all-caps, never two-tone).
- Divider: architectural hairline `--line` `#d8d3c6`.
- Reversed: light `#eef2f6` on navy `#1a2330`.
- Wordmark & descriptor set in **Satoshi** (`--sans`), tracked caps.

## Status

### Completed (this PR)
- [x] Mark frozen (Streams), canonical `brand/*.svg` assets
- [x] `--logo-*` design tokens in `driftwood.css`
- [x] Secondary lockup wired into the nav across all 40 templates + `statepage.py` (state pages)
- [x] Favicon system regenerated from the new mark: `favicon.svg`, `mask-icon.svg`, `favicon-32.png`, `apple-touch-icon.png` (src + docs)
- [x] Mobile nav → Micro (divider hidden)
- [x] Brand standard page `brand.html`

### Remaining (follow-ups)
- [ ] Primary lockup in the homepage hero / footer brand sign-off
- [ ] Signature colophon on the Operating-System documents (Manual, Registers, AWOR) and proposals
- [ ] Micro lockup in the Advisor Workspace chrome
- [ ] Regenerate OG social cards with the new mark (`scripts/og_*.mjs`)
- [ ] Confirm **Austin, Texas** as a firm fact before it appears in the Signature (currently unconfirmed — do not ship the location until confirmed)

### Future
- [ ] Export `brand.html` to a distributable **Brand Standards** PDF
- [ ] Apply the identity to client PDFs / pitch decks / report templates
