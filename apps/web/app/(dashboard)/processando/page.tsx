"use client";

import { useEffect, useState } from "react";
import { Bot, CheckCircle2, Circle, Loader2 } from "lucide-react";
import { DashboardPage } from "@/components/layout/DashboardPage";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Metadata } from "next";

const etapas = [
  "Lendo itens e preços",
  "Buscando correspondências",
  "Avaliando equivalentes",
  "Comparando com histórico",
  "Calculando estoque e cobertura"
];

/* C-17: Barra de progresso animada e ícones de status por etapa */
export default function ProcessandoPage() {
  const [etapaAtual, setEtapaAtual] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setEtapaAtual((prev) => {
        if (prev >= etapas.length - 1) {
          clearInterval(timer);
          return prev;
        }
        return prev + 1;
      });
    }, 2000);
    return () => clearInterval(timer);
  }, []);

  const progressPercent = ((etapaAtual + 1) / etapas.length) * 100;

  return (
    <DashboardPage titulo="Analisando oferta" subtitulo="O processamento deve levar apenas alguns segundos." eyebrow="Motor de leitura">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <span className="ds-icon-chip text-primariaapp"><Bot className="h-4 w-4" /></span>
              <div>
                <CardTitle>Etapas do processamento</CardTitle>
                <p className="mt-1 text-sm text-secondary">
                  Etapa {etapaAtual + 1} de {etapas.length}
                </p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-5">
            {/* Barra de progresso — track surface-section, fill action-primary, height 6px */}
            <div className="overflow-hidden rounded-full bg-[rgb(var(--bg-input) / 1)]" style={{ height: 6 }}>
              <div
                className="h-full rounded-full bg-[rgb(var(--accent-primary))] transition-all duration-700 ease-out"
                style={{ width: `${progressPercent}%` }}
              />
            </div>

            {/* Checklist de etapas com ícones de status */}
            <div className="space-y-3">
              {etapas.map((etapa, index) => {
                const concluida = index < etapaAtual;
                const atual = index === etapaAtual;

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
          </CardContent>
        </Card>
    </DashboardPage>
  );
}
