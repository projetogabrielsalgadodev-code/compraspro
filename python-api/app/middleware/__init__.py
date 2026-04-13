"""
Middleware de autenticação — Extrai empresa_id de JWT Supabase.

Uso nos routers:
    from app.middleware.auth import get_current_empresa_id

    @router.post("/rota-protegida")
    async def rota(empresa_id: str = Depends(get_current_empresa_id)):
        ...
"""
from __future__ import annotations

import logging
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.db.supabase_client import get_settings

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)


def _decode_supabase_jwt(token: str) -> dict:
    """
    Decodifica um JWT do Supabase Auth sem verificar assinatura
    (a chave pública do Supabase não é disponível no service_role_key).

    Para produção ativa, usar a JWT secret do Supabase project settings.
    """
    settings = get_settings()

    # Supabase JWT secret = project JWT secret (disponível no dashboard)
    # Fallback: decodificar sem verificação (desenvolvimento)
    jwt_secret = getattr(settings, "supabase_jwt_secret", None)

    try:
        if jwt_secret:
            payload = jwt.decode(
                token,
                jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
        else:
            # Desenvolvimento: decodificar sem verificação de assinatura
            logger.warning("JWT decodificado sem verificação de assinatura (dev mode).")
            payload = jwt.decode(
                token,
                options={"verify_signature": False},
                algorithms=["HS256"],
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado.")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Token inválido: {str(e)}")


async def get_current_empresa_id(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    """
    Dependency do FastAPI que extrai empresa_id do JWT.

    Busca o token Bearer no header Authorization.
    Extrai empresa_id do campo `app_metadata.empresa_id` ou `user_metadata.empresa_id`
    no JWT do Supabase Auth.

    Fallback temporário: aceita empresa_id no body (para compatibilidade durante migração).
    """
    if credentials and credentials.credentials:
        token = credentials.credentials
        payload = _decode_supabase_jwt(token)

        # Tentar extrair empresa_id dos metadados do Supabase
        app_metadata = payload.get("app_metadata", {})
        user_metadata = payload.get("user_metadata", {})

        empresa_id = (
            app_metadata.get("empresa_id")
            or user_metadata.get("empresa_id")
            or payload.get("empresa_id")
        )

        if empresa_id:
            return str(empresa_id)

        raise HTTPException(
            status_code=403,
            detail="empresa_id não encontrado nos metadados do JWT. Configure app_metadata.empresa_id no Supabase Auth.",
        )

    # Fallback: extrair do body (compatibilidade temporária)
    # Isso será removido quando o frontend enviar JWT em todas as requisições
    try:
        body = await request.json()
        empresa_id = body.get("empresa_id")
        if empresa_id:
            logger.warning("empresa_id extraído do body (fallback). Migre para JWT.")
            return str(empresa_id)
    except Exception:
        pass

    raise HTTPException(
        status_code=401,
        detail="Token de autenticação não fornecido. Envie um Bearer token no header Authorization.",
    )
