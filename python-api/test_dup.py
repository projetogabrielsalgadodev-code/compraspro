"""Test duplicate histamin match"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from app.services.file_parser import parse_uploaded_file
from app.services.analysis_engine import construir_indice_arquivo, _match_item_no_arquivo

FILE_PATH = r"c:\Users\JoãoVictorRibeiroLag\Documents\Projetos Highcode\Projeto Gabriel Salgado\Projeto ComprasPRO\Entradas 01012025 a 15032026 diarias clean.xlsx"
with open(FILE_PATH, "rb") as f:
    file_bytes = f.read()
rows = parse_uploaded_file(file_bytes, "entradas.xlsx")
ean_stats, token_index = construir_indice_arquivo(rows)

used = set()
m1 = _match_item_no_arquivo("HISTAMIN XAROPE 100ML", None, ean_stats, token_index, used)
m2 = _match_item_no_arquivo("HISTAMIN XAROPE 100ML", None, ean_stats, token_index, used)
print("Match 1:", m1["descricao_arquivo"], "| menor=", m1["menor_preco"])
print("Match 2:", m2["descricao_arquivo"], "| menor=", m2["menor_preco"])
