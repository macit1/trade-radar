"use client";

import {
  CandlestickSeries,
  LineSeries,
  createChart,
  type IChartApi,
  type ISeriesApi,
  type SeriesType,
  type Time,
} from "lightweight-charts";
import { useEffect, useRef } from "react";

import { LINE_COLORS, candlestickOptions, chartOptions } from "@/lib/chartTheme";
import type { ChartType, PriceBar } from "@/lib/types";

type Props = {
  bars: PriceBar[];
  symbols: string[];
  chartType: ChartType;
};

/**
 * lightweight-charts is imperative: it owns a canvas and mutates it. React
 * wants to re-render. The chart and its series therefore live in refs, never in
 * state, and the work is split across two effects with different dependencies
 * so that a data change never tears down the chart itself.
 */
export function PriceChart({ bars, symbols, chartType }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<SeriesType>[]>([]);

  // Create the chart once. Recreating it whenever data arrives would throw away
  // the viewer's zoom and pan, and leak a chart instance on every render.
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const chart = createChart(container, {
      ...chartOptions,
      width: container.clientWidth,
      height: container.clientHeight,
    });
    chartRef.current = chart;

    const observer = new ResizeObserver(([entry]) => {
      chart.applyOptions({
        width: entry.contentRect.width,
        height: entry.contentRect.height,
      });
    });
    observer.observe(container);

    return () => {
      observer.disconnect();
      chart.remove();
      chartRef.current = null;
      seriesRef.current = [];
    };
  }, []);

  // Rebuild the series when the data, the symbols or the chart type change.
  // Creating a series and filling it are one step on purpose: a separate effect
  // for setData would leave a frame where an empty series is already attached.
  useEffect(() => {
    const chart = chartRef.current;
    if (!chart) return;

    seriesRef.current.forEach((series) => chart.removeSeries(series));
    seriesRef.current = [];

    if (chartType === "candlestick") {
      // Candles from several symbols on one axis are unreadable, so only the
      // first selected symbol is drawn.
      const symbol = symbols[0];
      if (!symbol) return;

      const series = chart.addSeries(CandlestickSeries, candlestickOptions);
      series.setData(
        bars
          .filter(
            (bar) =>
              bar.symbol === symbol &&
              bar.open !== null &&
              bar.high !== null &&
              bar.low !== null &&
              bar.close !== null,
          )
          .map((bar) => ({
            time: bar.date as Time,
            open: bar.open as number,
            high: bar.high as number,
            low: bar.low as number,
            close: bar.close as number,
          })),
      );
      seriesRef.current = [series];
    } else {
      seriesRef.current = symbols.map((symbol, index) => {
        const series = chart.addSeries(LineSeries, {
          color: LINE_COLORS[index % LINE_COLORS.length],
          lineWidth: 2,
          priceLineVisible: false,
          lastValueVisible: false,
        });

        series.setData(
          bars
            .filter((bar) => bar.symbol === symbol && bar.close !== null)
            .map((bar) => ({
              time: bar.date as Time,
              value: bar.close as number,
            })),
        );

        return series;
      });
    }

    chart.timeScale().fitContent();
  }, [bars, symbols, chartType]);

  return <div ref={containerRef} className="h-[440px] w-full" />;
}
