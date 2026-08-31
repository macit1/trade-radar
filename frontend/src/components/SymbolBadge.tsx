import { badgeLabel } from "@/lib/symbolBadge";
import { cn } from "@/lib/utils";

type Props = {
  symbol: string;
  /** 1-based slot from `buildBadgeSlots`. */
  slot: number | undefined;
  className?: string;
};

/**
 * A two-letter stand-in for a company mark.
 *
 * Deliberately not a real logo: the tracked symbols are live trademarks, and
 * reproducing them on a personal public repo risks implying an association that
 * does not exist. Two letters in a fixed colour give the same at-a-glance
 * recognition with none of that.
 *
 * Always sits beside the symbol's own text, so it is hidden from the
 * accessibility tree - it decorates a label, it is not one.
 */
export function SymbolBadge({ symbol, slot, className }: Props) {
  // An unknown symbol still renders, just in the neutral border colour, rather
  // than throwing away the label.
  const colour = slot ? `var(--badge-${slot})` : "var(--muted-foreground)";

  return (
    <span
      aria-hidden
      className={cn(
        "inline-flex size-6 shrink-0 items-center justify-center rounded-full border font-mono text-[10px] leading-none font-medium tracking-tight",
        className,
      )}
      style={{
        color: colour,
        backgroundColor: `color-mix(in oklab, ${colour} 14%, transparent)`,
        borderColor: `color-mix(in oklab, ${colour} 32%, transparent)`,
      }}
    >
      {badgeLabel(symbol)}
    </span>
  );
}
