"use client";

import { useEffect, useState } from "react";
import { BarChart3, Brain, Database, FileSearch, Sparkles, Zap } from "lucide-react";

const ETAPAS = [
  { icone: FileSearch, texto: "Extraindo itens da oferta...", delay: 0 },
  { icone: Database, texto: "Consultando catálogo de produtos...", delay: 3000 },
  { icone: Brain, texto: "Analisando histórico de preços...", delay: 7000 },
  { icone: Zap, texto: "Buscando equivalentes farmacêuticos...", delay: 12000 },
  { icone: Sparkles, texto: "Classificando e gerando recomendações...", delay: 18000 },
  { icone: BarChart3, texto: "Finalizando análise inteligente...", delay: 25000 },
];

interface AnaliseLoadingScreenProps {
  visible: boolean;
}

export function AnaliseLoadingScreen({ visible }: AnaliseLoadingScreenProps) {
  const [etapaAtual, setEtapaAtual] = useState(0);
  const [dots, setDots] = useState("");

  // Avançar etapas automaticamente
  useEffect(() => {
    if (!visible) {
      setEtapaAtual(0);
      return;
    }

    const timers = ETAPAS.map((etapa, index) =>
      setTimeout(() => setEtapaAtual(index), etapa.delay)
    );

    return () => timers.forEach(clearTimeout);
  }, [visible]);

  // Animar os pontinhos
  useEffect(() => {
    if (!visible) return;
    const interval = setInterval(() => {
      setDots((prev) => (prev.length >= 3 ? "" : prev + "."));
    }, 500);
    return () => clearInterval(interval);
  }, [visible]);

  if (!visible) return null;

  const EtapaIcone = ETAPAS[etapaAtual].icone;

  return (
    <div
      className="fixed inset-0 z-[100] flex flex-col items-center justify-center"
      style={{
        background:
          "linear-gradient(135deg, rgb(var(--accent-primary)) 0%, rgb(var(--accent-tertiary)) 55%, rgb(var(--accent-secondary)) 100%)",
      }}
    >
      {/* Glow orbs decorativos */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute left-1/2 top-1/3 h-[320px] w-[320px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-white/10 blur-[80px]" />
        <div className="absolute bottom-[15%] right-[20%] h-[200px] w-[200px] rounded-full bg-white/[0.06] blur-[60px]" />
        {/* Orb animado extra */}
        <div
          className="absolute left-[15%] top-[60%] h-[180px] w-[180px] rounded-full bg-white/[0.08] blur-[70px]"
          style={{ animation: "pulse 3s ease-in-out infinite" }}
        />
      </div>

      {/* Conteúdo central */}
      <div className="flex flex-col items-center gap-8">
        {/* Ícone principal com animação de pulso */}
        <div className="relative">
          {/* Ring animado */}
          <div
            className="absolute inset-0 rounded-[28px] bg-white/20"
            style={{
              animation: "ping 2s cubic-bezier(0, 0, 0.2, 1) infinite",
              transform: "scale(1.3)",
            }}
          />
          <div className="relative flex h-24 w-24 items-center justify-center rounded-[28px] bg-white/[0.14] shadow-[0_16px_48px_rgba(0,0,0,0.18),inset_0_1px_0_rgba(255,255,255,0.2)] backdrop-blur-sm">
            <Brain className="h-12 w-12 text-white" style={{ animation: "pulse 2s ease-in-out infinite" }} />
          </div>
        </div>

        {/* Título */}
        <div className="text-center">
          <h1 className="text-4xl font-bold tracking-tight text-white">
            IA Analisando
          </h1>
          <p className="mt-2 text-lg font-normal text-white/70">
            Processamento inteligente em andamento
          </p>
        </div>

        {/* Etapa atual com animação */}
        <div className="flex items-center gap-3 rounded-2xl bg-white/10 px-6 py-4 backdrop-blur-sm transition-all duration-500">
          <EtapaIcone className="h-5 w-5 text-white/90" style={{ animation: "spin 3s linear infinite" }} />
          <span className="text-sm font-medium text-white/90">
            {ETAPAS[etapaAtual].texto}
          </span>
        </div>

        {/* Barra de progresso das etapas */}
        <div className="flex items-center gap-2 px-4">
          {ETAPAS.map((_, index) => (
            <div
              key={index}
              className={`h-1.5 rounded-full transition-all duration-700 ${
                index <= etapaAtual
                  ? "w-8 bg-white/80"
                  : "w-4 bg-white/20"
              }`}
            />
          ))}
        </div>
      </div>

      {/* Indicador de carregamento inferior */}
      <div className="absolute bottom-20 flex flex-col items-center gap-3">
        <div className="flex gap-1.5">
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-white/50" style={{ animationDelay: "0ms" }} />
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-white/50" style={{ animationDelay: "200ms" }} />
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-white/50" style={{ animationDelay: "400ms" }} />
        </div>
        <p className="text-xs font-medium tracking-widest text-white/40 uppercase">
          Aguarde, isso pode levar alguns segundos{dots}
        </p>
      </div>
    </div>
  );
}
