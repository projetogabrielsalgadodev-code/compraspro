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
import re as _re_global
from typing import Any

logger = logging.getLogger(__name__)

# Tokens genéricos de forma farmacêutica / embalagem / via de administração
# Não devem contar como "drug tokens" (peso 5) no matching nem na busca de equivalentes.
# Apenas o NOME da molécula/princípio ativo deve ter peso alto.
_GENERIC_FORM_TOKENS = {
    "xarope", "comprimido", "comprimidos", "comp", "capsula", "capsulas",
    "dragea", "drageas", "solucao", "solucoes", "suspensao", "nasal",
    "oral", "gotas", "spray", "creme", "pomada", "locao", "shampoo",
    "sache", "envelope", "fracao", "frasco", "bisnaga", "geleia",
    "pastilha", "pastilhas", "infantil", "adulto", "pediatrico",
    "injetavel", "topico", "generico", "similar", "referencia",
    "eurofarma", "medley",
    # Common non-pharmaceutical words that cause false positives
    "bolso", "display", "refil", "caixa", "blister", "cartela",
    "fracionado", "embalagem", "unidade", "unidades", "original",
    "lacrado", "especial", "promocional", "linha", "marca",
    "fresh", "menta", "limao", "morango", "cereja", "uva",
    "laranja", "framboesa", "tutti", "frutti", "sabor",
    "mastigavel", "efervescente", "sublingual", "retard",
    "revestido", "liberacao", "prolongada", "modificada",
    # Cosmetic/presentation terms that cause pharma ↔ cosmetics false positives
    "emulsao", "capilar", "fluido", "condicionador", "harmonizacao",
    "treino", "color", "touch", "novex", "revlon", "loreal",
    "hidratante", "nutritivo", "reparador", "alisamento",
    # Additional generic terms to prevent cross-category false matches
    "agua", "micelar", "ampola", "antioxidante", "ions", "dermachem",
    "health", "labs", "black", "caps", "copo",
    "quimica", "mole", "dura", "gelatinosa",
    "revest", "film", "coat", "tabs",
}

# Prefixos de sal farmacêutico — NÃO devem ser usados como primary_molecule.
# Ex: "dicloridrato de hidroxizina" → primary deve ser "hidroxizina", não "dicloridrato".
_SALT_PREFIXES = {
    "dicloridrato", "cloridrato", "fumarato", "succinato", "maleato",
    "tartarato", "mesilato", "besilato", "hemifumarato", "bromidrato",
    "oxalato", "fosfato", "sulfato", "acetato", "benzoato", "citrato",
    "lactato", "nitrato", "propionato", "valerato", "dipropionato",
    "furoato", "palmitato", "estearato", "gluconato", "tosilato",
    "clor",  # abreviação comum de cloridrato
    "trometamol",  # sal de cetorolaco
    "medoxomila",  # sal de olmesartana
    "axetil",  # sal de cefuroxima
    "potassio",  # sal de clavulanato
}

# Regex para extrair dosagens numéricas de descrições farmacêuticas
_DOSAGE_PATTERN = _re_global.compile(
    r'(\d+(?:[.,]\d+)?)\s*(?:mg|mcg|g|ml|ui|un)\b',
    _re_global.IGNORECASE
)

def _extract_dosages(desc: str) -> set[str]:
    """Extrai dosagens numéricas normalizadas de uma descrição farmacêutica.
    Ex: 'Duloxetina 60mg' → {'60'}, 'Amox+Clav 875+125mg' → {'875', '125'}
    """
    matches = _DOSAGE_PATTERN.findall(desc)
    return {m.replace(',', '.') for m in matches}


# ─── Helper: prefix lookup no token_index ─────────────────────────────────────

def _prefix_lookup(token: str, token_index: dict[str, list[str]], min_prefix: int = 4) -> list[str]:
    """
    Busca EANs no token_index por correspondência exata OU por prefixo.
    
    Resolve o problema de abreviações: "amox" encontra "amoxicilina",
    "clav" encontra "clavulanato", etc.
    
    Rules:
    - Se o token tem match exato, retorna apenas o exato (mais preciso)
    - Se não, busca todos os tokens no índice que COMEÇAM com esse token
    - Mínimo de `min_prefix` chars para evitar matches muito amplos
    """
    # 1. Match exato — preferencial
    if token in token_index:
        return token_index[token]
    
    # 2. Prefix match — só se token tem tamanho mínimo
    if len(token) < min_prefix:
        return []
    
    results: list[str] = []
    for idx_token, eans in token_index.items():
        if idx_token.startswith(token) and idx_token != token:
            results.extend(eans)
    return results


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
    
    NOTA: used_eans NÃO é usado para excluir candidatos.
    Múltiplos itens da oferta podem ter match com o mesmo EAN histórico,
    pois o histórico é referência de preço, não estoque.
    """
    from app.services.file_parser import _extract_tokens
    from app.services.offer_extractor import _classificar_forma_farmaceutica
    import re as _re_match

    # Categoria do item da oferta — para filtrar candidatos da mesma forma farmacêutica
    categoria_oferta = _classificar_forma_farmaceutica(descricao)

    # Match por EAN exato (se disponivel)
    if ean_oferta and ean_oferta in ean_stats:
        stats = ean_stats[ean_oferta]
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

    # Separar drug tokens (nomes de moléculas) de tokens genéricos (forma, embalagem)
    drug_tokens = {t for t in item_tokens if len(t) >= 4 and t.isalpha() and t not in _GENERIC_FORM_TOKENS}
    generic_tokens = item_tokens - drug_tokens

    # ── COMBINED NAME DETECTION ──
    # Detect combined drug names like "AMOX+CLAV", "LANSOPRAZOL+AMOXICILINA" in original text
    # Split on + and . to get individual molecule tokens
    combined_parts = set()
    for part in _re_match.split(r'[+./]', descricao.upper()):
        part_clean = part.strip()
        # Only consider alpha parts >= 4 chars as potential molecule names
        sub_words = _re_match.findall(r'[A-Za-zÀ-ú]{4,}', part_clean)
        for w in sub_words:
            w_lower = w.lower()
            if w_lower not in _GENERIC_FORM_TOKENS and w_lower not in {'caps', 'comp', 'cprs', 'drgs'}:
                combined_parts.add(w_lower)
    # Add combined parts as drug tokens (they may already be there from _extract_tokens)
    drug_tokens = drug_tokens | combined_parts

    # Identify the PRIMARY tokens — ALL significant molecule names from the description
    # For "Amox+Clav 875mg+125mg c/14", primary tokens are {"amox", "clav"}
    words = _re_match.findall(r"[A-Za-zÀ-ú]{4,}", descricao.upper())
    primary_tokens = set()
    for w in words:
        w_lower = w.lower()
        if w_lower not in _GENERIC_FORM_TOKENS and w_lower not in {"caps", "comp", "cprs", "drgs"}:
            primary_tokens.add(w_lower)
    # Also add combined parts as primary tokens
    primary_tokens = primary_tokens | combined_parts

    # Maximum possible score (for coverage threshold)
    max_possible_score = len(drug_tokens) * 5.0 + len(generic_tokens) * 1.0

    candidate_scores: dict[str, float] = {}
    for token in drug_tokens:
        for ean in _prefix_lookup(token, token_index):
            candidate_scores[ean] = candidate_scores.get(ean, 0) + 5.0
    for token in generic_tokens:
        for ean in _prefix_lookup(token, token_index):
            candidate_scores[ean] = candidate_scores.get(ean, 0) + 1.0

    if not candidate_scores:
        return None

    # Bug 18: Extrair dosagens da oferta para scoring
    offer_dosages = _extract_dosages(descricao)

    sorted_candidates = sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)

    # Aplicar ajustes de score antes de iterar (dosagem + palavras extra)
    adjusted_candidates: list[tuple[str, float]] = []
    for ean, raw_score in sorted_candidates:
        adj_score = raw_score
        cand_desc = ean_stats[ean].get("descricao", "")

        # Bug 18: Dosage matching — boost se dosagem coincide, penalizar se difere
        if offer_dosages:
            cand_dosages = _extract_dosages(cand_desc)
            if cand_dosages:
                common_doses = offer_dosages & cand_dosages
                if common_doses:
                    adj_score += len(common_doses) * 10.0  # forte boost por dosagem
                else:
                    adj_score -= 5.0  # penalidade por dosagem diferente

        # Bug 17: Penalizar candidatos com palavras significativas extras
        # Ex: "ENGOV" não deve matchear "ENGOV AFTER BERRY VIBES" (produto diferente)
        cand_drug_tokens = {t for t in _extract_tokens(cand_desc) 
                           if len(t) >= 4 and t.isalpha() and t not in _GENERIC_FORM_TOKENS}
        extra_cand_tokens = cand_drug_tokens - drug_tokens
        # Não penalizar salt prefixes ou tokens genéricos
        extra_significant = extra_cand_tokens - _SALT_PREFIXES
        if extra_significant and len(drug_tokens) <= 2:
            adj_score -= len(extra_significant) * 3.0

        adjusted_candidates.append((ean, adj_score))

    # Re-sort by adjusted score
    adjusted_candidates.sort(key=lambda x: x[1], reverse=True)

    # Iterar candidatos: encontrar o melhor que passa nos filtros
    for best_ean, best_score in adjusted_candidates:
        best_desc_tokens = _extract_tokens(ean_stats[best_ean].get("descricao", ""))

        # Also extract combined parts from the candidate description
        candidate_combined = set()
        for part in _re_match.split(r'[+./]', ean_stats[best_ean].get("descricao", "").upper()):
            sub_words = _re_match.findall(r'[A-Za-zÀ-ú]{4,}', part.strip())
            for w in sub_words:
                w_lower = w.lower()
                if w_lower not in _GENERIC_FORM_TOKENS:
                    candidate_combined.add(w_lower)
        all_candidate_tokens = best_desc_tokens | candidate_combined

        # Prefix-aware intersection for common_drug_tokens
        common_drug_tokens = set()
        for dt in drug_tokens:
            for ct in all_candidate_tokens:
                if dt.startswith(ct) or ct.startswith(dt):
                    common_drug_tokens.add(dt)
                    break

        if not common_drug_tokens and best_score < 10:
            continue

        # PRIMARY TOKENS CHECK: ALL primary molecule names from the offer
        # must appear in the candidate. This prevents:
        # - "AMOX+CLAV" matching "LANSOPRAZOL+AMOX" (missing CLAV)
        # - "CEFUROXIMA" matching "CEFALEXINA" (different molecule)
        if primary_tokens:
            missing_primary = set()
            for pt in primary_tokens:
                matched = False
                for ct in all_candidate_tokens:
                    if pt.startswith(ct) or ct.startswith(pt):
                        matched = True
                        break
                if not matched:
                    missing_primary.add(pt)
            
            if missing_primary:
                # If more than 30% of primary tokens are missing, reject
                missing_ratio = len(missing_primary) / len(primary_tokens)
                if missing_ratio > 0.3:
                    continue

        # COVERAGE THRESHOLD: score must represent at least 30% of possible
        if max_possible_score > 0 and (best_score / max_possible_score) < 0.3:
            continue

        # Filtrar por categoria farmacêutica: não misturar líquido com sólido
        cat_candidato = _classificar_forma_farmaceutica(ean_stats[best_ean].get("descricao", ""))
        if categoria_oferta != "unknown" and cat_candidato != "unknown":
            if categoria_oferta != cat_candidato:
                continue  # Skip: category mismatch

        stats = ean_stats[best_ean]
        n_common = len(common_drug_tokens)
        confianca = "alto" if n_common >= 2 else "medio" if n_common >= 1 else "baixo"

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

    return None



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
    1. Extrair tokens farmacologicos da descricao (>= 4 chars, alfa, NÃO genéricos)
    2. Identificar o PRIMARY molecule token (ex: 'rivaroxabana', 'domperidona')
    3. Buscar no token_index todos os EANs que compartilham esses tokens
    4. Filtrar: remover o EAN do match principal
    5. Filtrar: exigir que o PRIMARY token esteja presente no equivalente
    6. Filtrar: manter apenas equivalentes da MESMA categoria farmaceutica
    7. Ranquear por numero de tokens em comum
    8. Retornar top N com dados de preco

    Returns:
        Lista de dicts {ean, descricao, menor_preco, media_preco, qtd_entradas, demanda_mes}
    """
    from app.services.file_parser import _extract_tokens
    from app.services.offer_extractor import _classificar_forma_farmaceutica
    import re as _re_equiv

    tokens = _extract_tokens(descricao)
    # Tokens farmacologicos: >= 4 chars, apenas letras, NÃO termos genéricos
    drug_tokens = {t for t in tokens if len(t) >= 4 and t.isalpha() and t not in _GENERIC_FORM_TOKENS}

    if not drug_tokens:
        return []

    # Identify the PRIMARY molecule token — the LONGEST drug token
    # EXCLUDING salt prefixes (dicloridrato, fumarato, etc.)
    # Ex: "DICLORIDRATO DE HIDROXIZINA" → primary = "hidroxizina", NOT "dicloridrato"
    molecule_candidates = drug_tokens - _SALT_PREFIXES
    if molecule_candidates:
        primary_molecule = max(molecule_candidates, key=len)
    elif drug_tokens:
        primary_molecule = max(drug_tokens, key=len)
    else:
        primary_molecule = None

    # Also extract combined parts from original description (handle + separators)
    combined_parts = set()
    for part in _re_equiv.split(r'[+./]', descricao.upper()):
        sub_words = _re_equiv.findall(r'[A-Za-zÀ-ú]{4,}', part.strip())
        for w in sub_words:
            w_lower = w.lower()
            if w_lower not in _GENERIC_FORM_TOKENS:
                combined_parts.add(w_lower)
    drug_tokens = drug_tokens | combined_parts

    # Categoria do produto original — usada para filtrar equivalentes
    categoria_original = _classificar_forma_farmaceutica(descricao)

    # Contar score de cada EAN candidato (SOMENTE por drug_tokens, não genéricos)
    candidate_scores: dict[str, float] = {}
    for token in drug_tokens:
        for ean in _prefix_lookup(token, token_index):
            if ean != ean_principal:
                candidate_scores[ean] = candidate_scores.get(ean, 0) + 1.0

    if not candidate_scores:
        return []

    # Ranquear por score e filtrar por relevancia
    sorted_candidates = sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)

    equivalentes = []
    for ean, score in sorted_candidates:
        if len(equivalentes) >= max_equivalentes:
            break
        if score < 1:
            continue

        stats = ean_stats.get(ean)
        if not stats or stats.get("menor_preco") is None:
            continue

        # Extract drug tokens from candidate
        ean_tokens = _extract_tokens(stats.get("descricao", ""))
        ean_drug_tokens = {t for t in ean_tokens if len(t) >= 4 and t.isalpha() and t not in _GENERIC_FORM_TOKENS}

        # Also extract combined parts from candidate
        cand_combined = set()
        for part in _re_equiv.split(r'[+./]', stats.get("descricao", "").upper()):
            sub_words = _re_equiv.findall(r'[A-Za-zÀ-ú]{4,}', part.strip())
            for w in sub_words:
                w_lower = w.lower()
                if w_lower not in _GENERIC_FORM_TOKENS:
                    cand_combined.add(w_lower)
        all_cand_tokens = ean_drug_tokens | cand_combined

        common = drug_tokens & all_cand_tokens

        if not common:
            continue

        # PRIMARY MOLECULE CHECK (prefix-aware): the main molecule name
        # must appear in the equivalent.
        # This prevents VITAMINA D3 → VITAMINA C, HIDROXIZINA → BETAISTINA
        if primary_molecule:
            primary_found = False
            for ct in all_cand_tokens:
                if primary_molecule.startswith(ct) or ct.startswith(primary_molecule):
                    primary_found = True
                    break
            if not primary_found:
                continue

        # COVERAGE CHECK: at least 50% of the original drug tokens must be present
        # This prevents partial matches where only 1 of 3 molecules match
        coverage = len(common) / len(drug_tokens) if drug_tokens else 0
        if coverage < 0.5:
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
            "estoque_item": stats.get("estoque_item", 0),
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

    import re as _re
    _EAN_PATTERN = _re.compile(r"^\d{8,14}$")

    for row in rows:
        ean = row.get("ean")
        if ean:
            ean_str = str(ean).strip()
            # Validate: must be numeric with 8-14 digits (standard EAN/GTIN)
            # Filters out garbage like "00000SEM GTIN", "None", etc.
            if _EAN_PATTERN.match(ean_str) and ean_str not in ("0", "00000000"):
                # Also trim description while we're here (fix #7)
                if row.get("descricao"):
                    row["descricao"] = str(row["descricao"]).strip()
                by_ean[ean_str].append(row)

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
                # SANITY CHECK: se o resultado fica < 0.01, provável que pu
                # já esteja unitário (por comprimido) — não dividir novamente
                preco_normalizado = round(pu / mult, 4) if mult > 1 else pu
                if preco_normalizado < 0.01 and pu >= 0.01:
                    # Dupla divisão detectada — usar preço original
                    preco_normalizado = pu
                precos.append(preco_normalizado)
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
        preco_oferta_original = item.get("preco")  # Original box/pack price
        ean_oferta = item.get("ean")
        tipo_preco = item.get("tipo_preco", "absoluto")
        desconto_pct = item.get("desconto_percentual")
        multiplicador_embalagem = item.get("multiplicador_embalagem", 1.0)

        # Normalize offer price to unit price for COMPARISON only
        preco_oferta = preco_oferta_original
        if preco_oferta is not None and multiplicador_embalagem > 1:
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

            # Bug 15: Detectar multiplicador do histórico e equalizar escalas
            from app.services.offer_extractor import extrair_multiplicador_inteligente
            mult_historico = extrair_multiplicador_inteligente(match["descricao_arquivo"])
            
            # mult_efetivo é o multiplicador real para conversão unitário ↔ caixa
            # Se a oferta tem mult=1 mas o histórico tem "C/30", usar o do histórico
            mult_efetivo = multiplicador_embalagem
            if multiplicador_embalagem <= 1 and mult_historico > 1:
                mult_efetivo = mult_historico
                # A oferta é preço de CAIXA, normalizar para unitário
                if preco_oferta_original is not None:
                    preco_oferta = round(preco_oferta_original / mult_efetivo, 4)
                logger.info(
                    f"ESCALA CORRIGIDA: oferta mult=1 → usando mult_historico={mult_historico} | "
                    f"oferta='{descricao[:50]}' historico='{match['descricao_arquivo'][:50]}'"
                )
            elif mult_historico != multiplicador_embalagem and multiplicador_embalagem > 1:
                logger.warning(
                    f"MULT DISCREPANCIA: oferta mult={multiplicador_embalagem} vs "
                    f"historico mult={mult_historico} | "
                    f"oferta='{descricao[:50]}' historico='{match['descricao_arquivo'][:50]}'"
                )

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
                    "preco_oferta_caixa": preco_oferta_original,
                    "multiplicador_embalagem": multiplicador_embalagem,
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

            # Re-scale history to match the offer's packaging for the UI
            # Bug 15: usar mult_efetivo (pode ser do histórico se oferta mult=1)
            menor_hist_caixa = round(menor_hist * mult_efetivo, 4) if menor_hist else None

            # 5. RECOMENDACAO POR TEMPLATE (usando os valores em escala de caixa para exibicao coerente)
            recomendacao = gerar_recomendacao(
                classificacao=classificacao,
                variacao=variacao,
                menor_historico=menor_hist_caixa,
                preco_oferta=preco_oferta_original,
                demanda_mes=demanda,
                sugestao_pedido=sugestao,
                descricao=descricao,
                origem_menor=origem_menor,
                equivalentes=equivalentes,
                tipo_preco=tipo_preco,
                desconto_percentual=desconto_pct,
            )

            estoque_equiv = sum(eq.get("estoque_item", 0) for eq in equivalentes)

            # Re-scale equivalentes usando mult_efetivo
            for eq in equivalentes:
                if eq.get("menor_preco"):
                    eq["menor_preco"] = round(eq["menor_preco"] * mult_efetivo, 4)
                if eq.get("media_preco"):
                    eq["media_preco"] = round(eq["media_preco"] * mult_efetivo, 4)
                if eq.get("maior_preco"):
                    eq["maior_preco"] = round(eq["maior_preco"] * mult_efetivo, 4)

            itens_resultado.append({
                "descricao_original": descricao,
                "preco_oferta": preco_oferta_original,  # Mantem preço original da caixa
                "preco_oferta_caixa": preco_oferta_original,
                "multiplicador_embalagem": mult_efetivo,  # Bug 15: usar mult real detectado
                "ean": match["ean"],
                "descricao_produto": match["descricao_arquivo"],
                "menor_historico": menor_hist_caixa,  # Histórico escalado para o mesmo multiplicador
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
            estoque_equiv = sum(eq.get("estoque_item", 0) for eq in equivalentes)

            # Bug 19: Detectar multiplicador dos equivalentes para equalizar escala
            from app.services.offer_extractor import extrair_multiplicador_inteligente
            mult_efetivo_nomatch = multiplicador_embalagem
            if equivalentes and multiplicador_embalagem <= 1:
                # Usar o multiplicador do equivalente mais relevante (primeiro)
                eq_desc = equivalentes[0].get("descricao", "")
                mult_eq = extrair_multiplicador_inteligente(eq_desc)
                if mult_eq > 1:
                    mult_efetivo_nomatch = mult_eq
                    # Normalizar preço da oferta para unitário
                    if preco_oferta_original is not None:
                        preco_oferta = round(preco_oferta_original / mult_efetivo_nomatch, 4)

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

            # Re-scale history to match the offer's packaging for the UI
            menor_hist_equiv_caixa = round(menor_hist_equiv * mult_efetivo_nomatch, 4) if menor_hist_equiv else None

            recomendacao = gerar_recomendacao(
                classificacao=classificacao if menor_hist_equiv else "descartavel",
                variacao=variacao,
                menor_historico=menor_hist_equiv_caixa,
                preco_oferta=preco_oferta_original,
                demanda_mes=0,
                sugestao_pedido=0,
                descricao=descricao,
                origem_menor=origem_menor,
                equivalentes=equivalentes,
                tipo_preco=tipo_preco,
                desconto_percentual=desconto_pct,
            )

            # Re-scale equivalentes
            for eq in equivalentes:
                if eq.get("menor_preco"):
                    eq["menor_preco"] = round(eq["menor_preco"] * mult_efetivo_nomatch, 4)
                if eq.get("media_preco"):
                    eq["media_preco"] = round(eq["media_preco"] * mult_efetivo_nomatch, 4)
                if eq.get("maior_preco"):
                    eq["maior_preco"] = round(eq["maior_preco"] * mult_efetivo_nomatch, 4)

            itens_resultado.append({
                "descricao_original": descricao,
                "preco_oferta": preco_oferta_original,
                "preco_oferta_caixa": preco_oferta_original,
                "multiplicador_embalagem": mult_efetivo_nomatch,
                "ean": None,
                "descricao_produto": None,
                "menor_historico": menor_hist_equiv_caixa,
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
