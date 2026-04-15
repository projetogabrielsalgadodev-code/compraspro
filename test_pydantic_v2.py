"""Test Pydantic V2 schema conversion end-to-end."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "python-api"))

from app.services.file_parser import parse_uploaded_file
from app.services.offer_extractor import extrair_itens
from app.services.analysis_engine import construir_indice_arquivo, executar_analise_deterministico
from app.models.schemas import ItemAnaliseAgno, AnaliseOfertaAgnoOutput

XLSX = r"c:\Users\JoãoVictorRibeiroLag\Documents\Projetos Highcode\Projeto Gabriel Salgado\Projeto ComprasPRO\Entradas 01012025 a 15032026 diarias clean.xlsx"


async def test():
    with open(XLSX, "rb") as f:
        rows = parse_uploaded_file(f.read(), "e.xlsx")

    fornecedor, itens = await extrair_itens(
        "Germed\nAcetilcisteina 600 mg R$ 13,41\nPregabalina 75 mg R$ 4,24"
    )
    ean_stats, token_index = construir_indice_arquivo(rows)
    resultado = executar_analise_deterministico(itens, fornecedor, ean_stats, token_index, len(rows))

    # Test Pydantic conversion (this is what agno_agent.py does)
    itens_agno = [ItemAnaliseAgno(**item) for item in resultado["itens"]]
    output = AnaliseOfertaAgnoOutput(fornecedor=resultado["fornecedor"], itens=itens_agno)

    # Test full serialization
    d = output.model_dump()
    print(f"OK: {len(d['itens'])} itens serialized to dict")
    for it in d["itens"]:
        equiv_count = len(it.get("equivalentes", []))
        preco = it.get("preco_oferta")
        preco_str = f"R${preco:.2f}" if preco else "None"
        print(
            f"  {it['descricao_original'][:40]:40} | "
            f"preco={preco_str:10} | "
            f"class={it['classificacao']:12} | "
            f"equiv={equiv_count} | "
            f"origem={it.get('origem_menor_historico')} | "
            f"tipo={it.get('tipo_preco')}"
        )
    
    # Test model_dump_json (used by FastAPI response)
    json_str = output.model_dump_json()
    print(f"\nJSON serialization: {len(json_str)} bytes - OK")
    print("\n=== ALL TESTS PASSED ===")


asyncio.run(test())
