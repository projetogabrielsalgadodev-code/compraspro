from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

import pandas as pd
df = pd.DataFrame([{"descricao": "Item 1", "preco": 10.0, "ean": "1234567890123", "quantidade": 1}])
df.to_excel("dummy.xlsx", index=False)

def test_endpoint():
    # Attempt to bypass auth by using a disabled dependency override or just see if it fails 401
    
    # We will override the dependency
    from app.middleware import get_current_empresa_id
    app.dependency_overrides[get_current_empresa_id] = lambda: "empresa-teste-123"
    
    with open('dummy.xlsx', 'rb') as f:
        response = client.post(
            "/api/ofertas/analisar-async-file",
            data={
                "texto_bruto": "Oferta de teste",
                "fonte_dados": "arquivo",
                "fornecedor_informado": "Fornecedor Teste",
                "usuario_id": "usuario-teste-123"
            },
            files={"arquivo": ("dummy.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        )
    print("Status:", response.status_code)
    print("Response json:", response.json())
    
if __name__ == "__main__":
    test_endpoint()
