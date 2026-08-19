"""Sez. F/G — Schede Informazioni e Guida Incontri."""

import unittest

from legio.dadi import Dadiera
from legio.modello import Pianeta, Posizione
from legio.schede import (
    carica_guida,
    carica_scheda,
    completa_informazioni,
    prossimo_livello,
    risolvi_attivita,
    risolvi_livello,
    tira_arrivi,
    tira_presenze,
    voce_gi,
)


def pianeta_vuoto() -> Pianeta:
    return Pianeta(posizione=Posizione(0, 3, 4))


class TestSequenzaInformazioni(unittest.TestCase):
    def test_ordine_dei_livelli(self):
        """Si sale un gradino alla volta: I, poi II, poi III, poi IV."""
        pianeta = pianeta_vuoto()
        dadiera = Dadiera("ORDINE")
        attesi = ["I", "II", "III", "IV"]
        for atteso in attesi:
            livello = prossimo_livello(pianeta)
            if livello is None:  # pianeta deserto: la scala si ferma prima
                self.assertTrue(pianeta.informazioni.get("terminale"))
                return
            self.assertEqual(livello, atteso)
            while livello in attesi and livello not in pianeta.livelli_noti:
                risolvi_livello(pianeta, livello, dadiera)  # il D.N.S. fa ripetere

    def test_la_sotto_informazione_di_radioattivita_solo_nello_spazio_esterno(self):
        pianeta = pianeta_vuoto()
        risolvi_livello(pianeta, "I", Dadiera("RADIO"))
        if pianeta.livelli_noti:  # se non e' uscito un D.N.S.
            self.assertEqual(prossimo_livello(pianeta, spazio_esterno=False), "II")
            self.assertEqual(prossimo_livello(pianeta, spazio_esterno=True), "I-bis")

    def test_non_si_puo_saltare_un_livello(self):
        pianeta = pianeta_vuoto()
        with self.assertRaises(ValueError):
            risolvi_livello(pianeta, "IV", Dadiera("SALTO"))

    def test_livello_gia_noto_respinto(self):
        pianeta = pianeta_vuoto()
        dadiera = Dadiera("RIPETUTO")
        risolvi_livello(pianeta, "I", dadiera)
        with self.assertRaises(ValueError):
            risolvi_livello(pianeta, "I", dadiera)

    def test_dns_non_aggiunge_notizie(self):
        """Il D.N.S. spreca la richiesta: nessuna caratteristica viene registrata."""
        for numero in range(400):
            prova = pianeta_vuoto()
            resoconto = risolvi_livello(prova, "I", Dadiera(f"S{numero}"))
            if resoconto["dns"]:
                self.assertEqual(prova.informazioni, {})
                self.assertEqual(prova.livelli_noti, [])
                return
        self.fail("nessun D.N.S. estratto in 400 tentativi")

    def test_pianeta_deserto_e_terminale(self):
        pianeta = pianeta_vuoto()
        pianeta.informazioni.update({"tipo": "TERRA", "codice": "A", "vita": "NESSUNA"})
        pianeta.livelli_noti.extend(["I", "II"])
        resoconto = risolvi_livello(pianeta, "III", Dadiera("DESERTO"))
        self.assertIsNone(resoconto["dado"])
        self.assertTrue(pianeta.informazioni["terminale"])
        self.assertIsNone(prossimo_livello(pianeta))

    def test_completamento_allo_sbarco_arriva_in_fondo(self):
        pianeta = pianeta_vuoto()
        completa_informazioni(pianeta, Dadiera("SBARCO"))
        self.assertIsNone(prossimo_livello(pianeta))
        self.assertTrue(pianeta.completo)

    def test_ogni_ramo_del_quarto_livello_ha_una_voce_gi(self):
        """Ogni razza raggiungibile deve esistere sulla Guida Incontri."""
        scheda = carica_scheda()
        voci = carica_guida()["voci"]
        for tabella in scheda["livelli"]["IV"]["tabelle"]:
            for esito in tabella["esiti"]:
                if esito.get("dns"):
                    continue
                self.assertIn(str(esito["dati"]["rif_gi"]), voci, esito["dati"]["razza"])

    def test_tutti_i_rami_di_vita_e_sapienza_sono_coperti(self):
        scheda = carica_scheda()
        coppie = [
            ("ANIMALI", "SAPIENS"), ("ANIMALI", "NON SAPIENS"),
            ("VEGETALI", "SAPIENS"), ("VEGETALI", "NON SAPIENS"),
            ("MINERALI", "SAPIENS"), ("MINERALI", "NON SAPIENS"),
            ("MINERALI", "MINERALI DI OZ"),
        ]
        for vita, sapienza in coppie:
            pianeta = pianeta_vuoto()
            pianeta.informazioni.update({"vita": vita, "sapienza": sapienza})
            pianeta.livelli_noti.extend(["I", "II", "III"])
            with self.subTest(vita=vita, sapienza=sapienza):
                resoconto = risolvi_livello(pianeta, "IV", Dadiera(f"{vita}{sapienza}"))
                self.assertTrue(resoconto["dns"] or resoconto["dati"].get("rif_gi"))

    def test_esempio_del_manuale_vegetali_non_sapiens(self):
        """«d6 → 1-2-3: VELENOSI; d6 → 4-5-6: MOSTRI.»"""
        scheda = carica_scheda()
        tabella = next(
            t for t in scheda["livelli"]["IV"]["tabelle"]
            if t.get("quando", {}).get("vita") == ["VEGETALI"]
            and t.get("quando", {}).get("sapienza") == ["NON SAPIENS"]
        )
        self.assertEqual(tabella["dado"], "d6")
        self.assertEqual(
            [(e["faccia"], e["dati"]["razza"]) for e in tabella["esiti"]],
            [("1-3", "VELENOSI"), ("4-6", "MOSTRI")],
        )


class TestGuidaIncontri(unittest.TestCase):
    def test_ogni_voce_ha_le_tabelle_di_servizio(self):
        for riferimento, voce in carica_guida()["voci"].items():
            with self.subTest(rif=riferimento):
                scheda = voce["scheda"]
                self.assertIn("presenze", scheda)
                self.assertIn("arrivi", scheda)
                self.assertTrue(voce["descrizione"].strip())
                for attivita in scheda.get("attivita", []):
                    self.assertIn(attivita["controllo"], {"U.C.", "S.C."})

    def test_tabelle_presenze_e_arrivi_coprono_tutte_le_facce(self):
        dadiera = Dadiera("TABELLE")
        for riferimento in carica_guida()["voci"]:
            voce = voce_gi(riferimento)
            with self.subTest(rif=riferimento):
                for _ in range(24):  # ogni faccia di d6 esce piu' volte
                    self.assertGreaterEqual(tira_presenze(voce, dadiera)[0], 0)
                    self.assertGreaterEqual(tira_arrivi(voce, dadiera)[0], 0)

    def test_attivita_coprono_tutte_le_facce(self):
        dadiera = Dadiera("ATTIVITA")
        for riferimento in carica_guida()["voci"]:
            voce = voce_gi(riferimento)
            with self.subTest(rif=riferimento):
                for _ in range(40):
                    for esito in risolvi_attivita(voce, dadiera):
                        self.assertTrue(esito["testo"])
                        self.assertIn(esito["controllo"], {"U.C.", "S.C."})


if __name__ == "__main__":
    unittest.main()
