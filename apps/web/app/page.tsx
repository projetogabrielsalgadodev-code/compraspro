"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { BarChart3 } from "lucide-react";

/**
 * C-15: Tela Splash — animação de entrada com logo, nome do app e
 * subtítulo, seguida de redirect automático para /home após 2.4s.
 *
 * Design system spec:
 * - bg: action-strong (gradiente accent-primary → accent-tertiary)
 * - Logo: text-on-dark, text-5xl, font-bold
 * - Subtítulo: text-on-dark (opacity 70%), text-lg, font-normal
 * - Padding: space-20 (80px)
 */
export default function SplashPage() {
  const router = useRouter();
  const [phase, setPhase] = useState<"enter" | "exit">("enter");

  useEffect(() => {
    // Inicia animação de saída após 1.8s, navega após a transição
    const exitTimer = setTimeout(() => setPhase("exit"), 1800);
    const navTimer = setTimeout(() => router.replace("/home"), 2400);
    return () => {
      clearTimeout(exitTimer);
      clearTimeout(navTimer);
    };
  }, [router]);

  return (
    <div
      className={`fixed inset-0 z-[100] flex flex-col items-center justify-center transition-opacity duration-500 ${
        phase === "exit" ? "opacity-0" : "opacity-100"
      }`}
      style={{
        background:
          "linear-gradient(135deg, rgb(var(--accent-primary)) 0%, rgb(var(--accent-tertiary)) 55%, rgb(var(--accent-secondary)) 100%)"
      }}
    >
      {/* Glow orb decorativo */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute left-1/2 top-1/3 h-[320px] w-[320px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-white/10 blur-[80px]" />
        <div className="absolute bottom-[15%] right-[20%] h-[200px] w-[200px] rounded-full bg-white/[0.06] blur-[60px]" />
      </div>

      {/* Conteúdo central com animação fade-up */}
      <div
        className={`flex flex-col items-center gap-6 transition-all duration-700 ease-out ${
          phase === "enter" ? "translate-y-0 opacity-100" : "translate-y-4 opacity-0"
        }`}
        style={{ animationDelay: "100ms" }}
      >
        {/* Ícone/Logo */}
        <div
          className="flex h-24 w-24 items-center justify-center rounded-[28px] bg-white/[0.14] shadow-[0_16px_48px_rgba(0,0,0,0.18),inset_0_1px_0_rgba(255,255,255,0.2)] backdrop-blur-sm"
        >
          <BarChart3 className="h-12 w-12 text-white" />
        </div>

        {/* Nome do app — text-5xl bold */}
        <h1 className="text-5xl font-bold tracking-tight text-white">
          Compras PRO
        </h1>

        {/* Subtítulo — text-lg, 70% opacity */}
        <p className="text-lg font-normal text-white/70">
          Análise inteligente de ofertas
        </p>
      </div>

      {/* Indicador de carregamento sutil */}
      <div className="absolute bottom-20 flex flex-col items-center gap-3">
        <div className="flex gap-1.5">
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-white/50" style={{ animationDelay: "0ms" }} />
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-white/50" style={{ animationDelay: "200ms" }} />
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-white/50" style={{ animationDelay: "400ms" }} />
        </div>
        <p className="text-xs font-medium tracking-widest text-white/40 uppercase">Carregando</p>
      </div>
    </div>
  );
}
