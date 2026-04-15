import httpx
import os
import json
import pandas as pd

base_url = "http://localhost:8000"

def get_token():
    try:
        from dotenv import load_dotenv
        load_dotenv(".env")
        bearer_token = os.getenv("TEST_BEARER_TOKEN", "")
        if bearer_token:
            return bearer_token
            
        with open("app/tests/test_data.json", "r") as f:
            data = json.load(f)
            return data.get("jwt_token", "")
    except Exception as e:
        print(f"Error getting token: {e}")
        return ""

token = get_token()

if not token:
    print("No token found")
    exit(1)

headers = {"Authorization": f"Bearer {token}"}

# Create a dummy excel file
df = pd.DataFrame([{"descricao": "Item 1", "preco": 10.0, "ean": "1234567890123", "quantidade": 1}])
df.to_excel("dummy.xlsx", index=False)

files = {'arquivo': ('dummy.xlsx', open('dummy.xlsx', 'rb'), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
data = {
    'texto_bruto': 'Item 1 R$ 5,00',
    'fonte_dados': 'arquivo',
    'fornecedor_informado': 'Fornecedor Teste',
}

try:
    response = httpx.post(f"{base_url}/api/ofertas/analisar-async-file", headers=headers, data=data, files=files, timeout=30.0)
    print("Status:", response.status_code)
    print("Response:", response.text)
except Exception as e:
    print("Exception:", e)
