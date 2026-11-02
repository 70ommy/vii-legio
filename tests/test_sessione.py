"""La partita vista dalla cella dello S.C."""

import unittest

from legio.dadi import Dadiera
from legio.modello import Anomalia, Galassia, Pianeta, Posizione
from legio.rotte import RottaNonValida
from legio.sessione import ErroreDiRegolamento, Nave, Sessione


def sessione_di_prova() -> Sessione:
    """Base in A1, un sistema in A5, uno in D3 — tutti sul primo livello."""
    pianeti = [
        Pianeta(posizione=Posizione(0, 0, 0), base=True),
        Pianeta(posizione=Posizione(0, 0, 4)),
        Pianeta(posizione=Posizione(0, 3, 2)),
    ]
    galassia = Galassia(seme="PROVA", lato=12, pianeti=pianeti)
    galassia.reindicizza()
    sessione = Sessione(galassia=galassia, dadiera=Dadiera("PROVA"))
    base = galassia.base.posizione
    sessione.navi["ALFA"] = Nave(
        nome="ALFA", colore="#ff5c39", posizione=base, partenza_movimento=base,
        a_terra=galassia.base.id, computer=2, informazioni_residue=2,
    )
    sessione.ordine_turno = ["ALFA"]
    return sessione


class TestAvvio(unittest.TestCase):
    def test_le_navi_partono_dal_pianeta_base(self):
        sessione = Sessione.nuova(seme="AVVIO", ufficiali=["UNO", "DUE"])
        base = sessione.galassia.base.posizione
        for nave in sessione.navi.values():
            self.assertEqual(nave.posizione, base)
            self.assertEqual(nave.partenza_movimento, base)

    def test_due_segnalini_per_ufficiale_e_ordine_a_sorte(self):
        sessione = Sessione.nuova(seme="ORDINE", ufficiali=["UNO", "DUE", "TRE"])
        self.assertEqual(sorted(sessione.ordine_turno), ["DUE", "TRE", "UNO"])
        self.assertEqual(len(sessione.navi), 3)

    def test_ufficiale_inesistente(self):
        sessione = sessione_di_prova()
        with self.assertRaises(ErroreDiRegolamento):
            sessione.nave("OMEGA")


class TestMovimentoEInformazioni(unittest.TestCase):
    def setUp(self):
        self.sessione = sessione_di_prova()

    def test_rotta_sposta_il_segnalino_e_annota_il_registro(self):
        prima = len(self.sessione.registro)
        self.sessione.dichiara_rotta("ALFA", "2 E", serbatoi=1, radar=2, computer=2)
        nave = self.sessione.nave("ALFA")
        self.assertEqual(nave.posizione, Posizione(0, 2, 0))
        self.assertEqual(nave.partenza_movimento, Posizione(0, 0, 0))
        self.assertGreater(len(self.sessione.registro), prima)

    def test_informazione_solo_entro_il_raggio_dei_radar(self):
        self.sessione.dichiara_rotta("ALFA", "2 E", serbatoi=1, radar=2, computer=2)
        with self.assertRaises(ErroreDiRegolamento):
            self.sessione.richiedi_informazione("ALFA", "L1·A5")  # a 4 parsec: fuori gittata
        resoconto = self.sessione.richiedi_informazione("ALFA", "L1·D3")
        self.assertEqual(resoconto["livello"], "I")

    def test_le_informazioni_sono_limitate_dai_computer_di_bordo(self):
        self.sessione.dichiara_rotta("ALFA", "2 E", serbatoi=1, radar=2, computer=1)
        self.sessione.richiedi_informazione("ALFA", "L1·D3")
        with self.assertRaises(ErroreDiRegolamento):
            self.sessione.richiedi_informazione("ALFA", "L1·D3")

    def test_il_turno_nuovo_ripristina_le_informazioni(self):
        self.sessione.dichiara_rotta("ALFA", "2 E", serbatoi=1, radar=2, computer=2)
        self.sessione.richiedi_informazione("ALFA", "L1·D3")
        self.sessione.chiudi_turno()
        self.assertEqual(self.sessione.nave("ALFA").informazioni_residue, 2)

    def test_informazioni_note_ripetute_gratuitamente(self):
        self.sessione.dichiara_rotta("ALFA", "2 E", serbatoi=1, radar=2, computer=2)
        self.sessione.richiedi_informazione("ALFA", "L1·D3")
        esito = self.sessione.dichiara_rotta("ALFA", "1 O", serbatoi=1, radar=2, computer=2)
        pianeti_ripetuti = [r["pianeta"] for r in esito.get("ripetizioni", [])]
        self.assertIn("L1·D3", pianeti_ripetuti)


class TestAtterraggio(unittest.TestCase):
    def setUp(self):
        self.sessione = sessione_di_prova()

    def test_atterraggio_completa_le_informazioni_e_assegna_punti(self):
        esito = self.sessione.dichiara_rotta(
            "ALFA", "4 S", serbatoi=1, radar=3, computer=2, atterraggio=True
        )
        self.assertIsNotNone(esito["atterraggio"])
        pianeta = self.sessione.galassia.per_id("L1·A5")
        self.assertTrue(pianeta.completo)
        self.assertEqual(self.sessione.nave("ALFA").a_terra, "L1·A5")

    def test_senza_radar_l_atterraggio_e_obbligatorio(self):
        esito = self.sessione.dichiara_rotta("ALFA", "8 S", serbatoi=2, radar=0, computer=1)
        self.assertTrue(esito["movimento"]["atterraggio_obbligato"])
        self.assertEqual(esito["movimento"]["atterraggio_su"], "L1·A5")

    def test_ripartendo_da_un_pianeta_lo_si_barra(self):
        self.sessione.dichiara_rotta("ALFA", "4 S", serbatoi=1, radar=3, computer=2, atterraggio=True)
        self.sessione.dichiara_rotta("ALFA", "2 N", serbatoi=1, radar=3, computer=2)
        self.assertTrue(self.sessione.galassia.per_id("L1·A5").barrato)

    def test_il_pianeta_base_non_viene_barrato(self):
        self.sessione.dichiara_rotta("ALFA", "2 E", serbatoi=1, radar=2, computer=2)
        self.assertFalse(self.sessione.galassia.base.barrato)

    def test_atterraggio_senza_sistema_sotto_la_nave(self):
        self.sessione.dichiara_rotta("ALFA", "2 E", serbatoi=1, radar=2, computer=2)
        with self.assertRaises(ErroreDiRegolamento):
            self.sessione.atterra("ALFA")


class TestSpazioEsterno(unittest.TestCase):
    def test_dettagli_navi_propagati_alla_creazione(self):
        sessione = Sessione.nuova(
            seme="DETTAGLI", ufficiali=["UNO", "DUE"],
            dettagli_navi={"UNO": {"classe_massa": 3, "princeps_psi": True}},
        )
        self.assertEqual(sessione.nave("UNO").classe_massa, 3)
        self.assertTrue(sessione.nave("UNO").princeps_psi)
        self.assertEqual(sessione.nave("DUE").classe_massa, 2)
        self.assertFalse(sessione.nave("DUE").princeps_psi)

    def test_rischio_buco_nero_annota_il_registro(self):
        sessione = sessione_di_prova()
        sessione.spazio_esterno = True
        sessione.galassia.aggiungi_anomalia(
            Anomalia(tipo="BN", celle=[Posizione(0, 2, 0)], raggio_effetto=4)
        )
        prima = len(sessione.registro)
        sessione.dichiara_rotta("ALFA", "2 E", serbatoi=1, radar=2, computer=2)
        self.assertGreater(len(sessione.registro), prima)
        self.assertTrue(any("campo gravitazionale" in v["testo"] for v in sessione.registro))

    def test_atterraggio_in_spazio_esterno_produce_tab_o_e_p(self):
        sessione = sessione_di_prova()
        sessione.spazio_esterno = True
        esito = sessione.dichiara_rotta(
            "ALFA", "4 S", serbatoi=1, radar=3, computer=2, atterraggio=True
        )
        self.assertIn("rischio_massa", esito["atterraggio"])
        self.assertIn("zona_atterraggio", esito["atterraggio"])

    def test_riatterraggio_una_sola_volta_e_non_barra_il_pianeta(self):
        sessione = sessione_di_prova()
        sessione.spazio_esterno = True
        sessione.dichiara_rotta("ALFA", "4 S", serbatoi=1, radar=3, computer=2, atterraggio=True)
        sessione.riatterra("ALFA")
        with self.assertRaises(ErroreDiRegolamento):
            sessione.riatterra("ALFA")
        self.assertFalse(sessione.galassia.per_id("L1·A5").barrato)

    def test_riatterraggio_richiede_spazio_esterno(self):
        sessione = sessione_di_prova()
        sessione.dichiara_rotta("ALFA", "4 S", serbatoi=1, radar=3, computer=2, atterraggio=True)
        with self.assertRaises(ErroreDiRegolamento):
            sessione.riatterra("ALFA")


class TestEditorGalassia(unittest.TestCase):
    def galassia_a_mano(self) -> Galassia:
        pianeti = [
            Pianeta(posizione=Posizione(0, 0, 0), base=True),
            Pianeta(posizione=Posizione(0, 5, 5)),
        ]
        galassia = Galassia(seme="A-MANO", lato=12, pianeti=pianeti)
        galassia.reindicizza()
        return galassia

    def test_nuova_da_galassia_posiziona_le_navi_sulla_base(self):
        sessione = Sessione.nuova_da_galassia(
            self.galassia_a_mano(), ufficiali=["UNO", "DUE"],
            dettagli_navi={"UNO": {"classe_massa": 1, "princeps_psi": True}},
        )
        base = sessione.galassia.base.posizione
        self.assertEqual(sessione.nave("UNO").posizione, base)
        self.assertEqual(sessione.nave("UNO").classe_massa, 1)
        self.assertTrue(sessione.nave("UNO").princeps_psi)
        self.assertEqual(sessione.nave("DUE").classe_massa, 2)
        self.assertEqual(sorted(sessione.ordine_turno), ["DUE", "UNO"])
        self.assertEqual(sessione.distribuzione, "manuale")

    def test_nuova_da_galassia_propaga_spazio_esterno(self):
        sessione = Sessione.nuova_da_galassia(self.galassia_a_mano(), ufficiali=["UNO"], spazio_esterno=True)
        self.assertTrue(sessione.spazio_esterno)

    def test_nuova_da_galassia_annota_la_creazione_a_mano(self):
        sessione = Sessione.nuova_da_galassia(self.galassia_a_mano(), ufficiali=["UNO"])
        self.assertTrue(any("a mano dal master" in v["testo"] for v in sessione.registro))


class TestDichiarazioni(unittest.TestCase):
    """Terminale di bordo (3D): l'U.C. dichiara, lo S.C. esegue. Ordine di turno morbido."""

    def setUp(self):
        self.sessione = sessione_di_prova()

    def test_deposita_non_muove_la_nave(self):
        posizione = self.sessione.nave("ALFA").posizione
        self.sessione.deposita_dichiarazione("ALFA", "2 E", serbatoi=1, radar=2, computer=2)
        self.assertEqual(self.sessione.nave("ALFA").posizione, posizione)
        self.assertIsNotNone(self.sessione.nave("ALFA").dichiarazione_in_attesa)

    def test_risolvi_esegue_e_azzera_l_attesa(self):
        self.sessione.deposita_dichiarazione("ALFA", "2 E", serbatoi=1, radar=2, computer=2)
        self.sessione.risolvi_dichiarazione("ALFA")
        nave = self.sessione.nave("ALFA")
        self.assertEqual(nave.posizione, Posizione(0, 2, 0))
        self.assertIsNone(nave.dichiarazione_in_attesa)

    def test_annulla_ritira_la_dichiarazione(self):
        self.sessione.deposita_dichiarazione("ALFA", "2 E", serbatoi=1, radar=2, computer=2)
        self.sessione.annulla_dichiarazione("ALFA")
        self.assertIsNone(self.sessione.nave("ALFA").dichiarazione_in_attesa)

    def test_risolvere_senza_dichiarazione_e_un_errore(self):
        with self.assertRaises(ErroreDiRegolamento):
            self.sessione.risolvi_dichiarazione("ALFA")

    def test_una_rotta_malformata_e_respinta_al_deposito(self):
        with self.assertRaises(RottaNonValida):
            self.sessione.deposita_dichiarazione("ALFA", "banane", serbatoi=1, radar=2, computer=2)
        self.assertIsNone(self.sessione.nave("ALFA").dichiarazione_in_attesa)

    def test_turno_di_e_solo_un_indicatore(self):
        self.assertEqual(self.sessione.turno_di, "ALFA")  # tocca al primo dell'ordine
        self.sessione.deposita_dichiarazione("ALFA", "2 E", serbatoi=1, radar=2, computer=2)
        self.assertEqual(self.sessione.turno_di, "ALFA")  # una dichiarazione non consuma il turno
        self.sessione.risolvi_dichiarazione("ALFA")
        self.assertIsNone(self.sessione.turno_di)  # ALFA ha mosso: nessuno resta da muovere
        self.sessione.chiudi_turno()
        self.assertEqual(self.sessione.turno_di, "ALFA")  # nuovo turno: si riparte

    def test_lo_stato_espone_dichiarazione_e_turno(self):
        self.sessione.deposita_dichiarazione("ALFA", "2 E", serbatoi=1, radar=2, computer=2)
        stato = self.sessione.in_chiaro("uc")
        self.assertEqual(stato["turno_di"], "ALFA")
        [alfa] = stato["navi"]
        self.assertEqual(alfa["dichiarazione_in_attesa"]["rotta"], "2 E")


class TestStato(unittest.TestCase):
    def test_la_plancia_uc_occulta_i_sistemi_non_noti(self):
        sessione = Sessione.nuova(seme="OCCULTO", ufficiali=["UNO"])
        vista_sc = sessione.in_chiaro("sc")
        vista_uc = sessione.in_chiaro("uc")
        self.assertEqual(len(vista_sc["galassia"]["pianeti"]), 36)
        self.assertEqual(len(vista_uc["galassia"]["pianeti"]), 1)  # solo il pianeta base
        self.assertNotIn(sessione.galassia.seme, vista_uc["galassia"]["seme"])

    def test_partita_completa_riproducibile(self):
        def gioca() -> list[str]:
            sessione = Sessione.nuova(seme="RIPROVA", lato=12, ufficiali=["UNO"])
            for rotta in ("3 E", "4 GIU", "2 SE"):
                try:
                    sessione.dichiara_rotta("UNO", rotta, serbatoi=2, radar=3, computer=2)
                except Exception:  # noqa: BLE001 — una rotta respinta e' un esito valido
                    pass
            return [voce["testo"] for voce in sessione.registro]

        self.assertEqual(gioca(), gioca())


if __name__ == "__main__":
    unittest.main()
