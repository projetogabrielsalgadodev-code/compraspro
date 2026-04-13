import type { Metadata } from "next";
import { AnaliseHistoricaMock } from "@/components/historico/AnaliseHistoricaMock";
import { DashboardPage } from "@/components/layout/DashboardPage";

export const metadata: Metadata = {
  title: "Histórico Detalhado | Compras PRO",
  description: "Painel detalhado da análise com comparativos, prioridades e sugestões de compra.",
};

export default function HistoricoDetalhePage({ params }: { params: { id: string } }) {
  return (
    <DashboardPage
      titulo="Analise historica"
      subtitulo={`Painel detalhado da analise ${params.id} com comparativos, prioridades e sugestoes de compra.`}
      eyebrow="Historico detalhado"
    >
      <AnaliseHistoricaMock analiseId={params.id} />
    </DashboardPage>
  );
}
