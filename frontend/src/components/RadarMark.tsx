/**
 * The logo mark: a scope face with a sweep line orbiting it.
 *
 * This is the only animated element on the page. The chart and the KPI cards
 * stay perfectly still - numbers people read should never move.
 */
export function RadarMark() {
  return (
    <span
      aria-hidden
      // The rings and the sweep are alpha over the brand, and alpha that reads
      // as a glow on black nearly disappears on white - so light mode carries
      // its own, firmer set. The dark values are the originals.
      className="relative inline-flex size-9 shrink-0 items-center justify-center rounded-full border border-brand/50 bg-brand/8 dark:border-brand/30 dark:bg-brand/5"
    >
      {/* Range rings. */}
      <span className="absolute inset-1.5 rounded-full border border-brand/35 dark:border-brand/20" />
      <span className="absolute inset-3 rounded-full border border-brand/25 dark:border-brand/15" />

      {/* The sweep: a quarter-turn wedge of light, rotating once every 4s. */}
      <span
        className="radar-sweep absolute inset-0 rounded-full"
        style={{
          background:
            "conic-gradient(from 0deg, color-mix(in oklab, var(--brand) var(--sweep-strength), transparent), transparent 25%)",
          maskImage: "radial-gradient(circle, black 62%, transparent 63%)",
          WebkitMaskImage:
            "radial-gradient(circle, black 62%, transparent 63%)",
        }}
      />

      {/* Contact blip at the centre. */}
      <span className="size-1 rounded-full bg-brand" />
    </span>
  );
}
