"use client";

import { useState } from "react";
import { PanelLeftOpen } from "lucide-react";
import { Sidebar } from "@/components/layout/Sidebar";
import { cn } from "@/lib/utils";

export function DashboardShell({ children, isAdmin = false }: { children: React.ReactNode; isAdmin?: boolean }) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-fundo lg:flex">
      <Sidebar
        collapsed={sidebarCollapsed}
        mobileOpen={mobileMenuOpen}
        onToggleCollapse={() => setSidebarCollapsed((current) => !current)}
        onCloseMobile={() => setMobileMenuOpen(false)}
        isAdmin={isAdmin}
      />
      <main
        className={cn(
          "min-w-0 flex-1 pb-10 transition-[padding] duration-300 lg:pr-5",
          sidebarCollapsed ? "lg:pl-[136px]" : "lg:pl-[312px]"
        )}
      >
        <div className="fixed left-3 top-4 z-30 lg:hidden">
          <button
            type="button"
            onClick={() => setMobileMenuOpen(true)}
            className="group inline-flex h-12 w-12 items-center justify-center rounded-[20px] border border-app-strong bg-[linear-gradient(180deg,rgb(var(--bg-card) / 0.98),rgb(var(--bg-card-strong) / 1))] text-texto shadow-[0_14px_30px_rgba(15,23,42,0.16)] backdrop-blur transition-all duration-300 ease-out hover:-translate-y-0.5 hover:scale-[1.02] hover:border-app-strong hover:shadow-[0_18px_36px_rgba(15,23,42,0.22)] active:scale-[0.98]"
            aria-label="Abrir menu lateral"
          >
            <span className="absolute inset-0 rounded-[20px] bg-[radial-gradient(circle_at_top_left,rgb(var(--accent-primary) / 0.14),transparent_55%)] opacity-80" />
            <PanelLeftOpen className="relative h-5 w-5 text-primariaapp transition duration-300 group-hover:translate-x-[1px] group-hover:scale-105" />
          </button>
        </div>
        {children}
      </main>
    </div>
  );
}
