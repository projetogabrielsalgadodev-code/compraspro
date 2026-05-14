"""
Regras de negócio — facade fina sobre o motor determinístico.

Centraliza a API estável usada por testes e callers externos sem expor o
detalhe interno do motor (analysis_engine).
"""
from __future__ import annotations

from app.services.analysis_engine import (
    calcular_sugestao_pedido as _calcular_sugestao_pedido,
    classificar_oferta as _classificar_oferta_engine,
)


def classificar_oferta(
    variacao: float | None,
    tem_estoque_equivalente: bool = False,
    *,
    vantagem_minima_percentual: float = 1.0,
    preco_oferta: float | None = None,
    media_historica: float | None = None,
    estoque_equivalentes: int | None = None,
    demanda_mes: float | None = None,
    horizonte_sugestao_meses: int = 3,
    considerar_equivalentes: bool = True,
) -> str:
    """
    Classifica uma oferta de acordo com a regra de negócio (AGENTS.md).

    Compatível com a assinatura antiga `classificar_oferta(variacao, tem_equivalente)`
    e também aceita os novos parâmetros granulares.

    Regras:
      - descartavel: preco_oferta > media_historica  (override explícito)
                     OU variacao < vantagem_minima_percentual
      - ouro:        variacao >= 20%
      - prata:       vantagem_minima <= variacao < 20%
      - atencao:     classificacao seria ouro/prata MAS há estoque equivalente
                     cobrindo o horizonte.
    """
    # Override: preço > média histórica → descartavel
    if preco_oferta is not None and media_historica is not None:
        if preco_oferta > media_historica:
            return "descartavel"

    # Se a chamada legada passou apenas `tem_estoque_equivalente=True`,
    # sintetizamos um cenário que dispara o caminho de cobertura.
    if estoque_equivalentes is None and demanda_mes is None:
        estoque_equivalentes = 999_999 if tem_estoque_equivalente else 0
        demanda_mes = 1.0  # garante cobertura > horizonte

    return _classificar_oferta_engine(
        variacao,
        estoque_equivalentes=int(estoque_equivalentes or 0),
        demanda_mes=float(demanda_mes or 0),
        horizonte_sugestao_meses=int(horizonte_sugestao_meses),
        vantagem_minima_percentual=float(vantagem_minima_percentual),
        considerar_equivalentes=bool(considerar_equivalentes),
    )


def sugestao_pedido(demanda_mes: float, estoque_atual: int, horizonte_meses: int = 3) -> int:
    """sugestao_pedido = max(0, demanda_mes * horizonte_meses - estoque_atual)"""
    return _calcular_sugestao_pedido(demanda_mes, estoque=estoque_atual, meses_cobertura=horizonte_meses)


_COBERTURA_THRESHOLDS = {"A": 12.0, "B": 6.0, "C": 3.0}


def precisa_repor(estoque_atual: int, demanda_mes: float, curva_abc: str | None = None) -> bool:
    """
    Decide se um produto precisa de reposição.

    Itens A: cobertura < 12 meses → repor (conservador, alta importância)
    Itens B: cobertura < 6 meses
    Itens C / default: cobertura < 3 meses
    """
    if demanda_mes <= 0:
        return False
    cobertura_meses = estoque_atual / demanda_mes
    threshold = _COBERTURA_THRESHOLDS.get((curva_abc or "").upper(), 3.0)
    return cobertura_meses < threshold
