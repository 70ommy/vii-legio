"""Terminale della C.S.C.: un piccolo server locale che serve la consolle dello S.C.

Solo libreria standard: nessuna dipendenza da installare, funziona senza rete.
"""

from __future__ import annotations

import json
import mimetypes
import secrets
import socket
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .dadi import Dadiera
from .editor import valida_galassia
from .modello import (
    LATO_PREDEFINITO,
    LIVELLI,
    Anomalia,
    Galassia,
    Pianeta,
    Posizione,
    occulta_per_uc,
)
from .rotte import RottaNonValida
from .schede import carica_guida, carica_scheda
from .sessione import ErroreDiRegolamento, Sessione

CARTELLA_WEB = Path(__file__).parent / "web"
ALFABETO_CODICE = "0123456789ABCDEFGHJKLMNPRSTVXZ"  # senza I/O/Q/U: si confondono ad alta voce
_lucchetto = threading.Lock()
_sessione: Sessione | None = None
_bozza: Galassia | None = None


def _nuovo_codice() -> str:
    """Codice d'accesso alla Consolle S.C., generato una volta per avvio del processo.

    Non e' sicurezza: chi e' in LAN puo' comunque chiamare le API a mano. E' un paletto
    contro l'incidente piu' probabile a un tavolo di amici — un giocatore che digita
    l'indirizzo nudo e si trova davanti l'intera galassia, in un gioco che e' tutto
    informazione nascosta.
    """
    return "".join(secrets.choice(ALFABETO_CODICE) for _ in range(4))


CODICE_CONSOLLE = _nuovo_codice()


def indirizzo_lan() -> str:
    """L'indirizzo con cui i telefoni in LAN raggiungono questa macchina.

    Il socket UDP non invia nulla: serve solo a farsi dire dal sistema operativo quale
    interfaccia userebbe per uscire, che e' quella giusta anche con piu' schede di rete.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sonda:
            sonda.connect(("192.0.2.1", 9))  # rete di documentazione: non esiste, non si contatta
            return sonda.getsockname()[0]
    except OSError:
        pass
    try:
        return socket.gethostbyname(socket.gethostname())
    except OSError:
        return "127.0.0.1"


def sessione_corrente() -> Sessione:
    global _sessione
    if _sessione is None:
        _sessione = Sessione.nuova()
    return _sessione


def nuova_sessione(**parametri) -> Sessione:
    global _sessione
    _sessione = Sessione.nuova(**parametri)
    return _sessione


def _elenco_navi() -> dict:
    """Elenco pubblico con cui un telefono riconosce la propria nave nella pagina d'ingresso.

    Volutamente scarno: solo nome e colore, nessun dato di gioco (posizioni, punti,
    galassia). Serve a farsi scegliere prima ancora di sapere chi sei, quindi non puo'
    presupporre un'identita' ne' filtrare per vista.

    Non crea una sessione se non c'e' (a differenza di `sessione_corrente`): finche' il
    master non avvia la partita la lista e' vuota, e il telefono mostra "in attesa".
    """
    if _sessione is None:
        return {"partita_attiva": False, "navi": []}
    return {
        "partita_attiva": True,
        "navi": [{"nome": nave.nome, "colore": nave.colore} for nave in _sessione.navi.values()],
    }


def _bozza_corrente() -> Galassia:
    if _bozza is None:
        raise ErroreDiRegolamento("nessuna bozza di galassia in costruzione: avviarne una nuova")
    return _bozza


def _cella_valida(livello: int, x: int, y: int, lato: int) -> Posizione:
    """Posizione dentro la TABULA, o un errore leggibile.

    Il messaggio non puo' usare `sigla`: fuori griglia non esiste una lettera di
    colonna, e comporla solleverebbe un IndexError al posto dell'errore di regolamento.
    """
    posizione = Posizione(livello, x, y)
    if not posizione.dentro(lato):
        raise ErroreDiRegolamento(
            f"cella fuori dalla TABULA {lato}×{lato}:"
            f" livello {livello + 1}, colonna {x + 1}, riga {y + 1}"
        )
    return posizione


def _stato_editor(vista: str = "sc") -> dict:
    """La validazione guarda sempre la bozza intera: al master servono gli errori
    anche mentre sta sbirciando l'anteprima della plancia dei Comandanti."""
    if _bozza is None:
        return {"bozza": None, "validazione": None, "vista": vista}
    bozza = _bozza.in_chiaro()
    if vista == "uc":
        bozza = occulta_per_uc(bozza)
    return {"bozza": bozza, "validazione": valida_galassia(_bozza), "vista": vista}


class Terminale(BaseHTTPRequestHandler):
    server_version = "SpazioComputer/1.0"

    # -- utilita' ------------------------------------------------------- #

    def _json(self, dati: dict, stato: int = 200) -> None:
        corpo = json.dumps(dati, ensure_ascii=False).encode("utf-8")
        self.send_response(stato)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(corpo)

    def _corpo(self) -> dict:
        lunghezza = int(self.headers.get("Content-Length") or 0)
        if not lunghezza:
            return {}
        try:
            return json.loads(self.rfile.read(lunghezza).decode("utf-8"))
        except json.JSONDecodeError as errore:
            raise ErroreDiRegolamento(f"richiesta illeggibile: {errore}") from errore

    def _pagina(self, percorso: str) -> None:
        """Instrada le pagine HTML; gli asset (css/js) restano pubblici e piatti.

        Tre porte:
          /              ingresso — dal telefono scegli la tua nave (pagina pubblica);
          /uc            terminale di bordo — la plancia personale di quell'Ufficiale;
          /sc/<codice>   Consolle dello S.C. — dietro un codice perche' mostra tutta la
                         galassia, che in questo gioco e' quasi tutta informazione nascosta.
        """
        if percorso == "/" or percorso == "":
            self._statico("ingresso.html")
            return
        if percorso.rstrip("/") == "/uc":
            self._statico("terminale.html")
            return
        if percorso.rstrip("/") == f"/sc/{CODICE_CONSOLLE}":
            self._statico("index.html")
            return
        if percorso == "/sc" or percorso.startswith("/sc/"):
            # Codice sbagliato: un 404 secco, identico a quello di un file inesistente.
            self.send_error(404, "file non presente nella cella dello S.C.")
            return
        self._statico(percorso)

    def _statico(self, percorso: str) -> None:
        nome = percorso.lstrip("/") or "index.html"
        file = (CARTELLA_WEB / nome).resolve()
        if not file.is_file() or CARTELLA_WEB.resolve() not in file.parents:
            self.send_error(404, "file non presente nella cella dello S.C.")
            return
        tipo = mimetypes.guess_type(file.name)[0] or "application/octet-stream"
        dati = file.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", f"{tipo}; charset=utf-8" if tipo.startswith("text/") else tipo)
        self.send_header("Content-Length", str(len(dati)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(dati)

    def log_message(self, formato: str, *argomenti) -> None:  # silenzio in cella
        pass

    # -- rotte HTTP ----------------------------------------------------- #

    def do_GET(self) -> None:  # noqa: N802
        percorso, _, query = self.path.partition("?")
        if percorso.startswith("/api/"):
            try:
                self._json(self._api_get(percorso, _leggi_query(query)))
            except (ErroreDiRegolamento, RottaNonValida, ValueError) as errore:
                self._json({"errore": str(errore)}, 400)
            return
        self._pagina(percorso)

    def do_POST(self) -> None:  # noqa: N802
        percorso, _, _query = self.path.partition("?")
        try:
            corpo = self._corpo()
            with _lucchetto:
                self._json(self._api_post(percorso, corpo))
        except (ErroreDiRegolamento, RottaNonValida, ValueError) as errore:
            self._json({"errore": str(errore)}, 400)
        except Exception as errore:  # imprevisto: lo S.C. deve saperlo
            self._json({"errore": f"guasto del pianeta-logico: {errore!r}"}, 500)

    # -- API ------------------------------------------------------------ #

    def _api_get(self, percorso: str, query: dict) -> dict:
        if percorso == "/api/stato":
            return sessione_corrente().in_chiaro(vista=query.get("vista", "sc"))
        if percorso == "/api/navi":
            return _elenco_navi()
        if percorso == "/api/tabelle":
            return {"scheda": carica_scheda(), "guida": carica_guida()}
        if percorso == "/api/esporta":
            sessione = sessione_corrente()
            return {
                "stato": sessione.in_chiaro("sc"),
                "tiri": [
                    {"dado": t.dado, "esito": t.esito, "motivo": t.motivo}
                    for t in sessione.dadiera.registro
                ],
            }
        if percorso == "/api/editor/stato":
            return _stato_editor(query.get("vista", "sc"))
        if percorso == "/api/editor/esporta":
            return _bozza_corrente().in_chiaro()
        raise ErroreDiRegolamento(f"funzione non prevista: {percorso}")

    def _api_post(self, percorso: str, corpo: dict) -> dict:
        if percorso == "/api/nuova":
            sessione = nuova_sessione(
                seme=(corpo.get("seme") or "").strip() or None,
                lato=int(corpo.get("lato") or LATO_PREDEFINITO),
                distribuzione=corpo.get("distribuzione") or "bilanciata",
                ufficiali=corpo.get("ufficiali") or None,
                spazio_esterno=bool(corpo.get("spazio_esterno")),
                dettagli_navi=corpo.get("dettagli_navi") or None,
            )
            return sessione.in_chiaro("sc")

        if percorso.startswith("/api/editor/"):
            return self._api_post_editor(percorso, corpo)

        sessione = sessione_corrente()
        if percorso == "/api/rotta":
            esito = sessione.dichiara_rotta(
                nome=corpo.get("nave", ""),
                rotta=corpo.get("rotta", ""),
                serbatoi=int(corpo.get("serbatoi") or 1),
                radar=int(corpo.get("radar") or 0),
                computer=int(corpo["computer"]) if corpo.get("computer") is not None else None,
                atterraggio=bool(corpo.get("atterraggio")),
            )
            return {"esito": esito, "stato": sessione.in_chiaro("sc")}
        if percorso == "/api/dichiarazione":
            # Deposito dal Terminale di bordo: la vista di risposta e' 'uc' (la chiama un telefono).
            vista = corpo.get("vista") or "sc"
            esito = sessione.deposita_dichiarazione(
                nome=corpo.get("nave", ""),
                rotta=corpo.get("rotta", ""),
                serbatoi=int(corpo.get("serbatoi") or 1),
                radar=int(corpo.get("radar") or 0),
                computer=int(corpo["computer"]) if corpo.get("computer") is not None else None,
                atterraggio=bool(corpo.get("atterraggio")),
            )
            return {"esito": esito, "stato": sessione.in_chiaro(vista)}
        if percorso == "/api/dichiarazione/annulla":
            vista = corpo.get("vista") or "sc"
            esito = sessione.annulla_dichiarazione(corpo.get("nave", ""))
            return {"esito": esito, "stato": sessione.in_chiaro(vista)}
        if percorso == "/api/dichiarazione/risolvi":
            # Solo la consolle dello S.C.: esegue davvero, risponde con la vista completa.
            esito = sessione.risolvi_dichiarazione(corpo.get("nave", ""))
            return {"esito": esito, "stato": sessione.in_chiaro("sc")}
        if percorso == "/api/informazione":
            esito = sessione.richiedi_informazione(corpo.get("nave", ""), corpo.get("pianeta", ""))
            return {"esito": esito, "stato": sessione.in_chiaro("sc")}
        if percorso == "/api/atterraggio":
            esito = sessione.atterra(corpo.get("nave", ""), corpo.get("pianeta") or None)
            return {"esito": esito, "stato": sessione.in_chiaro("sc")}
        if percorso == "/api/riatterraggio":
            esito = sessione.riatterra(corpo.get("nave", ""))
            return {"esito": esito, "stato": sessione.in_chiaro("sc")}
        if percorso == "/api/turno":
            sessione.chiudi_turno()
            return {"stato": sessione.in_chiaro("sc")}
        raise ErroreDiRegolamento(f"funzione non prevista: {percorso}")

    def _api_post_editor(self, percorso: str, corpo: dict) -> dict:
        global _bozza

        if percorso == "/api/editor/nuova":
            # Matricola a sorte come per le zone generate a seme: e' anche il seme dei
            # dadi della partita che nascera' dalla bozza (vedi Sessione.nuova_da_galassia).
            _bozza = Galassia(
                seme=Dadiera.seme_casuale(), lato=int(corpo.get("lato") or LATO_PREDEFINITO)
            )
            return _stato_editor()

        if percorso == "/api/editor/pianeta":
            bozza = _bozza_corrente()
            posizione = _cella_valida(
                int(corpo["livello"]), int(corpo["x"]), int(corpo["y"]), bozza.lato
            )
            base = bool(corpo.get("base"))
            if base:
                for altro in bozza.pianeti:
                    altro.base = False
            esistente = bozza.a(posizione)
            informazioni = {}
            if corpo.get("tipo"):
                informazioni["tipo"] = corpo["tipo"]
            if corpo.get("codice"):
                informazioni["codice"] = corpo["codice"]
            if esistente is not None:
                esistente.base = base
                esistente.informazioni.update(informazioni)
            else:
                bozza.pianeti.append(Pianeta(posizione=posizione, base=base, informazioni=informazioni))
            bozza.reindicizza()
            return _stato_editor()

        if percorso == "/api/editor/anomalia":
            bozza = _bozza_corrente()
            tipo = corpo.get("tipo")
            if tipo == "BN":
                x, y = int(corpo["x"]), int(corpo["y"])
                celle = [_cella_valida(livello, x, y, bozza.lato) for livello in range(LIVELLI)]
                bozza.aggiungi_anomalia(Anomalia(tipo="BN", celle=celle, raggio_effetto=4))
            elif tipo == "DN":
                cella = _cella_valida(
                    int(corpo["livello"]), int(corpo["x"]), int(corpo["y"]), bozza.lato
                )
                bozza.aggiungi_anomalia(Anomalia(tipo="DN", celle=[cella]))
            elif tipo == "RMG":
                grezze = corpo.get("celle") or []
                if len(grezze) != 3:
                    raise ErroreDiRegolamento("una R.M.G. richiede esattamente 3 celle")
                celle = [
                    _cella_valida(int(c["livello"]), int(c["x"]), int(c["y"]), bozza.lato)
                    for c in grezze
                ]
                if len({c.livello for c in celle}) != 1:
                    raise ErroreDiRegolamento("le 3 celle di una R.M.G. devono stare sullo stesso livello")
                bozza.aggiungi_anomalia(Anomalia(tipo="RMG", celle=celle))
            else:
                raise ErroreDiRegolamento(f"tipo di anomalia non previsto: {tipo!r}")
            return _stato_editor()

        if percorso == "/api/editor/elimina":
            bozza = _bozza_corrente()
            genere = corpo.get("genere")
            if genere == "pianeta":
                bozza.rimuovi_pianeta(Posizione(int(corpo["livello"]), int(corpo["x"]), int(corpo["y"])))
            elif genere == "anomalia":
                bozza.rimuovi_anomalia(corpo.get("id", ""))
            else:
                raise ErroreDiRegolamento(f"genere da eliminare non previsto: {genere!r}")
            return _stato_editor()

        if percorso == "/api/editor/importa":
            _bozza = Galassia.da_dict(corpo)
            return _stato_editor()

        if percorso == "/api/editor/avvia":
            bozza = _bozza_corrente()
            validazione = valida_galassia(bozza)
            if validazione["errori"]:
                messaggi = "; ".join(e["messaggio"] for e in validazione["errori"])
                raise ErroreDiRegolamento(f"la bozza ha errori bloccanti: {messaggi}")
            sessione = Sessione.nuova_da_galassia(
                bozza,
                seme=(corpo.get("seme") or "").strip() or None,
                ufficiali=corpo.get("ufficiali") or None,
                spazio_esterno=bool(corpo.get("spazio_esterno")),
                dettagli_navi=corpo.get("dettagli_navi") or None,
            )
            global _sessione
            _sessione = sessione
            _bozza = None
            return sessione.in_chiaro("sc")

        raise ErroreDiRegolamento(f"funzione non prevista: {percorso}")


def _leggi_query(query: str) -> dict:
    from urllib.parse import parse_qs

    return {chiave: valori[0] for chiave, valori in parse_qs(query).items()}


def avvia(porta: int = 7734, apri_browser: bool = True, solo_locale: bool = False) -> None:
    """Apre la cella dello S.C. In ascolto su tutta la LAN, se non si chiede il contrario.

    Serve perche' i giocatori si collegano dai propri telefoni: un server legato a
    127.0.0.1 sarebbe raggiungibile solo dalla macchina del master.
    """
    interfaccia = "127.0.0.1" if solo_locale else "0.0.0.0"
    ospite = "127.0.0.1" if solo_locale else indirizzo_lan()
    consolle = f"http://{ospite}:{porta}/sc/{CODICE_CONSOLLE}"
    giocatori = f"http://{ospite}:{porta}/"

    with ThreadingHTTPServer((interfaccia, porta), Terminale) as servizio:
        larghezza = 58
        print("╔" + "═" * larghezza + "╗")
        for riga in ("C.S.C. — CORPORAZIONE SPAZIO COMPUTER",
                     "Terminale di cella attivo. Classifica: Basico Segreto."):
            print("║  " + riga.ljust(larghezza - 2) + "║")
        print("╚" + "═" * larghezza + "╝")
        print(f"  Consolle S.C. (tienila per te):  {consolle}")
        print(f"  Terminali di bordo (U.C.):       {giocatori}")
        if not solo_locale:
            print()
            print("  Gli Ufficiali digitano il secondo indirizzo sul proprio telefono,")
            print("  collegati alla stessa rete. Al primo avvio Windows chiedera' se")
            print("  autorizzare Python sulle reti private: bisogna dire di si'.")
            print("  Con --solo-locale la cella resta chiusa su questa macchina.")
        print("\n  Ctrl+C per chiudere la cella.\n")
        if apri_browser:
            threading.Timer(0.4, webbrowser.open, args=(f"http://127.0.0.1:{porta}/sc/{CODICE_CONSOLLE}",)).start()
        try:
            servizio.serve_forever()
        except KeyboardInterrupt:
            print("\n  Terminale disattivato. Le rotte restano tracciate a matita.")
