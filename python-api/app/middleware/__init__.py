"""
Middleware de autenticação — Extrai empresa_id via chave interna ou JWT.

FLUXO PRINCIPAL (recomendado):
  O Next.js valida a sessão do usuário (Supabase Auth SSR) e repassa
  empresa_id + usuario_id nos headers X-Empresa-Id e X-User-Id,
  autenticando com X-Internal-Key (SUPABASE_SERVICE_ROLE_KEY).

FLUXO LEGADO (fallback):
  Bearer JWT do Supabase Auth → extrai empresa_id de app_metadata.

Uso nos routers:
    from app.middleware import get_current_empresa_id

    @router.post("/rota-protegida")
    async def rota(empresa_id: str = Depends(get_current_empresa_id)):
        ...
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.db.supabase_client import get_settings

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)


def _verify_internal_key(key: str) -> bool:
    """
    Valida a chave interna (service-to-service).
    Usa SUPABASE_SERVICE_ROLE_KEY como shared secret.
    """
    settings = get_settings()
    expected = getattr(settings, "supabase_service_role_key", None)
    if not expected:
        logger.error("SUPABASE_SERVICE_ROLE_KEY não configurada.")
        return False
    return key == expected


def _decode_supabase_jwt(token: str) -> dict:
    """
    Decodifica um JWT do Supabase Auth COM verificação de assinatura.
    Fallback para quando não há chave interna.
    """
    import jwt as pyjwt

    settings = get_settings()
    jwt_secret = getattr(settings, "supabase_jwt_secret", None)

    if not jwt_secret:
        raise HTTPException(
            status_code=503,
            detail="SUPABASE_JWT_SECRET não configurada.",
        )

    try:
        payload = pyjwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return payload
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado.")
    except pyjwt.InvalidTokenError as e:
        logger.error(f"JWT decode error: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Token inválido: {str(e)}")


async def get_current_empresa_id(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    """
    Dependency do FastAPI que extrai empresa_id.

    Caminho 1: X-Internal-Key + X-Empresa-Id headers (Next.js → FastAPI)
    Caminho 2: Bearer JWT do Supabase Auth (chamadas diretas)
    """
    # ── Caminho 1: Chave interna (service-to-service) ────────────────────
    internal_key = request.headers.get("X-Internal-Key")
    if internal_key:
        if not _verify_internal_key(internal_key):
            raise HTTPException(status_code=401, detail="Chave interna inválida.")

        empresa_id = request.headers.get("X-Empresa-Id")
        usuario_id = request.headers.get("X-User-Id")

        if not empresa_id:
            raise HTTPException(
                status_code=400,
                detail="X-Empresa-Id header é obrigatório com autenticação interna.",
            )

        request.state.empresa_id = str(empresa_id)
        request.state.user_id = usuario_id
        logger.info(f"Auth via internal key: empresa_id={empresa_id}")
        return str(empresa_id)

    # ── Caminho 2: Bearer JWT (fallback) ─────────────────────────────────
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=401,
            detail="Autenticação necessária. Envie X-Internal-Key ou Bearer token.",
        )

    token = credentials.credentials
    payload = _decode_supabase_jwt(token)

    app_metadata = payload.get("app_metadata", {})
    user_metadata = payload.get("user_metadata", {})

    empresa_id = (
        app_metadata.get("empresa_id")
        or user_metadata.get("empresa_id")
        or payload.get("empresa_id")
    )

    if empresa_id:
        request.state.empresa_id = str(empresa_id)
        request.state.user_id = payload.get("sub")
        return str(empresa_id)

    raise HTTPException(
        status_code=403,
        detail="empresa_id não encontrado nos metadados do JWT.",
    )


async def get_current_user_id(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    """
    Dependency do FastAPI que extrai o user_id.
    Suporta autenticação interna (X-Internal-Key) e JWT.
    """
    # Se já resolvido pelo get_current_empresa_id
    if hasattr(request.state, "user_id") and request.state.user_id:
        return str(request.state.user_id)

    # Chave interna
    internal_key = request.headers.get("X-Internal-Key")
    if internal_key:
        if not _verify_internal_key(internal_key):
            raise HTTPException(status_code=401, detail="Chave interna inválida.")
        user_id = request.headers.get("X-User-Id")
        if user_id:
            return str(user_id)
        raise HTTPException(status_code=400, detail="X-User-Id header obrigatório.")

    # JWT fallback
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Autenticação necessária.")

    payload = _decode_supabase_jwt(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID não encontrado no JWT.")
    return str(user_id)
