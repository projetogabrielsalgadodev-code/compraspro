from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


ClassificacaoOferta = Literal["ouro", "prata", "atencao", "descartavel"]
ConfiancaMatch = Literal["alto", "medio", "baixo"]


class ItemExtraido(BaseModel):
    descricao: str
    ean: str | None = None
    preco_oferta: float
    unidade: str | None = None
    quantidade_por_caixa: int | None = None


class ExtracaoOferta(BaseModel):
    fornecedor: str | None = None
    items: list[ItemExtraido] = Field(default_factory=list)


class OfertaAnalyzeRequest(BaseModel):
    texto_bruto: str
    empresa_id: str | None = None
    usuario_id: str | None = None
    fornecedor_informado: str | None = None


class ConfiguracaoEmpresaBase(BaseModel):
    estoque_minimo_dias: int = 30
    estoque_alto_dias: int = 90
    vantagem_minima_percentual: float = 5
    metodo_comparacao: Literal["average", "median", "lowest"] = "average"
    considerar_equivalentes: bool = True
    horizonte_sugestao_meses: int = 3
    usar_demanda_mes_sugcompra: bool = True
    exibir_extremos_historicos: bool = True


class ConfiguracaoEmpresaUpdate(ConfiguracaoEmpresaBase):
    empresa_id: str


class ConfiguracaoEmpresaResponse(ConfiguracaoEmpresaBase):
    id: str | None = None
    empresa_id: str
    created_at: str | None = None
    updated_at: str | None = None


class EquivalenteResumo(BaseModel):
    descricao: str
    ean: str | None = None
    fabricante: str | None = None
    estoque: int | None = None
    menor_preco: float | None = None
    media_preco: float | None = None
    qtd_entradas: int | None = None
    demanda_mes: float | None = None


class HistoricoPrecoResumo(BaseModel):
    preco_unitario: float
    fornecedor: str | None = None
    data_entrada: str | None = None
    ean: str | None = None
    descricao_produto: str | None = None


class ItemOfertaResponse(BaseModel):
    ean: str | None = None
    descricao_original: str
    descricao_produto: str | None = None
    preco_oferta: float | None = None
    preco_oferta_caixa: float | None = None
    multiplicador_embalagem: float | None = None
    menor_historico: float = 0.0
    origem_menor_historico: str | None = None
    variacao_percentual: float = 0.0
    estoque_item: int = 0
    demanda_mes: float = 0.0
    sugestao_pedido: int = 0
    estoque_equivalentes: int = 0
    classificacao: ClassificacaoOferta
    confianca_match: ConfiancaMatch
    recomendacao: str
    tipo_preco: str | None = None
    desconto_percentual: float | None = None
    equivalente_detalhes: list[EquivalenteResumo] = Field(default_factory=list)
    historico_menores: list[HistoricoPrecoResumo] = Field(default_factory=list)
    historico_maiores: list[HistoricoPrecoResumo] = Field(default_factory=list)


class ResumoAnalise(BaseModel):
    itens_analisados: int
    oportunidades: int
    sem_necessidade: int
    revisar: int


class OfertaAnalyzeResponse(BaseModel):
    analise_id: str | None = None
    fornecedor: str | None = None
    origem: str = "texto"
    resumo: ResumoAnalise
    itens: list[ItemOfertaResponse]
    tempo_processamento_ms: int | None = None
    tokens_utilizados: int | None = None
    custo_reais: float | None = None


class ProdutoImportado(BaseModel):
    ean: str
    descricao: str | None = None
    principio_ativo: str | None = None
    fabricante_bruto: str | None = None
    fabricante: str | None = None
    estoque: int = 0
    demanda_mes: float | None = None
    curva_abc: str | None = None
    grupo: str | None = None


class EntradaImportada(BaseModel):
    ean: str
    data_entrada: str
    quantidade_unitaria: float
    valor_total_item: float
    valor_icms_st: float = 0
    valor_outras_despesas: float = 0
    fornecedor: str | None = None


# ─── Novos schemas para persistência de análise ───────────────────────────────

class AnaliseCreate(BaseModel):
    """Payload para persistência de uma análise concluída no Supabase."""
    empresa_id: str
    usuario_id: str | None = None
    fornecedor: str | None = None
    origem: str = "texto"
    entrada_bruta: str | None = None
    status: str = "concluida"
    tempo_processamento_ms: int | None = None
    tokens_utilizados: int | None = None
    custo_reais: float | None = None
    created_at: str | None = None


class AnaliseItemCreate(BaseModel):
    """Payload para persistência de cada item de uma análise no Supabase."""
    analise_id: str
    ean: str | None = None
    produto_id: str | None = None
    descricao_bruta: str | None = None
    preco_oferta: float | None = None
    menor_preco_historico: float | None = None
    origem_menor_historico: str | None = None
    desconto_percentual: float | None = None
    estoque_item: int | None = None
    demanda_mes: float | None = None
    sugestao_pedido: int | None = None
    estoque_equivalentes: int | None = None
    classificacao: str | None = None
    confianca_match: str | None = None
    recomendacao: str | None = None
    dados_json: dict[str, Any] = Field(default_factory=dict)
    created_at: str | None = None


# ─── Schema de saída estruturada do Agno Agent ────────────────────────────────

class ItemAnaliseAgno(BaseModel):
    """Resultado da análise de um item individual pelo agente Agno."""
    model_config = {"extra": "ignore"}  # Ignore extra fields from engine output

    ean: str | None = Field(None, description="EAN do produto identificado")
    descricao_original: str = Field(description="Descrição original do item na oferta")
    descricao_produto: str | None = Field(None, description="Descrição do produto no catálogo")
    preco_oferta: float | None = Field(None, description="Preço ofertado normalizado por unidade (None para ofertas com desconto %)")
    preco_oferta_caixa: float | None = Field(None, description="Preço original da caixa/embalagem conforme enviado pelo fornecedor")
    multiplicador_embalagem: float | None = Field(None, description="Qtd de unidades na embalagem (ex: 14 comprimidos)")
    menor_historico: float | None = Field(None, description="Menor preço histórico pago")
    variacao_percentual: float | None = Field(None, description="Variação % vs menor histórico (positivo = desconto)")
    estoque_item: int = Field(0, description="Estoque atual do produto")
    demanda_mes: float = Field(0, description="Demanda mensal do produto")
    sugestao_pedido: int = Field(0, description="Quantidade sugerida de compra")
    estoque_equivalentes: int = Field(0, description="Estoque total de equivalentes farmacêuticos")
    classificacao: ClassificacaoOferta = Field(description="Classificação: ouro/prata/atencao/descartavel")
    confianca_match: ConfiancaMatch = Field(description="Confiança do match: alto (EAN), medio (descrição), baixo (aproximado)")
    recomendacao: str = Field(description="Recomendação textual para o comprador (1-2 frases, pt-BR)")
    equivalentes: list[EquivalenteResumo] = Field(default_factory=list, description="Equivalentes farmacêuticos encontrados")
    origem_menor_historico: str | None = Field(None, description="= (direto) ou != (via equivalente)")
    tipo_preco: str | None = Field(None, description="absoluto, percentual_desconto, ou sem_preco")
    desconto_percentual: float | None = Field(None, description="Percentual de desconto quando tipo_preco=percentual_desconto")


class AnaliseOfertaAgnoOutput(BaseModel):
    """Schema de saída estruturada do agente Agno para análise de oferta."""
    fornecedor: str | None = Field(None, description="Nome do fornecedor identificado na oferta")
    itens: list[ItemAnaliseAgno] = Field(description="Lista de itens analisados")
