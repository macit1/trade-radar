import { cn } from "@/lib/utils";

type Props = {
  /** Closing prices, oldest first. */
  values: number[];
  className?: string;
};

const WIDTH = 72;
const HEIGHT = 20;
const PAD = 2;

/**
 * The shape of a symbol's recent move, with no axes, grid or labels.
 *
 * A hand-rolled polyline rather than a charting library: this is twenty pixels
 * tall and drawn once per row, and `lightweight-charts` would mean an
 * instance, a canvas and a resize observer each time.
 *
 * Each line is scaled to its own range, so the shape is comparable across rows
 * but the height is not - a flat-looking line here is a flat *period*, not a
 * small number. The row's own change column carries the magnitude.
 */
export function Sparkline({ values, className }: Props) {
  // One point is a dot, not a trend, and zero is an empty period.
  if (values.length < 2) {
    return <span className="text-muted-foreground">—</span>;
  }

  const min = Math.min(...values);
  const max = Math.max(...values);
  // A perfectly flat series would divide by zero; it draws down the middle.
  const span = max - min || 1;

  const points = values
    .map((value, index) => {
      const x = PAD + (index / (values.length - 1)) * (WIDTH - PAD * 2);
      const y = HEIGHT - PAD - ((value - min) / span) * (HEIGHT - PAD * 2);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  const first = values[0];
  const last = values[values.length - 1];
  const up = last >= first;
  const movePct = first === 0 ? 0 : ((last - first) / first) * 100;

  const [lastX, lastY] = points.split(" ").at(-1)!.split(",");

  return (
    <svg
      // Not decorative: the shape says something the row's figures do not, so
      // it gets a label rather than being hidden. The label carries the same
      // fact the picture does - direction and size of the move over the window.
      role="img"
      aria-label={`${values.length}-session trend, ${up ? "up" : "down"} ${Math.abs(movePct).toFixed(1)} percent`}
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      width={WIDTH}
      height={HEIGHT}
      className={cn("overflow-visible", up ? "text-gain" : "text-loss", className)}
    >
      <polyline
        points={points}
        fill="none"
        stroke="currentColor"
        strokeWidth={1.5}
        strokeLinecap="round"
        strokeLinejoin="round"
        // pathLength normalises the stroke to 1 unit, so the draw-in below can
        // use a dash offset of 1 without measuring the real path.
        pathLength={1}
        className="sparkline-draw"
      />
      {/* The end of the line is where the eye should land, and it doubles as a
          second cue for direction alongside the colour. */}
      <circle cx={lastX} cy={lastY} r={1.6} fill="currentColor" />
    </svg>
  );
}
