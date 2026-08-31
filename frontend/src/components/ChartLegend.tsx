"use client";

import { useChartTheme } from "@/hooks/useChartTheme";
import { lineColor, lineStyle } from "@/lib/chartTheme";

type Props = {
  symbols: string[];
};

/**
 * Names the line series drawn on the chart. Presentational: it takes the same
 * `selected` array the chart does, in the same order, so the nth swatch here is
 * the nth series there.
 *
 * The swatch colour is inline rather than a Tailwind class because the palette
 * lives in `chartTheme` - the canvas cannot read CSS custom properties, so the
 * legend has to meet it on its own terms.
 */
export function ChartLegend({ symbols }: Props) {
  const theme = useChartTheme();

  return (
    <ul className="flex flex-wrap items-center gap-x-4 gap-y-1.5">
      {symbols.map((symbol, index) => (
        <li key={symbol} className="flex items-center gap-1.5">
          {/* A border rather than a background: a filled block cannot show a
              dash pattern, and the pattern is half of what tells the series
              apart on the canvas. */}
          <span
            aria-hidden
            className="w-5"
            style={{
              borderTopWidth: 2,
              borderTopStyle: lineStyle(index).css,
              borderTopColor: lineColor(index, theme),
            }}
          />
          <span className="font-mono text-xs text-muted-foreground">
            {symbol}
          </span>
        </li>
      ))}
    </ul>
  );
}
