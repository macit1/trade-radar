# Current UI — record of what exists before the redesign

Captured 2026-08-31 from a running instance (backend on :8000, six symbols,
753 daily bars each). This file is a **record, not a rule**: the redesign is not
bound by anything here. It exists so nothing has to be rediscovered by reading
diffs later, and so the parts that genuinely work are visible when the new
direction is chosen.

## Shape

One page, one column, `max-w-6xl`, top to bottom:

1. Header — radar mark + "TRADERADAR" wordmark + one line of subtext
2. Filter bar — symbol multiselect, line/candlestick toggle, normalise switch, theme toggle
3. KPI cards — one per selected symbol, 4-up grid
4. Chart panel — heading, period toggle, candle symbol picker, legend, canvas
5. Summary table — "Latest bar", one row per symbol, seven columns

No sidebar (deliberate: it would spend 300px permanently on a page whose point
is the chart). No navigation — there is only one view.

## Visual identity (being retired)

- **Accent:** phosphor green `--radar`, defined twice in `globals.css`
  (`:root` light, `.dark`) and mirrored by hand in `lib/chartTheme.ts`.
  Light `oklch(0.525 0.13 152)`, dark `oklch(0.8 0.155 152)`.
- **Loss colour:** `--loss` red, same three-place arrangement.
- **Fonts:** Inter (prose), JetBrains Mono (all figures), Chakra Petch
  (wordmark only), all self-hosted through `next/font`.
- **Panel treatment:** `.panel` — accent-tinted hairline border, a faint
  top-to-bottom accent wash, and a lit 1px top edge via `::before`.
- **The one animation:** `.radar-sweep`, a line orbiting the logo mark, 4s linear.

## What works and is worth carrying over regardless of style

These are behaviours, not decoration — they cost real effort to get right:

- **`next/font` self-hosting.** No render-blocking call to fonts.googleapis.com,
  no FOIT, no layout shift. Whatever the new faces are, load them this way.
- **Tabular figures everywhere a number is shown.** Prices and volumes do not
  jitter as they change.
- **Light and dark are separately measured, not inverted.** The light accent is
  a different colour from the dark one because the dark one reads 1.8:1 on white.
- **Canvas colours live in one file** (`lib/chartTheme.ts`) and the legend reads
  from the same functions the chart does, so the two cannot drift apart.
- **Series carry meaning without colour** — line dash patterns cycle
  solid/dashed/dotted; rising candles are hollow, falling candles filled.
- **The chart caps at 500 candles and says so** rather than silently trimming.
- **Filtering is client-side.** Period, normalise and chart type recompute
  locally from one cached fetch; toggling costs no network.
- **The chart is created once.** Theme changes go through `applyOptions`, so a
  toggle never throws away the viewer's zoom and pan.

## Verified state at capture time

- Light theme: page `lab(98.14%)` slate-50, cards `lab(100%)` white — surfaces
  separate without relying on the border.
- Muted text `lab(35.56%)`, 7.4:1 on the page ground.
- Legend swatches confirmed rendering solid / dashed / dotted / solid.
- Candle bodies confirmed hollow on rising bars, filled on falling bars.
- Trim caption confirmed: "Showing the latest 500 of 753 bars."
