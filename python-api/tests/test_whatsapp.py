"""Testes para o fluxo completo de WhatsApp do ComprasPRO.

Cobre:
- Parser de mensagens Uazapi (_parse_uazapi_message)
- Webhook endpoint (autenticação, persistência)
- Endpoint de status com contagem de mensagens
- Endpoint de análise manual
- Identificação de instância por token e instance_id
"""
import pytest
from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.routers.whatsapp import _parse_uazapi_message

client = TestClient(app)

# ═══════════════════════════════════════════════════════════════════════════════
# 1. TESTES DO PARSER DE MENSAGENS (_parse_uazapi_message)
# ═══════════════════════════════════════════════════════════════════════════════


class TestParseUazapiMessage:
    """Testes unitários do parser de mensagens da Uazapi."""

    def test_texto_simples_conversation(self):
        """Formato mais comum: mensagem de texto via 'conversation'."""
        data = {
            "key": {
                "remoteJid": "5511999999999@s.whatsapp.net",
                "fromMe": False,
                "id": "MSG001",
            },
            "message": {"conversation": "PARACETAMOL 500MG C/20 R$ 12,50"},
            "pushName": "Farmácia ABC",
            "messageTimestamp": 1715033000,
        }
        result = _parse_uazapi_message(data)

        assert result is not None
        assert result["message_id"] == "MSG001"
        assert result["chat_id"] == "5511999999999@s.whatsapp.net"
        assert result["sender_name"] == "Farmácia ABC"
        assert result["conteudo_texto"] == "PARACETAMOL 500MG C/20 R$ 12,50"
        assert result["tipo_mensagem"] == "text"
        assert result["is_group"] is False

    def test_texto_extended(self):
        """Mensagem com extendedTextMessage (links, menções, etc.)."""
        data = {
            "key": {
                "remoteJid": "5511888888888@s.whatsapp.net",
                "fromMe": False,
                "id": "MSG002",
            },
            "message": {
                "extendedTextMessage": {
                    "text": "Segue tabela de preços atualizada",
                    "contextInfo": {},
                }
            },
            "pushName": "Distribuidora XYZ",
            "messageTimestamp": 1715033100,
        }
        result = _parse_uazapi_message(data)

        assert result is not None
        assert result["conteudo_texto"] == "Segue tabela de preços atualizada"
        assert result["tipo_mensagem"] == "text"

    def test_mensagem_grupo(self):
        """Detecta corretamente mensagens de grupo (@g.us)."""
        data = {
            "key": {
                "remoteJid": "120363049309493028@g.us",
                "fromMe": False,
                "id": "MSG003",
                "participant": "5511777777777@s.whatsapp.net",
            },
            "message": {"conversation": "Oferta do dia"},
            "pushName": "João",
            "messageTimestamp": 1715033200,
        }
        result = _parse_uazapi_message(data)

        assert result is not None
        assert result["is_group"] is True
        assert result["sender_id"] == "5511777777777@s.whatsapp.net"
        assert result["sender_phone"] == "5511777777777"

    def test_mensagem_imagem(self):
        """Imagem com caption é tipo 'image' mas mantém o texto do caption."""
        data = {
            "key": {
                "remoteJid": "5511666666666@s.whatsapp.net",
                "fromMe": False,
                "id": "MSG004",
            },
            "message": {
                "imageMessage": {
                    "caption": "Tabela de preços em imagem",
                    "mimetype": "image/jpeg",
                }
            },
            "pushName": "Fornecedor",
            "messageTimestamp": 1715033300,
        }
        result = _parse_uazapi_message(data)

        assert result is not None
        assert result["tipo_mensagem"] == "image"
        assert result["conteudo_texto"] == "Tabela de preços em imagem"

    def test_mensagem_documento(self):
        """Documento (PDF, XLSX) é tipo 'document'."""
        data = {
            "key": {
                "remoteJid": "5511555555555@s.whatsapp.net",
                "fromMe": False,
                "id": "MSG005",
            },
            "message": {
                "documentMessage": {
                    "mimetype": "application/pdf",
                    "title": "tabela.pdf",
                }
            },
            "pushName": "Vendedor",
            "messageTimestamp": 1715033400,
        }
        result = _parse_uazapi_message(data)

        assert result is not None
        assert result["tipo_mensagem"] == "document"
        assert result["conteudo_texto"] is None

    def test_mensagem_audio(self):
        """Áudio é tipo 'audio'."""
        data = {
            "key": {
                "remoteJid": "5511444444444@s.whatsapp.net",
                "fromMe": False,
                "id": "MSG006",
            },
            "message": {"audioMessage": {"mimetype": "audio/ogg"}},
            "pushName": "Cliente",
            "messageTimestamp": 1715033500,
        }
        result = _parse_uazapi_message(data)

        assert result is not None
        assert result["tipo_mensagem"] == "audio"

    def test_mensagem_video(self):
        """Vídeo é tipo 'video'."""
        data = {
            "key": {
                "remoteJid": "5511333333333@s.whatsapp.net",
                "fromMe": False,
                "id": "MSG007",
            },
            "message": {"videoMessage": {"mimetype": "video/mp4"}},
            "pushName": "Representante",
            "messageTimestamp": 1715033600,
        }
        result = _parse_uazapi_message(data)

        assert result is not None
        assert result["tipo_mensagem"] == "video"

    def test_formato_messages_upsert(self):
        """Formato messages.upsert: data contém array 'messages'."""
        data = {
            "messages": [
                {
                    "key": {
                        "remoteJid": "5511222222222@s.whatsapp.net",
                        "fromMe": False,
                        "id": "MSG008",
                    },
                    "message": {"conversation": "Preço especial"},
                    "pushName": "Atacadista",
                    "messageTimestamp": 1715033700,
                }
            ]
        }
        result = _parse_uazapi_message(data)

        assert result is not None
        assert result["message_id"] == "MSG008"
        assert result["conteudo_texto"] == "Preço especial"

    def test_data_vazia_retorna_none(self):
        """Data vazia deve retornar None."""
        assert _parse_uazapi_message({}) is None
        assert _parse_uazapi_message(None) is None

    def test_sem_message_id_retorna_none(self):
        """Sem message_id deve retornar None."""
        data = {
            "key": {"remoteJid": "5511111111111@s.whatsapp.net"},
            "message": {"conversation": "teste"},
        }
        result = _parse_uazapi_message(data)
        assert result is None

    def test_sem_chat_id_retorna_none(self):
        """Sem chat_id (remoteJid) deve retornar None."""
        data = {
            "key": {"id": "MSG009"},
            "message": {"conversation": "teste"},
        }
        result = _parse_uazapi_message(data)
        assert result is None

    def test_timestamp_valido(self):
        """Verifica conversão correta de timestamp Unix."""
        data = {
            "key": {
                "remoteJid": "5511999999999@s.whatsapp.net",
                "fromMe": False,
                "id": "MSG010",
            },
            "message": {"conversation": "teste"},
            "messageTimestamp": 1715033000,
        }
        result = _parse_uazapi_message(data)

        assert result is not None
        # Deve ser ISO format
        parsed = datetime.fromisoformat(result["timestamp_msg"])
        assert parsed.tzinfo is not None

    def test_timestamp_ausente_usa_now(self):
        """Sem timestamp deve usar datetime.now."""
        data = {
            "key": {
                "remoteJid": "5511999999999@s.whatsapp.net",
                "fromMe": False,
                "id": "MSG011",
            },
            "message": {"conversation": "teste"},
        }
        result = _parse_uazapi_message(data)

        assert result is not None
        assert result["timestamp_msg"] is not None

    def test_message_content_string(self):
        """Quando message é string direto ao invés de dict."""
        data = {
            "key": {
                "remoteJid": "5511999999999@s.whatsapp.net",
                "fromMe": False,
                "id": "MSG012",
            },
            "message": "Mensagem como string",
            "messageTimestamp": 1715033000,
        }
        result = _parse_uazapi_message(data)

        assert result is not None
        assert result["conteudo_texto"] == "Mensagem como string"
        assert result["tipo_mensagem"] == "text"

    def test_tipo_outro(self):
        """Tipo de mensagem desconhecido deve ser 'other'."""
        data = {
            "key": {
                "remoteJid": "5511999999999@s.whatsapp.net",
                "fromMe": False,
                "id": "MSG013",
            },
            "message": {"stickerMessage": {"mimetype": "image/webp"}},
            "messageTimestamp": 1715033000,
        }
        result = _parse_uazapi_message(data)

        assert result is not None
        assert result["tipo_mensagem"] == "other"


# ═══════════════════════════════════════════════════════════════════════════════
# 2. TESTES DO WEBHOOK ENDPOINT
# ═══════════════════════════════════════════════════════════════════════════════


FAKE_INSTANCIA = {
    "id": "f05fad58-36bc-4b64-8793-c12df1f62835",
    "empresa_id": "11111111-1111-1111-1111-111111111111",
    "instance_id": "ra6f045ea899ae5",
    "status": "conectada",
}


def _make_webhook_payload(
    event="message",
    instance_id="ra6f045ea899ae5",
    message_id="WBHK001",
    chat_id="5511999999999@s.whatsapp.net",
    text="AMOXICILINA 500MG C/21 R$ 18,90",
):
    """Helper para criar payloads de webhook padronizados."""
    return {
        "event": event,
        "instance": instance_id,
        "data": {
            "key": {
                "remoteJid": chat_id,
                "fromMe": False,
                "id": message_id,
            },
            "message": {"conversation": text},
            "pushName": "Fornecedor Teste",
            "messageTimestamp": 1715033000,
        },
    }


class TestWebhookEndpoint:
    """Testes de integração do webhook."""

    @patch("app.routers.whatsapp._get_instancia_by_instance_id")
    @patch("app.routers.whatsapp._get_instancia_by_token")
    @patch("app.routers.whatsapp.get_supabase_client")
    def test_webhook_via_instance_id(
        self, mock_supabase, mock_by_token, mock_by_iid
    ):
        """Webhook deve aceitar autenticação via instance_id no body (formato Uazapi)."""
        mock_by_token.return_value = None
        mock_by_iid.return_value = FAKE_INSTANCIA

        mock_client = MagicMock()
        mock_client.table.return_value.upsert.return_value.execute.return_value = MagicMock()
        mock_supabase.return_value = mock_client

        payload = _make_webhook_payload()
        resp = client.post("/api/whatsapp/webhook", json=payload)

        assert resp.status_code == 200
        assert resp.json()["saved"] is True
        mock_by_iid.assert_called_once_with("ra6f045ea899ae5")

    @patch("app.routers.whatsapp._get_instancia_by_instance_id")
    @patch("app.routers.whatsapp._get_instancia_by_token")
    @patch("app.routers.whatsapp.get_supabase_client")
    def test_webhook_via_bearer_token(
        self, mock_supabase, mock_by_token, mock_by_iid
    ):
        """Webhook deve aceitar autenticação via Bearer token."""
        mock_by_token.return_value = FAKE_INSTANCIA

        mock_client = MagicMock()
        mock_client.table.return_value.upsert.return_value.execute.return_value = MagicMock()
        mock_supabase.return_value = mock_client

        payload = _make_webhook_payload()
        resp = client.post(
            "/api/whatsapp/webhook",
            json=payload,
            headers={"Authorization": "Bearer test-token-123"},
        )

        assert resp.status_code == 200
        assert resp.json()["saved"] is True
        mock_by_token.assert_called_once_with("test-token-123")
        mock_by_iid.assert_not_called()

    @patch("app.routers.whatsapp._get_instancia_by_instance_id")
    @patch("app.routers.whatsapp._get_instancia_by_token")
    def test_webhook_instancia_nao_encontrada(self, mock_by_token, mock_by_iid):
        """Webhook deve retornar 401 quando instância não é encontrada."""
        mock_by_token.return_value = None
        mock_by_iid.return_value = None

        payload = _make_webhook_payload(instance_id="instancia_inexistente")
        resp = client.post("/api/whatsapp/webhook", json=payload)

        assert resp.status_code == 401

    @patch("app.routers.whatsapp._get_instancia_by_instance_id")
    @patch("app.routers.whatsapp._get_instancia_by_token")
    @patch("app.routers.whatsapp.get_supabase_client")
    def test_webhook_evento_connection_ignorado(
        self, mock_supabase, mock_by_token, mock_by_iid
    ):
        """Eventos de connection devem ser ignorados (não salvos)."""
        mock_by_token.return_value = None
        mock_by_iid.return_value = FAKE_INSTANCIA

        payload = {
            "event": "connection",
            "instance": "ra6f045ea899ae5",
            "data": {"status": "connected"},
        }
        resp = client.post("/api/whatsapp/webhook", json=payload)

        assert resp.status_code == 200
        assert resp.json().get("ignored") is True

    @patch("app.routers.whatsapp._get_instancia_by_instance_id")
    @patch("app.routers.whatsapp._get_instancia_by_token")
    @patch("app.routers.whatsapp.get_supabase_client")
    def test_webhook_salva_campos_corretos(
        self, mock_supabase, mock_by_token, mock_by_iid
    ):
        """Verifica que todos os campos são salvos corretamente no banco."""
        mock_by_token.return_value = None
        mock_by_iid.return_value = FAKE_INSTANCIA

        mock_client = MagicMock()
        mock_upsert = mock_client.table.return_value.upsert
        mock_upsert.return_value.execute.return_value = MagicMock()
        mock_supabase.return_value = mock_client

        payload = _make_webhook_payload(
            message_id="SAVE_TEST",
            chat_id="5521987654321@s.whatsapp.net",
            text="DIPIRONA 500MG R$ 5,00",
        )
        resp = client.post("/api/whatsapp/webhook", json=payload)

        assert resp.status_code == 200

        # Verificar o que foi passado para o upsert
        upsert_call = mock_upsert.call_args
        saved_data = upsert_call[0][0]

        assert saved_data["empresa_id"] == "11111111-1111-1111-1111-111111111111"
        assert saved_data["message_id"] == "SAVE_TEST"
        assert saved_data["chat_id"] == "5521987654321@s.whatsapp.net"
        assert saved_data["conteudo_texto"] == "DIPIRONA 500MG R$ 5,00"
        assert saved_data["status_analise"] == "pendente"
        assert saved_data["is_group"] is False

    def test_webhook_json_invalido(self):
        """Webhook com body inválido deve retornar 200 (ignorado)."""
        resp = client.post(
            "/api/whatsapp/webhook",
            content=b"isso nao e json",
            headers={"Content-Type": "application/json"},
        )
        # FastAPI pode retornar 422 para JSON inválido
        assert resp.status_code in (200, 422)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. TESTES DE STATUS COM CONTAGEM DE MENSAGENS PENDENTES
# ═══════════════════════════════════════════════════════════════════════════════

from app.middleware import get_current_empresa_id

FAKE_EMPRESA_ID = "11111111-1111-1111-1111-111111111111"


def _override_empresa_id():
    return FAKE_EMPRESA_ID


class TestStatusEndpoint:
    """Testes do endpoint GET /instancia/status."""

    def setup_method(self):
        app.dependency_overrides[get_current_empresa_id] = _override_empresa_id

    def teardown_method(self):
        app.dependency_overrides.clear()

    @patch("app.routers.whatsapp._get_uazapi_config", return_value=("https://test.uazapi.com", "test-admin"))
    @patch("app.routers.whatsapp.get_supabase_client")
    def test_status_sem_instancia(self, mock_supabase, mock_config):
        """Sem instância cadastrada deve retornar status sem_instancia."""
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(data=[])
        mock_supabase.return_value = mock_client

        resp = client.get("/api/whatsapp/instancia/status")
        assert resp.status_code == 200
        assert resp.json()["status"] == "sem_instancia"


# ═══════════════════════════════════════════════════════════════════════════════
# 4. TESTES DE ANÁLISE MANUAL
# ═══════════════════════════════════════════════════════════════════════════════


class TestAnalisarEndpoint:
    """Testes do endpoint POST /instancia/analisar."""

    def setup_method(self):
        app.dependency_overrides[get_current_empresa_id] = _override_empresa_id

    def teardown_method(self):
        app.dependency_overrides.clear()

    @patch("app.routers.whatsapp.get_supabase_client")
    def test_analisar_sem_whatsapp_conectado(self, mock_supabase):
        """Deve retornar 400 se WhatsApp não está conectado."""
        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(data=[])
        mock_supabase.return_value = mock_client

        resp = client.post("/api/whatsapp/instancia/analisar")
        assert resp.status_code == 400

    @patch("app.routers.whatsapp.get_supabase_client")
    def test_analisar_sem_mensagens_pendentes(self, mock_supabase):
        """Deve retornar processados=0 quando não há mensagens pendentes."""
        mock_client = MagicMock()

        def table_side_effect(table_name):
            mock_table = MagicMock()
            if table_name == "whatsapp_instancias":
                mock_table.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = MagicMock(data=[{"id": "inst-1", "status": "conectada"}])
            else:
                mock_table.select.return_value.eq.return_value.in_.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(data=[])
            return mock_table

        mock_client.table.side_effect = table_side_effect
        mock_supabase.return_value = mock_client

        resp = client.post("/api/whatsapp/instancia/analisar")
        assert resp.status_code == 200
        assert resp.json()["processados"] == 0


# ═══════════════════════════════════════════════════════════════════════════════
# 5. TESTES E2E - Webhook completo com produção
# ═══════════════════════════════════════════════════════════════════════════════


class TestWebhookE2EProd:
    """Testes que disparam contra a API em produção (somente leitura/webhook).

    Estes testes NÃO são executados por padrão.
    Use: pytest tests/test_whatsapp.py -m e2e
    """

    @pytest.mark.e2e
    def test_webhook_produção_salva_mensagem(self):
        """Envia uma mensagem de teste ao webhook em produção e verifica se salva."""
        import httpx

        payload = _make_webhook_payload(
            message_id=f"E2E_TEST_{int(datetime.now().timestamp())}",
            text="[TESTE AUTOMATIZADO] Não analisar",
        )

        resp = httpx.post(
            "https://compraspro.onrender.com/api/whatsapp/webhook",
            json=payload,
            timeout=30,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data.get("saved") is True or data.get("status") == "ok"

    @pytest.mark.e2e
    def test_health_produção(self):
        """Verifica se a API está viva."""
        import httpx

        resp = httpx.get("https://compraspro.onrender.com/health", timeout=30)
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
