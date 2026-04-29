from __future__ import annotations

from statistics import mean, median
from typing import Any


def calcular_menor_historico(entradas: list[dict[str, Any]]) -> float | None:
    precos = [float(item["preco_unitario"]) for item in entradas if item.get("preco_unitario") is not None]
    return min(precos) if precos else None


def calcular_media_historica(entradas: list[dict[str, Any]]) -> float | None:
    precos = [float(item["preco_unitario"]) for item in entradas if item.get("preco_unitario") is not None]
    return mean(precos) if precos else None


def calcular_mediana_historica(entradas: list[dict[str, Any]]) -> float | None:
    precos = [float(item["preco_unitario"]) for item in entradas if item.get("preco_unitario") is not None]
    return median(precos) if precos else None


def calcular_variacao_percentual(preco_oferta: float, menor_historico: float | None) -> float | None:
    """Wrapper de compatibilidade — delega para analysis_engine (fonte única de verdade).

    NOTA: Esta assinatura tem (preco_oferta, menor_historico), enquanto
    analysis_engine tem (menor_historico, preco_oferta). Este wrapper inverte
    os argumentos para manter compatibilidade retroativa.
    """
    from app.services.analysis_engine import calcular_variacao_percentual as _calc
    return _calc(menor_historico, preco_oferta)


def extremos_historicos(entradas: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    ordenadas = sorted(entradas, key=lambda item: float(item.get("preco_unitario", 0)))
    return {
        "menores": ordenadas[:2],
        "maiores": list(reversed(ordenadas[-2:])),
    }
