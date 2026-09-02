"use client";

import { Search } from "lucide-react";
import { useId, useMemo, useState } from "react";

import { SymbolBadge } from "@/components/SymbolBadge";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

type Props = {
  options: string[];
  slots: Record<string, number>;
  /** Replaces the selection outright - this is a jump, not an add. */
  onPick: (symbol: string) => void;
};

/**
 * Jump straight to one symbol.
 *
 * The multiselect beside this already has a filter box, so this only earns its
 * place by doing a different job: that one edits a set, this one pivots the
 * whole page onto a single symbol in one keystroke. Picking here replaces the
 * selection rather than extending it, which is why it is a separate control and
 * not a second way into the same popover.
 */
export function TickerSearch({ options, slots, onPick }: Props) {
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const [open, setOpen] = useState(false);
  const listId = useId();

  const matches = useMemo(() => {
    const typed = query.trim().toUpperCase();
    if (!typed) return [];
    // Prefix, not substring: a ticker is read from the front, and "MS" should
    // not surface something that merely contains those letters.
    return options.filter((symbol) => symbol.startsWith(typed));
  }, [options, query]);

  const showList = open && query.trim().length > 0;
  const activeSymbol = matches[active];

  function pick(symbol: string) {
    onPick(symbol);
    setQuery("");
    setOpen(false);
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Escape") {
      setQuery("");
      setOpen(false);
      return;
    }
    if (!showList) return;

    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActive((index) => Math.min(index + 1, matches.length - 1));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActive((index) => Math.max(index - 1, 0));
    } else if (event.key === "Enter" && activeSymbol) {
      event.preventDefault();
      pick(activeSymbol);
    }
  }

  return (
    <div className="relative">
      <Search
        aria-hidden
        className="pointer-events-none absolute top-1/2 left-2 size-3.5 -translate-y-1/2 text-muted-foreground"
      />
      <Input
        role="combobox"
        aria-label="Jump to a symbol"
        aria-expanded={showList}
        aria-controls={showList ? listId : undefined}
        aria-activedescendant={
          showList && activeSymbol ? `${listId}-${activeSymbol}` : undefined
        }
        aria-autocomplete="list"
        placeholder="Jump to…"
        value={query}
        onChange={(event) => {
          setQuery(event.target.value);
          setActive(0);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        onKeyDown={handleKeyDown}
        className="h-9 w-36 pl-7 font-mono text-xs tracking-wide"
      />

      {showList && (
        <ul
          id={listId}
          role="listbox"
          aria-label="Matching symbols"
          // Blur fires before click, which would unmount the row mid-press.
          // Swallowing mousedown keeps focus on the input so the click lands.
          onMouseDown={(event) => event.preventDefault()}
          // z-30 rather than z-20: this now opens over the chart canvas, which
          // paints itself and would otherwise win.
          className="panel absolute top-full right-0 z-30 mt-1 w-44 rounded-md border bg-popover p-1 shadow-sm"
        >
          {matches.length === 0 ? (
            // Said rather than shown as an empty box: nothing matching is a
            // fact about the store, not a spinner that has yet to finish.
            <li className="px-2 py-1.5 font-mono text-xs text-muted-foreground">
              Not tracked.
            </li>
          ) : (
            matches.map((symbol, index) => (
              <li
                key={symbol}
                id={`${listId}-${symbol}`}
                role="option"
                aria-selected={index === active}
                onClick={() => pick(symbol)}
                onMouseEnter={() => setActive(index)}
                className={cn(
                  "flex cursor-pointer items-center gap-2 rounded px-2 py-1.5 font-mono text-xs tracking-wide",
                  index === active && "bg-muted text-foreground",
                )}
              >
                <SymbolBadge symbol={symbol} slot={slots[symbol]} />
                {symbol}
              </li>
            ))
          )}
        </ul>
      )}
    </div>
  );
}
