from __future__ import annotations

from fastapi import APIRouter


router = APIRouter()


@router.get("")
def listar_produtos() -> dict[str, list[dict[str, object]]]:
    return {
        "items": [
            {"ean": "7891234567890", "descricao": "Paracetamol 500mg - 20 comprimidos", "estoque": 34},
            {"ean": "7894561234567", "descricao": "Dipirona Sodica 500mg/ml - 10ml", "estoque": 180},
        ]
    }
