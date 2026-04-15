from supabase import create_client
import os

from dotenv import load_dotenv
load_dotenv()

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
client = create_client(supabase_url, supabase_key)

response = client.table("itens_oferta").select("*").eq("analise_id", "547ee286-0afd-4ee5-a94a-cad5203a786e").execute()
print(f"Encontrou {len(response.data)} itens para 547ee286-0afd-4ee5-a94a-cad5203a786e")
