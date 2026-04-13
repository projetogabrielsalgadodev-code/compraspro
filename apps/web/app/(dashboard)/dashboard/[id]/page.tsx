import type { Metadata } from "next";
import { createClient } from "@/lib/supabase/server";
import { DashboardPage } from "@/components/layout/DashboardPage";
import { DashboardAnaliticoClient } from "@/components/dashboard/DashboardAnaliticoClient";
import type { ItemOferta } from "@/types";

export const metadata: Metadata = {
  title: "Dashboard Analítico | Compras PRO",
  description: "Visão gráfica completa da análise de ofertas com indicadores de desempenho.",
};

export default async function DashboardAnaliticoPage({ params }: { params: { id: string } }) {
  const analiseId = params.id;
  let fornecedor = "Análise";
  let origem = "texto";
  let criadoEm = "";
  let itens: ItemOferta[] = [];

  try {
    const supabase = await createClient();

    const { data: analise } = await supabase
      .from("analises_oferta")
      .select("*")
      .eq("id", analiseId)
      .single();

    if (analise) {
      fornecedor = analise.fornecedor || "Fornecedor";
      origem = analise.origem || "texto";
      criadoEm = analise.created_at || "";

      const { data: itensRaw } = await supabase
        .from("itens_oferta")
        .select("*")
        .eq("analise_id", analiseId);

      itens = (itensRaw || []).map((item) => {
        const json = item.dados_json || {};
        return {
          id: item.id,
          ean: item.ean,
          descricao_original: item.descricao_bruta || json.descricao_original || "",
          descricao_produto: json.descricao_produto,
          preco_oferta: item.preco_oferta,
          menor_historico: item.menor_preco_historico,
          variacao_percentual: item.desconto_percentual,
          estoque_item: item.estoque_item,
          demanda_mes: item.demanda_mes,
          sugestao_pedido: item.sugestao_pedido,
          estoque_equivalentes: item.estoque_equivalentes,
          classificacao: item.classificacao || "atencao",
          confianca_match: item.confianca_match || "baixo",
          recomendacao: item.recomendacao || "",
          equivalente_detalhes: json.equivalentes || [],
          origem_menor_historico: item.origem_menor_historico,
          ...json,
        };
      });
    }
  } catch (e) {
    console.error("Erro ao buscar dados para dashboard:", e);
  }

  return (
    <DashboardPage
      titulo={`Dashboard: ${fornecedor}`}
      subtitulo={`Painel gráfico com indicadores da análise ${analiseId.slice(0, 8)}...`}
      eyebrow="Dashboard Analítico"
    >
      <DashboardAnaliticoClient
        analiseId={analiseId}
        fornecedor={fornecedor}
        origem={origem}
        criadoEm={criadoEm}
        itens={itens}
      />
    </DashboardPage>
  );
}
