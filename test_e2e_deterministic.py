"""Teste E2E: Fluxo determinístico completo com arquivo XLSX real."""
import asyncio
import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "python-api"))

from app.services.file_parser import parse_uploaded_file
from app.services.offer_extractor import extrair_itens
from app.services.analysis_engine import (
    construir_indice_arquivo,
    executar_analise_deterministico,
)

XLSX_PATH = os.path.join(os.path.dirname(__file__), "Projeto ComprasPRO", "Entradas 01012025 a 15032026 diarias clean.xlsx")
if not os.path.exists(XLSX_PATH):
    XLSX_PATH = os.path.join(os.path.dirname(__file__), "Entradas 01012025 a 15032026 diarias clean.xlsx")
if not os.path.exists(XLSX_PATH):
    print(f"XLSX nao encontrado em {XLSX_PATH}")
    # Try relative
    for root, dirs, files in os.walk(os.path.dirname(__file__)):
        for f in files:
            if "Entradas" in f and f.endswith(".xlsx"):
                XLSX_PATH = os.path.join(root, f)
                break

OFERTA = """Oferta Germed - Abril 2025
Dicloridrato de Hidroxizina 25 mg - R$ 24,17
Nitazoxanida 500 mg - R$ 9,58
Olmesartana+Anlodipino 40/5mg - R$ 43,67
Paracetamol+Pseudoefedrina - R$ 14,73
Prednisona 20 mg - R$ 2,21
Pregabalina 75 mg - R$ 4,24
Trometamol Cetorolaco 10mg - R$ 7,14"""


async def main():
    print("=" * 70)
    print("TESTE E2E: Fluxo Deterministico com XLSX Real")
    print("=" * 70)

    # 1. Carregar arquivo
    print(f"\n1. Carregando arquivo: {XLSX_PATH}")
    if not os.path.exists(XLSX_PATH):
        print("ARQUIVO NAO ENCONTRADO - pulando teste E2E")
        return

    with open(XLSX_PATH, "rb") as f:
        file_bytes = f.read()

    start = time.time()
    rows = parse_uploaded_file(file_bytes, "Entradas.xlsx")
    t_parse = time.time() - start
    print(f"   {len(rows)} registros em {t_parse*1000:.0f}ms")

    # 2. Extrair itens da oferta
    print(f"\n2. Extraindo itens da oferta ({len(OFERTA)} chars)")
    start = time.time()
    fornecedor, itens = await extrair_itens(OFERTA)
    t_extract = time.time() - start
    print(f"   Fornecedor: {fornecedor}")
    print(f"   {len(itens)} itens em {t_extract*1000:.0f}ms")
    for i, item in enumerate(itens, 1):
        print(f"   {i}. {item['descricao']} -> R${item['preco']:.2f}")

    # 3. Construir indice
    print(f"\n3. Construindo indice do arquivo...")
    start = time.time()
    ean_stats, token_index = construir_indice_arquivo(rows)
    t_index = time.time() - start
    print(f"   {len(ean_stats)} EANs, {len(token_index)} tokens em {t_index*1000:.0f}ms")

    # 4. Analise deterministica
    print(f"\n4. Executando analise deterministica...")
    start = time.time()
    resultado = executar_analise_deterministico(
        itens_extraidos=itens,
        fornecedor=fornecedor,
        ean_stats=ean_stats,
        token_index=token_index,
        total_registros=len(rows),
    )
    t_analysis = time.time() - start
    print(f"   Concluido em {t_analysis*1000:.0f}ms")

    # 5. Resultados
    print(f"\n{'=' * 70}")
    print("RESULTADOS DA ANALISE")
    print(f"{'=' * 70}")
    print(f"Fornecedor: {resultado['fornecedor']}")
    print(f"Total itens: {len(resultado['itens'])}")
    print()

    for i, item in enumerate(resultado["itens"], 1):
        print(f"--- Item {i} ---")
        print(f"  Oferta:        {item['descricao_original']}")
        print(f"  Preco oferta:  R${item['preco_oferta']:.2f}")
        if item.get("descricao_produto"):
            print(f"  Match:         {item['descricao_produto']}")
            print(f"  EAN:           {item['ean']}")
            print(f"  Menor hist:    R${item['menor_historico']:.2f}" if item.get('menor_historico') else "  Menor hist:    N/A")
            print(f"  Variacao:      {item['variacao_percentual']:.1f}%" if item.get('variacao_percentual') is not None else "  Variacao:      N/A")
            print(f"  Demanda/mes:   {item['demanda_mes']}")
            print(f"  Sugestao:      {item['sugestao_pedido']} un")
            print(f"  Confianca:     {item['confianca_match']}")
        else:
            print(f"  Match:         SEM MATCH")
        print(f"  Classificacao: {item['classificacao']}")
        print(f"  Recomendacao:  {item['recomendacao']}")
        print()

    # Totais
    total_ms = (t_parse + t_extract + t_index + t_analysis) * 1000
    print(f"{'=' * 70}")
    print(f"PERFORMANCE")
    print(f"  Parse XLSX:       {t_parse*1000:.0f}ms")
    print(f"  Extracao regex:   {t_extract*1000:.0f}ms")
    print(f"  Indice arquivo:   {t_index*1000:.0f}ms")
    print(f"  Analise itens:    {t_analysis*1000:.0f}ms")
    print(f"  TOTAL:            {total_ms:.0f}ms")
    print(f"  Custo LLM:        R$0.00 (100% deterministico)")
    print(f"{'=' * 70}")

    classificacoes = [i["classificacao"] for i in resultado["itens"]]
    matched = sum(1 for i in resultado["itens"] if i.get("descricao_produto"))
    print(f"\nResumo: {matched}/{len(resultado['itens'])} matches encontrados")
    print(f"  Ouro: {classificacoes.count('ouro')}")
    print(f"  Prata: {classificacoes.count('prata')}")
    print(f"  Atencao: {classificacoes.count('atencao')}")
    print(f"  Descartavel: {classificacoes.count('descartavel')}")


asyncio.run(main())
