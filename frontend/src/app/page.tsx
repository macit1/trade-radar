"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { ChartTypeToggle } from "@/components/ChartTypeToggle";
import { PriceChart } from "@/components/PriceChart";
import { SymbolMultiSelect } from "@/components/SymbolMultiSelect";
import { usePrices } from "@/hooks/usePrices";
import { useSymbols } from "@/hooks/useSymbols";
import type { ChartType } from "@/lib/types";

export default function DashboardPage() {
  // The page owns the filter state; every child below is presentational and
  // fetches nothing of its own.
  const [selected, setSelected] = useState<string[]>([]);
  const [chartType, setChartType] = useState<ChartType>("line");

  const symbolsQuery = useSymbols();
  const pricesQuery = usePrices(selected);

  // Memoised so the fallback [] is not a fresh array on every render, which
  // would re-run the preselect effect below for no reason.
  const symbols = useMemo(() => symbolsQuery.data ?? [], [symbolsQuery.data]);

  // Preselect the first symbol so the page shows a chart on arrival, but only
  // once - after that the selection belongs to the viewer.
  const preselected = useRef(false);
  useEffect(() => {
    if (!preselected.current && symbols.length > 0) {
      preselected.current = true;
      setSelected([symbols[0]]);
    }
  }, [symbols]);

  return (
    <main className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 py-10">
      <header className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-tight">TradeRadar</h1>
        <p className="text-sm text-muted-foreground">
          Daily bars from the local store.
        </p>
      </header>

      <div className="flex flex-wrap items-center justify-between gap-4">
        <SymbolMultiSelect
          options={symbols}
          selected={selected}
          onChange={setSelected}
        />
        <ChartTypeToggle value={chartType} onChange={setChartType} />
      </div>

      <section className="rounded-xl border bg-card p-4">
        <div className="mb-3 flex items-baseline justify-between">
          <h2 className="text-sm font-medium">
            {chartType === "candlestick"
              ? `Candlesticks — ${selected[0] ?? "—"}`
              : "Closing price"}
          </h2>
          {chartType === "candlestick" && selected.length > 1 && (
            <span className="text-xs text-muted-foreground">
              Showing the first selected symbol only
            </span>
          )}
        </div>

        <ChartArea
          isLoading={symbolsQuery.isLoading || pricesQuery.isFetching}
          error={symbolsQuery.error ?? pricesQuery.error}
          hasSymbols={symbols.length > 0}
          hasSelection={selected.length > 0}
          barCount={pricesQuery.data?.length ?? 0}
        >
          <PriceChart
            bars={pricesQuery.data ?? []}
            symbols={selected}
            chartType={chartType}
          />
        </ChartArea>
      </section>
    </main>
  );
}

type ChartAreaProps = {
  isLoading: boolean;
  error: Error | null;
  hasSymbols: boolean;
  hasSelection: boolean;
  barCount: number;
  children: React.ReactNode;
};

/** Keeps the empty, loading and error branches out of the page body. */
function ChartArea({
  isLoading,
  error,
  hasSymbols,
  hasSelection,
  barCount,
  children,
}: ChartAreaProps) {
  let message: string | null = null;

  if (error) {
    message = `Could not reach the API: ${error.message}`;
  } else if (!hasSymbols && !isLoading) {
    message = "The database is empty. Run `python main.py --output sql` first.";
  } else if (!hasSelection) {
    message = "Pick at least one symbol.";
  } else if (barCount === 0 && isLoading) {
    message = "Loading…";
  }

  if (message) {
    return (
      <div className="flex h-[440px] items-center justify-center text-sm text-muted-foreground">
        {message}
      </div>
    );
  }

  return <>{children}</>;
}
