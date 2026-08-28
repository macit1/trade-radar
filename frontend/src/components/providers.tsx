"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

export function Providers({ children }: { children: React.ReactNode }) {
  // useState, not a module-level client: this keeps one client across
  // re-renders without sharing it between requests during server rendering.
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // The store only changes when the CLI runs, so daily bars stay
            // fresh far longer than a default query would assume.
            staleTime: 5 * 60 * 1000,
            refetchOnWindowFocus: false,
          },
        },
      }),
  );

  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
