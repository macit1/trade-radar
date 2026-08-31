# TradeRadar — Design System (Master)

> **LOGIC:** When building a specific page, first check
> `design-system/traderadar/pages/[page-name].md`. If that file exists, its
> rules **override** this Master file. If not, follow the rules below.

**Project:** TradeRadar — a daily OHLCV market monitor. Six symbols, three years
of daily bars, one view. No orders, no brokerage, no advice: it watches, it does
not act.
**Generated:** 2026-08-31 · replaces the first draft entirely
**Category:** Analytics Dashboard (dark-first)
**Design Dials:** Variance 7/10 · Motion 4/10 · Density 8/10

## Where this came from

Composed from three `ui-ux-pro-max` queries, because no single one answered it:

| Query | Took |
|---|---|
| `"fintech crypto trading terminal dark HUD" --design-system` | palette, structural style, dials |
| `"HUD sci-fi FUI wireframe technical" --domain style` | the radar character layer |
| `"technical monospace precise data terminal" --domain typography` | the type pairing |

**Rejected on the way:** a `"radar monitoring scanning surveillance"` query
returned **Organic Biophilic** — wellness, eco, rounded, green. The word "radar"
without a product type reads as nature. Discarded outright.

---

## 1. The idea

**The radar is structural, not chromatic.** The previous identity said "radar"
by being phosphor green. That is retired. This one says it by behaving like an
instrument: hairline rules, bracket markers at the corners of live regions,
monospace readouts, a sweep that runs only where something is actually being
watched.

A radar screen is mostly empty and very precise. That is the target: dense with
data, sparse with decoration.

---

## 2. Colour

Dark is the primary mode. Light is a supported second mode, measured
separately — never the dark values inverted.

### Dark (primary)

| Role | Hex | Notes |
|------|-----|-------|
| Background | `#0F172A` | deep navy, not black — black kills the hairlines |
| Card | `#222735` | |
| Muted surface | `#272F42` | |
| Border | `#334155` | |
| Foreground | `#F8FAFC` | |
| Muted foreground | `#94A3B8` | |
| **Brand / primary** | `#F59E0B` | amber. The instrument-panel colour |
| Secondary | `#FBBF24` | |
| Accent | `#8B5CF6` | violet, sparingly — one CTA per view at most |
| Destructive | `#EF4444` | |

*Palette note from the source data: "Gold trust + purple tech".*

### Gain / loss are a separate pair

Brand amber must never mean "up". Direction gets its own semantic tokens, and
teal beats green here: **teal vs red separates for a red-green colourblind
viewer where green vs red does not.**

| Token | Dark | Light |
|---|---|---|
| `--gain` | `#2DD4BF` | measure a ≥4.5:1 variant before use |
| `--loss` | `#EF4444` | measure a ≥4.5:1 variant before use |

Colour is still never the only channel — see §6.

### Forbidden

- **The old phosphor green `--radar` / `oklch(… 152)` hues.** Retired. Not
  "toned down", gone.
- Neon-on-black glow. The HUD source style is `accessibility: risk:high` and
  `performance: drivers:animation,blur`; its palette is borrowed for *geometry
  only*.
- AI purple/pink gradients (named anti-pattern in the source data).

---

## 3. Typography

| Role | Face | Why |
|---|---|---|
| Display / headings | **Exo** | squared, technical, slightly futurist — the instrument character without a novelty font |
| Body & UI | **Roboto Mono** | |
| Figures | **Roboto Mono**, `tabular-nums` | |

Source mood: *science, technology, research, data, futuristic, precise*.

**The old trio — Inter / JetBrains Mono / Chakra Petch — is retired.**

**Load them with `next/font`, not `@import url(fonts.googleapis.com)`.** The
skill's generated CSS import is a regression here: it is render-blocking, causes
FOIT and layout shift, and contradicts the skill's own `font-loading` and
`third-party-scripts` rules. Self-host. This is not negotiable regardless of
which faces are chosen.

`tabular-nums` on every price, change and volume. Proportional digits make the
table jitter as values update.

---

## 4. Structure

Base style: **Minimalism & Swiss Style** — grid-based, high contrast,
functional, generous with white space *between* groups and tight *within* them.

Density 8/10 spacing scale: **2 / 4 / 8 / 12 / 16 / 24 / 32px**.

- Grid, not one centred column. At ≥1024px the KPI row and the summary table
  should be able to sit beside the chart rather than stacking below it.
- No sidebar. There is one view; a sidebar would spend 300px permanently.
- One primary action per view.

**Discard the returned page pattern.** The `--design-system` run returned
"Trust & Authority + Conversion" (hero, proof logos, contact sales). That is a
marketing landing page. TradeRadar is a single-view dashboard.

---

## 5. The radar character layer

Borrowed from HUD / Sci-Fi FUI — **geometry and motion only, no neon, no glow**:

- **1px hairlines.** Rules and dividers at 1px, low contrast, doing the work
  that shadows would do elsewhere.
- **Bracket markers.** Corner brackets on the live chart region, not on every
  card — they mark what is being watched.
- **Monospace readouts** with unit labels, aligned in columns.
- **A sweep.** One, and only where something is actually live. The old logo
  sweep is the right instinct; keep exactly one instance of it.
- **Ticker/scan motion is opt-in**, never ambient.

Everything here is decorative and must degrade to nothing under
`prefers-reduced-motion` without loss of meaning.

---

## 6. Rules that survive the redesign

These are behaviours, not decoration. The redesign does not get to drop them:

1. **Direction never depends on hue alone.** Line series cycle
   solid / dashed / dotted; rising candles are hollow, falling candles filled.
2. **Canvas colour lives in one file.** `lightweight-charts` draws into a canvas
   and cannot read CSS custom properties, so every token used by the chart is
   mirrored in `lib/chartTheme.ts` — and the legend reads the *same functions*
   the chart does, so the two cannot drift.
3. **Light and dark are measured separately.** Every foreground/background pair
   ≥4.5:1 in both modes, checked, not eyeballed.
4. **Max 500 candles, and say so** when trimming. Max 6 line series.
5. **Client-side filtering.** Period, normalise and chart type recompute from
   one cached fetch. No network on toggle.
6. **The chart is created once.** Theme changes go through `applyOptions` so a
   toggle never discards the viewer's zoom and pan.
7. **`prefers-reduced-motion` covers everything**, not one named animation.

## 7. Motion

Reject the generated `back.out(1.4)` stagger preset. The skill's own note says
the overshoot "reads as sloppy on informational UI" — and this is entirely
informational UI.

Fade/translate, 150–300ms, one shared easing token. Exit ~60–70% of enter.

## 8. Anti-patterns

- Generic design · ignored accessibility · AI purple/pink gradients *(named in
  the source data)*
- Emoji as icons — SVG only, one family, consistent stroke width
- Decorative shadows on data surfaces
- Any colour-only signal

## 9. Checklist

- [ ] No trace of the retired green
- [ ] Fonts self-hosted via `next/font`
- [ ] `tabular-nums` on every figure
- [ ] Text ≥4.5:1 in **both** modes, measured
- [ ] Focus rings visible on every control
- [ ] `prefers-reduced-motion` honoured globally
- [ ] Responsive at 375 / 768 / 1024 / 1440
- [ ] Chart readable in greyscale

---

*What the interface looks like today, before any of this lands, is recorded in
[`CURRENT-UI.md`](./CURRENT-UI.md). That file is a record, not a constraint.*
