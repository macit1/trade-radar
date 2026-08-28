"use client";

import { Switch } from "@/components/ui/switch";

type Props = {
  checked: boolean;
  onChange: (next: boolean) => void;
};

export function NormaliseSwitch({ checked, onChange }: Props) {
  return (
    <label className="flex cursor-pointer items-center gap-2 text-sm text-muted-foreground">
      <Switch checked={checked} onCheckedChange={onChange} />
      Normalise to %
    </label>
  );
}
