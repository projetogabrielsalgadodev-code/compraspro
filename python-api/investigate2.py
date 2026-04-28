"""Investigate remaining divergences after fixes."""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from app.services.file_parser import parse_uploaded_file, _extract_tokens
from app.services.offer_extractor import extrair_multiplicador_inteligente, _classificar_forma_farmaceutica
from app.services.analysis_engine import construir_indice_arquivo, buscar_equivalentes, _match_item_no_arquivo

FILE_PATH = r"c:\Users\JoãoVictorRibeiroLag\Documents\Projetos Highcode\Projeto Gabriel Salgado\Projeto ComprasPRO\Entradas 01012025 a 15032026 diarias clean.xlsx"
with open(FILE_PATH, "rb") as f:
    file_bytes = f.read()
rows = parse_uploaded_file(file_bytes, "entradas.xlsx")
ean_stats, token_index = construir_indice_arquivo(rows)

print("=" * 100)
print("HISTAMIN XAROPE 100ML — Why is LOCAL=1.87 (DIPIRONA)?")
print("=" * 100)
desc = "HISTAMIN XAROPE 100ML"
cat = _classificar_forma_farmaceutica(desc)
print(f"Category: {cat}")
tokens = _extract_tokens(desc)
drug_tokens = {t for t in tokens if len(t) >= 4 and t.isalpha()}
print(f"Drug tokens: {drug_tokens}")
print(f"All tokens: {tokens}")

# Direct match
match = _match_item_no_arquivo(desc, None, ean_stats, token_index, set())
if match:
    print(f"Match: {match['descricao_arquivo']} | menor={match['menor_preco']} | conf={match['confianca_match']}")
    print(f"  EAN: {match['ean']}")

# Check what DIPIRONA XAROPE looks like  
print("\nAll DIPIRONA entries:")
for ean, stats in ean_stats.items():
    if "DIPIRONA" in stats.get("descricao", "").upper() and "XAROPE" in stats.get("descricao", "").upper():
        cat_eq = _classificar_forma_farmaceutica(stats["descricao"])
        t = _extract_tokens(stats["descricao"])
        dt = {tok for tok in t if len(tok) >= 4 and tok.isalpha()}
        common = drug_tokens & dt
        print(f"  EAN={ean}: {stats['descricao']} | cat={cat_eq} | menor={stats['menor_preco']}")
        print(f"    tokens={t}, drug_tokens={dt}")
        print(f"    common with HISTAMIN: {common}")

print("\nAll HISTAMIN entries:")
for ean, stats in ean_stats.items():
    if "HISTAMIN" in stats.get("descricao", "").upper():
        cat_eq = _classificar_forma_farmaceutica(stats["descricao"])
        print(f"  EAN={ean}: {stats['descricao']} | cat={cat_eq} | menor={stats['menor_preco']}")

print("\n" + "=" * 100)
print("DORFLEX HOSPITALAR C/300CPR 30X10 — DB=0.5144 vs LOCAL=0.1859")
print("=" * 100)
desc = "DORFLEX HOSPITALAR C/300CPR 30X10"
cat = _classificar_forma_farmaceutica(desc)
print(f"Category: {cat}")
mult = extrair_multiplicador_inteligente(desc)
print(f"Multiplicador: {mult}")

match = _match_item_no_arquivo(desc, None, ean_stats, token_index, set())
if match:
    print(f"Match: {match['descricao_arquivo']} | menor_raw={match['menor_preco']} | conf={match['confianca_match']}")

# What's the actual price per tablet?
# Oferta: 179.90 / 300 = 0.5997 per tablet
# But if the historical data is for a 36-pack at 17.99 => 0.4997 per tablet
# The LOCAL shows 0.1859 which seems too low - likely the index normalized by a wrong mult

for ean, stats in ean_stats.items():
    if "DORFLEX" in stats.get("descricao", "").upper():
        cat_eq = _classificar_forma_farmaceutica(stats["descricao"])
        mm = extrair_multiplicador_inteligente(stats["descricao"])
        print(f"  EAN={ean}: {stats['descricao']} | cat={cat_eq} | mult={mm} | menor={stats['menor_preco']}")
