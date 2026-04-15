import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.middleware import get_current_empresa_id

def override_get_empresa():
    return "11111111-1111-1111-1111-111111111111"  # Matches the empresa_id for the database record

app.dependency_overrides[get_current_empresa_id] = override_get_empresa

client = TestClient(app)

def run_test():
    print("Enviando requisição GET para status...")
    response = client.get("/api/ofertas/status/547ee286-0afd-4ee5-a94a-cad5203a786e")
    print("Status code:", response.status_code)
    # Don't print the huge JSON, just the keys and status
    data = response.json()
    print("Keys:", data.keys())
    print("Status:", data.get("status"))

run_test()
