"""Teste funcional do fluxo determinístico completo."""
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "python-api"))

from app.services.offer_extractor import extrair_itens_regex, _detectar_fornecedor_regex
from app.services.analysis_engine import (
    calcular_variacao_percentual,
    calcular_sugestao_pedido,
    classificar_oferta,
    gerar_recomendacao,
)

# ─── Teste 1: Extração por Regex ──────────────────────────────────────────────
print("=" * 70)
print("TESTE 1: Extração por Regex")
print("=" * 70)

texto_oferta = """Oferta Germed - Medicamentos com desconto
Dicloridrato de Hidroxizina 25 mg - R$ 24,17
Nitazoxanida 500 mg - R$ 9,58
Olmesartana+Anlodipino 40/5mg - R$ 43,67
Paracetamol+Pseudoefedrina - R$ 14,73
Prednisona 20 mg - R$ 2,21
Pregabalina 75 mg - R$ 4,24
Trometamol Cetorolaco 10mg - R$ 7,14"""

itens = extrair_itens_regex(texto_oferta)
fornecedor = _detectar_fornecedor_regex(texto_oferta)

print(f"Fornecedor detectado: {fornecedor}")
print(f"Itens extraídos: {len(itens)}")
for i, item in enumerate(itens, 1):
    print(f"  {i}. {item['descricao']} -> R${item['preco']:.2f} (EAN: {item['ean']})")

assert len(itens) == 7, f"Esperava 7 itens, got {len(itens)}"
assert fornecedor is not None, "Fornecedor deveria ser detectado"
print("\n✅ Teste 1: PASSOU\n")

# ─── Teste 2: Cálculos Determinísticos ───────────────────────────────────────
print("=" * 70)
print("TESTE 2: Cálculos Determinísticos")
print("=" * 70)

# Caso 1: Desconto forte (ouro)
var1 = calcular_variacao_percentual(2.96, 2.21)
print(f"Prednisona: menor=R$2.96, oferta=R$2.21 → var={var1}%")
assert var1 is not None
assert var1 > 20, f"Deveria ser >20%, got {var1}%"
assert classificar_oferta(var1) == "ouro"
print(f"  Classificação: {classificar_oferta(var1)} ✅")

# Caso 2: Desconto moderado (prata)
var2 = calcular_variacao_percentual(9.31, 8.50)
print(f"Nitazoxanida: menor=R$9.31, oferta=R$8.50 → var={var2}%")
assert classificar_oferta(var2) == "prata"
print(f"  Classificação: {classificar_oferta(var2)} ✅")

# Caso 3: Ágio (descartavel)
var3 = calcular_variacao_percentual(5.00, 6.00)
print(f"Produto X: menor=R$5.00, oferta=R$6.00 → var={var3}%")
assert var3 < 0
assert classificar_oferta(var3) == "descartavel"
print(f"  Classificação: {classificar_oferta(var3)} ✅")

# Sugestão de pedido
sug = calcular_sugestao_pedido(demanda_mes=25.5, estoque=0, meses_cobertura=3)
print(f"\nSugestão pedido: demanda=25.5, estoque=0, 3 meses → {sug} unidades")
assert sug == 76, f"Esperava 76, got {sug}"  # round(25.5 * 3) = round(76.5) = 76 (banker's rounding)

sug2 = calcular_sugestao_pedido(demanda_mes=25.5, estoque=50, meses_cobertura=3)
print(f"Sugestão pedido: demanda=25.5, estoque=50, 3 meses → {sug2} unidades")
assert sug2 == 26, f"Esperava 26, got {sug2}"  # 76 - 50 = 26

print("\n✅ Teste 2: PASSOU\n")

# ─── Teste 3: Recomendações por Template ──────────────────────────────────────
print("=" * 70)
print("TESTE 3: Recomendações por Template")
print("=" * 70)

rec_ouro = gerar_recomendacao("ouro", 25.34, 2.96, 2.21, 25.5, 77, "Prednisona 20mg")
print(f"OURO: {rec_ouro}")
assert "25.3%" in rec_ouro
assert "R$2.96" in rec_ouro
assert "77" in rec_ouro

rec_prata = gerar_recomendacao("prata", 8.70, 9.31, 8.50, 10.0, 30)
print(f"PRATA: {rec_prata}")
assert "8.7%" in rec_prata

rec_descartavel = gerar_recomendacao("descartavel", -20.0, 5.00, 6.00, 0, 0)
print(f"DESCARTÁVEL: {rec_descartavel}")
assert "ACIMA" in rec_descartavel

rec_sem_match = gerar_recomendacao("descartavel", None, None, None, 0, 0)
print(f"SEM MATCH: {rec_sem_match}")
assert "Sem dados" in rec_sem_match

print("\n✅ Teste 3: PASSOU\n")

print("=" * 70)
print("TODOS OS TESTES PASSARAM ✅✅✅")
print("=" * 70)
