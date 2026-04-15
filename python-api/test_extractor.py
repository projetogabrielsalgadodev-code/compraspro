import asyncio
import json
from app.services.agno_agent import executar_analise_oferta

oferta = """Germed🚨

💊 Acetilcisteína 600 mg – R$ 13,41
📦 Pedido mínimo: 6 unidades

💊 Amoxicilina + Clavulanato 875/125 mg  14 com– R$ 28,57
📦 Pedido mínimo: 3 unidades"""

async def test():
    try:
        # Simulate an uploaded file
        fake_rows = [
            {"ean": "123", "descricao": "Acetilcisteína 600 mg", "preco_unitario": 10.0, "quantidade": 100},
            {"ean": "456", "descricao": "Amoxicilina + Clavulanato", "preco_unitario": 20.0, "quantidade": 50}
        ]
        res, metrics = await executar_analise_oferta(
            texto_bruto=oferta,
            empresa_id="5eec567f-1d48-4279-acc9-cdbfa2c5d41f", # Assuming this one exists or don't need it
            dados_arquivo=json.dumps(fake_rows),
            rows_arquivo=fake_rows
        )
        print("Success!")
        print(res.model_dump())
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Error during test:", e)

asyncio.run(test())
