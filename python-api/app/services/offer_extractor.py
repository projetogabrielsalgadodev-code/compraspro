"""
Offer Extractor v2 — Extrai itens estruturados do texto bruto de ofertas.

Estrategia:  LLM-first  (entende hierarquia, %, blocos, emojis)
             Regex-sanitizer  (limpa texto antes de enviar ao LLM)
             Regex-fallback   (se LLM falhar / timeout)

Suporta os formatos reais de WhatsApp:
- Preco absoluto:  "Produto R$ 24,17"
- Desconto %:      "BENEGRIP 30%"
- Hierarquico:     "Olmesartana" -> sub-linhas "20 Mg 10,97"
- Bloco categoria: "Desconto 20%" aplicado a uma lista de produtos
- Emojis/setas:    seta, ponto, foguinho, etc.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


# ─── Pre-processamento / Sanitizacao ──────────────────────────────────────────

# Emojis comuns em ofertas WhatsApp
_EMOJI_PATTERNS = re.compile(
    r"[\U0001F4A5\U0001F525\U0001F4A8\U0001F4E6\U0001F48A\U0001F4A9"
    r"\U0001F4B0\U0001F4B2\U0001F4B5\U0001F4B6\U0001F4B7\U0001F4B8"
    r"\U0001F4B3\U0001F389\U0001F38A\U0001F381\U0001F380\U0001F947"
    r"\U0001F948\U0001F949\U0001F3C6\U0001F396\U0001F31F\U00002B50"
    r"\U00002728\U0001F4AB\U0001F4A2\U0001F4A0\U0001F6A8\U00002757"
    r"\U00002755\U00002714\U0000274C\U00002705\U000026A0\U0001F534"
    r"\U0001F535\U0001F7E2\U0001F7E1\U0001F7E0\U0001F48E\U0001F4E2"
    r"\U0001F4E3\U0001F3AF\U0001F50A\U0001F50B\U0001F50C\U0001F50D"
    r"\U00002611\U00002B06\U00002B07\U000027A1\U00002B05\U0001F449"
    r"\U0001F448\U0001F446\U0001F447\U0001F4CC\U0001F4CD\U0001F4CE"
    r"\U0001F4CF\U0001F4D0\U0001F4DD\U0001F4D1\U0001F4D2\U0001F4D3"
    r"\U0001F4D4\U0001F4D5\U0001F4D6\U0001F4D7\U0001F4D8\U0001F4D9]"
    r"|[\u2600-\u27BF]"      # misc symbols
    r"|[\uFE00-\uFE0F]"     # variation selectors
    r"|[\u200D]"             # ZWJ
    r"|[\u20E3]"             # combining encl keycap
    r"|[\uD83C-\uDBFF\uDC00-\uDFFF]"  # surrogate pairs
)

# Keycap digit emojis: 0️⃣ 1️⃣ 2️⃣ ... 9️⃣
_KEYCAP_PATTERN = re.compile(r"(\d)\uFE0F?\u20E3")


def sanitizar_texto_oferta(texto: str) -> str:
    """
    Limpa texto de oferta WhatsApp mantendo informacao semantica.
    - Substitui setas arrow emojis por ->
    - Converte keycap digits (2️⃣0️⃣ -> 20)
    - Remove emojis decorativos
    - Normaliza whitespace
    """
    # Converter keycap digits ANTES de remover emojis
    texto = _KEYCAP_PATTERN.sub(r"\1", texto)

    # Setas
    texto = texto.replace("\u27a1\ufe0f", "->")
    texto = texto.replace("\u27a1", "->")
    texto = texto.replace("\u2b95", "->")
    texto = texto.replace("\u2192", "->")
    texto = re.sub(r"➡️?", "->", texto)

    # Remove emojis decorativos restantes
    texto = _EMOJI_PATTERNS.sub("", texto)
    # Remove qualquer emoji restante via broad Unicode range
    texto = re.sub(
        r"[\U0001F300-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF]",
        "",
        texto,
    )

    # Normaliza whitespace
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)

    return texto.strip()


# ─── Extracao via LLM ─────────────────────────────────────────────────────────

_EXTRACTION_PROMPT = """Voce e um extrator de dados de ofertas farmaceuticas recebidas por WhatsApp.

Extraia TODOS os itens de compra da mensagem abaixo. Retorne APENAS o JSON, sem explicacao.

Regras IMPORTANTES:
1. **Preco absoluto** (ex: "R$ 24,17" ou "24,17" ou "->13,45"): extrair como tipo_preco="absoluto" com o preco numerico.
2. **Desconto percentual** (ex: "BENEGRIP 30%" ou "Desconto 20%"): extrair como tipo_preco="percentual_desconto" com desconto_percentual=30.
3. **Hierarquia pai-filho** (ex: "Olmesartana" na linha de cima, "20 Mg 10,97" / "40 Mg 13,60" nas sub-linhas): gerar UM item SEPARADO para cada variante, combinando o nome pai com a variante.
   Exemplo: "Olmesartana 20mg" preco=10.97 e "Olmesartana 40mg" preco=13.60
4. **Bloco de categoria com desconto** (ex: "Rebaixa Linha Luftal Desconto 20%" seguido de uma lista de produtos): cada produto herda o desconto do bloco. tipo_preco="percentual_desconto".
5. **Produtos sem preco e sem desconto**: incluir com tipo_preco="sem_preco" apenas se forem claramente um produto farmaceutico. Nao incluir frases de marketing.
6. **multiplicador_embalagem** — REGRA CRÍTICA para cálculo correto:
   O multiplicador indica QUANTAS UNIDADES VENDÁVEIS estão no pacote.
   
   SÓLIDOS (comprimidos, cápsulas):
   - "C/36CPR" → multiplicador_embalagem = 36 (36 comprimidos)
   - "CX 20 COMP" → multiplicador_embalagem = 20
   - "30X10" em comprimidos → multiplicador_embalagem = 300 (30 blisters x 10 comp = 300 comp total)
   - "C/1CPR" → multiplicador_embalagem = 1
   
   LÍQUIDOS (xaropes, soluções, gotas, sprays):
   - "C/30ML", "100ML", "60ML" → multiplicador_embalagem = 1 (é UM frasco, ML é volume, não unidades!)
   - "XAROPE 100ML" → multiplicador_embalagem = 1
   - "GTS 30ML" → multiplicador_embalagem = 1
   
   TÓPICOS (cremes, pomadas, géis):
   - "CREME 30G", "POM 20G" → multiplicador_embalagem = 1 (é UMA bisnaga, G é peso)
   
   SACHÊS/ENVELOPES (displays):
   - "SACHÊ 30X2" → multiplicador_embalagem = 30 (30 sachês de 2, preço por sachê)
   - "FRAÇÃO 2 ENV" → multiplicador_embalagem = 1 (1 sachê de 2 envelopes)
   
   SEM INDICAÇÃO → multiplicador_embalagem = 1
   
7. **Pedido minimo**: ignorar linhas de "Pedido minimo: X unidades".
8. **Mensagens de marketing**: ignorar completamente.

Formato de saida:
```json
{{
  "fornecedor": "nome do fornecedor/laboratorio ou null",
  "itens": [
    {{
      "descricao": "nome completo do produto com dosagem e apresentacao",
      "preco": 24.17,
      "ean": "codigo_de_barras",
      "tipo_preco": "absoluto",
      "desconto_percentual": null,
      "multiplicador_embalagem": 60
    }}
  ]
}}
```

Mensagem de oferta:
---
{texto}
---"""


async def extrair_itens_llm(texto: str) -> tuple[str | None, list[dict[str, Any]]]:
    """
    Extrai itens usando Claude com prompt expandido.
    Entende: hierarquia, %, blocos, emojis, formatos WhatsApp.
    
    Returns:
        fornecedor, itens, metrics
    """
    from agno.agent import Agent
    from agno.models.anthropic import Claude
    from app.db.supabase_client import get_settings

    settings = get_settings()

    texto_limpo = sanitizar_texto_oferta(texto)
    prompt = _EXTRACTION_PROMPT.format(texto=texto_limpo)

    model = Claude(
        id=settings.anthropic_model or "claude-sonnet-4-5-20250929",
        api_key=settings.anthropic_api_key,
        max_tokens=4096,
        temperature=0.0,
    )

    agent = Agent(
        model=model,
        instructions="Voce e um extrator de dados. Extraia itens de ofertas farmaceuticas e retorne JSON puro. Sem explicacao.",
        markdown=False,
    )

    response = await agent.arun(prompt)
    content = response.content

    # Extrair Métricas de Uso
    metrics = {"tokens_utilizados": 0, "custo_reais": 0.0}
    if hasattr(response, "metrics") and response.metrics:
        # Agno metrics are usually inside response.metrics
        metr_dict = response.metrics if isinstance(response.metrics, dict) else (getattr(response, "run_metrics", None) or {})
        
        input_tokens = metr_dict.get("input_tokens", metr_dict.get("prompt_tokens", 0))
        output_tokens = metr_dict.get("output_tokens", metr_dict.get("completion_tokens", 0))
        
        # Agno may sometimes return a list or dict for multi-turn metrics
        if isinstance(input_tokens, list): input_tokens = sum(input_tokens)
        elif isinstance(input_tokens, dict): input_tokens = sum(input_tokens.values())
        
        if isinstance(output_tokens, list): output_tokens = sum(output_tokens)
        elif isinstance(output_tokens, dict): output_tokens = sum(output_tokens.values())
        
        input_tokens = int(input_tokens)
        output_tokens = int(output_tokens)
        
        total_tokens = metr_dict.get("total_tokens", input_tokens + output_tokens)
        if isinstance(total_tokens, list): total_tokens = sum(total_tokens)
        elif isinstance(total_tokens, dict): total_tokens = sum(total_tokens.values())
        total_tokens = int(total_tokens)
        
        metrics["tokens_utilizados"] = total_tokens
        
        # Custo aproximado para Claude 3.5 Sonnet (USD 3 / 1M input, USD 15 / 1M output) -> Dólar a ~R$ 5.50
        # Input: R$ 16,50 por milhão | Output: R$ 82,50 por milhão
        custo_input = (input_tokens / 1_000_000) * 16.50
        custo_output = (output_tokens / 1_000_000) * 82.50
        metrics["custo_reais"] = round(custo_input + custo_output, 4)

    # Parsear JSON da resposta
    if isinstance(content, str):
        content = re.sub(r"```(?:json)?\s*", "", content).strip()
        content = re.sub(r"```\s*$", "", content).strip()

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # Robust: find outermost { ... } using rfind for last }
            start = content.find("{")
            end = content.rfind("}")
            if start >= 0 and end > start:
                try:
                    data = json.loads(content[start:end + 1])
                except json.JSONDecodeError:
                    logger.error(f"LLM retornou JSON invalido: {content[:500]}")
                    return None, [], metrics
            else:
                logger.error(f"LLM nao retornou JSON: {content[:300]}")
                return None, [], metrics
    elif isinstance(content, dict):
        data = content
    else:
        logger.error(f"LLM retornou tipo inesperado: {type(content)}")
        return None, [], metrics

    fornecedor = data.get("fornecedor")
    itens_raw = data.get("itens", [])

    itens = []
    for item in itens_raw:
        desc = item.get("descricao", "").strip()
        preco = item.get("preco")
        ean = item.get("ean")
        tipo = item.get("tipo_preco", "absoluto")
        desconto_pct = item.get("desconto_percentual")

        if not desc or len(desc) < 2:
            continue

        # Normalizar
        if preco is not None:
            try:
                preco = float(preco)
                if preco <= 0:
                    preco = None
            except (ValueError, TypeError):
                preco = None

        if desconto_pct is not None:
            try:
                desconto_pct = float(desconto_pct)
            except (ValueError, TypeError):
                desconto_pct = None

        multiplicador_embalagem = item.get("multiplicador_embalagem", 1)
        try:
            multiplicador_embalagem = float(multiplicador_embalagem)
            if multiplicador_embalagem <= 0:
                multiplicador_embalagem = 1
        except (ValueError, TypeError):
            multiplicador_embalagem = 1
            
        # Fallback para regex caso o LLM não identifique corretamente (ex: retorne 1 para C/36)
        if multiplicador_embalagem == 1:
            mult_regex = _extrair_multiplicador_regex(desc)
            if mult_regex > 1:
                multiplicador_embalagem = mult_regex

        # Validar combinacao tipo vs dados
        if tipo == "absoluto" and preco is None:
            tipo = "sem_preco"
        elif tipo == "percentual_desconto" and desconto_pct is None:
            tipo = "sem_preco"

        itens.append({
            "descricao": desc,
            "preco": preco,
            "ean": str(ean) if ean else None,
            "tipo_preco": tipo,
            "desconto_percentual": desconto_pct,
            "multiplicador_embalagem": multiplicador_embalagem
        })

    logger.info(f"LLM extraiu {len(itens)} itens, fornecedor={fornecedor}")
    return fornecedor, itens, metrics


# ─── Extracao Regex (fallback) ────────────────────────────────────────────────

def _limpar_descricao(desc: str) -> str:
    """Remove artefatos comuns da descricao extraida."""
    desc = re.sub(r"[\s\-\u2013\u2014=:]+$", "", desc).strip()
    desc = re.sub(r"^\d+[\.)\-\u2013]\s*", "", desc).strip()
    return desc


def _parse_preco_br(texto: str) -> float | None:
    """Parseia preco em formato brasileiro: 24,17 ou 24.17 ou 1.234,56 ou 15.1905"""
    texto = texto.strip().replace(" ", "")
    # Brazilian thousands format: 1.234,56
    m = re.match(r"(\d{1,3}(?:\.\d{3})*,\d{2,})$", texto)
    if m:
        return float(m.group(1).replace(".", "").replace(",", "."))
    # Simple comma decimal: 24,17 or 24,1705
    m = re.match(r"(\d+,\d{2,})$", texto)
    if m:
        return float(m.group(1).replace(",", "."))
    # English dot decimal: 24.17 or 15.1905
    m = re.match(r"(\d+\.\d+)$", texto)
    if m:
        return float(m.group(1))
    # Integer
    m = re.match(r"(\d+)$", texto)
    if m:
        val = float(m.group(1))
        return val if val > 0 else None
    return None

def _classificar_forma_farmaceutica(desc: str) -> str:
    """
    Classifica a forma farmacêutica do produto pela descrição.
    
    Retorna:
      'liquido'  - xaropes, soluções, gotas, suspensões (vendidos por frasco)
      'topico'   - cremes, pomadas, géis (vendidos por bisnaga/tubo)
      'solido'   - comprimidos, cápsulas, drágeas (vendidos por unidade contável)
      'sache'    - sachês, envelopes, fração (vendidos por unidade de sachê)
      'po'       - pós em frasco/pote (Sal de Fruta 100G = 1 frasco)
      'unknown'  - não identificado
    """
    d = desc.upper()
    
    # Líquidos — preço por FRASCO, não por ML
    liquido_markers = [
        "XAROPE", "XPE ", "XPE.", "XAROPE",
        "SOL NASAL", "SOL ORAL", "SOL ", "SOLUCAO", "SOLUÇÃO",
        "SUSP ", "SUSPENSAO", "SUSPENSÃO",
        "GTS ", "GOTAS", " GTS",
        "SPRAY", "COLIRI", "COLIRIO",
        "ELIXIR",
    ]
    for marker in liquido_markers:
        if marker in d:
            return "liquido"
    
    # Soluções genéricas: "SOL" seguido de forma indicando líquido
    # Mas "SOL ADULTO" em NEOSORO é solução nasal
    if re.search(r"\bSOL\b", d) and ("FR " in d or "ML" in d):
        return "liquido"
    
    # Tópicos — preço por UNIDADE (bisnaga/tubo), não por grama
    topico_markers = [
        "CREME", "POMADA", "POM ", "GEL ",
        "LOCAO", "LOÇÃO", "SHAMPOO",
        " BG ", "BISNAGA",
    ]
    for marker in topico_markers:
        if marker in d:
            return "topico"
    
    # Sachês / Envelopes / Fração
    sache_markers = [
        "SACHE", "SACHÊ", "FRACAO", "FRAÇÃO",
        " ENV ", "ENV.", "ENVELOPE",
    ]
    for marker in sache_markers:
        if marker in d:
            return "sache"
    
    # Sólidos contáveis — preço por comprimido/cápsula
    solido_markers = [
        "CPR", "COMP", "CAP", "DRG", "DRAGEA", "DRÁGEA",
        "PASTILHA", "PAST ",
    ]
    for marker in solido_markers:
        if marker in d:
            return "solido"
    
    # Pó em frasco/pote (ex: SAL DE FRUTA FR 100G, SAL DE FRUTA 100GRS)
    if re.search(r"\bFR\s+\d+\s*G(?:RS)?\b", d):
        return "po"
    # Peso sem frasco mas sem marcador de sólido/líquido (ex: "100GRS", "100G")
    if re.search(r"\b\d+\s*G(?:RS)?\b", d) and not re.search(r"(?:CPR|COMP|CAP|DRG|SACHE|ENV|XAROPE|XPE|SOL|GTS|SPRAY|CREME|POM|GEL|SUSP)", d):
        return "po"
    
    # Fallback: se tem "C/" ou "CX" seguido de número, provavelmente é contável
    if re.search(r"\b[cC][/xX]\s*\d+\b", d):
        return "solido"
    
    return "unknown"


def extrair_multiplicador_inteligente(desc: str) -> float:
    """
    Extrai o multiplicador de embalagem DE FORMA INTELIGENTE por categoria de produto.
    
    Regras por categoria:
      - LÍQUIDO (xarope, solução, gotas): mult = 1 (1 frasco, independente dos ML)
      - TÓPICO (creme, pomada, gel): mult = 1 (1 bisnaga/tubo)
      - PÓ em frasco (Sal de Fruta 100G frasco): mult = 1 (1 frasco)
      - SÓLIDO (CPR, COMP, CAP): 
          - C/36CPR → 36 (total de comprimidos)
          - 30X10 → 300 (display de sólidos = total comprimidos)
      - SACHÊ/ENVELOPE:
          - Fração 2 ENV → mult = 1 (1 sachê de 2 envelopes)
          - Display 30X2 sachê → mult = 30 (30 sachês, preço por sachê)
          - C/150 25X6 sachê → mult = 25 (25 blisters de 6, preço por blister)
    
    A mesma função é usada tanto para oferta quanto para histórico,
    garantindo que a comparação de preço unitário seja justa.
    """
    # Remove controlled substance markers (C1), (C2), (C4), (C5) that
    # would otherwise be matched by the C/N pattern as "Com 1 unidade"
    desc = re.sub(r"\(C[1-5]\)", "", desc).strip()
    
    categoria = _classificar_forma_farmaceutica(desc)
    
    # LÍQUIDOS e TÓPICOS: sempre mult=1 (1 frasco/bisnaga)
    if categoria in ("liquido", "topico", "po"):
        return 1.0
    
    # SACHÊS / ENVELOPES
    if categoria == "sache":
        # Display NxM de sachês → mult = N (número de sachês no display)
        m_display = re.search(r"\b(\d+)\s*[xX]\s*(\d+)\b", desc)
        if m_display:
            n = float(m_display.group(1))
            return n if n > 0 else 1.0
        # C/150 com NxM → usar N do NxM (ex: C/150CPR 25X6 → mult = 25)
        # Sem NxM: sachê individual (FRACAO 2 ENV) → mult = 1
        m_c = re.search(r"\b[cC]/?\s*(\d+)\b", desc)
        if m_c:
            return float(m_c.group(1)) if float(m_c.group(1)) > 0 else 1.0
        return 1.0
    
    # SÓLIDOS (comprimidos, cápsulas, drágeas)
    if categoria == "solido":
        # 1. NxM para sólidos = total de comprimidos (30x10 = 300)
        m_box = re.search(r"\b(\d+)\s*[xX]\s*(\d+)\b", desc)
        if m_box:
            mult = float(m_box.group(1)) * float(m_box.group(2))
            return mult if mult > 0 else 1.0
        
        # 2. C/N onde N é quantidade de comprimidos
        m_c = re.search(r"\b[cC]/?\s*(\d+)\b", desc)
        if m_c:
            mult = float(m_c.group(1))
            return mult if mult > 0 else 1.0
        
        # 3. CX N ou N COMP sem prefixo C/
        m_cx = re.search(r"\b(?:CX|cx)\s+(\d+)\b", desc, re.IGNORECASE)
        if m_cx:
            mult = float(m_cx.group(1))
            return mult if mult > 0 else 1.0
        
        m_comp = re.search(r"\b(\d+)\s*(?:COMP|CPR|CAPS|CAP|DRG)\b", desc, re.IGNORECASE)
        if m_comp:
            mult = float(m_comp.group(1))
            return mult if mult > 0 else 1.0
        
        return 1.0
    
    # UNKNOWN — fallback conservador: tentar C/ se existir, senão 1
    m_c = re.search(r"\b[cC]/?\s*(\d+)\s*(?:CPR|COMP|CAPS|CAP|DRG)\b", desc, re.IGNORECASE)
    if m_c:
        mult = float(m_c.group(1))
        return mult if mult > 0 else 1.0
    
    return 1.0


def _extrair_multiplicador_regex(desc: str) -> float:
    """Wrapper de compatibilidade → delega para extrair_multiplicador_inteligente."""
    return extrair_multiplicador_inteligente(desc)

def extrair_itens_regex(texto: str) -> list[dict[str, Any]]:
    """
    Extrai itens de uma oferta usando regex — zero custo, instantaneo.
    Usado como FALLBACK se LLM falhar.

    Suporta hierarquia pai/filho:
    - Linha sem preco = potencial pai
    - Linhas com "->" ou indentadas com preco = filhos que herdam nome do pai
    """
    itens = []
    texto_limpo = sanitizar_texto_oferta(texto)
    current_parent: str | None = None  # Track parent for hierarchical items
    current_block_pct: float | None = None  # Track block-level discount %

    linhas = texto_limpo.strip().split("\n")
    skip_words = {"pedido", "minimo", "unidades", "promocao", "valida", "aproveite",
                  "ofertas", "estoque", "live", "hoje", "brindes", "verifique"}

    for idx, linha in enumerate(linhas):
        linha = linha.strip()
        if not linha or len(linha) < 3:
            current_parent = None
            current_block_pct = None
            continue

        lower = linha.lower()
        # Skip marketing / pedido minimo lines
        if any(w in lower for w in skip_words):
            continue

        # Detect block-level discount: "Desconto XX%" or "Desconto 20%"
        m_block = re.match(r"(?:desconto|rebaixa|promo).*?(\d+(?:[.,]\d+)?)\s*%", linha, re.IGNORECASE)
        if m_block:
            try:
                current_block_pct = float(m_block.group(1).replace(",", "."))
            except ValueError:
                pass
            continue

        # Tentar extrair EAN (13 digitos)
        ean_match = re.search(r"\b(\d{13})\b", linha)
        ean = ean_match.group(1) if ean_match else None

        # Is this line an arrow-prefixed child? ("->XX,XX" or "->4 Mg 3,17")
        is_arrow = linha.startswith("->") or linha.startswith("-> ")
        if is_arrow:
            linha_clean = re.sub(r"^->\s*", "", linha).strip()
        else:
            linha_clean = linha

        # Pattern 1: "Descricao - R$ XX,XX" ou "Descricao R$ XX,XX"
        m = re.match(
            r"(.+?)\s*[-\u2013\u2014]?\s*R\$\s*([\d.,]+)",
            linha_clean, re.IGNORECASE
        )
        if m:
            desc = _limpar_descricao(m.group(1))
            preco = _parse_preco_br(m.group(2))
            if desc and preco and preco > 0:
                if ean:
                    desc = desc.replace(ean, "").strip()
                # Prepend parent if this is a child line
                if is_arrow and current_parent:
                    desc = f"{current_parent} {desc}"
                elif not is_arrow:
                    current_parent = desc  # This becomes the parent
                itens.append({
                    "descricao": desc,
                    "preco": preco,
                    "ean": ean,
                    "tipo_preco": "absoluto",
                    "desconto_percentual": None,
                    "multiplicador_embalagem": _extrair_multiplicador_regex(desc),
                })
                continue

        # Pattern 2: "Descricao XX,XX" (sem R$) or "-> Desc XX,XX"
        m = re.match(r"(.+?)\s+(\d+[.,]\d{2,})\s*(?:\(.*\))?\s*$", linha_clean)
        if m:
            desc = _limpar_descricao(m.group(1))
            preco = _parse_preco_br(m.group(2))
            if desc and preco and preco > 0 and len(desc) >= 2:
                if ean:
                    desc = desc.replace(ean, "").strip()
                # Prepend parent if arrow
                if is_arrow and current_parent:
                    desc = f"{current_parent} {desc}"
                elif not is_arrow and not re.search(r"\d+[.,]\d{2}", desc):
                    current_parent = desc
                itens.append({
                    "descricao": desc,
                    "preco": preco,
                    "ean": ean,
                    "tipo_preco": "absoluto",
                    "desconto_percentual": None,
                    "multiplicador_embalagem": _extrair_multiplicador_regex(desc),
                })
                continue

        # Pattern 2b: "-> XX,XX" (solo price, no description — inherit parent)
        m = re.match(r"(\d+[.,]\d{2})\s*$", linha_clean)
        if m and is_arrow and current_parent:
            preco = _parse_preco_br(m.group(1))
            if preco and preco > 0:
                itens.append({
                    "descricao": current_parent,
                    "preco": preco,
                    "ean": None,
                    "tipo_preco": "absoluto",
                    "desconto_percentual": None,
                    "multiplicador_embalagem": _extrair_multiplicador_regex(current_parent),
                })
                continue

        # Pattern 3: "PRODUTO XX%" (desconto percentual)
        m = re.match(r"(.+?)\s+(\d+(?:[.,]\d+)?)\s*%\s*$", linha_clean)
        if m:
            desc = _limpar_descricao(m.group(1))
            pct_str = m.group(2).replace(",", ".")
            try:
                pct = float(pct_str)
                if desc and 0 < pct <= 100 and len(desc) > 2:
                    itens.append({
                        "descricao": desc,
                        "preco": None,
                        "ean": None,
                        "tipo_preco": "percentual_desconto",
                        "desconto_percentual": pct,
                        "multiplicador_embalagem": _extrair_multiplicador_regex(desc),
                    })
            except ValueError:
                pass
            continue

        # Pattern 4: Product in a block-discount context (no price, has block %)
        if current_block_pct and not re.search(r"\d+[.,]\d{2}", linha_clean):
            desc = _limpar_descricao(linha_clean)
            if desc and len(desc) > 3:
                itens.append({
                    "descricao": desc,
                    "preco": None,
                    "ean": None,
                    "tipo_preco": "percentual_desconto",
                    "desconto_percentual": current_block_pct,
                    "multiplicador_embalagem": _extrair_multiplicador_regex(desc),
                })
                continue

        # No match — this line might be a parent for next arrow lines
        if not is_arrow and not re.search(r"\d+[.,]\d{2}", linha_clean) and len(linha_clean) > 3:
            # Check if next non-empty line is an arrow
            for next_idx in range(idx + 1, min(idx + 3, len(linhas))):
                next_line = linhas[next_idx].strip()
                if next_line:
                    if next_line.startswith("->") or re.match(r"\d+[.,]\d{2}", next_line):
                        current_parent = _limpar_descricao(linha_clean)
                    break

    logger.info(f"Regex extraiu {len(itens)} itens da oferta")
    return itens


# ─── Deteccao de Fornecedor ──────────────────────────────────────────────────

def _detectar_fornecedor_regex(texto: str) -> str | None:
    """Tenta detectar o nome do fornecedor no cabecalho da oferta."""
    linhas = texto.strip().split("\n")

    for linha in linhas[:5]:
        linha = linha.strip()
        if not linha:
            continue

        m = re.match(
            r"(?:oferta|promocao|promo|fornecedor|lab|distribuidora)\s*[:\-\u2013]?\s*(.+)",
            linha, re.IGNORECASE
        )
        if m:
            nome = m.group(1).strip().rstrip("-\u2013:. ")
            if nome and len(nome) >= 3:
                return nome

        if not re.search(r"\d+[.,]\d{2}", linha) and len(linha) > 3 and len(linha) < 80:
            if len(linhas) > 1 and re.search(r"\d+[.,]\d{2}", linhas[1]):
                return linha.strip().rstrip("-\u2013:. ")

    return None


# ─── Orquestrador Principal ──────────────────────────────────────────────────

async def extrair_itens(texto: str) -> tuple[str | None, list[dict[str, Any]], dict[str, Any]]:
    """
    Extrai itens da oferta: LLM primeiro (entende tudo), regex como fallback.

    Returns:
        Tuple de (fornecedor, lista de itens [{descricao, preco, ean, tipo_preco, desconto_percentual}], metrics)
    """
    # LLM primeiro — entende hierarquia, %, blocos, emojis
    metrics = {"tokens_utilizados": 0, "custo_reais": 0.0}
    try:
        fornecedor, itens, metrics = await extrair_itens_llm(texto)
        if itens:
            logger.info(f"Extracao via LLM: {len(itens)} itens, fornecedor={fornecedor}, custo={metrics.get('custo_reais')}")
            return fornecedor, itens, metrics
    except Exception as e:
        logger.warning(f"LLM falhou na extracao: {e}")

    # Fallback: regex
    logger.info("LLM falhou ou retornou 0 itens, tentando regex como fallback")
    itens = extrair_itens_regex(texto)
    fornecedor = _detectar_fornecedor_regex(texto)

    if itens:
        logger.info(f"Extracao via REGEX (fallback): {len(itens)} itens")
        return fornecedor, itens, metrics

    logger.warning("Nenhum item extraido (LLM + regex falharam)")
    return None, [], metrics
