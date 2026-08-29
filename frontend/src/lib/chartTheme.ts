import {
  ColorType,
  CrosshairMode,
  LineStyle,
  type ChartOptions,
  type DeepPartial,
} from "lightweight-charts";

/**
 * lightweight-charts draws into a canvas, so Tailwind classes cannot reach
 * inside it. Every visual decision about the chart itself lives here; Tailwind
 * only styles the frame around it.
 *
 * The values below are the literal counterparts of the CSS tokens in
 * globals.css - `--radar`, `--loss`, `--font-jetbrains-mono` - kept in sync by
 * hand because canvas cannot read custom properties.
 */

const RADAR = "#3ed992";
const LOSS = "#f2545b";
const AXIS_TEXT = "#8b93a7";
const GRID_LINE = "rgba(148, 163, 184, 0.10)";
const CROSSHAIR_LABEL = "#16211c";

const MONO_STACK =
  "var(--font-jetbrains-mono), ui-monospace, SFMono-Regular, monospace";

export const chartOptions: DeepPartial<ChartOptions> = {
  layout: {
    // Transparent so the chart sits on the page surface rather than a box.
    background: { type: ColorType.Solid, color: "transparent" },
    textColor: AXIS_TEXT,
    // Axis figures are read alongside the KPI cards, so they use the same face.
    fontFamily: MONO_STACK,
    fontSize: 11,
    attributionLogo: false,
  },
  grid: {
    // A horizontal line helps read a price level. Vertical ones only add noise.
    vertLines: { visible: false },
    horzLines: { color: GRID_LINE },
  },
  rightPriceScale: { borderVisible: false },
  timeScale: { borderVisible: false, rightOffset: 4 },
  crosshair: {
    mode: CrosshairMode.Normal,
    vertLine: {
      color: "rgba(62, 217, 146, 0.45)",
      width: 1,
      style: LineStyle.Dashed,
      labelBackgroundColor: CROSSHAIR_LABEL,
    },
    horzLine: {
      color: "rgba(62, 217, 146, 0.45)",
      width: 1,
      style: LineStyle.Dashed,
      labelBackgroundColor: CROSSHAIR_LABEL,
    },
  },
};

export const candlestickOptions = {
  upColor: RADAR,
  downColor: LOSS,
  wickUpColor: RADAR,
  wickDownColor: LOSS,
  borderVisible: false,
};

/**
 * One colour per line series, cycled if more symbols than colours are picked.
 * The accent leads: with a single symbol selected - the common case - the chart
 * is drawn in the same green as the rest of the interface.
 */
const LINE_COLORS = [
  RADAR,
  "#5ab0ff",
  "#c58cff",
  "#f7b955",
  "#ff7ab8",
  "#4dd8d1",
];

/**
 * Colour of the nth line series. The chart canvas and the legend beside it both
 * go through here: a legend that indexed the palette itself would drift out of
 * step with the canvas the moment either side changed.
 */
export function lineColor(index: number) {
  return LINE_COLORS[index % LINE_COLORS.length];
}
