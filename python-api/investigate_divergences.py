"""Investigate specific divergences"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from app.services.file_parser import parse_uploaded_file, _extract_tokens
from app.services.offer_extractor import extrair_multiplicador_inteligente, _classificar_forma_farmaceutica
from app.services.analysis_engine import construir_indice_arquivo, buscar_equivalentes

FILE_PATH = r"c:\Users\JoãoVictorRibeiroLag\Documents\Projetos Highcode\Projeto Gabriel Salgado\Projeto ComprasPRO\Entradas 01012025 a 15032026 diarias clean.xlsx"

with open(FILE_PATH, "rb") as f:
    file_bytes = f.read()
rows = parse_uploaded_file(file_bytes, "entradas.xlsx")
ean_stats, token_index = construir_indice_arquivo(rows)

print("=" * 100)
print("DIVERGENCE 1: SAL DE FRUTA 100GRS")
print("=" * 100)
# DB shows menor_hist=9.72, LOCAL shows 16.642
# DB was getting menor via equivalente (SAL DE FRUTA LARANJA)
# LOCAL correctly only shows same-category (po) equivalentes
desc = "SAL DE FRUTA 100GRS"
cat = _classificar_forma_farmaceutica(desc)
print(f"  Category: {cat}")
print(f"  Mult: {extrair_multiplicador_inteligente(desc)}")

# Find all SAL DE FRUTA in index
sal_eans = []
for ean, stats in ean_stats.items():
    if "SAL" in stats.get("descricao", "").upper() and "FRUT" in stats.get("descricao", "").upper():
        cat_eq = _classificar_forma_farmaceutica(stats["descricao"])
        print(f"  EAN={ean}: {stats['descricao']} | cat={cat_eq} | menor={stats['menor_preco']}")
        sal_eans.append(ean)

print("\n" + "=" * 100)
print("DIVERGENCE 2: HISTAMIN XAROPE - DB=6.804 vs LOCAL=6.07")
print("=" * 100)
desc = "HISTAMIN XAROPE 100ML"
cat = _classificar_forma_farmaceutica(desc)
print(f"  Category: {cat}")

for ean, stats in ean_stats.items():
    if "HISTAMIN" in stats.get("descricao", "").upper():
        cat_eq = _classificar_forma_farmaceutica(stats["descricao"])
        print(f"  EAN={ean}: {stats['descricao']} | cat={cat_eq} | menor={stats['menor_preco']}")

# LOCAL got 6.07 - must be from an equivalente with different match 
# DB got 6.804 - direct match
# Need to check what the equivalentes are finding

print("\n" + "=" * 100)
print("DIVERGENCE 3: CELESTRAT XAROPE - DB=1.8693 vs LOCAL=6.07")
print("=" * 100)
desc = "CELESTRAT XAROPE 100ML"
cat = _classificar_forma_farmaceutica(desc)
print(f"  Category: {cat}")

# Search for CELESTRAT
for ean, stats in ean_stats.items():
    if "CELESTRAT" in stats.get("descricao", "").upper():
        print(f"  EAN={ean}: {stats['descricao']} | menor={stats['menor_preco']}")

# DB matched DIPIRONA MONOIDRATADA XAROPE - that's wrong match
# LOCAL matched DESLORATADINA XAROPE 60ML - also wrong
# The LOCAL menor_hist=6.07 came from equivalente

# Find what token overlap exists
tokens_celestrat = _extract_tokens(desc)
print(f"  Tokens: {tokens_celestrat}")

# Search what the equivalentes function finds
equivs = buscar_equivalentes(desc, None, ean_stats, token_index)
for eq in equivs:
    print(f"  Equiv: {eq['descricao']} | menor={eq['menor_preco']}")

print("\n" + "=" * 100)
print("DIVERGENCE 4: CETOPROFENO - DB=0.1103 vs LOCAL=0.3565")
print("=" * 100)
desc = "CETOPROFENO 150MG C/ 10CPR EMS"
cat = _classificar_forma_farmaceutica(desc)
print(f"  Category: {cat}")

for ean, stats in ean_stats.items():
    if "CETOPROF" in stats.get("descricao", "").upper():
        cat_eq = _classificar_forma_farmaceutica(stats["descricao"])
        print(f"  EAN={ean}: {stats['descricao']} | cat={cat_eq} | menor={stats['menor_preco']}")

equivs = buscar_equivalentes(desc, None, ean_stats, token_index)
for eq in equivs:
    print(f"  Equiv: {eq['descricao']} | menor={eq['menor_preco']}")

print("\n" + "=" * 100)
print("DIVERGENCE 5: DESLORATADINA XAROPE - DB=6.07 vs LOCAL=0.307")
print("=" * 100)
desc = "DESLORATADINA XAROPE 0,5MG/ML C/60ML"
cat = _classificar_forma_farmaceutica(desc)
print(f"  Category: {cat}")
print(f"  Mult: {extrair_multiplicador_inteligente(desc)}")

for ean, stats in ean_stats.items():
    if "DESLORAT" in stats.get("descricao", "").upper():
        cat_eq = _classificar_forma_farmaceutica(stats["descricao"])
        print(f"  EAN={ean}: {stats['descricao']} | cat={cat_eq} | menor={stats['menor_preco']}")

equivs = buscar_equivalentes(desc, None, ean_stats, token_index)
for eq in equivs:
    print(f"  Equiv: {eq['descricao']} | menor={eq['menor_preco']}")
