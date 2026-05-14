"""
Router WhatsApp — Endpoints para integração WhatsApp / Cron automático.

Endpoints:
  POST /cron-whatsapp       → Chamado pelo pg_cron (1x por empresa), processa em background
  POST /webhook             → Recebe mensagens da Uazapi em tempo real
  POST /instancia/criar     → Cria instância na Uazapi + QR code (self-service)
  GET  /instancia/status    → Polling de status + QR code atualizado
  GET  /instancia           → Consulta instância salva da empresa
  POST /instancia/desconectar → Desconecta instância
  POST /instancia/reconectar  → Reconecta instância (novo QR)

SEGURANÇA:
  - /cron-whatsapp: protegido por X-Cron-Secret (não usa JWT)
  - /webhook: protegido por token estático da instância Uazapi
  - /instancia/*: protegido por JWT (via get_current_empresa_id)
"""
from __future__ import annotations

import logging
import os
from collections import defaultdict
from datetime import datetime, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel

from app.db.supabase_client import get_settings, get_supabase_client
from app.middleware import get_current_empresa_id

logger = logging.getLogger(__name__)
router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# 1. CRON ENDPOINT — chamado pelo pg_cron (1x por empresa)
# ═══════════════════════════════════════════════════════════════════════════════


async def verify_cron_secret(request: Request):
    """Dependency que valida o secret do pg_cron.
    Separada do JWT — este endpoint é chamado server-to-server."""
    secret = request.headers.get("X-Cron-Secret")
    expected = os.getenv("CRON_SECRET")
    if not expected:
        raise HTTPException(503, "CRON_SECRET não configurada no servidor.")
    if secret != expected:
        raise HTTPException(401, "Unauthorized")


class CronWhatsAppRequest(BaseModel):
    empresa_id: str


@router.post("/cron-whatsapp", dependencies=[Depends(verify_cron_secret)])
async def cron_analise_whatsapp(
    payload: CronWhatsAppRequest,
    background_tasks: BackgroundTasks,
):
    """Chamado pelo pg_cron a cada 2h (1 call por empresa).
    Retorna 200 imediatamente, processa em background."""

    empresa_id = payload.empresa_id
    client = get_supabase_client()
    if not client:
        raise HTTPException(503, "Supabase client indisponível.")

    # Buscar msgs pendentes DESTA empresa
    msgs_response = (
        client.table("whatsapp_mensagens")
        .select("*")
        .eq("empresa_id", empresa_id)
        .in_("status_analise", ["pendente", "erro_analise"])
        .eq("tipo_mensagem", "text")
        .order("timestamp_msg")
        .limit(50)
        .execute()
    )

    if not msgs_response.data:
        return {"status": "ok", "empresa_id": empresa_id, "processados": 0}

    # Agrupar por chat_id (dentro da mesma empresa)
    grupos: dict[str, list[dict]] = defaultdict(list)
    for msg in msgs_response.data:
        grupos[msg["chat_id"]].append(msg)

    # Processar em background (evita timeout)
    background_tasks.add_task(
        _processar_cron_empresa,
        empresa_id=empresa_id,
        grupos=dict(grupos),
    )

    return {
        "status": "ok",
        "empresa_id": empresa_id,
        "chats_enfileirados": len(grupos),
    }


async def _processar_cron_empresa(empresa_id: str, grupos: dict):
    """Background task que processa os chats de UMA empresa."""
    # Import local para evitar dependência circular
    from app.routers.ofertas import _executar_e_persistir

    client = get_supabase_client()
    if not client:
        logger.error(f"[CRON] Supabase indisponível para empresa {empresa_id}")
        return

    resultados = []

    for chat_id, mensagens in grupos.items():
        texto_concatenado = "\n---\n".join(
            m["conteudo_texto"] for m in mensagens if m.get("conteudo_texto")
        )
        msg_ids = [m["id"] for m in mensagens]

        if not texto_concatenado.strip():
            # Mensagens sem texto (ex: imagens) — marcar como ignoradas
            try:
                client.table("whatsapp_mensagens") \
                    .update({"status_analise": "ignorada"}) \
                    .in_("id", msg_ids).execute()
            except Exception:
                pass
            continue

        # Marcar como em_analise
        try:
            client.table("whatsapp_mensagens") \
                .update({"status_analise": "em_analise"}) \
                .in_("id", msg_ids).execute()
        except Exception as e:
            logger.error(f"[CRON] Erro ao marcar msgs em_analise: {e}")
            continue

        analise_id = str(uuid4())

        # Criar registro "processando" no banco (como o fluxo async faz)
        try:
            client.table("analises_oferta").insert({
                "id": analise_id,
                "empresa_id": empresa_id,
                "usuario_id": None,  # análise automática
                "origem": "whatsapp",
                "entrada_bruta": texto_concatenado[:5000],  # truncar se muito grande
                "status": "processando",
                "created_at": datetime.now(ZoneInfo("UTC")).isoformat(),
            }).execute()
        except Exception as e:
            logger.error(f"[CRON] Erro ao criar registro analise: {e}")
            client.table("whatsapp_mensagens") \
                .update({"status_analise": "pendente"}) \
                .in_("id", msg_ids).execute()
            continue

        try:
            # Reutiliza _executar_e_persistir do ofertas.py
            await _executar_e_persistir(
                analise_id=analise_id,
                empresa_id=empresa_id,
                usuario_id=None,
                texto_bruto=texto_concatenado,
                fornecedor_informado=None,
                is_async=True,
                origem="whatsapp",
            )

            # Atualizar registro com status concluída
            client.table("analises_oferta").update({
                "status": "concluida",
            }).eq("id", analise_id).execute()

            # Marcar mensagens como analisadas
            client.table("whatsapp_mensagens") \
                .update({
                    "status_analise": "analisada",
                    "analise_id": analise_id,
                }).in_("id", msg_ids).execute()

            resultados.append({
                "analise_id": analise_id,
                "chat_id": chat_id,
                "total_msgs": len(mensagens),
            })

        except Exception as e:
            logger.exception(f"[CRON] Erro ao analisar chat {chat_id}: {e}")
            client.table("whatsapp_mensagens") \
                .update({"status_analise": "erro_analise"}) \
                .in_("id", msg_ids).execute()
            client.table("analises_oferta").update({
                "status": "erro",
                "resultado_json": {"erro": str(e)},
            }).eq("id", analise_id).execute()

    # ─── NOTIFICAÇÕES (após processar todos os chats da empresa) ───
    if resultados:
        await _enviar_notificacoes(
            empresa_id=empresa_id,
            total_analises=len(resultados),
            resumo=resultados,
        )

    logger.info(
        f"[CRON] Empresa {empresa_id}: "
        f"{len(resultados)} análises concluídas de {len(grupos)} chats"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 2. NOTIFICAÇÕES — 3 canais: in-app, email, WhatsApp
# ═══════════════════════════════════════════════════════════════════════════════


async def _enviar_notificacoes(
    empresa_id: str,
    total_analises: int,
    resumo: list[dict],
):
    """Dispara notificações nos 3 canais após o cron processar."""
    client = get_supabase_client()
    if not client:
        return

    # 1. Notificação in-app (salvar no banco — o frontend escuta via Realtime)
    try:
        client.table("notificacoes").insert({
            "empresa_id": empresa_id,
            "tipo": "analise_whatsapp",
            "titulo": f"📊 {total_analises} nova(s) análise(s) de oferta",
            "mensagem": (
                f"O sistema analisou automaticamente {total_analises} "
                f"grupo(s) de mensagens do WhatsApp."
            ),
            "link": "/ofertas/historico",
            "metadata": {"resumo": resumo},
        }).execute()
    except Exception as e:
        logger.error(f"[NOTIF] Erro ao salvar notificação in-app: {e}")

    # Buscar dados da empresa para email/WhatsApp
    try:
        empresa_data = (
            client.table("empresas")
            .select("nome, notificacao_email, notificacao_whatsapp, notificacoes_ativas")
            .eq("id", empresa_id)
            .single()
            .execute()
        )
        empresa = empresa_data.data
    except Exception as e:
        logger.error(f"[NOTIF] Erro ao buscar empresa: {e}")
        return

    if not empresa or not empresa.get("notificacoes_ativas", True):
        return

    nome_empresa = empresa.get("nome", "Empresa")

    # 2. Notificação por Email (via Resend)
    email_destino = empresa.get("notificacao_email")
    if email_destino:
        await _enviar_email_notificacao(
            email=email_destino,
            nome_empresa=nome_empresa,
            total_analises=total_analises,
        )

    # 3. Notificação por WhatsApp (via Uazapi)
    whatsapp_destino = empresa.get("notificacao_whatsapp")
    if whatsapp_destino:
        await _enviar_whatsapp_notificacao(
            empresa_id=empresa_id,
            numero_destino=whatsapp_destino,
            nome_empresa=nome_empresa,
            total_analises=total_analises,
        )


async def _enviar_email_notificacao(
    email: str,
    nome_empresa: str,
    total_analises: int,
):
    """Envia notificação por email via Resend."""
    try:
        import resend

        resend_key = os.getenv("RESEND_API_KEY")
        if not resend_key:
            logger.warning("[NOTIF] RESEND_API_KEY não configurada, email pulado.")
            return

        resend.api_key = resend_key

        resend.Emails.send({
            "from": "ComprasPRO <notificacoes@compraspro.com.br>",
            "to": [email],
            "subject": f"📊 {total_analises} nova(s) análise(s) — {nome_empresa}",
            "html": f"""
            <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #1a73e8;">ComprasPRO — Análise Automática</h2>
                <p>Olá!</p>
                <p>O sistema analisou automaticamente <strong>{total_analises} grupo(s)
                de mensagens</strong> recebidas via WhatsApp para <strong>{nome_empresa}</strong>.</p>
                <p>Acesse a plataforma para ver os resultados detalhados:</p>
                <a href="{os.getenv('NEXT_PUBLIC_APP_URL', 'https://compraspro.com.br')}/ofertas/historico"
                   style="display: inline-block; padding: 12px 24px; background: #1a73e8;
                   color: white; text-decoration: none; border-radius: 6px; margin: 16px 0;">
                    Ver Análises
                </a>
                <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">
                <p style="font-size: 12px; color: #888;">
                    Esta é uma notificação automática do ComprasPRO.
                </p>
            </div>
            """,
        })
        logger.info(f"[NOTIF] Email enviado para {email}")

    except ImportError:
        logger.warning("[NOTIF] Pacote 'resend' não instalado. Email pulado.")
    except Exception as e:
        logger.error(f"[NOTIF] Erro ao enviar email: {e}")


async def _enviar_whatsapp_notificacao(
    empresa_id: str,
    numero_destino: str,
    nome_empresa: str,
    total_analises: int,
):
    """Envia notificação por WhatsApp via Uazapi (usando a instância da empresa)."""

    client = get_supabase_client()
    if not client:
        return

    try:
        # Buscar instância conectada da empresa
        inst_response = (
            client.table("whatsapp_instancias")
            .select("instance_id, api_token")
            .eq("empresa_id", empresa_id)
            .eq("status", "conectada")
            .limit(1)
            .execute()
        )

        if not inst_response.data:
            logger.warning(f"[NOTIF] Sem instância WhatsApp conectada para empresa {empresa_id}")
            return

        instancia = inst_response.data[0]
        instance_id = instancia["instance_id"]
        api_token = instancia["api_token"]

        # Formatar número (remover caracteres não-numéricos, adicionar @c.us)
        numero_limpo = "".join(c for c in numero_destino if c.isdigit())
        if not numero_limpo.endswith("@c.us"):
            numero_limpo = f"{numero_limpo}@c.us"

        mensagem = (
            f"📊 *ComprasPRO — Análise Automática*\n\n"
            f"Olá! O sistema analisou automaticamente *{total_analises} grupo(s) "
            f"de mensagens* recebidas via WhatsApp para *{nome_empresa}*.\n\n"
            f"Acesse a plataforma para ver os resultados detalhados.\n\n"
            f"_Notificação automática do ComprasPRO._"
        )

        settings = get_settings()
        base_url = settings.uazapi_base_url

        async with httpx.AsyncClient(timeout=15.0) as http_client:
            response = await http_client.post(
                f"{base_url}/send/text",
                headers={
                    "Content-Type": "application/json",
                    "token": api_token,
                },
                json={
                    "number": numero_limpo,
                    "text": mensagem,
                },
            )
            if response.status_code == 200:
                logger.info(f"[NOTIF] WhatsApp enviado para {numero_destino}")
            else:
                logger.error(
                    f"[NOTIF] Erro ao enviar WhatsApp: {response.status_code} - {response.text}"
                )

    except Exception as e:
        logger.error(f"[NOTIF] Erro ao enviar WhatsApp: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# 3. WEBHOOK — Recebe mensagens da Uazapi em tempo real
# ═══════════════════════════════════════════════════════════════════════════════


# Cache de instâncias em memória com TTL de 5 minutos
_CACHE_TTL_SECONDS = 300
_instance_cache: dict[str, tuple[dict, float]] = {}


def _cache_get(key: str) -> dict | None:
    """Busca no cache com verificação de TTL."""
    entry = _instance_cache.get(key)
    if entry is None:
        return None
    data, ts = entry
    if (datetime.now(ZoneInfo("UTC")).timestamp() - ts) > _CACHE_TTL_SECONDS:
        _instance_cache.pop(key, None)
        return None
    return data


def _cache_set(key: str, data: dict) -> None:
    """Armazena no cache com timestamp."""
    _instance_cache[key] = (data, datetime.now(ZoneInfo("UTC")).timestamp())


async def _get_instancia_by_token(token: str) -> dict | None:
    """Busca instância pelo api_token, com cache em memória (TTL 5min)."""
    cache_key = f"token:{token}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    client = get_supabase_client()
    if not client:
        return None

    try:
        result = (
            client.table("whatsapp_instancias")
            .select("id, empresa_id, instance_id, status")
            .eq("api_token", token)
            .limit(1)
            .execute()
        )
        if result.data:
            _cache_set(cache_key, result.data[0])
            return result.data[0]
    except Exception as e:
        logger.error(f"[WEBHOOK] Erro ao buscar instância por token: {e}")

    return None


async def _get_instancia_by_instance_id(instance_id: str) -> dict | None:
    """Busca instância pelo instance_id da Uazapi, com cache em memória (TTL 5min)."""
    cache_key = f"iid:{instance_id}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    client = get_supabase_client()
    if not client:
        return None

    try:
        result = (
            client.table("whatsapp_instancias")
            .select("id, empresa_id, instance_id, status")
            .eq("instance_id", instance_id)
            .limit(1)
            .execute()
        )
        if result.data:
            _cache_set(cache_key, result.data[0])
            return result.data[0]
    except Exception as e:
        logger.error(f"[WEBHOOK] Erro ao buscar instância por instance_id: {e}")

    return None


class UazapiWebhookPayload(BaseModel):
    """Payload simplificado do webhook da Uazapi."""
    event: str | None = None
    data: dict | None = None


@router.post("/webhook")
async def webhook_uazapi(request: Request):
    """Recebe mensagens da Uazapi via webhook.

    Autenticação flexível — aceita 3 formas:
    1. Token via header Authorization: Bearer <token>
    2. Token via query param ?token=<token>
    3. instance_id no body do payload (formato padrão da Uazapi)
    """

    # Processar payload primeiro (necessário para fallback por instance_id)
    try:
        body = await request.json()
    except Exception:
        return {"status": "ok", "ignored": True, "reason": "invalid_json"}

    # Tentar autenticar via token (header ou query param)
    instancia = None
    auth_header = request.headers.get("Authorization", "")
    token = None
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    else:
        token = request.query_params.get("token")

    if token:
        instancia = await _get_instancia_by_token(token)

    # Fallback: buscar pela instance_id no body (formato padrão Uazapi)
    if not instancia:
        instance_id_from_body = body.get("instance")
        if instance_id_from_body:
            instancia = await _get_instancia_by_instance_id(instance_id_from_body)

    if not instancia:
        logger.warning(f"[WEBHOOK] Instância não identificada. token={bool(token)}, instance={body.get('instance')}")
        raise HTTPException(401, "Instância não identificada.")

    # Extrair event e data do payload já lido
    event = body.get("event", "")
    data = body.get("data", body)  # Uazapi às vezes envia flat, às vezes nested

    # Só processar eventos de mensagem recebida
    if event not in ("messages", "messages.upsert", "message", ""):
        return {"status": "ok", "event": event, "ignored": True}

    # Extrair dados da mensagem
    message_data = _parse_uazapi_message(data)
    if not message_data:
        return {"status": "ok", "no_message": True}

    # A1: Ignorar mensagens enviadas pelo próprio número (fromMe)
    raw_key = data.get("key", {}) if isinstance(data, dict) else {}
    messages_arr = data.get("messages", [])
    if isinstance(messages_arr, list) and messages_arr:
        raw_key = messages_arr[0].get("key", {})
    if raw_key.get("fromMe", False):
        return {"status": "ok", "ignored": True, "reason": "fromMe"}

    # Salvar no banco (idempotente via UNIQUE constraint)
    client = get_supabase_client()
    if not client:
        raise HTTPException(503, "Supabase indisponível.")

    try:
        client.table("whatsapp_mensagens").upsert(
            {
                "empresa_id": instancia["empresa_id"],
                "instancia_id": instancia["id"],
                "message_id": message_data["message_id"],
                "chat_id": message_data["chat_id"],
                "chat_name": message_data.get("chat_name"),
                "sender_id": message_data.get("sender_id"),
                "sender_name": message_data.get("sender_name"),
                "sender_phone": message_data.get("sender_phone"),
                "is_group": message_data.get("is_group", False),
                "tipo_mensagem": message_data.get("tipo_mensagem", "text"),
                "conteudo_texto": message_data.get("conteudo_texto"),
                "media_url": message_data.get("media_url"),
                "timestamp_msg": message_data["timestamp_msg"],
                "status_analise": "pendente",
                "raw_payload": body,
            },
            on_conflict="instancia_id,message_id",
        ).execute()
    except Exception as e:
        logger.error(f"[WEBHOOK] Erro ao salvar mensagem: {e}")
        # M4: Não expõe detalhes internos — webhook deve retornar 200 para Uazapi não retentar
        return {"status": "error", "detail": "Erro interno ao processar mensagem."}

    return {"status": "ok", "saved": True}


def _parse_uazapi_message(data: dict) -> dict | None:
    """Extrai campos relevantes do payload Uazapi.

    A Uazapi pode enviar em diferentes formatos dependendo do evento.
    Esta função normaliza para o formato interno.
    """
    if not data:
        return None

    # Formato 1: data.messages[] (messages.upsert)
    messages = data.get("messages", [])
    if isinstance(messages, list) and messages:
        msg = messages[0]
    else:
        msg = data

    # Extrair message_id
    message_id = msg.get("key", {}).get("id") or msg.get("id")
    if not message_id:
        return None

    # Extrair chat_id e detectar grupo
    key = msg.get("key", {})
    chat_id = key.get("remoteJid") or msg.get("from") or msg.get("chatId")
    if not chat_id:
        return None

    is_group = chat_id.endswith("@g.us")

    # Extrair sender
    sender_id = key.get("participant") or msg.get("participant")
    sender_name = msg.get("pushName") or msg.get("senderName")

    # Extrair conteúdo
    message_content = msg.get("message", {})
    tipo_mensagem = "text"
    conteudo_texto = None
    media_url = None

    if isinstance(message_content, dict):
        if "conversation" in message_content:
            conteudo_texto = message_content["conversation"]
        elif "extendedTextMessage" in message_content:
            conteudo_texto = message_content["extendedTextMessage"].get("text")
        elif "imageMessage" in message_content:
            tipo_mensagem = "image"
            conteudo_texto = message_content["imageMessage"].get("caption")
            media_url = message_content["imageMessage"].get("url")
        elif "documentMessage" in message_content:
            tipo_mensagem = "document"
            conteudo_texto = message_content["documentMessage"].get("caption")
        elif "audioMessage" in message_content:
            tipo_mensagem = "audio"
        elif "videoMessage" in message_content:
            tipo_mensagem = "video"
            conteudo_texto = message_content["videoMessage"].get("caption")
            media_url = message_content["videoMessage"].get("url")
        else:
            tipo_mensagem = "other"
    elif isinstance(message_content, str):
        conteudo_texto = message_content

    # Extrair timestamp
    timestamp_raw = msg.get("messageTimestamp")
    if timestamp_raw:
        try:
            ts = int(timestamp_raw)
            timestamp_msg = datetime.fromtimestamp(ts, tz=ZoneInfo("UTC")).isoformat()
        except (ValueError, TypeError, OSError):
            timestamp_msg = datetime.now(ZoneInfo("UTC")).isoformat()
    else:
        timestamp_msg = datetime.now(ZoneInfo("UTC")).isoformat()

    return {
        "message_id": message_id,
        "chat_id": chat_id,
        "chat_name": msg.get("chatName"),
        "sender_id": sender_id,
        "sender_name": sender_name,
        "sender_phone": sender_id.split("@")[0] if sender_id and "@" in sender_id else None,
        "is_group": is_group,
        "tipo_mensagem": tipo_mensagem,
        "conteudo_texto": conteudo_texto,
        "media_url": media_url,
        "timestamp_msg": timestamp_msg,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 4. CONEXÃO SELF-SERVICE — Instância WhatsApp (protegido por JWT)
# ═══════════════════════════════════════════════════════════════════════════════


def _get_uazapi_config() -> tuple[str, str]:
    """Retorna (base_url, admin_token) da Uazapi."""
    settings = get_settings()
    base_url = settings.uazapi_base_url
    admin_token = settings.uazapi_admin_token
    if not admin_token:
        raise HTTPException(503, "UAZAPI_ADMIN_TOKEN não configurado.")
    return base_url, admin_token


@router.get("/instancia")
async def get_instancia(empresa_id: str = Depends(get_current_empresa_id)):
    """Consulta a instância WhatsApp da empresa."""
    client = get_supabase_client()
    if not client:
        raise HTTPException(503, "Supabase indisponível.")

    result = (
        client.table("whatsapp_instancias")
        .select("id, instance_id, status, numero_telefone, nome_instancia, created_at, updated_at")
        .eq("empresa_id", empresa_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if not result.data:
        return {"instancia": None}

    return {"instancia": result.data[0]}


@router.post("/instancia/criar")
async def criar_instancia_whatsapp(
    empresa_id: str = Depends(get_current_empresa_id),
):
    """Cria instância na Uazapi, configura webhook e retorna QR code.

    Fluxo completo:
    1. POST /instance/create (admintoken) → cria instância
    2. POST /webhook (token) → configura webhook ComprasPRO
    3. POST /instance/connect (token) → gera QR code
    4. Salva tudo no Supabase
    5. Retorna QR code para o frontend
    """
    base_url, admin_token = _get_uazapi_config()
    client = get_supabase_client()
    if not client:
        raise HTTPException(503, "Supabase indisponível.")

    # Verificar se já existe instância para esta empresa
    existing = (
        client.table("whatsapp_instancias")
        .select("id, instance_id, api_token, status")
        .eq("empresa_id", empresa_id)
        .limit(1)
        .execute()
    )

    if existing.data and existing.data[0].get("status") == "conectada":
        raise HTTPException(409, "Esta empresa já possui uma instância WhatsApp conectada.")

    async with httpx.AsyncClient(timeout=30.0) as http:
        # ── 1. Criar instância na Uazapi ──
        nome_instancia = f"compraspro-{empresa_id[:8]}"
        create_resp = await http.post(
            f"{base_url}/instance/create",
            headers={"admintoken": admin_token, "Content-Type": "application/json"},
            json={"name": nome_instancia},
        )

        if create_resp.status_code != 200:
            logger.error(f"[UAZAPI] Erro ao criar instância: {create_resp.status_code} - {create_resp.text}")
            raise HTTPException(502, f"Erro ao criar instância na Uazapi: {create_resp.text}")

        create_data = create_resp.json()
        instance_token = create_data.get("token")
        instance_id = create_data.get("instance", {}).get("id") or create_data.get("id") or nome_instancia

        if not instance_token:
            raise HTTPException(502, "Uazapi não retornou token da instância.")

        # ── 2. Configurar webhook automaticamente ──
        webhook_url = os.getenv("FASTAPI_URL", "https://compraspro.onrender.com")
        webhook_url = f"{webhook_url}/api/whatsapp/webhook"

        webhook_resp = await http.post(
            f"{base_url}/webhook",
            headers={"token": instance_token, "Content-Type": "application/json"},
            json={
                "enabled": True,
                "url": webhook_url,
                "events": ["messages", "connection"],
                "excludeMessages": ["wasSentByApi", "fromMeYes"],
            },
        )

        if webhook_resp.status_code != 200:
            logger.warning(f"[UAZAPI] Webhook não configurado: {webhook_resp.status_code} - {webhook_resp.text}")
            # Não bloqueia — o webhook pode ser configurado depois

        # ── 3. Iniciar conexão (gerar QR code) ──
        connect_resp = await http.post(
            f"{base_url}/instance/connect",
            headers={"token": instance_token, "Content-Type": "application/json"},
            json={},  # sem 'phone' → gera QR code
        )

        qrcode_base64 = None
        if connect_resp.status_code == 200:
            connect_data = connect_resp.json()
            instance_info = connect_data.get("instance", {})
            qrcode_base64 = instance_info.get("qrcode")
        else:
            logger.warning(f"[UAZAPI] Erro ao conectar: {connect_resp.status_code} - {connect_resp.text}")

    # ── 4. Salvar no Supabase ──
    now_iso = datetime.now(ZoneInfo("UTC")).isoformat()
    data = {
        "empresa_id": empresa_id,
        "instance_id": instance_id,
        "api_token": instance_token,
        "nome_instancia": nome_instancia,
        "status": "aguardando_qr",
        "updated_at": now_iso,
    }

    if existing.data:
        client.table("whatsapp_instancias") \
            .update(data) \
            .eq("id", existing.data[0]["id"]).execute()
    else:
        client.table("whatsapp_instancias").insert(data).execute()

    _instance_cache.clear()

    return {
        "status": "aguardando_qr",
        "qrcode": qrcode_base64,
        "instance_id": instance_id,
        "nome_instancia": nome_instancia,
    }


@router.get("/instancia/status")
async def get_instancia_status(
    empresa_id: str = Depends(get_current_empresa_id),
):
    """Polling de status da instância. Retorna status + QR code atualizado.

    O frontend chama a cada 3s enquanto status = 'aguardando_qr'.
    Quando status muda para 'connected', atualiza o DB.
    """
    base_url, _ = _get_uazapi_config()
    client = get_supabase_client()
    if not client:
        raise HTTPException(503, "Supabase indisponível.")

    # Buscar instância da empresa
    result = (
        client.table("whatsapp_instancias")
        .select("id, instance_id, api_token, status, nome_instancia")
        .eq("empresa_id", empresa_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if not result.data:
        return {"instancia": None, "status": "sem_instancia"}

    instancia = result.data[0]
    token = instancia["api_token"]

    # Consultar status na Uazapi
    try:
        async with httpx.AsyncClient(timeout=15.0) as http:
            status_resp = await http.get(
                f"{base_url}/instance/status",
                headers={"token": token},
            )
    except (httpx.TimeoutException, httpx.ConnectError) as exc:
        logger.warning(f"[STATUS] Erro de rede ao consultar Uazapi: {exc}")
        return {
            "status": "desconectada",
            "erro": "Não foi possível conectar à Uazapi. Tente novamente.",
            "nome_instancia": instancia.get("nome_instancia"),
            "instance_id": instancia["instance_id"],
            "mensagens_pendentes": 0,
        }

    if status_resp.status_code == 401:
        # Token inválido — instância não existe mais na Uazapi
        logger.warning(f"[STATUS] Uazapi retornou 401 para instância {instancia['instance_id']}. Marcando como desconectada.")
        client.table("whatsapp_instancias") \
            .update({
                "status": "desconectada",
                "updated_at": datetime.now(ZoneInfo("UTC")).isoformat(),
            }) \
            .eq("id", instancia["id"]).execute()
        _instance_cache.clear()
        return {
            "status": "desconectada",
            "erro": "Instância expirou na Uazapi. Reconecte para gerar um novo QR Code.",
            "nome_instancia": instancia.get("nome_instancia"),
            "instance_id": instancia["instance_id"],
            "mensagens_pendentes": 0,
        }

    if status_resp.status_code != 200:
        logger.warning(f"[STATUS] Uazapi retornou {status_resp.status_code}: {status_resp.text[:200]}")
        return {
            "status": "desconectada",
            "erro": f"Erro ao consultar Uazapi (código {status_resp.status_code}). Tente reconectar.",
            "nome_instancia": instancia.get("nome_instancia"),
            "instance_id": instancia["instance_id"],
            "mensagens_pendentes": 0,
        }

    status_data = status_resp.json()
    uazapi_instance = status_data.get("instance", {})
    uazapi_status = status_data.get("status", {})

    # Mapear status Uazapi → status interno
    is_connected = uazapi_status.get("connected", False)
    uazapi_raw_status = uazapi_instance.get("status", "disconnected")
    qrcode = uazapi_instance.get("qrcode")
    profile_name = uazapi_instance.get("profileName")
    phone_number = None

    jid = uazapi_status.get("jid")
    if jid and isinstance(jid, dict):
        phone_number = jid.get("user")

    if is_connected and instancia["status"] != "conectada":
        # Atualizar status no DB
        update_data = {
            "status": "conectada",
            "nome_instancia": profile_name or instancia.get("nome_instancia"),
            "updated_at": datetime.now(ZoneInfo("UTC")).isoformat(),
        }
        if phone_number:
            update_data["numero_telefone"] = phone_number

        client.table("whatsapp_instancias") \
            .update(update_data) \
            .eq("id", instancia["id"]).execute()

        _instance_cache.clear()

    elif uazapi_raw_status == "disconnected" and instancia["status"] == "conectada":
        client.table("whatsapp_instancias") \
            .update({
                "status": "desconectada",
                "updated_at": datetime.now(ZoneInfo("UTC")).isoformat(),
            }) \
            .eq("id", instancia["id"]).execute()
        _instance_cache.clear()

    status_interno = (
        "conectada" if is_connected
        else "aguardando_qr" if uazapi_raw_status == "connecting"
        else "desconectada"
    )

    # C3: Contar mensagens pendentes com mesmo filtro do /analisar (tipo_mensagem='text')
    mensagens_pendentes = 0
    if is_connected:
        try:
            count_result = (
                client.table("whatsapp_mensagens")
                .select("id", count="exact")
                .eq("empresa_id", empresa_id)
                .in_("status_analise", ["pendente", "erro_analise"])
                .eq("tipo_mensagem", "text")
                .execute()
            )
            mensagens_pendentes = count_result.count or 0
        except Exception:
            pass  # Não bloqueia o status se a contagem falhar

    return {
        "status": status_interno,
        "qrcode": qrcode if not is_connected else None,
        "profile_name": profile_name,
        "numero_telefone": phone_number,
        "nome_instancia": instancia.get("nome_instancia"),
        "instance_id": instancia["instance_id"],
        "mensagens_pendentes": mensagens_pendentes,
    }


@router.post("/instancia/desconectar")
async def desconectar_instancia(
    empresa_id: str = Depends(get_current_empresa_id),
):
    """Desconecta a instância WhatsApp da empresa."""
    base_url, _ = _get_uazapi_config()
    client = get_supabase_client()
    if not client:
        raise HTTPException(503, "Supabase indisponível.")

    result = (
        client.table("whatsapp_instancias")
        .select("id, api_token")
        .eq("empresa_id", empresa_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if not result.data:
        raise HTTPException(404, "Nenhuma instância WhatsApp encontrada.")

    instancia = result.data[0]

    async with httpx.AsyncClient(timeout=15.0) as http:
        await http.post(
            f"{base_url}/instance/disconnect",
            headers={"token": instancia["api_token"]},
        )

    client.table("whatsapp_instancias") \
        .update({
            "status": "desconectada",
            "updated_at": datetime.now(ZoneInfo("UTC")).isoformat(),
        }) \
        .eq("id", instancia["id"]).execute()

    _instance_cache.clear()
    return {"status": "desconectada"}


@router.post("/instancia/reconectar")
async def reconectar_instancia(
    empresa_id: str = Depends(get_current_empresa_id),
):
    """Reconecta uma instância existente (gera novo QR code)."""
    base_url, _ = _get_uazapi_config()
    client = get_supabase_client()
    if not client:
        raise HTTPException(503, "Supabase indisponível.")

    result = (
        client.table("whatsapp_instancias")
        .select("id, api_token, status")
        .eq("empresa_id", empresa_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if not result.data:
        raise HTTPException(404, "Nenhuma instância WhatsApp encontrada.")

    instancia = result.data[0]

    async with httpx.AsyncClient(timeout=15.0) as http:
        connect_resp = await http.post(
            f"{base_url}/instance/connect",
            headers={"token": instancia["api_token"], "Content-Type": "application/json"},
            json={},
        )

    qrcode_base64 = None
    if connect_resp.status_code == 200:
        connect_data = connect_resp.json()
        instance_info = connect_data.get("instance", {})
        qrcode_base64 = instance_info.get("qrcode")

    client.table("whatsapp_instancias") \
        .update({
            "status": "aguardando_qr",
            "updated_at": datetime.now(ZoneInfo("UTC")).isoformat(),
        }) \
        .eq("id", instancia["id"]).execute()

    _instance_cache.clear()

    return {
        "status": "aguardando_qr",
        "qrcode": qrcode_base64,
    }


@router.post("/instancia/sincronizar")
async def sincronizar_mensagens(
    empresa_id: str = Depends(get_current_empresa_id),
):
    """Sincroniza mensagens recentes da Uazapi (últimas 2h).

    Busca mensagens via API /message/find da Uazapi e salva no banco.
    Filtra apenas mensagens recebidas (não enviadas pelo dono).
    """
    base_url, _ = _get_uazapi_config()
    client = get_supabase_client()
    if not client:
        raise HTTPException(503, "Supabase indisponível.")

    # Buscar instância conectada
    result = (
        client.table("whatsapp_instancias")
        .select("id, instance_id, api_token, status")
        .eq("empresa_id", empresa_id)
        .eq("status", "conectada")
        .limit(1)
        .execute()
    )

    if not result.data:
        raise HTTPException(400, "Nenhuma instância WhatsApp conectada.")

    instancia = result.data[0]
    token = instancia["api_token"]

    # Timestamp de 2 horas atrás (em ms)
    cutoff_ms = int((datetime.now(ZoneInfo("UTC")) - timedelta(hours=2)).timestamp() * 1000)

    # Buscar mensagens via API da Uazapi
    total_salvas = 0
    total_buscadas = 0
    offset = 0
    max_pages = 10  # Segurança: máximo de 10 páginas (2000 mensagens)

    try:
        async with httpx.AsyncClient(timeout=30.0) as http:
            for _ in range(max_pages):
                resp = await http.post(
                    f"{base_url}/message/find",
                    headers={"token": token, "Content-Type": "application/json"},
                    json={"limit": 200, "offset": offset},
                )

                if resp.status_code != 200:
                    logger.warning(f"[SYNC] Uazapi /message/find retornou {resp.status_code}")
                    break

                data = resp.json()
                messages = data.get("messages", [])
                if not messages:
                    break

                total_buscadas += len(messages)

                # Filtrar: só mensagens recebidas (não fromMe) e dentro das últimas 2h
                mensagens_para_salvar = []
                oldest_timestamp = None

                for msg in messages:
                    msg_ts = msg.get("messageTimestamp", 0)

                    # Rastrear a mensagem mais antiga da página
                    if oldest_timestamp is None or msg_ts < oldest_timestamp:
                        oldest_timestamp = msg_ts

                    # Pular se é mais antiga que 2h
                    if msg_ts < cutoff_ms:
                        continue

                    # Pular mensagens enviadas pelo próprio número
                    if msg.get("fromMe", True):
                        continue

                    # Extrair dados
                    message_id = msg.get("messageid") or msg.get("id", "")
                    chat_id = msg.get("chatid", "")
                    if not message_id or not chat_id:
                        continue

                    is_group = msg.get("isGroup", False)
                    msg_type = msg.get("messageType", "text").lower()
                    text_content = msg.get("text", "")

                    # Mapear tipo
                    tipo = "text"
                    if "image" in msg_type:
                        tipo = "image"
                    elif "video" in msg_type:
                        tipo = "video"
                    elif "audio" in msg_type or "ptt" in msg_type:
                        tipo = "audio"
                    elif "document" in msg_type:
                        tipo = "document"

                    # Timestamp para ISO
                    ts_seconds = msg_ts / 1000 if msg_ts > 9999999999 else msg_ts
                    try:
                        ts_iso = datetime.fromtimestamp(ts_seconds, tz=ZoneInfo("UTC")).isoformat()
                    except (ValueError, OSError):
                        ts_iso = datetime.now(ZoneInfo("UTC")).isoformat()

                    mensagens_para_salvar.append({
                        "empresa_id": empresa_id,
                        "instancia_id": instancia["id"],
                        "message_id": message_id,
                        "chat_id": chat_id,
                        "sender_name": msg.get("senderName"),
                        "sender_phone": msg.get("sender"),
                        "is_group": is_group,
                        "tipo_mensagem": tipo,
                        "conteudo_texto": text_content[:5000] if text_content else None,
                        "media_url": msg.get("fileURL") or None,
                        "timestamp_msg": ts_iso,
                        "status_analise": "pendente",
                    })

                # Salvar em batch via upsert
                if mensagens_para_salvar:
                    try:
                        client.table("whatsapp_mensagens").upsert(
                            mensagens_para_salvar,
                            on_conflict="instancia_id,message_id",
                        ).execute()
                        total_salvas += len(mensagens_para_salvar)
                    except Exception as e:
                        logger.error(f"[SYNC] Erro ao salvar batch: {e}")

                # Parar se não tem mais páginas ou se já passou do cutoff
                if not data.get("hasMore", False):
                    break
                if oldest_timestamp and oldest_timestamp < cutoff_ms:
                    break  # Todas as mensagens restantes são mais antigas

                offset = data.get("nextOffset", offset + 200)

    except (httpx.TimeoutException, httpx.ConnectError) as exc:
        logger.error(f"[SYNC] Erro de rede: {exc}")
        raise HTTPException(502, "Erro ao conectar com Uazapi.")

    return {
        "status": "ok",
        "total_buscadas": total_buscadas,
        "total_salvas": total_salvas,
    }

@router.post("/instancia/analisar")
async def analisar_mensagens_whatsapp(
    background_tasks: BackgroundTasks,
    empresa_id: str = Depends(get_current_empresa_id),
):
    """Dispara análise manual das mensagens pendentes do WhatsApp da empresa.

    Chamado pelo botão "Analisar WhatsApp" no frontend.
    Reutiliza a mesma lógica de background do cron.
    """
    client = get_supabase_client()
    if not client:
        raise HTTPException(503, "Supabase indisponível.")

    # Verificar se WhatsApp está conectado
    instancia = (
        client.table("whatsapp_instancias")
        .select("id, status")
        .eq("empresa_id", empresa_id)
        .eq("status", "conectada")
        .limit(1)
        .execute()
    )

    if not instancia.data:
        raise HTTPException(400, "WhatsApp não está conectado.")

    # Buscar mensagens pendentes
    msgs_response = (
        client.table("whatsapp_mensagens")
        .select("*")
        .eq("empresa_id", empresa_id)
        .in_("status_analise", ["pendente", "erro_analise"])
        .eq("tipo_mensagem", "text")
        .order("timestamp_msg")
        .limit(50)
        .execute()
    )

    if not msgs_response.data:
        return {"status": "ok", "processados": 0, "mensagem": "Nenhuma mensagem pendente."}

    # Agrupar por chat_id
    grupos: dict[str, list[dict]] = defaultdict(list)
    for msg in msgs_response.data:
        grupos[msg["chat_id"]].append(msg)

    # Processar em background
    background_tasks.add_task(
        _processar_cron_empresa,
        empresa_id=empresa_id,
        grupos=dict(grupos),
    )

    return {
        "status": "processando",
        "chats_enfileirados": len(grupos),
        "mensagens_total": len(msgs_response.data),
    }
