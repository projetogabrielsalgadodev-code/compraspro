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

import logging
import time

from app.models.schemas import AnaliseOfertaAgnoOutput

logger = logging.getLogger(__name__)


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
