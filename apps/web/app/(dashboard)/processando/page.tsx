"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Bot, CheckCircle2, Circle, Loader2, AlertTriangle, ArrowRight, RotateCcw } from "lucide-react";
import { DashboardPage } from "@/components/layout/DashboardPage";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const etapas = [
  "Lendo itens e preços",
  "Buscando correspondências",
  "Avaliando equivalentes",
  "Comparando com histórico",
  "Calculando estoque e cobertura"
];

const POLL_INTERVAL_MS = 3000;

export default function ProcessandoPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const analiseId = searchParams.get("id");

  const [etapaAtual, setEtapaAtual] = useState(0);
  const [status, setStatus] = useState<"processando" | "concluida" | "erro" | "timeout">("processando");
  const [erroMsg, setErroMsg] = useState<string | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  // Animated step progression (visual only)
  useEffect(() => {
    if (status !== "processando") return;

    const timer = setInterval(() => {
      setEtapaAtual((prev) => {
        // Loop slowly through steps while processing
        if (prev >= etapas.length - 1) return prev;
        return prev + 1;
      });
    }, 2500);
    return () => clearInterval(timer);
  }, [status]);

  // Track elapsed time for timeout
  useEffect(() => {
    if (status !== "processando") return;
    const timer = setInterval(() => {
      setElapsedSeconds((prev) => {
        const next = prev + 1;
        // Timeout after 2 minutes
        if (next >= 120) {
          setStatus("timeout");
          return next;
        }
        return next;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [status]);

  // Real polling against backend
  const poll = useCallback(async () => {
    if (!analiseId) return;

    try {
      const response = await fetch(`/api/ofertas/status/${analiseId}`);
      if (!response.ok) return;

      const data = await response.json();

      if (data.status === "concluida") {
        setStatus("concluida");
        setEtapaAtual(etapas.length - 1);
        // Small delay for the animation to feel complete
        setTimeout(() => {
          router.push(`/resultado/${analiseId}`);
        }, 800);
      } else if (data.status === "erro") {
        setStatus("erro");
        setErroMsg(data.resultado?.erro || data.erro || "A análise encontrou um problema durante o processamento.");
      }
      // else keep polling (still processando)
    } catch {
      // Network error — just continue polling
    }
  }, [analiseId, router]);

  useEffect(() => {
    if (!analiseId || (status !== "processando" && status !== "timeout")) return;

    // Initial poll
    poll();

    const interval = setInterval(poll, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [analiseId, status, poll]);

  // If no ID provided, show fallback
  if (!analiseId) {
    return (
      <DashboardPage titulo="Processamento" subtitulo="Nenhuma análise em andamento." eyebrow="Motor de leitura">
        <Card className="py-16 text-center">
          <p className="text-lg font-semibold text-texto mb-2">Nenhuma análise identificada</p>
          <p className="text-sm text-secondary mb-6">Inicie uma nova análise na Central de Análise.</p>
          <Button onClick={() => router.push("/home")} variant="secondary">
            Voltar à Central
          </Button>
        </Card>
      </DashboardPage>
    );
  }

  const progressPercent = status === "concluida"
    ? 100
    : status === "erro" || status === "timeout"
      ? 100
      : ((etapaAtual + 1) / etapas.length) * 100;

  return (
    <DashboardPage titulo="Analisando oferta" subtitulo="O processamento deve levar apenas alguns segundos." eyebrow="Motor de leitura">
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <span className="ds-icon-chip text-primariaapp">
              {status === "erro" ? (
                <AlertTriangle className="h-4 w-4 text-descartavel" />
              ) : status === "concluida" ? (
                <CheckCircle2 className="h-4 w-4 text-ouro" />
              ) : (
                <Bot className="h-4 w-4" />
              )}
            </span>
            <div>
              <CardTitle>
                {status === "erro"
                  ? "Erro na análise"
                  : status === "concluida"
                    ? "Análise concluída!"
                    : "Etapas do processamento"}
              </CardTitle>
              <p className="mt-1 text-sm text-secondary">
                {status === "erro"
                  ? "Ocorreu um problema durante a análise."
                  : status === "concluida"
                    ? "Redirecionando para os resultados..."
                    : `Etapa ${etapaAtual + 1} de ${etapas.length}`}
              </p>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-5">
          {/* Barra de progresso */}
          <div className="overflow-hidden rounded-full bg-[rgb(var(--bg-input) / 1)]" style={{ height: 6 }}>
            <div
              className={`h-full rounded-full transition-all duration-700 ease-out ${
                status === "erro"
                  ? "bg-descartavel"
                  : status === "concluida"
                    ? "bg-ouro"
                    : "bg-[rgb(var(--accent-primary))]"
              }`}
              style={{ width: `${progressPercent}%` }}
            />
          </div>

          {/* Erro / Timeout state */}
          {(status === "erro" || status === "timeout") && (
            <div className="ds-subpanel rounded-2xl p-5 space-y-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="h-5 w-5 text-descartavel shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-semibold text-texto">
                    {status === "timeout"
                      ? "A análise está demorando mais que o esperado"
                      : "A análise não pôde ser concluída"}
                  </p>
                  <p className="text-sm text-secondary mt-1">
                    {status === "timeout"
                      ? "O processamento está levando mais de 2 minutos. Isso pode acontecer com ofertas muito grandes. A análise continua em segundo plano — você pode verificar o resultado no histórico."
                      : erroMsg}
                  </p>
                </div>
              </div>
              <div className="flex gap-3">
                <Button onClick={() => router.push("/home")} variant="secondary" className="gap-2">
                  <RotateCcw className="h-4 w-4" />
                  {status === "timeout" ? "Nova Análise" : "Tentar novamente"}
                </Button>
                <Button onClick={() => router.push("/historico")} variant="secondary" className="gap-2">
                  Ver Histórico
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}

          {/* Steps checklist */}
          <div className="space-y-3">
            {etapas.map((etapa, index) => {
              const concluida = index < etapaAtual || status === "concluida";
              const atual = index === etapaAtual && status === "processando";

              return (
                <div
                  key={etapa}
                  className={`flex items-center gap-3 rounded-[20px] border px-4 py-3.5 text-sm transition-all duration-300 ${
                    concluida
                      ? "border-ouro/20 bg-[linear-gradient(135deg,rgba(22,163,74,0.08),transparent)] text-texto"
                      : atual
                        ? "border-app-strong bg-[linear-gradient(135deg,rgb(var(--accent-primary) / 0.08),transparent)] text-texto shadow-[inset_0_1px_0_var(--surface-inset)]"
                        : "border-app bg-[rgb(var(--bg-input) / 0.5)] text-muted-app"
                  }`}
                >
                  {concluida ? (
                    <CheckCircle2 className="h-5 w-5 shrink-0 text-ouro" />
                  ) : atual ? (
                    <Loader2 className="h-5 w-5 shrink-0 animate-spin text-primariaapp" />
                  ) : (
                    <Circle className="h-5 w-5 shrink-0 text-muted-app" />
                  )}
                  <span className={concluida ? "line-through opacity-60" : ""}>
                    {index + 1}. {etapa}
                  </span>
                </div>
              );
            })}
          </div>

          {/* Concluída state */}
          {status === "concluida" && (
            <div className="flex items-center justify-center gap-3 pt-2">
              <Loader2 className="h-4 w-4 animate-spin text-primariaapp" />
              <p className="text-sm font-medium text-texto">Carregando resultados...</p>
            </div>
          )}
        </CardContent>
      </Card>
    </DashboardPage>
  );
}
