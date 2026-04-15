from app.db.supabase_client import get_supabase_client

def check():
    client = get_supabase_client()
    try:
        r = client.table("itens_oferta").select("id").limit(1).execute()
        print("itens_oferta exists!")
    except Exception as e:
        print("Error on itens_oferta:", e)
        
    try:
        r = client.table("analise_itens").select("id").limit(1).execute()
        print("analise_itens exists!")
    except Exception as e:
        print("Error on analise_itens:", e)

check()
