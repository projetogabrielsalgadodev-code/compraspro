from __future__ import annotations

import re
from typing import Any


def slug_texto(valor: str | None) -> str:
    if not valor:
        return ""
    return re.sub(r"[^a-z0-9]+", " ", valor.lower()).strip()


def sao_equivalentes(produto_a: dict[str, Any], produto_b: dict[str, Any]) -> bool:
    principio_a = slug_texto(produto_a.get("principio_ativo"))
    principio_b = slug_texto(produto_b.get("principio_ativo"))
    if not principio_a or not principio_b or principio_a != principio_b:
        return False
    descricao_a = slug_texto(produto_a.get("descricao"))
    descricao_b = slug_texto(produto_b.get("descricao"))
    tokens_a = set(descricao_a.split())
    tokens_b = set(descricao_b.split())
    return len(tokens_a.intersection(tokens_b)) >= 2
