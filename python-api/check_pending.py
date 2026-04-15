from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
client = create_client(supabase_url, supabase_key)

response = client.table("analises_oferta").select("resultado_json").eq("id", "547ee286-0afd-4ee5-a94a-cad5203a786e").execute()
if response.data and response.data[0].get("resultado_json"):
    res = response.data[0]["resultado_json"]
    if "itens" in res:
        for i, item in enumerate(res["itens"]):
            if item.get("preco_oferta") is None:
                print(f"Item {i} tem preco_oferta null!")
