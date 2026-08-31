/**
 * Company logo URLs, from Brandfetch's Logo API.
 *
 * Two things about this endpoint are easy to get wrong and were measured
 * before it was wired in:
 *
 * 1. **`fallback/404` is a path segment, not a query parameter.** Without it
 *    the CDN answers a missing ticker with its own lettermark placeholder and a
 *    200, so `onError` never fires and the badge below never falls back. The
 *    query form `?fallback=404` is silently ignored. Verified against a
 *    nonsense ticker: path form errors, query form returns a placeholder.
 * 2. **Sizing is also a path segment.** `?w=64` is ignored and the CDN returns
 *    the full 400x400; `/w/64/h/64` is honoured.
 *
 * Brandfetch requires the client ID on every request and expects the URL to be
 * embedded directly in an `img` tag - proxying it server-side is not allowed.
 * The ID is public by design, which is why it is a `NEXT_PUBLIC_` variable, but
 * it still lives in `.env.local` rather than the repo: this is a public
 * repository and a committed ID is someone else's quota to spend.
 */
const CLIENT_ID = process.env.NEXT_PUBLIC_BRANDFETCH_CLIENT_ID;

/**
 * Symbols whose ticker record is not the mark a reader recognises.
 *
 * GOOGL resolves correctly to Alphabet Inc., whose logo is a horizontal
 * wordmark - illegible in a 24px circle. Google's mark is the one that actually
 * identifies the company at this size. Remove the entry to go back to the
 * strictly-correct-but-unreadable one.
 */
const DOMAIN_OVERRIDES: Record<string, string> = {
  GOOGL: "google.com",
};

/** `null` when no client ID is configured - the badge then stays lettered. */
export function logoUrl(symbol: string, size = 48): string | null {
  if (!CLIENT_ID) return null;

  const override = DOMAIN_OVERRIDES[symbol];
  const subject = override ?? `ticker/${encodeURIComponent(symbol)}`;

  return `https://cdn.brandfetch.io/${subject}/fallback/404/w/${size}/h/${size}?c=${CLIENT_ID}`;
}
