"""
Agno Tools — Funções expostas como tools para o agente de análise de ofertas.

Cada tool faz queries diretas ao Supabase, recebendo empresa_id
via agent.session_state (injetado no momento da chamada).

Na versão 1.4.x do Agno, as tools recebem `agent` (instância do Agent)
como parâmetro especial, não RunContext.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from agno.agent import Agent

from app.db.supabase_client import get_supabase_client
from app.services.equivalencia import sao_equivalentes, slug_texto
from app.services.persistencia_service import (
    buscar_historico_por_ean,
    buscar_produto_por_ean,
    buscar_produtos,
    buscar_produtos_por_principio_ativo,
)
from app.services.preco_service import (
    calcular_media_historica,
    calcular_variacao_percentual,
    extremos_historicos,
)
from app.services.regras_negocio import classificar_oferta, sugestao_pedido

logger = logging.getLogger(__name__)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _get_empresa_id(agent: Agent) -> str:
    """Extrai empresa_id do session_state do agent."""
    state = agent.session_state or {}
    empresa_id = state.get("empresa_id")
    if not empresa_id:
        raise ValueError("empresa_id não encontrado no session_state do agente.")
    return empresa_id


def _safe_json(data: Any) -> str:
    """Serializa para JSON, lidando com tipos não-serializáveis."""
    return json.dumps(data, ensure_ascii=False, default=str)


# ─── Tool: Buscar produto por EAN ────────────────────────────────────────────

def buscar_produto_estoque(agent: Agent, ean: str) -> str:
    """Busca um produto no catálogo da empresa pelo código EAN/código de barras.
    Retorna: ean, descricao, principio_ativo, fabricante, estoque, demanda_mes.

    Args:
        ean: Código EAN / código de barras do produto.
    """
    empresa_id = _get_empresa_id(agent)
    client = get_supabase_client()
    produto = buscar_produto_por_ean(client, empresa_id, ean)
    if not produto:
        return _safe_json({"encontrado": False, "ean": ean})
    # Retorna apenas campos essenciais para evitar estouro de tokens
    return _safe_json({
        "encontrado": True,
        "ean": produto.get("ean"),
        "descricao": produto.get("descricao"),
        "principio_ativo": produto.get("principio_ativo"),
        "fabricante": produto.get("fabricante"),
        "estoque": produto.get("estoque"),
        "demanda_mes": produto.get("demanda_mes"),
        "curva_abc": produto.get("curva_abc"),
    })


# ─── Tool: Buscar histórico de preço ─────────────────────────────────────────

def consultar_historico_precos(agent: Agent, ean: str) -> str:
    """Consulta o histórico de preços pagos pela empresa para um produto pelo EAN.
    Retorna: menor_preco, maior_preco, media_preco e últimos 3 registros.

    Args:
        ean: Código EAN do produto para buscar histórico.
    """
    empresa_id = _get_empresa_id(agent)
    client = get_supabase_client()
    historico = buscar_historico_por_ean(client, empresa_id, ean)
    if not historico:
        return _safe_json({"ean": ean, "registros": 0})

    media = calcular_media_historica(historico)
    precos = [float(h["preco_unitario"]) for h in historico if h.get("preco_unitario") is not None]
    menor = min(precos) if precos else None
    maior = max(precos) if precos else None

    # Retorna apenas estatísticas + 3 registros recentes (sem campos verbosos)
    ultimos = [
        {"preco_unitario": h.get("preco_unitario"), "data_entrada": h.get("data_entrada")}
        for h in historico[:3]
    ]
    return _safe_json({
        "ean": ean,
        "registros": len(historico),
        "menor_preco": menor,
        "maior_preco": maior,
        "media_preco": round(media, 4) if media else None,
        "ultimos_registros": ultimos,
    })


# ─── Tool: Buscar equivalentes farmacêuticos ─────────────────────────────────

def buscar_equivalentes(agent: Agent, principio_ativo: str, ean_excluir: str | None = None) -> str:
    """Busca produtos equivalentes farmacêuticos pelo princípio ativo.
    Retorna estoque_total_equivalentes e até 3 equivalentes (ean, descricao, estoque).

    Args:
        principio_ativo: Princípio ativo do medicamento para buscar equivalentes.
        ean_excluir: EAN a excluir dos resultados (produto original).
    """
    empresa_id = _get_empresa_id(agent)
    client = get_supabase_client()
    produtos = buscar_produtos_por_principio_ativo(client, empresa_id, principio_ativo)

    if ean_excluir:
        produtos = [p for p in produtos if str(p.get("ean")) != str(ean_excluir)]

    estoque_total = sum(int(p.get("estoque") or 0) for p in produtos)
    # Apenas os 3 mais relevantes (com maior estoque)
    produtos_sorted = sorted(produtos, key=lambda p: int(p.get("estoque") or 0), reverse=True)
    equivalentes = [
        {"ean": p.get("ean"), "descricao": p.get("descricao"), "estoque": int(p.get("estoque") or 0)}
        for p in produtos_sorted[:3]
    ]
    return _safe_json({
        "principio_ativo": principio_ativo,
        "total_equivalentes": len(produtos),
        "estoque_total_equivalentes": estoque_total,
        "equivalentes": equivalentes,
    })


# ─── Tool: Buscar por descrição (fuzzy match) ────────────────────────────────

def buscar_produto_por_descricao(agent: Agent, descricao: str) -> str:
    """Busca um produto no catálogo usando correspondência por descrição/nome comercial.
    Use quando o EAN não está disponível ou não foi encontrado.
    Retorna apenas o melhor match com campos essenciais.

    Args:
        descricao: Descrição ou nome comercial do produto da oferta.
    """
    empresa_id = _get_empresa_id(agent)
    client = get_supabase_client()

    descricao_slug = slug_texto(descricao)
    tokens = set(descricao_slug.split())
    if not tokens:
        return _safe_json({"encontrado": False})

    best_tokens = sorted([t for t in tokens if len(t) > 2], key=len, reverse=True)
    if not best_tokens:
        return _safe_json({"encontrado": False})

    longest_token = best_tokens[0]

    # Limit to 50 candidates to reduce token usage
    response = (
        client.table("produtos")
        .select("ean, descricao, principio_ativo, fabricante, estoque, demanda_mes, curva_abc")
        .eq("empresa_id", empresa_id)
        .ilike("descricao", f"%{longest_token}%")
        .limit(50)
        .execute()
    )
    candidatos_produtos = response.data or []

    melhor_produto = None
    melhor_score = 0
    for produto in candidatos_produtos:
        desc_prod = slug_texto(produto.get("descricao") or "")
        score = len(tokens.intersection(set(desc_prod.split())))
        if score > melhor_score:
            melhor_score = score
            melhor_produto = produto

    if melhor_produto and melhor_score >= 4:
        confianca = "medio"
    elif melhor_produto and melhor_score >= 2:
        confianca = "baixo"
    else:
        return _safe_json({"encontrado": False})

    # Return only essential fields — NOT the full object
    return _safe_json({
        "encontrado": True,
        "confianca_match": confianca,
        "ean": melhor_produto.get("ean"),
        "descricao": melhor_produto.get("descricao"),
        "principio_ativo": melhor_produto.get("principio_ativo"),
        "fabricante": melhor_produto.get("fabricante"),
        "estoque": melhor_produto.get("estoque"),
        "demanda_mes": melhor_produto.get("demanda_mes"),
        "curva_abc": melhor_produto.get("curva_abc"),
    })


# ─── Tool: Classificar oferta ────────────────────────────────────────────────

def classificar_item_oferta(
    agent: Agent,
    preco_oferta: float,
    menor_historico: float | None = None,
    media_historica: float | None = None,
    estoque_item: int = 0,
    demanda_mes: float = 0,
    estoque_equivalentes: int = 0,
    horizonte_meses: int = 3,
) -> str:
    """Classifica uma oferta de fornecedor com base nas regras de negócio da empresa.
    Retorna classificação (ouro/prata/atencao/descartavel), sugestão de pedido e recomendação.

    Args:
        preco_oferta: Preço unitário ofertado pelo fornecedor.
        menor_historico: Menor preço histórico pago (pode ser None).
        media_historica: Média histórica de preço (pode ser None).
        estoque_item: Estoque atual do produto.
        demanda_mes: Demanda mensal do produto.
        estoque_equivalentes: Estoque total de equivalentes farmacêuticos.
        horizonte_meses: Horizonte em meses para sugestão de pedido (padrão: 3).
    """
    variacao = calcular_variacao_percentual(preco_oferta, menor_historico)

    classificacao = classificar_oferta(
        variacao or -100,
        estoque_equivalentes > 0,
        preco_oferta=preco_oferta,
        media_historica=media_historica,
    )

    sug_pedido = sugestao_pedido(demanda_mes, estoque_item, horizonte_meses)

    return _safe_json({
        "classificacao": classificacao,
        "variacao_percentual": variacao,
        "sugestao_pedido": sug_pedido,
        "estoque_item": estoque_item,
        "demanda_mes": demanda_mes,
        "estoque_equivalentes": estoque_equivalentes,
    })


# ─── Lista de tools para o agente ────────────────────────────────────────────

AGNO_TOOLS = [
    buscar_produto_estoque,
    consultar_historico_precos,
    buscar_equivalentes,
    buscar_produto_por_descricao,
    classificar_item_oferta,
]
