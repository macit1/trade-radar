"use client";

import { Sparkline } from "@/components/Sparkline";
import { SymbolBadge } from "@/components/SymbolBadge";
import type { SymbolSummary } from "@/lib/analytics";
import {
  formatChange,
  formatPercent,
  formatPrice,
  formatVolume,
} from "@/lib/format";
import { cn } from "@/lib/utils";

/**
 * The latest bar of every selected symbol, one row each.
 *
 * It reads the same `summarise()` output the KPI cards do - the cards are the
 * glanceable view of one symbol, this is the comparable view across all of
 * them, where the figures line up in a column instead of across cards.
 */
type Props = {
  summaries: SymbolSummary[];
  slots: Record<string, number>;
  /** Closing prices per symbol for the trend column, oldest first. */
  trends: Record<string, number[]>;
};

export function SummaryTable({ summaries, slots, trends }: Props) {
  if (summaries.length === 0) return null;

  return (
    <section className="panel rounded-xl border bg-card p-4">
      <h2 className="mb-3 text-sm font-medium">Latest bar</h2>

      {/* Seven columns do not fit a phone; the table scrolls rather than
          wrapping figures onto two lines. */}
      <div className="overflow-x-auto">
        <table className="w-full min-w-[720px] border-collapse font-mono text-sm tabular-nums">
          <thead>
            <tr className="border-b text-xs tracking-wide text-muted-foreground uppercase">
              <Th align="left">Symbol</Th>
              {/* Hidden rather than shrunk below md: a 72px line squeezed into
                  a phone column stops being readable as a shape at all, and
                  every figure it summarises is still in the row. */}
              <Th align="left" className="hidden md:table-cell">
                Trend
              </Th>
              <Th align="left">Date</Th>
              <Th>Close</Th>
              <Th>Change</Th>
              <Th>Change %</Th>
              <Th>Volume</Th>
              <Th>Bars</Th>
            </tr>
          </thead>
          <tbody>
            {summaries.map((summary) => (
              <Row
                key={summary.symbol}
                summary={summary}
                slot={slots[summary.symbol]}
                trend={trends[summary.symbol] ?? []}
              />
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function Th({
  children,
  align = "right",
  className,
}: {
  children: React.ReactNode;
  align?: "left" | "right";
  className?: string;
}) {
  return (
    <th
      scope="col"
      className={cn(
        "px-3 py-2 font-medium",
        align === "left" ? "text-left" : "text-right",
        className,
      )}
    >
      {children}
    </th>
  );
}

function Row({
  summary,
  slot,
  trend,
}: {
  summary: SymbolSummary;
  slot: number | undefined;
  trend: number[];
}) {
  const { change } = summary;
  const up = change !== null && change >= 0;

  // Same rule as the KPI cards: a missing change means a single-bar window,
  // not a flat day, so it stays neutral rather than reading as green.
  const changeTone =
    change === null ? "text-muted-foreground" : up ? "text-gain" : "text-loss";

  return (
    <tr className="border-b last:border-0">
      <td className="px-3 py-2 font-medium">
        <span className="flex items-center gap-2">
          <SymbolBadge symbol={summary.symbol} slot={slot} />
          {summary.symbol}
        </span>
      </td>
      <td className="hidden px-3 py-2 md:table-cell">
        <Sparkline values={trend} />
      </td>
      <td className="px-3 py-2 text-muted-foreground">{summary.date}</td>
      <td className="px-3 py-2 text-right">{formatPrice(summary.close)}</td>
      <td className={cn("px-3 py-2 text-right", changeTone)}>
        {formatChange(change)}
      </td>
      <td className={cn("px-3 py-2 text-right", changeTone)}>
        {formatPercent(summary.changePct)}
      </td>
      <td className="px-3 py-2 text-right">{formatVolume(summary.volume)}</td>
      <td className="px-3 py-2 text-right text-muted-foreground">
        {summary.bars}
      </td>
    </tr>
  );
}
