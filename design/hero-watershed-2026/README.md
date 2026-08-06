# Hero Watershed — three concept prototypes (2026-08)

Three self-contained homepage-hero treatments built on one muted abstract Mississippi watershed.
**Concept prototypes, not production templates.** Nothing here is wired into `src/drift/web/` or
`docs/`, and nothing here should be deployed without the review gates at the bottom.

```
variant-1-basin.html            The full system — 24 capillaries, four majors, one stem
variant-2-bdote.html            Ultra-minimal — two waters converge, one channel leaves
variant-3-panch-prayag.html     Five congruent arrivals lock into one dominant channel
build_paths.py                  Generates every path, and every animation delay
inline-fonts.py                 Inlines Satoshi + Erode as data URIs
```

Each HTML file is a complete, zero-dependency block: inline SVG, CSS-only motion, no script of
any kind, fonts embedded. Open one in a browser, or lift `<header class="hero">` and the `<style>`
block straight into a page. The `<section class="under">` at the foot is test furniture (a caption
plus scroll room to exercise the parallax) — delete it when lifting.

**Copy is identical across all three on purpose.** The only variable is the drawing, so the three
can be judged against each other rather than against three different headlines.

## The geometry is generated

The first pass was hand-placed control points and it produced a blob — smooth, plausible, not
recognisably a watershed. So `build_paths.py` owns the drawing:

1. Each feature is a short list of `(lat, lon)` landmarks. Deliberately short — twelve points for
   the Missouri, eight for the Ohio. Simplification happens in the landmark list, where it can be
   argued about, not afterwards as jitter smoothed out of a trace.
2. One equirectangular projection, latitude scale held at 1.31× longitude (the true ratio at 40°N)
   so the basin is not silently stretched. The basin's own bbox is fitted to the canvas — no
   coastline is drawn, so nothing outside the watershed reserves space.
3. **Centripetal** Catmull-Rom (α = 0.5) converted exactly to cubic beziers — C1-continuous by
   construction, passing through every landmark. Uniform Catmull-Rom was tried first and overshot:
   it put a loop in the Missouri's bend above Great Falls and threw a hook past the delta.

```bash
python3 design/hero-watershed-2026/build_paths.py            # print all path data
python3 design/hero-watershed-2026/build_paths.py --inject   # write it into the three variants
python3 design/hero-watershed-2026/inline-fonts.py           # re-embed the woff2 faces
```

`--inject` rewrites only the region between the `GEOM:BEGIN` / `GEOM:END` markers. Everything
outside them — the prose, the CSS — is safe to hand-edit. **Do not hand-edit a `d` attribute.**

## Specification as built

| | |
|---|---|
| Ground | limestone `#f1efe9`, and nothing else — single visual world, no dark theme |
| Watershed fill | slate `#6c7f92` at 10% (8% in Variant II), fill only, no outline |
| Resting vectors | `#4a86b8`, **0.85px**, opacity 0.9, `stroke-linecap="round"` |
| Stem at rest | editorial blue `#2c5878`, 1.7px |
| Draw | 12s continuous, linear, infinite, `stroke-dasharray`/`dashoffset`, outer → stem |
| Hover hierarchy | outer thins to 0.5px / 0.26 → majors 1.2px full opacity → stem 3.0px + blue drop-shadow pulse |
| Confluence nodes | one soft radial pulse per cycle, then nothing — no residual dot |
| Ambient breath | stem only, 12s, locked to the draw clock so the two never beat |
| Mouse proximity | nearest vector takes editorial blue and releases a travelling glow |
| Scroll | 4-unit (~3px) parallax on the silhouette only, CSS scroll-driven timeline |

0.85px is a *screen* measurement, so `vector-effect="non-scaling-stroke"` takes the stroke out of
the viewBox scale entirely — the hairline is exactly 0.85px at any hero width.

**Zero labels, borders, city dots, topography, graticule, coastline, or north arrow.** The
confluence markers are transient by construction: a node exists only during its pulse, so the
drawing can never acquire a city dot.

### On the 12s draw

The network stays drawn; what moves is the front. Each vector carries a second copy of itself
(`.trace`) with `stroke-dasharray: .16 .84` over `pathLength="1"` and `stroke-dashoffset` running
1 → 0. The dash period equals the path length, so exactly one lit segment is on a vector at any
instant and it re-enters at the headwater as it leaves at the mouth — no seam, no reset.

The first implementation animated the visible line itself (`dasharray "1 1"`, offset 2 → 0), the
textbook continuous draw. It satisfies every word of the spec and leaves each vector absent for
half of every cycle; sampled at t=11.5s, Variant III was very nearly blank. A hero cannot be empty
a third of the time it is on screen. Same technique, same 12s linear infinite dashoffset, without
ever emptying the plate.

Phases are emitted per path as `--t`, always negative — a negative delay *advances* a vector in
the cycle rather than postponing it, so nothing waits for its first turn.

### On Variant III's balance

All five arrivals are **one curve**. A single template in a local frame (u upstream, v sideways) is
placed five times, rotated into each node's tangent frame and mirrored onto the alternate bank —
same length, same curvature, same 36.9° approach. Each carries one feeder, the same template at
half size. Measured in the browser: five tributaries, identical arc length; five confluence pulses
at 2.68 / 4.00 / 5.33 / 6.67 / 8.01s — equal intervals to within 0.02s, because the nodes are
equally spaced along the channel and the front moves at constant velocity. Equal geometry, equal
time; the sequence is the drawing's, not a set of numbers chosen to look even.

Its channel is **constructed**, not geographic — the one place the three variants part company.
Hanging the five on the real Mississippi was tried and abandoned: the real channel turns hard
between the Illinois and the Arkansas, and rotating the template into those swinging tangent frames
threw the west-bank arrivals across one another. It is still pinned at both ends to the real
drawing — Itasca's projected position to the projected delta, inside the real silhouette.

### On Variant II and the literal Bdóte

Bdóte is the Minnesota meeting the Mississippi at Fort Snelling, and that is where the variant
started. At hero scale it fails: the whole Minnesota is ~110 units long here and its bend at
Mankato reads as a kink, in the one variant whose entire subject is two legible waters. So it draws
the Bdóte *figure* at the basin's own great confluence — the upper Mississippi and the Missouri,
above St Louis. `MINNESOTA` is still generated, and is still right for a folio spread or a print.

## Before any of this goes near the live site

Two things need a decision that is not a design decision:

1. **The homepage hero already holds the house mark.** The heron replaced *a generic hydrographic
   plate* in exactly this slot on 2026-08-03, on the finding that the plate was "page furniture —
   atmosphere with nothing to say" (`OPERATIONS.md`). A watershed drawing is closer to what was
   removed than to what replaced it. These three are not drop-in additions to `hub.html`; they are
   candidates to be judged *against* the heron for that slot, or for a different slot entirely.
2. **The motion doctrine for that slot is explicit: "permanent, not animated" — no loop, no scroll
   replay, no drift, no breathing.** Every variant here loops on 12s by design. That is a
   deliberate departure, requested, and it should be signed off as a change to the doctrine rather
   than slipped in under it.

Both are governance calls, not taste calls. `tests/test_drift_heron.py` guards the current rule.
