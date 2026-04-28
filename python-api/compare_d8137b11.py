"""
Fetch analysis d8137b11 from DB and run local analysis, then compare.
"""
import asyncio
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ANALISE_ID = "d8137b11-3ab5-477e-8a78-8526719a3dd3"
FILE_PATH = r"c:\Users\JoãoVictorRibeiroLag\Documents\Projetos Highcode\Projeto Gabriel Salgado\Projeto ComprasPRO\Entradas 01012025 a 15032026 diarias clean.xlsx"

OFERTA = """Germed

Acetilcisteina 600 mg - R$ 13,41
Pedido minimo: 6 unidades

Amoxicilina + Clavulanato 875/125 mg 14 com - R$ 28,57
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
13,45

Bilastina 20/30
26,45

Ondasetrona
4 Mg 3,17
8 Mg 5,55

Hidroxizina 25/30
23,14

Mesalazina 800/30
56,65

Levetiracetam 250/30
16,64

Olmesartana
20 Mg 10,97
40 Mg 13,60

Olmesartana hct
20/12,5 17,75
40/12,5 19,67
40/25 18,01

Clotrimazol vag
10 Mg C/6 aplic 15,54
20 Mg C/3 aplic 15,82

Trimetazidina 35 Mg/60
27,43

Certo beta neo CR
6,99

Tansulosina C/60
52,17

Desvenlaflaxina 100/30
25,81

Sibutramina 15/30
8,60

Rebaixa Linha Luftal 20%

Luftal 75mg GTS 15ml
Luftal 75mg GTS 30ml
Luftal inf 75mg GTS 15ml
Luftal inf 75mg GTS 30ml
Luftal max 125mg 10cps
Luftal max 150mg GTS 15ml
Luftal max 250mg gel 10cps

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
"""


async def main():
    # ══════════ STEP 1: Fetch from DB ══════════
    print("=" * 100)
    print(f"STEP 1: Fetching analysis {ANALISE_ID} from database...")
    print("=" * 100)

    from app.db.supabase_client import get_supabase_client
    client = get_supabase_client()
    response = client.table("analises_oferta").select(
        "id, status, resultado_json, created_at"
    ).eq("id", ANALISE_ID).execute()

    if not response.data:
        print(f"ERROR: Analise {ANALISE_ID} nao encontrada no banco!")
        return

    row = response.data[0]
    print(f"Status: {row['status']}")
    print(f"Created: {row['created_at']}")

    db_result = row.get("resultado_json", {})
    db_itens = db_result.get("itens", [])
    print(f"DB Items count: {len(db_itens)}")

    # Save DB result for reference
    with open("analise_d8137b11_db.json", "w", encoding="utf-8") as f:
        json.dump(db_result, f, ensure_ascii=False, indent=2)

    # Print all DB items for reference
    print("\n--- DB Items ---")
    for i, item in enumerate(db_itens):
        desc = item.get("descricao_original", "N/A")
        preco = item.get("preco_oferta", "N/A")
        menor = item.get("menor_historico", "N/A")
        var = item.get("variacao_percentual", "N/A")
        classif = item.get("classificacao", "N/A")
        conf = item.get("confianca_match", "N/A")
        match_desc = item.get("descricao_produto", "N/A")
        print(f"  {i+1:2d}. {desc:50s} | oferta={preco} | menor={menor} | var={var}% | {classif} | {conf} | match={match_desc}")

    # ══════════ STEP 2: Run local analysis ══════════
    print("\n" + "=" * 100)
    print("STEP 2: Running LOCAL analysis...")
    print("=" * 100)

    from app.services.offer_extractor import extrair_itens
    from app.services.analysis_engine import construir_indice_arquivo, executar_analise_deterministico
    from app.services.file_parser import parse_uploaded_file

    with open(FILE_PATH, "rb") as f:
        file_bytes = f.read()
    rows = parse_uploaded_file(file_bytes, "entradas.xlsx")
    print(f"File parsed: {len(rows)} rows")

    fornecedor, itens_extraidos = await extrair_itens(OFERTA)
    print(f"Extracted: {len(itens_extraidos)} items, fornecedor={fornecedor}")

    print("\n--- Itens extraidos (LLM) ---")
    for i, item in enumerate(itens_extraidos):
        desc = item.get("descricao", "")
        preco = item.get("preco")
        mult = item.get("multiplicador_embalagem", 1.0)
        tipo = item.get("tipo_preco", "absoluto")
        desc_pct = item.get("desconto_percentual")
        print(f"  {i+1:2d}. {desc:50s} | preco={preco} | mult={mult} | tipo={tipo} | desc_pct={desc_pct}")

    ean_stats, token_index = construir_indice_arquivo(rows)
    print(f"\nIndex: {len(ean_stats)} EANs, {len(token_index)} tokens")

    resultado_local = executar_analise_deterministico(
        itens_extraidos=itens_extraidos,
        fornecedor=fornecedor,
        ean_stats=ean_stats,
        token_index=token_index,
        total_registros=len(rows),
    )
    local_itens = resultado_local.get("itens", [])
    print(f"Local items: {len(local_itens)}")

    print("\n--- LOCAL Items ---")
    for i, item in enumerate(local_itens):
        desc = item.get("descricao_original", "N/A")
        preco = item.get("preco_oferta", "N/A")
        menor = item.get("menor_historico", "N/A")
        var = item.get("variacao_percentual", "N/A")
        classif = item.get("classificacao", "N/A")
        conf = item.get("confianca_match", "N/A")
        match_desc = item.get("descricao_produto", "N/A")
        print(f"  {i+1:2d}. {desc:50s} | oferta={preco} | menor={menor} | var={var}% | {classif} | {conf} | match={match_desc}")

    # ══════════ STEP 3: Compare ══════════
    print("\n" + "=" * 100)
    print("STEP 3: COMPARISON - DB (d8137b11) vs LOCAL")
    print("=" * 100)

    # Build index by normalized description
    def normalize(s):
        import re
        s = s.upper().strip()
        s = re.sub(r'[^\w\s]', '', s)
        s = re.sub(r'\s+', ' ', s)
        return s

    db_by_desc = {}
    for item in db_itens:
        desc = item.get("descricao_original", "")
        key = normalize(desc)
        db_by_desc[key] = item

    issues = []
    ok_count = 0
    total_fields = 0

    for local_item in local_itens:
        desc_local = local_item.get("descricao_original", "")
        desc_key = normalize(desc_local)

        db_item = db_by_desc.get(desc_key)

        print(f"\n{'─' * 90}")
        print(f"PRODUTO: {desc_local}")

        if not db_item:
            # Try fuzzy match
            best_match = None
            best_score = 0
            for db_key, db_i in db_by_desc.items():
                # Check for common prefix or substring
                common = len(set(desc_key.split()) & set(db_key.split()))
                if common > best_score and common >= 2:
                    best_score = common
                    best_match = db_i
            
            if best_match:
                db_item = best_match
                print(f"  [~] Fuzzy match: '{db_item.get('descricao_original', '')}'")
            else:
                issues.append(f"{desc_local}: nao encontrado no DB")
                print(f"  [!] NAO ENCONTRADO NO DB")
                print(f"  LOCAL: preco_oferta={local_item.get('preco_oferta')} | "
                      f"menor_hist={local_item.get('menor_historico')} | "
                      f"var={local_item.get('variacao_percentual')}% | "
                      f"class={local_item.get('classificacao')} | "
                      f"match={local_item.get('descricao_produto')}")
                continue

        # Compare key fields
        fields = [
            ("preco_oferta", 4),
            ("menor_historico", 4),
            ("variacao_percentual", 1),
            ("classificacao", None),
            ("confianca_match", None),
        ]

        for field, decimals in fields:
            local_val = local_item.get(field)
            db_val = db_item.get(field)
            total_fields += 1

            if decimals is not None:
                local_num = round(float(local_val or 0), decimals)
                db_num = round(float(db_val or 0), decimals)
                match = abs(local_num - db_num) < (10 ** -decimals)
                symbol = "OK" if match else "DIFF"
                if match:
                    ok_count += 1
                print(f"  {field:30s}: DB={db_num:12.{decimals}f} | LOCAL={local_num:12.{decimals}f} [{symbol}]")
                if not match:
                    issues.append(f"{desc_local}: {field} DB={db_num} vs LOCAL={local_num}")
            else:
                match = str(local_val) == str(db_val)
                symbol = "OK" if match else "DIFF"
                if match:
                    ok_count += 1
                print(f"  {field:30s}: DB={str(db_val):>12s} | LOCAL={str(local_val):>12s} [{symbol}]")
                if not match:
                    issues.append(f"{desc_local}: {field} DB={db_val} vs LOCAL={local_val}")

        # Show match description if different
        db_match = db_item.get("descricao_produto", "")
        local_match = local_item.get("descricao_produto", "")
        if db_match != local_match:
            print(f"  {'descricao_produto':30s}: DB={db_match}")
            print(f"  {'':30s}  LOCAL={local_match}")

    # Check for DB items not in LOCAL
    local_keys = {normalize(it.get("descricao_original", "")) for it in local_itens}
    for db_key, db_item in db_by_desc.items():
        if db_key not in local_keys:
            # Try fuzzy
            found = False
            for lk in local_keys:
                common = len(set(db_key.split()) & set(lk.split()))
                if common >= 2:
                    found = True
                    break
            if not found:
                desc = db_item.get("descricao_original", db_key)
                issues.append(f"{desc}: presente no DB mas NAO no LOCAL")

    # ══════════ Summary ══════════
    print("\n" + "=" * 100)
    pct = round(ok_count / total_fields * 100, 1) if total_fields else 0
    print(f"RESUMO: {ok_count}/{total_fields} campos OK ({pct}%) | {len(issues)} divergencias")
    print("=" * 100)

    if issues:
        print("\nDivergencias encontradas:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
    else:
        print("\n*** TODOS OS CAMPOS SAO IDENTICOS! ***")

    # ══════════ Sanity Checks ══════════
    print("\n" + "=" * 100)
    print("SANITY CHECKS")
    print("=" * 100)

    sanity_issues = []
    for item in local_itens:
        desc = item.get("descricao_original", "").upper()
        preco = item.get("preco_oferta")
        menor = item.get("menor_historico")
        match_desc = (item.get("descricao_produto") or "").upper()

        # Cross-molecule match check
        desc_words = set(desc.split())
        match_words = set(match_desc.split()) if match_desc else set()

        # Specific checks
        if "DULOXETINA" in desc and match_desc and "DULOXETINA" not in match_desc:
            sanity_issues.append(f"DULOXETINA matched incorrectly: {match_desc}")
        if "PREGABALINA" in desc and match_desc and "PREGABALINA" not in match_desc:
            sanity_issues.append(f"PREGABALINA matched incorrectly: {match_desc}")
        if "OLMESARTANA" in desc and match_desc and "OLMESARTANA" not in match_desc and "OLMES" not in match_desc:
            sanity_issues.append(f"OLMESARTANA matched incorrectly: {match_desc}")

        # Price sanity
        if preco and preco < 0:
            sanity_issues.append(f"{desc}: preco negativo={preco}")

        # Check: discount items should have tipo_preco=percentual
        if match_desc and "None" in str(preco):
            sanity_issues.append(f"{desc}: preco is None")

    if sanity_issues:
        print("\n[FALHA] Problemas de sanidade:")
        for s in sanity_issues:
            print(f"  - {s}")
    else:
        print("\n*** TODOS OS SANITY CHECKS PASSARAM! ***")

if __name__ == "__main__":
    asyncio.run(main())
