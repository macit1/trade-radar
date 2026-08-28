import type { PriceBar } from "./types";

/**
 * Pure transforms over the /prices response, ported from the Streamlit
 * dashboard's pandas helpers. The API returns full history, so every filter and
 * derived figure below is computed here rather than round-tripping to the
 * server.
 */

/** Trailing window sizes in calendar days. `null` means everything stored. */
export const PERIODS = {
  "1M": 30,
  "6M": 182,
  "1Y": 365,
  All: null,
} as const;

export type Period = keyof typeof PERIODS;

export const PERIOD_KEYS = Object.keys(PERIODS) as Period[];

const DAY_MS = 24 * 60 * 60 * 1000;

/**
 * Keep only bars inside the trailing window, measured from the newest bar in
 * the data rather than from today - the store can be a few days stale and the
 * chart should still show a full window.
 */
export function applyPeriod(bars: PriceBar[], period: Period): PriceBar[] {
  const days = PERIODS[period];
  if (days === null || bars.length === 0) return bars;

  const latest = bars.reduce(
    (newest, bar) => (bar.date > newest ? bar.date : newest),
    bars[0].date,
  );
  const cutoff = new Date(`${latest}T00:00:00Z`).getTime() - days * DAY_MS;

  return bars.filter(
    (bar) => new Date(`${bar.date}T00:00:00Z`).getTime() >= cutoff,
  );
}

export type LinePoint = { time: string; value: number };

/**
 * Closing prices for one symbol.
 *
 * With `normalise`, every series is rebased to 0% at its own first bar in the
 * window. Symbols trade at very different price levels, so an absolute chart
 * shows the gap between them rather than how each one moved.
 */
export function lineSeriesData(
  bars: PriceBar[],
  symbol: string,
  normalise: boolean,
): LinePoint[] {
  const closes = bars
    .filter((bar) => bar.symbol === symbol && bar.close !== null)
    .map((bar) => ({ time: bar.date, value: bar.close as number }));

  if (!normalise || closes.length === 0) return closes;

  const base = closes[0].value;
  if (base === 0) return closes;

  return closes.map((point) => ({
    time: point.time,
    value: (point.value / base) * 100 - 100,
  }));
}

/** OHLC bars for one symbol, dropping any bar with a missing value. */
export function candleSeriesData(bars: PriceBar[], symbol: string) {
  return bars
    .filter(
      (bar) =>
        bar.symbol === symbol &&
        bar.open !== null &&
        bar.high !== null &&
        bar.low !== null &&
        bar.close !== null,
    )
    .map((bar) => ({
      time: bar.date,
      open: bar.open as number,
      high: bar.high as number,
      low: bar.low as number,
      close: bar.close as number,
    }));
}

export type SymbolSummary = {
  symbol: string;
  date: string;
  close: number | null;
  /** Null when the window holds a single bar - there is nothing to compare to. */
  change: number | null;
  changePct: number | null;
  volume: number | null;
  bars: number;
};

/** One row per symbol: last close, move against the previous bar, volume. */
export function summarise(
  bars: PriceBar[],
  symbols: string[],
): SymbolSummary[] {
  return symbols.flatMap((symbol) => {
    const own = bars.filter((bar) => bar.symbol === symbol);
    if (own.length === 0) return [];

    const last = own[own.length - 1];
    const previousClose = own.length > 1 ? own[own.length - 2].close : null;

    const change =
      last.close === null || previousClose === null
        ? null
        : last.close - previousClose;

    const changePct =
      change === null || !previousClose ? null : (change / previousClose) * 100;

    return [
      {
        symbol,
        date: last.date,
        close: last.close,
        change,
        changePct,
        volume: last.volume,
        bars: own.length,
      },
    ];
  });
}
