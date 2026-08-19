"""La partita vista dalla cella dello S.C."""

import unittest

from legio.dadi import Dadiera
from legio.modello import Galassia, Pianeta, Posizione
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
