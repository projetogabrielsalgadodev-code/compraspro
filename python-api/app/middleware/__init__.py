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
import sys
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.db.supabase_client import get_settings

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)


def _decode_supabase_jwt(token: str) -> dict:
    """
    Decodifica um JWT do Supabase Auth COM verificação de assinatura.

    A JWT secret deve estar configurada na variável SUPABASE_JWT_SECRET.
    Se não estiver configurada, a aplicação bloqueia a requisição em vez
    de decodificar sem verificação (que permitiria forjamento de tokens).
    """
    settings = get_settings()

    jwt_secret = getattr(settings, "supabase_jwt_secret", None)

    if not jwt_secret:
        logger.error(
            "SUPABASE_JWT_SECRET não configurada. "
            "Todas as requisições autenticadas serão rejeitadas. "
            "Configure a variável no .env com o JWT secret do projeto Supabase."
        )
        raise HTTPException(
            status_code=503,
            detail="Serviço de autenticação indisponível. SUPABASE_JWT_SECRET não configurada.",
        )

    try:
        # Log do header para diagnóstico
        header = jwt.get_unverified_header(token)
        token_alg = header.get("alg", "unknown")
        logger.info(f"JWT header: alg={token_alg}, typ={header.get('typ')}")

        payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado.")
    except jwt.InvalidTokenError as e:
        logger.error(f"JWT decode error: {str(e)} | alg_header={token_alg} | secret_len={len(jwt_secret)}")
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

    SEGURANÇA: empresa_id é extraído EXCLUSIVAMENTE do JWT verificado.
    Não aceita empresa_id do body da requisição (eliminado em abril/2026).
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=401,
            detail="Token de autenticação não fornecido. Envie um Bearer token no header Authorization.",
        )

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
        # Armazenar no request.state para acesso em outros middlewares/deps
        request.state.empresa_id = str(empresa_id)
        request.state.user_id = payload.get("sub")
        return str(empresa_id)

    raise HTTPException(
        status_code=403,
        detail="empresa_id não encontrado nos metadados do JWT. Configure app_metadata.empresa_id no Supabase Auth.",
    )


async def get_current_user_id(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> str:
    """
    Dependency do FastAPI que extrai o user_id (sub) do JWT.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=401,
            detail="Token de autenticação não fornecido.",
        )

    token = credentials.credentials
    payload = _decode_supabase_jwt(token)

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID não encontrado no JWT.")

    return str(user_id)
