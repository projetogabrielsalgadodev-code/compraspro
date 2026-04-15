from app.services.offer_extractor import extrair_itens_por_regex

oferta = """Germed🚨

💊 Acetilcisteína 600 mg – R$ 13,41
📦 Pedido mínimo: 6 unidades

💊 Amoxicilina + Clavulanato 875/125 mg  14 com– R$ 28,57
📦 Pedido mínimo: 3 unidades"""

res = extrair_itens_por_regex(oferta)
print("Regex result:", res)
