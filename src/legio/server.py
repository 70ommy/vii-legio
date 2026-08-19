"""Terminale della C.S.C.: un piccolo server locale che serve la consolle dello S.C.

Solo libreria standard: nessuna dipendenza da installare, funziona senza rete.
"""

from __future__ import annotations

import json
import mimetypes
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .modello import LATO_PREDEFINITO
from .rotte import RottaNonValida
from .schede import carica_guida, carica_scheda
from .sessione import ErroreDiRegolamento, Sessione

CARTELLA_WEB = Path(__file__).parent / "web"
_lucchetto = threading.Lock()
_sessione: Sessione | None = None


def sessione_corrente() -> Sessione:
    global _sessione
    if _sessione is None:
        _sessione = Sessione.nuova()
    return _sessione


def nuova_sessione(**parametri) -> Sessione:
    global _sessione
    _sessione = Sessione.nuova(**parametri)
    return _sessione


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
        self._statico(percorso)

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
        raise ErroreDiRegolamento(f"funzione non prevista: {percorso}")

    def _api_post(self, percorso: str, corpo: dict) -> dict:
        if percorso == "/api/nuova":
            sessione = nuova_sessione(
                seme=(corpo.get("seme") or "").strip() or None,
                lato=int(corpo.get("lato") or LATO_PREDEFINITO),
                distribuzione=corpo.get("distribuzione") or "bilanciata",
                ufficiali=corpo.get("ufficiali") or None,
                spazio_esterno=bool(corpo.get("spazio_esterno")),
            )
            return sessione.in_chiaro("sc")

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
        if percorso == "/api/informazione":
            esito = sessione.richiedi_informazione(corpo.get("nave", ""), corpo.get("pianeta", ""))
            return {"esito": esito, "stato": sessione.in_chiaro("sc")}
        if percorso == "/api/atterraggio":
            esito = sessione.atterra(corpo.get("nave", ""), corpo.get("pianeta") or None)
            return {"esito": esito, "stato": sessione.in_chiaro("sc")}
        if percorso == "/api/turno":
            sessione.chiudi_turno()
            return {"stato": sessione.in_chiaro("sc")}
        raise ErroreDiRegolamento(f"funzione non prevista: {percorso}")


def _leggi_query(query: str) -> dict:
    from urllib.parse import parse_qs

    return {chiave: valori[0] for chiave, valori in parse_qs(query).items()}


def avvia(porta: int = 7734, apri_browser: bool = True) -> None:
    indirizzo = f"http://127.0.0.1:{porta}/"
    with ThreadingHTTPServer(("127.0.0.1", porta), Terminale) as servizio:
        larghezza = 58
        print("╔" + "═" * larghezza + "╗")
        for riga in ("C.S.C. — CORPORAZIONE SPAZIO COMPUTER",
                     "Terminale di cella attivo. Classifica: Basico Segreto."):
            print("║  " + riga.ljust(larghezza - 2) + "║")
        print("╚" + "═" * larghezza + "╝")
        print(f"  Consolle S.C.:  {indirizzo}")
        print("  Ctrl+C per chiudere la cella.\n")
        if apri_browser:
            threading.Timer(0.4, webbrowser.open, args=(indirizzo,)).start()
        try:
            servizio.serve_forever()
        except KeyboardInterrupt:
            print("\n  Terminale disattivato. Le rotte restano tracciate a matita.")
