"""Sez. D/E — Rotte e avvistamenti.

Lo S.C. traccia la rotta dichiarata dall'U.C., la ripercorre per verificare cosa i
radar potevano avvistare, e determina dove il movimento termina.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .modello import (
    DIREZIONI,
    LIVELLI,
    NOMI_DIREZIONE,
    PARSEC_FRA_LIVELLI,
    PARSEC_PER_SERBATOIO,
    RADAR_MASSIMI,
    VERTICALI,
    Galassia,
    Posizione,
    normalizza_direzione,
    scomponi_direzione,
)

_SEGMENTO = re.compile(r"([0-9]+)\s*([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\-]*)")


class RottaNonValida(ValueError):
    """La dichiarazione dell'U.C. non e' tracciabile: lo S.C. la respinge."""


@dataclass(frozen=True, slots=True)
class Segmento:
    parsec: int
    direzione: str

    def __str__(self) -> str:
        return f"{self.parsec} {self.direzione}"


@dataclass(frozen=True, slots=True)
class Passo:
    """Un parsec della rotta tracciata a matita sulla TABULA."""

    indice: int
    posizione: Posizione
    cambio_livello: bool = False


@dataclass
class Avvistamento:
    pianeta_id: str
    parsec_rotta: int
    distanza: int
    direzione: str
    da: Posizione
    tutti_i_parsec: list[int] = field(default_factory=list)

    @property
    def comunicazione(self) -> str:
        dove = "dal punto di partenza" if self.parsec_rotta == 0 else f"al {self.parsec_rotta}° parsec"
        if self.distanza == 0:
            return f"Avvistamento {dove} — la nave si trova sul sistema stesso."
        return (
            f"Avvistamento {dove} — Distanza dal pianeta {self.distanza} parsec"
            f" — Direzione {self.direzione}."
        )


@dataclass
class Movimento:
    partenza: Posizione
    arrivo: Posizione
    segmenti: list[Segmento]
    passi: list[Passo]
    parsec_percorsi: int
    parsec_dichiarati: int
    radar: int
    serbatoi: int
    avvistamenti: list[Avvistamento] = field(default_factory=list)
    motivo_fermata: str = "rotta completata"
    atterraggio_su: str | None = None
    atterraggio_obbligato: bool = False
    comunicazioni: list[str] = field(default_factory=list)

    def in_chiaro(self) -> dict:
        return {
            "partenza": self.partenza.riferimento,
            "arrivo": self.arrivo.riferimento,
            "arrivo_dettaglio": {
                "livello": self.arrivo.livello,
                "x": self.arrivo.x,
                "y": self.arrivo.y,
                "sigla": self.arrivo.sigla,
            },
            "segmenti": [str(s) for s in self.segmenti],
            "traccia": [
                {
                    "indice": p.indice,
                    "livello": p.posizione.livello,
                    "x": p.posizione.x,
                    "y": p.posizione.y,
                    "sigla": p.posizione.sigla,
                    "cambio_livello": p.cambio_livello,
                }
                for p in self.passi
            ],
            "parsec_percorsi": self.parsec_percorsi,
            "parsec_dichiarati": self.parsec_dichiarati,
            "radar": self.radar,
            "serbatoi": self.serbatoi,
            "avvistamenti": [
                {
                    "pianeta": a.pianeta_id,
                    "parsec_rotta": a.parsec_rotta,
                    "distanza": a.distanza,
                    "direzione": a.direzione,
                    "da": a.da.sigla,
                    "tutti_i_parsec": a.tutti_i_parsec,
                    "comunicazione": a.comunicazione,
                }
                for a in self.avvistamenti
            ],
            "motivo_fermata": self.motivo_fermata,
            "atterraggio_su": self.atterraggio_su,
            "atterraggio_obbligato": self.atterraggio_obbligato,
            "comunicazioni": list(self.comunicazioni),
        }


# --------------------------------------------------------------------------- #
#  Lettura della dichiarazione di rotta
# --------------------------------------------------------------------------- #


def analizza_rotta(testo: str) -> list[Segmento]:
    """Legge una dichiarazione come «10 N, +5 E» o «8 NE, 4 GIU, 3 O»."""
    trovati = _SEGMENTO.findall(testo or "")
    if not trovati:
        raise RottaNonValida(
            "Rotta non comprensibile. Attesa una sequenza tipo «10 N, +5 E»"
            " (direzioni: N NE E SE S SO O NO, oppure SU/GIU per cambiare livello)."
        )
    segmenti: list[Segmento] = []
    for parsec, direzione in trovati:
        try:
            sigla = normalizza_direzione(direzione)
        except ValueError as errore:
            raise RottaNonValida(str(errore)) from errore
        passi = int(parsec)
        if passi <= 0:
            raise RottaNonValida("ogni tratto di rotta deve valere almeno 1 parsec")
        if sigla in VERTICALI and passi % PARSEC_FRA_LIVELLI:
            raise RottaNonValida(
                f"il cambio di livello costa {PARSEC_FRA_LIVELLI} parsec: «{passi} {sigla}»"
                f" non e' un multiplo di {PARSEC_FRA_LIVELLI}."
            )
        segmenti.append(Segmento(passi, sigla))
    return segmenti


def descrivi_rotta(segmenti: list[Segmento]) -> str:
    return ", ".join(f"{s.parsec} {NOMI_DIREZIONE[s.direzione]}" for s in segmenti)


# --------------------------------------------------------------------------- #
#  Tracciamento
# --------------------------------------------------------------------------- #


def traccia(partenza: Posizione, segmenti: list[Segmento], lato: int) -> tuple[list[Passo], str]:
    """Traccia a matita la rotta, fermandosi all'ultimo parsec utile se esce dalla zona (sez. D)."""
    passi = [Passo(0, partenza)]
    posizione = partenza
    indice = 0
    motivo = "rotta completata"

    for segmento in segmenti:
        if segmento.direzione in VERTICALI:
            verso = -1 if segmento.direzione == "SU" else 1
            for _ in range(segmento.parsec // PARSEC_FRA_LIVELLI):
                prossima = posizione.traslata(0, 0, verso)
                if not 0 <= prossima.livello < LIVELLI:
                    return passi, "limite verticale della zona"
                indice += PARSEC_FRA_LIVELLI
                posizione = prossima
                passi.append(Passo(indice, posizione, cambio_livello=True))
        else:
            dx, dy = DIREZIONI[segmento.direzione]
            for _ in range(segmento.parsec):
                prossima = posizione.traslata(dx, dy)
                if not prossima.dentro(lato):
                    return passi, "limite della zona"
                indice += 1
                posizione = prossima
                passi.append(Passo(indice, posizione))
    return passi, motivo


# --------------------------------------------------------------------------- #
#  Percorso completo con avvistamenti
# --------------------------------------------------------------------------- #


def esegui_movimento(
    galassia: Galassia,
    partenza: Posizione,
    segmenti: list[Segmento],
    radar: int,
    serbatoi: int,
    atterraggio_dichiarato: bool = False,
    parsec_per_serbatoio: int = PARSEC_PER_SERBATOIO,
    controllo_carburante: bool = True,
) -> Movimento:
    """Traccia la rotta, ripercorrela per gli avvistamenti e stabilisce dove si ferma."""
    if not 0 <= radar <= RADAR_MASSIMI:
        raise RottaNonValida(f"i radar imbarcati vanno da 0 a {RADAR_MASSIMI}")
    if serbatoi < 1:
        raise RottaNonValida("va imbarcato almeno un serbatoio")

    dichiarati = sum(s.parsec for s in segmenti)
    autonomia = serbatoi * parsec_per_serbatoio
    if controllo_carburante and dichiarati > autonomia:
        raise RottaNonValida(
            f"rotta di {dichiarati} parsec con {serbatoi} serbatoi"
            f" (autonomia {autonomia} parsec): lo S.C. non puo' tracciarla."
        )

    passi, motivo = traccia(partenza, segmenti, galassia.lato)
    pianeta_di_partenza = galassia.a(partenza)

    # Si ripercorre la rotta: la gittata e' di 1 parsec per radar, fino a 3.
    visti: dict[str, list[tuple[int, int, int, int, Posizione]]] = {}
    limite_utile = len(passi) - 1
    atterraggio_su: str | None = None
    atterraggio_obbligato = False

    for ordine, passo in enumerate(passi):
        # Senza radar a bordo non esiste alcun avvistamento, nemmeno a distanza zero.
        if radar:
            for pianeta, distanza in galassia.entro_raggio(passo.posizione, radar):
                # Il sistema da cui si e' appena decollato non si "avvista": lo si conosce gia'.
                if pianeta is pianeta_di_partenza:
                    continue
                dx = pianeta.posizione.x - passo.posizione.x
                dy = pianeta.posizione.y - passo.posizione.y
                visti.setdefault(pianeta.id, []).append((passo.indice, distanza, dx, dy, passo.posizione))

        attraversato = galassia.a(passo.posizione)
        if attraversato is None or ordine == 0 or attraversato is pianeta_di_partenza:
            continue

        ultimo_passo = ordine == len(passi) - 1
        if ultimo_passo and atterraggio_dichiarato:
            atterraggio_su = attraversato.id
            motivo = "atterraggio dichiarato"
        elif radar == 0:
            # Senza radar l'atterraggio e' obbligatorio sul pianeta attraversato.
            atterraggio_su = attraversato.id
            atterraggio_obbligato = True
            motivo = "atterraggio obbligato (nessun radar a bordo)"
        else:
            # Il movimento termina sul primo parsec in cui e' avvenuto l'avvistamento.
            primo = min(indice for indice, *_ in visti.get(attraversato.id, [(passo.indice,)]))
            limite_utile = next(o for o, p in enumerate(passi) if p.indice >= primo)
            motivo = "sistema sulla rotta: fermata al primo parsec di avvistamento"
        limite_utile = ordine if atterraggio_su else limite_utile
        break

    passi = passi[: limite_utile + 1]
    indice_finale = passi[-1].indice
    avvistamenti = _componi_avvistamenti(visti, indice_finale)

    movimento = Movimento(
        partenza=partenza,
        arrivo=passi[-1].posizione,
        segmenti=list(segmenti),
        passi=passi,
        parsec_percorsi=indice_finale,
        parsec_dichiarati=dichiarati,
        radar=radar,
        serbatoi=serbatoi,
        avvistamenti=avvistamenti,
        motivo_fermata=motivo,
        atterraggio_su=atterraggio_su,
        atterraggio_obbligato=atterraggio_obbligato,
    )
    movimento.comunicazioni = _comunicazioni(movimento, galassia)
    return movimento


def _componi_avvistamenti(
    visti: dict[str, list[tuple[int, int, int, int, Posizione]]],
    indice_finale: int,
) -> list[Avvistamento]:
    """Per ogni pianeta si comunica il parsec piu' vicino (sez. E, punto a)."""
    risultato: list[Avvistamento] = []
    for pianeta_id, occorrenze in visti.items():
        valide = [o for o in occorrenze if o[0] <= indice_finale]
        if not valide:
            continue
        indice, distanza, dx, dy, da = min(valide, key=lambda o: (o[1], o[0]))
        risultato.append(
            Avvistamento(
                pianeta_id=pianeta_id,
                parsec_rotta=indice,
                distanza=distanza,
                direzione=scomponi_direzione(dx, dy),
                da=da,
                tutti_i_parsec=sorted({o[0] for o in valide}),
            )
        )
    risultato.sort(key=lambda a: (a.parsec_rotta, a.distanza))
    return risultato


def _comunicazioni(movimento: Movimento, galassia: Galassia) -> list[str]:
    """Le frasi che lo S.C. pronuncia, «in modo da essere recepito da tutti»."""
    righe: list[str] = []
    if movimento.radar == 0:
        righe.append("Nessun radar a bordo: nessun avvistamento possibile.")
    elif not movimento.avvistamenti:
        righe.append(f"Rotta percorsa, {movimento.parsec_percorsi} parsec: nessun avvistamento.")

    for avvistamento in movimento.avvistamenti:
        righe.append(avvistamento.comunicazione)
        if len(avvistamento.tutti_i_parsec) > 1:
            elenco = ", ".join(str(i) for i in avvistamento.tutti_i_parsec)
            righe.append(f"   (lo stesso sistema resta visibile dai parsec {elenco})")

    if movimento.motivo_fermata == "limite della zona":
        righe.append(
            f"La nave si e' fermata sul limite della zona, nel parsec {movimento.arrivo.sigla}"
            f" del livello {movimento.arrivo.livello + 1}."
        )
    elif movimento.motivo_fermata == "limite verticale della zona":
        righe.append(
            f"Non esistono livelli oltre il {movimento.arrivo.livello + 1}: la nave resta"
            f" sul livello {movimento.arrivo.livello + 1}, parsec {movimento.arrivo.sigla}."
        )
    elif movimento.motivo_fermata.startswith("sistema sulla rotta"):
        righe.append(
            "La rotta dichiarata attraversa un sistema: movimento terminato sul primo parsec"
            f" di avvistamento ({movimento.arrivo.sigla}). Per scendere occorre dichiarare ATTERRAGGIO."
        )

    if movimento.atterraggio_su:
        pianeta = galassia.per_id(movimento.atterraggio_su)
        avviso = " — atterraggio obbligatorio" if movimento.atterraggio_obbligato else ""
        righe.append(f"ATTERRAGGIO sul sistema in {pianeta.posizione.sigla}{avviso}.")

    righe.append(
        f"Posizione finale: livello {movimento.arrivo.livello + 1}, parsec {movimento.arrivo.sigla}"
        f" — {movimento.parsec_percorsi} parsec percorsi su {movimento.parsec_dichiarati} dichiarati."
    )
    return righe
