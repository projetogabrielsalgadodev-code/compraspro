import os
import sys
from dotenv import load_dotenv
load_dotenv(".env")
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from typing import Optional
from app.db.supabase_client import get_supabase_client
from app.services.file_parser import parse_uploaded_file, format_file_data_for_prompt
from app.services.agno_agent import executar_analise_oferta

async def main():
    oferta = """🥇 NEOSORO SOL ADULTO C/30ML = 2,89
Preço Final em Nota!
⚠️ Válido acima de 120 unidades

🥇 DORFLEX C/36CPR = 17,99
Preço Final em Nota!

🥇 SAL DE FRUTA SACHÊ 30X2 = 92,99
Preço Final em Nota!

🥇 SAL DE FRUTA 100GRS = 19,29
Preço Final em Nota!

🥇DORFLEX HOSPITALAR  C/300CPR 30X10 = 179,90
Preço Final em Nota!

🥇 HISTAMIN XAROPE 100ML = 8,59
Preço Final em Nota!

🥇 HISTAMIN 2MG C/20CPR  = 3,79
Preço Final em Nota!
"""
    file_path = r"c:\Users\JoãoVictorRibeiroLag\Documents\Projetos Highcode\Projeto Gabriel Salgado\Projeto ComprasPRO\Entradas 01012025 a 15032026 diarias clean.xlsx"
    empresa_id = "0c8d1976-13cb-45ec-b1fb-a144f808db39"
    
    print("Parsing document...")
    with open(file_path, "rb") as f:
        file_bytes = f.read()
    
    parsed_data = parse_uploaded_file(file_bytes, "Entradas 01012025 a 15032026 diarias clean.xlsx")
    formatted_data = format_file_data_for_prompt(parsed_data, texto_oferta=oferta)
    
    print("Running new analysis engine...")
    resultado, metrics = await executar_analise_oferta(
        texto_bruto=oferta,
        empresa_id=empresa_id,
        dados_arquivo=formatted_data,
        rows_arquivo=parsed_data
    )
    
    print("======= NOVO RESULTADO DA ANALISE (MOTOR ATUALIZADO) =======")
    for item in resultado.itens:
        print(f"Produto: {item.descricao_original}")
        print(f"         Multiplicador Oferta: {getattr(item, 'multiplicador_embalagem', 1)}")
        print(f"         Preco Oferta: {item.preco_oferta}")
        print(f"         Menor Historico: {item.menor_historico}")
        print(f"         Variacao: {item.variacao_percentual}%")
        print(f"         Classificação: {item.classificacao}")
        print(f"         Demanda / Estoque: {item.demanda_mes} / {item.estoque_item}")
        print(f"         Recomendacao: {item.recomendacao}")
        print("-------")
        
    print("\n\n")

    # Comparar com db475c04-2311-48e3-9fc7-77ad118ca722
    client = get_supabase_client()
    if client:
        res = client.table("itens_oferta").select("*").eq("analise_id", "db475c04-2311-48e3-9fc7-77ad118ca722").execute()
        print(f"======= ANALISE ANTERIOR (db475c04-2311-48e3-9fc7-77ad118ca722) =======")
        for i in res.data:
            print(f"Produto: {i['descricao_bruta']}")
            print(f"         Origem Hist: {i['origem_menor_historico']}")
            print(f"         Preco Oferta: {i['preco_oferta']}")
            print(f"         Menor Historico: {i['menor_preco_historico']}")
            print(f"         Variacao: {i['desconto_percentual']}%")
            print(f"         Classificação: {i['classificacao']}")
            print(f"         Demanda / Estoque: {i['demanda_mes']} / {i['estoque_item']}")
            print(f"         Recomendacao: {i['recomendacao']}")
            print("-------")

if __name__ == "__main__":
    asyncio.run(main())
