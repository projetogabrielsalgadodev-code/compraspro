from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.db.supabase_client import get_supabase_client
from app.models.schemas import ConfiguracaoEmpresaResponse, ConfiguracaoEmpresaUpdate
from app.services.persistencia_service import buscar_configuracao_empresa, upsert_configuracao_empresa


router = APIRouter()


@router.get("/empresa", response_model=ConfiguracaoEmpresaResponse)
def obter_configuracao_empresa(empresa_id: str = Query(...)) -> ConfiguracaoEmpresaResponse:
    client = get_supabase_client()
    if client is None:
        raise HTTPException(status_code=503, detail="Supabase indisponivel.")

    configuracao = buscar_configuracao_empresa(client, empresa_id)
    if configuracao is None:
        raise HTTPException(status_code=404, detail="Configuracao da empresa nao encontrada.")
    return configuracao


@router.put("/empresa", response_model=ConfiguracaoEmpresaResponse)
def salvar_configuracao_empresa(payload: ConfiguracaoEmpresaUpdate) -> ConfiguracaoEmpresaResponse:
    client = get_supabase_client()
    if client is None:
        raise HTTPException(status_code=503, detail="Supabase indisponivel.")

    return upsert_configuracao_empresa(client, payload)
