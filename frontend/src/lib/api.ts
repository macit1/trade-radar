import type { PriceBar } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`);

  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText} from ${path}`);
  }

  return response.json() as Promise<T>;
}

/** Every symbol in the store. An empty store returns [], not an error. */
export function fetchSymbols() {
  return getJson<string[]>("/symbols");
}

/** Daily bars for the given symbols, oldest first, all symbols in one array. */
export function fetchPrices(symbols: string[]) {
  // The API takes one `symbols` parameter per ticker, not a comma-joined list.
  const params = new URLSearchParams();
  symbols.forEach((symbol) => params.append("symbols", symbol));

  return getJson<PriceBar[]>(`/prices?${params.toString()}`);
}
