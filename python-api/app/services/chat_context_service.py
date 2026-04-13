from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from app.db.supabase_client import get_settings


def _default_context_path() -> Path:
    return Path(__file__).resolve().parents[3] / "consolidacao_chats_1_a_5.md"


@lru_cache
def carregar_contexto_analise() -> str:
    settings = get_settings()
    configured_path = settings.oferta_chat_history_path
    file_path = Path(configured_path) if configured_path else _default_context_path()

    try:
        return file_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return ""
