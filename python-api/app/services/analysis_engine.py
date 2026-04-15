"""
Analysis Engine v2 — Motor de calculos deterministicos para analise de ofertas.

Fase 2 do fluxo deterministico:
Recebe itens extraidos + dados do arquivo/banco e calcula TUDO em Python:
- Matching (weighted token scoring)
- Variacao percentual
- Classificacao (ouro/prata/atencao/descartavel)
- Sugestao de pedido
- Busca de EQUIVALENTES por principio ativo
- Suporte a ofertas com desconto % (sem preco absoluto)
- Recomendacao (templates)

ZERO dependencia de LLM para calculos = 100% precisao.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


# ─── Calculos Deterministicos ─────────────────────────────────────────────────

def calcular_variacao_percentual(menor_historico: float | None, preco_oferta: float | None) -> float | None:
    """
    Calcula variacao percentual: ((menor_hist - preco_oferta) / menor_hist) x 100.

    Positivo = desconto (oferta mais barata)
    Negativo = agio (oferta mais cara)
    """
    if not menor_historico or not preco_oferta or menor_historico <= 0:
        return None
    return round(((menor_historico - preco_oferta) / menor_historico) * 100, 2)


def calcular_sugestao_pedido(demanda_mes: float, estoque: int = 0, meses_cobertura: int = 3) -> int:
    """
    Calcula sugestao de pedido: max(0, (demanda_mes x meses) - estoque).

    Default: cobertura de 3 meses.
    """
    return max(0, round(demanda_mes * meses_cobertura) - estoque)


def classificar_oferta(variacao: float | None) -> str:
    """
    Classifica a oferta com base na variacao percentual.

    - ouro: >= 20% (desconto forte)
    - prata: 5% a 20% (desconto moderado)
    - atencao: 0% a 5% (desconto marginal)
    - descartavel: < 0% (agio) ou sem dados
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
    origem_menor: str = "=",
    equivalentes: list[dict] | None = None,
    tipo_preco: str = "absoluto",
    desconto_percentual: float | None = None,
) -> str:
    """
    Gera recomendacao textual deterministica, com dados numericos reais.
    """
    menor_str = f"R${menor_historico:.2f}" if menor_historico else "N/A"
    preco_str = f"R${preco_oferta:.2f}" if preco_oferta else "N/A"
    var_str = f"{variacao:.1f}%" if variacao is not None else "N/A"

    # Sufixo de equivalentes
    equiv_info = ""
    if equivalentes:
        nomes = [e["descricao"][:35] for e in equivalentes[:3]]
        equiv_info = f" Equivalentes em estoque: {', '.join(nomes)}."

    # Para itens com desconto % (sem preco absoluto)
    if tipo_preco == "percentual_desconto" and desconto_percentual:
        if menor_historico:
            pct_str = f"{desconto_percentual:.0f}%"
            preco_estimado = menor_historico * (1 - desconto_percentual / 100)
            return (
                f"Oferta com {pct_str} de desconto. "
                f"O menor historico e {menor_str}, preco estimado da oferta: R${preco_estimado:.2f}. "
                f"Verificar condicao comercial fixa antes de pedir.{equiv_info}"
            )
        return (
            f"Oferta com {desconto_percentual:.0f}% de desconto. "
            f"Sem historico de precos — verificar diretamente com o fornecedor.{equiv_info}"
        )

    # Origem do menor historico
    orig_tag = ""
    if origem_menor == "!=":
        orig_tag = " (via equivalente)"

    if classificacao == "ouro":
        base = f"Oportunidade excelente! Desconto de {var_str} vs menor historico ({menor_str}{orig_tag})."
        if sugestao_pedido > 0:
            base += f" Sugestao: comprar {sugestao_pedido} unidades para ~3 meses de cobertura."
        else:
            base += " Comprar imediatamente."
        return base + equiv_info

    if classificacao == "prata":
        base = f"Boa oportunidade. Desconto de {var_str} vs menor historico ({menor_str}{orig_tag})."
        if sugestao_pedido > 0:
            base += f" Considerar compra de {sugestao_pedido} unidades."
        return base + equiv_info

    if classificacao == "atencao":
        if variacao is not None and variacao >= 0:
            return (
                f"Desconto marginal de {var_str} vs menor historico ({menor_str}{orig_tag}). "
                f"Preco da oferta: {preco_str}. Avaliar necessidade real antes de comprar.{equiv_info}"
            )
        return f"Preco proximo ao historico ({menor_str}). Avaliar necessidade antes de comprar.{equiv_info}"

    # descartavel
    if variacao is not None and variacao < 0:
        return (
            f"Preco {abs(variacao):.1f}% ACIMA do menor historico ({menor_str}{orig_tag}). "
            f"Oferta a {preco_str} nao e vantajosa. Nao recomendado.{equiv_info}"
        )
    return f"Produto sem historico de compras. Sem dados para avaliar a oferta.{equiv_info}"


# ─── Matching: weighted token scoring ─────────────────────────────────────────

def _match_item_no_arquivo(
    descricao: str,
    ean_oferta: str | None,
    ean_stats: dict[str, dict],
    token_index: dict[str, list[str]],
    used_eans: set[str],
) -> dict | None:
    """
    Faz matching de um item da oferta com os dados do arquivo.
    """
    from app.services.file_parser import _extract_tokens

    # Match por EAN exato (se disponivel)
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
            "demanda_mes": stats.get("demanda_mes") or _calcular_demanda_mes(stats),
            "estoque_item": stats.get("estoque_item", 0),
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
        "demanda_mes": stats.get("demanda_mes") or _calcular_demanda_mes(stats),
        "estoque_item": stats.get("estoque_item", 0),
        "primeira_data": stats["primeira_data"],
        "ultima_data": stats["ultima_data"],
    }


def _calcular_demanda_mes(stats: dict) -> float:
    """Calcula demanda mensal com base no periodo e quantidade total."""
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


# ─── Busca de Equivalentes ────────────────────────────────────────────────────

def buscar_equivalentes(
    descricao: str,
    ean_principal: str | None,
    ean_stats: dict[str, dict],
    token_index: dict[str, list[str]],
    max_equivalentes: int = 5,
) -> list[dict]:
    """
    Busca produtos equivalentes no historico baseado em principio ativo (molecula).

    Estrategia:
    1. Extrair tokens farmacologicos da descricao (>= 5 chars, alfa)
    2. Buscar no token_index todos os EANs que compartilham esses tokens
    3. Filtrar: remover o EAN do match principal
    4. Filtrar: manter apenas equivalentes da MESMA categoria farmaceutica
    5. Ranquear por numero de tokens em comum
    6. Retornar top N com dados de preco

    Returns:
        Lista de dicts {ean, descricao, menor_preco, media_preco, qtd_entradas, demanda_mes}
    """
    from app.services.file_parser import _extract_tokens
    from app.services.offer_extractor import _classificar_forma_farmaceutica

    tokens = _extract_tokens(descricao)
    # Tokens farmacologicos: >= 5 chars, apenas letras (moleculas, principios ativos)
    drug_tokens = {t for t in tokens if len(t) >= 5 and t.isalpha()}

    if not drug_tokens:
        return []

    # Categoria do produto original — usada para filtrar equivalentes
    categoria_original = _classificar_forma_farmaceutica(descricao)

    # Contar score de cada EAN candidato
    candidate_scores: dict[str, float] = {}
    for token in drug_tokens:
        for ean in token_index.get(token, []):
            if ean != ean_principal:
                candidate_scores[ean] = candidate_scores.get(ean, 0) + 1.0

    if not candidate_scores:
        return []

    # Ranquear por score e filtrar por relevancia
    sorted_candidates = sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)

    # Exigir pelo menos 1 token farmacologico em comum para ser equivalente
    equivalentes = []
    for ean, score in sorted_candidates:
        if len(equivalentes) >= max_equivalentes:
            break
        if score < 1:
            continue

        stats = ean_stats.get(ean)
        if not stats or stats.get("menor_preco") is None:
            continue

        # Verificar que compartilha ao menos 1 drug token
        ean_tokens = _extract_tokens(stats.get("descricao", ""))
        ean_drug_tokens = {t for t in ean_tokens if len(t) >= 5 and t.isalpha()}
        common = drug_tokens & ean_drug_tokens

        if not common:
            continue

        # Filtrar por mesma categoria farmacêutica (não misturar líquido com sólido)
        cat_equivalente = _classificar_forma_farmaceutica(stats.get("descricao", ""))
        if categoria_original != "unknown" and cat_equivalente != "unknown":
            if categoria_original != cat_equivalente:
                continue  # Não comparar frasco com sachê, comprimido com xarope, etc.

        equivalentes.append({
            "ean": ean,
            "descricao": stats["descricao"],
            "menor_preco": stats["menor_preco"],
            "media_preco": stats["media_preco"],
            "qtd_entradas": stats["qtd_entradas"],
            "demanda_mes": _calcular_demanda_mes(stats),
        })

    return equivalentes


# ─── Construcao do Indice ─────────────────────────────────────────────────────

def construir_indice_arquivo(rows: list[dict]) -> tuple[dict[str, dict], dict[str, list[str]]]:
    """
    Constroi o indice de EANs e o indice invertido de tokens a partir dos rows do arquivo.

    Returns:
        (ean_stats, token_index) onde:
        - ean_stats[ean] = {descricao, menor_preco, media_preco, ...}
        - token_index[token] = [lista de EANs que contem esse token]
    """
    from collections import defaultdict
    from statistics import mean
    from app.services.file_parser import _calcular_preco_unitario, _parse_number, _extract_tokens
    from app.services.offer_extractor import extrair_multiplicador_inteligente

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

        # Primeiro, encontrar a descricao para calcular o multiplicador
        for e in entries:
            if not descricao and e.get("descricao"):
                descricao = str(e["descricao"]).strip()

        # Calcular multiplicador inteligente baseado na categoria do produto
        mult = extrair_multiplicador_inteligente(descricao) if descricao else 1.0
        if mult <= 0:
            mult = 1.0

        for e in entries:
            pu = _calcular_preco_unitario(e)
            if pu and pu > 0:
                # Normalizar preço pela mesma regra usada na oferta
                precos.append(round(pu / mult, 4))
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

    # Construir indice invertido de tokens
    token_index: dict[str, list[str]] = {}
    for ean, stats in ean_stats.items():
        tokens = _extract_tokens(stats.get("descricao", ""))
        for token in tokens:
            if token not in token_index:
                token_index[token] = []
            token_index[token].append(ean)

    logger.info(f"Indice construido: {len(ean_stats)} EANs, {len(token_index)} tokens")
    return ean_stats, token_index

def construir_indice_banco(empresa_id: str) -> tuple[dict[str, dict], dict[str, list[str]]]:
    """
    Constroi o indice deterministico baixando produtos e historico do Supabase.
    Isso substitui as queries granulares por uma carga massiva no inicio da analise.
    """
    from app.db.supabase_client import get_supabase_client
    from app.services.persistencia_service import buscar_produtos, buscar_historico
    from app.services.file_parser import _extract_tokens
    from statistics import mean

    client = get_supabase_client()
    if not client:
        logger.warning("Supabase não configurado. Índice de banco retornará vazio.")
        return {}, {}

    produtos = buscar_produtos(client, empresa_id)
    historico = buscar_historico(client, empresa_id)

    ean_stats: dict[str, dict] = {}
    for p in produtos:
        ean = str(p.get("ean") or "").strip()
        if not ean:
            continue
            
        descricao = str(p.get("descricao") or "").strip()
        entries = historico.get(ean, [])
        
        precos = []
        datas = []
        qtde_total = 0.0

        for e in entries:
            try:
                pu = float(e.get("preco_unitario") or 0)
                if pu > 0:
                    precos.append(pu)
            except Exception:
                pass
            
            d = e.get("data_entrada")
            if d:
                datas.append(str(d))
            
            try:
                qtd = float(e.get("quantidade_unitaria") or 0)
                qtde_total += qtd
            except Exception:
                # Fall back to try to extract from valor_total / preco se precisar, mas quantidade_unitaria e padrao
                pass

        demanda_mes = float(p.get("demanda_mes") or 0)
        estoque_item = int(float(p.get("estoque") or 0))

        ean_stats[ean] = {
            "ean": ean,
            "descricao": descricao,
            "qtd_entradas": len(entries),
            "qtde_total": qtde_total,
            "demanda_mes": demanda_mes,
            "estoque_item": estoque_item,
            "menor_preco": min(precos) if precos else None,
            "media_preco": round(mean(precos), 4) if precos else None,
            "maior_preco": max(precos) if precos else None,
            "primeira_data": min(datas) if datas else "N/A",
            "ultima_data": max(datas) if datas else "N/A",
        }

    # Adicionar itens no historico que talvez NÃO tenham cadastro no produto
    for ean_hist, entries in historico.items():
        if ean_hist not in ean_stats:
            precos = []
            datas = []
            qtde_total = 0.0
            
            for e in entries:
                try:
                    pu = float(e.get("preco_unitario") or 0)
                    if pu > 0:
                        precos.append(pu)
                except:
                    pass
                d = e.get("data_entrada")
                if d:
                    datas.append(str(d))
                try:
                    qtd = float(e.get("quantidade_unitaria") or 0)
                    qtde_total += qtd
                except:
                    pass
                    
            ean_stats[ean_hist] = {
                "ean": ean_hist,
                "descricao": f"Item {ean_hist} (sem cadastro)",
                "qtd_entradas": len(entries),
                "qtde_total": qtde_total,
                "demanda_mes": 0.0,
                "estoque_item": 0,
                "menor_preco": min(precos) if precos else None,
                "media_preco": round(mean(precos), 4) if precos else None,
                "maior_preco": max(precos) if precos else None,
                "primeira_data": min(datas) if datas else "N/A",
                "ultima_data": max(datas) if datas else "N/A",
            }

    token_index: dict[str, list[str]] = {}
    for ean, stats in ean_stats.items():
        tokens = _extract_tokens(stats.get("descricao", ""))
        for token in tokens:
            if token not in token_index:
                token_index[token] = []
            token_index[token].append(ean)

    logger.info(f"Indice Banco construido: {len(ean_stats)} EANs, {len(token_index)} tokens")
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
    Executa a analise completa de forma deterministica.
    Agora com:
    - Busca de equivalentes por principio ativo
    - Suporte a ofertas com desconto % (sem preco absoluto)
    - Marcacao de origem do menor historico (= ou !=)
    """
    itens_resultado = []
    used_eans: set[str] = set()

    for item in itens_extraidos:
        descricao = item.get("descricao", "")
        preco_oferta = item.get("preco")
        ean_oferta = item.get("ean")
        tipo_preco = item.get("tipo_preco", "absoluto")
        desconto_pct = item.get("desconto_percentual")
        multiplicador_embalagem = item.get("multiplicador_embalagem", 1.0)

        # Normalize offer price to unit price if multiplier is present
        if preco_oferta is not None and multiplicador_embalagem > 0:
            preco_oferta = round(preco_oferta / multiplicador_embalagem, 4)

        # 1. MATCHING
        match = _match_item_no_arquivo(
            descricao=descricao,
            ean_oferta=ean_oferta,
            ean_stats=ean_stats,
            token_index=token_index,
            used_eans=used_eans,
        )

        if match:
            menor_hist = match["menor_preco"]
            origem_menor = "="

            # 2. BUSCAR EQUIVALENTES pelo EAN que deu match (usando descricao do arquivo)
            equivalentes = buscar_equivalentes(
                descricao=match["descricao_arquivo"],
                ean_principal=match["ean"],
                ean_stats=ean_stats,
                token_index=token_index,
            )

            # Verificar se algum equivalente tem preco MENOR que o match principal
            menor_hist_equiv = None
            for eq in equivalentes:
                if eq["menor_preco"] and (menor_hist is None or eq["menor_preco"] < menor_hist):
                    menor_hist_equiv = eq["menor_preco"]

            if menor_hist_equiv is not None and (menor_hist is None or menor_hist_equiv < menor_hist):
                menor_hist = menor_hist_equiv
                origem_menor = "!="

            # 3. TRATAR TIPO DE PRECO
            preco_efetivo = preco_oferta
            if tipo_preco == "percentual_desconto" and desconto_pct and menor_hist:
                # Estimar preco efetivo a partir de desconto % aplicado ao menor historico
                preco_efetivo = round(menor_hist * (1 - desconto_pct / 100), 2)
            elif tipo_preco == "percentual_desconto" and desconto_pct:
                # Sem historico — transformar desconto em variacao direta
                variacao = desconto_pct
                demanda = match.get("demanda_mes") or float(match.get("demanda_mes", 0))
                estoque_item = match.get("estoque_item", 0)
                sugestao = calcular_sugestao_pedido(demanda, estoque=estoque_item)
                classificacao = classificar_oferta(variacao)

                recomendacao = gerar_recomendacao(
                    classificacao=classificacao,
                    variacao=variacao,
                    menor_historico=menor_hist,
                    preco_oferta=None,
                    demanda_mes=demanda,
                    sugestao_pedido=sugestao,
                    descricao=descricao,
                    origem_menor=origem_menor,
                    equivalentes=equivalentes,
                    tipo_preco=tipo_preco,
                    desconto_percentual=desconto_pct,
                )

                estoque_equiv = sum(eq.get("estoque_item", 0) for eq in equivalentes)

                itens_resultado.append({
                    "descricao_original": descricao,
                    "preco_oferta": None,
                    "ean": match["ean"],
                    "descricao_produto": match["descricao_arquivo"],
                    "menor_historico": menor_hist,
                    "variacao_percentual": variacao,
                    "estoque_item": estoque_item,
                    "demanda_mes": demanda,
                    "sugestao_pedido": sugestao,
                    "estoque_equivalentes": estoque_equiv,
                    "classificacao": classificacao,
                    "confianca_match": match["confianca_match"],
                    "recomendacao": recomendacao,
                    "equivalentes": equivalentes,
                    "origem_menor_historico": origem_menor,
                    "tipo_preco": tipo_preco,
                    "desconto_percentual": desconto_pct,
                })
                continue

            # 4. CALCULOS DETERMINISTICOS (preco absoluto ou estimado)
            variacao = calcular_variacao_percentual(menor_hist, preco_efetivo)
            demanda = match.get("demanda_mes") or float(match.get("demanda_mes", 0))
            estoque_item = match.get("estoque_item", 0)
            sugestao = calcular_sugestao_pedido(demanda, estoque=estoque_item)
            classificacao = classificar_oferta(variacao)

            # 5. RECOMENDACAO POR TEMPLATE
            recomendacao = gerar_recomendacao(
                classificacao=classificacao,
                variacao=variacao,
                menor_historico=menor_hist,
                preco_oferta=preco_efetivo,
                demanda_mes=demanda,
                sugestao_pedido=sugestao,
                descricao=descricao,
                origem_menor=origem_menor,
                equivalentes=equivalentes,
                tipo_preco=tipo_preco,
                desconto_percentual=desconto_pct,
            )

            estoque_equiv = sum(eq.get("estoque_item", 0) for eq in equivalentes)

            itens_resultado.append({
                "descricao_original": descricao,
                "preco_oferta": preco_efetivo,
                "ean": match["ean"],
                "descricao_produto": match["descricao_arquivo"],
                "menor_historico": menor_hist,
                "variacao_percentual": variacao,
                "estoque_item": estoque_item,
                "demanda_mes": demanda,
                "sugestao_pedido": sugestao,
                "estoque_equivalentes": estoque_equiv,
                "classificacao": classificacao,
                "confianca_match": match["confianca_match"],
                "recomendacao": recomendacao,
                "equivalentes": equivalentes,
                "origem_menor_historico": origem_menor,
                "tipo_preco": tipo_preco,
                "desconto_percentual": desconto_pct,
            })

            logger.info(
                f"OK {descricao[:40]} -> {match['descricao_arquivo'][:40]} | "
                f"var={variacao}% class={classificacao} equiv={len(equivalentes)}"
            )
        else:
            # SEM MATCH — tentar buscar equivalentes mesmo assim
            equivalentes = buscar_equivalentes(
                descricao=descricao,
                ean_principal=None,
                ean_stats=ean_stats,
                token_index=token_index,
            )
            estoque_equiv = sum(eq.get("qtd_entradas", 0) for eq in equivalentes)

            # Se encontrou equivalentes, usar menor preco deles como referencia
            menor_hist_equiv = None
            origem_menor = "!="
            if equivalentes:
                precos_equiv = [e["menor_preco"] for e in equivalentes if e.get("menor_preco")]
                if precos_equiv:
                    menor_hist_equiv = min(precos_equiv)

            variacao = None
            classificacao = "descartavel"
            if menor_hist_equiv and preco_oferta:
                variacao = calcular_variacao_percentual(menor_hist_equiv, preco_oferta)
                classificacao = classificar_oferta(variacao)

            recomendacao = gerar_recomendacao(
                classificacao=classificacao if menor_hist_equiv else "descartavel",
                variacao=variacao,
                menor_historico=menor_hist_equiv,
                preco_oferta=preco_oferta,
                demanda_mes=0,
                sugestao_pedido=0,
                descricao=descricao,
                origem_menor=origem_menor,
                equivalentes=equivalentes,
                tipo_preco=tipo_preco,
                desconto_percentual=desconto_pct,
            )

            itens_resultado.append({
                "descricao_original": descricao,
                "preco_oferta": preco_oferta,
                "ean": None,
                "descricao_produto": None,
                "menor_historico": menor_hist_equiv,
                "variacao_percentual": variacao,
                "estoque_item": 0,
                "demanda_mes": 0,
                "sugestao_pedido": 0,
                "estoque_equivalentes": estoque_equiv,
                "classificacao": classificacao,
                "confianca_match": "baixo",
                "recomendacao": recomendacao,
                "equivalentes": equivalentes,
                "origem_menor_historico": origem_menor if equivalentes else None,
                "tipo_preco": tipo_preco,
                "desconto_percentual": desconto_pct,
            })
            logger.info(f"SEM MATCH {descricao[:40]} equiv={len(equivalentes)}")

    # Resumo
    classificacoes = [i["classificacao"] for i in itens_resultado]
    logger.info(
        f"Analise v2 completa: {len(itens_resultado)} itens | "
        f"ouro={classificacoes.count('ouro')} prata={classificacoes.count('prata')} "
        f"atencao={classificacoes.count('atencao')} descartavel={classificacoes.count('descartavel')}"
    )

    return {
        "fornecedor": fornecedor,
        "itens": itens_resultado,
    }
