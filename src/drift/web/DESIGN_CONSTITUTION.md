# The Driftwood Design Constitution

*Frozen July 2026. This is not a style guide — it is the small set of laws the interface obeys.
When you are tempted, a year from now, to add a flourish because it "looks cool," read this first.*

---

## Preamble

**Design exists to make ideas easier to understand, never to compete with them.**

Driftwood sells one thing: a clearer way to see a financial life as a system. Everything the
interface does must serve that comprehension. A prospect's attention is finite; every pixel that
asks "look at me" is attention stolen from the idea. The design's job is to disappear.

## The seven principles

1. **Design exists to make ideas easier to understand, never to compete with them.**
2. **Surfaces behave like paper, not floating software.** Cards, plates, tables, and panels are
   ruled sheets — square corners, a hairline border, no drop shadow pretending they float.
3. **Motion communicates hierarchy, not delight.** A hover answers the cursor quietly; it never
   performs. Nothing bounces, springs, or celebrates. Reduced-motion is always honored.
4. **Typography carries emphasis before color.** Weight, size, and rhythm do the work first;
   color is reserved for identity and wayfinding, not decoration.
5. **Every page teaches exactly one enduring idea.** If a page has two theses, it has none.
6. **Every interaction should feel calm, deliberate, and institutional.**
7. **The interface should disappear behind the operating system it describes.**

## The visual language has a single source of truth

All of it lives in **`driftwood.css` `:root`**, linked last on every page so its tokens cascade
through each page's local palette. Change a token here and the whole site follows. Do not
reintroduce hardcoded values that a token already governs.

| Token | Value | Governs |
|---|---|---|
| `--surface-radius` | `0px` | Every card, plate, table, callout, panel, chart frame. One line squares the whole site. |
| `--surface-border` | `1px solid var(--line)` | The hairline that carries a surface's edge (in place of shadow). |
| `--surface-shadow` | `none` | Surfaces are paper, not floating software. |
| `--transition-standard` | `180ms ease` | The calm default for every hover/state change. |
| `--content-max-width` | `720px` | The content column. |
| `--reading-measure` | `62ch` | Prose line length. |
| `--rfull` | `999px` | Pills, tags, status chips — **a distinct component class that stays round.** |
| `--sans` / `--serif` | Satoshi / Erode | Satoshi carries headings, body, and all UI; Erode is editorial callouts only. |
| Palette | `--bg --ink --line --teal --navy` … | Limestone paper, slate-navy ink, editorial blue for identity/wayfinding. |

**Surfaces are square; pills are round.** This is not an inconsistency — it is a rule. A surface
is a container for content; a pill is a word wearing a badge. They are different object classes and
they read differently on purpose. Circles (avatars, dots) keep `50%` for the same reason.

## The freeze

As of this document, the visual system is **frozen**. That means no more:

- typography debates
- border-radius tweaks
- spacing adjustments
- hover refinements
- animation experiments
- color changes

**The one exception:** a genuine usability problem surfaced by testing real people. Not a
preference, not a "what if," not a fresh eye on a Tuesday — a documented case where the current
design measurably impedes understanding. Fix that. Everything else waits.

The reason for the freeze is not that the design is perfect. It is that **the prospect's brain
should be entirely focused on the paradigm shift** — wealth as a system — and visual churn is
cognitive noise. Consistency is now worth more than any individual improvement.
