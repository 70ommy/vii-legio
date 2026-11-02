"""Modello della TABULA SPATII: parsec, direzioni, pianeti, livelli, galassia.

Convenzioni (sez. C del Regolamento):
  * 4 settori = 4 livelli tridimensionali;
  * il livello 0 e' il piu' alto (in alto a sinistra), il 3 il piu' basso;
  * fra un livello e l'altro corrono 4 parsec;
  * 9 pianeti per livello, 1 parsec quadrato ciascuno, 36 in totale;
  * 1 parsec = 1 quadretto.
"""

from __future__ import annotations

from dataclasses import dataclass, field

LETTERE = "ABCDEFGHJKLMNPQRSTUVZ"  # senza I e O: si confondono con 1 e 0 sui terminali
LIVELLI = 4
PIANETI_PER_LIVELLO = 9
PARSEC_FRA_LIVELLI = 4
LATO_PREDEFINITO = 12
RADAR_MASSIMI = 3
PARSEC_PER_SERBATOIO = 5  # dedotto dall'esempio della sez. E: «10 N, +5 E — 3 serbatoi»

NOMI_LIVELLO = ("I — Livello Alto", "II — Livello Medio-Alto", "III — Medio-Basso", "IV — Livello Basso")


# --------------------------------------------------------------------------- #
#  Direzioni
# --------------------------------------------------------------------------- #

# y cresce verso il basso: il Nord e' in alto sulla TABULA.
DIREZIONI: dict[str, tuple[int, int]] = {
    "N": (0, -1),
    "NE": (1, -1),
    "E": (1, 0),
    "SE": (1, 1),
    "S": (0, 1),
    "SO": (-1, 1),
    "O": (-1, 0),
    "NO": (-1, -1),
}

NOMI_DIREZIONE = {
    "N": "Nord",
    "NE": "Nord-Est",
    "E": "Est",
    "SE": "Sud-Est",
    "S": "Sud",
    "SO": "Sud-Ovest",
    "O": "Ovest",
    "NO": "Nord-Ovest",
    "SU": "Zenit",   # verso il livello superiore
    "GIU": "Nadir",  # verso il livello inferiore
}

# Alias tollerati nella dichiarazione di rotta dell'U.C.
ALIAS_DIREZIONE = {
    "NORD": "N",
    "NORDEST": "NE",
    "NORD-EST": "NE",
    "EST": "E",
    "SUDEST": "SE",
    "SUD-EST": "SE",
    "SUD": "S",
    "SUDOVEST": "SO",
    "SUD-OVEST": "SO",
    "SW": "SO",
    "OVEST": "O",
    "W": "O",
    "NORDOVEST": "NO",
    "NORD-OVEST": "NO",
    "NW": "NO",
    "SU": "SU",
    "ALTO": "SU",
    "ZENIT": "SU",
    "Z": "SU",
    "GIU": "GIU",
    "GIÙ": "GIU",
    "BASSO": "GIU",
    "NADIR": "GIU",
}

VERTICALI = frozenset({"SU", "GIU"})


def normalizza_direzione(testo: str) -> str:
    """Restituisce la sigla canonica di una direzione dichiarata dall'U.C."""
    grezzo = testo.strip().upper().replace(" ", "")
    if grezzo in DIREZIONI or grezzo in VERTICALI:
        return grezzo
    if grezzo in ALIAS_DIREZIONE:
        return ALIAS_DIREZIONE[grezzo]
    raise ValueError(f"direzione non riconosciuta: {testo!r}")


def scomponi_direzione(dx: int, dy: int) -> str:
    """Traduce uno scostamento nella dizione della sez. E, es. «2 Ovest + 1 Nord-Ovest».

    La distanza in parsec e' la distanza di Chebyshev: si procede in diagonale
    finche' possibile, poi in linea retta.
    """
    if dx == 0 and dy == 0:
        return "sulla stessa posizione"
    diagonali = min(abs(dx), abs(dy))
    dritti = max(abs(dx), abs(dy)) - diagonali

    pezzi: list[str] = []
    if dritti:
        sigla = ("E" if dx > 0 else "O") if abs(dx) > abs(dy) else ("S" if dy > 0 else "N")
        pezzi.append(f"{dritti} {NOMI_DIREZIONE[sigla]}")
    if diagonali:
        sigla = ("S" if dy > 0 else "N") + ("E" if dx > 0 else "O")
        pezzi.append(f"{diagonali} {NOMI_DIREZIONE[sigla]}")
    return " + ".join(pezzi)


def distanza_piana(a: Posizione, b: Posizione) -> int:
    """Distanza di Chebyshev sullo stesso piano, senza tener conto del livello."""
    return max(abs(a.x - b.x), abs(a.y - b.y))


def distanza_parsec(a: Posizione, b: Posizione) -> int:
    """Distanza in parsec fra due posizioni, livelli compresi (4 parsec a salto)."""
    return distanza_piana(a, b) + abs(a.livello - b.livello) * PARSEC_FRA_LIVELLI


# --------------------------------------------------------------------------- #
#  Posizioni
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True, order=True)
class Posizione:
    """Un parsec quadrato della TABULA SPATII."""

    livello: int
    x: int
    y: int

    @property
    def sigla(self) -> str:
        """Riferimento in lettere e numeri riportato a fianco di ogni livello."""
        return f"{LETTERE[self.x]}{self.y + 1}"

    @property
    def riferimento(self) -> str:
        return f"L{self.livello + 1}·{self.sigla}"

    def traslata(self, dx: int, dy: int, dlivello: int = 0) -> Posizione:
        return Posizione(self.livello + dlivello, self.x + dx, self.y + dy)

    def dentro(self, lato: int) -> bool:
        return 0 <= self.x < lato and 0 <= self.y < lato and 0 <= self.livello < LIVELLI


def leggi_sigla(sigla: str, livello: int) -> Posizione:
    """Converte «F7» + livello in Posizione."""
    testo = sigla.strip().upper()
    lettera, numero = testo[0], testo[1:]
    if lettera not in LETTERE or not numero.isdigit():
        raise ValueError(f"riferimento non valido: {sigla!r}")
    return Posizione(livello, LETTERE.index(lettera), int(numero) - 1)


# --------------------------------------------------------------------------- #
#  Pianeti
# --------------------------------------------------------------------------- #


@dataclass
class Pianeta:
    """Un sistema planetario. Di interessante ce n'e' un pianeta solo (nota sez. C).

    Il *contenuto* (tipo, forme di vita, razza) non esiste finche' una nave non lo
    incontra: viene tirato ai dadi e conservato qui man mano.
    """

    posizione: Posizione
    base: bool = False
    informazioni: dict[str, object] = field(default_factory=dict)
    livelli_noti: list[str] = field(default_factory=list)
    barrato: bool = False  # gia' visitato: non piu' visitabile (sez. F)
    avvistato_da: list[str] = field(default_factory=list)
    alieni_presenti: int | None = None

    @property
    def id(self) -> str:
        return self.posizione.riferimento

    @property
    def etichetta(self) -> str:
        """Come lo S.C. lo nomina: «B» per la base, altrimenti nome noto o sigla."""
        if self.base:
            return "B"
        nome = self.informazioni.get("tipo")
        codice = self.informazioni.get("codice")
        if nome and codice:
            return f"{nome} ({codice})"
        return self.posizione.sigla

    @property
    def completo(self) -> bool:
        return "razza" in self.informazioni or self.informazioni.get("terminale") is True

    def in_chiaro(self) -> dict:
        return {
            "id": self.id,
            "livello": self.posizione.livello,
            "x": self.posizione.x,
            "y": self.posizione.y,
            "sigla": self.posizione.sigla,
            "base": self.base,
            "barrato": self.barrato,
            "etichetta": self.etichetta,
            "informazioni": dict(self.informazioni),
            "livelli_noti": list(self.livelli_noti),
            "completo": self.completo,
            "alieni_presenti": self.alieni_presenti,
            "noto": bool(self.livelli_noti) or self.base,
            # Chi ha avvistato questo sistema: la conoscenza resta della flotta (tutti
            # vedono i sistemi noti), ma il Terminale di bordo evidenzia quelli che la
            # *propria* nave ha avvistato di persona. Sopravvive a `occulta_per_uc`.
            "avvistato_da": list(self.avvistato_da),
        }


# --------------------------------------------------------------------------- #
#  Anomalie (regolamento avanzato — spazio esterno)
# --------------------------------------------------------------------------- #


@dataclass
class Anomalia:
    """Un ostacolo statico dello spazio esterno: invisibile ai radar.

    Buco Nero e Distorsione Nullius occupano 1 cella, la Rete Magneto-Gravitazionale
    3 celle contigue. Piazzata solo a mano (editor del master): il generatore a seme
    non ne crea.
    """

    tipo: str  # "BN" | "RMG" | "DN"
    celle: list[Posizione]
    raggio_effetto: int | None = None  # solo B.N.: 4 parsec

    @property
    def id(self) -> str:
        return f"{self.tipo}-{self.celle[0].riferimento}"

    def in_chiaro(self) -> dict:
        return {
            "id": self.id,
            "tipo": self.tipo,
            "celle": [
                {"livello": c.livello, "x": c.x, "y": c.y, "sigla": c.sigla} for c in self.celle
            ],
            "raggio_effetto": self.raggio_effetto,
        }


# --------------------------------------------------------------------------- #
#  Galassia
# --------------------------------------------------------------------------- #


@dataclass
class Galassia:
    """La zona di galassia da esplorare: 4 livelli, 36 pianeti, 1 pianeta base."""

    seme: str
    lato: int = LATO_PREDEFINITO
    pianeti: list[Pianeta] = field(default_factory=list)
    anomalie: list[Anomalia] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._indice: dict[Posizione, Pianeta] = {p.posizione: p for p in self.pianeti}
        self._indice_anomalie: dict[Posizione, Anomalia] = {}
        for anomalia in self.anomalie:
            for cella in anomalia.celle:
                self._indice_anomalie[cella] = anomalia

    def reindicizza(self) -> None:
        self._indice = {p.posizione: p for p in self.pianeti}

    def aggiungi_anomalia(self, anomalia: Anomalia) -> None:
        self.anomalie.append(anomalia)
        for cella in anomalia.celle:
            self._indice_anomalie[cella] = anomalia

    def rimuovi_pianeta(self, posizione: Posizione) -> None:
        self.pianeti = [p for p in self.pianeti if p.posizione != posizione]
        self.reindicizza()

    def rimuovi_anomalia(self, id: str) -> None:
        rimossa = next((a for a in self.anomalie if a.id == id), None)
        if rimossa is None:
            return
        self.anomalie.remove(rimossa)
        self._indice_anomalie = {}
        for anomalia in self.anomalie:
            for cella in anomalia.celle:
                self._indice_anomalie[cella] = anomalia

    def anomalia_a(self, posizione: Posizione) -> Anomalia | None:
        return self._indice_anomalie.get(posizione)

    def a(self, posizione: Posizione) -> Pianeta | None:
        return self._indice.get(posizione)

    def per_id(self, identificativo: str) -> Pianeta | None:
        for pianeta in self.pianeti:
            if pianeta.id == identificativo:
                return pianeta
        return None

    @property
    def base(self) -> Pianeta:
        return next(p for p in self.pianeti if p.base)

    def del_livello(self, livello: int) -> list[Pianeta]:
        return [p for p in self.pianeti if p.posizione.livello == livello]

    def entro_raggio(self, centro: Posizione, raggio: int) -> list[tuple[Pianeta, int]]:
        """Pianeti visibili dal centro entro `raggio` parsec, sullo stesso livello.

        I livelli distano 4 parsec: con radar da 3 parsec al massimo, nessun
        avvistamento e' possibile fra livelli diversi.
        """
        trovati = []
        for pianeta in self.pianeti:
            posizione = pianeta.posizione
            if posizione.livello != centro.livello:
                continue
            distanza = distanza_piana(posizione, centro)
            if distanza <= raggio:
                trovati.append((pianeta, distanza))
        trovati.sort(key=lambda coppia: (coppia[1], coppia[0].posizione))
        return trovati

    def in_chiaro(self) -> dict:
        return {
            "seme": self.seme,
            "lato": self.lato,
            "lettere": list(LETTERE[: self.lato]),
            "livelli": LIVELLI,
            "nomi_livello": list(NOMI_LIVELLO),
            "parsec_fra_livelli": PARSEC_FRA_LIVELLI,
            "pianeti": [p.in_chiaro() for p in self.pianeti],
            "anomalie": [a.in_chiaro() for a in self.anomalie],
        }

    @classmethod
    def da_dict(cls, dati: dict) -> Galassia:
        """Ricostruisce una Galassia da un dict prodotto da `in_chiaro()` (import editor)."""
        pianeti = []
        for p in dati.get("pianeti", []):
            posizione = Posizione(p["livello"], p["x"], p["y"])
            pianeti.append(
                Pianeta(
                    posizione=posizione,
                    base=bool(p.get("base")),
                    informazioni=dict(p.get("informazioni") or {}),
                    livelli_noti=list(p.get("livelli_noti") or []),
                    barrato=bool(p.get("barrato")),
                    avvistato_da=list(p.get("avvistato_da") or []),
                    alieni_presenti=p.get("alieni_presenti"),
                )
            )
        galassia = cls(seme=dati["seme"], lato=int(dati["lato"]), pianeti=pianeti)
        galassia.reindicizza()
        for a in dati.get("anomalie", []):
            celle = [Posizione(c["livello"], c["x"], c["y"]) for c in a["celle"]]
            galassia.aggiungi_anomalia(
                Anomalia(tipo=a["tipo"], celle=celle, raggio_effetto=a.get("raggio_effetto"))
            )
        return galassia


def occulta_per_uc(galassia: dict) -> dict:
    """Filtra una galassia gia' serializzata per la vista dei Comandanti.

    Regola unica per la partita in corso (`Sessione.in_chiaro`) e per l'anteprima
    dell'editor: le due viste non devono poter divergere, altrimenti il master
    proverebbe la plancia sulla bozza e vedrebbe qualcosa di diverso da cio' che
    i giocatori vedranno davvero.
    """
    filtrata = dict(galassia)
    filtrata["pianeti"] = [
        p for p in galassia["pianeti"] if p["noto"] or p["base"] or p["barrato"]
    ]
    filtrata["seme"] = "— RISERVATO —"
    # Le anomalie non sono mai rilevabili dai radar: restano occulte agli U.C.
    filtrata["anomalie"] = []
    return filtrata
