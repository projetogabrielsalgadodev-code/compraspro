"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, ChevronLeft, ClipboardList, Cog, Home, Package, ShieldCheck, X } from "lucide-react";
import { cn } from "@/lib/utils";

const items = [
  { href: "/home", label: "Home", icon: Home },
  { href: "/historico", label: "Histórico", icon: BarChart3 },
  { href: "/produtos", label: "Produtos", icon: Package },
  { href: "/nova-analise", label: "Nova análise", icon: ClipboardList },
  { href: "/configuracoes", label: "Configurações", icon: Cog }
];

interface SidebarProps {
  collapsed: boolean;
  mobileOpen: boolean;
  onToggleCollapse: () => void;
  onCloseMobile: () => void;
  isAdmin?: boolean;
}

export function Sidebar({ collapsed, mobileOpen, onToggleCollapse, onCloseMobile, isAdmin = false }: SidebarProps) {
  const pathname = usePathname();
  const isOnAdminPages = pathname?.startsWith("/admin");

  const renderNavItem = (item: typeof items[0]) => {
    const Icon = item.icon;
    const ativo = pathname === item.href || (item.href !== "/" && pathname?.startsWith(item.href));
    return (
      <Link
        key={item.href}
        href={item.href}
        onClick={onCloseMobile}
        aria-current={ativo ? "page" : undefined}
        className={cn(
          "flex items-center gap-3 rounded-2xl px-4 py-3.5 text-base font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primaria focus-visible:ring-offset-2 focus-visible:ring-offset-fundo lg:text-sm",
          ativo
            ? "bg-[linear-gradient(180deg,rgb(var(--accent-primary) / 0.22),rgb(var(--accent-primary) / 0.08))] text-texto ring-app shadow-[inset_0_1px_0_var(--surface-inset)]"
            : "text-texto/88 hover:bg-[linear-gradient(180deg,rgb(var(--bg-card) / 0.96),rgb(var(--bg-input) / 0.94))] hover:text-texto"
        )}
      >
        <span className={cn("ds-icon-chip h-11 w-11 shrink-0", ativo ? "bg-[linear-gradient(180deg,rgb(var(--accent-primary) / 0.30),rgb(var(--accent-primary) / 0.12))] text-primariaapp" : "bg-[linear-gradient(180deg,rgb(var(--bg-card) / 0.98),rgb(var(--bg-input) / 0.95))] text-primariaapp") }>
          <Icon className="h-5 w-5 lg:h-4 lg:w-4" />
        </span>
        {!collapsed ? item.label : null}
      </Link>
    );
  };

  return (
    <>
      {mobileOpen ? <button type="button" className="fixed inset-0 z-40 bg-[rgba(15,23,42,0.42)] backdrop-blur-[2px] lg:hidden" onClick={onCloseMobile} aria-label="Fechar menu" /> : null}
      <aside
        className={cn(
          "fixed inset-y-4 left-3 z-50 w-[min(88vw,320px)] transition-transform duration-300 lg:left-4 lg:w-auto lg:translate-x-0",
          mobileOpen ? "translate-x-0" : "-translate-x-[120%] lg:translate-x-0"
        )}
      >
      <div className={cn("ds-panel flex h-[calc(100vh-2rem)] flex-col rounded-[28px] border-app-strong px-5 py-5 shadow-cartao lg:bg-[linear-gradient(180deg,rgb(var(--bg-card) / 0.98),rgb(var(--bg-card-strong) / 0.98))]", mobileOpen ? "bg-[linear-gradient(180deg,rgb(var(--bg-card) / 1),rgb(var(--bg-card-strong) / 1))] shadow-[0_22px_64px_rgba(15,23,42,0.26)]" : "", collapsed ? "lg:w-[96px] lg:px-3" : "lg:w-[272px]") }>
        <div className="pointer-events-none absolute inset-y-0 right-0 w-20 bg-[radial-gradient(circle_at_top_right,rgb(var(--accent-primary) / 0.12),transparent_65%)]" />
        <div className="ds-shell-line mb-8 flex items-center justify-between gap-3 pb-5">
          <div className="flex items-center gap-3 overflow-hidden">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[linear-gradient(135deg,rgba(36,76,255,1),rgba(14,165,233,0.95))] text-white shadow-[0_10px_24px_rgba(36,76,255,0.28)]">
            <BarChart3 className="h-5 w-5" />
          </div>
          {!collapsed ? <div>
            <p className="text-sm font-semibold tracking-tight text-texto">Compras PRO</p>
            <p className="text-xs font-medium text-secondary">Inteligência de compras</p>
          </div> : null}
          </div>
          <div className="flex gap-2">
            {/* C-10: focus-visible com ring-offset nos botões inline da sidebar */}
            <button type="button" onClick={onToggleCollapse} className="hidden h-9 w-9 items-center justify-center rounded-xl border border-app bg-[linear-gradient(180deg,var(--surface-highlight),rgb(var(--bg-input) / 0.92))] text-secondary transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primaria focus-visible:ring-offset-2 focus-visible:ring-offset-fundo hover:border-app-strong hover:text-texto lg:inline-flex" aria-label="Alternar menu lateral">
              <ChevronLeft className={cn("h-4 w-4 transition-transform", collapsed ? "rotate-180" : "rotate-0")} />
            </button>
            <button type="button" onClick={onCloseMobile} className="inline-flex h-9 w-9 items-center justify-center rounded-xl border border-app bg-[linear-gradient(180deg,rgb(var(--bg-card) / 0.98),rgb(var(--bg-input) / 0.96))] text-texto shadow-[0_10px_24px_rgba(15,23,42,0.12)] transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primaria focus-visible:ring-offset-2 focus-visible:ring-offset-fundo lg:hidden" aria-label="Fechar menu lateral">
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
        <nav className="space-y-2 flex-1 overflow-y-auto">
          {items.map(renderNavItem)}

          {/* Botão Painel Admin — visível somente para quem é admin */}
          {isAdmin && (
            <>
              <div className={cn("ds-shell-line relative mt-6 mb-3 pt-4", collapsed && "mt-4 mb-2 pt-2")} />
              <Link
                href="/admin/empresas"
                onClick={onCloseMobile}
                className={cn(
                  "group flex items-center gap-3 rounded-2xl px-4 py-3.5 text-base font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primaria focus-visible:ring-offset-2 focus-visible:ring-offset-fundo lg:text-sm",
                  isOnAdminPages
                    ? "bg-[linear-gradient(135deg,rgb(var(--accent-primary) / 0.20),rgb(var(--accent-secondary) / 0.10))] text-primariaapp ring-1 ring-[rgb(var(--accent-primary) / 0.18)] shadow-[0_4px_16px_rgba(36,76,255,0.12)]"
                    : "text-texto/88 hover:bg-[linear-gradient(135deg,rgb(var(--accent-primary) / 0.12),rgb(var(--accent-secondary) / 0.06))] hover:text-primariaapp"
                )}
              >
                <span className={cn(
                  "ds-icon-chip h-11 w-11 shrink-0",
                  isOnAdminPages
                    ? "bg-[linear-gradient(135deg,rgb(var(--accent-primary) / 0.30),rgb(var(--accent-secondary) / 0.16))] text-primariaapp"
                    : "bg-[linear-gradient(135deg,rgb(var(--accent-primary) / 0.14),rgb(var(--accent-secondary) / 0.08))] text-primariaapp"
                )}>
                  <ShieldCheck className="h-5 w-5 lg:h-4 lg:w-4" />
                </span>
                {!collapsed ? "Painel Admin" : null}
              </Link>
            </>
          )}
        </nav>
      </div>
    </aside>
    </>
  );
}
