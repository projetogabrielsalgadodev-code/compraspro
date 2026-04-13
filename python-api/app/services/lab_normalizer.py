from __future__ import annotations


ALIASES_PADRAO = {
    "NQ": "Neoquimica",
    "NEO Q": "Neoquimica",
    "MDL": "Medley",
    "EMS": "EMS",
    "PD": "Prati-Donaduzzi",
}


def normalizar_laboratorio(nome: str | None, aliases: dict[str, str] | None = None) -> str | None:
    if not nome:
        return None
    base = nome.strip().upper()
    mapa = {**ALIASES_PADRAO, **(aliases or {})}
    return mapa.get(base, nome.strip().title())
