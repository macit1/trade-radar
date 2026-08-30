import type { Metadata } from "next";
import { Geist, JetBrains_Mono } from "next/font/google";
import "./globals.css";

import { Providers } from "@/components/providers";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

// Prices, changes and volumes are read as an instrument panel, so they get a
// monospace face: digits line up column to column and never reflow as they tick.
const jetBrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
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
      className={`${geistSans.variable} ${jetBrainsMono.variable} h-full antialiased`}
    >
      <body className="min-h-full bg-background text-foreground">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
