"""
Router de Ofertas — Endpoints para análise de ofertas (síncrono + assíncrono).

Fluxo assíncrono (recomendado para análises longas):
  POST /analisar-async → retorna analise_id imediatamente
  GET  /status/{analise_id} → frontend faz polling até status=concluida

Fluxo síncrono legado:
  POST /analisar → aguarda resultado (pode dar timeout para ofertas grandes)

SEGURANÇA: empresa_id é extraído EXCLUSIVAMENTE do JWT via Depends(get_current_empresa_id).
Nunca aceita empresa_id do body/payload da requisição.
"""
from __future__ import annotations


import logging
from collections import Counter
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile

from app.db.supabase_client import get_settings, get_supabase_client
from app.middleware import get_current_empresa_id, get_current_user_id
from app.models.schemas import (
    AnaliseCreate,
    AnaliseItemCreate,
    ItemOfertaResponse,
    OfertaAnalyzeRequest,
    OfertaAnalyzeResponse,
    ResumoAnalise,
)
from app.services.agno_agent import executar_analise_oferta
from app.services.file_parser import format_file_data_for_prompt, parse_uploaded_file
from app.services.persistencia_service import salvar_analise, salvar_itens_analise

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── Helper: executar análise e persistir resultado ───────────────────────────

def _build_itens_response(resultado_agno) -> list[ItemOfertaResponse]:
    itens_response: list[ItemOfertaResponse] = []
    for item in resultado_agno.itens:
        itens_response.append(
            ItemOfertaResponse(
                ean=item.ean,
                descricao_original=item.descricao_original,
                descricao_produto=item.descricao_produto,
                preco_oferta=item.preco_oferta,
                menor_historico=item.menor_historico,
                origem_menor_historico=None,
                variacao_percentual=item.variacao_percentual,
                estoque_item=item.estoque_item,
                demanda_mes=item.demanda_mes,
                sugestao_pedido=item.sugestao_pedido,
                estoque_equivalentes=item.estoque_equivalentes,
                classificacao=item.classificacao,
                confianca_match=item.confianca_match,
                recomendacao=item.recomendacao,
                equivalente_detalhes=[eq for eq in item.equivalentes] if item.equivalentes else [],
                historico_menores=[],
                historico_maiores=[],
            )
        )
    return itens_response


async def _executar_e_persistir(
    analise_id: str,
    empresa_id: str,
    usuario_id: str | None,
    texto_bruto: str,
    fornecedor_informado: str | None,
    is_async: bool = False,
    dados_arquivo: str | None = None,
    rows_arquivo: list | None = None,
) -> OfertaAnalyzeResponse:
    """Executa a analise e persiste no Supabase. Retorna o response completo."""
    resultado_agno, metrics = await executar_analise_oferta(
        texto_bruto=texto_bruto,
        empresa_id=empresa_id,
        dados_arquivo=dados_arquivo,
        rows_arquivo=rows_arquivo,
    )

    itens_response = _build_itens_response(resultado_agno)

    contador = Counter(item.classificacao for item in itens_response)
    resumo = ResumoAnalise(
        itens_analisados=len(itens_response),
        oportunidades=contador.get("ouro", 0) + contador.get("prata", 0),
        sem_necessidade=contador.get("descartavel", 0),
        revisar=contador.get("atencao", 0),
    )

    fornecedor_final = fornecedor_informado or resultado_agno.fornecedor

    response_obj = OfertaAnalyzeResponse(
        analise_id=analise_id,
        fornecedor=fornecedor_final,
        origem="texto",
        resumo=resumo,
        itens=itens_response,
        tempo_processamento_ms=metrics.get("tempo_processamento_ms"),
        tokens_utilizados=metrics.get("tokens_utilizados"),
        custo_reais=metrics.get("custo_reais"),
    )

    # Persistir no Supabase
    client = get_supabase_client()
    if client:
        try:
            if not is_async:
                # Fluxo síncrono: inserir registro completo
                salvar_analise(
                    client,
                    AnaliseCreate(
                        empresa_id=empresa_id,
                        usuario_id=usuario_id,
                        fornecedor=fornecedor_final,
                        origem="texto",
                        entrada_bruta=texto_bruto,
                        status="concluida",
                        tempo_processamento_ms=metrics.get("tempo_processamento_ms"),
                        tokens_utilizados=metrics.get("tokens_utilizados"),
                        custo_reais=metrics.get("custo_reais"),
                    ),
                )

            itens_persistencia = [
                AnaliseItemCreate(
                    analise_id=analise_id,
                    ean=item.ean,
                    produto_id=None,
                    descricao_bruta=item.descricao_original,
                    preco_oferta=item.preco_oferta,
                    menor_preco_historico=item.menor_historico,
                    origem_menor_historico=None,
                    desconto_percentual=item.variacao_percentual,
                    estoque_item=item.estoque_item,
                    demanda_mes=item.demanda_mes,
                    sugestao_pedido=item.sugestao_pedido,
                    estoque_equivalentes=item.estoque_equivalentes,
                    classificacao=item.classificacao,
                    confianca_match=item.confianca_match,
                    recomendacao=item.recomendacao,
                    dados_json=item.model_dump(),
                )
                for item in resultado_agno.itens
            ]
            salvar_itens_analise(client, itens_persistencia)
            logger.info(f"Análise {analise_id} persistida com {len(itens_persistencia)} itens.")
        except Exception as e:
            logger.warning(f"Falha ao persistir análise (não-bloqueante): {e}")

    return response_obj


# ─── Background task: executa análise e atualiza status no Supabase ──────────

async def _background_analise(
    analise_id: str,
    empresa_id: str,
    usuario_id: str | None,
    texto_bruto: str,
    fornecedor_informado: str | None,
    dados_arquivo: str | None = None,
    rows_arquivo: list | None = None,
):
    """Task executada em background. Atualiza o status no Supabase ao terminar."""
    client = get_supabase_client()
    try:
        logger.info(f"[BG] Iniciando analise {analise_id}")
        response_obj = await _executar_e_persistir(
            analise_id=analise_id,
            empresa_id=empresa_id,
            usuario_id=usuario_id,
            texto_bruto=texto_bruto,
            fornecedor_informado=fornecedor_informado,
            is_async=True,
            dados_arquivo=dados_arquivo,
            rows_arquivo=rows_arquivo,
        )

        # Atualizar o registro com o resultado completo e status=concluida
        if client:
            client.table("analises_oferta").update({
                "status": "concluida",
                "fornecedor": response_obj.fornecedor,
                "tempo_processamento_ms": response_obj.tempo_processamento_ms,
                "tokens_utilizados": response_obj.tokens_utilizados,
                "custo_reais": float(response_obj.custo_reais) if response_obj.custo_reais else None,
                "resultado_json": response_obj.model_dump(),
            }).eq("id", analise_id).execute()

        logger.info(f"[BG] Análise {analise_id} concluída com sucesso")

    except Exception as e:
        logger.exception(f"[BG] Erro na análise {analise_id}: {e}")
        if client:
            try:
                client.table("analises_oferta").update({
                    "status": "erro",
                    "resultado_json": {"erro": str(e)},
                }).eq("id", analise_id).execute()
            except Exception:
                pass


# ─── Endpoint 1: Iniciar análise async (retorna imediatamente) ───────────────

@router.post("/analisar-async")
async def analisar_oferta_async(
    payload: OfertaAnalyzeRequest,
    background_tasks: BackgroundTasks,
    empresa_id: str = Depends(get_current_empresa_id),
):
    """
    Inicia a análise em background e retorna analise_id imediatamente.
    O frontend deve fazer polling em GET /status/{analise_id}.

    SEGURANÇA: empresa_id extraído do JWT via dependency injection.
    """
    settings = get_settings()

    if not settings.anthropic_api_key:
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY não configurada.",
        )

    if not payload.texto_bruto or not payload.texto_bruto.strip():
        raise HTTPException(
            status_code=400,
            detail="texto_bruto é obrigatório.",
        )

    analise_id = str(uuid4())

    # Criar registro "processando" no banco imediatamente
    client = get_supabase_client()
    if client:
        try:
            client.table("analises_oferta").insert({
                "id": analise_id,
                "empresa_id": empresa_id,  # do JWT, não do payload
                "usuario_id": payload.usuario_id,
                "fornecedor": payload.fornecedor_informado,
                "origem": "texto",
                "entrada_bruta": payload.texto_bruto,
                "status": "processando",
            }).execute()
        except Exception as e:
            logger.warning(f"Falha ao criar registro inicial: {e}")

    # Iniciar análise em background
    background_tasks.add_task(
        _background_analise,
        analise_id=analise_id,
        empresa_id=empresa_id,  # do JWT, não do payload
        usuario_id=payload.usuario_id,
        texto_bruto=payload.texto_bruto,
        fornecedor_informado=payload.fornecedor_informado,
    )

    return {
        "analise_id": analise_id,
        "status": "processando",
        "mensagem": "Análise iniciada. Faça polling em /api/ofertas/status/{analise_id}",
    }


# ─── Endpoint 1b: Iniciar análise async com arquivo (multipart) ──────────────

@router.post("/analisar-async-file")
async def analisar_oferta_async_file(
    background_tasks: BackgroundTasks,
    empresa_id: str = Depends(get_current_empresa_id),
    texto_bruto: str = Form(...),
    fonte_dados: str = Form("banco"),
    fornecedor_informado: str = Form(None),
    usuario_id: str = Form(None),
    arquivo: UploadFile | None = File(None),
):
    """
    Inicia a análise em background com suporte a upload de arquivo.
    Aceita multipart/form-data.

    Quando fonte_dados="arquivo", o arquivo enviado é parseado e seus dados
    são injetados diretamente no prompt do agente IA como referência histórica.

    SEGURANÇA: empresa_id extraído do JWT via dependency injection.
    """
    settings = get_settings()

    if not settings.anthropic_api_key:
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY não configurada.",
        )

    if not texto_bruto or not texto_bruto.strip():
        raise HTTPException(
            status_code=400,
            detail="texto_bruto é obrigatório.",
        )

    # Parsear arquivo se fonte_dados=arquivo
    rows_arquivo: list | None = None
    dados_arquivo_str: str | None = None
    if fonte_dados == "arquivo":
        if not arquivo:
            raise HTTPException(
                status_code=400,
                detail="Arquivo obrigatorio quando fonte_dados='arquivo'.",
            )
        try:
            file_bytes = await arquivo.read()
            filename = arquivo.filename or "upload.xlsx"
            rows_arquivo = parse_uploaded_file(file_bytes, filename)
            if not rows_arquivo:
                raise HTTPException(
                    status_code=400,
                    detail="Nenhum dado encontrado no arquivo enviado.",
                )
            logger.info(f"Arquivo {filename} parseado: {len(rows_arquivo)} registros para analise deterministica")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.exception(f"Erro ao parsear arquivo: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Erro ao processar arquivo: {str(e)}",
            )

    analise_id = str(uuid4())

    # Criar registro "processando" no banco imediatamente
    client = get_supabase_client()
    if client:
        try:
            client.table("analises_oferta").insert({
                "id": analise_id,
                "empresa_id": empresa_id,
                "usuario_id": usuario_id,
                "fornecedor": fornecedor_informado,
                "origem": "arquivo" if fonte_dados == "arquivo" else "texto",
                "entrada_bruta": texto_bruto,
                "status": "processando",
            }).execute()
        except Exception as e:
            logger.warning(f"Falha ao criar registro inicial: {e}")

    # Iniciar análise em background
    background_tasks.add_task(
        _background_analise,
        analise_id=analise_id,
        empresa_id=empresa_id,
        usuario_id=usuario_id,
        texto_bruto=texto_bruto,
        fornecedor_informado=fornecedor_informado,
        dados_arquivo=dados_arquivo_str,
        rows_arquivo=rows_arquivo,
    )

    return {
        "analise_id": analise_id,
        "status": "processando",
        "fonte_dados": fonte_dados,
        "mensagem": "Análise iniciada. Faça polling em /api/ofertas/status/{analise_id}",
    }

# ─── Endpoint 2: Polling de status (autenticado) ─────────────────────────────

@router.get("/status/{analise_id}")
async def status_analise(
    analise_id: str,
    empresa_id: str = Depends(get_current_empresa_id),
):
    """
    Retorna o status atual de uma análise.
    - status=processando → análise ainda em andamento
    - status=concluida   → resultado disponível em resultado_json
    - status=erro        → falha, mensagem em resultado_json.erro

    SEGURANÇA: verifica que a análise pertence à empresa do usuário autenticado.
    """
    client = get_supabase_client()
    if not client:
        raise HTTPException(status_code=503, detail="Banco de dados indisponível.")

    try:
        response = (
            client.table("analises_oferta")
            .select("id, status, resultado_json, created_at, empresa_id")
            .eq("id", analise_id)
            .limit(1)
            .execute()
        )
        data = response.data or []
        if not data:
            raise HTTPException(status_code=404, detail="Análise não encontrada.")

        row = data[0]

        # Verificar que a análise pertence à empresa do usuário
        if row.get("empresa_id") != empresa_id:
            raise HTTPException(status_code=403, detail="Acesso negado a esta análise.")

        return {
            "analise_id": analise_id,
            "status": row.get("status"),
            "resultado": row.get("resultado_json"),
            "created_at": row.get("created_at"),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Erro ao buscar status da análise {analise_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ─── Endpoint legado síncrono (mantido para compatibilidade / test_api.py) ───

@router.post("/analisar", response_model=OfertaAnalyzeResponse)
async def analisar_oferta(
    payload: OfertaAnalyzeRequest,
    empresa_id: str = Depends(get_current_empresa_id),
) -> OfertaAnalyzeResponse:
    """
    Analisa uma oferta de forma síncrona. Pode dar timeout para ofertas longas.
    Prefira /analisar-async + polling para uso em produção.

    SEGURANÇA: empresa_id extraído do JWT via dependency injection.
    """
    settings = get_settings()

    if not settings.anthropic_api_key:
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY não configurada. Configure a variável de ambiente.",
        )

    try:
        analise_id = str(uuid4())
        return await _executar_e_persistir(
            analise_id=analise_id,
            empresa_id=empresa_id,  # do JWT, não do payload
            usuario_id=payload.usuario_id,
            texto_bruto=payload.texto_bruto,
            fornecedor_informado=payload.fornecedor_informado,
        )

    except Exception as e:
        logger.exception(f"Erro na análise de oferta: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar análise: {str(e)}",
        )
