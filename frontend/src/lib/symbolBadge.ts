/**
 * Stable per-symbol badge colours.
 *
 * The slot is the symbol's position in the *tracked universe* - every symbol
 * the store knows about, sorted - not its position in whatever the viewer has
 * selected. So AAPL is the same colour whether it is picked alone or fifth in a
 * list of six, which is the whole point: the badge has to be recognisable
 * before you have read it.
 *
 * A hash of the symbol name was the obvious first choice and was measured and
 * rejected: six names into six slots is the birthday problem, and every variant
 * tried (djb2, FNV-1a, both xor-folded) put three of the six tracked symbols on
 * the same colour. Positional assignment is collision-free up to the size of
 * the palette.
 *
 * The trade-off is real and worth knowing: inserting a symbol early in the
 * alphabet shifts the colours of everything after it. That is a rare,
 * config-time event, where a collision would have been permanent and visible
 * every day.
 */

/** Matches the `--badge-N` custom properties defined in globals.css. */
export const BADGE_SLOTS = 6;

export function buildBadgeSlots(symbols: string[]): Record<string, number> {
  return Object.fromEntries(
    [...symbols]
      .sort()
      .map((symbol, index) => [symbol, (index % BADGE_SLOTS) + 1]),
  );
}

/**
 * Two letters, not one. Three of the six tracked symbols start with A - AAPL,
 * AMZN and ASML - so a single initial would give three of them the same label
 * and leave colour as the only thing telling them apart, which is exactly the
 * dependency the rest of this interface avoids.
 */
export function badgeLabel(symbol: string) {
  return symbol.slice(0, 2).toUpperCase();
}
