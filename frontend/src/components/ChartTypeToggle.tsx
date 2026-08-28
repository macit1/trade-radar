"use client";

import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import type { ChartType } from "@/lib/types";

type Props = {
  value: ChartType;
  onChange: (next: ChartType) => void;
};

export function ChartTypeToggle({ value, onChange }: Props) {
  return (
    <ToggleGroup
      variant="outline"
      value={[value]}
      onValueChange={(next) => {
        // Base UI reports the group's value as an array and allows clearing it;
        // an empty selection would leave no chart to draw, so it is ignored.
        const picked = next[0] as ChartType | undefined;
        if (picked) onChange(picked);
      }}
    >
      <ToggleGroupItem value="line">Line</ToggleGroupItem>
      <ToggleGroupItem value="candlestick">Candlestick</ToggleGroupItem>
    </ToggleGroup>
  );
}
