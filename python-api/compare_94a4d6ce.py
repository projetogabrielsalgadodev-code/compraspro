"""
Fetch analysis 94a4d6ce from DB and run local analysis, then compare.
"""
import asyncio
import json
import sys
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ANALISE_ID = "94a4d6ce-bf5b-468a-83dd-14d5ae0c51cd"
FILE_PATH = r"c:\Users\JoãoVictorRibeiroLag\Documents\Projetos Highcode\Projeto Gabriel Salgado\Projeto ComprasPRO\Entradas 01012025 a 15032026 diarias clean.xlsx"

OFERTA = """
NEOSORO SOL ADULTO C/30ML = 2,89
DORFLEX C/36CPR = 17,99
SAL DE FRUTA SACHE 30X2 = 92,99
SAL DE FRUTA 100GRS = 19,29
DORFLEX HOSPITALAR C/300CPR 30X10 = 179,90
HISTAMIN XAROPE 100ML = 8,59
HISTAMIN 2MG C/20CPR = 3,79
NEOSALDINA C/20CPR = 24,99
LACTO-PURGA C/150CPR 25X6 = 113,99
ATORVASTATINA 40MG C/30CPR = 11,79
CELESTRAT XAROPE 100ML = 7,99
RAPILAX GTS 30ML = 10,59
HISTAMIN XAROPE 100ML = 8,59
CETOPROFENO 150MG C/ 10CPR EMS = 4,59
CYSTEC C/24CPR = 27,99
NEOLEFRIN DIA C/20CPR = 5,49
NEOLEFRIN NOITE C/20CPR = 5,99
SALICETIL 100MG C/200CPR 20X10 = 11,59
ALBENDAZOL 400MG C/1CPR = 1,49
DESLORATADINA XAROPE 0,5MG/ML C/60ML = 6,39
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

    with open("analise_94a4d6ce_db.json", "w", encoding="utf-8") as f:
        json.dump(db_result, f, ensure_ascii=False, indent=2)

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

    # Show extracted items with their multipliers
    print("\n--- Itens extraidos (LLM) ---")
    for i, item in enumerate(itens_extraidos):
        print(f"  {i+1}. {item.get('descricao')} | preco={item.get('preco')} | mult={item.get('multiplicador_embalagem', 1.0)}")

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

    # ══════════ STEP 3: Compare ══════════
    print("\n" + "=" * 100)
    print("STEP 3: COMPARISON - DB (94a4d6ce) vs LOCAL")
    print("=" * 100)

    db_by_desc = {}
    for item in db_itens:
        desc = item.get("descricao_original", "")
        db_by_desc[desc.upper().strip()] = item

    issues = []
    ok_count = 0
    total_fields = 0

    for local_item in local_itens:
        desc_local = local_item.get("descricao_original", "")
        desc_key = desc_local.upper().strip()

        db_item = db_by_desc.get(desc_key)

        print(f"\n{'─' * 90}")
        print(f"PRODUTO: {desc_local}")

        if not db_item:
            print(f"  [!] NAO ENCONTRADO NO DB")
            # Try partial match
            for db_desc, db_i in db_by_desc.items():
                if desc_key[:15] in db_desc or db_desc[:15] in desc_key:
                    print(f"  [~] Possible match: '{db_desc}'")
                    db_item = db_i
                    break
            if not db_item:
                issues.append(f"{desc_local}: nao encontrado no DB")
                print(f"  LOCAL: preco_oferta={local_item.get('preco_oferta')} | "
                      f"menor_hist={local_item.get('menor_historico')} | "
                      f"var={local_item.get('variacao_percentual')}% | "
                      f"class={local_item.get('classificacao')}")
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

        # Show match description differences
        db_match_desc = db_item.get("descricao_produto", "")
        local_match_desc = local_item.get("descricao_produto", "")
        if db_match_desc != local_match_desc:
            print(f"  {'descricao_produto':30s}: DB={db_match_desc}")
            print(f"  {'':30s}  LOCAL={local_match_desc}")

        # Show equivalents if present
        local_equivs = local_item.get("equivalentes", [])
        if local_equivs:
            print(f"  Equivalentes LOCAL ({len(local_equivs)}):")
            for eq in local_equivs[:3]:
                print(f"    - {eq.get('descricao', 'N/A')} | menor={eq.get('menor_preco', 'N/A')}")

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
        print("\n*** TODOS OS CAMPOS SAO IDENTICOS! Os fixes funcionaram perfeitamente. ***")

    # ══════════ Sanity Checks ══════════
    print("\n" + "=" * 100)
    print("SANITY CHECKS (validade dos resultados)")
    print("=" * 100)

    sanity_issues = []
    for item in local_itens:
        desc = item.get("descricao_original", "")
        preco = item.get("preco_oferta")
        menor = item.get("menor_historico")
        var = item.get("variacao_percentual")
        classif = item.get("classificacao")
        match_desc = item.get("descricao_produto")

        # Check 1: CELESTRAT should NOT match DIPIRONA
        if "CELESTRAT" in desc.upper() and match_desc and "DIPIRONA" in match_desc.upper():
            sanity_issues.append(f"{desc}: CELESTRAT nao deveria dar match com DIPIRONA!")

        # Check 2: HISTAMIN XAROPE should match HISTAMIN, not DIPIRONA
        if "HISTAMIN" in desc.upper() and "XAROPE" in desc.upper():
            if match_desc and "DIPIRONA" in match_desc.upper():
                sanity_issues.append(f"{desc}: HISTAMIN XAROPE nao deveria dar match com DIPIRONA!")
            elif match_desc and "HISTAMIN" in match_desc.upper():
                print(f"  [PASS] {desc} -> {match_desc}")

        # Check 3: DESLORATADINA XAROPE should match DESLORATADINA XAROPE, not COMP
        if "DESLORATADINA" in desc.upper() and "XAROPE" in desc.upper():
            if match_desc and "COMP" in match_desc.upper():
                sanity_issues.append(f"{desc}: DESLORATADINA XAROPE nao deveria match com COMP!")
            elif match_desc and "XAROPE" in match_desc.upper():
                print(f"  [PASS] {desc} -> {match_desc}")

        # Check 4: SAL DE FRUTA 100GRS - category should be 'po', not sachê mix
        if "SAL DE FRUTA" in desc.upper() and "100G" in desc.upper():
            if menor and menor < 5:
                sanity_issues.append(f"{desc}: menor_historico={menor} muito baixo (sachê vazou?)")
            else:
                print(f"  [PASS] {desc}: menor_historico={menor} (OK para po)")

        # Check 5: Liquids should have mult=1 (price per bottle)
        if preco and preco > 50 and "XAROPE" in desc.upper():
            sanity_issues.append(f"{desc}: preco_oferta={preco} > 50 para xarope (multiplicador errado?)")

    if sanity_issues:
        print("\n[FALHA] Problemas de sanidade detectados:")
        for s in sanity_issues:
            print(f"  - {s}")
    else:
        print("\n*** TODOS OS SANITY CHECKS PASSARAM! ***")

if __name__ == "__main__":
    asyncio.run(main())
