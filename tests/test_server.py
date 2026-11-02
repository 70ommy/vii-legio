"""Controlli della cella del terminale che non appartengono al dominio."""

import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

from legio.modello import LIVELLI, Posizione
from legio.server import ALFABETO_CODICE, CODICE_CONSOLLE, Terminale, _cella_valida, indirizzo_lan
from legio.sessione import ErroreDiRegolamento, Sessione


class TestCellaValida(unittest.TestCase):
    def test_cella_dentro_la_tabula(self):
        self.assertEqual(_cella_valida(0, 3, 4, 12), Posizione(0, 3, 4))
        self.assertEqual(_cella_valida(LIVELLI - 1, 11, 11, 12), Posizione(LIVELLI - 1, 11, 11))

    def test_colonna_oltre_le_lettere_disponibili(self):
        """Fuori griglia non esiste una sigla: comporla sollevava un IndexError al
        posto dell'errore di regolamento, e il terminale rispondeva 500 invece di 400."""
        with self.assertRaises(ErroreDiRegolamento):
            _cella_valida(0, 40, 0, 12)

    def test_cella_appena_fuori_dal_lato(self):
        with self.assertRaises(ErroreDiRegolamento):
            _cella_valida(0, 12, 0, 12)
        with self.assertRaises(ErroreDiRegolamento):
            _cella_valida(0, 0, -1, 12)

    def test_livello_inesistente(self):
        with self.assertRaises(ErroreDiRegolamento):
            _cella_valida(LIVELLI, 0, 0, 12)


class TestIndirizzoLan(unittest.TestCase):
    def test_restituisce_un_indirizzo_ipv4(self):
        """Serve a stampare a schermo dove i telefoni devono collegarsi."""
        parti = indirizzo_lan().split(".")
        self.assertEqual(len(parti), 4)
        self.assertTrue(all(p.isdigit() and 0 <= int(p) <= 255 for p in parti))


class TestCodiceConsolle(unittest.TestCase):
    def test_leggibile_ad_alta_voce(self):
        """Il master lo detta: niente caratteri che si confondono pronunciandoli."""
        self.assertEqual(len(CODICE_CONSOLLE), 4)
        self.assertTrue(set(CODICE_CONSOLLE) <= set(ALFABETO_CODICE))
        for ambiguo in "IOQU":
            self.assertNotIn(ambiguo, ALFABETO_CODICE)


class TestInstradamentoPagine(unittest.TestCase):
    """La Consolle S.C. sta dietro un codice; le pagine dei giocatori alla radice."""

    @classmethod
    def setUpClass(cls):
        cls.servizio = ThreadingHTTPServer(("127.0.0.1", 0), Terminale)
        cls.porta = cls.servizio.server_address[1]
        cls.filo = threading.Thread(target=cls.servizio.serve_forever, daemon=True)
        cls.filo.start()

    @classmethod
    def tearDownClass(cls):
        cls.servizio.shutdown()
        cls.servizio.server_close()

    def prendi(self, percorso: str):
        url = f"http://127.0.0.1:{self.porta}{percorso}"
        try:
            with urllib.request.urlopen(url) as risposta:
                return risposta.status, risposta.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as errore:
            return errore.code, ""

    def test_la_radice_serve_la_pagina_dei_giocatori(self):
        stato, corpo = self.prendi("/")
        self.assertEqual(stato, 200)
        self.assertIn("Terminale di bordo", corpo)
        self.assertIn("Identificazione", corpo)  # e' la pagina d'ingresso, si sceglie la nave
        self.assertNotIn("Creazione della zona", corpo)  # non e' la consolle del master

    def test_il_terminale_di_bordo_risponde_su_uc(self):
        stato, corpo = self.prendi("/uc")
        self.assertEqual(stato, 200)
        self.assertIn("La mia nave", corpo)  # e' terminale.html, non l'ingresso

    def test_la_consolle_risponde_solo_col_codice_giusto(self):
        stato, corpo = self.prendi(f"/sc/{CODICE_CONSOLLE}")
        self.assertEqual(stato, 200)
        self.assertIn("Creazione della zona", corpo)

    def test_codice_sbagliato_e_un_404_come_un_altro(self):
        self.assertEqual(self.prendi("/sc/ZZZZ")[0], 404)
        self.assertEqual(self.prendi("/sc")[0], 404)

    def test_gli_asset_restano_pubblici_e_piatti(self):
        """Le pagine li chiamano con percorso assoluto: /sc/<codice> sta piu' in basso."""
        for asset in ("/style.css", "/app.js", "/ingresso.css", "/ingresso.js",
                      "/terminale.css", "/terminale.js"):
            with self.subTest(asset=asset):
                self.assertEqual(self.prendi(asset)[0], 200)

    def test_la_consolle_non_usa_percorsi_relativi(self):
        _, corpo = self.prendi(f"/sc/{CODICE_CONSOLLE}")
        self.assertIn('href="/style.css"', corpo)
        self.assertIn('src="/app.js"', corpo)

    def test_le_api_non_sono_toccate_dal_nuovo_instradamento(self):
        stato, corpo = self.prendi("/api/tabelle")
        self.assertEqual(stato, 200)
        self.assertIn("scheda", json.loads(corpo))


class TestApiNavi(unittest.TestCase):
    """L'elenco pubblico con cui il telefono sceglie la nave: nomi e colori, nient'altro."""

    @classmethod
    def setUpClass(cls):
        cls.servizio = ThreadingHTTPServer(("127.0.0.1", 0), Terminale)
        cls.porta = cls.servizio.server_address[1]
        cls.filo = threading.Thread(target=cls.servizio.serve_forever, daemon=True)
        cls.filo.start()

    @classmethod
    def tearDownClass(cls):
        cls.servizio.shutdown()
        cls.servizio.server_close()

    def setUp(self):
        import legio.server as srv

        self._srv = srv
        self._salvata = srv._sessione  # la ripristino: le API condividono un solo globale

    def tearDown(self):
        self._srv._sessione = self._salvata

    def prendi_json(self, percorso: str) -> dict:
        url = f"http://127.0.0.1:{self.porta}{percorso}"
        with urllib.request.urlopen(url) as risposta:
            return json.loads(risposta.read().decode("utf-8"))

    def test_senza_partita_la_lista_e_vuota(self):
        """Prima che il master avvii non deve nascere una sessione fantasma."""
        self._srv._sessione = None
        dati = self.prendi_json("/api/navi")
        self.assertFalse(dati["partita_attiva"])
        self.assertEqual(dati["navi"], [])

    def test_con_partita_elenca_nome_e_colore(self):
        self._srv._sessione = Sessione.nuova(ufficiali=["ALFA", "BETA"])
        dati = self.prendi_json("/api/navi")
        self.assertTrue(dati["partita_attiva"])
        self.assertEqual([n["nome"] for n in dati["navi"]], ["ALFA", "BETA"])
        self.assertTrue(all(n["colore"].startswith("#") for n in dati["navi"]))

    def test_non_trapela_nessun_dato_di_gioco(self):
        """Chi non ha ancora scelto la nave non deve poter leggere la galassia."""
        self._srv._sessione = Sessione.nuova(ufficiali=["ALFA"])
        dati = self.prendi_json("/api/navi")
        self.assertEqual(set(dati.keys()), {"partita_attiva", "navi"})
        self.assertEqual(set(dati["navi"][0].keys()), {"nome", "colore"})


class TestDichiarazioneHTTP(unittest.TestCase):
    """Rotte 3D: il Terminale deposita (risposta filtrata per U.C.), la consolle risolve."""

    @classmethod
    def setUpClass(cls):
        cls.servizio = ThreadingHTTPServer(("127.0.0.1", 0), Terminale)
        cls.porta = cls.servizio.server_address[1]
        cls.filo = threading.Thread(target=cls.servizio.serve_forever, daemon=True)
        cls.filo.start()

    @classmethod
    def tearDownClass(cls):
        cls.servizio.shutdown()
        cls.servizio.server_close()

    def posta(self, percorso: str, corpo: dict):
        dati = json.dumps(corpo).encode("utf-8")
        richiesta = urllib.request.Request(
            f"http://127.0.0.1:{self.porta}{percorso}",
            data=dati, headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(richiesta) as risposta:
            return risposta.status, json.loads(risposta.read().decode("utf-8"))

    def test_deposito_filtrato_per_uc_poi_annullo(self):
        self.posta("/api/nuova", {"ufficiali": ["ALFA", "BETA"]})
        stato, corpo = self.posta(
            "/api/dichiarazione",
            {"nave": "ALFA", "vista": "uc", "rotta": "2 E", "serbatoi": 1, "radar": 2, "computer": 2},
        )
        self.assertEqual(stato, 200)
        self.assertEqual(corpo["stato"]["vista"], "uc")  # la risposta a un telefono e' filtrata
        alfa = next(n for n in corpo["stato"]["navi"] if n["nome"] == "ALFA")
        self.assertEqual(alfa["dichiarazione_in_attesa"]["rotta"], "2 E")

        _, dopo = self.posta("/api/dichiarazione/annulla", {"nave": "ALFA", "vista": "uc"})
        alfa = next(n for n in dopo["stato"]["navi"] if n["nome"] == "ALFA")
        self.assertIsNone(alfa["dichiarazione_in_attesa"])


if __name__ == "__main__":
    unittest.main()
