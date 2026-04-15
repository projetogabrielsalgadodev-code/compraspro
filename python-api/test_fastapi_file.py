import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.middleware import get_current_empresa_id

def override_get_empresa():
    return "5eec567f-1d48-4279-acc9-cdbfa2c5d41f"

app.dependency_overrides[get_current_empresa_id] = override_get_empresa

client = TestClient(app)

oferta = '''Germed

Acetilcisteína 600 mg – R$ 13,41
Pedido mínimo: 6 unidades'''

def run_test():
    file_content = b"ean,descricao,preco_unitario,quantidade,valor_total\n123,Acetilciste\xc3\xadna 600 mg,10.0,1,10.0\n"
    files = {"arquivo": ("teste.csv", file_content, "text/csv")}
    data = {
        "texto_bruto": oferta,
        "fonte_dados": "arquivo",
        "fornecedor_informado": "Germed",
    }
    print("Enviando requisição POST...")
    response = client.post("/api/ofertas/analisar-async-file", data=data, files=files)
    print("Status code:", response.status_code)
    print("Response JSON:", response.json())

run_test()
