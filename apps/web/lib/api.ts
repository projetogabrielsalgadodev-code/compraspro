import { z } from "zod";

const itemOfertaSchema = z.object({
  id: z.string().optional(),
  ean: z.string().nullable().optional(),
  descricao_original: z.string(),
  descricao_produto: z.string().nullable().optional(),
  preco_oferta: z.number(),
  classificacao: z.enum(["ouro", "prata", "atencao", "descartavel"]),
  confianca_match: z.enum(["alto", "medio", "baixo"]),
  recomendacao: z.string(),
  menor_historico: z.number().nullable().optional(),
  origem_menor_historico: z.string().nullable().optional(),
  variacao_percentual: z.number().nullable().optional(),
  estoque_item: z.number().nullable().optional(),
  demanda_mes: z.number().nullable().optional(),
  sugestao_pedido: z.number().nullable().optional(),
  estoque_equivalentes: z.number().nullable().optional(),
  equivalente_detalhes: z.array(
    z.object({
      descricao: z.string(),
      fabricante: z.string().nullable().optional(),
      estoque: z.number().nullable().optional()
    })
  ).optional()
});

export const respostaAnaliseSchema = z.object({
  analise_id: z.string().nullable().optional(),
  fornecedor: z.string().nullable().optional(),
  origem: z.string().optional().default("texto"),
  resumo: z.object({
    itens_analisados: z.number(),
    oportunidades: z.number(),
    sem_necessidade: z.number(),
    revisar: z.number()
  }),
  itens: z.array(itemOfertaSchema)
});

export type RespostaAnaliseOferta = z.infer<typeof respostaAnaliseSchema>;

export const configuracaoEmpresaSchema = z.object({
  id: z.string().nullable().optional(),
  empresa_id: z.string(),
  estoque_minimo_dias: z.number(),
  estoque_alto_dias: z.number(),
  vantagem_minima_percentual: z.number(),
  metodo_comparacao: z.enum(["average", "median", "lowest"]),
  considerar_equivalentes: z.boolean(),
  horizonte_sugestao_meses: z.number(),
  usar_demanda_mes_sugcompra: z.boolean(),
  exibir_extremos_historicos: z.boolean(),
  created_at: z.string().nullable().optional(),
  updated_at: z.string().nullable().optional()
});

export type ConfiguracaoEmpresa = z.infer<typeof configuracaoEmpresaSchema>;

const FASTAPI_URL = process.env.FASTAPI_URL ?? "http://localhost:8000";

export async function analisarOferta(payload: { texto_bruto: string; empresa_id?: string | null }) {
  const response = await fetch(`${FASTAPI_URL}/api/ofertas/analisar`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload),
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error("Falha ao analisar oferta.");
  }

  const data = await response.json();
  return respostaAnaliseSchema.parse(data);
}

export async function buscarConfiguracaoEmpresa(empresaId: string) {
  const response = await fetch(`/api/configuracoes/empresa?empresa_id=${encodeURIComponent(empresaId)}`, {
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error("Falha ao carregar configuracoes.");
  }

  return configuracaoEmpresaSchema.parse(await response.json());
}

export async function salvarConfiguracaoEmpresa(payload: ConfiguracaoEmpresa) {
  const response = await fetch("/api/configuracoes/empresa", {
    method: "PUT",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error("Falha ao salvar configuracoes.");
  }

  return configuracaoEmpresaSchema.parse(await response.json());
}
