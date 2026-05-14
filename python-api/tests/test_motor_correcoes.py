"""
Testes específicos das correções do review (A1, A2, A6).
Cobrem:
  - A1: normalização de preço caixa→unitário no _normalizar_precos_entries
  - A2: classificar_oferta com thresholds AGENTS.md
  - A6: match por EAN reduz confiança quando dosagem/forma divergem
"""
import os

os.environ.setdefault("SUPABASE_URL", "x")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "x")
os.environ.setdefault("ANTHROPIC_API_KEY", "x")

from app.services.analysis_engine import (
    _normalizar_precos_entries,
    _match_item_no_arquivo,
    classificar_oferta,
    executar_analise_deterministico,
)


# ─── A1: Normalização de preço ────────────────────────────────────────────────

def test_a1_normalizacao_caixa_para_unitario():
    """Preço de caixa de 14 cprs com R$35,51 deve virar R$2,5364 por unidade."""
    entries = [{"preco_unitario": 35.51, "data_entrada": "2025-01-01", "quantidade_unitaria": 1}]
    precos, _, _ = _normalizar_precos_entries(entries, "AXETILCEFUROXIMA 500MG 14CPR TEU")
    assert len(precos) == 1
    assert abs(precos[0] - (35.51 / 14)) < 0.001


def test_a1_liquido_nao_divide_por_ml():
    """Frasco 120ml não deve virar preço por ml — multiplicador=1."""
    entries = [{"preco_unitario": 15.0, "data_entrada": "2025-01-01", "quantidade_unitaria": 1}]
    precos, _, _ = _normalizar_precos_entries(entries, "TOSSEXPEC XPE C/ 120ML + COPO")
    assert precos == [15.0]


def test_a1_sanity_check_evita_dupla_divisao():
    """Se o preço já é unitário e a divisão der < 0.01, mantém o original."""
    entries = [{"preco_unitario": 0.05, "data_entrada": "2025-01-01", "quantidade_unitaria": 1}]
    precos, _, _ = _normalizar_precos_entries(entries, "PRODUTO 30X10")
    # mult = 300, 0.05/300 = 0.00017 < 0.01 → mantém original
    assert precos == [0.05]


def test_a1_ignora_historico_acima_dias():
    """Entradas mais antigas que N dias são filtradas."""
    entries = [
        {"preco_unitario": 10.0, "data_entrada": "2020-01-01", "quantidade_unitaria": 1},
        {"preco_unitario": 20.0, "data_entrada": "2099-01-01", "quantidade_unitaria": 1},
    ]
    precos, _, _ = _normalizar_precos_entries(entries, "ITEM AVULSO", ignorar_acima_dias=30)
    # 2020 está fora; 2099 sempre dentro (data futura para o teste é igual a "agora-30d")
    assert len(precos) == 1
    assert precos[0] == 20.0


# ─── A2: Classificação (AGENTS.md) ────────────────────────────────────────────

def test_a2_ouro_threshold_20():
    assert classificar_oferta(20) == "ouro"
    assert classificar_oferta(19.9) == "prata"


def test_a2_prata_threshold_default_1():
    """Default vantagem_minima_percentual=1 → 1.0% é prata, 0.99% é descartavel."""
    assert classificar_oferta(1.0) == "prata"
    assert classificar_oferta(0.99) == "descartavel"


def test_a2_atencao_quando_equivalente_cobre_horizonte():
    """30% de desconto + estoque eq cobrindo 6 meses (horizonte 3) → atencao."""
    r = classificar_oferta(
        30, estoque_equivalentes=60, demanda_mes=10, horizonte_sugestao_meses=3
    )
    assert r == "atencao"


def test_a2_equivalente_insuficiente_nao_rebaixa():
    """30% + estoque eq que cobre só 1 mês → continua ouro."""
    r = classificar_oferta(
        30, estoque_equivalentes=10, demanda_mes=10, horizonte_sugestao_meses=3
    )
    assert r == "ouro"


def test_a2_considerar_equivalentes_false_ignora_estoque():
    """Quando empresa configura considerar_equivalentes=False, nunca rebaixa."""
    r = classificar_oferta(
        30, estoque_equivalentes=999, demanda_mes=10, horizonte_sugestao_meses=3,
        considerar_equivalentes=False,
    )
    assert r == "ouro"


# ─── A6: Match por EAN valida dosagem/forma ──────────────────────────────────

def test_a6_ean_dosagem_diferente_baixa_confianca():
    """EAN bate mas dosagem é 500MG vs 250MG → confianca='medio'."""
    ean = "7896000000001"
    ean_stats = {
        ean: {
            "ean": ean,
            "descricao": "AMOX 250MG C/14",
            "menor_preco": 10.0,
            "media_preco": 11.0,
            "maior_preco": 12.0,
            "qtd_entradas": 1,
            "qtde_total": 1,
            "demanda_mes": 1,
            "estoque_item": 0,
            "primeira_data": "2025-01-01",
            "ultima_data": "2025-01-01",
        }
    }
    match = _match_item_no_arquivo("AMOX 500MG C/14", ean, ean_stats, {})
    assert match is not None
    assert match["confianca_match"] == "medio"


def test_a6_ean_forma_farmaceutica_diferente_baixa_confianca():
    """EAN bate mas forma é solido vs xarope → confianca='baixo'."""
    ean = "7896000000002"
    ean_stats = {
        ean: {
            "ean": ean,
            "descricao": "DIPIRONA XPE 100ML",
            "menor_preco": 8.0,
            "media_preco": 9.0,
            "maior_preco": 10.0,
            "qtd_entradas": 1,
            "qtde_total": 1,
            "demanda_mes": 1,
            "estoque_item": 0,
            "primeira_data": "2025-01-01",
            "ultima_data": "2025-01-01",
        }
    }
    match = _match_item_no_arquivo("DIPIRONA 500MG C/10 CPR", ean, ean_stats, {})
    assert match is not None
    assert match["confianca_match"] == "baixo"


def test_a6_ean_dosagem_igual_mantem_alto():
    """EAN bate e dosagem 500mg igual → confianca='alto'."""
    ean = "7896000000003"
    ean_stats = {
        ean: {
            "ean": ean,
            "descricao": "AMOX 500MG C/14",
            "menor_preco": 10.0,
            "media_preco": 11.0,
            "maior_preco": 12.0,
            "qtd_entradas": 1,
            "qtde_total": 1,
            "demanda_mes": 1,
            "estoque_item": 0,
            "primeira_data": "2025-01-01",
            "ultima_data": "2025-01-01",
        }
    }
    match = _match_item_no_arquivo("AMOX 500MG C/14", ean, ean_stats, {})
    assert match is not None
    assert match["confianca_match"] == "alto"


# ─── Integração: motor end-to-end com config customizada ─────────────────────

def test_motor_integra_config_vantagem_minima():
    """Empresa com vantagem_minima=10 — descontos < 10% viram descartavel."""
    ean = "7896000000004"
    ean_stats = {
        ean: {
            "ean": ean,
            "descricao": "PRODUTO X 500MG C/10",
            "menor_preco": 1.0,  # unidade
            "media_preco": 1.0,
            "maior_preco": 1.0,
            "qtd_entradas": 1,
            "qtde_total": 10,
            "demanda_mes": 5,
            "estoque_item": 0,
            "primeira_data": "2025-01-01",
            "ultima_data": "2025-01-01",
        }
    }
    token_index = {"produto": [ean], "500mg": [ean]}
    itens = [{
        "descricao": "PRODUTO X 500MG C/10",
        "preco": 9.5,  # caixa de 10 → unitário 0.95 → desconto 5% sobre 1.0
        "ean": ean,
        "tipo_preco": "absoluto",
        "multiplicador_embalagem": 10,
    }]
    # Default (vantagem_min=1): 5% = prata
    r_default = executar_analise_deterministico(itens, None, ean_stats, token_index)
    assert r_default["itens"][0]["classificacao"] == "prata"
    # Empresa exige >= 10%: vira descartavel
    r_strict = executar_analise_deterministico(
        itens, None, ean_stats, token_index,
        config={"vantagem_minima_percentual": 10.0, "metodo_comparacao": "lowest",
                "considerar_equivalentes": True, "horizonte_sugestao_meses": 3}
    )
    assert r_strict["itens"][0]["classificacao"] == "descartavel"


def test_motor_metodo_comparacao_average():
    """Quando metodo=average, usa media_preco em vez de menor_preco."""
    ean = "7896000000005"
    ean_stats = {
        ean: {
            "ean": ean,
            "descricao": "PRODUTO Y 500MG C/10",
            "menor_preco": 1.0,
            "media_preco": 2.0,
            "maior_preco": 3.0,
            "qtd_entradas": 3,
            "qtde_total": 30,
            "demanda_mes": 5,
            "estoque_item": 0,
            "primeira_data": "2025-01-01",
            "ultima_data": "2025-01-01",
        }
    }
    token_index = {"produto": [ean], "500mg": [ean]}
    itens = [{
        "descricao": "PRODUTO Y 500MG C/10",
        "preco": 15.0,  # caixa de 10 → unitário 1.50
        "ean": ean,
        "tipo_preco": "absoluto",
        "multiplicador_embalagem": 10,
    }]
    # average=2.0, oferta=1.5 → desconto 25% → ouro
    r = executar_analise_deterministico(
        itens, None, ean_stats, token_index,
        config={"vantagem_minima_percentual": 1.0, "metodo_comparacao": "average",
                "considerar_equivalentes": True, "horizonte_sugestao_meses": 3}
    )
    assert r["itens"][0]["classificacao"] == "ouro"
    # menor=1.0, oferta=1.5 → -50% → descartavel
    r2 = executar_analise_deterministico(
        itens, None, ean_stats, token_index,
        config={"vantagem_minima_percentual": 1.0, "metodo_comparacao": "lowest",
                "considerar_equivalentes": True, "horizonte_sugestao_meses": 3}
    )
    assert r2["itens"][0]["classificacao"] == "descartavel"
