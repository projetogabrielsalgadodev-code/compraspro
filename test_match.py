import sys
sys.path.insert(0, 'python-api')
from app.services.file_parser import parse_uploaded_file, format_file_data_for_prompt

with open('Entradas 01012025 a 15032026 diarias clean.xlsx', 'rb') as f:
    data = f.read()

rows = parse_uploaded_file(data, 'Entradas.xlsx')
print(f"Total rows: {len(rows)}")

# Simular o texto da oferta real
texto_oferta = """Oferta Germed - Medicamentos com desconto

Dicloridrato de Hidroxizina 25 mg - R$ 24,17
Nitazoxanida 500 mg - R$ 9,58
Olmesartana + Anlodipino 40/5 mg - R$ 24,54
Paracetamol + Pseudoefedrina 500/30 mg - R$ 9,37
Prednisona 20 mg - R$ 2,21
Pregabalina 75 mg - R$ 4,24
Trometamol Cetorolaco 10 mg Sublingual - R$ 3,75
"""

formatted = format_file_data_for_prompt(rows, texto_oferta=texto_oferta)
print(f"\n=== FORMATTED OUTPUT ({len(formatted)} chars) ===\n")
print(formatted)
