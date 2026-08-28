const price = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const signedPrice = new Intl.NumberFormat("en-US", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
  signDisplay: "always",
});

const compactVolume = new Intl.NumberFormat("en-US", {
  notation: "compact",
  maximumFractionDigits: 1,
});

export const formatPrice = (value: number | null) =>
  value === null ? "—" : price.format(value);

export const formatChange = (value: number | null) =>
  value === null ? "—" : signedPrice.format(value);

export const formatPercent = (value: number | null) =>
  value === null ? "—" : `${signedPrice.format(value)}%`;

export const formatVolume = (value: number | null) =>
  value === null ? "—" : compactVolume.format(value);
