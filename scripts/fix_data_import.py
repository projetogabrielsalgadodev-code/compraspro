"""
Script para corrigir a importação de dados no Supabase.

Problemas encontrados:
1. historico_precos: quantidade_unitaria=0 e preco_unitario=NULL em todos os 45762 registros
2. produtos: estoque=0, demanda_mes=0, principio_ativo="" em todos os 9060 produtos

Este script:
1. Lê a planilha original  
2. Recalcula os dados corretos
3. Atualiza no Supabase via SQL
"""
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict

import openpyxl

# Configuração
XLSX_PATH = os.path.join(os.path.dirname(__file__), "..", "Entradas 01012025 a 15032026 diarias clean.xlsx")
EMPRESA_ID = "11111111-1111-1111-1111-111111111111"

def load_spreadsheet():
    """Carrega e parseia a planilha de entradas."""
    wb = openpyxl.load_workbook(XLSX_PATH, read_only=True)
    ws = wb.active
    
    entries = []
    for row in ws.iter_rows(min_row=5):
        vals = [cell.value for cell in row]
        
        # Skip empty rows
        ean = vals[2]
        if not ean or not str(ean).strip():
            continue
        
        ean = str(ean).strip()
        descricao = str(vals[3] or "").strip()
        
        # Parse date
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
        
        # Calcular preço unitário
        if qtde > 0:
            preco_unitario = round(valor_total / qtde, 4)
        else:
            preco_unitario = valor_total  # fallback
            
        entries.append({
            "ean": ean,
            "descricao": descricao,
            "data_entrada": data_str,
            "quantidade_unitaria": qtde,
            "valor_total_item": valor_total,
            "valor_icms_st": icms_st,
            "valor_outras_despesas": outras_desp,
            "preco_unitario": preco_unitario,
        })
    
    wb.close()
    return entries


def calculate_product_stats(entries):
    """Calcula estoque e demanda_mes para cada produto baseado nas entradas."""
    # Agrupar por EAN
    by_ean = defaultdict(list)
    for e in entries:
        by_ean[e["ean"]].append(e)
    
    products = {}
    
    # Data de referência: última data da planilha
    all_dates = [e["data_entrada"] for e in entries]
    max_date = max(all_dates)
    min_date = min(all_dates)
    
    # Período total em meses
    max_dt = datetime.strptime(max_date, "%Y-%m-%d")
    min_dt = datetime.strptime(min_date, "%Y-%m-%d")
    months = max(1, (max_dt - min_dt).days / 30)
    
    for ean, ean_entries in by_ean.items():
        # Demanda mensal = total de entradas / meses
        total_qtde = sum(e["quantidade_unitaria"] for e in ean_entries)
        demanda_mes = round(total_qtde / months, 1)
        
        # Estoque estimado: entradas dos últimos 30 dias (simplificado)
        recentes = [e for e in ean_entries if e["data_entrada"] >= (max_dt - timedelta(days=30)).strftime("%Y-%m-%d")]
        estoque = sum(int(e["quantidade_unitaria"]) for e in recentes)
        
        # Descrição mais recente
        ean_entries.sort(key=lambda x: x["data_entrada"], reverse=True)
        descricao = ean_entries[0]["descricao"]
        
        products[ean] = {
            "ean": ean,
            "descricao": descricao,
            "estoque": estoque,
            "demanda_mes": demanda_mes,
        }
    
    print(f"Período: {min_date} a {max_date} ({months:.1f} meses)")
    return products


def generate_sql_updates(entries, products):
    """Gera os comandos SQL para corrigir os dados."""
    
    # 1. SQL para limpar e re-inserir historico_precos
    print(f"\n--- Gerando SQL para {len(entries)} registros de histórico ---")
    
    # Deletar registros existentes
    delete_sql = f"DELETE FROM historico_precos WHERE empresa_id = '{EMPRESA_ID}';\n"
    
    # Inserir com dados corretos (em batches de 500)
    insert_sqls = []
    batch = []
    for i, e in enumerate(entries):
        desc_escaped = e["descricao"].replace("'", "''")
        row = f"('{EMPRESA_ID}', '{e['ean']}', '{e['data_entrada']}', {e['quantidade_unitaria']}, {e['valor_total_item']}, {e['valor_icms_st']}, {e['valor_outras_despesas']}, {e['preco_unitario']})"
        batch.append(row)
        
        if len(batch) >= 500 or i == len(entries) - 1:
            sql = f"INSERT INTO historico_precos (empresa_id, ean, data_entrada, quantidade_unitaria, valor_total_item, valor_icms_st, valor_outras_despesas, preco_unitario) VALUES\n" + ",\n".join(batch) + ";"
            insert_sqls.append(sql)
            batch = []
    
    # 2. SQL para atualizar produtos
    print(f"--- Gerando SQL para {len(products)} produtos ---")
    update_sqls = []
    for ean, p in products.items():
        sql = f"UPDATE produtos SET estoque = {p['estoque']}, demanda_mes = {p['demanda_mes']} WHERE empresa_id = '{EMPRESA_ID}' AND ean = '{ean}';"
        update_sqls.append(sql)
    
    return delete_sql, insert_sqls, update_sqls


def main():
    print("=== Correção de Dados - Compras PRO ===\n")
    
    # 1. Ler planilha
    print("1. Lendo planilha...")
    entries = load_spreadsheet()
    print(f"   {len(entries)} registros carregados")
    
    # 2. Calcular estatísticas dos produtos
    print("2. Calculando estatísticas dos produtos...")
    products = calculate_product_stats(entries)
    print(f"   {len(products)} produtos únicos")
    
    # Exemplos
    sample_eans = ["7896004729688", "7896714292489", "7891317029272"]
    print("\n--- Exemplos de preco_unitario calculado ---")
    for e in entries[:20]:
        if e["ean"] in sample_eans:
            print(f"   EAN {e['ean']}: R${e['valor_total_item']:.2f} / {e['quantidade_unitaria']:.0f} un = R${e['preco_unitario']:.4f}/un ({e['data_entrada']})")
    
    print("\n--- Exemplos de demanda_mes ---")
    for ean in sample_eans:
        if ean in products:
            p = products[ean]
            print(f"   EAN {ean}: estoque={p['estoque']}, demanda_mes={p['demanda_mes']}")
    
    # 3. Gerar SQL
    print("\n3. Gerando SQL...")
    delete_sql, insert_sqls, update_sqls = generate_sql_updates(entries, products)
    
    # Salvar SQL em arquivo
    output_dir = os.path.dirname(__file__)
    
    with open(os.path.join(output_dir, "fix_historico.sql"), "w", encoding="utf-8") as f:
        f.write(f"-- Fix historico_precos: adicionar preco_unitario e quantidade_unitaria\n")
        f.write(f"-- Total: {len(entries)} registros\n\n")
        f.write(delete_sql + "\n")
        for sql in insert_sqls:
            f.write(sql + "\n\n")
    
    with open(os.path.join(output_dir, "fix_produtos.sql"), "w", encoding="utf-8") as f:
        f.write(f"-- Fix produtos: atualizar estoque e demanda_mes\n")
        f.write(f"-- Total: {len(products)} produtos\n\n")
        for sql in update_sqls:
            f.write(sql + "\n")
    
    print(f"   Arquivos SQL salvos em {output_dir}/")
    print(f"   - fix_historico.sql ({len(insert_sqls)} batches)")
    print(f"   - fix_produtos.sql ({len(update_sqls)} updates)")
    
    print("\n=== Concluído. Execute os SQLs no Supabase. ===")


if __name__ == "__main__":
    main()
