"use client";

import { useState } from "react";
import Link from "next/link";
import { ChevronDown, ChevronUp, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { OfferBadge } from "@/components/oferta/OfferBadge";
import { formatarMoeda, formatarPercentual } from "@/lib/utils";
import { EquivalentsList } from "@/components/oferta/EquivalentsList";
import type { ItemOferta } from "@/types";

const borderClassByClassification = {
  ouro: "border-l-4 border-l-ouro",
  prata: "border-l-4 border-l-prata",
  atencao: "border-l-4 border-l-atencao",
  descartavel: "border-l-4 border-l-descartavel"
} as const;

/* C-28: Cor da variação de preço baseada no valor */
function corVariacao(variacao?: number | null) {
  if (variacao == null) return "text-secondary";
  if (variacao > 0) return "text-ouro"; // desconto — preço abaixo do histórico
  if (variacao >= -10) return "text-prata"; // ágio pequeno — até 10% acima
  return "text-descartavel"; // ágio alto — >10% acima
}

export function OfferCard({ item, analiseId }: { item: ItemOferta; analiseId?: string }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <Card className={`surface-highlight surface-orb overflow-hidden ${borderClassByClassification[item.classificacao]}`}>
      {/* C-11: Adicionado focus-visible com ring-offset para acessibilidade por teclado */}
      <button
        className="w-full rounded-[inherit] p-5 text-left transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primaria focus-visible:ring-offset-2 focus-visible:ring-offset-fundo"
        onClick={() => setExpanded((current) => !current)}
      >
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-3">
            <OfferBadge classification={item.classificacao} />
            <div>
              <p className="text-base font-semibold text-texto">{item.descricao_produto ?? item.descricao_original}</p>
              <p className="text-sm text-secondary">{item.descricao_original}</p>
            </div>
          </div>
          {expanded ? <ChevronUp className="h-5 w-5 text-muted-app" /> : <ChevronDown className="h-5 w-5 text-muted-app" />}
        </div>
        <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-wide text-muted-app">Preço da oferta</p>
            <p className="text-2xl font-bold text-texto">{formatarMoeda(item.preco_oferta)}</p>
          </div>
          <div className="text-right">
            <p className="text-xs uppercase tracking-wide text-muted-app">Var. vs histórico</p>
            {/* C-28: Variação colorida por status */}
            <p className={`text-sm font-semibold ${corVariacao(item.variacao_percentual)}`}>{formatarPercentual(item.variacao_percentual)}</p>
          </div>
        </div>
      </button>

      {expanded ? (
        <div className="border-t border-app px-5 pb-5 pt-4">
          <div className="grid gap-3 text-sm sm:grid-cols-2">
            <DataRow label="EAN" value={item.ean ?? "Não identificado"} />
            <DataRow label="Confiança" value={item.confianca_match} />
            <DataRow label="Menor histórico" value={formatarMoeda(item.menor_historico)} />
            <DataRow label="Origem histórico" value={item.origem_menor_historico ?? "--"} />
            <DataRow label="Estoque item" value={String(item.estoque_item ?? 0)} />
            <DataRow label="Demanda mês" value={String(item.demanda_mes ?? 0)} />
            <DataRow label="Sugestão pedido" value={String(item.sugestao_pedido ?? 0)} />
            <DataRow label="Estoque equivalentes" value={String(item.estoque_equivalentes ?? 0)} />
          </div>
          <div className="mt-4 rounded-[22px] border border-app bg-[linear-gradient(135deg,rgb(var(--accent-primary) / 0.08),var(--surface-highlight))] p-4 shadow-[inset_0_1px_0_var(--surface-inset)]">
            <p className="text-xs uppercase tracking-wide text-muted-app">Recomendação</p>
            <p className="mt-1 text-sm text-texto">{item.recomendacao}</p>
          </div>
          <div className="mt-4">
            <p className="mb-3 text-sm font-semibold text-texto">Equivalentes</p>
            <EquivalentsList items={item.equivalente_detalhes} />
          </div>
          <div className="mt-4 flex gap-2">
            <Button asChild variant="secondary" className="gap-2">
              <Link href={`/item/${item.id ?? item.ean ?? 'detalhe'}${analiseId ? `?analise=${analiseId}` : ''}`}>
                <ExternalLink className="h-4 w-4" />
                Ver detalhe completo
              </Link>
            </Button>
          </div>
        </div>
      ) : null}
    </Card>
  );
}

/* C-32: Substituído bg-white/5 por bg-surface-subtle (token tema-adaptável) */
function DataRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between rounded-2xl border border-app bg-surface-subtle px-3 py-3">
      <span className="text-secondary">{label}</span>
      <span className="font-medium text-texto">{value}</span>
    </div>
  );
}
