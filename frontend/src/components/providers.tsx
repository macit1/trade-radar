"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "next-themes";
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

  return (
    <QueryClientProvider client={client}>
      {/*
       * defaultTheme="system" is what the brief asks for read literally: with
       * nothing stored, the OS preference decides the first paint - light if
       * the machine is light, dark otherwise. The toggle then writes an
       * explicit "light" or "dark" to localStorage, which outranks the OS from
       * then on.
       */}
      <ThemeProvider
        attribute="class"
        defaultTheme="system"
        enableSystem
        disableTransitionOnChange
      >
        {children}
      </ThemeProvider>
    </QueryClientProvider>
  );
}
