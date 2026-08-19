"""Sez. C — Creazione della zona di galassia da esplorare.

Prima attivita' dello S.C., e da svolgersi «senza che gli U.C. ne siano al corrente».
Qui si genera *solo la topografia*: quali parsec ospitano un sistema e quale sia il
pianeta base. Il contenuto dei pianeti (tipo, forme di vita, razze) non viene
deciso adesso — cfr. `schede.py`.
"""

from __future__ import annotations

from .dadi import Dadiera
from .modello import (
    LATO_PREDEFINITO,
    LETTERE,
    LIVELLI,
    PIANETI_PER_LIVELLO,
    Galassia,
    Pianeta,
    Posizione,
)

DISTRIBUZIONI = {
    "libera": "Nessun limite alla disposizione, salvo il divieto di sovrapposizione (da regolamento).",
    "bilanciata": "I sistemi vengono tenuti a non meno di 3 parsec l'uno dall'altro: esplorazione piu' leggibile.",
    "ammassata": "I sistemi tendono ad addensarsi in nebulose: rotte lunghe e vuote, poi grappoli di avvistamenti.",
}


def genera_galassia(
    seme: str | None = None,
    lato: int = LATO_PREDEFINITO,
    distribuzione: str = "bilanciata",
    dadiera: Dadiera | None = None,
) -> tuple[Galassia, Dadiera]:
    """Costruisce i 4 livelli con 9 pianeti ciascuno e contrassegna il pianeta base."""
    if not 6 <= lato <= len(LETTERE):
        raise ValueError(f"il lato della TABULA deve stare fra 6 e {len(LETTERE)} parsec")
    if distribuzione not in DISTRIBUZIONI:
        raise ValueError(f"distribuzione sconosciuta: {distribuzione!r}")

    if dadiera is None:
        dadiera = Dadiera(seme or Dadiera.seme_casuale())

    pianeti: list[Pianeta] = []
    for livello in range(LIVELLI):
        for posizione in _disponi_livello(dadiera, livello, lato, distribuzione):
            pianeti.append(Pianeta(posizione=posizione))

    # Fra i 36 pianeti, uno e' il pianeta base da cui partono tutte le navi.
    dadiera.scegli(pianeti).base = True

    galassia = Galassia(seme=dadiera.seme, lato=lato, pianeti=pianeti)
    galassia.reindicizza()
    return galassia, dadiera


def _disponi_livello(dadiera: Dadiera, livello: int, lato: int, distribuzione: str) -> list[Posizione]:
    if distribuzione == "libera":
        celle = dadiera.campiona([(x, y) for x in range(lato) for y in range(lato)], PIANETI_PER_LIVELLO)
        return [Posizione(livello, x, y) for x, y in celle]

    if distribuzione == "ammassata":
        return _disponi_ammassata(dadiera, livello, lato)

    return _disponi_distanziata(dadiera, livello, lato)


def _disponi_distanziata(dadiera: Dadiera, livello: int, lato: int) -> list[Posizione]:
    """Campionamento a rifiuto con distanza minima, allentata se lo spazio non basta."""
    for minima in (3, 2, 1):
        scelte: list[Posizione] = []
        for _ in range(4000):
            if len(scelte) == PIANETI_PER_LIVELLO:
                return scelte
            candidato = Posizione(livello, dadiera.scegli(range(lato)), dadiera.scegli(range(lato)))
            if all(
                max(abs(candidato.x - p.x), abs(candidato.y - p.y)) >= minima for p in scelte
            ):
                scelte.append(candidato)
        if len(scelte) == PIANETI_PER_LIVELLO:
            return scelte
    return _disponi_livello(dadiera, livello, lato, "libera")


def _disponi_ammassata(dadiera: Dadiera, livello: int, lato: int) -> list[Posizione]:
    """Due o tre nuclei di addensamento, i sistemi cadono attorno a quelli."""
    nuclei = [
        (dadiera.scegli(range(lato)), dadiera.scegli(range(lato)))
        for _ in range(dadiera.scegli((2, 3)))
    ]
    occupate: set[tuple[int, int]] = set()
    raggio = max(2, lato // 4)
    for _ in range(4000):
        if len(occupate) == PIANETI_PER_LIVELLO:
            break
        cx, cy = dadiera.scegli(nuclei)
        x = min(lato - 1, max(0, cx + dadiera.scegli(range(-raggio, raggio + 1))))
        y = min(lato - 1, max(0, cy + dadiera.scegli(range(-raggio, raggio + 1))))
        occupate.add((x, y))
    while len(occupate) < PIANETI_PER_LIVELLO:  # nuclei troppo stretti: si completa a caso
        occupate.add((dadiera.scegli(range(lato)), dadiera.scegli(range(lato))))
    return [Posizione(livello, x, y) for x, y in occupate]
