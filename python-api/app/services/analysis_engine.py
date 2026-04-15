"""
Analysis Engine — Motor de cálculos determinísticos para análise de ofertas.

Fase 2 do fluxo determinístico:
Recebe itens extraídos + dados do arquivo/banco e calcula TUDO em Python:
- Matching (reutiliza lógica do file_parser)
- Variação percentual
- Classificação (ouro/prata/atenção/descartável)
- Sugestão de pedido
- Recomendação (templates)

ZERO dependência de LLM para cálculos = 100% precisão.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


# ─── Cálculos Determinísticos ─────────────────────────────────────────────────

def calcular_variacao_percentual(menor_historico: float | None, preco_oferta: float | None) -> float | None:
    """
    Calcula variação percentual: ((menor_hist - preco_oferta) / menor_hist) × 100.
    
    Positivo = desconto (oferta mais barata)
    Negativo = ágio (oferta mais cara)
    """
    if not menor_historico or not preco_oferta or menor_historico <= 0:
        return None
    return round(((menor_historico - preco_oferta) / menor_historico) * 100, 2)


def calcular_sugestao_pedido(demanda_mes: float, estoque: int = 0, meses_cobertura: int = 3) -> int:
    """
    Calcula sugestão de pedido: max(0, (demanda_mes × meses) - estoque).
    
    Default: cobertura de 3 meses.
    """
    return max(0, round(demanda_mes * meses_cobertura) - estoque)


def classificar_oferta(variacao: float | None) -> str:
    """
    Classifica a oferta com base na variação percentual.
    
    - ouro: ≥ 20% (desconto forte)
    - prata: 5% a 20% (desconto moderado)
    - atencao: 0% a 5% (desconto marginal)
    - descartavel: < 0% (ágio) ou sem dados
    """
    if variacao is None:
        return "descartavel"
    if variacao >= 20:
        return "ouro"
    if variacao >= 5:
        return "prata"
    if variacao >= 0:
        return "atencao"
    return "descartavel"


def gerar_recomendacao(
    classificacao: str,
    variacao: float | None,
    menor_historico: float | None,
    preco_oferta: float | None,
    demanda_mes: float = 0,
    sugestao_pedido: int = 0,
    descricao: str = "",
) -> str:
    """
    Gera recomendação textual determinística, com dados numéricos reais.
    
    Templates por classificação — sem risco de inconsistência com os dados.
    """
    menor_str = f"R${menor_historico:.2f}" if menor_historico else "N/A"
    preco_str = f"R${preco_oferta:.2f}" if preco_oferta else "N/A"
    var_str = f"{variacao:.1f}%" if variacao is not None else "N/A"
    
    if classificacao == "ouro":
        base = f"Oportunidade excelente! Desconto de {var_str} vs menor histórico ({menor_str})."
        if sugestao_pedido > 0:
            base += f" Sugestão: comprar {sugestao_pedido} unidades para ~3 meses de cobertura."
        else:
            base += " Comprar imediatamente."
        return base
    
    if classificacao == "prata":
        base = f"Boa oportunidade. Desconto de {var_str} vs menor histórico ({menor_str})."
        if sugestao_pedido > 0:
            base += f" Considerar compra de {sugestao_pedido} unidades."
        return base
    
    if classificacao == "atencao":
        if variacao is not None and variacao >= 0:
            return (
                f"Desconto marginal de {var_str} vs menor histórico ({menor_str}). "
                f"Preço da oferta: {preco_str}. Avaliar necessidade real antes de comprar."
            )
        return f"Preço próximo ao histórico ({menor_str}). Avaliar necessidade antes de comprar."
    
    # descartavel
    if variacao is not None and variacao < 0:
        return (
            f"Preço {abs(variacao):.1f}% ACIMA do menor histórico ({menor_str}). "
            f"Oferta a {preco_str} não é vantajosa. Não recomendado."
        )
    return "Produto sem histórico de compras no arquivo. Sem dados para avaliar a oferta."


# ─── Matching: reutiliza lógica do file_parser ────────────────────────────────

def _match_item_no_arquivo(
    descricao: str,
    ean_oferta: str | None,
    ean_stats: dict[str, dict],
    token_index: dict[str, list[str]],
    used_eans: set[str],
) -> dict | None:
    """
    Faz matching de um item da oferta com os dados do arquivo.
    
    Reutiliza a lógica de weighted token scoring do file_parser.
    """
    from app.services.file_parser import _slugify, _extract_tokens
    
    # Match por EAN exato (se disponível)
    if ean_oferta and ean_oferta in ean_stats and ean_oferta not in used_eans:
        stats = ean_stats[ean_oferta]
        used_eans.add(ean_oferta)
        return {
            "ean": ean_oferta,
            "descricao_arquivo": stats["descricao"],
            "confianca_match": "alto",
            "menor_preco": stats["menor_preco"],
            "media_preco": stats["media_preco"],
            "maior_preco": stats["maior_preco"],
            "qtd_entradas": stats["qtd_entradas"],
            "qtde_total": stats["qtde_total"],
            "demanda_mes": _calcular_demanda_mes(stats),
            "primeira_data": stats["primeira_data"],
            "ultima_data": stats["ultima_data"],
        }
    
    # Match por tokens ponderados
    item_tokens = _extract_tokens(descricao)
    if len(item_tokens) < 1:
        return None
    
    drug_tokens = {t for t in item_tokens if len(t) >= 4 and t.isalpha()}
    generic_tokens = item_tokens - drug_tokens
    
    candidate_scores: dict[str, float] = {}
    for token in drug_tokens:
        for ean in token_index.get(token, []):
            if ean not in used_eans:
                candidate_scores[ean] = candidate_scores.get(ean, 0) + 5.0
    for token in generic_tokens:
        for ean in token_index.get(token, []):
            if ean not in used_eans:
                candidate_scores[ean] = candidate_scores.get(ean, 0) + 1.0
    
    if not candidate_scores:
        return None
    
    sorted_candidates = sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)
    best_ean, best_score = sorted_candidates[0]
    
    # Validar: exige ao menos 1 drug token em comum ou score >= 10
    best_desc_tokens = _extract_tokens(ean_stats[best_ean].get("descricao", ""))
    common_drug_tokens = drug_tokens & best_desc_tokens
    
    if not common_drug_tokens and best_score < 10:
        return None
    
    stats = ean_stats[best_ean]
    n_common = len(common_drug_tokens)
    confianca = "alto" if n_common >= 2 else "medio" if n_common >= 1 else "baixo"
    
    used_eans.add(best_ean)
    
    return {
        "ean": best_ean,
        "descricao_arquivo": stats["descricao"],
        "confianca_match": confianca,
        "menor_preco": stats["menor_preco"],
        "media_preco": stats["media_preco"],
        "maior_preco": stats["maior_preco"],
        "qtd_entradas": stats["qtd_entradas"],
        "qtde_total": stats["qtde_total"],
        "demanda_mes": _calcular_demanda_mes(stats),
        "primeira_data": stats["primeira_data"],
        "ultima_data": stats["ultima_data"],
    }


def _calcular_demanda_mes(stats: dict) -> float:
    """Calcula demanda mensal com base no período e quantidade total."""
    if stats.get("primeira_data") == "N/A" or stats.get("ultima_data") == "N/A":
        return 0.0
    try:
        from datetime import datetime
        d1 = datetime.strptime(str(stats["primeira_data"])[:10], "%Y-%m-%d")
        d2 = datetime.strptime(str(stats["ultima_data"])[:10], "%Y-%m-%d")
        meses = max(1, (d2 - d1).days / 30)
        return round(stats["qtde_total"] / meses, 1)
    except Exception:
        return 0.0


# ─── Construção do Índice (extraído do file_parser) ──────────────────────────

def construir_indice_arquivo(rows: list[dict]) -> tuple[dict[str, dict], dict[str, list[str]]]:
    """
    Constrói o índice de EANs e o índice invertido de tokens a partir dos rows do arquivo.
    
    Returns:
        (ean_stats, token_index) onde:
        - ean_stats[ean] = {descricao, menor_preco, media_preco, ...}
        - token_index[token] = [lista de EANs que contêm esse token]
    """
    from collections import defaultdict
    from statistics import mean
    from app.services.file_parser import _calcular_preco_unitario, _parse_number, _extract_tokens
    
    by_ean: dict[str, list[dict]] = defaultdict(list)
    
    for row in rows:
        ean = row.get("ean")
        if ean and str(ean).strip() and str(ean).strip() not in ("0", "None", "none", "null"):
            by_ean[str(ean).strip()].append(row)
    
    ean_stats: dict[str, dict] = {}
    for ean, entries in by_ean.items():
        precos = []
        datas = []
        descricao = ""
        qtde_total = 0.0
        
        for e in entries:
            pu = _calcular_preco_unitario(e)
            if pu and pu > 0:
                precos.append(pu)
            d = e.get("data_entrada")
            if d:
                datas.append(str(d))
            if not descricao and e.get("descricao"):
                descricao = str(e["descricao"]).strip()
            qtde_total += _parse_number(e.get("quantidade")) or 0
        
        ean_stats[ean] = {
            "ean": ean,
            "descricao": descricao,
            "qtd_entradas": len(entries),
            "qtde_total": qtde_total,
            "menor_preco": min(precos) if precos else None,
            "media_preco": round(mean(precos), 4) if precos else None,
            "maior_preco": max(precos) if precos else None,
            "primeira_data": min(datas) if datas else "N/A",
            "ultima_data": max(datas) if datas else "N/A",
        }
    
    # Construir índice invertido de tokens
    token_index: dict[str, list[str]] = {}
    for ean, stats in ean_stats.items():
        tokens = _extract_tokens(stats.get("descricao", ""))
        for token in tokens:
            if token not in token_index:
                token_index[token] = []
            token_index[token].append(ean)
    
    logger.info(f"Índice construído: {len(ean_stats)} EANs, {len(token_index)} tokens")
    return ean_stats, token_index


# ─── Orquestrador Principal ──────────────────────────────────────────────────

def executar_analise_deterministico(
    itens_extraidos: list[dict[str, Any]],
    fornecedor: str | None,
    ean_stats: dict[str, dict],
    token_index: dict[str, list[str]],
    total_registros: int = 0,
) -> dict:
    """
    Executa a análise completa de forma 100% determinística.
    
    Args:
        itens_extraidos: Lista de {descricao, preco, ean} da Fase 1
        fornecedor: Nome do fornecedor
        ean_stats: Estatísticas por EAN do arquivo
        token_index: Índice invertido de tokens
        total_registros: Total de registros no arquivo (para info)
    
    Returns:
        Dict no formato AnaliseOfertaAgnoOutput (fornecedor + itens)
    """
    itens_resultado = []
    used_eans: set[str] = set()
    
    for item in itens_extraidos:
        descricao = item.get("descricao", "")
        preco_oferta = item.get("preco")
        ean_oferta = item.get("ean")
        
        # 1. MATCHING
        match = _match_item_no_arquivo(
            descricao=descricao,
            ean_oferta=ean_oferta,
            ean_stats=ean_stats,
            token_index=token_index,
            used_eans=used_eans,
        )
        
        if match:
            # 2. CÁLCULOS DETERMINÍSTICOS
            menor_hist = match["menor_preco"]
            variacao = calcular_variacao_percentual(menor_hist, preco_oferta)
            demanda = match["demanda_mes"]
            sugestao = calcular_sugestao_pedido(demanda, estoque=0)
            classificacao = classificar_oferta(variacao)
            
            # 3. RECOMENDAÇÃO POR TEMPLATE
            recomendacao = gerar_recomendacao(
                classificacao=classificacao,
                variacao=variacao,
                menor_historico=menor_hist,
                preco_oferta=preco_oferta,
                demanda_mes=demanda,
                sugestao_pedido=sugestao,
                descricao=descricao,
            )
            
            itens_resultado.append({
                "descricao_original": descricao,
                "preco_oferta": preco_oferta,
                "ean": match["ean"],
                "descricao_produto": match["descricao_arquivo"],
                "menor_historico": menor_hist,
                "variacao_percentual": variacao,
                "estoque_item": 0,
                "demanda_mes": demanda,
                "sugestao_pedido": sugestao,
                "estoque_equivalentes": 0,
                "classificacao": classificacao,
                "confianca_match": match["confianca_match"],
                "recomendacao": recomendacao,
                "equivalentes": [],
            })
            
            logger.info(
                f"✅ {descricao[:40]} → {match['descricao_arquivo'][:40]} | "
                f"oferta=R${preco_oferta:.2f} menor=R${menor_hist:.2f} var={variacao:.1f}% "
                f"class={classificacao} sugestao={sugestao}"
            )
        else:
            # SEM MATCH
            itens_resultado.append({
                "descricao_original": descricao,
                "preco_oferta": preco_oferta,
                "ean": None,
                "descricao_produto": None,
                "menor_historico": None,
                "variacao_percentual": None,
                "estoque_item": 0,
                "demanda_mes": 0,
                "sugestao_pedido": 0,
                "estoque_equivalentes": 0,
                "classificacao": "descartavel",
                "confianca_match": "baixo",
                "recomendacao": "Produto sem histórico de compras no arquivo. Sem dados para avaliar a oferta.",
                "equivalentes": [],
            })
            logger.info(f"❌ {descricao[:40]} → SEM MATCH")
    
    # Resumo
    classificacoes = [i["classificacao"] for i in itens_resultado]
    logger.info(
        f"Análise determinística completa: {len(itens_resultado)} itens | "
        f"ouro={classificacoes.count('ouro')} prata={classificacoes.count('prata')} "
        f"atencao={classificacoes.count('atencao')} descartavel={classificacoes.count('descartavel')}"
    )
    
    return {
        "fornecedor": fornecedor,
        "itens": itens_resultado,
    }
