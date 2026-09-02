"use client";

import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { TOGGLE_ITEM } from "@/lib/toggleStyles";

type Props = {
  /** The symbols currently selected on the page - the only candidates. */
  options: string[];
  value: string | null;
  onChange: (next: string) => void;
};

/**
 * Picks which symbol the candlestick chart draws. Candles from several symbols
 * on one axis are unreadable, so exactly one is charted; without this control
 * that one would silently be whichever symbol happened to be selected first.
 *
 * A segmented control rather than a dropdown: the candidates are the symbols
 * already selected above, so the list is short and worth showing at a glance.
 */
export function CandleSymbolToggle({ options, value, onChange }: Props) {
  return (
    <ToggleGroup
      variant="outline"
      size="sm"
      value={value ? [value] : []}
      onValueChange={(next) => {
        // Base UI allows clearing the group; the chart always needs a symbol,
        // so the last choice stands.
        const picked = next[0];
        if (picked) onChange(picked);
      }}
    >
      {options.map((symbol) => (
        <ToggleGroupItem key={symbol} value={symbol} className={TOGGLE_ITEM}>
          {symbol}
        </ToggleGroupItem>
      ))}
    </ToggleGroup>
  );
}
