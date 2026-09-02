"use client";

import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { PERIOD_KEYS, type Period } from "@/lib/analytics";
import { TOGGLE_ITEM } from "@/lib/toggleStyles";

type Props = {
  value: Period;
  onChange: (next: Period) => void;
};

export function PeriodToggle({ value, onChange }: Props) {
  return (
    <ToggleGroup
      variant="outline"
      size="sm"
      value={[value]}
      onValueChange={(next) => {
        // Base UI allows clearing the group; an empty period has no meaning
        // here, so the last choice stands.
        const picked = next[0] as Period | undefined;
        if (picked) onChange(picked);
      }}
    >
      {PERIOD_KEYS.map((period) => (
        <ToggleGroupItem key={period} value={period} className={TOGGLE_ITEM}>
          {period}
        </ToggleGroupItem>
      ))}
    </ToggleGroup>
  );
}
