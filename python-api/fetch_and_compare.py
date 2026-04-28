"""
Fetch analysis 44a93f2f from DB and run local analysis, then compare.
"""
import asyncio
import json
import sys
import time

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ANALISE_ID = "44a93f2f-5911-487f-87b2-1b2659ac70e5"
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
    # ═══════ STEP 1: Fetch from DB ═══════
    print("=" * 100)
    print("STEP 1: Fetching analysis from database...")
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

    # Save full DB result for reference
    with open("analise_44a93f2f_db.json", "w", encoding="utf-8") as f:
        json.dump(db_result, f, ensure_ascii=False, indent=2)

    # ═══════ STEP 2: Run local analysis ═══════
    print("\n" + "=" * 100)
    print("STEP 2: Running LOCAL analysis...")
    print("=" * 100)

    from app.services.offer_extractor import extrair_itens
    from app.services.analysis_engine import construir_indice_arquivo, executar_analise_deterministico
    from app.services.file_parser import parse_uploaded_file

    # Parse file
    with open(FILE_PATH, "rb") as f:
        file_bytes = f.read()
    rows = parse_uploaded_file(file_bytes, "entradas.xlsx")
    print(f"File parsed: {len(rows)} rows")

    # Extract items from offer
    fornecedor, itens_extraidos = await extrair_itens(OFERTA)
    print(f"Extracted: {len(itens_extraidos)} items, fornecedor={fornecedor}")

    # Build index
    ean_stats, token_index = construir_indice_arquivo(rows)
    print(f"Index: {len(ean_stats)} EANs, {len(token_index)} tokens")

    # Run deterministic analysis
    resultado_local = executar_analise_deterministico(
        itens_extraidos=itens_extraidos,
        fornecedor=fornecedor,
        ean_stats=ean_stats,
        token_index=token_index,
        total_registros=len(rows),
    )
    local_itens = resultado_local.get("itens", [])
    print(f"Local items: {len(local_itens)}")

    # ═══════ STEP 3: Compare ═══════
    print("\n" + "=" * 100)
    print("STEP 3: COMPARISON - DB vs LOCAL")
    print("=" * 100)

    # Build lookup by descricao_original for DB items
    db_by_desc = {}
    for item in db_itens:
        desc = item.get("descricao_original", "")
        db_by_desc[desc.upper().strip()] = item

    issues = []
    for local_item in local_itens:
        desc_local = local_item.get("descricao_original", "")
        desc_key = desc_local.upper().strip()

        # Find matching DB item
        db_item = db_by_desc.get(desc_key)

        print(f"\n{'─' * 90}")
        print(f"PRODUTO: {desc_local}")

        if not db_item:
            print(f"  [!] NAO ENCONTRADO NO DB")
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

            if decimals is not None:
                # Numeric comparison
                local_num = round(float(local_val or 0), decimals)
                db_num = round(float(db_val or 0), decimals)
                match = abs(local_num - db_num) < (10 ** -decimals)
                symbol = "OK" if match else "DIFF"
                print(f"  {field:30s}: DB={db_num:12.{decimals}f} | LOCAL={local_num:12.{decimals}f} [{symbol}]")
                if not match:
                    issues.append(f"{desc_local}: {field} DB={db_num} vs LOCAL={local_num}")
            else:
                match = str(local_val) == str(db_val)
                symbol = "OK" if match else "DIFF"
                print(f"  {field:30s}: DB={str(db_val):>12s} | LOCAL={str(local_val):>12s} [{symbol}]")
                if not match:
                    issues.append(f"{desc_local}: {field} DB={db_val} vs LOCAL={local_val}")

        # Show match descriptions
        db_match = db_item.get("descricao_produto", "")
        local_match = local_item.get("descricao_produto", "")
        if db_match != local_match:
            print(f"  {'descricao_produto':30s}: DB={db_match}")
            print(f"  {'':30s}  LOCAL={local_match}")

    # ═══════ Summary ═══════
    print("\n" + "=" * 100)
    print(f"RESUMO: {len(issues)} divergencias encontradas")
    print("=" * 100)
    for i, issue in enumerate(issues, 1):
        print(f"  {i}. {issue}")

if __name__ == "__main__":
    asyncio.run(main())
