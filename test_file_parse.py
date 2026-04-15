import sys, os
sys.path.insert(0, 'python-api')
from app.services.file_parser import parse_uploaded_file, format_file_data_for_prompt

with open('Entradas 01012025 a 15032026 diarias clean.xlsx', 'rb') as f:
    data = f.read()

rows = parse_uploaded_file(data, 'Entradas.xlsx')
print(f"Total rows: {len(rows)}")
if rows:
    print(f"First row keys: {list(rows[0].keys())}")
    print(f"First 3 rows:")
    for r in rows[:3]:
        print(f"  {r}")

# Check EANs and descriptions
eans = set()
descs = set()
for r in rows[:500]:
    if r.get('ean'):
        eans.add(str(r['ean']))
    if r.get('descricao'):
        descs.add(str(r['descricao'])[:80])

print(f"\nUnique EANs (sample of {min(len(eans), 15)}): {list(eans)[:15]}")
print(f"\nUnique descriptions (sample of {min(len(descs), 15)}):")
for d in list(descs)[:15]:
    print(f"  - {d}")

# Search for specific products from the offer
search_terms = ["hidroxizina", "nitazoxanida", "olmesartana", "paracetamol", "prednisona", "pregabalina", "cetorolaco"]
print(f"\n--- BUSCAS ESPECÍFICAS ---")
for term in search_terms:
    matches = [r for r in rows if term.lower() in str(r.get('descricao', '')).lower()]
    if matches:
        first = matches[0]
        precos = []
        for m in matches:
            pu = m.get('preco_unitario') or m.get('valor_total')
            if pu:
                try:
                    precos.append(float(str(pu).replace(',', '.')))
                except:
                    pass
        print(f"  {term}: {len(matches)} registros, EAN={first.get('ean')}, desc={str(first.get('descricao',''))[:50]}, precos_sample={precos[:5]}")
    else:
        print(f"  {term}: NAO ENCONTRADO")

# Generate formatted output
formatted = format_file_data_for_prompt(rows)
print(f"\n--- FORMATTED OUTPUT (first 2000 chars) ---")
print(formatted[:2000])
print(f"\n... (total {len(formatted)} chars)")
