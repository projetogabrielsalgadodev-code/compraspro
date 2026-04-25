import type { Metadata } from "next";
import { ResultadoAnaliseClient } from "@/components/oferta/ResultadoAnaliseClient";
import { DashboardPage } from "@/components/layout/DashboardPage";
import { createClient } from "@/lib/supabase/server";
import type { RespostaAnaliseOferta, ItemOferta } from "@/types";

export const metadata: Metadata = {
  title: "Resultado da Análise | Compras PRO",
  description: "Resumo executivo e detalhamento por produto da análise de compras.",
};

export default async function ResultadoPage({ params }: { params: { id: string } }) {
  const analiseId = params.id;
  let dadosIniciais: RespostaAnaliseOferta | undefined = undefined;

  if (analiseId && analiseId !== "local") {
    try {
      const supabase = await createClient();
      
      const { data: analise } = await supabase
        .from("analises_oferta")
        .select("*")
        .eq("id", analiseId)
        .single();

      if (analise) {
        const { data: itens } = await supabase
          .from("itens_oferta")
          .select("*")
          .eq("analise_id", analiseId);

        // Check if we have items from the dedicated table
        const hasItensFromTable = itens && itens.length > 0;

        if (hasItensFromTable) {
          // Primary path: use structured data from itens_oferta table
          const counts = { ouro: 0, prata: 0, atencao: 0, descartavel: 0 };
          const itemsFormatados: ItemOferta[] = (itens || []).map((item) => {
            const json = item.dados_json || {};
            const classificacao = item.classificacao || "atencao";
            if (counts[classificacao as keyof typeof counts] !== undefined) {
               counts[classificacao as keyof typeof counts]++;
            }
            
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
              classificacao: classificacao,
              confianca_match: item.confianca_match || "baixo",
              recomendacao: item.recomendacao || "",
              equivalente_detalhes: json.equivalentes || [],
              origem_menor_historico: item.origem_menor_historico,
              ...json,
            };
          });

          dadosIniciais = {
            analise_id: analise.id,
            fornecedor: analise.fornecedor || "Fornecedor",
            origem: analise.origem,
            status: analise.status || "pendente",
            resumo: {
              itens_analisados: itemsFormatados.length,
              oportunidades: counts.ouro + counts.prata,
              sem_necessidade: counts.descartavel,
              revisar: counts.atencao,
            },
            itens: itemsFormatados,
            tempo_processamento_ms: analise.tempo_processamento_ms || null,
            tokens_utilizados: analise.tokens_utilizados || null,
            custo_reais: analise.custo_reais ? parseFloat(analise.custo_reais) : null,
          };
        } else if (analise.resultado_json) {
          // Fallback: use resultado_json blob (items persistence may have failed)
          const resultBlob = analise.resultado_json as Record<string, unknown>;
          const blobItens = (resultBlob.itens || []) as ItemOferta[];
          const blobResumo = resultBlob.resumo as Record<string, number> | undefined;

          // Recount classifications from actual items for accurate summary
          const recounted = { ouro: 0, prata: 0, atencao: 0, descartavel: 0 };
          for (const it of blobItens) {
            const cls = it.classificacao;
            if (cls && recounted[cls as keyof typeof recounted] !== undefined) {
              recounted[cls as keyof typeof recounted]++;
            }
          }

          dadosIniciais = {
            analise_id: analise.id,
            fornecedor: (resultBlob.fornecedor as string) || analise.fornecedor || "Fornecedor",
            origem: analise.origem,
            status: analise.status || "pendente",
            resumo: blobResumo ? {
              itens_analisados: blobResumo.itens_analisados || blobItens.length,
              oportunidades: blobResumo.oportunidades || (recounted.ouro + recounted.prata),
              sem_necessidade: blobResumo.sem_necessidade || recounted.descartavel,
              revisar: blobResumo.revisar || recounted.atencao,
            } : {
              itens_analisados: blobItens.length,
              oportunidades: recounted.ouro + recounted.prata,
              sem_necessidade: recounted.descartavel,
              revisar: recounted.atencao,
            },
            itens: blobItens,
            tempo_processamento_ms: analise.tempo_processamento_ms || null,
            tokens_utilizados: analise.tokens_utilizados || null,
            custo_reais: analise.custo_reais ? parseFloat(analise.custo_reais) : null,
          };
        }
      }
    } catch (e) {
      console.error("Erro ao buscar dados no servidor:", e);
    }
  }

  return (
    <DashboardPage 
      titulo={dadosIniciais?.fornecedor ? `Análise: ${dadosIniciais.fornecedor}` : "Resultado da analise"}
      subtitulo={`Analise ${params.id} com resumo executivo e detalhamento por produto.`} 
      eyebrow="Resultado executivo">
      <ResultadoAnaliseClient analiseId={params.id} dadosIniciais={dadosIniciais} />
    </DashboardPage>
  );
}
