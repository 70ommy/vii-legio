"""La cella metallica dello S.C.: stato della partita, navi, registro.

Tiene insieme galassia, dadiera, Segnalini Nave e tutto quanto lo S.C. deve
ricordare fra un movimento e l'altro.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .dadi import Dadiera
from .generatore import genera_galassia
from .modello import (
    LATO_PREDEFINITO,
    PARSEC_PER_SERBATOIO,
    RADAR_MASSIMI,
    Galassia,
    Pianeta,
    Posizione,
    occulta_per_uc,
)
from .rotte import Movimento, analizza_rotta, descrivi_rotta, distanza_minima_da_buco_nero, esegui_movimento
from .schede import (
    completa_informazioni,
    prossimo_livello,
    risolvi_attivita,
    risolvi_danni,
    risolvi_livello,
    risolvi_massa_atterraggio,
    risolvi_zona_atterraggio,
    tira_arrivi,
    tira_presenze,
    voce_gi,
)

COLORI_SN = ("#ff5c39", "#ffd23f", "#39d7c4", "#c66bff", "#7ee081", "#ff8ad2")
UFFICIALI_PREDEFINITI = ("LEGIONARIO I", "LEGIONARIO II")


class ErroreDiRegolamento(ValueError):
    """Mossa non ammessa: lo S.C. la respinge prima di commettere un errore."""


@dataclass
class Nave:
    """Un U.C. in azione, con i suoi due Segnalini Nave."""

    nome: str
    colore: str
    posizione: Posizione
    partenza_movimento: Posizione
    serbatoi: int = 3
    radar: int = 3
    computer: int = 2
    punti: int = 0
    a_terra: str | None = None
    informazioni_residue: int = 0
    ultimo_movimento: dict | None = None
    # Regolamento avanzato — spazio esterno (assunzioni non confermate dal manuale
    # fisico: vedi tabella "Assunzioni prese" nel README).
    classe_massa: int = 2  # 1 leggera, 2 media, 3 pesante — usata dalla formula del B.N.
    princeps_psi: bool = False  # percepisce R.M.G./D.N. altrimenti invisibili
    riatterraggio_usato: bool = False  # sez. D — un solo nuovo tentativo di zona per atterraggio
    # Terminale di bordo (pacchetto 3D): l'U.C. dichiara la rotta dal telefono; resta qui
    # in attesa finche' lo S.C. non la esegue dalla consolle. None = nessuna dichiarazione.
    dichiarazione_in_attesa: dict | None = None

    def in_chiaro(self) -> dict:
        return {
            "nome": self.nome,
            "colore": self.colore,
            "posizione": {
                "livello": self.posizione.livello,
                "x": self.posizione.x,
                "y": self.posizione.y,
                "sigla": self.posizione.sigla,
                "riferimento": self.posizione.riferimento,
            },
            "partenza_movimento": {
                "livello": self.partenza_movimento.livello,
                "x": self.partenza_movimento.x,
                "y": self.partenza_movimento.y,
                "sigla": self.partenza_movimento.sigla,
            },
            "serbatoi": self.serbatoi,
            "radar": self.radar,
            "computer": self.computer,
            "punti": self.punti,
            "a_terra": self.a_terra,
            "informazioni_residue": self.informazioni_residue,
            "ultimo_movimento": self.ultimo_movimento,
            "classe_massa": self.classe_massa,
            "princeps_psi": self.princeps_psi,
            "dichiarazione_in_attesa": self.dichiarazione_in_attesa,
        }


@dataclass
class Sessione:
    """Una partita di esplorazione seguita da un solo S.C."""

    galassia: Galassia
    dadiera: Dadiera
    navi: dict[str, Nave] = field(default_factory=dict)
    registro: list[dict] = field(default_factory=list)
    turno: int = 1
    ordine_turno: list[str] = field(default_factory=list)
    mosse_turno: list[str] = field(default_factory=list)  # chi ha gia' mosso in questo turno (indicatore, non vincolo)
    spazio_esterno: bool = False
    parsec_per_serbatoio: int = PARSEC_PER_SERBATOIO
    controllo_carburante: bool = True
    distribuzione: str = "bilanciata"

    # ------------------------------------------------------------------ #
    #  Avvio
    # ------------------------------------------------------------------ #

    @classmethod
    def nuova(
        cls,
        seme: str | None = None,
        lato: int = LATO_PREDEFINITO,
        distribuzione: str = "bilanciata",
        ufficiali: list[str] | None = None,
        spazio_esterno: bool = False,
        dettagli_navi: dict[str, dict] | None = None,
    ) -> Sessione:
        galassia, dadiera = genera_galassia(seme=seme, lato=lato, distribuzione=distribuzione)
        return cls._avvia(
            galassia, dadiera,
            distribuzione=distribuzione,
            ufficiali=ufficiali,
            spazio_esterno=spazio_esterno,
            dettagli_navi=dettagli_navi,
            messaggio_creazione=(
                f"Zona di galassia creata: 4 livelli, 36 sistemi, TABULA {galassia.lato}×{galassia.lato} parsec."
                f" Pianeta base in {galassia.base.posizione.riferimento}. Matricola {galassia.seme}."
            ),
        )

    @classmethod
    def nuova_da_galassia(
        cls,
        galassia: Galassia,
        seme: str | None = None,
        ufficiali: list[str] | None = None,
        spazio_esterno: bool = False,
        dettagli_navi: dict[str, dict] | None = None,
    ) -> Sessione:
        """Regolamento avanzato, Parte II — avvia la partita su una galassia costruita a mano.

        La Dadiera serve comunque durante il gioco (D.N., TAB. O/P): si usa il seme
        indicato o, in mancanza, la matricola assegnata dall'editor alla bozza.
        """
        dadiera = Dadiera(seme or galassia.seme or Dadiera.seme_casuale())
        return cls._avvia(
            galassia, dadiera,
            distribuzione="manuale",
            ufficiali=ufficiali,
            spazio_esterno=spazio_esterno,
            dettagli_navi=dettagli_navi,
            messaggio_creazione=(
                f"Zona di galassia creata a mano dal master: TABULA {galassia.lato}×{galassia.lato} parsec."
                f" Pianeta base in {galassia.base.posizione.riferimento}. Matricola {galassia.seme}."
            ),
        )

    @classmethod
    def _avvia(
        cls,
        galassia: Galassia,
        dadiera: Dadiera,
        *,
        distribuzione: str,
        ufficiali: list[str] | None,
        spazio_esterno: bool,
        dettagli_navi: dict[str, dict] | None,
        messaggio_creazione: str,
    ) -> Sessione:
        sessione = cls(
            galassia=galassia,
            dadiera=dadiera,
            spazio_esterno=spazio_esterno,
            distribuzione=distribuzione,
        )
        nomi = [n.strip().upper() for n in (ufficiali or UFFICIALI_PREDEFINITI) if n.strip()]
        dettagli_navi = dettagli_navi or {}
        base = galassia.base.posizione
        for indice, nome in enumerate(nomi or list(UFFICIALI_PREDEFINITI)):
            dettagli = dettagli_navi.get(nome, {})
            nave = Nave(
                nome=nome,
                colore=COLORI_SN[indice % len(COLORI_SN)],
                posizione=base,
                partenza_movimento=base,
                a_terra=galassia.base.id,
                classe_massa=int(dettagli.get("classe_massa") or 2),
                princeps_psi=bool(dettagli.get("princeps_psi")),
            )
            # Le informazioni si possono chiedere anche all'inizio del movimento (sez. F).
            nave.informazioni_residue = nave.computer
            sessione.navi[nome] = nave
        # In una successione stabilita preventivamente a sorte (sez. D).
        sessione.ordine_turno = list(sessione.navi)
        dadiera.mescola(sessione.ordine_turno)

        sessione.annota("C.S.C.", "sistema", messaggio_creazione)
        sessione.annota(
            "C.S.C.",
            "sistema",
            "Ordine di gioco estratto a sorte: " + " → ".join(sessione.ordine_turno) + ".",
        )
        return sessione

    # ------------------------------------------------------------------ #
    #  Registro
    # ------------------------------------------------------------------ #

    def annota(self, attore: str, tipo: str, testo: str, dettaglio: dict | None = None) -> dict:
        voce = {
            "n": len(self.registro) + 1,
            "turno": self.turno,
            "attore": attore,
            "tipo": tipo,
            "testo": testo,
            "dettaglio": dettaglio or {},
        }
        self.registro.append(voce)
        return voce

    # ------------------------------------------------------------------ #
    #  Movimento
    # ------------------------------------------------------------------ #

    def nave(self, nome: str) -> Nave:
        chiave = (nome or "").strip().upper()
        if chiave not in self.navi:
            raise ErroreDiRegolamento(f"U.C. non in servizio: {nome!r}")
        return self.navi[chiave]

    def dichiara_rotta(
        self,
        nome: str,
        rotta: str,
        serbatoi: int,
        radar: int,
        computer: int | None = None,
        atterraggio: bool = False,
    ) -> dict:
        """Sez. D — l'U.C. dichiara rotta, serbatoi e radar; lo S.C. traccia ed esegue."""
        nave = self.nave(nome)
        if not 0 <= radar <= RADAR_MASSIMI:
            raise ErroreDiRegolamento(f"i radar imbarcati vanno da 0 a {RADAR_MASSIMI}")

        segmenti = analizza_rotta(rotta)
        movimento = esegui_movimento(
            self.galassia,
            nave.posizione,
            segmenti,
            radar=radar,
            serbatoi=serbatoi,
            atterraggio_dichiarato=atterraggio,
            parsec_per_serbatoio=self.parsec_per_serbatoio,
            controllo_carburante=self.controllo_carburante,
            dadiera=self.dadiera,
            princeps_psi=nave.princeps_psi,
        )

        self._barra_pianeta_di_partenza(nave, movimento)
        self._rischio_buco_nero(nave, movimento)

        nave.partenza_movimento = movimento.partenza
        nave.posizione = movimento.arrivo
        nave.serbatoi, nave.radar = serbatoi, radar
        if computer is not None:
            nave.computer = max(0, computer)
        nave.informazioni_residue = nave.computer
        nave.a_terra = movimento.atterraggio_su
        nave.ultimo_movimento = movimento.in_chiaro()
        # Chi muove ha "fatto il suo turno" (indicatore morbido) e non ha piu' nulla in attesa.
        if nave.nome not in self.mosse_turno:
            self.mosse_turno.append(nave.nome)
        nave.dichiarazione_in_attesa = None

        for pianeta_id in {a.pianeta_id for a in movimento.avvistamenti}:
            pianeta = self.galassia.per_id(pianeta_id)
            if pianeta and nave.nome not in pianeta.avvistato_da:
                pianeta.avvistato_da.append(nave.nome)

        self.annota(
            nave.nome,
            "rotta",
            f"«Rotta {descrivi_rotta(segmenti)} — {serbatoi} serbatoi e {radar} radar"
            f"{', ATTERRAGGIO' if atterraggio else ''}.»",
            {"movimento": nave.ultimo_movimento},
        )
        for riga in movimento.comunicazioni:
            self.annota("S.C.", "avvistamento", riga)

        risposta: dict = {"movimento": nave.ultimo_movimento, "atterraggio": None}
        # Le informazioni gia' note vengono ripetute gratuitamente (sez. F).
        ripetizioni = self._ripeti_informazioni_note(movimento)
        if ripetizioni:
            risposta["ripetizioni"] = ripetizioni

        if movimento.atterraggio_su:
            risposta["atterraggio"] = self.atterra(nave.nome)
        return risposta

    def _barra_pianeta_di_partenza(self, nave: Nave, movimento: Movimento) -> None:
        """Sez. F — chi riparte da un pianeta lo lascia «noto»: barrato e non piu' visitabile.

        Il pianeta base resta escluso: e' la casa della Legio, ci si torna sempre.
        """
        if nave.a_terra is None or movimento.parsec_percorsi == 0:
            return
        pianeta = self.galassia.per_id(nave.a_terra)
        if pianeta is None or pianeta.base or pianeta.barrato:
            return
        pianeta.barrato = True
        self.annota(
            "S.C.",
            "sistema",
            f"Il sistema in {pianeta.posizione.riferimento} viene barrato sulla TABULA:"
            " ormai noto, non e' piu' visitabile da nessuno.",
        )

    def _rischio_buco_nero(self, nave: Nave, movimento: Movimento) -> None:
        """Sez. avanzata, parte I·A — B.N. invisibile ai radar: rischio sempre controllato.

        `DISTANZA − MASSA(classe_nave) − ESITO(d6)`: un risultato negativo e' un
        numero di danni, letto sulla TAB. C. La posizione del B.N. non si rivela mai.
        """
        distanza = distanza_minima_da_buco_nero(movimento, self.galassia)
        if distanza is None:
            return
        tiro = self.dadiera.d6(f"B.N. — rischio per {nave.nome}")
        numero_danni = distanza - nave.classe_massa - tiro.esito
        if numero_danni <= 0:
            self.annota(
                "S.C.",
                "sistema",
                f"{nave.nome} sfiora un campo gravitazionale anomalo (posizione non rivelata):"
                f" nessun danno [{tiro.dado} → {tiro.esito}].",
            )
            return
        resoconto = risolvi_danni(numero_danni, self.dadiera)
        self.annota(
            "S.C.",
            "danni",
            f"{nave.nome} subisce {numero_danni} danni da un campo gravitazionale anomalo"
            f" (posizione non rivelata) [{tiro.dado} → {tiro.esito}]: {resoconto['testo']}",
            resoconto,
        )

    def _ripeti_informazioni_note(self, movimento: Movimento) -> list[dict]:
        ripetizioni = []
        for avvistamento in movimento.avvistamenti:
            pianeta = self.galassia.per_id(avvistamento.pianeta_id)
            if pianeta is None or not pianeta.livelli_noti:
                continue
            righe = [f"{lv} livello: {self._frase_nota(pianeta, lv)}" for lv in pianeta.livelli_noti]
            ripetizioni.append({"pianeta": pianeta.id, "sigla": pianeta.posizione.sigla, "righe": righe})
            self.annota(
                "S.C.",
                "ripetizione",
                f"Notizie gia' di dominio pubblico sul sistema in {pianeta.posizione.sigla}"
                f" (ripetute gratuitamente): {' · '.join(righe)}",
            )
        return ripetizioni

    def _frase_nota(self, pianeta: Pianeta, livello: str) -> str:
        from .schede import frase_informazione

        informazioni = pianeta.informazioni
        chiavi = {
            "I": ("tipo", "codice", "classe", "ambiente"),
            "I-bis": ("radioattivita", "nota_radio"),
            "II": ("vita",),
            "III": ("sapienza", "terminale", "esito_finale"),
            "IV": ("razza", "rif_gi"),
        }[livello]
        return frase_informazione(livello, {k: informazioni[k] for k in chiavi if k in informazioni})

    # ------------------------------------------------------------------ #
    #  Informazioni
    # ------------------------------------------------------------------ #

    def richiedi_informazione(self, nome: str, pianeta_id: str) -> dict:
        """Sez. F — una richiesta consuma un computer di bordo; il D.N.S. la spreca."""
        nave = self.nave(nome)
        pianeta = self.galassia.per_id(pianeta_id)
        if pianeta is None:
            raise ErroreDiRegolamento(f"sistema inesistente: {pianeta_id}")
        if nave.informazioni_residue <= 0:
            raise ErroreDiRegolamento(
                f"{nave.nome} ha esaurito le informazioni del movimento"
                f" ({nave.computer} computer installati a bordo)."
            )
        if not self._entro_radar(nave, pianeta):
            raise ErroreDiRegolamento(
                "Le informazioni sono date solo su pianeti entro il raggio dei radar:"
                f" {pianeta.posizione.sigla} non lo e' ne' dal punto di partenza ne' da quello d'arrivo."
            )
        livello = prossimo_livello(pianeta, self.spazio_esterno)
        if livello is None:
            raise ErroreDiRegolamento(
                f"sul sistema in {pianeta.posizione.sigla} non restano livelli di informazione da dare."
            )

        nave.informazioni_residue -= 1
        resoconto = risolvi_livello(pianeta, livello, self.dadiera)
        etichetta = f"{livello} livello di informazione su {pianeta.posizione.sigla}"
        dado = f" [{resoconto['dado']} → {resoconto['esito']}]" if resoconto["dado"] else ""
        self.annota("S.C.", "informazione", f"{etichetta}{dado}: {resoconto['testo']}", resoconto)

        if resoconto["dati"].get("rif_gi"):
            resoconto["gi"] = self._apri_gi(pianeta, resoconto["dati"]["rif_gi"])
        resoconto["informazioni_residue"] = nave.informazioni_residue
        resoconto["pianeta_stato"] = pianeta.in_chiaro()
        return resoconto

    def _entro_radar(self, nave: Nave, pianeta: Pianeta) -> bool:
        raggio = nave.radar
        if raggio <= 0:
            return False
        for centro in {nave.posizione, nave.partenza_movimento}:
            if any(p is pianeta for p, _ in self.galassia.entro_raggio(centro, raggio)):
                return True
        return False

    def _apri_gi(self, pianeta: Pianeta, riferimento: int) -> dict:
        """Il IV livello da' il riferimento sulla G.I.: le notizie vanno lette integralmente.

        Il numero di Alieni presenti si dichiara con un nuovo lancio, prima del resto.
        """
        voce = voce_gi(riferimento)
        if voce is None:
            raise ErroreDiRegolamento(f"riferimento G.I. mancante: {riferimento}")
        if pianeta.alieni_presenti is None:
            pianeta.alieni_presenti, tiro = tira_presenze(voce, self.dadiera)
            self.annota(
                "S.C.",
                "presenze",
                f"TAB. PRESENZE [{tiro['dado']} → {tiro['esito']}]:"
                f" {pianeta.alieni_presenti} {voce['nome']} presenti in {pianeta.posizione.sigla}.",
            )
        self.annota("S.C.", "gi", f"G.I. n. {riferimento} — {voce['nome']}: {voce['descrizione']}")
        return {"voce": voce, "alieni_presenti": pianeta.alieni_presenti}

    # ------------------------------------------------------------------ #
    #  Atterraggio
    # ------------------------------------------------------------------ #

    def atterra(self, nome: str, pianeta_id: str | None = None) -> dict:
        """Sez. G — completa le informazioni, conta gli Alieni, svolge le attivita', assegna i punti."""
        nave = self.nave(nome)
        pianeta = (
            self.galassia.per_id(pianeta_id or nave.a_terra or "")
            or self.galassia.a(nave.posizione)  # il sistema su cui la nave si trova
        )
        if pianeta is None:
            raise ErroreDiRegolamento("nessun sistema sotto la nave: l'atterraggio non e' possibile.")
        if pianeta.posizione != nave.posizione:
            raise ErroreDiRegolamento(
                f"{nave.nome} non si trova su {pianeta.posizione.sigla}."
            )

        nave.a_terra = pianeta.id
        nave.riatterraggio_usato = False
        risposta: dict = {"pianeta": pianeta.id, "sigla": pianeta.posizione.sigla, "informazioni": [], "punti": 0}

        self.annota(nave.nome, "atterraggio", f"«ATTERRAGGIO sul sistema in {pianeta.posizione.sigla}.»")
        mancanti = completa_informazioni(pianeta, self.dadiera, self.spazio_esterno)
        for resoconto in mancanti:
            dado = f" [{resoconto['dado']} → {resoconto['esito']}]" if resoconto["dado"] else ""
            self.annota(
                "S.C.",
                "informazione",
                f"{resoconto['livello']} livello (completamento allo sbarco){dado}: {resoconto['testo']}",
                resoconto,
            )
        risposta["informazioni"] = mancanti
        risposta["pianeta_stato"] = pianeta.in_chiaro()

        if self.spazio_esterno:
            resoconto_massa = risolvi_massa_atterraggio(pianeta, self.dadiera)
            self.annota("S.C.", "sistema", f"TAB. O — {resoconto_massa['testo']}", resoconto_massa)
            risposta["rischio_massa"] = resoconto_massa
            if resoconto_massa["danni"]:
                resoconto_danni = risolvi_danni(resoconto_massa["danni"], self.dadiera)
                self.annota("S.C.", "danni", f"TAB. C — {resoconto_danni['testo']}", resoconto_danni)
                risposta["danni_massa"] = resoconto_danni
            resoconto_zona = risolvi_zona_atterraggio(pianeta, self.dadiera)
            self.annota("S.C.", "sistema", f"TAB. P — {resoconto_zona['testo']}", resoconto_zona)
            risposta["zona_atterraggio"] = resoconto_zona

        riferimento = pianeta.informazioni.get("rif_gi")
        if riferimento is None:
            self.annota("S.C.", "sistema", "Nessun incontro: sbarco senza esiti da tabella.")
            return risposta

        voce = voce_gi(riferimento)
        risposta["gi"] = self._apri_gi(pianeta, riferimento)["voce"]
        risposta["alieni_presenti"] = pianeta.alieni_presenti

        esiti = risolvi_attivita(voce, self.dadiera)
        punti = int(voce["scheda"].get("punti_base", 0)) + sum(e["punti"] for e in esiti)
        for esito in esiti:
            self.annota(
                "S.C.",
                "attivita",
                f"{esito['nome']} — esito controllato dall'{esito['controllo']}"
                f" [{esito['dado']} → {esito['esito']}]: {esito['testo']}"
                f" ({esito['punti']:+d} punti)",
                esito,
            )
        arrivi, tiro_arrivi = tira_arrivi(voce, self.dadiera)
        self.annota(
            "S.C.",
            "arrivi",
            f"TAB. ARRIVI [{tiro_arrivi['dado']} → {tiro_arrivi['esito']}]:"
            f" {arrivi} nuovi Alieni per ogni turno di permanenza sul pianeta.",
        )

        nave.punti += punti
        self.annota(
            "S.C.",
            "punteggio",
            f"Punti attribuiti a {nave.nome}: {punti:+d} (totale {nave.punti}).",
        )
        risposta.update({"attivita": esiti, "arrivi_per_turno": arrivi, "punti": punti, "punti_totali": nave.punti})
        return risposta

    def riatterra(self, nome: str) -> dict:
        """Sez. avanzata, parte I·D — l'U.C. insoddisfatto della zona tenta un nuovo atterraggio.

        Un solo tentativo per sbarco; a differenza di un decollo vero non barra il
        pianeta (non lo rende "noto").
        """
        nave = self.nave(nome)
        if not self.spazio_esterno:
            raise ErroreDiRegolamento("il riatterraggio e' una regola dello spazio esterno")
        if not nave.a_terra:
            raise ErroreDiRegolamento(f"{nave.nome} non e' atterrata: nessun riatterraggio possibile.")
        if nave.riatterraggio_usato:
            raise ErroreDiRegolamento(f"{nave.nome} ha gia' tentato un riatterraggio su questo sbarco.")

        nave.riatterraggio_usato = True
        pianeta = self.galassia.per_id(nave.a_terra)
        resoconto_zona = risolvi_zona_atterraggio(pianeta, self.dadiera)
        self.annota(
            nave.nome,
            "sistema",
            f"«RIATTERRAGGIO — nuova zona.» TAB. P — {resoconto_zona['testo']}",
            resoconto_zona,
        )
        return resoconto_zona

    # ------------------------------------------------------------------ #
    #  Dichiarazioni dal Terminale di bordo (pacchetto 3D)
    # ------------------------------------------------------------------ #

    @property
    def turno_di(self) -> str | None:
        """Indicatore morbido: il primo dell'ordine che non ha ancora mosso in questo turno.

        Non e' un vincolo — `dichiara_rotta` non lo controlla. Serve al Terminale e alla
        consolle per *mostrare* di chi e' il turno; l'arbitro resta lo S.C.
        """
        for nome in self.ordine_turno:
            if nome not in self.mosse_turno:
                return nome
        return None

    def deposita_dichiarazione(
        self,
        nome: str,
        rotta: str,
        serbatoi: int,
        radar: int,
        computer: int | None = None,
        atterraggio: bool = False,
    ) -> dict:
        """L'U.C. dichiara la rotta dal telefono; non viene eseguita finche' lo S.C. non risolve."""
        nave = self.nave(nome)
        if not 0 <= radar <= RADAR_MASSIMI:
            raise ErroreDiRegolamento(f"i radar imbarcati vanno da 0 a {RADAR_MASSIMI}")
        analizza_rotta(rotta)  # convalida la forma della rotta subito, senza eseguirla
        nave.dichiarazione_in_attesa = {
            "rotta": rotta,
            "serbatoi": serbatoi,
            "radar": radar,
            "computer": computer,
            "atterraggio": bool(atterraggio),
            "turno": self.turno,
        }
        return {"nave": nave.nome, "dichiarazione": nave.dichiarazione_in_attesa}

    def annulla_dichiarazione(self, nome: str) -> dict:
        """Ritira una dichiarazione in attesa (la puo' fare l'U.C. o lo S.C.)."""
        nave = self.nave(nome)
        nave.dichiarazione_in_attesa = None
        return {"nave": nave.nome}

    def risolvi_dichiarazione(self, nome: str) -> dict:
        """Lo S.C. esegue dalla consolle la rotta dichiarata dall'U.C., riusando `dichiara_rotta`."""
        nave = self.nave(nome)
        dichiarazione = nave.dichiarazione_in_attesa
        if not dichiarazione:
            raise ErroreDiRegolamento(f"{nave.nome} non ha dichiarazioni in attesa.")
        # `dichiara_rotta` azzera da se' la dichiarazione in attesa a esecuzione avvenuta.
        return self.dichiara_rotta(
            nome=nave.nome,
            rotta=dichiarazione["rotta"],
            serbatoi=int(dichiarazione["serbatoi"]),
            radar=int(dichiarazione["radar"]),
            computer=dichiarazione.get("computer"),
            atterraggio=bool(dichiarazione.get("atterraggio")),
        )

    # ------------------------------------------------------------------ #
    #  Turni
    # ------------------------------------------------------------------ #

    def chiudi_turno(self) -> dict:
        self.turno += 1
        self.mosse_turno = []  # nuovo turno: tutti tornano "da muovere"
        for nave in self.navi.values():
            nave.informazioni_residue = nave.computer
        self.annota("C.S.C.", "sistema", f"Inizio del turno {self.turno}.")
        return {"turno": self.turno}

    # ------------------------------------------------------------------ #
    #  Stato
    # ------------------------------------------------------------------ #

    def in_chiaro(self, vista: str = "sc") -> dict:
        """`vista='sc'` mostra tutto; `vista='uc'` e' la plancia proiettata ai Comandanti."""
        galassia = self.galassia.in_chiaro()
        if vista == "uc":
            galassia = occulta_per_uc(galassia)
        return {
            "vista": vista,
            "turno": self.turno,
            "ordine_turno": list(self.ordine_turno),
            "turno_di": self.turno_di,
            "mosse_turno": list(self.mosse_turno),
            "distribuzione": self.distribuzione,
            "spazio_esterno": self.spazio_esterno,
            "parsec_per_serbatoio": self.parsec_per_serbatoio,
            "controllo_carburante": self.controllo_carburante,
            "radar_massimi": RADAR_MASSIMI,
            "galassia": galassia,
            "navi": [n.in_chiaro() for n in self.navi.values()],
            "registro": list(self.registro),
            "tiri": len(self.dadiera.registro),
        }
