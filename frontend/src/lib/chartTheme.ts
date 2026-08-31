import {
  ColorType,
  CrosshairMode,
  LineStyle,
  type ChartOptions,
  type DeepPartial,
} from "lightweight-charts";

/**
 * lightweight-charts draws into a canvas, so Tailwind classes cannot reach
 * inside it and the `dark` class on <html> means nothing here. Every visual
 * decision about the chart itself lives in this file, and each one is a pair:
 * the value for dark and the value for light, picked by the theme the page
 * resolved. Change a token in globals.css and its twin here has to move with
 * it - canvas cannot read CSS custom properties.
 */

export type ChartTheme = "light" | "dark";

/** The literal counterparts of `--radar` and `--loss` in globals.css. */
const RADAR = { dark: "#3ed992", light: "#167f42" };
const LOSS = { dark: "#f2545b", light: "#c4162f" };

const AXIS_TEXT = { dark: "#8b93a7", light: "#5b6472" };
const GRID_LINE = {
  dark: "rgba(148, 163, 184, 0.10)",
  light: "rgba(71, 85, 105, 0.14)",
};
/** The chip behind a crosshair figure: darker than the page in both themes. */
const CROSSHAIR_LABEL = { dark: "#16211c", light: "#1d3527" };
const CROSSHAIR_LINE = {
  dark: "rgba(62, 217, 146, 0.45)",
  light: "rgba(22, 127, 66, 0.55)",
};

const MONO_STACK =
  "var(--font-jetbrains-mono), ui-monospace, SFMono-Regular, monospace";

export function chartOptions(theme: ChartTheme): DeepPartial<ChartOptions> {
  const crosshairLine = {
    color: CROSSHAIR_LINE[theme],
    width: 1 as const,
    style: LineStyle.Dashed,
    labelBackgroundColor: CROSSHAIR_LABEL[theme],
  };

  return {
    layout: {
      // Transparent so the chart sits on the page surface rather than a box -
      // which also means it follows the theme's background for free.
      background: { type: ColorType.Solid, color: "transparent" },
      textColor: AXIS_TEXT[theme],
      // Axis figures are read alongside the KPI cards, so they use the same face.
      fontFamily: MONO_STACK,
      fontSize: 11,
      attributionLogo: false,
    },
    grid: {
      // A horizontal line helps read a price level. Vertical ones only add noise.
      vertLines: { visible: false },
      horzLines: { color: GRID_LINE[theme] },
    },
    rightPriceScale: { borderVisible: false },
    timeScale: { borderVisible: false, rightOffset: 4 },
    crosshair: {
      mode: CrosshairMode.Normal,
      vertLine: crosshairLine,
      horzLine: crosshairLine,
    },
  };
}

/**
 * Direction is carried by the body fill as well as the hue: an up bar is
 * hollow, a down bar solid. Red and green are the one pair a red-green
 * colourblind viewer cannot separate, and on this chart they are the whole
 * message - so the shape has to say it too. This is the standard hollow-candle
 * convention, not an invention.
 */
export function candlestickOptions(theme: ChartTheme) {
  return {
    upColor: "transparent",
    downColor: LOSS[theme],
    // Borders are what draw a hollow body at all, so unlike the filled version
    // they cannot be switched off.
    borderVisible: true,
    borderUpColor: RADAR[theme],
    borderDownColor: LOSS[theme],
    wickUpColor: RADAR[theme],
    wickDownColor: LOSS[theme],
  };
}

/**
 * One colour per line series, cycled if more symbols than colours are picked.
 * The accent leads: with a single symbol selected - the common case - the chart
 * is drawn in the same green as the rest of the interface.
 *
 * The light row is not the dark row darkened by eye; every entry clears 4.5:1
 * against white, where the dark row sits between 1.7:1 and 2.5:1 and would
 * read as pastel noise.
 */
const LINE_COLORS: Record<ChartTheme, string[]> = {
  dark: [RADAR.dark, "#5ab0ff", "#c58cff", "#f7b955", "#ff7ab8", "#4dd8d1"],
  light: [RADAR.light, "#1a6fd4", "#7b3fd1", "#a35c00", "#c02a72", "#0f7a75"],
};

/**
 * Colour of the nth line series. The chart canvas and the legend beside it both
 * go through here: a legend that indexed the palette itself would drift out of
 * step with the canvas the moment either side changed.
 */
export function lineColor(index: number, theme: ChartTheme) {
  const palette = LINE_COLORS[theme];
  return palette[index % palette.length];
}

/**
 * Dash pattern of the nth line series, in both dialects at once: the enum the
 * canvas takes and the CSS keyword the legend swatch takes. They are one entry
 * rather than two lookups so the swatch cannot claim a pattern the line does
 * not draw.
 *
 * Hue alone is not enough to tell six series apart - it fails outright for a
 * colourblind viewer, and it fails for everyone once a printout or a screenshot
 * loses the colour. The pattern is the second channel.
 */
const LINE_STYLES = [
  { canvas: LineStyle.Solid, css: "solid" },
  { canvas: LineStyle.Dashed, css: "dashed" },
  { canvas: LineStyle.Dotted, css: "dotted" },
] as const;

export function lineStyle(index: number) {
  return LINE_STYLES[index % LINE_STYLES.length];
}
