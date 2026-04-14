"""
File Parser — Parseia arquivos de dados enviados pelo frontend (CSV, XLSX, XLS, TXT).

Converte o conteúdo em uma lista de dicts normalizados para injeção no prompt do agente.
"""
from __future__ import annotations

import csv
import io
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Mapeamento de nomes de coluna comuns → nomes canônicos
_COLUMN_ALIASES: dict[str, str] = {
    # EAN / código de barras
    "ean": "ean",
    "codigo_barras": "ean",
    "código de barras": "ean",
    "codigo de barras": "ean",
    "cod barras": "ean",
    "cod. barras": "ean",
    "gtin": "ean",
    "barcode": "ean",
    # Descrição
    "descricao": "descricao",
    "descrição": "descricao",
    "descricao do produto": "descricao",
    "descrição do produto": "descricao",
    "produto": "descricao",
    "nome": "descricao",
    "nome do produto": "descricao",
    "item": "descricao",
    # Preço unitário
    "preco_unitario": "preco_unitario",
    "preco unitario": "preco_unitario",
    "preço unitário": "preco_unitario",
    "preco": "preco_unitario",
    "preço": "preco_unitario",
    "vlr unitario": "preco_unitario",
    "vlr. unitário": "preco_unitario",
    "valor unitario": "preco_unitario",
    "valor unitário": "preco_unitario",
    "unit_price": "preco_unitario",
    # Quantidade
    "quantidade": "quantidade",
    "qtde": "quantidade",
    "qtd": "quantidade",
    "qtde. unitária": "quantidade",
    "qtde. unitaria": "quantidade",
    "qtde unitaria": "quantidade",
    "qtde unitária": "quantidade",
    "qty": "quantidade",
    "quantity": "quantidade",
    "quantidade_unitaria": "quantidade",
    # Valor total
    "valor_total": "valor_total",
    "valor total": "valor_total",
    "valor total do item": "valor_total",
    "vlr total": "valor_total",
    "vlr. total": "valor_total",
    "total": "valor_total",
    "valor_total_item": "valor_total",
    # Data
    "data": "data_entrada",
    "data_entrada": "data_entrada",
    "data entrada": "data_entrada",
    "data/hora da entrada": "data_entrada",
    "data hora da entrada": "data_entrada",
    "dt entrada": "data_entrada",
    "date": "data_entrada",
    # Fornecedor
    "fornecedor": "fornecedor",
    "supplier": "fornecedor",
    # ICMS ST
    "valor_icms_st": "valor_icms_st",
    "valor do icms st": "valor_icms_st",
    "icms st": "valor_icms_st",
    # Outras despesas
    "valor_outras_despesas": "valor_outras_despesas",
    "valor de outras despesas": "valor_outras_despesas",
    "outras despesas": "valor_outras_despesas",
}


def _normalize_column_name(col: str) -> str:
    """Normaliza nome de coluna para o alias canônico."""
    import re as _re
    import unicodedata
    cleaned = col.strip().lower()
    # Remover acentos para matching
    cleaned_no_accent = unicodedata.normalize("NFKD", cleaned)
    cleaned_no_accent = "".join(c for c in cleaned_no_accent if not unicodedata.combining(c))
    # Substituir separadores por espaço e colapsar
    cleaned_no_accent = _re.sub(r"[_./]+", " ", cleaned_no_accent).strip()
    cleaned_no_accent = _re.sub(r"\s+", " ", cleaned_no_accent)
    # Tentar match exato com versão sem acento
    if cleaned_no_accent in _COLUMN_ALIASES:
        return _COLUMN_ALIASES[cleaned_no_accent]
    # Também tentar a versão original com acentos
    cleaned_spaces = _re.sub(r"[_./]+", " ", cleaned).strip()
    cleaned_spaces = _re.sub(r"\s+", " ", cleaned_spaces)
    if cleaned_spaces in _COLUMN_ALIASES:
        return _COLUMN_ALIASES[cleaned_spaces]
    # Tentar com underscores
    cleaned_underscore = cleaned_no_accent.replace(" ", "_")
    if cleaned_underscore in _COLUMN_ALIASES:
        return _COLUMN_ALIASES[cleaned_underscore]
    return cleaned_underscore  # retorna como está


def _parse_number(value: Any) -> float | None:
    """Converte valor para float, tratando vírgulas e strings."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().replace(" ", "")
    if not s or s.lower() in ("none", "null", "nan", "-", ""):
        return None
    # Formato brasileiro: 1.234,56 → 1234.56
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _parse_csv(file_bytes: bytes, filename: str) -> list[dict[str, Any]]:
    """Parseia CSV ou TXT (tab-separated)."""
    # Detectar encoding
    for encoding in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        try:
            text = file_bytes.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = file_bytes.decode("utf-8", errors="replace")

    # Detectar delimitador
    sample = text[:2000]
    if "\t" in sample:
        delimiter = "\t"
    elif ";" in sample and sample.count(";") > sample.count(","):
        delimiter = ";"
    else:
        delimiter = ","

    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    rows = []
    for row_raw in reader:
        normalized = {}
        for col, val in row_raw.items():
            if col is None:
                continue
            canonical = _normalize_column_name(col)
            normalized[canonical] = val
        rows.append(normalized)

    return rows


def _parse_xlsx(file_bytes: bytes, filename: str) -> list[dict[str, Any]]:
    """Parseia XLSX/XLS usando openpyxl."""
    import openpyxl
    from datetime import datetime as dt

    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
    ws = wb.active

    # Encontrar o header: procurar a primeira linha com ≥3 colunas não-vazias
    header_row = None
    header_idx = 1
    for i, row in enumerate(ws.iter_rows(min_row=1, max_row=20), 1):
        vals = [cell.value for cell in row]
        non_empty = sum(1 for v in vals if v is not None and str(v).strip())
        if non_empty >= 3:
            header_row = vals
            header_idx = i
            break

    if not header_row:
        wb.close()
        return []

    # Normalizar nomes de colunas
    col_mapping: list[tuple[int, str]] = []
    for idx, col_name in enumerate(header_row):
        if col_name and str(col_name).strip():
            canonical = _normalize_column_name(str(col_name))
            col_mapping.append((idx, canonical))

    rows = []
    for row in ws.iter_rows(min_row=header_idx + 1):
        vals = [cell.value for cell in row]
        # Pular linhas totalmente vazias
        if all(v is None or str(v).strip() == "" for v in vals):
            continue

        record: dict[str, Any] = {}
        for col_idx, canonical_name in col_mapping:
            if col_idx < len(vals):
                value = vals[col_idx]
                # Converter datetime para string
                if isinstance(value, dt):
                    value = value.strftime("%Y-%m-%d")
                record[canonical_name] = value

        # Só adicionar se tem ao menos um campo relevante
        if record.get("ean") or record.get("descricao") or record.get("valor_total"):
            rows.append(record)

    wb.close()
    return rows


def parse_uploaded_file(file_bytes: bytes, filename: str) -> list[dict[str, Any]]:
    """
    Parseia um arquivo enviado pelo usuário.

    Retorna lista de dicts com colunas normalizadas.
    Suporta: .csv, .xlsx, .xls, .txt
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext in ("xlsx", "xls"):
        rows = _parse_xlsx(file_bytes, filename)
    elif ext in ("csv", "txt", "tsv"):
        rows = _parse_csv(file_bytes, filename)
    else:
        raise ValueError(f"Formato de arquivo não suportado: .{ext}. Use CSV, XLSX, XLS ou TXT.")

    logger.info(f"Arquivo {filename} parseado: {len(rows)} registros")
    return rows


def _calcular_preco_unitario(row: dict) -> float | None:
    """Calcula preço unitário a partir de valor_total / quantidade."""
    valor_total = _parse_number(row.get("valor_total"))
    qtde = _parse_number(row.get("quantidade"))

    # Se já tem preço unitário, usar esse
    pu = _parse_number(row.get("preco_unitario"))
    if pu and pu > 0:
        return round(pu, 4)

    # Calcular a partir de valor_total / quantidade
    if valor_total and qtde and qtde > 0:
        return round(valor_total / qtde, 4)

    # Fallback: valor_total é o preço unitário (qtde=1 implícita)
    if valor_total and valor_total > 0:
        return round(valor_total, 4)

    return None


def format_file_data_for_prompt(rows: list[dict[str, Any]], max_rows: int = 300) -> str:
    """
    Formata os dados parseados como texto estruturado para injeção no prompt do agente.

    Agrupa por EAN e calcula estatísticas (menor preço, média, contagem de entradas).
    """
    from collections import defaultdict
    from statistics import mean

    if not rows:
        return "Nenhum dado encontrado no arquivo enviado."

    # Agrupar por EAN
    by_ean: dict[str, list[dict]] = defaultdict(list)
    sem_ean: list[dict] = []

    for row in rows:
        ean = row.get("ean")
        if ean and str(ean).strip() and str(ean).strip() not in ("0", "None", "none", "null"):
            by_ean[str(ean).strip()].append(row)
        elif row.get("descricao"):
            sem_ean.append(row)

    lines = [
        f"=== DADOS DO ARQUIVO DO CLIENTE ({len(rows)} registros, {len(by_ean)} EANs únicos) ===",
        "",
        "Formato: EAN | Descrição | Qtd Entradas | Menor Preço Unit. | Média Preço Unit. | Última Data",
        "---",
    ]

    count = 0
    for ean, entries in sorted(by_ean.items()):
        if count >= max_rows:
            lines.append(f"... e mais {len(by_ean) - count} EANs não exibidos")
            break

        precos = []
        datas = []
        descricao = ""

        for e in entries:
            pu = _calcular_preco_unitario(e)
            if pu and pu > 0:
                precos.append(pu)
            d = e.get("data_entrada")
            if d:
                datas.append(str(d))
            if not descricao and e.get("descricao"):
                descricao = str(e["descricao"]).strip()

        menor = min(precos) if precos else None
        media = round(mean(precos), 4) if precos else None
        ultima_data = max(datas) if datas else "N/A"
        qtd_entradas = len(entries)
        qtde_total = sum(_parse_number(e.get("quantidade")) or 0 for e in entries)

        menor_str = f"R${menor:.2f}" if menor else "N/A"
        media_str = f"R${media:.2f}" if media else "N/A"

        lines.append(
            f"EAN: {ean} | {descricao[:60]} | {qtd_entradas} entradas ({qtde_total:.0f} un) | "
            f"Menor: {menor_str} | Média: {media_str} | Última: {ultima_data}"
        )
        count += 1

    if sem_ean:
        lines.append(f"\n--- {len(sem_ean)} registros sem EAN (ignorados para comparação) ---")

    lines.append("\n=== FIM DOS DADOS DO ARQUIVO ===")
    return "\n".join(lines)
