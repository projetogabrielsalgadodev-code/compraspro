"""
Test completo end-to-end do fluxo de analise de ofertas.
Testa todos os cenarios com os dados reais do cliente.
Inclui verificacao das melhorias da auditoria.
"""
import sys
import os
os.chdir(r'c:\Users\JoãoVictorRibeiroLag\Documents\Projetos Highcode\Projeto Gabriel Salgado\Projeto ComprasPRO\python-api')

import logging
logging.basicConfig(level=logging.INFO, format="%(name)s %(levelname)s %(message)s")
logger = logging.getLogger("test_e2e")

from app.services.file_parser import parse_uploaded_file, parse_offer_file, _calcular_preco_unitario
from app.services.analysis_engine import construir_indice_arquivo, executar_analise_deterministico
from app.services.offer_extractor import extrair_itens_regex, extrair_multiplicador_inteligente, _parse_preco_br

OFFER_PATH = r'c:\Users\JoãoVictorRibeiroLag\Documents\Projetos Highcode\Projeto Gabriel Salgado\Projeto ComprasPRO\TABELA OL- MEDQUIMICA.xlsx'
ENTRIES_PATH = r'c:\Users\JoãoVictorRibeiroLag\Documents\Projetos Highcode\Projeto Gabriel Salgado\Projeto ComprasPRO\Entradas ate 16042026.xlsx'

errors = []
warnings = []

def check(condition, msg, is_warning=False):
    if not condition:
        if is_warning:
            warnings.append(msg)
            print(f"  [WARN] {msg}")
        else:
            errors.append(msg)
            print(f"  [FAIL] {msg}")
    else:
        print(f"  [OK] {msg}")

print("=" * 80)
print("TEST 1: _parse_preco_br - Price parsing")
print("=" * 80)
check(_parse_preco_br("15.1905") == 15.1905, "15.1905 (4 decimais)")
check(_parse_preco_br("24,17") == 24.17, "24,17 (BR format)")
check(_parse_preco_br("1.234,56") == 1234.56, "1.234,56 (BR thousands)")

print()
print("=" * 80)
print("TEST 2: extrair_multiplicador_inteligente - All product types")
print("=" * 80)
check(
    extrair_multiplicador_inteligente("**DONEPEZILA 10MG (C1) GEN 30 CPR-MQG") == 30.0,
    "DONEPEZILA (C1) 30 CPR -> mult=30"
)
check(
    extrair_multiplicador_inteligente("**FLUOXETINA 20MG (C1) GEN 30 CAPS-MQG") == 30.0,
    "FLUOXETINA (C1) 30 CAPS -> mult=30"
)

print()
print("=" * 80)
print("TEST 3: _calcular_preco_unitario - FIX #1 valor_unitario_final")
print("=" * 80)
# Simulating the client's actual column structure after alias normalization
row_with_final = {
    'preco_unitario': 18.68,  # valor_unitario_final is mapped to preco_unitario
    'valor_unitario_bruto': 20.0,
    'quantidade': 2,
    'valor_total': 37.36,
}
pu = _calcular_preco_unitario(row_with_final)
check(pu == 18.68, f"preco_unitario (via valor_unitario_final alias) = {pu}")

row_bruto_only = {
    'valor_unitario_bruto': 25.50,
    'quantidade': 4,
    'valor_total': 102.0,
}
pu2 = _calcular_preco_unitario(row_bruto_only)
check(pu2 == 25.50, f"Fallback to valor_unitario_bruto = {pu2}")

row_total_only = {
    'quantidade': 10,
    'valor_total': 150.0,
}
pu3 = _calcular_preco_unitario(row_total_only)
check(pu3 == 15.0, f"Fallback to valor_total/quantidade = {pu3}")

print()
print("=" * 80)
print("TEST 4: parse_offer_file - FIX #2 Supplier extraction")
print("=" * 80)
with open(OFFER_PATH, 'rb') as f:
    offer_bytes = f.read()
items, fornecedor = parse_offer_file(offer_bytes, 'TABELA OL- MEDQUIMICA.xlsx')
check(len(items) == 54, f"Offer: {len(items)} items (expected 54)")
check(fornecedor is not None, f"Fornecedor detectado: {fornecedor}")
check(items[0]["preco"] is not None and items[0]["preco"] > 0, f"First item preco = {items[0]['preco']}")

print()
print("=" * 80)
print("TEST 5: parse_uploaded_file - History XLSX")
print("=" * 80)
with open(ENTRIES_PATH, 'rb') as f:
    entries_bytes = f.read()
rows = parse_uploaded_file(entries_bytes, 'Entradas ate 16042026.xlsx')
check(len(rows) > 10000, f"Entries: {len(rows)} rows")
# FIX #1: Check that valor_unitario_final is mapped to preco_unitario
first_row_keys = list(rows[0].keys())
check("preco_unitario" in first_row_keys, f"valor_unitario_final mapped to preco_unitario")

print()
print("=" * 80)
print("TEST 6: construir_indice_arquivo - FIX #3 EAN validation")
print("=" * 80)
ean_stats, token_index = construir_indice_arquivo(rows)
check(len(ean_stats) > 1000, f"EAN stats: {len(ean_stats)} EANs")
# FIX #3: Verify invalid EANs like "00000SEM GTIN" are filtered out
invalid_eans = [e for e in ean_stats.keys() if not e.isdigit()]
check(len(invalid_eans) == 0, f"No invalid EANs (non-numeric entries filtered): found {len(invalid_eans)}")
# FIX #7: Verify descriptions are trimmed
sample_desc = ean_stats[list(ean_stats.keys())[0]]["descricao"]
check(sample_desc == sample_desc.strip(), f"Descriptions are trimmed (no leading spaces)")

print()
print("=" * 80)
print("TEST 7: executar_analise_deterministico - Full analysis + FIX #4")
print("=" * 80)
resultado = executar_analise_deterministico(
    itens_extraidos=items,
    fornecedor="MEDQUIMICA",
    ean_stats=ean_stats,
    token_index=token_index,
    total_registros=len(rows),
)

total_items = len(resultado['itens'])
ouro = sum(1 for i in resultado['itens'] if i['classificacao'] == 'ouro')
prata = sum(1 for i in resultado['itens'] if i['classificacao'] == 'prata')
atencao = sum(1 for i in resultado['itens'] if i['classificacao'] == 'atencao')
descartavel = sum(1 for i in resultado['itens'] if i['classificacao'] == 'descartavel')

check(total_items == 54, f"Analyzed {total_items} items")
check(ouro + prata + atencao + descartavel == total_items, "All items classified")

# FIX #4: Check false positive — GASTROGEL DE BOLSO should NOT match CALCULADORA DE BOLSO
gastrogel_bolso_items = [
    i for i in resultado['itens']
    if 'GASTROGEL' in i.get('descricao_original', '') and 'BOLSO' in i.get('descricao_original', '')
]
for g in gastrogel_bolso_items:
    matched = g.get('descricao_produto', '') or ''
    check(
        'CALCULADORA' not in matched.upper(),
        f"GASTROGEL DE BOLSO NOT matched with CALCULADORA (matched: {matched[:50]})"
    )

print()
print("=" * 80)
print("TEST 8: extrair_itens_regex - Text-based extraction")
print("=" * 80)
test_text = """PARACETAMOL 750MG C/20 R$ 12,50
DIPIRONA 500MG GOTAS 10ML R$ 8,90
IBUPROFENO 600MG C/10 R$ 15,00"""
regex_items = extrair_itens_regex(test_text)
check(len(regex_items) == 3, f"Regex: {len(regex_items)} items from BR text")

print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"  Analysis: {total_items} items")
print(f"    Ouro: {ouro} | Prata: {prata} | Atencao: {atencao} | Descartavel: {descartavel}")
if errors:
    print(f"\n  FAILED: {len(errors)} errors")
    for e in errors:
        print(f"    X {e}")
    sys.exit(1)
else:
    print(f"\n  ALL TESTS PASSED ({len(warnings)} warnings)")
    sys.exit(0)
