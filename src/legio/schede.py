"""Sez. F/G — Modulo Schede Informazioni e Guida Incontri.

Il contenuto di un pianeta non esiste finche' non viene richiesto: ogni livello di
informazione si risolve con il dado indicato dalla Scheda, tenendo presente le
notizie precedenti. Cosi' «neanche lo Spazio Computer conosce con precisione in
cosa si imbatteranno le astronavi».
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from .dadi import Dadiera
from .modello import Pianeta

CARTELLA_DATI = Path(__file__).parent / "dati"
ORDINE_STANDARD = ("I", "II", "III", "IV")


@lru_cache(maxsize=1)
def carica_scheda() -> dict:
    return json.loads((CARTELLA_DATI / "scheda_informazioni.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def carica_guida() -> dict:
    return json.loads((CARTELLA_DATI / "guida_incontri.json").read_text(encoding="utf-8"))


def voce_gi(riferimento: int | str | None) -> dict | None:
    if riferimento is None:
        return None
    voce = carica_guida()["voci"].get(str(riferimento))
    return dict(voce, rif=int(riferimento)) if voce else None


# --------------------------------------------------------------------------- #
#  Lettura delle tabelle
# --------------------------------------------------------------------------- #


def _faccia_contiene(faccia: str, esito: int) -> bool:
    if "-" in faccia:
        primo, ultimo = faccia.split("-", 1)
        return int(primo) <= esito <= int(ultimo)
    return int(faccia) == esito


def _tabella_applicabile(tabella: dict, noto: dict) -> bool:
    for chiave, ammessi in tabella.get("quando", {}).items():
        if noto.get(chiave) not in ammessi:
            return False
    return True


def _scegli_tabella(livello: dict, noto: dict) -> dict | None:
    for tabella in livello["tabelle"]:
        if _tabella_applicabile(tabella, noto):
            return tabella
    return None


def prossimo_livello(pianeta: Pianeta, spazio_esterno: bool = False) -> str | None:
    """Il livello di informazione che l'U.C. puo' richiedere adesso, o None se esaurito."""
    if pianeta.informazioni.get("terminale"):
        return None
    ordine = list(ORDINE_STANDARD)
    if spazio_esterno:
        ordine.insert(1, "I-bis")
    for livello in ordine:
        if livello not in pianeta.livelli_noti:
            return livello
    return None


def risolvi_livello(
    pianeta: Pianeta,
    livello: str,
    dadiera: Dadiera,
    scheda: dict | None = None,
) -> dict:
    """Esegue una richiesta di informazione: tira il dado e legge la caratteristica.

    Restituisce un resoconto pronto per il registro dello S.C. Un esito D.N.S.
    consuma la richiesta senza aggiungere notizie.
    """
    scheda = scheda or carica_scheda()
    definizione = scheda["livelli"].get(livello)
    if definizione is None:
        raise ValueError(f"livello di informazione inesistente: {livello!r}")
    if livello in pianeta.livelli_noti:
        raise ValueError(f"livello {livello} gia' noto per {pianeta.id}")

    tabella = _scegli_tabella(definizione, pianeta.informazioni)
    if tabella is None:
        raise ValueError(
            f"nessuna tabella di {livello} livello applicabile alle notizie precedenti di {pianeta.id}"
        )

    resoconto: dict = {
        "pianeta": pianeta.id,
        "livello": livello,
        "nome": definizione["nome"],
        "dado": None,
        "esito": None,
        "dns": False,
        "dati": {},
    }

    if tabella.get("senza_dado"):
        dati = dict(tabella["dati"])
    else:
        tiro = dadiera.tira(tabella["dado"], f"{livello} livello di informazione su {pianeta.id}")
        resoconto["dado"] = tiro.dado
        resoconto["esito"] = tiro.esito
        voce = next((v for v in tabella["esiti"] if _faccia_contiene(v["faccia"], tiro.esito)), None)
        if voce is None:
            raise ValueError(f"tabella incompleta: {tabella['dado']} → {tiro.esito} non previsto")
        if voce.get("dns"):
            resoconto["dns"] = True
            resoconto["testo"] = "D.N.S. — dati non sufficienti. La richiesta va ripetuta; la precedente e' sprecata."
            return resoconto
        dati = dict(voce["dati"])

    pianeta.informazioni.update(dati)
    pianeta.livelli_noti.append(livello)
    resoconto["dati"] = dati
    resoconto["testo"] = frase_informazione(livello, dati)
    return resoconto


def frase_informazione(livello: str, dati: dict) -> str:
    """La dizione con cui lo S.C. comunica l'informazione agli U.C."""
    if livello == "I":
        return f"Pianeta {dati['tipo']} ({dati['codice']}) — {dati['classe']}. {dati['ambiente']}"
    if livello == "I-bis":
        return f"Radioattivita' {dati['radioattivita']}. {dati['nota_radio']}"
    if livello == "II":
        if dati["vita"] == "NESSUNA":
            return "Non si rilevano forme di vita."
        return f"Si dichiarano forme di vita {dati['vita']}."
    if livello == "III":
        if dati.get("terminale"):
            return dati.get("esito_finale", "Nessuna forma di vita: pianeta deserto.")
        return f"Si dichiarano {dati['sapienza']}."
    if livello == "IV":
        return f"Razza: {dati['razza']} — riferimento G.I. n. {dati['rif_gi']}."
    return ", ".join(f"{k}: {v}" for k, v in dati.items())


def completa_informazioni(pianeta: Pianeta, dadiera: Dadiera, spazio_esterno: bool = False) -> list[dict]:
    """Sez. F — all'atterraggio l'U.C. riceve tutte insieme le informazioni mancanti.

    Anche queste dipendono da esiti casuali: un D.N.S. viene semplicemente ripetuto,
    perche' qui non c'e' una richiesta da sprecare.
    """
    resoconti: list[dict] = []
    for _ in range(64):
        livello = prossimo_livello(pianeta, spazio_esterno)
        if livello is None:
            break
        resoconti.append(risolvi_livello(pianeta, livello, dadiera))
    return resoconti


# --------------------------------------------------------------------------- #
#  Guida Incontri — presenze e arrivi
# --------------------------------------------------------------------------- #


def _leggi_tab(tab: dict, dadiera: Dadiera, motivo: str) -> tuple[int, dict]:
    tiro = dadiera.tira(tab["dado"], motivo)
    for faccia, valore in tab["esiti"].items():
        if _faccia_contiene(faccia, tiro.esito):
            return int(valore), {"dado": tiro.dado, "esito": tiro.esito}
    raise ValueError(f"TAB. incompleta: {tab['dado']} → {tiro.esito} non previsto")


def tira_presenze(voce: dict, dadiera: Dadiera) -> tuple[int, dict]:
    """TAB. PRESENZE — quanti Alieni sono presenti (sez. G, punto a)."""
    return _leggi_tab(voce["scheda"]["presenze"], dadiera, f"TAB. PRESENZE — {voce['nome']}")


def tira_arrivi(voce: dict, dadiera: Dadiera) -> tuple[int, dict]:
    """TAB. ARRIVI — quanti nuovi Alieni arrivano nel turno (sez. G, punto c)."""
    return _leggi_tab(voce["scheda"]["arrivi"], dadiera, f"TAB. ARRIVI — {voce['nome']}")


def risolvi_attivita(voce: dict, dadiera: Dadiera) -> list[dict]:
    """Sez. G, punto b — svolge le attivita' previste dagli Alieni e ne legge gli esiti.

    Ogni tabella indica se l'esito casuale e' controllato dall'U.C. o dallo S.C.:
    il dato viene riportato nel resoconto perche' al tavolo tiri chi deve.
    """
    esiti: list[dict] = []
    for attivita in voce["scheda"].get("attivita", []):
        tiro = dadiera.tira(attivita["dado"], f"{attivita['nome']} — {voce['nome']}")
        riga = next(
            (v for f, v in attivita["esiti"].items() if _faccia_contiene(f, tiro.esito)),
            None,
        )
        if riga is None:
            raise ValueError(f"tabella attivita' incompleta: {attivita['dado']} → {tiro.esito}")
        esiti.append(
            {
                "nome": attivita["nome"],
                "controllo": attivita["controllo"],
                "dado": tiro.dado,
                "esito": tiro.esito,
                "testo": riga["testo"],
                "punti": int(riga.get("punti", 0)),
            }
        )
    return esiti
