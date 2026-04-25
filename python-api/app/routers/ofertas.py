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
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.db.supabase_client import get_settings, get_supabase_client
from app.middleware import get_current_empresa_id, get_current_user_id
from app.models.schemas import (
    AnaliseCreate,
    AnaliseItemCreate,
    EquivalenteResumo,
    ItemOfertaResponse,
    OfertaAnalyzeRequest,
    OfertaAnalyzeResponse,
    ResumoAnalise,
)
from app.services.agno_agent import executar_analise_oferta
from app.services.file_parser import format_file_data_for_prompt, parse_uploaded_file, parse_offer_file
from app.services.persistencia_service import salvar_analise, salvar_itens_analise

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── Helper: executar análise e persistir resultado ───────────────────────────

def _build_itens_response(resultado_agno) -> list[ItemOfertaResponse]:
    itens_response: list[ItemOfertaResponse] = []
    for item in resultado_agno.itens:
        # Convert equivalentes — may be EquivalenteResumo objects or raw dicts
        equiv_list = []
        if item.equivalentes:
            for eq in item.equivalentes:
                if isinstance(eq, EquivalenteResumo):
                    equiv_list.append(eq)
                elif isinstance(eq, dict):
                    equiv_list.append(EquivalenteResumo(**eq))
                else:
                    equiv_list.append(eq)

        itens_response.append(
            ItemOfertaResponse(
                ean=item.ean,
                descricao_original=item.descricao_original,
                descricao_produto=item.descricao_produto,
                preco_oferta=item.preco_oferta if item.preco_oferta is not None else 0.0,
                menor_historico=item.menor_historico if item.menor_historico is not None else 0.0,
                origem_menor_historico=getattr(item, "origem_menor_historico", None),
                variacao_percentual=item.variacao_percentual if item.variacao_percentual is not None else 0.0,
                estoque_item=item.estoque_item if item.estoque_item is not None else 0,
                demanda_mes=item.demanda_mes if item.demanda_mes is not None else 0.0,
                sugestao_pedido=item.sugestao_pedido if item.sugestao_pedido is not None else 0,
                estoque_equivalentes=item.estoque_equivalentes if item.estoque_equivalentes is not None else 0,
                classificacao=item.classificacao,
                confianca_match=item.confianca_match,
                recomendacao=item.recomendacao,
                equivalente_detalhes=equiv_list,
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
    rows_arquivo: list | None = None,
    itens_oferta_arquivo: list | None = None,
) -> OfertaAnalyzeResponse:
    """Executa a analise e persiste no Supabase. Retorna o response completo."""
    resultado_agno, metrics = await executar_analise_oferta(
        texto_bruto=texto_bruto,
        empresa_id=empresa_id,
        rows_arquivo=rows_arquivo,
        itens_oferta_arquivo=itens_oferta_arquivo,
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
                        created_at=datetime.now(ZoneInfo("UTC")).isoformat(),
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
                    origem_menor_historico=getattr(item, "origem_menor_historico", None),
                    desconto_percentual=item.variacao_percentual,
                    estoque_item=item.estoque_item,
                    demanda_mes=item.demanda_mes,
                    sugestao_pedido=item.sugestao_pedido,
                    estoque_equivalentes=item.estoque_equivalentes,
                    classificacao=item.classificacao,
                    confianca_match=item.confianca_match,
                    recomendacao=item.recomendacao,
                    dados_json=item.model_dump(),
                    created_at=datetime.now(ZoneInfo("UTC")).isoformat(),
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
    rows_arquivo: list | None = None,
    itens_oferta_arquivo: list | None = None,
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
            rows_arquivo=rows_arquivo,
            itens_oferta_arquivo=itens_oferta_arquivo,
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
                "fonte_dados": "banco",
                "status": "processando",
                "created_at": datetime.now(ZoneInfo("UTC")).isoformat(),
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
    texto_bruto: str = Form(""),
    fonte_dados: str = Form("banco"),
    fornecedor_informado: str = Form(None),
    usuario_id: str = Form(None),
    arquivo: UploadFile | None = File(None),
    arquivo_oferta: UploadFile | None = File(None),
):
    """
    Inicia a análise em background com suporte a upload de arquivo.
    Aceita multipart/form-data.

    Fluxos suportados:
    - texto_bruto + fonte_dados="banco": oferta em texto, comparar com BD
    - texto_bruto + fonte_dados="arquivo" + arquivo: oferta em texto, comparar com arquivo
    - arquivo_oferta + fonte_dados="banco": oferta em arquivo, comparar com BD
    - arquivo_oferta + fonte_dados="arquivo" + arquivo: oferta em arquivo, comparar com arquivo

    SEGURANÇA: empresa_id extraído do JWT via dependency injection.
    """
    settings = get_settings()

    if not settings.anthropic_api_key:
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY não configurada.",
        )

    # Validate: need at least texto_bruto OR arquivo_oferta
    has_text = texto_bruto and texto_bruto.strip()
    has_offer_file = arquivo_oferta is not None

    if not has_text and not has_offer_file:
        raise HTTPException(
            status_code=400,
            detail="Envie texto_bruto ou arquivo_oferta para análise.",
        )

    # Parsear arquivo de HISTÓRICO se fonte_dados=arquivo
    rows_arquivo: list | None = None
    file_bytes = None
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
            logger.info(f"Arquivo histórico {filename} parseado: {len(rows_arquivo)} registros")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.exception(f"Erro ao parsear arquivo de histórico: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Erro ao processar arquivo de histórico: {str(e)}",
            )

    # Parsear arquivo de OFERTA se fornecido
    itens_oferta_arquivo: list | None = None
    fornecedor_do_arquivo: str | None = None
    if has_offer_file:
        try:
            offer_bytes = await arquivo_oferta.read()
            offer_filename = arquivo_oferta.filename or "oferta.xlsx"
            itens_oferta_arquivo, fornecedor_do_arquivo = parse_offer_file(offer_bytes, offer_filename)
            if not itens_oferta_arquivo:
                raise HTTPException(
                    status_code=400,
                    detail="Nenhum item encontrado no arquivo de oferta.",
                )
            # Use detected supplier as fallback if user didn't provide one
            if fornecedor_do_arquivo and not fornecedor_informado:
                fornecedor_informado = fornecedor_do_arquivo
                logger.info(f"Fornecedor auto-detectado do arquivo: {fornecedor_do_arquivo}")
            # Use a placeholder texto_bruto for persistence if text is empty
            if not has_text:
                texto_bruto = f"[Oferta via arquivo: {offer_filename}]"
            logger.info(f"Arquivo oferta {offer_filename} parseado: {len(itens_oferta_arquivo)} itens")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Erro ao parsear arquivo de oferta: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Erro ao processar arquivo de oferta: {str(e)}",
            )

    analise_id = str(uuid4())

    # Criar registro "processando" no banco imediatamente
    client = get_supabase_client()
    if client:
        try:
            # Metadados do arquivo para a página de inputs
            nome_arq_hist = arquivo.filename if arquivo else None
            tamanho_arq = len(file_bytes) if file_bytes else None
            nome_arq_oferta = arquivo_oferta.filename if arquivo_oferta else None

            client.table("analises_oferta").insert({
                "id": analise_id,
                "empresa_id": empresa_id,
                "usuario_id": usuario_id,
                "fornecedor": fornecedor_informado,
                "origem": "arquivo" if has_offer_file else ("arquivo" if fonte_dados == "arquivo" else "texto"),
                "entrada_bruta": texto_bruto,
                "fonte_dados": fonte_dados,
                "nome_arquivo_historico": nome_arq_hist,
                "tamanho_arquivo_historico": tamanho_arq,
                "status": "processando",
                "created_at": datetime.now(ZoneInfo("UTC")).isoformat(),
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
        rows_arquivo=rows_arquivo,
        itens_oferta_arquivo=itens_oferta_arquivo,
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


# ─── Endpoint 4: Análise via Supabase Storage (elimina limites de upload) ─────

class StorageAnalyzeRequest(BaseModel):
    """Request para análise via Storage. Arquivos já estão no Supabase Storage."""
    texto_bruto: str = ""
    fonte_dados: str = "banco"
    fornecedor_informado: str | None = None
    usuario_id: str | None = None
    storage_path_oferta: str | None = None
    storage_path_historico: str | None = None
    nome_arquivo_oferta: str | None = None
    nome_arquivo_historico: str | None = None



def _download_from_storage(client, storage_path: str) -> bytes:
    """Baixa um arquivo do Supabase Storage usando service_role."""
    try:
        data = client.storage.from_("uploads-temp").download(storage_path)
        return data
    except Exception as e:
        logger.error(f"Erro ao baixar do Storage ({storage_path}): {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao baixar arquivo do Storage: {str(e)}",
        )


def _cleanup_storage(client, paths: list[str]):
    """Remove arquivos temporários do Storage após o processamento."""
    try:
        if paths:
            client.storage.from_("uploads-temp").remove(paths)
            logger.info(f"Arquivos temporários removidos do Storage: {paths}")
    except Exception as e:
        logger.warning(f"Falha ao limpar arquivos do Storage (não-bloqueante): {e}")


async def _background_analise_storage(
    analise_id: str,
    empresa_id: str,
    usuario_id: str | None,
    texto_bruto: str,
    fornecedor_informado: str | None,
    storage_path_oferta: str | None,
    storage_path_historico: str | None,
    nome_arquivo_oferta: str | None,
    nome_arquivo_historico: str | None,
    fonte_dados: str,
):
    """Background task que baixa arquivos do Storage, processa, e limpa."""
    client = get_supabase_client()
    cleanup_paths: list[str] = []

    try:
        logger.info(f"[BG-Storage] Iniciando analise {analise_id}")

        # Baixar e parsear arquivo de OFERTA do Storage
        itens_oferta_arquivo: list | None = None
        if storage_path_oferta and client:
            offer_bytes = _download_from_storage(client, storage_path_oferta)
            cleanup_paths.append(storage_path_oferta)
            filename = nome_arquivo_oferta or "oferta.xlsx"
            itens_oferta_arquivo, fornecedor_do_arquivo = parse_offer_file(offer_bytes, filename)
            if fornecedor_do_arquivo and not fornecedor_informado:
                fornecedor_informado = fornecedor_do_arquivo
                logger.info(f"Fornecedor auto-detectado: {fornecedor_do_arquivo}")
            if not texto_bruto.strip():
                texto_bruto = f"[Oferta via arquivo: {filename}]"
            logger.info(f"Arquivo oferta do Storage parseado: {len(itens_oferta_arquivo or [])} itens")

        # Baixar e parsear arquivo de HISTÓRICO do Storage
        rows_arquivo: list | None = None
        if storage_path_historico and client and fonte_dados == "arquivo":
            hist_bytes = _download_from_storage(client, storage_path_historico)
            cleanup_paths.append(storage_path_historico)
            hist_filename = nome_arquivo_historico or "historico.xlsx"
            rows_arquivo = parse_uploaded_file(hist_bytes, hist_filename)
            logger.info(f"Arquivo histórico do Storage parseado: {len(rows_arquivo or [])} registros")

        # Executar análise
        response_obj = await _executar_e_persistir(
            analise_id=analise_id,
            empresa_id=empresa_id,
            usuario_id=usuario_id,
            texto_bruto=texto_bruto,
            fornecedor_informado=fornecedor_informado,
            is_async=True,
            rows_arquivo=rows_arquivo,
            itens_oferta_arquivo=itens_oferta_arquivo,
        )

        # Atualizar registro com resultado
        if client:
            client.table("analises_oferta").update({
                "status": "concluida",
                "fornecedor": response_obj.fornecedor,
                "tempo_processamento_ms": response_obj.tempo_processamento_ms,
                "tokens_utilizados": response_obj.tokens_utilizados,
                "custo_reais": float(response_obj.custo_reais) if response_obj.custo_reais else None,
                "resultado_json": response_obj.model_dump(),
            }).eq("id", analise_id).execute()

        logger.info(f"[BG-Storage] Análise {analise_id} concluída com sucesso")

    except Exception as e:
        logger.exception(f"[BG-Storage] Erro na análise {analise_id}: {e}")
        if client:
            try:
                client.table("analises_oferta").update({
                    "status": "erro",
                    "resultado_json": {"erro": str(e)},
                }).eq("id", analise_id).execute()
            except Exception:
                pass

    finally:
        # Limpar arquivos temporários do Storage
        if client and cleanup_paths:
            _cleanup_storage(client, cleanup_paths)


@router.post("/analisar-via-storage")
async def analisar_oferta_via_storage(
    payload: StorageAnalyzeRequest,
    background_tasks: BackgroundTasks,
    empresa_id: str = Depends(get_current_empresa_id),
):
    """
    Inicia a análise em background usando arquivos já upados no Supabase Storage.

    Fluxo:
    1. Frontend faz upload dos arquivos direto pro Supabase Storage (bucket uploads-temp)
    2. Frontend chama essa rota com os paths do Storage
    3. Render baixa os arquivos do Storage em background
    4. Após processamento, arquivos temporários são removidos

    Isso elimina:
    - Limite de body size da Vercel (4.5 MB / 10s)
    - Timeout do Render cold start
    - Transferência de arquivos grandes via HTTP duplo (browser→Vercel→Render)

    SEGURANÇA: empresa_id extraído via dependency injection.
    """
    settings = get_settings()

    if not settings.anthropic_api_key:
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY não configurada.",
        )

    # Validar: precisa de texto OU arquivo de oferta
    has_text = payload.texto_bruto and payload.texto_bruto.strip()
    has_offer_file = bool(payload.storage_path_oferta)

    if not has_text and not has_offer_file:
        raise HTTPException(
            status_code=400,
            detail="Envie texto_bruto ou storage_path_oferta para análise.",
        )

    # Validar que storage paths existem se informados
    client = get_supabase_client()
    if not client:
        raise HTTPException(status_code=503, detail="Banco de dados indisponível.")

    analise_id = str(uuid4())
    texto_para_persistir = payload.texto_bruto or f"[Oferta via arquivo: {payload.nome_arquivo_oferta or 'upload'}]"

    # Criar registro "processando" no banco imediatamente
    try:
        client.table("analises_oferta").insert({
            "id": analise_id,
            "empresa_id": empresa_id,
            "usuario_id": payload.usuario_id,
            "fornecedor": payload.fornecedor_informado,
            "origem": "arquivo" if has_offer_file else ("arquivo" if payload.fonte_dados == "arquivo" else "texto"),
            "entrada_bruta": texto_para_persistir,
            "fonte_dados": payload.fonte_dados,
            "nome_arquivo_historico": payload.nome_arquivo_historico,
            "status": "processando",
            "created_at": datetime.now(ZoneInfo("UTC")).isoformat(),
        }).execute()
    except Exception as e:
        logger.warning(f"Falha ao criar registro inicial: {e}")

    # Iniciar análise em background — Render baixa os arquivos do Storage
    background_tasks.add_task(
        _background_analise_storage,
        analise_id=analise_id,
        empresa_id=empresa_id,
        usuario_id=payload.usuario_id,
        texto_bruto=payload.texto_bruto or "",
        fornecedor_informado=payload.fornecedor_informado,
        storage_path_oferta=payload.storage_path_oferta,
        storage_path_historico=payload.storage_path_historico,
        nome_arquivo_oferta=payload.nome_arquivo_oferta,
        nome_arquivo_historico=payload.nome_arquivo_historico,
        fonte_dados=payload.fonte_dados,
    )

    return {
        "analise_id": analise_id,
        "status": "processando",
        "fonte_dados": payload.fonte_dados,
        "mensagem": "Análise iniciada via Storage. Faça polling em /api/ofertas/status/{analise_id}",
    }

