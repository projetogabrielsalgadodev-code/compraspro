from __future__ import annotations


COVERAGE_DAYS = {"A": 30, "B": 15, "C": 5}


def classificar_oferta(
    desconto_percentual: float,
    possui_estoque_equivalente: bool,
    preco_oferta: float | None = None,
    media_historica: float | None = None,
    vantagem_minima_percentual: float = 1,
) -> str:
    if preco_oferta is not None and media_historica is not None and preco_oferta > media_historica:
        return "descartavel"
    if desconto_percentual >= 20 and not possui_estoque_equivalente:
        return "ouro"
    if vantagem_minima_percentual <= desconto_percentual < 20 and not possui_estoque_equivalente:
        return "prata"
    if desconto_percentual >= vantagem_minima_percentual and possui_estoque_equivalente:
        return "atencao"
    return "descartavel"


def sugestao_pedido(demanda_mes: float, estoque_atual: int, horizonte_meses: int = 3) -> int:
    return max(0, int((demanda_mes * horizonte_meses) - estoque_atual))


def precisa_repor(estoque: int, demanda_diaria: float, curva_abc: str | None) -> bool:
    target_days = COVERAGE_DAYS.get((curva_abc or "").upper(), 15)
    cobertura = estoque / demanda_diaria if demanda_diaria > 0 else 999
    return cobertura < target_days


def preco_unitario_historico(valor_total_item: float, quantidade_unitaria: float) -> float:
    if quantidade_unitaria == 0:
        return 0
    return valor_total_item / quantidade_unitaria


def preco_unitario_liquido(valor_total_item: float, quantidade_unitaria: float, valor_outras_despesas: float, valor_icms_st: float) -> float:
    if quantidade_unitaria == 0:
        return 0
    return (valor_total_item - valor_outras_despesas - valor_icms_st) / quantidade_unitaria
