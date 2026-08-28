"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { ChartTypeToggle } from "@/components/ChartTypeToggle";
import { KpiCards } from "@/components/KpiCards";
import { NormaliseSwitch } from "@/components/NormaliseSwitch";
import { PeriodToggle } from "@/components/PeriodToggle";
import { PriceChart } from "@/components/PriceChart";
import { SymbolMultiSelect } from "@/components/SymbolMultiSelect";
import { usePrices } from "@/hooks/usePrices";
import { useSymbols } from "@/hooks/useSymbols";
import { applyPeriod, summarise, type Period } from "@/lib/analytics";
import type { ChartType } from "@/lib/types";

export default function DashboardPage() {
  // The page owns every filter; children below are presentational and fetch
  // nothing of their own.
  const [selected, setSelected] = useState<string[]>([]);
  const [period, setPeriod] = useState<Period>("All");
  const [chartType, setChartType] = useState<ChartType>("line");
  const [normalise, setNormalise] = useState(false);

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

  // /prices returns full history, so the period is a local slice: switching it
  // costs one array pass and no network request.
  const bars = useMemo(
    () => applyPeriod(pricesQuery.data ?? [], period),
    [pricesQuery.data, period],
  );

  const summaries = useMemo(
    () => summarise(bars, selected),
    [bars, selected],
  );

  const error = symbolsQuery.error ?? pricesQuery.error;
  const loading = symbolsQuery.isLoading || pricesQuery.isFetching;

  return (
    <main className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-6 py-10">
      <header className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-tight">TradeRadar</h1>
        <p className="text-sm text-muted-foreground">
          Daily bars from the local store.
        </p>
      </header>

      {/* A top bar rather than a sidebar: the chart is the point of the page
          and a sidebar would spend 300px of its width permanently. */}
      <div className="flex flex-wrap items-center gap-x-6 gap-y-3 rounded-xl border bg-card/50 px-4 py-3">
        <SymbolMultiSelect
          options={symbols}
          selected={selected}
          onChange={setSelected}
        />

        <div className="ml-auto flex flex-wrap items-center gap-x-6 gap-y-3">
          <PeriodToggle value={period} onChange={setPeriod} />
          <ChartTypeToggle value={chartType} onChange={setChartType} />
          {/* Percent-rebased candles would be meaningless, so this control
              only exists for the line chart. */}
          {chartType === "line" && (
            <NormaliseSwitch checked={normalise} onChange={setNormalise} />
          )}
        </div>
      </div>

      <KpiCards summaries={summaries} />

      <section className="rounded-xl border bg-card p-4">
        <div className="mb-3 flex items-baseline justify-between gap-4">
          <h2 className="text-sm font-medium">
            {chartType === "candlestick"
              ? `Candlesticks — ${selected[0] ?? "—"}`
              : normalise
                ? "Percent change"
                : "Closing price"}
          </h2>
          <span className="text-xs text-muted-foreground">
            {chartType === "candlestick" && selected.length > 1
              ? "Showing the first selected symbol only"
              : normalise
                ? "Rebased to 0% at the start of the period"
                : null}
          </span>
        </div>

        <ChartArea
          loading={loading}
          error={error}
          hasSymbols={symbols.length > 0}
          hasSelection={selected.length > 0}
          barCount={bars.length}
        >
          <PriceChart
            bars={bars}
            symbols={selected}
            chartType={chartType}
            normalise={normalise}
          />
        </ChartArea>
      </section>
    </main>
  );
}

type ChartAreaProps = {
  loading: boolean;
  error: Error | null;
  hasSymbols: boolean;
  hasSelection: boolean;
  barCount: number;
  children: React.ReactNode;
};

/** Keeps the empty, loading and error branches out of the page body. */
function ChartArea({
  loading,
  error,
  hasSymbols,
  hasSelection,
  barCount,
  children,
}: ChartAreaProps) {
  let message: string | null = null;

  if (error) {
    message = `Could not reach the API: ${error.message}`;
  } else if (!hasSymbols && !loading) {
    message = "The database is empty. Run `python main.py --output sql` first.";
  } else if (!hasSelection) {
    message = "Pick at least one symbol.";
  } else if (barCount === 0) {
    message = loading ? "Loading…" : "No stored bars fall inside this period.";
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
