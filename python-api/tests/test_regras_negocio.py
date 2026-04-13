from app.services.regras_negocio import classificar_oferta, precisa_repor, sugestao_pedido


def test_classifica_ouro_sem_equivalente() -> None:
    assert classificar_oferta(25, False) == "ouro"


def test_classifica_atencao_com_equivalente() -> None:
    assert classificar_oferta(10, True) == "atencao"


def test_classifica_descartavel_quando_oferta_supera_media_historica() -> None:
    assert classificar_oferta(5, False, preco_oferta=12, media_historica=10) == "descartavel"


def test_sugestao_pedido_respeita_regra() -> None:
    assert sugestao_pedido(30, 20) == 70


def test_sugestao_pedido_respeita_horizonte_customizado() -> None:
    assert sugestao_pedido(30, 20, horizonte_meses=2) == 40


def test_classifica_prata_com_vantagem_minima_customizada() -> None:
    assert classificar_oferta(6, False, vantagem_minima_percentual=5) == "prata"


def test_precisa_repor_por_curva() -> None:
    assert precisa_repor(10, 1, "A") is True
