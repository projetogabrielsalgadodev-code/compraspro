import asyncio
import sys
import os
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "python-api"))

from app.services.agno_agent import executar_analise_oferta

OFERTA = """Germed

Acetilcisteína 600 mg R$ 13,41
Amoxicilina + Clavulanato 875/125 mg R$ 28,57
"""

async def main():
    print("Iniciando analise de banco de dados...")
    resultado, metricas = await executar_analise_oferta(
        texto_bruto=OFERTA,
        empresa_id="4b79b2a7-ea4b-4b20-baeb-3c224213dbe6", # Um ID válido se precisar
        model_id=None,
        dados_arquivo=None,
        rows_arquivo=None
    )
    print("Sucesso!")
    print(resultado)
    print(metricas)

if __name__ == "__main__":
    asyncio.run(main())
