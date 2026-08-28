"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchPrices } from "@/lib/api";

/**
 * Bars for the given symbols. The key is sorted so that picking A then B and
 * picking B then A hit the same cache entry.
 */
export function usePrices(symbols: string[]) {
  const key = [...symbols].sort();

  return useQuery({
    queryKey: ["prices", key],
    queryFn: () => fetchPrices(key),
    enabled: key.length > 0,
  });
}
