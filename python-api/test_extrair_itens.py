import asyncio
import os
from pprint import pprint
from app.services.offer_extractor import extrair_itens
from app.db.supabase_client import get_settings

async def test_full():
    texto = "Oferta: Aspirina 10,00"
    fornecedor, itens, metrics = await extrair_itens(texto)
    print("Fornecedor:", fornecedor)
    print("Itens:", itens)
    print("Metrics:", metrics)

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(test_full())
