"use client";

import { useTheme } from "next-themes";

import type { ChartTheme } from "@/lib/chartTheme";

/**
 * The resolved theme, narrowed to what the chart palette understands.
 *
 * next-themes reports "system" as a *setting* and resolves it separately, and
 * reports nothing at all until it has mounted. Both cases fall back to dark -
 * the design's default - so callers never handle undefined.
 */
export function useChartTheme(): ChartTheme {
  const { resolvedTheme } = useTheme();
  return resolvedTheme === "light" ? "light" : "dark";
}
