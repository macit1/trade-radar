"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";

import { Button } from "@/components/ui/button";

/**
 * Flips between the two themes. It shows the theme you would switch *to*, the
 * way an OS control does - a sun means "go light".
 *
 * Which icon shows is decided in CSS, not in React state. The stored choice is
 * only known in the browser, so a component that rendered the icon from state
 * would either mismatch the server's HTML or need a mount flag and a
 * placeholder frame. next-themes has already put the theme class on <html>
 * before first paint, so `dark:` variants get it right with no JavaScript and
 * no layout shift.
 */
export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();

  return (
    <Button
      variant="outline"
      size="icon"
      // `resolvedTheme` rather than `theme`: with nothing stored the setting is
      // "system", and the button has to act on what is actually on screen. By
      // the time anyone can click, it has resolved.
      onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
      aria-label="Toggle light and dark theme"
      title="Toggle light and dark theme"
      className="text-muted-foreground hover:border-radar/45 hover:text-radar"
    >
      <Sun className="hidden size-4 dark:block" />
      <Moon className="size-4 dark:hidden" />
    </Button>
  );
}
