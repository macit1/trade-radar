/** Mirrors the `PriceBar` model in backend/main.py. */
export type PriceBar = {
  symbol: string;
  /** `YYYY-MM-DD`, which is already a valid lightweight-charts `Time`. */
  date: string;
  /** OHLC and volume are nullable: the API returns null for gaps in the data. */
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume: number | null;
};

export type ChartType = "line" | "candlestick";
