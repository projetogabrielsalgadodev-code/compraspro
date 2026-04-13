"use client";

import { useEffect, useState } from "react";
import { MoonStar, SunMedium } from "lucide-react";
import { useTheme } from "next-themes";
import { cn } from "@/lib/utils";

export function ThemeToggle({ compact = false, className }: { compact?: boolean; className?: string }) {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const isDark = mounted ? resolvedTheme !== "light" : true;

  return (
    <button
      type="button"
      onClick={() => setTheme(isDark ? "light" : "dark")}
      className={cn(
        compact
          ? "inline-flex h-11 w-11 items-center justify-center rounded-full border border-app bg-[linear-gradient(180deg,var(--surface-highlight),rgb(var(--bg-input) / 0.9))] text-secondary shadow-[inset_0_1px_0_var(--surface-inset)] transition hover:border-app-strong hover:text-texto focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primaria focus-visible:ring-offset-2 focus-visible:ring-offset-fundo"
          : "inline-flex h-11 items-center gap-2 rounded-full border border-app bg-[linear-gradient(180deg,var(--surface-highlight),rgb(var(--bg-input) / 0.9))] px-4 text-sm font-medium text-secondary shadow-[inset_0_1px_0_var(--surface-inset)] transition hover:border-app-strong hover:text-texto focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primaria focus-visible:ring-offset-2 focus-visible:ring-offset-fundo",
        className
      )}
      aria-label="Alternar tema"
    >
      {isDark ? <SunMedium className="h-4 w-4" /> : <MoonStar className="h-4 w-4" />}
      {compact ? null : <span>{isDark ? "Modo claro" : "Modo escuro"}</span>}
    </button>
  );
}
