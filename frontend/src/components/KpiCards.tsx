"use client";

import { TrendingDown, TrendingUp } from "lucide-react";

import { Card } from "@/components/ui/card";
import type { SymbolSummary } from "@/lib/analytics";
import {
  formatChange,
  formatPercent,
  formatPrice,
  formatVolume,
} from "@/lib/format";
import { cn } from "@/lib/utils";

export function KpiCards({ summaries }: { summaries: SymbolSummary[] }) {
  if (summaries.length === 0) return null;

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {summaries.map((summary) => (
        <KpiCard key={summary.symbol} summary={summary} />
      ))}
    </div>
  );
}

function KpiCard({ summary }: { summary: SymbolSummary }) {
  const { change, changePct } = summary;
  const up = change !== null && change >= 0;
  const Icon = up ? TrendingUp : TrendingDown;

  return (
    <Card className="panel gap-0 p-4">
      <div className="flex items-baseline justify-between">
        <span className="font-mono text-sm font-medium tracking-wide">
          {summary.symbol}
        </span>
        <span className="font-mono text-xs text-muted-foreground">
          {summary.date}
        </span>
      </div>

      <div className="mt-2 font-mono text-2xl font-semibold tabular-nums">
        {formatPrice(summary.close)}
      </div>

      <div
        className={cn(
          "mt-1 flex items-center gap-1.5 font-mono text-sm tabular-nums",
          // A missing change means a single-bar window, not a flat day.
          change === null ? "text-muted-foreground" : up ? "text-radar" : "text-loss",
        )}
      >
        {change !== null && <Icon className="size-3.5" />}
        <span>{formatChange(change)}</span>
        <span className="opacity-70">({formatPercent(changePct)})</span>
      </div>

      <div className="mt-3 flex items-center justify-between font-mono text-xs text-muted-foreground">
        <span>Vol {formatVolume(summary.volume)}</span>
        <span>{summary.bars} bars</span>
      </div>
    </Card>
  );
}
