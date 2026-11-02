"""Regolamento avanzato, Parte II — validazione della galassia costruita a mano.

Le regole 1-9 della specifica "Editor Galassia": alcune sono conteggi che il master
puo' legittimamente derogare (avviso), altre proteggono invarianti da cui dipende il
resto del motore di gioco (errore, blocca l'avvio della partita). Vedi la sezione
"Decisioni di scoping" del piano per la motivazione di ogni classificazione.
"""

from __future__ import annotations

from .modello import LIVELLI, PIANETI_PER_LIVELLO, Galassia, Pianeta, Posizione, distanza_piana

DISTANZA_MINIMA_RMG = 4
DISTANZA_MINIMA_BN = 5


def _distanza_minima_da_pianeti(cella: Posizione, pianeti: list[Pianeta]) -> int | None:
    stesso_livello = [p for p in pianeti if p.posizione.livello == cella.livello]
    if not stesso_livello:
        return None
    return min(distanza_piana(cella, p.posizione) for p in stesso_livello)


def _celle_contigue(celle: list[Posizione]) -> bool:
    """Vero se ogni cella dista al massimo 1 (Chebyshev) da almeno un'altra del gruppo."""
    for indice, cella in enumerate(celle):
        altre = celle[:indice] + celle[indice + 1 :]
        if not any(distanza_piana(cella, altra) == 1 for altra in altre):
            return False
    return True


def valida_galassia(galassia: Galassia) -> dict:
    """Ritorna `{"errori": [...], "avvisi": [...], "info": [...]}`.

    Ogni voce e' `{"codice": str, "messaggio": str, "livello": int | None}`.
    """
    errori: list[dict] = []
    avvisi: list[dict] = []
    info: list[dict] = []

    def aggiungi(elenco: list[dict], codice: str, messaggio: str, livello: int | None = None) -> None:
        elenco.append({"codice": codice, "messaggio": messaggio, "livello": livello})

    basi = [p for p in galassia.pianeti if p.base]
    if len(basi) == 0:
        aggiungi(errori, "base-assente", "Nessun pianeta base: designarne uno prima di avviare la partita.")
    elif len(basi) > 1:
        aggiungi(errori, "base-multipla", f"{len(basi)} pianeti sono segnati come base: deve essercene uno solo.")

    for livello in range(LIVELLI):
        pianeti_livello = [p for p in galassia.pianeti if p.posizione.livello == livello]
        etichetta_livello = livello + 1

        if len(pianeti_livello) != PIANETI_PER_LIVELLO:
            aggiungi(
                avvisi, "conteggio-pianeti",
                f"Livello {etichetta_livello}: {len(pianeti_livello)} pianeti (atteso {PIANETI_PER_LIVELLO}).",
                livello,
            )

        posizioni_viste: dict[Posizione, int] = {}
        for pianeta in pianeti_livello:
            posizioni_viste[pianeta.posizione] = posizioni_viste.get(pianeta.posizione, 0) + 1
        for posizione, conteggio in posizioni_viste.items():
            if conteggio > 1:
                aggiungi(
                    errori, "sovrapposizione-pianeti",
                    f"Livello {etichetta_livello}: {conteggio} pianeti sovrapposti in {posizione.sigla}.",
                    livello,
                )

        rmg_livello = [a for a in galassia.anomalie if a.tipo == "RMG" and a.celle[0].livello == livello]
        if len(rmg_livello) != 1:
            aggiungi(
                avvisi, "conteggio-rmg",
                f"Livello {etichetta_livello}: {len(rmg_livello)} R.M.G. (attesa 1).",
                livello,
            )
        for rmg in rmg_livello:
            if len(rmg.celle) != 3 or not _celle_contigue(rmg.celle):
                aggiungi(
                    errori, "rmg-non-contigua",
                    f"Livello {etichetta_livello}: la R.M.G. in {rmg.celle[0].sigla} non ha 3 celle contigue.",
                    livello,
                )
            for cella in rmg.celle:
                distanza = _distanza_minima_da_pianeti(cella, pianeti_livello)
                if distanza is not None and distanza < DISTANZA_MINIMA_RMG:
                    aggiungi(
                        errori, "rmg-troppo-vicina",
                        f"Livello {etichetta_livello}: la R.M.G. dista {distanza} parsec da un pianeta"
                        f" (minimo {DISTANZA_MINIMA_RMG}).",
                        livello,
                    )
                    break

        dn_livello = [a for a in galassia.anomalie if a.tipo == "DN" and a.celle[0].livello == livello]
        if len(dn_livello) != 3:
            aggiungi(
                avvisi, "conteggio-dn",
                f"Livello {etichetta_livello}: {len(dn_livello)} Distorsioni Nullius (attese 3).",
                livello,
            )

        bn_livello = [a for a in galassia.anomalie if a.tipo == "BN"]
        if len(bn_livello) != 1:
            aggiungi(
                avvisi, "conteggio-bn",
                f"Livello {etichetta_livello}: {len(bn_livello)} Buchi Neri (atteso 1).",
                livello,
            )
        for bn in bn_livello:
            cella = next((c for c in bn.celle if c.livello == livello), None)
            if cella is None:
                continue
            distanza = _distanza_minima_da_pianeti(cella, pianeti_livello)
            if distanza is not None and distanza < DISTANZA_MINIMA_BN:
                aggiungi(
                    errori, "bn-troppo-vicino",
                    f"Livello {etichetta_livello}: il B.N. dista {distanza} parsec da un pianeta"
                    f" (minimo {DISTANZA_MINIMA_BN}).",
                    livello,
                )

    aggiungi(info, "totale-pianeti", f"Totale pianeti: {len(galassia.pianeti)} (atteso {PIANETI_PER_LIVELLO * LIVELLI}).")

    return {"errori": errori, "avvisi": avvisi, "info": info}
