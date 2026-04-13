"use client";

import { useEffect, useRef, useState, useTransition } from "react";
import { Bell, ChevronRight, Loader2, LogOut, Settings, Sparkles, UserCircle2 } from "lucide-react";
import { ThemeToggle } from "@/components/theme-toggle";
import { createClient } from "@/lib/supabase/client";

interface HeaderProps {
  titulo: string;
  subtitulo?: string;
  eyebrow?: string;
  userName?: string;
  userEmail?: string;
  userOrg?: string;
}

export function Header({
  titulo,
  subtitulo,
  eyebrow = "Painel operacional",
  userName,
  userEmail,
  userOrg,
}: HeaderProps) {
  const [openPanel, setOpenPanel] = useState<"notificacoes" | "perfil" | null>(null);
  const [nome, setNome] = useState(userName ?? "Usuário");
  const [email, setEmail] = useState(userEmail ?? "");
  const [org, setOrg] = useState(userOrg ?? "ComprasPRO");
  const [isPending, startTransition] = useTransition();
  const wrapperRef = useRef<HTMLDivElement | null>(null);

  // Fechar dropdown ao clicar fora
  useEffect(() => {
    function handleOutsideClick(event: MouseEvent) {
      if (!wrapperRef.current?.contains(event.target as Node)) {
        setOpenPanel(null);
      }
    }
    document.addEventListener("mousedown", handleOutsideClick);
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, []);

  // Carregar dados reais do usuário logado (client-side)
  useEffect(() => {
    if (userName) return; // já veio via props do servidor — não sobrescrever
    const supabase = createClient();
    supabase.auth.getUser().then(({ data: { user } }) => {
      if (!user) return;
      setEmail(user.email ?? "");
      // Buscar nome do perfil
      supabase
        .from("perfis")
        .select("nome_completo, empresa_id")
        .eq("id", user.id)
        .single()
        .then(({ data }) => {
          if (data?.nome_completo) setNome(data.nome_completo);
        });
    });
  }, [userName]);

  // ─── Logout ───────────────────────────────────────────────────────────────
  // Chama o endpoint server-side para limpar os cookies SSR corretamente.
  // O signOut() client-side não consegue limpar cookies HTTP-only do servidor.
  const handleLogout = () => {
    startTransition(async () => {
      await fetch("/api/auth/logout", { method: "POST" });
      // Hard navigation para garantir que o middleware re-avalie a sessão
      window.location.href = "/auth/login";
    });
  };

  return (
    <header className="px-4 pt-4 sm:px-6 sm:pt-4 lg:px-6 lg:pt-4">
      <div className="relative rounded-[32px]" ref={wrapperRef}>
        {/* Fundo decorativo */}
        <div className="ds-panel absolute inset-0 rounded-[32px]">
          <div className="pointer-events-none absolute inset-y-0 right-0 w-[42%] bg-[radial-gradient(circle_at_top_right,rgb(var(--accent-primary) / 0.18),transparent_52%),radial-gradient(circle_at_60%_40%,rgb(var(--accent-secondary) / 0.12),transparent_40%)]" />
        </div>

        {/* Conteúdo */}
        <div className="relative flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between px-6 py-6 sm:px-8">
          <div className="min-w-0">
            <div className="inline-flex items-center gap-2 rounded-full border border-app bg-[linear-gradient(180deg,var(--surface-highlight),rgb(var(--bg-input) / 0.88))] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.24em] text-secondary shadow-[inset_0_1px_0_var(--surface-inset)]">
              <Sparkles className="h-3.5 w-3.5 text-primariaapp" />
              {eyebrow}
            </div>
            <h1 className="mt-4 text-3xl font-bold tracking-tight text-texto sm:text-4xl">{titulo}</h1>
            {subtitulo ? <p className="mt-2 max-w-3xl text-sm text-secondary sm:text-base">{subtitulo}</p> : null}
          </div>

          <div className="relative flex flex-wrap items-center gap-2 sm:gap-3 lg:justify-end">
            <ThemeToggle />

            {/* Notificações */}
            <button
              className="inline-flex h-11 w-11 items-center justify-center rounded-full border border-app bg-[linear-gradient(180deg,var(--surface-highlight),rgb(var(--bg-input) / 0.9))] text-secondary shadow-[inset_0_1px_0_var(--surface-inset)] transition hover:border-app-strong hover:text-texto focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primaria focus-visible:ring-offset-2 focus-visible:ring-offset-fundo"
              type="button"
              aria-label="Notificações"
              aria-expanded={openPanel === "notificacoes"}
              aria-haspopup="dialog"
              onClick={() => setOpenPanel((c) => (c === "notificacoes" ? null : "notificacoes"))}
            >
              <Bell className="h-5 w-5" />
            </button>

            {/* Perfil */}
            <button
              className="inline-flex h-11 w-11 items-center justify-center rounded-full border border-app bg-[linear-gradient(180deg,var(--surface-highlight),rgb(var(--bg-input) / 0.9))] text-secondary shadow-[inset_0_1px_0_var(--surface-inset)] transition hover:border-app-strong hover:text-texto focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primaria focus-visible:ring-offset-2 focus-visible:ring-offset-fundo"
              type="button"
              aria-label="Perfil"
              aria-expanded={openPanel === "perfil"}
              aria-haspopup="dialog"
              onClick={() => setOpenPanel((c) => (c === "perfil" ? null : "perfil"))}
            >
              <UserCircle2 className="h-5 w-5" />
            </button>

            {/* Dropdown — Notificações */}
            {openPanel === "notificacoes" && (
              <div
                role="dialog"
                aria-modal="false"
                aria-label="Painel de notificações"
                className="absolute right-0 top-14 z-30 w-[min(320px,calc(100vw-2rem))] rounded-[24px] border border-app-strong bg-[rgb(var(--bg-card))] p-4 shadow-[0_24px_64px_rgba(15,23,42,0.24)] sm:right-14"
              >
                <p className="ds-eyebrow">Notificações</p>
                <div className="mt-4 space-y-3">
                  {[
                    ["Nova análise importada", "Distribuidora XYZ enviou 15 itens agora"],
                    ["Validação manual pendente", "4 itens aguardam revisão de correspondência"],
                    ["Oportunidade ouro", "Paracetamol 500mg entrou com 20% abaixo do histórico"],
                  ].map(([tituloItem, descricao]) => (
                    <div key={tituloItem} className="rounded-[20px] border border-app bg-[rgb(var(--bg-card-strong))] p-3 shadow-[inset_0_1px_0_var(--surface-inset)]">
                      <p className="text-sm font-semibold text-texto">{tituloItem}</p>
                      <p className="mt-1 text-sm text-secondary">{descricao}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Dropdown — Perfil */}
            {openPanel === "perfil" && (
              <div
                role="dialog"
                aria-modal="false"
                aria-label="Painel de perfil"
                className="absolute right-0 top-14 z-30 w-[min(320px,calc(100vw-2rem))] rounded-[24px] border border-app-strong bg-[rgb(var(--bg-card))] p-4 shadow-[0_24px_64px_rgba(15,23,42,0.24)]"
              >
                <p className="ds-eyebrow">Usuário atual</p>
                <div className="mt-4 rounded-[20px] border border-app bg-[rgb(var(--bg-card-strong))] p-4 shadow-[inset_0_1px_0_var(--surface-inset)]">
                  <div className="flex items-center gap-3">
                    <div className="ds-icon-chip text-primariaapp">
                      <UserCircle2 className="h-5 w-5" />
                    </div>
                    <div className="min-w-0">
                      <p className="truncate text-sm font-semibold text-texto">{nome}</p>
                      {email && <p className="truncate text-xs text-secondary">{email}</p>}
                      {org && <p className="truncate text-xs text-secondary">{org}</p>}
                    </div>
                  </div>
                </div>
                <div className="mt-4 space-y-2">
                  <button
                    type="button"
                    className="flex w-full items-center justify-between rounded-2xl border border-app bg-[linear-gradient(180deg,var(--surface-highlight),rgb(var(--bg-input) / 0.9))] px-4 py-3 text-left text-sm text-texto transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primaria focus-visible:ring-offset-2 focus-visible:ring-offset-fundo hover:border-app-strong"
                  >
                    <span className="inline-flex items-center gap-2">
                      <Settings className="h-4 w-4 text-secondary" />
                      Configurações da conta
                    </span>
                    <ChevronRight className="h-4 w-4 text-secondary" />
                  </button>

                  {/* Botão Sair — chama handleLogout */}
                  <button
                    type="button"
                    disabled={isPending}
                    onClick={handleLogout}
                    className="flex w-full items-center justify-between rounded-2xl border border-red-500/20 bg-[linear-gradient(180deg,var(--surface-highlight),rgb(var(--bg-input) / 0.9))] px-4 py-3 text-left text-sm text-red-400 transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-400 focus-visible:ring-offset-2 focus-visible:ring-offset-fundo hover:border-red-500/40 hover:bg-red-500/5 disabled:opacity-60"
                  >
                    <span className="inline-flex items-center gap-2">
                      {isPending ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <LogOut className="h-4 w-4" />
                      )}
                      {isPending ? "Saindo..." : "Sair"}
                    </span>
                    {!isPending && <ChevronRight className="h-4 w-4 opacity-50" />}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
