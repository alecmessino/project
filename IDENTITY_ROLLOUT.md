# Identity System v1 — KIT 02 (frozen)

The Driftwood Wealth visual identity, frozen July 2026. The mark is the **Streams
confluence** — five tributaries entering from one shared origin and stepping through
a true **45° convergence** into a single, heavier trunk: *what you keep*. The trunk
is held at length and cut square, so the mark reads as **coordination and structure**,
not direction or speed.

**The five streams are an emblem, not an inventory.** They stand for confluence
itself, many currents becoming one coordinated whole, and are deliberately *not* a
count of the systems Driftwood coordinates. The working model of what we coordinate
is the **seven-system lattice** on the home page (Investments · Taxes · Liquidity &
cash flow · Estate & legacy · Risk & protection · Ownership & account structure ·
Purpose & family). Never equate the two: the mark keeps five streams at every size,
the model has seven systems, and no site copy should tie the stream count to the
system count.

Full standard: **[`src/drift/web/brand.html`](src/drift/web/brand.html)** (open with `driftwood.css` alongside).

## The rules that do not move

1. **Five streams, always.** The mark holds all five lines at every size, down to
   16px. It is never redrawn with fewer lines, never a three-stream or simplified
   cut, never swapped for a different glyph. One silhouette earns recognition.
2. **45° convergence, squared terminals.** Straight geometry, square caps, miter
   joins. No curves, no rounded corners, no shortened trunk.
3. **Editorial blue `#2C5878` is the mark's only identity colour.** Bright teal
   `#15806A` is reserved for *data* (positive values, links, the recompute pulse)
   and never touches the mark or carries identity.

## The mark (frozen geometry)

`viewBox 6 13 90 74` on a 100-unit grid, single ink via `currentColor` (or `#2c5878`
in the standalone assets):

```
polyline 10,18 24.35,18 62,50   ┐ outer tributaries bend soonest (x=24.35)
polyline 10,34 43.18,34 62,50   │ inner tributaries bend later (x=43.18)
line     10,50        62,50     │ middle tributary + trunk are collinear
polyline 10,66 43.18,66 62,50   │ so coordination builds gradually, not at one node
polyline 10,82 24.35,82 62,50   ┘ stroke-width 3.2 (streams)
line     62,50        90,50       trunk / river — one step heavier, 5.2
```

- **Weights:** stream `3.2` / trunk `5.2` (trunk-units) — stream : void ≈ 1 : 1.
- **Nav cut:** `4.6 / 7.0` at ~22px — the small-size optical weight the site nav uses so the
  mark holds its own beside the wordmark (thin strokes go pale at nav scale).
- **Favicon cut:** heavier `~5.5 / 9`, white on tile, for legibility at ≤ 32px.
- **Convergence:** all five land on `(62,50)`; the trunk runs `(62,50) → (90,50)`.

Canonical files (`src/drift/web/brand/`):

| File | Role |
|---|---|
| `mark.svg` | editorial-blue mark on transparent — the nameplate mark |
| `mark-reversed.svg` | limestone mark for navy / dark grounds |
| `favicon-cut.svg` | heavier cut for ≤ 32px |
| `icon.svg` | editorial-blue tile + white mark |
| `avatar.svg` | editorial-blue disc + white mark, mark at 52% diameter |

Derived, rendered assets: `favicon.svg`, `mask-icon.svg`, `favicon-32.png`,
`apple-touch-icon.png` (avatar disc, 180px). The OG share cards
(`scripts/og_cards.mjs`) carry the same nameplate lockup.

## The three applications

| Application | Ground | Mark | Use |
|---|---|---|---|
| **Nameplate** | limestone `#F1EFE9` | editorial-blue mark + ink `#1E2833` wordmark | site nav, headers, reports, PDFs, email |
| **Favicon** | editorial-blue tile, **zero radius** | white mark (heavier cut) | browser chrome, ≤ 32px |
| **Social avatar** | editorial-blue disc | white mark at 52% diameter | social, app / workspace icon |

The favicon tile and the avatar disc are **both editorial blue** — the blue frame is
the brand's own colour, so the icon reads as Driftwood at a glance rather than as a
generic dark tile, and the disc seats cleanly inside a circular profile crop.

## Lockups

| Lockup | Contents | Use |
|---|---|---|
| **Primary** | mark · hairline · `DRIFTWOOD WEALTH` / `PRIVATE WEALTH ADVISORY` | hero, reports, PDFs, proposals |
| **Secondary** | mark · hairline · `DRIFTWOOD WEALTH` | navigation, headers, email |
| **Micro** | mark · `DRIFTWOOD WEALTH` (no divider) | chrome, dashboard, mobile, footers |
| **Avatar** | mark only (favicon / disc) | favicon, social, app icon |
| **Signature** | `DRIFTWOOD WEALTH` / *Private Wealth Advisory* / Austin, Texas | document colophon — proposals, letters, AWOR, Operating Manual |

Metrics live in `driftwood.css` `:root` as `--logo-*` tokens (gap, mark, rule,
word size, word spacing). Clear-space = the mark's height on every side. Below the
minimum lockup width the lockup falls back to the Avatar; on mobile the nav drops
the divider (Micro).

## Colours & type

- Mark & descriptor: **editorial blue** `--accent-strike` `#2C5878` — identity only.
- Wordmark: **slate-navy ink** `--ink` `#1E2833` (all-caps, tracked, never two-tone).
- Paper: **limestone** `--bg` `#F1EFE9`; reversed ground: **navy** `--navy` `#1A2330`.
- Tint: **soft blue** `#A9C2D6`. Data accent: **bright teal** `--teal2` `#15806A` — data only.
- Wordmark & descriptor set in **Satoshi** (`--sans`), tracked caps. The Signature
  descriptor is the one place the editorial serif (**Erode**) appears, as a colophon.

## Do / Don't

**Do** — keep all five streams down to 16px · keep the mark's height of clear-space
on every side · editorial blue on limestone, white or limestone on navy · favicon
tile and avatar disc both editorial blue · use the heavier favicon cut at ≤ 32px.

**Don't** — reduce the stream count (no three-stream or simplified cut) · colour the
mark anything but editorial blue, or use teal for identity · two-tone the wordmark or
set it anything but tracked caps · curve the streams, shorten the trunk, or round the
terminal · add a box, shadow, gradient, or rounded corner to the mark.

## Status

### Shipped
- [x] KIT 02 mark frozen (aligned confluence, 45°, five streams always)
- [x] Canonical `brand/*.svg` assets + `--logo-*` design tokens in `driftwood.css`
- [x] Secondary lockup wired into the nav across all templates + `statepage.py` (atlas pages)
- [x] Favicon system regenerated: `favicon.svg`, `mask-icon.svg`, `favicon-32.png`, `apple-touch-icon.png` (src + docs)
- [x] OG share cards carry the nameplate lockup (`scripts/og_cards.mjs`)
- [x] Mobile nav → Micro (divider hidden)
- [x] Brand Constitution page `brand.html`

### Follow-ups
- [ ] Primary lockup in the homepage hero / footer brand sign-off
- [ ] Signature colophon on the Operating-System documents (Manual, Registers, AWOR) and proposals
- [ ] Micro lockup in the Advisor Workspace chrome
- [ ] Export `brand.html` to a distributable **Brand Standards** PDF
- [ ] Apply the identity to client PDFs / pitch decks / report templates
