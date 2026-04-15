from app.db.supabase_client import get_supabase_client
import json

def check_analise():
    client = get_supabase_client()
    response = client.table("analises_oferta").select("id, status, resultado_json, created_at, empresa_id").eq("id", "547ee286-0afd-4ee5-a94a-cad5203a786e").execute()
    with open("db_record.json", "w", encoding="utf-8") as f:
        json.dump(response.data, f, ensure_ascii=False)

check_analise()
