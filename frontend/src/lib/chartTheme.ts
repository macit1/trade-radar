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
 */

const AXIS_TEXT = "#8b93a7";
const GRID_LINE = "rgba(148, 163, 184, 0.12)";
const CROSSHAIR_LABEL = "#1f2430";

export const chartOptions: DeepPartial<ChartOptions> = {
  layout: {
    // Transparent so the chart sits on the page surface rather than a box.
    background: { type: ColorType.Solid, color: "transparent" },
    textColor: AXIS_TEXT,
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
      color: AXIS_TEXT,
      width: 1,
      style: LineStyle.Dashed,
      labelBackgroundColor: CROSSHAIR_LABEL,
    },
    horzLine: {
      color: AXIS_TEXT,
      width: 1,
      style: LineStyle.Dashed,
      labelBackgroundColor: CROSSHAIR_LABEL,
    },
  },
};

const UP = "#26a69a";
const DOWN = "#ef5350";

export const candlestickOptions = {
  upColor: UP,
  downColor: DOWN,
  wickUpColor: UP,
  wickDownColor: DOWN,
  borderVisible: false,
};

/** One colour per line series, cycled if more symbols than colours are picked. */
export const LINE_COLORS = [
  "#38bdf8",
  "#f472b6",
  "#a3e635",
  "#fbbf24",
  "#c084fc",
  "#2dd4bf",
];
