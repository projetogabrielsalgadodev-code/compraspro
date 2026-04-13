from __future__ import annotations

from typing import Any

from app.services.equivalencia import slug_texto


def match_por_ean(produtos: list[dict[str, Any]], ean: str | None) -> tuple[dict[str, Any] | None, str]:
    if not ean:
        return None, "baixo"
    for produto in produtos:
        if str(produto.get("ean")) == str(ean):
            return produto, "alto"
    return None, "baixo"


def match_por_descricao(produtos: list[dict[str, Any]], descricao: str) -> tuple[dict[str, Any] | None, str]:
    descricao_slug = slug_texto(descricao)
    tokens = set(descricao_slug.split())
    if not tokens:
        return None, "baixo"
    melhor_produto: dict[str, Any] | None = None
    melhor_score = 0
    for produto in produtos:
        descricao_produto = slug_texto(produto.get("descricao"))
        score = len(tokens.intersection(set(descricao_produto.split())))
        if score > melhor_score:
            melhor_score = score
            melhor_produto = produto
    if melhor_produto and melhor_score >= 4:
        return melhor_produto, "medio"
    if melhor_produto and melhor_score >= 2:
        return melhor_produto, "baixo"
    return None, "baixo"
