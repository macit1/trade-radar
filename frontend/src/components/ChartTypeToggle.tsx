"use client";

import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { TOGGLE_ITEM } from "@/lib/toggleStyles";
import type { ChartType } from "@/lib/types";

type Props = {
  value: ChartType;
  onChange: (next: ChartType) => void;
};

export function ChartTypeToggle({ value, onChange }: Props) {
  return (
    <ToggleGroup
      variant="outline"
      size="sm"
      value={[value]}
      onValueChange={(next) => {
        // Base UI reports the group's value as an array and allows clearing it;
        // an empty selection would leave no chart to draw, so it is ignored.
        const picked = next[0] as ChartType | undefined;
        if (picked) onChange(picked);
      }}
    >
      <ToggleGroupItem value="line" className={TOGGLE_ITEM}>
        Line
      </ToggleGroupItem>
      <ToggleGroupItem value="candlestick" className={TOGGLE_ITEM}>
        Candlestick
      </ToggleGroupItem>
    </ToggleGroup>
  );
}
