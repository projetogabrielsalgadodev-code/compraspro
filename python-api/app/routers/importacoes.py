from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile

from app.db.supabase_client import get_supabase_client
from app.middleware import get_current_empresa_id
from app.services.importacao_service import parse_entradas, parse_produtos
from app.services.persistencia_service import inserir_historico, upsert_produtos


router = APIRouter()


@router.post("/sugcompra")
async def importar_sugcompra(
    arquivo: UploadFile = File(...),
    empresa_id: str = Depends(get_current_empresa_id),
) -> dict[str, object]:
    """Importa produtos da sugestão de compra.

    SEGURANÇA: empresa_id é extraído do JWT autenticado via dependency injection.
    """
    conteudo = await arquivo.read()
    itens = parse_produtos(arquivo.filename or "arquivo.csv", conteudo)
    client = get_supabase_client()
    persistidos = upsert_produtos(client, empresa_id, itens) if client else 0
    return {
        "arquivo": arquivo.filename,
        "total_itens": len(itens),
        "persistidos": persistidos,
        "amostra": [item.model_dump() for item in itens[:5]],
    }


@router.post("/entradas")
async def importar_entradas(
    arquivo: UploadFile = File(...),
    empresa_id: str = Depends(get_current_empresa_id),
) -> dict[str, object]:
    """Importa histórico de entradas.

    SEGURANÇA: empresa_id é extraído do JWT autenticado via dependency injection.
    """
    conteudo = await arquivo.read()
    itens = parse_entradas(arquivo.filename or "arquivo.xlsx", conteudo)
    client = get_supabase_client()
    persistidos = inserir_historico(client, empresa_id, itens) if client else 0
    return {
        "arquivo": arquivo.filename,
        "total_itens": len(itens),
        "persistidos": persistidos,
        "amostra": [item.model_dump() for item in itens[:5]],
    }
