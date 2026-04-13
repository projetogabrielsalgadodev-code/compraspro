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
    if menor_historico in (None, 0):
      return None
    return round(((menor_historico - preco_oferta) / menor_historico) * 100, 2)


def extremos_historicos(entradas: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    ordenadas = sorted(entradas, key=lambda item: float(item.get("preco_unitario", 0)))
    return {
        "menores": ordenadas[:2],
        "maiores": list(reversed(ordenadas[-2:])),
    }
