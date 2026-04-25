from __future__ import annotations

from typing import Any

from supabase import Client

from app.models.schemas import (
    AnaliseCreate,
    AnaliseItemCreate,
    ConfiguracaoEmpresaResponse,
    ConfiguracaoEmpresaUpdate,
    EntradaImportada,
    ProdutoImportado,
)


import logging as _logging

_ps_logger = _logging.getLogger(__name__)

_PAGE_SIZE = 1000  # Supabase PostgREST default limit


# ─── Produtos & Estoque ──────────────────────────────────────────────────────

def buscar_produtos(client: Client, empresa_id: str) -> list[dict[str, Any]]:
    """Busca todos os produtos da empresa com paginação automática."""
    all_rows: list[dict[str, Any]] = []
    offset = 0
    while True:
        response = (
            client.table("produtos")
            .select("id, ean, descricao, principio_ativo, fabricante, estoque, demanda_mes, curva_abc")
            .eq("empresa_id", empresa_id)
            .range(offset, offset + _PAGE_SIZE - 1)
            .execute()
        )
        batch = response.data or []
        all_rows.extend(batch)
        if len(batch) < _PAGE_SIZE:
            break
        offset += _PAGE_SIZE
    _ps_logger.info(f"buscar_produtos: {len(all_rows)} produtos carregados para empresa {empresa_id[:8]}...")
    return all_rows


def buscar_produto_por_ean(client: Client, empresa_id: str, ean: str) -> dict[str, Any] | None:
    """Busca um produto pelo EAN. Retorna None se não encontrado."""
    response = (
        client.table("produtos")
        .select("id, ean, descricao, principio_ativo, fabricante, estoque, demanda_mes, curva_abc")
        .eq("empresa_id", empresa_id)
        .eq("ean", ean)
        .limit(1)
        .execute()
    )
    data = response.data or []
    return data[0] if data else None


def buscar_produtos_por_principio_ativo(
    client: Client, empresa_id: str, principio_ativo: str
) -> list[dict[str, Any]]:
    """Busca todos produtos com o mesmo princípio ativo (equivalentes farmacêuticos)."""
    response = (
        client.table("produtos")
        .select("id, ean, descricao, principio_ativo, fabricante, estoque, demanda_mes")
        .eq("empresa_id", empresa_id)
        .ilike("principio_ativo", f"%{principio_ativo}%")
        .limit(100)
        .execute()
    )
    return response.data or []


# ─── Histórico de Preços ─────────────────────────────────────────────────────

def buscar_historico(client: Client, empresa_id: str) -> dict[str, list[dict[str, Any]]]:
    """Busca todo o histórico de preços da empresa com paginação automática."""
    all_rows: list[dict[str, Any]] = []
    offset = 0
    while True:
        response = (
            client.table("historico_precos")
            .select("ean, preco_unitario, fornecedor, data_entrada")
            .eq("empresa_id", empresa_id)
            .range(offset, offset + _PAGE_SIZE - 1)
            .execute()
        )
        batch = response.data or []
        all_rows.extend(batch)
        if len(batch) < _PAGE_SIZE:
            break
        offset += _PAGE_SIZE
    _ps_logger.info(f"buscar_historico: {len(all_rows)} registros carregados para empresa {empresa_id[:8]}...")
    historico: dict[str, list[dict[str, Any]]] = {}
    for item in all_rows:
        historico.setdefault(str(item.get("ean")), []).append(item)
    return historico


def buscar_historico_por_ean(
    client: Client, empresa_id: str, ean: str
) -> list[dict[str, Any]]:
    """Busca histórico de preços de um EAN específico."""
    response = (
        client.table("historico_precos")
        .select("ean, preco_unitario, data_entrada")
        .eq("empresa_id", empresa_id)
        .eq("ean", ean)
        .order("data_entrada", desc=True)
        .limit(10)
        .execute()
    )
    return response.data or []


# ─── Importação de dados ─────────────────────────────────────────────────────

def upsert_produtos(client: Client, empresa_id: str, itens: list[ProdutoImportado]) -> int:
    payload = [
        {
            "empresa_id": empresa_id,
            "ean": item.ean,
            "descricao": item.descricao,
            "principio_ativo": item.principio_ativo,
            "fabricante": item.fabricante,
            "fabricante_bruto": item.fabricante_bruto,
            "estoque": item.estoque,
            "demanda_mes": item.demanda_mes,
            "curva_abc": item.curva_abc,
            "grupo": item.grupo,
        }
        for item in itens
    ]
    if not payload:
        return 0
    client.table("produtos").upsert(payload, on_conflict="empresa_id,ean").execute()
    return len(payload)


def inserir_historico(client: Client, empresa_id: str, itens: list[EntradaImportada]) -> int:
    payload = [
        {
            "empresa_id": empresa_id,
            "ean": item.ean,
            "data_entrada": item.data_entrada,
            "quantidade_unitaria": item.quantidade_unitaria,
            "valor_total_item": item.valor_total_item,
            "valor_icms_st": item.valor_icms_st,
            "valor_outras_despesas": item.valor_outras_despesas,
            "fornecedor": item.fornecedor,
        }
        for item in itens
    ]
    if not payload:
        return 0
    client.table("historico_precos").insert(payload).execute()
    return len(payload)


# ─── Configuração de Empresa ─────────────────────────────────────────────────

def buscar_configuracao_empresa(client: Client, empresa_id: str) -> ConfiguracaoEmpresaResponse | None:
    response = (
        client.table("configuracoes_empresa")
        .select(
            "id, empresa_id, estoque_minimo_dias, estoque_alto_dias, vantagem_minima_percentual, metodo_comparacao, considerar_equivalentes, horizonte_sugestao_meses, usar_demanda_mes_sugcompra, exibir_extremos_historicos, created_at, updated_at"
        )
        .eq("empresa_id", empresa_id)
        .limit(1)
        .execute()
    )
    data = response.data or []
    if not data:
        return None
    return ConfiguracaoEmpresaResponse(**data[0])


def upsert_configuracao_empresa(client: Client, payload: ConfiguracaoEmpresaUpdate) -> ConfiguracaoEmpresaResponse:
    response = (
        client.table("configuracoes_empresa")
        .upsert(payload.model_dump(), on_conflict="empresa_id")
        .execute()
    )
    data = response.data or []
    if data:
        return ConfiguracaoEmpresaResponse(**data[0])

    configuracao = buscar_configuracao_empresa(client, payload.empresa_id)
    if configuracao is None:
        raise ValueError("Nao foi possivel carregar a configuracao da empresa apos o salvamento.")
    return configuracao


# ─── Persistência de Análise ─────────────────────────────────────────────────

def salvar_analise(client: Client, analise: AnaliseCreate) -> str:
    """Cria um registro de análise e retorna o ID gerado."""
    response = (
        client.table("analises_oferta")
        .insert(analise.model_dump())
        .execute()
    )
    data = response.data or []
    if not data:
        raise ValueError("Falha ao salvar análise no Supabase.")
    return str(data[0]["id"])


def salvar_itens_analise(client: Client, itens: list[AnaliseItemCreate]) -> int:
    """Persiste os itens de uma análise concluída."""
    payload = [item.model_dump() for item in itens]
    if not payload:
        return 0
    client.table("itens_oferta").insert(payload).execute()
    return len(payload)


def buscar_analises_empresa(
    client: Client, empresa_id: str, limite: int = 20
) -> list[dict[str, Any]]:
    """Lista análises recentes de uma empresa."""
    response = (
        client.table("analises_oferta")
        .select("id, fornecedor, origem, status, created_at")
        .eq("empresa_id", empresa_id)
        .order("created_at", desc=True)
        .limit(limite)
        .execute()
    )
    return response.data or []
