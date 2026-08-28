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
      className="relative inline-flex size-9 shrink-0 items-center justify-center rounded-full border border-radar/30 bg-radar/5"
    >
      {/* Range rings. */}
      <span className="absolute inset-1.5 rounded-full border border-radar/20" />
      <span className="absolute inset-3 rounded-full border border-radar/15" />

      {/* The sweep: a quarter-turn wedge of light, rotating once every 4s. */}
      <span
        className="radar-sweep absolute inset-0 rounded-full"
        style={{
          background:
            "conic-gradient(from 0deg, color-mix(in oklab, var(--radar) 55%, transparent), transparent 25%)",
          maskImage: "radial-gradient(circle, black 62%, transparent 63%)",
          WebkitMaskImage:
            "radial-gradient(circle, black 62%, transparent 63%)",
        }}
      />

      {/* Contact blip at the centre. */}
      <span className="size-1 rounded-full bg-radar" />
    </span>
  );
}
