"use client"

import { Moon, Sun } from "lucide-react"

import { Button } from "@/components/ui/button"
import { useMounted } from "@/hooks/use-mounted"
import { useTheme } from "@/providers/theme-provider"
import { cn } from "@/lib/utils"

export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme()
  const mounted = useMounted()

  if (!mounted) {
    return (
      <Button
        variant="ghost"
        size="icon-sm"
        className="size-8"
        aria-label="Toggle theme"
      />
    )
  }

  const isDark = resolvedTheme === "dark"

  return (
    <Button
      variant="ghost"
      size="icon-sm"
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      onClick={() => setTheme(isDark ? "light" : "dark")}
      className={cn(
        "size-8 text-muted-foreground hover:bg-white/[0.06] hover:text-foreground"
      )}
    >
      {isDark ? <Sun className="size-4" /> : <Moon className="size-4" />}
    </Button>
  )
}
