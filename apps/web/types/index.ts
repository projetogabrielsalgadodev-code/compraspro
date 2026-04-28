export type ClassificacaoOferta = "ouro" | "prata" | "atencao" | "descartavel";
export type ConfiancaMatch = "alto" | "medio" | "baixo";

export interface EquivalenteResumo {
  descricao: string;
  fabricante?: string | null;
  estoque?: number | null;
}

export interface ItemOferta {
  id?: string;
  ean?: string | null;
  descricao_original: string;
  descricao_produto?: string | null;
  preco_oferta?: number | null;
  preco_oferta_caixa?: number | null;
  multiplicador_embalagem?: number | null;
  classificacao: ClassificacaoOferta;
  confianca_match: ConfiancaMatch;
  recomendacao: string;
  menor_historico?: number | null;
  origem_menor_historico?: string | null;
  variacao_percentual?: number | null;
  estoque_item?: number | null;
  demanda_mes?: number | null;
  sugestao_pedido?: number | null;
  estoque_equivalentes?: number | null;
  equivalente_detalhes?: EquivalenteResumo[];
  tipo_preco?: string | null;
  desconto_percentual?: number | null;
}

export interface ResumoAnaliseOferta {
  itens_analisados: number;
  oportunidades: number;
  sem_necessidade: number;
  revisar: number;
}

export interface RespostaAnaliseOferta {
  analise_id?: string | null;
  fornecedor?: string | null;
  origem?: string;
  status?: string;
  resumo: ResumoAnaliseOferta;
  itens: ItemOferta[];
  tempo_processamento_ms?: number | null;
  tokens_utilizados?: number | null;
  custo_reais?: number | null;
}

export type MetodoComparacao = "average" | "median" | "lowest";

export interface ConfiguracaoEmpresa {
  id?: string | null;
  empresa_id: string;
  estoque_minimo_dias: number;
  estoque_alto_dias: number;
  vantagem_minima_percentual: number;
  metodo_comparacao: MetodoComparacao;
  considerar_equivalentes: boolean;
  horizonte_sugestao_meses: number;
  usar_demanda_mes_sugcompra: boolean;
  exibir_extremos_historicos: boolean;
  created_at?: string | null;
  updated_at?: string | null;
}
