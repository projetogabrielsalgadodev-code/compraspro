"""
Módulo de autenticação JWT para FastAPI.

Exporta get_current_empresa_id como dependency.
"""
from app.middleware.__init__ import get_current_empresa_id

__all__ = ["get_current_empresa_id"]
