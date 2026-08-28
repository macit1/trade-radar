"use client";

import { ChevronDown, X } from "lucide-react";

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
import { cn } from "@/lib/utils";

type Props = {
  options: string[];
  selected: string[];
  onChange: (next: string[]) => void;
};

/**
 * shadcn/ui ships no multiselect, so this is the documented composition: a
 * Popover holding a searchable Command list. Picks appear as removable chips in
 * the accent colour, which is how a symbol reads as "tracked" everywhere else
 * on the page.
 */
export function SymbolMultiSelect({ options, selected, onChange }: Props) {
  const toggle = (symbol: string) =>
    onChange(
      selected.includes(symbol)
        ? selected.filter((item) => item !== symbol)
        : [...selected, symbol],
    );

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Popover>
        <PopoverTrigger
          render={
            <Button
              variant="outline"
              className="group h-9 gap-2 border-radar/25 bg-radar/5 font-mono text-xs tracking-wide hover:border-radar/40 hover:bg-radar/10"
            />
          }
        >
          <span className="size-1.5 rounded-full bg-radar" />
          Symbols
          <span className="text-muted-foreground">{selected.length}</span>
          <ChevronDown className="size-3.5 opacity-60 transition-transform group-data-[popup-open]:rotate-180" />
        </PopoverTrigger>

        <PopoverContent className="panel w-52 p-0" align="start">
          <Command>
            <CommandInput placeholder="Filter symbols" />
            <CommandList>
              <CommandEmpty>No symbol matches.</CommandEmpty>
              <CommandGroup>
                {options.map((symbol) => {
                  const picked = selected.includes(symbol);

                  return (
                    <CommandItem
                      key={symbol}
                      value={symbol}
                      onSelect={() => toggle(symbol)}
                      data-checked={picked}
                      className={cn(
                        "font-mono text-xs tracking-wide",
                        picked && "text-radar",
                      )}
                    >
                      <span
                        className={cn(
                          "size-1.5 rounded-full",
                          picked ? "bg-radar" : "bg-muted-foreground/40",
                        )}
                      />
                      {symbol}
                    </CommandItem>
                  );
                })}
              </CommandGroup>
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>

      {selected.map((symbol) => (
        <span
          key={symbol}
          className="inline-flex h-7 items-center gap-1.5 rounded-md border border-radar/25 bg-radar/10 pr-1 pl-2 font-mono text-xs tracking-wide text-radar"
        >
          {symbol}
          <button
            type="button"
            onClick={() => toggle(symbol)}
            aria-label={`Stop tracking ${symbol}`}
            className="rounded p-0.5 text-radar/70 transition-colors hover:bg-radar/15 hover:text-radar focus-visible:ring-2 focus-visible:ring-radar/50 focus-visible:outline-none"
          >
            <X className="size-3" />
          </button>
        </span>
      ))}
    </div>
  );
}
