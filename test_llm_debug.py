"""Quick debug: ver o que o LLM extraiu exatamente."""
import asyncio, sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "python-api"))
from app.services.offer_extractor import extrair_itens

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

async def main():
    forn, itens = await extrair_itens(OFERTA)
    print(f"Fornecedor: {forn}")
    print(f"Total itens: {len(itens)}\n")
    for i, item in enumerate(itens, 1):
        print(f"{i:3}. {item['descricao'][:50]:50} | preco={item.get('preco')} | tipo={item['tipo_preco']} | desc%={item.get('desconto_percentual')}")

asyncio.run(main())
