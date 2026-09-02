"use client";

import { useState } from "react";

import { badgeLabel } from "@/lib/symbolBadge";
import { logoUrl } from "@/lib/symbolLogo";
import { cn } from "@/lib/utils";

type Props = {
  symbol: string;
  /** 1-based slot from `buildBadgeSlots`. */
  slot: number | undefined;
  className?: string;
};

/**
 * The company's mark, falling back to two letters.
 *
 * The logo is fetched from Brandfetch rather than bundled: the marks are live
 * trademarks and hosting copies of them would be the part that actually causes
 * trouble. They are shown to identify a listing, nothing more - see the note in
 * the README.
 *
 * The letter badge is not a placeholder for a slow image, it is the real
 * fallback: if the request fails, the ticker is unknown, or no client ID is
 * configured, the badge renders lettered and nothing is ever broken or blank.
 *
 * Always sits beside the symbol's own text, so it stays hidden from the
 * accessibility tree - it decorates a label, it is not one.
 */
export function SymbolBadge({ symbol, slot, className }: Props) {
  const [logoFailed, setLogoFailed] = useState(false);

  // An unknown symbol still renders, just in the neutral border colour, rather
  // than throwing away the label.
  const colour = slot ? `var(--badge-${slot})` : "var(--muted-foreground)";
  const source = logoFailed ? null : logoUrl(symbol);

  return (
    <span
      aria-hidden
      className={cn(
        "inline-flex size-6 shrink-0 items-center justify-center overflow-hidden rounded-full border font-mono text-[10px] leading-none font-medium tracking-tight",
        className,
      )}
      style={{
        color: colour,
        // Logos carry their own colours and several of the tracked ones are
        // near-black, which would vanish against the dark theme. A light chip
        // under the mark is the same trick a brokerage app uses, and it keeps
        // the badge identical in both themes.
        backgroundColor: source
          ? "#ffffff"
          : `color-mix(in oklab, ${colour} 14%, transparent)`,
        borderColor: `color-mix(in oklab, ${colour} 32%, transparent)`,
      }}
    >
      {source ? (
        // Brandfetch requires the CDN URL in a plain img tag and forbids
        // proxying it, so next/image - which fetches and re-serves - is not an
        // option here. The directive has to sit on the line directly above the
        // element it silences, hence the split from the reason.
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={source}
          alt=""
          width={48}
          height={48}
          loading="lazy"
          decoding="async"
          onError={() => setLogoFailed(true)}
          className="size-full object-contain p-px"
        />
      ) : (
        badgeLabel(symbol)
      )}
    </span>
  );
}
