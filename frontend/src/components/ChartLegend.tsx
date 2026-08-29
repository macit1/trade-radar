"use client";

import { lineColor } from "@/lib/chartTheme";

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
  return (
    <ul className="flex flex-wrap items-center gap-x-4 gap-y-1.5">
      {symbols.map((symbol, index) => (
        <li key={symbol} className="flex items-center gap-1.5">
          <span
            aria-hidden
            className="h-0.5 w-3 rounded-full"
            style={{ backgroundColor: lineColor(index) }}
          />
          <span className="font-mono text-xs text-muted-foreground">
            {symbol}
          </span>
        </li>
      ))}
    </ul>
  );
}
