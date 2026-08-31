"use client";

import { useEffect, useRef, useState } from "react";

import type { SparkPoint } from "@/lib/analytics";
import { formatPrice } from "@/lib/format";
import { cn } from "@/lib/utils";

type Props = {
  /** Closing prices with their dates, oldest first. */
  values: SparkPoint[];
  className?: string;
};

const WIDTH = 72;
const HEIGHT = 20;
const PAD = 2;

/**
 * The shape of a symbol's recent move, with no axes, grid or labels.
 *
 * A hand-rolled polyline rather than a charting library: this is twenty pixels
 * tall and drawn once per row, and `lightweight-charts` would mean an instance,
 * a canvas and a resize observer each time.
 *
 * Each line is scaled to its own range, so the shape is comparable across rows
 * but the height is not - a flat-looking line here is a flat *period*, not a
 * small number. The row's own change column carries the magnitude.
 */
export function Sparkline({ values, className }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  // The anchor is stored alongside the index rather than derived while
  // rendering: working it out needs the measured box, and reading a ref during
  // render is exactly what React tells you not to do. Every write below happens
  // inside an event handler, where the measurement is valid anyway.
  const [active, setActive] = useState<{
    index: number;
    x: number;
    y: number;
  } | null>(null);

  // A fixed-position readout is anchored to a measurement, and a measurement
  // goes stale the moment the page moves under it - including the scroll the
  // browser itself performs when this element is focused by keyboard. So while
  // a point is active, re-measure on scroll and resize. Runs before the early
  // return below because hooks have to.
  const activeIndex = active?.index ?? null;
  useEffect(() => {
    if (activeIndex === null) return;

    function remeasure() {
      const rect = svgRef.current?.getBoundingClientRect();
      if (!rect || values.length < 2) return;
      const svgX = PAD + (activeIndex! / (values.length - 1)) * (WIDTH - PAD * 2);
      setActive({
        index: activeIndex!,
        x: rect.left + (svgX / WIDTH) * rect.width,
        y: rect.top,
      });
    }

    // Once on the next frame, because focusing by keyboard scrolls the element
    // into view *synchronously* - before this effect subscribes - so there is
    // no scroll event left to react to and the measurement taken in the focus
    // handler is already stale. Re-running it costs nothing when nothing moved,
    // and setting the same index back does not re-run this effect.
    const frame = requestAnimationFrame(remeasure);

    // Capture phase: the scroll may happen on the table's own container rather
    // than the window, and those events do not bubble.
    window.addEventListener("scroll", remeasure, true);
    window.addEventListener("resize", remeasure);
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("scroll", remeasure, true);
      window.removeEventListener("resize", remeasure);
    };
  }, [activeIndex, values.length]);

  // One point is a dot, not a trend, and zero is an empty period.
  if (values.length < 2) {
    return <span className="text-muted-foreground">—</span>;
  }

  const closes = values.map((point) => point.close);
  const min = Math.min(...closes);
  const max = Math.max(...closes);
  // A perfectly flat series would divide by zero; it draws down the middle.
  const span = max - min || 1;

  const coords = values.map((point, index) => ({
    x: PAD + (index / (values.length - 1)) * (WIDTH - PAD * 2),
    y: HEIGHT - PAD - ((point.close - min) / span) * (HEIGHT - PAD * 2),
  }));

  const first = closes[0];
  const last = closes[closes.length - 1];
  const up = last >= first;
  const movePct = first === 0 ? 0 : ((last - first) / first) * 100;

  /** Index of the drawn point nearest a client x. */
  function nearestIndex(clientX: number) {
    const rect = svgRef.current?.getBoundingClientRect();
    if (!rect || rect.width === 0) return null;
    const ratio = (clientX - rect.left) / rect.width;
    const index = Math.round(ratio * (values.length - 1));
    return Math.min(Math.max(index, 0), values.length - 1);
  }

  /** The active-point record for an index, measured against the drawn box. */
  function pointAt(index: number) {
    const rect = svgRef.current?.getBoundingClientRect();
    if (!rect) return null;
    return {
      index,
      x: rect.left + (coords[index].x / WIDTH) * rect.width,
      y: rect.top,
    };
  }

  function handleKeyDown(event: React.KeyboardEvent<SVGSVGElement>) {
    if (event.key === "Escape") {
      setActive(null);
      return;
    }

    const step =
      event.key === "ArrowRight" ? 1 : event.key === "ArrowLeft" ? -1 : 0;
    if (step === 0) return;

    // Otherwise the arrow keys scroll the table sideways instead.
    event.preventDefault();
    const from = active?.index ?? values.length - 1;
    const next = Math.min(Math.max(from + step, 0), values.length - 1);
    setActive(pointAt(next));
  }

  return (
    <>
      <svg
        ref={svgRef}
        // Not decorative: the shape says something the row's figures do not, so
        // it gets a label rather than being hidden. The label carries the same
        // fact the picture does - direction and size of the move over the
        // window - for anyone who cannot see the line.
        role="img"
        aria-label={`${values.length}-session trend, ${up ? "up" : "down"} ${Math.abs(movePct).toFixed(1)} percent`}
        // Focusable because the readings are otherwise hover-only, and hover
        // exists on neither a keyboard nor a touchscreen. Arrow keys walk the
        // points, Escape dismisses.
        tabIndex={0}
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        width={WIDTH}
        height={HEIGHT}
        onMouseMove={(event) => {
          const index = nearestIndex(event.clientX);
          setActive(index === null ? null : pointAt(index));
        }}
        onMouseLeave={() => setActive(null)}
        onFocus={() => setActive(pointAt(values.length - 1))}
        onBlur={() => setActive(null)}
        onKeyDown={handleKeyDown}
        className={cn(
          "overflow-visible rounded-xs focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none",
          up ? "text-gain" : "text-loss",
          className,
        )}
      >
        <polyline
          points={coords.map((point) => `${point.x},${point.y}`).join(" ")}
          fill="none"
          stroke="currentColor"
          strokeWidth={1.5}
          strokeLinecap="round"
          strokeLinejoin="round"
          // pathLength normalises the stroke to 1 unit, so the draw-in can use
          // a dash offset of 1 without measuring the real path.
          pathLength={1}
          className="sparkline-draw"
        />

        {/* The end of the line is where the eye should land, and it doubles as
            a second cue for direction alongside the colour. */}
        <circle
          cx={coords[coords.length - 1].x}
          cy={coords[coords.length - 1].y}
          r={1.6}
          fill="currentColor"
        />

        {active && (
          // Ringed in the card colour so it stays visible wherever on the line
          // it lands, including on top of the end dot.
          <circle
            cx={coords[active.index].x}
            cy={coords[active.index].y}
            r={2.2}
            fill="currentColor"
            stroke="var(--card)"
            strokeWidth={1}
          />
        )}
      </svg>

      {/* Fixed rather than absolute: the table scrolls horizontally, and an
          absolutely positioned readout would be clipped by that container.
          No transition - it appears at once, so there is no motion for
          prefers-reduced-motion to have an opinion about. */}
      {active && (
        <div
          role="tooltip"
          // Deliberately not `.panel`: that class is declared outside Tailwind's
          // layers, so its `position: relative` beats the `fixed` utility here
          // and the readout lands wherever the document flow puts it. Cards can
          // have the panel treatment; a floating readout cannot.
          className="pointer-events-none fixed z-50 -translate-x-1/2 -translate-y-full rounded-md border border-border bg-popover px-2 py-1 font-mono text-xs whitespace-nowrap text-popover-foreground shadow-md"
          style={{ left: active.x, top: active.y - 6 }}
        >
          <span className="text-muted-foreground">
            {values[active.index].date}
          </span>{" "}
          <span className="tabular-nums">
            {formatPrice(values[active.index].close)}
          </span>
        </div>
      )}
    </>
  );
}
