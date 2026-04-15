"""Quick test: regex fallback does hierarchy."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "python-api"))
from app.services.offer_extractor import extrair_itens_regex

OFERTA = """GERMED
Amoxi clavi 400 Mg suspensao
->13,45

Ondasetrona
->4 Mg 3,17
->8 Mg 5,55

Olmesartana
->20 Mg 10,97
->40 Mg 13,60

Olmesartana hct
->20/12,5 17,75
->40/12,5 19,67
->40/25 18,01

Clotrimazol vag
->10 Mg C/6 aplic 15,54
->20 Mg C/3 aplic 15,82

Rebaixa Linha Luftal
Desconto 20%
Luftal 75mg GTS 15ml
Luftal 75mg GTS 30ml
Luftal max 125mg 10cps

BENEGRIP 30%
ENGOV 30%
"""

itens = extrair_itens_regex(OFERTA)
print(f"Total: {len(itens)} itens\n")
for i, item in enumerate(itens, 1):
    tipo = item["tipo_preco"]
    if tipo == "absoluto":
        print(f"  {i:2}. {item['descricao'][:55]:55} R${item['preco']:.2f}")
    else:
        print(f"  {i:2}. {item['descricao'][:55]:55} {item['desconto_percentual']:.0f}% desc")
