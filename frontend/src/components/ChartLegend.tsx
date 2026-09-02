"use client";

import { useChartTheme } from "@/hooks/useChartTheme";
import { lineColor, lineWidth } from "@/lib/chartTheme";

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
          {/* Solid, and as thick as the line it stands for - the canvas
              draws no pattern, so neither does the swatch. */}
          <span
            aria-hidden
            className="w-5 rounded-full"
            style={{
              height: lineWidth(index),
              backgroundColor: lineColor(index, theme),
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
