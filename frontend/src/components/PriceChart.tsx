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

import { candleSeriesData, lineSeriesData } from "@/lib/analytics";
import { candlestickOptions, chartOptions, lineColor } from "@/lib/chartTheme";
import type { ChartType, PriceBar } from "@/lib/types";

type Props = {
  bars: PriceBar[];
  symbols: string[];
  chartType: ChartType;
  normalise: boolean;
  /** Which symbol the candlestick chart draws; ignored by the line chart. */
  candleSymbol: string | null;
};

/**
 * lightweight-charts is imperative: it owns a canvas and mutates it. React
 * wants to re-render. The chart and its series therefore live in refs, never in
 * state, and the work is split across two effects with different dependencies
 * so that a data change never tears down the chart itself.
 */
export function PriceChart({
  bars,
  symbols,
  chartType,
  normalise,
  candleSymbol,
}: Props) {
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

  // Rebuild the series when the data, symbols, chart type or scaling change.
  // Creating a series and filling it are one step on purpose: a separate effect
  // for setData would leave a frame where an empty series is already attached.
  useEffect(() => {
    const chart = chartRef.current;
    if (!chart) return;

    seriesRef.current.forEach((series) => chart.removeSeries(series));
    seriesRef.current = [];

    if (chartType === "candlestick") {
      // Candles from several symbols on one axis are unreadable, so exactly one
      // symbol is drawn - the one the page's picker resolved.
      if (!candleSymbol) return;

      const series = chart.addSeries(CandlestickSeries, candlestickOptions);
      series.setData(
        candleSeriesData(bars, candleSymbol).map((bar) => ({
          ...bar,
          time: bar.time as Time,
        })),
      );
      seriesRef.current = [series];
    } else {
      seriesRef.current = symbols.map((symbol, index) => {
        const series = chart.addSeries(LineSeries, {
          color: lineColor(index),
          lineWidth: 2,
          priceLineVisible: false,
          lastValueVisible: false,
          // Normalised values are percentages, so the axis has to say so.
          priceFormat: normalise
            ? { type: "percent" }
            : { type: "price", precision: 2, minMove: 0.01 },
        });

        series.setData(
          lineSeriesData(bars, symbol, normalise).map((point) => ({
            ...point,
            time: point.time as Time,
          })),
        );

        return series;
      });
    }

    chart.timeScale().fitContent();
  }, [bars, symbols, chartType, normalise, candleSymbol]);

  return <div ref={containerRef} className="h-[440px] w-full" />;
}
