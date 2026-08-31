"use client";

import { Switch } from "@/components/ui/switch";

type Props = {
  checked: boolean;
  onChange: (next: boolean) => void;
};

export function NormaliseSwitch({ checked, onChange }: Props) {
  return (
    <label className="flex cursor-pointer items-center gap-2 font-mono text-xs tracking-wide text-muted-foreground transition-colors hover:text-foreground">
      <Switch
        checked={checked}
        onCheckedChange={onChange}
        className="data-checked:bg-brand"
      />
      Normalise to %
    </label>
  );
}
