"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchSymbols } from "@/lib/api";

/** The symbol list changes only when the CLI stores a new ticker. */
export function useSymbols() {
  return useQuery({
    queryKey: ["symbols"],
    queryFn: fetchSymbols,
  });
}
