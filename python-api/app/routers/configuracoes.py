"""
Router de Configurações — Endpoints para configuração de empresa.

SEGURANÇA: empresa_id é extraído EXCLUSIVAMENTE do JWT via dependency injection.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.db.supabase_client import get_supabase_client
from app.middleware import get_current_empresa_id
from app.models.schemas import ConfiguracaoEmpresaResponse, ConfiguracaoEmpresaUpdate
from app.services.persistencia_service import buscar_configuracao_empresa, upsert_configuracao_empresa


router = APIRouter()


@router.get("/empresa", response_model=ConfiguracaoEmpresaResponse)
def obter_configuracao_empresa(
    empresa_id: str = Depends(get_current_empresa_id),
) -> ConfiguracaoEmpresaResponse:
    """Busca a configuração da empresa do usuário autenticado.

    SEGURANÇA: empresa_id extraído do JWT — não aceita query param.
    """
    client = get_supabase_client()
    if client is None:
        raise HTTPException(status_code=503, detail="Supabase indisponivel.")

    configuracao = buscar_configuracao_empresa(client, empresa_id)
    if configuracao is None:
        raise HTTPException(status_code=404, detail="Configuracao da empresa nao encontrada.")
    return configuracao


@router.put("/empresa", response_model=ConfiguracaoEmpresaResponse)
def salvar_configuracao_empresa(
    payload: ConfiguracaoEmpresaUpdate,
    empresa_id: str = Depends(get_current_empresa_id),
) -> ConfiguracaoEmpresaResponse:
    """Salva a configuração da empresa do usuário autenticado.

    SEGURANÇA: sobrescreve empresa_id do payload com o valor do JWT para evitar
    que um usuário altere configurações de outra empresa.
    """
    client = get_supabase_client()
    if client is None:
        raise HTTPException(status_code=503, detail="Supabase indisponivel.")

    # Forçar empresa_id do JWT (ignorar o do payload)
    payload.empresa_id = empresa_id

    return upsert_configuracao_empresa(client, payload)
