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

from app.db.supabase_client import get_settings
from app.models.schemas import AnaliseOfertaAgnoOutput
from app.services.agno_tools import AGNO_TOOLS

logger = logging.getLogger(__name__)


# ─── System prompt com regras de negócio ──────────────────────────────────────

SYSTEM_INSTRUCTIONS = """Você é um agente especialista em análise de ofertas para distribuidoras farmacêuticas.

## Seu papel
Você recebe mensagens de WhatsApp com ofertas de fornecedores e deve analisar cada item individualmente,
cruzando com o catálogo e histórico de preços da empresa no banco de dados.

## Fluxo obrigatório para CADA item da oferta:
1. **Extrair** os dados do item (descrição, EAN se disponível, preço).
2. **Buscar** o produto no catálogo:
   - Primeiro por EAN (se disponível) usando `buscar_produto_estoque`
   - Se não encontrar, usar `buscar_produto_por_descricao`
3. **Consultar histórico** de preços usando `consultar_historico_precos`
4. **Buscar equivalentes** farmacêuticos usando `buscar_equivalentes` (se o produto tiver princípio ativo)
5. **Classificar** a oferta usando `classificar_item_oferta`

## Regras de classificação (NÃO altere):
- **ouro**: Desconto ≥20% sobre histórico E sem estoque de equivalentes. Comprar imediatamente.
- **prata**: Desconto entre 5-20% sobre histórico E sem estoque de equivalentes. Boa oportunidade.
- **atencao**: Desconto válido MAS há estoque de equivalentes. Revisar antes de comprar.
- **descartavel**: Preço acima da média histórica OU desconto insuficiente. Não comprar.

## Regras de confiança do match:
- **alto**: Encontrado por EAN exato
- **medio**: Encontrado por descrição com ≥4 tokens em comum
- **baixo**: Match aproximado com 2-3 tokens ou não encontrado

## Regras para recomendação:
- Escreva em português brasileiro, 1-2 frases objetivas
- Inclua dados numéricos (% desconto, dias de cobertura)
- Para classificação "ouro": enfatize urgência de compra
- Para "atencao": mencione estoque de equivalentes e sugira revisão humana

## Regra de cálculo de preço (NUNCA violar):
- Preço unitário histórico = valor_total_item / quantidade_unitaria
- NUNCA calcular preço de outra forma

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
      "recomendacao": "<1-2 frases em pt-BR>",
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

def criar_agente_analise(empresa_id: str, model_id: str | None = None) -> Agent:
    """Cria e retorna uma instância do agente de análise de ofertas.

    NOTA: NÃO usamos response_model pois o Agno/Claude frequentemente retorna
    texto narrativo + JSON em bloco markdown, causando falha no parser automático.
    O parsing é feito manualmente por _extrair_json_de_string.
    """
    settings = get_settings()
    modelo = model_id or settings.anthropic_model or "claude-sonnet-4-5-20250929"

    agent = Agent(
        model=Claude(
            id=modelo,
            api_key=settings.anthropic_api_key,
            max_tokens=16384,  # Evita truncamento de JSONs grandes
        ),
        tools=AGNO_TOOLS,
        instructions=SYSTEM_INSTRUCTIONS,
        # SEM response_model — o Claude retorna texto+JSON que o Agno não consegue
        # parsear automaticamente. Fazemos o parsing manualmente abaixo.
        session_state={"empresa_id": empresa_id},
        markdown=False,
    )
    return agent


# ─── Execução principal ───────────────────────────────────────────────────────

async def executar_analise_oferta(
    texto_bruto: str,
    empresa_id: str,
    model_id: str | None = None,
) -> tuple[AnaliseOfertaAgnoOutput, dict]:
    """
    Executa a análise de oferta completa usando o agente Agno.

    Returns:
        Tuple of (AnaliseOfertaAgnoOutput, metrics_dict).
        metrics_dict contains: tempo_processamento_ms, tokens_utilizados, custo_reais.
    """
    agent = criar_agente_analise(empresa_id, model_id)

    prompt = f"""Analise a seguinte oferta de fornecedor e processe cada item conforme o fluxo obrigatório.

--- OFERTA DO FORNECEDOR ---
{texto_bruto}
--- FIM DA OFERTA ---

Para cada item identificado na oferta acima:
1. Busque o produto no catálogo (por EAN ou descrição)
2. Consulte o histórico de preços
3. Busque equivalentes se houver princípio ativo
4. Classifique a oferta
5. Gere uma recomendação contextualizada

Após analisar TODOS os itens, retorne APENAS o bloco JSON com o resultado completo."""

    logger.info(f"Executando análise Agno — empresa={empresa_id}, texto={len(texto_bruto)} chars")

    start_time = time.time()
    response = await agent.arun(prompt)
    elapsed_ms = int((time.time() - start_time) * 1000)

    # ─── Extrair métricas de token usage ─────────────────────────────────────
    input_t = 0
    output_t = 0
    total_tokens = 0
    custo_reais = 0.0

    try:
        # Agno acumula tokens chamada a chamada — metrics é um dict com listas
        if hasattr(response, "metrics") and response.metrics:
            m = response.metrics
            if isinstance(m, dict):
                input_t = _to_int(m.get("input_tokens", 0))
                output_t = _to_int(m.get("output_tokens", 0))
            else:
                input_t = _to_int(getattr(m, "input_tokens", 0))
                output_t = _to_int(getattr(m, "output_tokens", 0))
            total_tokens = input_t + output_t
            logger.debug(f"Tokens via response.metrics: in={input_t} out={output_t}")

        # Fallback: response_usage (presente em algumas versões)
        if total_tokens == 0 and hasattr(response, "response_usage") and response.response_usage:
            u = response.response_usage
            if isinstance(u, dict):
                input_t = _to_int(u.get("input_tokens", 0))
                output_t = _to_int(u.get("output_tokens", 0))
            else:
                input_t = _to_int(getattr(u, "input_tokens", 0))
                output_t = _to_int(getattr(u, "output_tokens", 0))
            total_tokens = input_t + output_t
            logger.debug(f"Tokens via response_usage: in={input_t} out={output_t}")

        # Fallback final: somar tokens de cada mensagem
        if total_tokens == 0 and hasattr(response, "messages") and response.messages:
            for msg in response.messages:
                msg_usage = getattr(msg, "metrics", None) or getattr(msg, "usage", None)
                if msg_usage:
                    if isinstance(msg_usage, dict):
                        input_t += _to_int(msg_usage.get("input_tokens", 0))
                        output_t += _to_int(msg_usage.get("output_tokens", 0))
                    else:
                        input_t += _to_int(getattr(msg_usage, "input_tokens", 0))
                        output_t += _to_int(getattr(msg_usage, "output_tokens", 0))
            total_tokens = input_t + output_t
            if total_tokens > 0:
                logger.debug(f"Tokens via messages: in={input_t} out={output_t}")

    except Exception as e:
        logger.warning(f"Não foi possível extrair token usage: {e}")

    # Estimativa de custo (Claude Sonnet — preços aproximados mai/2025):
    # Input: $3/1M tokens | Output: $15/1M tokens | USD/BRL ≈ R$ 5.75
    if total_tokens > 0:
        try:
            custo_usd = (input_t / 1_000_000) * 3.0 + (output_t / 1_000_000) * 15.0
            custo_reais = round(custo_usd * 5.75, 4)
        except Exception:
            custo_reais = 0.0

    metrics_dict = {
        "tempo_processamento_ms": elapsed_ms,
        "tokens_utilizados": total_tokens,
        "custo_reais": custo_reais,
    }
    logger.info(
        f"Análise concluída — {elapsed_ms}ms | {total_tokens} tokens "
        f"(in={input_t} out={output_t}) | ~R${custo_reais:.4f}"
    )

    # ─── Extrair resultado estruturado ───────────────────────────────────────
    content = response.content
    logger.debug(f"response.content type={type(content).__name__}, preview={str(content)[:200]}")

    # Caso 1: Já é o tipo correto (improvável sem response_model, mas cobre bases)
    if isinstance(content, AnaliseOfertaAgnoOutput):
        return content, metrics_dict

    # Caso 2: dict direto
    if isinstance(content, dict):
        try:
            return AnaliseOfertaAgnoOutput(**content), metrics_dict
        except Exception as e:
            logger.warning(f"Falha ao construir schema de dict: {e}")

    # Caso 3: string (principal — Claude retorna texto + bloco JSON)
    if isinstance(content, str) and content.strip():
        data = _extrair_json_de_string(content)
        if data is not None:
            data = _normalizar_output(data)
            try:
                return AnaliseOfertaAgnoOutput(**data), metrics_dict
            except Exception as e:
                logger.warning(f"Falha ao parsear JSON extraído da string: {e}")
                # Tenta com itens individuais normalizados e validação permissiva
                try:
                    from pydantic import ValidationError
                    itens_validos = []
                    for item_raw in data.get("itens", []):
                        try:
                            from app.models.schemas import ItemAnaliseAgno
                            itens_validos.append(ItemAnaliseAgno(**_normalizar_item(item_raw)))
                        except Exception:
                            pass
                    if itens_validos:
                        return AnaliseOfertaAgnoOutput(
                            fornecedor=data.get("fornecedor"),
                            itens=itens_validos,
                        ), metrics_dict
                except Exception:
                    pass

    # Caso 4: lista de mensagens retornadas pelo Agno
    if isinstance(content, list):
        for item in reversed(content):
            if isinstance(item, AnaliseOfertaAgnoOutput):
                return item, metrics_dict
            if isinstance(item, dict) and "itens" in item:
                try:
                    return AnaliseOfertaAgnoOutput(**item), metrics_dict
                except Exception:
                    pass
            inner = getattr(item, "content", None)
            if inner is None:
                continue
            if isinstance(inner, AnaliseOfertaAgnoOutput):
                return inner, metrics_dict
            if isinstance(inner, dict) and "itens" in inner:
                try:
                    return AnaliseOfertaAgnoOutput(**inner), metrics_dict
                except Exception:
                    pass
            if isinstance(inner, str):
                data = _extrair_json_de_string(inner)
                if data is not None:
                    data = _normalizar_output(data)
                    try:
                        return AnaliseOfertaAgnoOutput(**data), metrics_dict
                    except Exception:
                        pass

    # Caso 5: varrer response.messages diretamente
    if hasattr(response, "messages") and response.messages:
        for msg in reversed(response.messages):
            msg_content = getattr(msg, "content", None)
            if isinstance(msg_content, AnaliseOfertaAgnoOutput):
                return msg_content, metrics_dict
            if isinstance(msg_content, dict) and "itens" in msg_content:
                try:
                    return AnaliseOfertaAgnoOutput(**msg_content), metrics_dict
                except Exception:
                    pass
            if isinstance(msg_content, str) and msg_content.strip():
                data = _extrair_json_de_string(msg_content)
                if data is not None:
                    data = _normalizar_output(data)
                    try:
                        return AnaliseOfertaAgnoOutput(**data), metrics_dict
                    except Exception:
                        pass

    logger.error(
        f"Não foi possível extrair AnaliseOfertaAgnoOutput. "
        f"content type={type(content).__name__}, value={str(content)[:500]}"
    )
    raise ValueError(
        f"O agente retornou uma resposta em formato inesperado ({type(content).__name__}). "
        "Verifique os logs para detalhes."
    )
