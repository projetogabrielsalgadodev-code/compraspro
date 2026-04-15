"""
Analise de oferta Germed via fluxo deterministico.
Roda localmente com o XLSX real.
"""
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

XLSX_PATH = r"c:\Users\JoãoVictorRibeiroLag\Documents\Projetos Highcode\Projeto Gabriel Salgado\Projeto ComprasPRO\Entradas 01012025 a 15032026 diarias clean.xlsx"

OFERTA = """Germed

Acetilcisteina 600 mg R$ 13,41
Amoxicilina + Clavulanato 875/125 mg R$ 28,57
Duloxetina 60 mg R$ 36,00
Tramadol 100 mg R$ 34,18
Duloxetina 30 mg R$ 22,40
Dicloridrato de Hidroxizina 25 mg R$ 24,17
Nitazoxanida 500 mg R$ 9,58
Olmesartana + Anlodipino 40/5 mg R$ 24,54
Paracetamol + Pseudoefedrina 500/30 mg R$ 9,37
Prednisona 20 mg R$ 2,21
Pregabalina 75 mg R$ 4,24
Trometamol Cetorolaco 10 mg R$ 3,75
Amoxi clavi 400 Mg suspensao R$ 13,45
Bilastina 20mg R$ 26,45
Ondasetrona 4 Mg R$ 3,17
Ondasetrona 8 Mg R$ 5,55
Hidroxizina 25mg R$ 23,14
Mesalazina 800mg R$ 56,65
Levetiracetam 250mg R$ 16,64
Olmesartana 20 Mg R$ 10,97
Olmesartana 40 Mg R$ 13,60
Olmesartana hct 20/12,5 R$ 17,75
Olmesartana hct 40/12,5 R$ 19,67
Olmesartana hct 40/25 R$ 18,01
Clotrimazol vaginal 10 Mg R$ 15,54
Clotrimazol vaginal 20 Mg R$ 15,82
Trimetazidina 35 Mg R$ 27,43
Tansulosina R$ 52,17
Desvenlaflaxina 100mg R$ 25,81
Sibutramina 15mg R$ 8,60"""

async def main():
    print("=" * 70)
    print("ANALISE GERMED — FLUXO DETERMINISTICO")
    print("=" * 70)
    print()

    # 1. Carregar arquivo
    with open(XLSX_PATH, "rb") as f:
        file_bytes = f.read()

    t0 = time.time()
    rows = parse_uploaded_file(file_bytes, "Entradas.xlsx")
    t_parse = time.time() - t0
    print(f"Arquivo carregado: {len(rows):,} registros em {t_parse:.1f}s")

    # 2. Extrair itens
    t0 = time.time()
    fornecedor, itens = await extrair_itens(OFERTA)
    t_extract = time.time() - t0
    print(f"Itens extraidos: {len(itens)} em {t_extract*1000:.0f}ms")

    # 3. Construir indice
    t0 = time.time()
    ean_stats, token_index = construir_indice_arquivo(rows)
    t_index = time.time() - t0
    print(f"Indice: {len(ean_stats):,} EANs, {len(token_index):,} tokens em {t_index*1000:.0f}ms")

    # 4. Analise
    t0 = time.time()
    resultado = executar_analise_deterministico(
        itens_extraidos=itens,
        fornecedor=fornecedor,
        ean_stats=ean_stats,
        token_index=token_index,
        total_registros=len(rows),
    )
    t_analise = time.time() - t0
    print(f"Analise: {len(resultado['itens'])} itens em {t_analise*1000:.0f}ms")
    print()

    # ─── Separar por classificacao ───────────────────────────────────────────
    ouro     = [i for i in resultado["itens"] if i["classificacao"] == "ouro"]
    prata    = [i for i in resultado["itens"] if i["classificacao"] == "prata"]
    atencao  = [i for i in resultado["itens"] if i["classificacao"] == "atencao"]
    desc     = [i for i in resultado["itens"] if i["classificacao"] == "descartavel"]
    sem_hist = [i for i in desc if i.get("descricao_produto") is None]

    # ─── OURO ────────────────────────────────────────────────────────────────
    if ouro:
        print("=" * 70)
        print("OURO — COMPRAR AGORA")
        print("=" * 70)
        for i in sorted(ouro, key=lambda x: x["variacao_percentual"] or 0, reverse=True):
            print(f"\n{i['descricao_original']}")
            print(f"  Preco oferta:  R${i['preco_oferta']:.2f}")
            print(f"  Match:         {i['descricao_produto']}")
            print(f"  Menor hist:    R${i['menor_historico']:.2f}")
            print(f"  DESCONTO:      {i['variacao_percentual']:.1f}%")
            print(f"  Demanda/mes:   {i['demanda_mes']:.1f} un/mes")
            print(f"  Sugestao:      {i['sugestao_pedido']} un (3 meses)")
            print(f"  Confianca:     {i['confianca_match']}")
            print(f"  -> {i['recomendacao']}")

    # ─── PRATA ───────────────────────────────────────────────────────────────
    if prata:
        print()
        print("=" * 70)
        print("PRATA — BOA OPORTUNIDADE")
        print("=" * 70)
        for i in sorted(prata, key=lambda x: x["variacao_percentual"] or 0, reverse=True):
            print(f"\n{i['descricao_original']}")
            print(f"  Preco oferta:  R${i['preco_oferta']:.2f}")
            print(f"  Match:         {i['descricao_produto']}")
            print(f"  Menor hist:    R${i['menor_historico']:.2f}")
            print(f"  DESCONTO:      {i['variacao_percentual']:.1f}%")
            print(f"  Demanda/mes:   {i['demanda_mes']:.1f} un/mes")
            print(f"  Sugestao:      {i['sugestao_pedido']} un")
            print(f"  -> {i['recomendacao']}")

    # ─── ATENCAO ─────────────────────────────────────────────────────────────
    if atencao:
        print()
        print("=" * 70)
        print("ATENCAO — AVALIAR")
        print("=" * 70)
        for i in atencao:
            print(f"\n{i['descricao_original']}")
            print(f"  Preco oferta:  R${i['preco_oferta']:.2f}  |  Menor hist: R${i.get('menor_historico', 0):.2f}")
            print(f"  Desconto:      {i['variacao_percentual']:.1f}%")
            print(f"  -> {i['recomendacao']}")

    # ─── DESCARTAVEL (com match) ──────────────────────────────────────────────
    desc_com_match = [i for i in desc if i.get("descricao_produto")]
    if desc_com_match:
        print()
        print("=" * 70)
        print("DESCARTAVEL — PRECO ACIMA DO HISTORICO")
        print("=" * 70)
        for i in sorted(desc_com_match, key=lambda x: x["variacao_percentual"] or 0, reverse=True):
            print(f"\n{i['descricao_original']}")
            print(f"  Preco oferta:  R${i['preco_oferta']:.2f}  |  Menor hist: R${i.get('menor_historico', 0):.2f}")
            print(f"  Agio:          {abs(i['variacao_percentual']):.1f}% acima do historico")

    # ─── SEM HISTORICO ───────────────────────────────────────────────────────
    if sem_hist:
        print()
        print("=" * 70)
        print("SEM HISTORICO — PRODUTO NAO COMPRADO ANTES")
        print("=" * 70)
        for i in sem_hist:
            print(f"  - {i['descricao_original']} R${i['preco_oferta']:.2f}")

    # ─── RESUMO FINAL ────────────────────────────────────────────────────────
    print()
    print("=" * 70)
    print("RESUMO EXECUTIVO")
    print("=" * 70)
    total_itens = len(resultado["itens"])
    total_matched = sum(1 for i in resultado["itens"] if i.get("descricao_produto"))
    print(f"Total itens analisados:  {total_itens}")
    print(f"Matches encontrados:     {total_matched}/{total_itens}")
    print(f"Classificacao:")
    print(f"  OURO (comprar agora):  {len(ouro)}")
    print(f"  PRATA (boa oferta):    {len(prata)}")
    print(f"  ATENCAO (avaliar):     {len(atencao)}")
    print(f"  DESCARTAVEL:           {len(desc)}")
    print()
    if ouro:
        print("TOP OPORTUNIDADES:")
        for i in sorted(ouro, key=lambda x: x["variacao_percentual"] or 0, reverse=True)[:5]:
            print(f"  {i['descricao_original'][:45]:45} {i['variacao_percentual']:.1f}% -> sugestao {i['sugestao_pedido']} un")
    print()
    print(f"Performance: Parse={t_parse:.1f}s | Extracao={t_extract*1000:.0f}ms | Analise={t_analise*1000:.0f}ms")
    print(f"Custo LLM: R$0.00 (100% deterministico)")

asyncio.run(main())
