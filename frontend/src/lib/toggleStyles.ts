/**
 * Shared look for every segmented control. The active segment is the accent
 * colour, so "what is switched on" reads the same way across the page.
 *
 * Base UI marks the active toggle with `data-pressed`, not `data-checked` -
 * the latter belongs to Switch and silently matches nothing here.
 */
export const TOGGLE_ITEM =
  "font-mono text-xs tracking-wide data-pressed:border-radar/45 " +
  "data-pressed:bg-radar/15 data-pressed:text-radar";
