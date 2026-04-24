from __future__ import annotations

import csv
import io
import logging
from uuid import uuid4

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException

from app.middleware import get_current_empresa_id
from app.db.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("")
def listar_produtos() -> dict[str, list[dict[str, object]]]:
    return {
        "items": [
            {"ean": "7891234567890", "descricao": "Paracetamol 500mg - 20 comprimidos", "estoque": 34},
            {"ean": "7894561234567", "descricao": "Dipirona Sodica 500mg/ml - 10ml", "estoque": 180},
        ]
    }


# ─── Colunas esperadas no CSV ────────────────────────────────────────────────
COLUNAS_OBRIGATORIAS = {"ean", "descricao"}
COLUNAS_OPCIONAIS = {
    "fabricante", "principio_ativo", "estoque", "demanda_mes",
    "custo_medio", "preco_venda", "curva_abc", "grupo",
}
TODAS_COLUNAS = COLUNAS_OBRIGATORIAS | COLUNAS_OPCIONAIS

# Campos numéricos para conversão
CAMPOS_INTEIROS = {"estoque"}
CAMPOS_DECIMAIS = {"demanda_mes", "custo_medio", "preco_venda"}


def _parse_int(val: str) -> int | None:
    """Converte string para int, retorna None se vazio ou inválido."""
    val = val.strip()
    if not val:
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def _parse_float(val: str) -> float | None:
    """Converte string para float, aceita vírgula como separador decimal."""
    val = val.strip().replace(",", ".")
    if not val:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


@router.post("/importar-csv")
async def importar_produtos_csv(
    empresa_id: str = Depends(get_current_empresa_id),
    arquivo: UploadFile = File(...),
):
    """
    Importar produtos em massa via arquivo CSV.

    Colunas obrigatórias: ean, descricao
    Colunas opcionais: fabricante, principio_ativo, estoque, demanda_mes,
                       custo_medio, preco_venda, curva_abc, grupo

    Faz upsert baseado em (ean + empresa_id).
    """
    if not arquivo.filename or not arquivo.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Apenas arquivos .csv são aceitos.")

    try:
        file_bytes = await arquivo.read()
        # Tentar decodificar como UTF-8, fallback para latin-1
        try:
            content = file_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            content = file_bytes.decode("latin-1")

        reader = csv.DictReader(io.StringIO(content), delimiter=None)

        # Detectar delimitador
        sniffer = csv.Sniffer()
        try:
            dialect = sniffer.sniff(content[:2048])
            reader = csv.DictReader(io.StringIO(content), delimiter=dialect.delimiter)
        except csv.Error:
            reader = csv.DictReader(io.StringIO(content))

        if not reader.fieldnames:
            raise HTTPException(status_code=400, detail="Arquivo CSV vazio ou sem cabeçalho.")

        # Normalizar nomes de colunas (lowercase, strip)
        normalized_fields = {f.strip().lower(): f for f in reader.fieldnames}

        # Verificar colunas obrigatórias
        missing = COLUNAS_OBRIGATORIAS - set(normalized_fields.keys())
        if missing:
            raise HTTPException(
                status_code=400,
                detail=f"Colunas obrigatórias ausentes: {', '.join(sorted(missing))}. "
                       f"Colunas encontradas: {', '.join(sorted(normalized_fields.keys()))}",
            )

        client = get_supabase_client()
        if not client:
            raise HTTPException(status_code=500, detail="Erro de conexão com o banco de dados.")

        # Buscar EANs existentes da empresa para decidir insert vs update
        existing_resp = client.table("produtos").select("id, ean").eq("empresa_id", empresa_id).execute()
        existing_map = {row["ean"]: row["id"] for row in (existing_resp.data or [])}

        inseridos = 0
        atualizados = 0
        erros: list[dict[str, str]] = []
        linhas_processadas = 0

        rows = list(reader)
        if len(rows) == 0:
            raise HTTPException(status_code=400, detail="Nenhuma linha de dados encontrada no CSV.")

        for i, row in enumerate(rows, start=2):  # start=2 because line 1 is header
            linhas_processadas += 1

            # Normalizar chaves
            norm_row = {k.strip().lower(): v.strip() for k, v in row.items() if k}

            ean = norm_row.get("ean", "").strip()
            descricao = norm_row.get("descricao", "").strip()

            if not ean:
                erros.append({"linha": str(i), "erro": "EAN vazio"})
                continue
            if not descricao:
                erros.append({"linha": str(i), "erro": f"Descrição vazia para EAN {ean}"})
                continue

            # Montar registro
            record: dict[str, object] = {
                "empresa_id": empresa_id,
                "ean": ean,
                "descricao": descricao,
            }

            # Campos opcionais de texto
            for campo in ("fabricante", "principio_ativo", "curva_abc", "grupo"):
                val = norm_row.get(campo, "").strip()
                if val:
                    record[campo] = val

            # Campos inteiros
            for campo in CAMPOS_INTEIROS:
                val = norm_row.get(campo, "")
                parsed = _parse_int(val)
                if parsed is not None:
                    record[campo] = parsed

            # Campos decimais
            for campo in CAMPOS_DECIMAIS:
                val = norm_row.get(campo, "")
                parsed = _parse_float(val)
                if parsed is not None:
                    record[campo] = parsed

            try:
                if ean in existing_map:
                    # Update
                    product_id = existing_map[ean]
                    update_data = {k: v for k, v in record.items() if k not in ("empresa_id", "ean")}
                    client.table("produtos").update(update_data).eq("id", product_id).execute()
                    atualizados += 1
                else:
                    # Insert
                    record["id"] = str(uuid4())
                    client.table("produtos").insert(record).execute()
                    existing_map[ean] = record["id"]  # Track for duplicates within the same CSV
                    inseridos += 1
            except Exception as e:
                erros.append({"linha": str(i), "erro": f"Erro ao salvar EAN {ean}: {str(e)[:100]}"})

        return {
            "sucesso": True,
            "linhas_processadas": linhas_processadas,
            "inseridos": inseridos,
            "atualizados": atualizados,
            "erros_count": len(erros),
            "erros": erros[:20],  # Limitar a 20 erros de detalhes
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Erro ao processar CSV: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar arquivo CSV: {str(e)}")
