import type { Metadata } from "next";
import { Exo, Roboto_Mono } from "next/font/google";
import "./globals.css";

import { Providers } from "@/components/providers";

// Two faces, and both of them are technical. next/font self-hosts each one and
// emits a CSS variable, so there is no render-blocking request to
// fonts.googleapis.com and no layout shift when a face arrives. The design
// system is explicit that this holds whatever the faces are - the generated
// `@import url(...)` alternative is a regression, not a shortcut.

// Headings and the wordmark. Squared and slightly futurist: the instrument
// character the interface is after, without resorting to a novelty face.
const exo = Exo({
  variable: "--font-exo",
  subsets: ["latin"],
});

// Everything else, prose included. A monospace UI is the point rather than a
// side effect - readings line up in columns and nothing reflows as a figure
// ticks. There is exactly one sentence of prose on the page, so the usual
// objection to mono body text does not apply here.
const robotoMono = Roboto_Mono({
  variable: "--font-roboto-mono",
  subsets: ["latin"],
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
      className={`${exo.variable} ${robotoMono.variable} h-full antialiased`}
    >
      <body className="min-h-full bg-background text-foreground">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
