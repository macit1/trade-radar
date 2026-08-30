import type { Metadata } from "next";
import { Chakra_Petch, Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

import { Providers } from "@/components/providers";

// Three faces, three jobs. next/font self-hosts each one and emits a CSS
// variable, so there is no render-blocking request to fonts.googleapis.com and
// no layout shift when a face arrives.

// Everything that is read as prose: labels, filter names, headings, body copy.
const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

// Prices, changes and volumes are read as an instrument panel, so they get a
// monospace face: digits line up column to column and never reflow as they tick.
const jetBrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
});

// The wordmark only. Chakra Petch is a squared technical face that suits the
// radar identity but is tiring to read in a paragraph, so it is wired to a
// `font-display` utility that exactly one element uses.
const chakraPetch = Chakra_Petch({
  variable: "--font-chakra-petch",
  subsets: ["latin"],
  // Not a variable font: the weights have to be named up front. The wordmark
  // is the only user and it is semibold, so one weight is the whole need.
  weight: ["600"],
});

export const metadata: Metadata = {
  title: "TradeRadar",
  description: "Daily OHLCV charts from the local TradeRadar store.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    // No theme class here: next-themes writes it onto <html> from a blocking
    // script before first paint, so the page never flashes the wrong palette.
    // That write is invisible to the server render, hence suppressHydrationWarning.
    <html
      lang="en"
      suppressHydrationWarning
      className={`${inter.variable} ${jetBrainsMono.variable} ${chakraPetch.variable} h-full antialiased`}
    >
      <body className="min-h-full bg-background text-foreground">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
