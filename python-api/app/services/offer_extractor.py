"""
Offer Extractor — Extrai itens estruturados do texto bruto da oferta.

Fase 1 do fluxo determinístico:
1. Tenta extrair com regex (instantâneo, custo zero)
2. Se regex falhar, usa Claude com prompt curto (fallback)
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


# ─── Extração por Regex ──────────────────────────────────────────────────────

def _limpar_descricao(desc: str) -> str:
    """Remove artefatos comuns da descrição extraída."""
    # Remove trailing separadores
    desc = re.sub(r"[\s\-–—=:]+$", "", desc).strip()
    # Remove prefixos numéricos tipo "1.", "2)", "01 -"
    desc = re.sub(r"^\d+[\.\)\-–]\s*", "", desc).strip()
    return desc


def _parse_preco_br(texto: str) -> float | None:
    """Parseia preço em formato brasileiro: 24,17 ou 24.17 ou 1.234,56"""
    texto = texto.strip().replace(" ", "")
    # Formato brasileiro: 1.234,56
    m = re.match(r"(\d{1,3}(?:\.\d{3})*,\d{2})$", texto)
    if m:
        return float(m.group(1).replace(".", "").replace(",", "."))
    # Formato simples com vírgula: 24,17
    m = re.match(r"(\d+,\d{2})$", texto)
    if m:
        return float(m.group(1).replace(",", "."))
    # Formato com ponto decimal: 24.17
    m = re.match(r"(\d+\.\d{2})$", texto)
    if m:
        return float(m.group(1))
    return None


def extrair_itens_regex(texto: str) -> list[dict[str, Any]]:
    """
    Extrai itens de uma oferta usando regex — zero custo, instantâneo.
    
    Suporta formatos comuns:
    - "Produto XYZ - R$ 24,17"
    - "Produto XYZ R$ 24,17"
    - "Produto XYZ 24,17"
    - "EAN 7891234567890 Produto XYZ R$ 24,17"
    """
    itens = []
    
    for linha in texto.strip().split("\n"):
        linha = linha.strip()
        if not linha or len(linha) < 5:
            continue
        
        # Tentar extrair EAN (13 dígitos)
        ean_match = re.search(r"\b(\d{13})\b", linha)
        ean = ean_match.group(1) if ean_match else None
        
        # Pattern 1: "Descrição - R$ XX,XX" ou "Descrição R$ XX,XX"
        m = re.match(
            r"(.+?)\s*[-–—]?\s*R\$\s*([\d.,]+)",
            linha, re.IGNORECASE
        )
        if m:
            desc = _limpar_descricao(m.group(1))
            preco = _parse_preco_br(m.group(2))
            if desc and preco and preco > 0:
                # Remover EAN da descrição se presente
                if ean:
                    desc = desc.replace(ean, "").strip()
                    desc = re.sub(r"^\s*[-–—:]\s*", "", desc).strip()
                itens.append({
                    "descricao": desc,
                    "preco": preco,
                    "ean": ean,
                })
                continue
        
        # Pattern 2: "Descrição XX,XX" (sem R$)
        m = re.match(
            r"(.+?)\s+(\d+[.,]\d{2})\s*$",
            linha
        )
        if m:
            desc = _limpar_descricao(m.group(1))
            preco = _parse_preco_br(m.group(2))
            if desc and preco and preco > 0 and len(desc) > 3:
                if ean:
                    desc = desc.replace(ean, "").strip()
                    desc = re.sub(r"^\s*[-–—:]\s*", "", desc).strip()
                itens.append({
                    "descricao": desc,
                    "preco": preco,
                    "ean": ean,
                })
    
    logger.info(f"Regex extraiu {len(itens)} itens da oferta")
    return itens


# ─── Extração por LLM (fallback) ─────────────────────────────────────────────

async def extrair_itens_llm(texto: str) -> list[dict[str, Any]]:
    """
    Extrai itens usando Claude com prompt curto e focado.
    Fallback para quando o regex não consegue parsear o formato.
    """
    from agno.agent import Agent
    from agno.models.anthropic import Claude
    from app.db.supabase_client import get_settings

    settings = get_settings()
    
    prompt = f"""Extraia os itens desta oferta farmacêutica. Retorne APENAS o JSON, sem explicação:

{{"fornecedor": "nome do fornecedor ou null", "itens": [{{"descricao": "nome do produto", "preco": 0.00, "ean": "código ou null"}}]}}

Oferta:
{texto}"""

    model = Claude(
        id=settings.anthropic_model or "claude-sonnet-4-5-20250929",
        api_key=settings.anthropic_api_key,
        max_tokens=4096,
        temperature=0.0,  # zero criatividade — queremos extração pura
    )
    
    agent = Agent(
        model=model,
        instructions="Você é um extrator de dados. Extraia itens de ofertas e retorne JSON puro. Sem explicação.",
        markdown=False,
    )
    
    response = await agent.arun(prompt)
    content = response.content
    
    # Parsear JSON da resposta
    if isinstance(content, str):
        # Limpar markdown se presente
        content = re.sub(r"```(?:json)?\s*", "", content).strip()
        content = re.sub(r"```\s*$", "", content).strip()
        
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # Tentar encontrar o JSON na string
            start = content.find("{")
            if start >= 0:
                try:
                    data = json.loads(content[start:])
                except json.JSONDecodeError:
                    logger.error(f"LLM retornou JSON inválido: {content[:300]}")
                    return []
            else:
                return []
    elif isinstance(content, dict):
        data = content
    else:
        logger.error(f"LLM retornou tipo inesperado: {type(content)}")
        return []
    
    fornecedor = data.get("fornecedor")
    itens_raw = data.get("itens", [])
    
    itens = []
    for item in itens_raw:
        desc = item.get("descricao", "").strip()
        preco = item.get("preco")
        ean = item.get("ean")
        
        if desc and preco and float(preco) > 0:
            itens.append({
                "descricao": desc,
                "preco": float(preco),
                "ean": str(ean) if ean else None,
            })
    
    logger.info(f"LLM extraiu {len(itens)} itens, fornecedor={fornecedor}")
    return itens


# ─── Extração com Fornecedor ─────────────────────────────────────────────────

def _detectar_fornecedor_regex(texto: str) -> str | None:
    """Tenta detectar o nome do fornecedor no cabeçalho da oferta."""
    linhas = texto.strip().split("\n")
    
    for linha in linhas[:5]:  # Só nas 5 primeiras linhas
        linha = linha.strip()
        if not linha:
            continue
        
        # Patterns comuns: "Oferta Germed", "Promoção Lab XYZ", "Fornecedor: ABC"
        m = re.match(r"(?:oferta|promoção|promo|fornecedor|lab|distribuidora)\s*[:\-–]?\s*(.+)", 
                     linha, re.IGNORECASE)
        if m:
            nome = m.group(1).strip().rstrip("-–:. ")
            if nome and len(nome) >= 3:
                return nome
        
        # Se a primeira linha não tem preço, pode ser o nome do fornecedor/título
        if not re.search(r"\d+[.,]\d{2}", linha) and len(linha) > 3 and len(linha) < 80:
            # Heurística: se a linha seguinte TEM preço, essa é o cabeçalho
            if len(linhas) > 1 and re.search(r"\d+[.,]\d{2}", linhas[1]):
                return linha.strip().rstrip("-–:. ")
    
    return None


async def extrair_itens(texto: str) -> tuple[str | None, list[dict[str, Any]]]:
    """
    Extrai itens da oferta: regex primeiro, LLM como fallback.
    
    Returns:
        Tuple de (fornecedor, lista de itens [{descricao, preco, ean}])
    """
    # Tentar regex primeiro (instantâneo)
    itens = extrair_itens_regex(texto)
    
    if itens:
        fornecedor = _detectar_fornecedor_regex(texto)
        logger.info(f"Extração via REGEX: {len(itens)} itens, fornecedor={fornecedor}")
        return fornecedor, itens
    
    # Fallback: LLM
    logger.info("Regex não encontrou itens, usando LLM como fallback")
    itens = await extrair_itens_llm(texto)
    
    if itens:
        fornecedor = _detectar_fornecedor_regex(texto)
        return fornecedor, itens
    
    logger.warning("Nenhum item extraído (regex + LLM falharam)")
    return None, []
