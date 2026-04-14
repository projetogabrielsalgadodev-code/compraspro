"""
Re-importa dados de entradas (historico_precos) diretamente no Supabase
com os campos corretos: quantidade_unitaria > 0.

preco_unitario é uma coluna GENERATED ALWAYS AS (valor_total_item / NULLIF(quantidade_unitaria, 0))
então basta inserir quantidade_unitaria correto e o preco_unitario será calculado automaticamente.
"""
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict

import openpyxl
from supabase import create_client

# Config
SUPABASE_URL = "https://hiaomhjxdmixblovvfpb.supabase.co"
SUPABASE_SERVICE_ROLE = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhpYW9taGp4ZG1peGJsb3Z2ZnBiIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3Mzg4MDkxNSwiZXhwIjoyMDg5NDU2OTE1fQ.at_5Y_Zore26B_QgIKnDDtGEGj3uuIFRaMX-pMUz8sU")

EMPRESA_ID = "11111111-1111-1111-1111-111111111111"
XLSX_PATH = os.path.join(os.path.dirname(__file__), "..", "Entradas 01012025 a 15032026 diarias clean.xlsx")

BATCH_SIZE = 300


def main():
    print("=== Re-import Histórico de Preços (v2) ===\n")
    
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE)
    
    # 1. Read spreadsheet
    print("1. Lendo planilha...")
    wb = openpyxl.load_workbook(XLSX_PATH, read_only=True)
    ws = wb.active
    
    entries = []
    by_ean = defaultdict(list)
    
    for row in ws.iter_rows(min_row=5):
        vals = [cell.value for cell in row]
        ean = vals[2]
        if not ean or not str(ean).strip():
            continue
        
        ean = str(ean).strip()
        descricao = str(vals[3] or "").strip()
        
        data = vals[0]
        if isinstance(data, datetime):
            data_str = data.strftime("%Y-%m-%d")
        elif data:
            data_str = str(data)[:10]
        else:
            continue
        
        qtde = float(vals[6] or 0)
        icms_st = float(vals[7] or 0)
        outras_desp = float(vals[8] or 0)
        valor_total = float(vals[9] or 0)
        
        # Garantir quantidade > 0
        if qtde <= 0:
            qtde = 1.0
        
        entry = {
            "empresa_id": EMPRESA_ID,
            "ean": ean,
            "data_entrada": data_str,
            "quantidade_unitaria": qtde,
            "valor_total_item": valor_total,
            "valor_icms_st": icms_st,
            "valor_outras_despesas": outras_desp,
            # preco_unitario é GENERATED — não incluir!
        }
        entries.append(entry)
        
        # Track for product stats 
        by_ean[ean].append({
            "descricao": descricao,
            "data_entrada": data_str,
            "quantidade_unitaria": qtde,
            "valor_total_item": valor_total,
        })
    
    wb.close()
    print(f"   {len(entries)} registros lidos, {len(by_ean)} EANs únicos")
    
    # 2. Insert historico_precos in batches
    print("\n2. Inserindo historico_precos em batches...")
    total_inserted = 0
    errors = 0
    for i in range(0, len(entries), BATCH_SIZE):
        batch = entries[i:i+BATCH_SIZE]
        try:
            supabase.table("historico_precos").insert(batch).execute()
            total_inserted += len(batch)
        except Exception as e:
            errors += 1
            print(f"   ERRO no batch {i//BATCH_SIZE}: {str(e)[:100]}")
            # Try smaller batches
            for entry in batch:
                try:
                    supabase.table("historico_precos").insert(entry).execute()
                    total_inserted += 1
                except Exception as e2:
                    print(f"   Falhou EAN {entry['ean']}: {str(e2)[:80]}")
        
        if (i // BATCH_SIZE) % 20 == 0:
            print(f"   ... {total_inserted}/{len(entries)} ({errors} erros)")
    
    print(f"\n   Total inserido: {total_inserted}/{len(entries)}")
    
    # 3. Calculate demanda_mes for each product
    print("\n3. Calculando e atualizando demanda_mes dos produtos...")
    
    all_dates = [e["data_entrada"] for e in by_ean[list(by_ean.keys())[0]]]
    for ean_entries_list in by_ean.values():
        for e in ean_entries_list:
            all_dates.append(e["data_entrada"])
    
    max_date = max(all_dates)
    min_date = min(all_dates)
    max_dt = datetime.strptime(max_date, "%Y-%m-%d")
    min_dt = datetime.strptime(min_date, "%Y-%m-%d")
    months = max(1, (max_dt - min_dt).days / 30)
    
    print(f"   Período: {min_date} a {max_date} ({months:.1f} meses)")
    
    updated = 0
    for ean, ean_entries_list in by_ean.items():
        total_qtde = sum(e["quantidade_unitaria"] for e in ean_entries_list)
        demanda_mes = round(total_qtde / months, 1)
        
        # Estoque: entradas dos últimos 30 dias
        cutoff = (max_dt - timedelta(days=30)).strftime("%Y-%m-%d")
        recentes = [e for e in ean_entries_list if e["data_entrada"] >= cutoff]
        estoque = sum(int(e["quantidade_unitaria"]) for e in recentes)
        
        try:
            supabase.table("produtos").update({
                "estoque": estoque,
                "demanda_mes": demanda_mes,
            }).eq("empresa_id", EMPRESA_ID).eq("ean", ean).execute()
            updated += 1
        except Exception as e:
            pass  # produto pode não existir
        
        if updated % 1000 == 0 and updated > 0:
            print(f"   ... {updated}/{len(by_ean)} produtos atualizados")
    
    print(f"   Total produtos atualizados: {updated}")
    
    # 4. Verify
    print("\n4. Verificação...")
    check_eans = ["7896004729688", "7896714292489", "7891317029272"]
    for ean in check_eans:
        result = supabase.table("historico_precos").select("ean, preco_unitario, quantidade_unitaria, valor_total_item, data_entrada").eq("empresa_id", EMPRESA_ID).eq("ean", ean).order("data_entrada", desc=True).limit(3).execute()
        print(f"\n   EAN {ean} - Histórico:")
        for r in (result.data or []):
            pu = r.get('preco_unitario')
            pu_str = f"R${float(pu):.4f}" if pu else "NULL"
            print(f"     {r['data_entrada']}: R${float(r['valor_total_item']):.2f} / {float(r['quantidade_unitaria']):.0f}un = {pu_str}/un")
        
        result2 = supabase.table("produtos").select("ean, descricao, estoque, demanda_mes").eq("empresa_id", EMPRESA_ID).eq("ean", ean).limit(1).execute()
        if result2.data:
            p = result2.data[0]
            print(f"     Produto: {p['descricao']} | estoque={p['estoque']} | demanda_mes={p['demanda_mes']}")
    
    print("\n=== Concluído! ===")


if __name__ == "__main__":
    main()
