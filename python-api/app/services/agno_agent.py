"""
Agno Agent — Agente de análise de ofertas farmacêuticas.

Usa Claude (Anthropic) como modelo e tools customizadas que consultam
o Supabase diretamente para matching, histórico e classificação.

Compatível com Agno 1.4.x:
- Tools recebem `agent: Agent` (não RunContext)
- session_state é definido no construtor do Agent
- SEM response_model: parsing manual robusto do conteúdo
- Resposta via `agent.arun()` retorna RunResponse com .content e .messages
"""
from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

from agno.agent import Agent
from agno.models.anthropic import Claude

from app.db.supabase_client import get_settings, get_supabase_client
from app.models.schemas import AnaliseOfertaAgnoOutput
from app.services.agno_tools import AGNO_TOOLS

logger = logging.getLogger(__name__)


# ─── System prompt com regras de negócio ──────────────────────────────────────

SYSTEM_INSTRUCTIONS = """Você é um agente especialista em análise de ofertas para distribuidoras farmacêuticas.

## Seu papel
Você recebe ofertas de fornecedores e deve analisar cada item individualmente,
cruzando com o catálogo e histórico de preços da empresa.

## Fluxo obrigatório para CADA item da oferta:
1. **Extrair** os dados do item (descrição, EAN se disponível, preço).
2. **Buscar** o produto no catálogo:
   - Primeiro por EAN (se disponível) usando `buscar_produto_estoque`
   - Se não encontrar, usar `buscar_produto_por_descricao`
3. **Consultar histórico** de preços usando `consultar_historico_precos`
4. **Buscar equivalentes** farmacêuticos usando `buscar_equivalentes` (se o produto tiver princípio ativo)
5. **Classificar** a oferta usando `classificar_item_oferta`

## Regra de cálculo de preço (NUNCA violar):
- Preço unitário histórico = Valor Total do Item ÷ Quantidade Unitária
- NUNCA calcular preço de outra forma
- O "menor_historico" = menor preço unitário histórico jamais pago por aquele item

## Cálculo da Variação Percentual (Var.%):
- variacao_percentual = ((menor_historico - preco_oferta) / menor_historico) × 100
- Se POSITIVO → oferta é MAIS BARATA que o menor histórico (DESCONTO) ✅
- Se NEGATIVO → oferta é MAIS CARA que o menor histórico (ÁGIO) ❌
- Exemplo: menor_historico=R$5.77, preco_oferta=R$4.24 → var = ((5.77-4.24)/5.77)×100 = 26.5% (desconto)

## Sugestão de Pedido:
- sugestao_pedido = max(0, (demanda_mes × 3) - estoque_item)
- Significado: sugestão para cobrir ~3 meses de demanda, descontando estoque atual
- Se não houver dados de estoque/demanda, usar sugestao_pedido = 0

## Regras de classificação (NÃO altere):
- **ouro**: variacao_percentual ≥ 20% (desconto forte vs menor histórico). Comprar imediatamente.
- **prata**: variacao_percentual entre 5% e 20%. Boa oportunidade.
- **atencao**: variacao_percentual entre 0% e 5%, OU há estoque de equivalentes. Revisar antes.
- **descartavel**: variacao_percentual < 0% (oferta mais cara que histórico) OU sem dados. Não comprar.

## Regras de confiança do match:
- **alto**: Encontrado por EAN exato ou ≥2 tokens-chave (nome do fármaco) em comum
- **medio**: Encontrado por descrição com 1 token-chave em comum
- **baixo**: Match aproximado ou não encontrado

## Regras para recomendação:
- Escreva em português brasileiro, 1-2 frases objetivas
- SEMPRE inclua dados numéricos: % desconto/ágio, cobertura em dias/meses, preço comparativo
- Para classificação "ouro": enfatize urgência e oportunidade, cite o desconto e menor histórico
- Para "prata": mencione o desconto moderado e sugira aproveitamento
- Para "atencao": mencione estoque de equivalentes se houver, sugira revisão humana
- Para "descartavel": explique por que não comprar (preço acima do histórico, sem dados, etc.)

## FORMATO DE SAÍDA OBRIGATÓRIO — RESPEITE EXATAMENTE ESTES NOMES DE CAMPO:
Após concluir todas as análises, retorne APENAS um JSON puro (SEM blocos markdown, SEM ```json, SEM texto antes ou depois).
Use EXATAMENTE estes nomes de campo, sem inventar campos extras:

{
  "fornecedor": "<nome do fornecedor ou null>",
  "itens": [
    {
      "descricao_original": "<descrição do item como aparece na oferta>",
      "preco_oferta": 0.00,
      "ean": "<EAN encontrado ou null>",
      "descricao_produto": "<descrição do catálogo ou null>",
      "menor_historico": 0.00,
      "variacao_percentual": 0.0,
      "estoque_item": 0,
      "demanda_mes": 0.0,
      "sugestao_pedido": 0,
      "estoque_equivalentes": 0,
      "classificacao": "ouro|prata|atencao|descartavel",
      "confianca_match": "alto|medio|baixo",
      "recomendacao": "<1-2 frases em pt-BR com dados numéricos>",
      "equivalentes": []
    }
  ]
}

IMPORTANTE: Retorne APENAS o JSON acima. Não use blocos markdown (```). Não inclua texto explicativo.
Seja CONCISO no JSON: não inclua sub-objetos extras como historico_precos, condicao_especial, etc.
"""


# ─── Helper: extrair JSON de string com texto narrativo ──────────────────────

def _reparar_json_truncado(text: str) -> dict | None:
    """Tenta reparar um JSON truncado (cortado pelo max_tokens do LLM).

    Fecha arrays e objetos abertos progressivamente e tenta parsear.
    Retorna o dict ou None se não for reparável.
    """
    if not text or "{" not in text:
        return None

    # Remove blocos markdown se presentes
    text = re.sub(r"```(?:json)?\s*", "", text).strip()
    text = re.sub(r"```\s*$", "", text).strip()

    # Encontra o início do objeto raiz
    start = text.find("{")
    if start == -1:
        return None
    text = text[start:]

    # Tenta com reparos incrementais (até 10 fechamentos)
    for _ in range(10):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Remove trailing vírgulas, texto parcial após a última vírgula/propriedade completa
        # e fecha estruturas abertas
        stripped = text.rstrip()

        # Remove valor parcial (string cortada, número cortado, etc.)
        # Patterns: "key": "valor_cort   ou   "key": 123   ou   "key": nul
        stripped = re.sub(r',\s*"[^"]*"\s*:\s*"[^"]*$', '', stripped)  # string cortada
        stripped = re.sub(r',\s*"[^"]*"\s*:\s*[\d.]+$', '', stripped)  # número no fim
        stripped = re.sub(r',\s*"[^"]*"\s*:\s*\{[^}]*$', '', stripped)  # objeto cortado
        stripped = re.sub(r',\s*"[^"]*"\s*:\s*$', '', stripped)  # valor ausente
        stripped = re.sub(r',\s*"[^"]*$', '', stripped)  # chave cortada
        stripped = re.sub(r',\s*$', '', stripped)  # vírgula final

        # Conta brackets/braces abertos
        open_braces = stripped.count("{") - stripped.count("}")
        open_brackets = stripped.count("[") - stripped.count("]")

        # Fecha estruturas na ordem correta
        closers = "]" * max(0, open_brackets) + "}" * max(0, open_braces)
        text = stripped + closers

        if not closers:
            break

    try:
        data = json.loads(text)
        if isinstance(data, dict):
            logger.info("JSON truncado reparado com sucesso")
            return data
    except Exception:
        pass

    return None


def _extrair_json_de_string(text: str) -> dict | None:
    """Tenta extrair um objeto JSON de uma string que pode conter texto narrativo.

    Estratégias em ordem de prioridade:
    1. JSON puro (a string inteira é JSON, sem markdown)
    2. Bloco markdown ```json ... ``` — extrai conteúdo entre delimitadores
    3. Primeiro objeto JSON balanceado { } encontrado na string
    4. REPARO: tenta fechar JSON truncado (quando LLM atinge max_tokens)
    """
    if not text or not text.strip():
        return None

    text = text.strip()

    # 1) String inteira é JSON (caso ideal, sem markdown)
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            logger.debug("JSON extraído: string inteira era JSON")
            return data
    except Exception:
        pass

    # 2) Bloco markdown ```json ... ``` — extrai conteúdo entre delimitadores
    block_start_match = re.search(r"```(?:json)?\s*", text)
    if block_start_match:
        content_start = block_start_match.end()
        block_end = text.find("```", content_start)
        block_content = text[content_start: block_end].strip() if block_end != -1 else text[content_start:].strip()
        # Tenta parsear o conteúdo do bloco diretamente
        try:
            data = json.loads(block_content)
            if isinstance(data, dict):
                logger.debug("JSON extraído via bloco markdown (parse direto)")
                return data
        except Exception:
            pass
        # Se o bloco markdown contém JSON truncado, tenta reparar
        repaired = _reparar_json_truncado(block_content)
        if repaired is not None:
            logger.info("JSON extraído via bloco markdown (após reparo de truncamento)")
            return repaired

    # 3) Percorrer a string completa e encontrar o primeiro objeto { } balanceado
    depth = 0
    start = None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                candidate = text[start: i + 1]
                try:
                    data = json.loads(candidate)
                    if isinstance(data, dict):
                        logger.debug(f"JSON extraído via busca balanceada (offset {start}:{i+1})")
                        return data
                except Exception:
                    pass
                start = None

    # 4) Último recurso: reparar JSON truncado na string completa
    repaired = _reparar_json_truncado(text)
    if repaired is not None:
        return repaired

    logger.warning("Não foi possível extrair nenhum JSON válido da string do agente.")
    return None


# ─── Helper: normalizar campos do item para o schema esperado ─────────────────

_FIELD_ALIASES: dict[str, str] = {
    "descricao_oferta": "descricao_original",
    "descricao": "descricao_original",
    "desc_oferta": "descricao_original",
    "descricao_catalogo": "descricao_produto",
    "desc_produto": "descricao_produto",
    "desc_catalogo": "descricao_produto",
    "preco": "preco_oferta",
    "preco_unitario": "preco_oferta",
    "condicao_minima": None,  # campo extra — ignorar
    "condicao_especial": None,  # campo extra — ignorar
    "produto_encontrado": None,  # campo extra — ignorar
    "principio_ativo": None,  # campo extra — ignorar
    "historico_precos": None,  # campo extra — ignorar (sub-objeto aninhado)
}

# Campos que o schema ItemAnaliseAgno aceita
_VALID_FIELDS = {
    "ean", "descricao_original", "descricao_produto", "preco_oferta",
    "menor_historico", "variacao_percentual", "estoque_item", "demanda_mes",
    "sugestao_pedido", "estoque_equivalentes", "classificacao",
    "confianca_match", "recomendacao", "equivalentes",
}


def _normalizar_item(raw: dict) -> dict:
    """Normaliza um dict de item do agente para o schema ItemAnaliseAgno.

    Mapeia aliases de campos e remove campos desconhecidos.
    """
    normalized: dict = {}
    for key, value in raw.items():
        # Aplica alias
        if key in _FIELD_ALIASES:
            target = _FIELD_ALIASES[key]
            if target is None:
                continue  # campo ignorado
            key = target
        # Só inclui campos válidos
        if key in _VALID_FIELDS:
            normalized[key] = value
    return normalized


def _normalizar_output(data: dict) -> dict:
    """Normaliza todo o output do agente, incluindo lista de itens."""
    if "itens" in data and isinstance(data["itens"], list):
        data["itens"] = [_normalizar_item(item) if isinstance(item, dict) else item for item in data["itens"]]
    return data


# ─── Helper: somar token usage (Agno retorna listas quando há multi-step) ────

def _to_int(v: Any) -> int:
    """Converte int, float, None ou list (acumulado pelo Agno) para int."""
    if v is None:
        return 0
    if isinstance(v, list):
        return sum(int(x) for x in v if x is not None)
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


# ─── Criação do agente ────────────────────────────────────────────────────────

def _buscar_parametros_agente() -> dict | None:
    """Busca parâmetros do agente na tabela parametros_agente do Supabase.
    
    Retorna dict com modelo, temperatura, max_tokens, prompt_sistema.
    Retorna None se não encontrar ou se Supabase não estiver disponível.
    """
    try:
        client = get_supabase_client()
        if client is None:
            return None
        result = client.table("parametros_agente").select("*").limit(1).execute()
        if result.data and len(result.data) > 0:
            logger.info("Parâmetros do agente carregados do banco de dados")
            return result.data[0]
    except Exception as e:
        logger.warning(f"Falha ao buscar parametros_agente: {e}")
    return None


def criar_agente_analise(empresa_id: str, model_id: str | None = None, use_tools: bool = True) -> Agent:
    """Cria e retorna uma instância do agente de análise de ofertas.

    Carrega parâmetros (prompt de sistema, max_tokens) da tabela
    `parametros_agente` do Supabase. Se não encontrar, usa os valores
    hardcoded como fallback.

    NOTA: NÃO usamos response_model pois o Agno/Claude frequentemente retorna
    texto narrativo + JSON em bloco markdown, causando falha no parser automático.
    O parsing é feito manualmente por _extrair_json_de_string.
    
    Args:
        empresa_id: ID da empresa para session_state.
        model_id: Override do modelo Claude (opcional).
        use_tools: Se True, inclui tools para consultar Supabase. Se False,
                   cria agente sem tools (modo arquivo).
    """
    settings = get_settings()
    modelo = model_id or settings.anthropic_model or "claude-sonnet-4-5-20250929"

    # Buscar parâmetros do banco de dados
    params_db = _buscar_parametros_agente()
    
    if params_db:
        instructions = params_db.get("prompt_sistema") or SYSTEM_INSTRUCTIONS
        max_tokens_val = params_db.get("max_tokens") or 16384
        temperatura = float(params_db.get("temperatura") or 0.2)
        logger.info(f"Usando prompt do banco ({len(instructions)} chars), max_tokens={max_tokens_val}, temp={temperatura}")
    else:
        instructions = SYSTEM_INSTRUCTIONS
        max_tokens_val = 16384
        temperatura = 0.2
        logger.info("Usando SYSTEM_INSTRUCTIONS hardcoded (banco indisponível)")

    agent = Agent(
        model=Claude(
            id=modelo,
            api_key=settings.anthropic_api_key,
            max_tokens=max_tokens_val,
            temperature=temperatura,
        ),
        tools=AGNO_TOOLS if use_tools else [],
        instructions=instructions,
        # SEM response_model — o Claude retorna texto+JSON que o Agno não consegue
        # parsear automaticamente. Fazemos o parsing manualmente abaixo.
        session_state={"empresa_id": empresa_id},
        markdown=False,
    )
    logger.info(f"Agente criado: modelo={modelo}, tools={'SIM' if use_tools else 'NÃO'}")
    return agent


# ─── Execução principal ───────────────────────────────────────────────────────

async def executar_analise_oferta(
    texto_bruto: str,
    empresa_id: str,
    model_id: str | None = None,
    rows_arquivo: list[dict] | None = None,
    itens_oferta_arquivo: list[dict] | None = None,
) -> tuple[AnaliseOfertaAgnoOutput, dict]:
    """
    Executa a analise de oferta completa de forma 100% DETERMINISTICA.
    
    Tanto para modo Arquivo quanto modo Banco:
      1. Extrai itens da oferta via LLM (com fallback regex) OU usa itens pre-parseados
      2. Constroi indice em memoria (do arquivo ou do banco restrito a empresa)
      3. Cruza dados em Python (match + variacao + classificacao)
    
    Args:
        texto_bruto: Texto bruto da oferta (WhatsApp, colado, etc.)
        empresa_id: ID da empresa do usuário autenticado.
        model_id: Override do modelo Claude (opcional).
        rows_arquivo: Linhas do arquivo de histórico (entradas).
        itens_oferta_arquivo: Itens extraídos diretamente de um arquivo de oferta
                              (XLSX/CSV). Quando presente, pula a extração LLM.
    """
    from app.services.offer_extractor import extrair_itens
    from app.services.analysis_engine import (
        construir_indice_arquivo,
        construir_indice_banco,
        executar_analise_deterministico,
    )
    from app.models.schemas import ItemAnaliseAgno

    start_time = time.time()
    
    # FASE 1: Extrair itens da oferta
    extracao_metrics = {"tokens_utilizados": 0, "custo_reais": 0.0}
    
    if itens_oferta_arquivo:
        # Items already parsed from offer file — skip LLM entirely
        itens_extraidos = itens_oferta_arquivo
        fornecedor_extraido = None
        # Try to detect supplier from file data
        for item in itens_oferta_arquivo[:1]:
            # Some offer files include a 'fornecedor' field
            if "fornecedor" in item:
                fornecedor_extraido = item["fornecedor"]
                break
        logger.info(f"Fase 1 (arquivo oferta): {len(itens_extraidos)} itens pre-parseados")
    else:
        # Standard: LLM/regex extraction from text
        fornecedor_extraido, itens_extraidos, extracao_metrics = await extrair_itens(texto_bruto)
        logger.info(f"Fase 1 (extracao): {len(itens_extraidos)} itens, fornecedor={fornecedor_extraido}")

    if not itens_extraidos:
        raise ValueError(
            "Nao foi possivel extrair itens da oferta. "
            "Verifique se o texto contem produtos com precos."
        )

    # FASE 2: Construir indice de dados
    if rows_arquivo is not None:
        logger.info(f"Modo ARQUIVO DETERMINISTICO: {len(rows_arquivo)} linhas")
        ean_stats, token_index = construir_indice_arquivo(rows_arquivo)
        total_rows = len(rows_arquivo)
    else:
        logger.info(f"Modo BANCO DETERMINISTICO: empresa={empresa_id}")
        ean_stats, token_index = construir_indice_banco(empresa_id)
        total_rows = len(ean_stats)

    # FASE 3: Calculos determinísticos em Python puro
    resultado = executar_analise_deterministico(
        itens_extraidos=itens_extraidos,
        fornecedor=fornecedor_extraido,
        ean_stats=ean_stats,
        token_index=token_index,
        total_registros=total_rows,
    )

    elapsed_ms = int((time.time() - start_time) * 1000)

    # Metricas
    metrics_dict = {
        "tempo_processamento_ms": elapsed_ms,
        "tokens_utilizados": extracao_metrics.get("tokens_utilizados", 0),
        "custo_reais": extracao_metrics.get("custo_reais", 0.0),
    }

    logger.info(f"Analise deterministica concluida em {elapsed_ms}ms")

    # FASE 4: Montar o Output
    itens_agno = []
    for item in resultado["itens"]:
        try:
            itens_agno.append(ItemAnaliseAgno(**item))
        except Exception as e:
            logger.warning(f"Erro ao montar ItemAnaliseAgno: {e} - Dados: {item}")

    return AnaliseOfertaAgnoOutput(
        fornecedor=resultado["fornecedor"],
        itens=itens_agno,
    ), metrics_dict
