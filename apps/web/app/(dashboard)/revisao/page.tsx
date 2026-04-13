"use client";

import { useState } from "react";
import { ScanSearch } from "lucide-react";
import { DashboardPage } from "@/components/layout/DashboardPage";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { ConfiancaMatch } from "@/types";

type FiltroRevisao = "todos" | "encontrados" | "baixa-confianca" | "nao-encontrados";

/* Mock data para demonstração — será substituído por dados reais da API */
const itensMock = [
  { id: 1, textoOriginal: "Dipirona sódica 500mg 10ml R$ 8,90", correspondencia: "Dipirona sódica 500mg/ml - genérico - 10ml", confianca: "alto" as ConfiancaMatch, status: "encontrados" as const },
  { id: 2, textoOriginal: "Omeprazol 20mg c/28 R$ 15,00", correspondencia: "Omeprazol 20mg - 28 cápsulas", confianca: "medio" as ConfiancaMatch, status: "encontrados" as const },
  { id: 3, textoOriginal: "Vitamina C efferv 1g R$ 22,90", correspondencia: "Vitamina C 1g efervescente - 10 comprimidos", confianca: "baixo" as ConfiancaMatch, status: "baixa-confianca" as const },
  { id: 4, textoOriginal: "Produto XYZ 123 R$ 45,00", correspondencia: null, confianca: "baixo" as ConfiancaMatch, status: "nao-encontrados" as const },
];

const filtros: { key: FiltroRevisao; label: string; count: number }[] = [
  { key: "todos", label: "Todos", count: itensMock.length },
  { key: "encontrados", label: "Encontrados", count: itensMock.filter((i) => i.status === "encontrados").length },
  { key: "baixa-confianca", label: "Baixa confiança", count: itensMock.filter((i) => i.status === "baixa-confianca").length },
  { key: "nao-encontrados", label: "Não encontrados", count: itensMock.filter((i) => i.status === "nao-encontrados").length },
];

const confiancaConfig: Record<ConfiancaMatch, { label: string; variant: "success" | "warning" | "danger" }> = {
  alto: { label: "Alta confiança", variant: "success" },
  medio: { label: "Média confiança", variant: "warning" },
  baixo: { label: "Baixa confiança", variant: "danger" },
};

/* C-18: Chips de filtro + badges de confiança conforme design system */
export default function RevisaoPage() {
  const [filtroAtivo, setFiltroAtivo] = useState<FiltroRevisao>("todos");
  const [feedbackSalvo, setFeedbackSalvo] = useState<number | null>(null);

  const itensFiltrados = filtroAtivo === "todos"
    ? itensMock
    : itensMock.filter((item) => item.status === filtroAtivo);

  const handleSalvarCorrecao = (id: number) => {
    setFeedbackSalvo(id);
    setTimeout(() => setFeedbackSalvo(null), 4000);
  };

  return (
    <DashboardPage titulo="Revisar leitura" subtitulo="Confirme itens com baixa confiança antes da análise final." eyebrow="Validação manual">
      {/* Chips de filtro */}
      <div className="flex flex-wrap gap-2">
        {filtros.map((filtro) => (
          <button
            key={filtro.key}
            type="button"
            onClick={() => setFiltroAtivo(filtro.key)}
            className={`inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-sm font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primaria focus-visible:ring-offset-2 focus-visible:ring-offset-fundo ${
              filtroAtivo === filtro.key
                ? "bg-[linear-gradient(135deg,rgb(var(--accent-primary) / 1),rgb(var(--accent-primary) / 0.88))] text-white shadow-primario"
                : "border border-app bg-[linear-gradient(180deg,var(--surface-highlight),rgb(var(--bg-input) / 0.92))] text-secondary hover:border-app-strong hover:text-texto"
            }`}
          >
            {filtro.label}
            <span className={`inline-flex h-5 min-w-5 items-center justify-center rounded-full px-1.5 text-xs font-bold ${
              filtroAtivo === filtro.key ? "bg-white/20 text-white" : "bg-surface-subtle text-muted-app"
            }`}>
              {filtro.count}
            </span>
          </button>
        ))}
      </div>

      {/* Lista de itens */}
      {itensFiltrados.map((item) => (
        <Card key={item.id}>
          <CardHeader>
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <span className="ds-icon-chip text-primariaapp"><ScanSearch className="h-4 w-4" /></span>
                <CardTitle>Item {item.id}</CardTitle>
              </div>
              {/* Badge de confiança */}
              <Badge variant={confiancaConfig[item.confianca].variant}>
                {confiancaConfig[item.confianca].label}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-secondary">
            <div className="ds-subpanel rounded-[20px] px-4 py-3">
              <p className="text-xs uppercase tracking-wide text-muted-app">Texto original</p>
              <p className="mt-1 text-texto">{item.textoOriginal}</p>
            </div>
            {item.correspondencia ? (
              <div className="ds-subpanel rounded-[20px] px-4 py-3">
                <p className="text-xs uppercase tracking-wide text-muted-app">Correspondência sugerida</p>
                <p className="mt-1 text-texto">{item.correspondencia}</p>
              </div>
            ) : (
              <div className="rounded-[20px] border border-descartavel/20 bg-descartavel-claro/10 px-4 py-3">
                <p className="text-sm font-medium text-descartavel">Nenhuma correspondência encontrada</p>
              </div>
            )}
            <div className="flex items-center gap-3">
              <div className="flex gap-2">
                <Button variant="secondary" onClick={() => handleSalvarCorrecao(item.id)}>Corrigir</Button>
                <Button variant="secondary" onClick={() => handleSalvarCorrecao(item.id)}>Trocar item</Button>
                {!item.correspondencia && <Button onClick={() => handleSalvarCorrecao(item.id)}>Cadastrar novo</Button>}
              </div>
              {feedbackSalvo === item.id && (
                <span className="animate-in fade-in zoom-in text-xs font-medium text-ouro">
                  Correspondência salva! O Compras PRO lembrará disso.
                </span>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </DashboardPage>
  );
}
