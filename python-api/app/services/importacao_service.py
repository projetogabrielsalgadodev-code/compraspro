from __future__ import annotations

from io import BytesIO
from typing import Any

import pandas as pd

from app.models.schemas import EntradaImportada, ProdutoImportado
from app.services.lab_normalizer import normalizar_laboratorio


MAPEAMENTO_SUGCOMPRA = {
    "Barras": "ean",
    "Descricao": "descricao",
    "Descri��o": "descricao",
    "Princ. Ativo": "principio_ativo",
    "Fabric.": "fabricante_bruto",
    "Estoque": "estoque",
    "Demanda M�s": "demanda_mes",
    "Grupo": "grupo",
    "Curva ABC": "curva_abc",
}

MAPEAMENTO_ENTRADAS = {
    "Data/Hora da Entrada": "data_entrada",
    "Codigo de Barras": "ean",
    "C�digo de Barras": "ean",
    "Qtde. Unit�ria": "quantidade_unitaria",
    "Valor Total do Item": "valor_total_item",
    "Valor do ICMS ST": "valor_icms_st",
    "Valor de Outras Despesas": "valor_outras_despesas",
    "Fornecedor": "fornecedor",
}


def _read_dataframe(filename: str, content: bytes) -> pd.DataFrame:
    if filename.lower().endswith(".csv"):
        df = pd.read_csv(BytesIO(content), sep=None, engine="python")
    else:
        df = pd.read_excel(BytesIO(content))
        
    # Heurística para pular cabeçalhos irrelevantes (Relatório, etc.) e achar colunas
    for idx, row in df.head(10).iterrows():
        row_str = " ".join([str(x) for x in row.values if pd.notna(x)])
        if "Barras" in row_str or "Data" in row_str or "Descri" in row_str:
            df.columns = row.values
            df = df.iloc[idx+1:]
            df = df.reset_index(drop=True)
            break
            
    return df


import unicodedata

def normalize_key(key: str) -> str:
    """Remove acentos e espaços extras para matching robusto de colunas"""
    if not isinstance(key, str):
        return ""
    nfkd = unicodedata.normalize('NFKD', key)
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).lower().replace(" ", "").replace(".", "")

MAPEAMENTO_SUGCOMPRA_NORM = {
    normalize_key(k): v for k, v in MAPEAMENTO_SUGCOMPRA.items()
}

MAPEAMENTO_ENTRADAS_NORM = {
    normalize_key(k): v for k, v in MAPEAMENTO_ENTRADAS.items()
}

def parse_produtos(filename: str, content: bytes) -> list[ProdutoImportado]:
    df = _read_dataframe(filename, content)
    registros: list[ProdutoImportado] = []
    
    # Criar dict reverso das colunas presentes
    col_map = {normalize_key(str(c)): c for c in df.columns}
    
    for _, row in df.iterrows():
        payload: dict[str, Any] = {}
        for original_norm, target in MAPEAMENTO_SUGCOMPRA_NORM.items():
            col_real = col_map.get(original_norm)
            if col_real and col_real in row and pd.notna(row[col_real]):
                val = row[col_real]
                if target == "ean":
                    val = str(val).split('.')[0].strip()
                payload[target] = val
        if not payload.get("ean"):
            continue
        payload["estoque"] = int(float(payload.get("estoque", 0) or 0))
        payload["demanda_mes"] = float(payload["demanda_mes"]) if payload.get("demanda_mes") is not None else None
        payload["fabricante"] = normalizar_laboratorio(payload.get("fabricante_bruto"))
        registros.append(ProdutoImportado(**payload))
    return registros


def parse_entradas(filename: str, content: bytes) -> list[EntradaImportada]:
    df = _read_dataframe(filename, content)
    registros: list[EntradaImportada] = []
    
    # Criar dict reverso das colunas
    col_map = {normalize_key(str(c)): c for c in df.columns}
    
    for _, row in df.iterrows():
        payload: dict[str, Any] = {}
        for original_norm, target in MAPEAMENTO_ENTRADAS_NORM.items():
            col_real = col_map.get(original_norm)
            if col_real and col_real in row and pd.notna(row[col_real]):
                val = row[col_real]
                if target == "data_entrada" and hasattr(val, "isoformat"):
                    val = val.isoformat()
                elif target == "ean":
                    val = str(val).split('.')[0].strip()
                payload[target] = val
        if not payload.get("ean"):
            continue
        payload["quantidade_unitaria"] = float(payload.get("quantidade_unitaria", 0) or 0)
        payload["valor_total_item"] = float(payload.get("valor_total_item", 0) or 0)
        payload["valor_icms_st"] = float(payload.get("valor_icms_st", 0) or 0)
        payload["valor_outras_despesas"] = float(payload.get("valor_outras_despesas", 0) or 0)
        registros.append(EntradaImportada(**payload))
    return registros
