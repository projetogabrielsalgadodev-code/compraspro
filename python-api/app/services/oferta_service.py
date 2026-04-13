from __future__ import annotations

from collections import Counter
from typing import Any
from uuid import uuid4

from app.models.schemas import (
    ConfiguracaoEmpresaResponse,
    EquivalenteResumo,
    ExtracaoOferta,
    HistoricoPrecoResumo,
    ItemOfertaResponse,
    OfertaAnalyzeResponse,
    ResumoAnalise,
)

from app.services.equivalencia import sao_equivalentes
from app.services.matching_service import match_por_descricao, match_por_ean
from app.services.preco_service import calcular_media_historica, calcular_mediana_historica, calcular_variacao_percentual, extremos_historicos
from app.services.regras_negocio import classificar_oferta, sugestao_pedido


CONFIGURACAO_PADRAO = ConfiguracaoEmpresaResponse(empresa_id="local")


def montar_resposta_analise(
    extracao: ExtracaoOferta,
    produtos: list[dict[str, Any]],
    historico_por_ean: dict[str, list[dict[str, Any]]],
    *,
    configuracao: ConfiguracaoEmpresaResponse | None = None,
    raw_text: str = "",
    contexto_operacional: str = "",
    anthropic_api_key: str | None = None,
    anthropic_model: str = "claude-opus-4-5",
) -> OfertaAnalyzeResponse:
    configuracao_ativa = configuracao or CONFIGURACAO_PADRAO
    itens_processados: list[ItemOfertaResponse] = []
    itens_para_refino: list[dict[str, Any]] = []
    for item in extracao.items:
        produto, confianca = match_por_ean(produtos, item.ean)
        if produto is None:
            produto, confianca = match_por_descricao(produtos, item.descricao)

        equivalentes = []
        estoque_equivalentes = 0
        produtos_equivalentes: list[dict[str, Any]] = []
        if produto is not None and configuracao_ativa.considerar_equivalentes:
            for candidato in produtos:
                if candidato.get("ean") == produto.get("ean"):
                    continue
                if sao_equivalentes(produto, candidato):
                    produtos_equivalentes.append(candidato)
                    estoque = int(candidato.get("estoque") or 0)
                    estoque_equivalentes += estoque
                    equivalentes.append(
                        EquivalenteResumo(
                            descricao=candidato.get("descricao") or "Produto equivalente",
                            fabricante=candidato.get("fabricante"),
                            estoque=estoque,
                        )
                    )

        historico_comparavel = _coletar_historico_comparavel(
            produto,
            produtos_equivalentes,
            historico_por_ean,
            ean_bruto=item.ean,
        )
        menor_historico_entry = _menor_historico_entry(historico_comparavel)
        menor_historico = float(menor_historico_entry["preco_unitario"]) if menor_historico_entry else None
        media_historica = calcular_media_historica(historico_comparavel)
        referencia_classificacao = _calcular_referencia_historica(historico_comparavel, configuracao_ativa.metodo_comparacao)
        variacao = calcular_variacao_percentual(item.preco_oferta, menor_historico)

        demanda_mes = float(produto.get("demanda_mes") or 0) if produto else 0
        estoque_item = int(produto.get("estoque") or 0) if produto else 0
        classificacao = classificar_oferta(
            variacao or -100,
            configuracao_ativa.considerar_equivalentes and estoque_equivalentes > 0,
            preco_oferta=item.preco_oferta,
            media_historica=referencia_classificacao or media_historica,
            vantagem_minima_percentual=configuracao_ativa.vantagem_minima_percentual,
        )
        recomendacao = _gerar_recomendacao(classificacao, estoque_item, demanda_mes, estoque_equivalentes, configuracao_ativa)
        extremos = (
            extremos_historicos(historico_comparavel)
            if configuracao_ativa.exibir_extremos_historicos and variacao is not None and variacao >= configuracao_ativa.vantagem_minima_percentual
            else {"menores": [], "maiores": []}
        )

        item_response = ItemOfertaResponse(
            ean=item.ean or (produto.get("ean") if produto else None),
            descricao_original=item.descricao,
            descricao_produto=produto.get("descricao") if produto else None,
            preco_oferta=item.preco_oferta,
            menor_historico=menor_historico,
            origem_menor_historico=_formatar_origem_menor_historico(menor_historico_entry),
            variacao_percentual=variacao,
            estoque_item=estoque_item,
            demanda_mes=demanda_mes,
            sugestao_pedido=sugestao_pedido(demanda_mes, estoque_item, configuracao_ativa.horizonte_sugestao_meses),
            estoque_equivalentes=estoque_equivalentes,
            classificacao=classificacao,
            confianca_match=confianca,
            recomendacao=recomendacao,
            equivalente_detalhes=equivalentes,
            historico_menores=_map_historico_resumo(extremos.get("menores", [])),
            historico_maiores=_map_historico_resumo(extremos.get("maiores", [])),
        )
        itens_processados.append(item_response)

        itens_para_refino.append(
            {
                "index": len(itens_processados) - 1,
                "ean": item_response.ean,
                "descricao_original": item_response.descricao_original,
                "descricao_produto": item_response.descricao_produto,
                "preco_oferta": item_response.preco_oferta,
                "menor_historico": item_response.menor_historico,
                "origem_menor_historico": item_response.origem_menor_historico,
                "variacao_percentual": item_response.variacao_percentual,
                "estoque_item": item_response.estoque_item,
                "demanda_mes": item_response.demanda_mes,
                "sugestao_pedido": item_response.sugestao_pedido,
                "estoque_equivalentes": item_response.estoque_equivalentes,
                "classificacao": item_response.classificacao,
                "confianca_match": item_response.confianca_match,
                "recomendacao_base": item_response.recomendacao,
                "equivalentes": [equivalente.model_dump() for equivalente in item_response.equivalente_detalhes],
                "historico_menores": [historico.model_dump() for historico in item_response.historico_menores],
                "historico_maiores": [historico.model_dump() for historico in item_response.historico_maiores],
            }
        )

    # Nota: O refinamento de recomendações agora é feito pelo agente Agno.
    # Esta função montar_resposta_analise é mantida como fallback/legado.

    contador = Counter(item.classificacao for item in itens_processados)
    resumo = ResumoAnalise(
        itens_analisados=len(itens_processados),
        oportunidades=contador.get("ouro", 0) + contador.get("prata", 0),
        sem_necessidade=contador.get("descartavel", 0),
        revisar=contador.get("atencao", 0),
    )
    return OfertaAnalyzeResponse(
        analise_id=str(uuid4()),
        fornecedor=extracao.fornecedor,
        origem="texto",
        resumo=resumo,
        itens=itens_processados,
    )


def _gerar_recomendacao(
    classificacao: str,
    estoque_item: int,
    demanda_mes: float,
    estoque_equivalentes: int,
    configuracao: ConfiguracaoEmpresaResponse,
) -> str:
    cobertura_atual_dias = _cobertura_em_dias(estoque_item, demanda_mes)
    if classificacao == "ouro":
        return (
            "Comprar agora. Ha desconto relevante frente ao historico e a cobertura atual "
            f"esta em cerca de {cobertura_atual_dias} dias, abaixo da meta de {configuracao.estoque_minimo_dias} dias."
        )
    if classificacao == "prata":
        return (
            "Boa oportunidade. O preco esta abaixo da referencia configurada e pode complementar o estoque "
            f"com horizonte de {configuracao.horizonte_sugestao_meses} meses."
        )
    if classificacao == "atencao":
        return f"Preco competitivo, mas ha {estoque_equivalentes} unidades em equivalentes. Revise antes de comprar."
    if cobertura_atual_dias >= configuracao.estoque_alto_dias:
        return (
            "Descartar por enquanto. O estoque atual ja cobre cerca de "
            f"{cobertura_atual_dias} dias, acima do limite alto de {configuracao.estoque_alto_dias} dias."
        )
    return "Descartar. O preco nao oferece vantagem suficiente frente ao historico."


def _calcular_referencia_historica(historico: list[dict[str, Any]], metodo: str) -> float | None:
    if metodo == "median":
        return calcular_mediana_historica(historico)
    if metodo == "lowest":
        item = _menor_historico_entry(historico)
        return float(item["preco_unitario"]) if item and item.get("preco_unitario") is not None else None
    return calcular_media_historica(historico)


def _cobertura_em_dias(estoque_item: int, demanda_mes: float) -> int:
    if demanda_mes <= 0:
        return 999
    return int(round((estoque_item / demanda_mes) * 30))


def _coletar_historico_comparavel(
    produto: dict[str, Any] | None,
    produtos_equivalentes: list[dict[str, Any]],
    historico_por_ean: dict[str, list[dict[str, Any]]],
    *,
    ean_bruto: str | None = None,
) -> list[dict[str, Any]]:
    historico_comparavel: list[dict[str, Any]] = []
    if produto is not None:
        historico_comparavel.extend(
            _anexar_metadados_historico(
                historico_por_ean.get(str(produto.get("ean")), []),
                origem="mesmo_produto",
                produto=produto,
            )
        )
    elif ean_bruto:
        historico_comparavel.extend(
            _anexar_metadados_historico(
                historico_por_ean.get(str(ean_bruto), []),
                origem="mesmo_produto",
                produto={"ean": ean_bruto, "descricao": None},
            )
        )
    for equivalente in produtos_equivalentes:
        historico_comparavel.extend(
            _anexar_metadados_historico(
                historico_por_ean.get(str(equivalente.get("ean")), []),
                origem="equivalente",
                produto=equivalente,
            )
        )
    return historico_comparavel


def _anexar_metadados_historico(
    historico: list[dict[str, Any]],
    *,
    origem: str,
    produto: dict[str, Any],
) -> list[dict[str, Any]]:
    enriquecido: list[dict[str, Any]] = []
    for item in historico:
        registro = dict(item)
        registro["origem_historico"] = origem
        registro["descricao_produto"] = produto.get("descricao")
        registro["ean"] = produto.get("ean")
        enriquecido.append(registro)
    return enriquecido


def _menor_historico_entry(historico: list[dict[str, Any]]) -> dict[str, Any] | None:
    entradas_validas = [item for item in historico if item.get("preco_unitario") is not None]
    if not entradas_validas:
        return None
    return min(entradas_validas, key=lambda item: float(item["preco_unitario"]))


def _formatar_origem_menor_historico(item: dict[str, Any] | None) -> str | None:
    if item is None:
        return None
    if item.get("origem_historico") == "equivalente":
        return "!= equivalente"
    return "= mesmo produto"


def _map_historico_resumo(historico: list[dict[str, Any]]) -> list[HistoricoPrecoResumo]:
    return [
        HistoricoPrecoResumo(
            preco_unitario=float(item["preco_unitario"]),
            fornecedor=item.get("fornecedor"),
            data_entrada=item.get("data_entrada"),
            ean=str(item.get("ean")) if item.get("ean") is not None else None,
            descricao_produto=item.get("descricao_produto"),
        )
        for item in historico
        if item.get("preco_unitario") is not None
    ]
