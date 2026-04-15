import sys
sys.path.insert(0, 'python-api')
from app.services.file_parser import parse_uploaded_file, _calcular_preco_unitario, _parse_number

with open('Entradas 01012025 a 15032026 diarias clean.xlsx', 'rb') as f:
    data = f.read()

rows = parse_uploaded_file(data, 'Entradas.xlsx')

# Check specific products from the offer
searches = [
    ("hidroxizina 25", "Dicloridrato de Hidroxizina 25 mg"),
    ("nitazoxanida 500", "Nitazoxanida 500 mg"),
    ("olmesartana", "Olmesartana + Anlodipino 40/5 mg"),
    ("paracetamol", "Paracetamol + Pseudoefedrina 500/30 mg"),
    ("prednisona 20", "Prednisona 20 mg"),
    ("pregabalina 75", "Pregabalina 75 mg"),
    ("cetorolaco", "Trometamol Cetorolaco 10 mg Sublingual"),
]

for search_term, oferta_desc in searches:
    terms = search_term.lower().split()
    matches = [r for r in rows if all(t in str(r.get('descricao', '')).lower() for t in terms)]
    
    if matches:
        # Calculate prices
        precos_unitarios = []
        for m in matches:
            pu = _calcular_preco_unitario(m)
            if pu and pu > 0:
                precos_unitarios.append(pu)
        
        first = matches[0]
        menor = min(precos_unitarios) if precos_unitarios else None
        media = sum(precos_unitarios) / len(precos_unitarios) if precos_unitarios else None
        
        print(f"OFERTA: {oferta_desc}")
        print(f"  Encontrados: {len(matches)} registros no arquivo")
        print(f"  EAN: {first.get('ean')}")
        print(f"  Desc arquivo: {first.get('descricao')}")
        print(f"  Menor preco unit: R${menor:.2f}" if menor else "  Menor preco unit: N/A")
        print(f"  Media preco unit: R${media:.2f}" if media else "  Media preco unit: N/A")
        print(f"  Sample qtdes: {[_parse_number(m.get('quantidade')) for m in matches[:5]]}")
        print(f"  Sample valor_total: {[_parse_number(m.get('valor_total')) for m in matches[:5]]}")
        print()
    else:
        print(f"OFERTA: {oferta_desc}")
        print(f"  NAO ENCONTRADO para termos: {terms}")
        print()
