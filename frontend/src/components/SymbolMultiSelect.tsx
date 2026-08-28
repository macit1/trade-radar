"use client";

import { ChevronsUpDown, X } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

type Props = {
  options: string[];
  selected: string[];
  onChange: (next: string[]) => void;
};

/**
 * shadcn/ui ships no multiselect, so this is the documented composition: a
 * Popover holding a searchable Command list, with the current picks rendered
 * as removable badges beside it.
 */
export function SymbolMultiSelect({ options, selected, onChange }: Props) {
  const toggle = (symbol: string) =>
    onChange(
      selected.includes(symbol)
        ? selected.filter((item) => item !== symbol)
        : [...selected, symbol],
    );

  const label =
    selected.length === 0
      ? "Select symbols"
      : `${selected.length} selected`;

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Popover>
        <PopoverTrigger
          render={<Button variant="outline" className="w-44 justify-between" />}
        >
          {label}
          <ChevronsUpDown className="opacity-50" />
        </PopoverTrigger>

        <PopoverContent className="w-44 p-0" align="start">
          <Command>
            <CommandInput placeholder="Search..." />
            <CommandList>
              <CommandEmpty>No symbol found.</CommandEmpty>
              <CommandGroup>
                {options.map((symbol) => (
                  <CommandItem
                    key={symbol}
                    value={symbol}
                    onSelect={() => toggle(symbol)}
                    // CommandItem renders its own check mark for this attribute.
                    data-checked={selected.includes(symbol)}
                  >
                    {symbol}
                  </CommandItem>
                ))}
              </CommandGroup>
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>

      {selected.map((symbol) => (
        <Badge key={symbol} variant="secondary" className="gap-1 pr-1">
          {symbol}
          <button
            type="button"
            onClick={() => toggle(symbol)}
            aria-label={`Remove ${symbol}`}
            className="rounded-full p-0.5 hover:bg-foreground/10"
          >
            <X className="size-3" />
          </button>
        </Badge>
      ))}
    </div>
  );
}
