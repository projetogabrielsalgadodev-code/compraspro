"""
Teste v2: Analise Germed com extrator LLM + equivalentes + desconto %.
"""
import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "python-api"))

from app.services.file_parser import parse_uploaded_file
from app.services.offer_extractor import extrair_itens, extrair_itens_regex, sanitizar_texto_oferta
from app.services.analysis_engine import (
    construir_indice_arquivo,
    executar_analise_deterministico,
)

XLSX_PATH = r"c:\Users\JoãoVictorRibeiroLag\Documents\Projetos Highcode\Projeto Gabriel Salgado\Projeto ComprasPRO\Entradas 01012025 a 15032026 diarias clean.xlsx"

# A oferta COMPLETA com todos os formatos
OFERTA = """Germed

Acetilcisteina 600 mg - R$ 13,41
Pedido minimo: 6 unidades

Amoxicilina + Clavulanato 875/125 mg 14 com- R$ 28,57
Pedido minimo: 3 unidades

Duloxetina 60 mg - R$ 36,00
Pedido minimo: 4 unidades

Tramadol 100 mg - R$ 34,18
Pedido minimo: 2 unidades

Duloxetina 30 mg - R$ 22,40
Pedido minimo: 4 unidades

Dicloridrato de Hidroxizina 25 mg - R$ 24,17
Pedido minimo: 4 unidades

Nitazoxanida 500 mg - R$ 9,58
Pedido minimo: 10 unidades

Olmesartana + Anlodipino 40/5 mg - R$ 24,54
Pedido minimo: 3 unidades

Paracetamol + Pseudoefedrina 500/30 mg - R$ 9,37
Pedido minimo: 8 unidades

Prednisona 20 mg - R$ 2,21
Pedido minimo: 36 unidades

Pregabalina 75 mg - R$ 4,24
Pedido minimo: 18 unidades

Trometamol Cetorolaco 10 mg Sublingual - R$ 3,75
Pedido minimo: 18 unidades


GERMED
Amoxi clavi 400 Mg suspensao
->13,45

Bilastina 20/30
->26,45

Ondasetrona
->4 Mg 3,17
->8 Mg 5,55

Hidroxizina 25/30
->23,14

Mesalazina 800/30
->56,65

Levetiracetam 250/30
->16,64

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

Trimetazidina 35 Mg/60
->27,43

Certo beta neo CR
->6,99

Tansulosina C/60
->52,17

Desvenlaflaxina 100/30
->25,81

Sibutramina 15/30
->8,60


Rebaixa Linha Luftal
Desconto 20%

Luftal 75mg GTS 15ml
Luftal 75mg GTS 30ml
Luftal inf 75mg GTS 15ml
Luftal inf 75mg GTS 30ml
Luftal max 125mg 10cps
Luftal max 150mg GTS 15ml
Luftal max 250mg gel 10cps


LIVE HOJE COM MAIORES DESCONTOS DO MES

BENEGRIP 30%
BIOTONICO 15%
BUSCOFEM 20%
BUSCOPAN 15%
CORISTINA 33%
ENGOV 30%
ENGOV AFTER 25%
ENGOV UP 50%
EPOCLER 25%
ESTOMAZIL 14%
GASTROL 30%
LACTO PURGA 15%
NEBACETIN 20%
NEOSALDINA 26%
NEOSALDINA MUSCULAR 30%
POLARAMINE 25%
APRACUR 30%
DORIL 28%
HUMECTOL 20%
MARACUGINA 22%
NATURETTI 25%
NENE DENT 22%
AAS 20%
ADDERA 25%
ADTIL GTS 15%
ALEKTOS 25%
ALIVIUM 25%
AMOME 25%
ATURGYL 20%
BUCLINA 15%
COLFLEX 15%
DESCON 25%
DIPROSPAN 20%
DRAMIN 20%
ECOXE 20%
HEXOMEDINE 20%
LISADOR 25%
MAXSULID 20%
MELATONUM 20%
NESINA 18%
ONDIF 20%
PREDSIM 25%
QUADRIDERM 20%
RINOSORO 25%
UNYCA 15%
VENALOT 15%
DIPROGENTA 10%
EPISOL EPIDRAT IVY C 18%"""


async def main():
    print("=" * 70)
    print("ANALISE GERMED v2 - LLM Extractor + Equivalentes")
    print("=" * 70)
    print()

    # 1. Carregar arquivo
    with open(XLSX_PATH, "rb") as f:
        file_bytes = f.read()

    t0 = time.time()
    rows = parse_uploaded_file(file_bytes, "Entradas.xlsx")
    t_parse = time.time() - t0
    print(f"[1] Arquivo carregado: {len(rows):,} registros em {t_parse:.1f}s")

    # 2. Extrair itens via LLM
    t0 = time.time()
    fornecedor, itens = await extrair_itens(OFERTA)
    t_extract = time.time() - t0
    print(f"[2] LLM extraiu: {len(itens)} itens em {t_extract:.1f}s")
    print(f"    Fornecedor: {fornecedor}")

    # Contagens por tipo
    abs_count = sum(1 for i in itens if i.get("tipo_preco") == "absoluto")
    pct_count = sum(1 for i in itens if i.get("tipo_preco") == "percentual_desconto")
    sem_count = sum(1 for i in itens if i.get("tipo_preco") == "sem_preco")
    print(f"    Tipos: {abs_count} absolutos, {pct_count} desconto%, {sem_count} sem preco")

    # 3. Construir indice
    t0 = time.time()
    ean_stats, token_index = construir_indice_arquivo(rows)
    t_index = time.time() - t0
    print(f"[3] Indice: {len(ean_stats):,} EANs, {len(token_index):,} tokens em {t_index*1000:.0f}ms")

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
    print(f"[4] Analise: {len(resultado['itens'])} itens em {t_analise*1000:.0f}ms")
    print()

    # ─── Separar por classificacao ────────────────────────────────────────────
    ouro = [i for i in resultado["itens"] if i["classificacao"] == "ouro"]
    prata = [i for i in resultado["itens"] if i["classificacao"] == "prata"]
    atencao = [i for i in resultado["itens"] if i["classificacao"] == "atencao"]
    desc = [i for i in resultado["itens"] if i["classificacao"] == "descartavel"]

    # ─── OURO ─────────────────────────────────────────────────────────────────
    if ouro:
        print("=" * 70)
        print(f"OURO - COMPRAR AGORA ({len(ouro)} itens)")
        print("=" * 70)
        for i in sorted(ouro, key=lambda x: x["variacao_percentual"] or 0, reverse=True):
            tipo_tag = f" [{i.get('tipo_preco','abs')}]" if i.get("tipo_preco") != "absoluto" else ""
            orig = i.get("origem_menor_historico", "=")
            print(f"\n  {i['descricao_original']}{tipo_tag}")
            if i.get("preco_oferta"):
                print(f"    Oferta: R${i['preco_oferta']:.2f}")
            elif i.get("desconto_percentual"):
                print(f"    Desconto: {i['desconto_percentual']:.0f}%")
            if i.get("descricao_produto"):
                print(f"    Match: {i['descricao_produto']}")
            if i.get("menor_historico"):
                print(f"    Menor hist: R${i['menor_historico']:.2f} ({orig})")
            print(f"    Variacao: {i['variacao_percentual']:.1f}% | Sugestao: {i['sugestao_pedido']} un")
            if i.get("equivalentes"):
                print(f"    Equivalentes ({len(i['equivalentes'])}): ", end="")
                print(", ".join(e["descricao"][:30] for e in i["equivalentes"][:3]))

    # ─── PRATA ────────────────────────────────────────────────────────────────
    if prata:
        print()
        print("=" * 70)
        print(f"PRATA - BOA OPORTUNIDADE ({len(prata)} itens)")
        print("=" * 70)
        for i in sorted(prata, key=lambda x: x["variacao_percentual"] or 0, reverse=True):
            orig = i.get("origem_menor_historico", "=")
            print(f"\n  {i['descricao_original']}")
            if i.get("preco_oferta"):
                print(f"    Oferta: R${i['preco_oferta']:.2f} | Menor hist: R${i.get('menor_historico',0):.2f} ({orig}) | Var: {i['variacao_percentual']:.1f}%")
            elif i.get("desconto_percentual"):
                print(f"    Desconto: {i['desconto_percentual']:.0f}% | Menor hist: R${i.get('menor_historico',0):.2f}")
            if i.get("equivalentes"):
                print(f"    Equivalentes ({len(i['equivalentes'])}): ", end="")
                print(", ".join(e["descricao"][:30] for e in i["equivalentes"][:3]))

    # ─── ATENCAO ──────────────────────────────────────────────────────────────
    if atencao:
        print()
        print("=" * 70)
        print(f"ATENCAO - AVALIAR ({len(atencao)} itens)")
        print("=" * 70)
        for i in atencao:
            print(f"  {i['descricao_original']} | {i.get('variacao_percentual',0):.1f}%")

    # ─── DESCARTAVEL ──────────────────────────────────────────────────────────
    desc_com = [i for i in desc if i.get("descricao_produto")]
    desc_sem = [i for i in desc if not i.get("descricao_produto") and not i.get("equivalentes")]
    desc_equiv = [i for i in desc if not i.get("descricao_produto") and i.get("equivalentes")]
    if desc_com:
        print()
        print("=" * 70)
        print(f"DESCARTAVEL - PRECO ACIMA ({len(desc_com)} itens)")
        print("=" * 70)
        for i in desc_com:
            print(f"  {i['descricao_original']} | Oferta R${i.get('preco_oferta',0):.2f} vs Hist R${i.get('menor_historico',0):.2f}")
    if desc_equiv:
        print()
        print(f"SEM MATCH DIRETO (com equivalentes): {len(desc_equiv)} itens")
        for i in desc_equiv:
            eq_names = ", ".join(e["descricao"][:25] for e in i["equivalentes"][:2])
            print(f"  {i['descricao_original']} -> Equiv: {eq_names}")
    if desc_sem:
        print()
        print(f"SEM HISTORICO: {len(desc_sem)} itens")
        for i in desc_sem:
            print(f"  {i['descricao_original']}")

    # ─── RESUMO ───────────────────────────────────────────────────────────────
    print()
    print("=" * 70)
    print("RESUMO EXECUTIVO")
    print("=" * 70)
    total = len(resultado["itens"])
    matched = sum(1 for i in resultado["itens"] if i.get("descricao_produto"))
    com_equiv = sum(1 for i in resultado["itens"] if i.get("equivalentes"))
    print(f"Total itens:            {total}")
    print(f"Matches diretos:        {matched}/{total}")
    print(f"Com equivalentes:       {com_equiv}/{total}")
    print(f"Classificacao:")
    print(f"  OURO:     {len(ouro)}")
    print(f"  PRATA:    {len(prata)}")
    print(f"  ATENCAO:  {len(atencao)}")
    print(f"  DESC:     {len(desc)}")
    print(f"\nPerformance: Parse={t_parse:.1f}s | LLM={t_extract:.1f}s | Analise={t_analise*1000:.0f}ms")


asyncio.run(main())
