"""Sez. D/E — dichiarazioni di rotta, limiti della zona, avvistamenti, atterraggi."""

import unittest

from legio.modello import Galassia, Pianeta, Posizione, scomponi_direzione
from legio.rotte import RottaNonValida, analizza_rotta, esegui_movimento


def galassia_di_prova(*coordinate: tuple[int, int, int], lato: int = 12) -> Galassia:
    pianeti = [Pianeta(posizione=Posizione(*c)) for c in coordinate]
    pianeti[0].base = True
    galassia = Galassia(seme="PROVA", lato=lato, pianeti=pianeti)
    galassia.reindicizza()
    return galassia


class TestDirezioni(unittest.TestCase):
    def test_esempio_del_manuale(self):
        """«Distanza dal pianeta 3 parsec — Direzione 2 Ovest + 1 Nord-Ovest.»"""
        self.assertEqual(scomponi_direzione(-3, -1), "2 Ovest + 1 Nord-Ovest")

    def test_solo_diagonale_e_solo_retta(self):
        self.assertEqual(scomponi_direzione(2, 2), "2 Sud-Est")
        self.assertEqual(scomponi_direzione(0, -4), "4 Nord")


class TestDichiarazione(unittest.TestCase):
    def test_esempio_del_manuale(self):
        segmenti = analizza_rotta("10 N, +5 E")
        self.assertEqual([(s.parsec, s.direzione) for s in segmenti], [(10, "N"), (5, "E")])

    def test_alias_e_nomi_estesi(self):
        segmenti = analizza_rotta("3 Nord-Ovest, 4 GIU, 2 sud")
        self.assertEqual([s.direzione for s in segmenti], ["NO", "GIU", "S"])

    def test_cambio_livello_multiplo_di_quattro(self):
        with self.assertRaises(RottaNonValida):
            analizza_rotta("3 SU")
        self.assertEqual(analizza_rotta("8 SU")[0].parsec, 8)

    def test_rotta_incomprensibile(self):
        with self.assertRaises(RottaNonValida):
            analizza_rotta("verso il centro della galassia")


class TestMovimento(unittest.TestCase):
    def setUp(self):
        # base in A1, un sistema in A5 (quattro parsec piu' a sud), uno in D3.
        self.galassia = galassia_di_prova((0, 0, 0), (0, 0, 4), (0, 3, 2))
        self.base = Posizione(0, 0, 0)

    def test_limite_della_zona(self):
        movimento = esegui_movimento(
            self.galassia, self.base, analizza_rotta("5 N"), radar=3, serbatoi=1
        )
        self.assertEqual(movimento.arrivo, self.base)
        self.assertEqual(movimento.motivo_fermata, "limite della zona")

    def test_fermata_al_primo_parsec_di_avvistamento(self):
        movimento = esegui_movimento(
            self.galassia, self.base, analizza_rotta("8 S"), radar=1, serbatoi=2
        )
        self.assertEqual(movimento.arrivo, Posizione(0, 0, 3))  # A4
        self.assertIn("sistema sulla rotta", movimento.motivo_fermata)
        self.assertIsNone(movimento.atterraggio_su)

    def test_senza_radar_atterraggio_obbligato(self):
        movimento = esegui_movimento(
            self.galassia, self.base, analizza_rotta("8 S"), radar=0, serbatoi=2
        )
        self.assertEqual(movimento.arrivo, Posizione(0, 0, 4))
        self.assertTrue(movimento.atterraggio_obbligato)
        self.assertEqual(movimento.atterraggio_su, "L1·A5")
        self.assertEqual(movimento.avvistamenti, [])

    def test_atterraggio_dichiarato_a_fine_rotta(self):
        movimento = esegui_movimento(
            self.galassia, self.base, analizza_rotta("4 S"), radar=3, serbatoi=1,
            atterraggio_dichiarato=True,
        )
        self.assertEqual(movimento.arrivo, Posizione(0, 0, 4))
        self.assertEqual(movimento.atterraggio_su, "L1·A5")
        self.assertFalse(movimento.atterraggio_obbligato)

    def test_avvistamento_comunica_parsec_distanza_e_direzione(self):
        movimento = esegui_movimento(
            self.galassia, self.base, analizza_rotta("2 E"), radar=2, serbatoi=1
        )
        avvistamento = next(a for a in movimento.avvistamenti if a.pianeta_id == "L1·D3")
        # Il sistema e' a 2 parsec sia dal 1° sia dal 2° parsec di rotta: si comunica il piu' vicino.
        self.assertEqual(avvistamento.parsec_rotta, 1)
        self.assertEqual(avvistamento.distanza, 2)
        self.assertEqual(avvistamento.direzione, "2 Sud-Est")
        self.assertEqual(avvistamento.tutti_i_parsec, [1, 2])

    def test_autonomia_dei_serbatoi(self):
        with self.assertRaises(RottaNonValida):
            esegui_movimento(self.galassia, self.base, analizza_rotta("8 E"), radar=3, serbatoi=1)

    def test_cambio_livello_costa_quattro_parsec(self):
        movimento = esegui_movimento(
            self.galassia, self.base, analizza_rotta("8 GIU"), radar=0, serbatoi=2
        )
        self.assertEqual(movimento.arrivo, Posizione(2, 0, 0))
        self.assertEqual(movimento.parsec_percorsi, 8)
        self.assertTrue(movimento.passi[-1].cambio_livello)

    def test_non_esistono_livelli_oltre_il_quarto(self):
        movimento = esegui_movimento(
            self.galassia, self.base, analizza_rotta("20 GIU"), radar=0, serbatoi=4
        )
        self.assertEqual(movimento.arrivo.livello, 3)
        self.assertEqual(movimento.motivo_fermata, "limite verticale della zona")

    def test_radar_oltre_il_massimo_respinti(self):
        with self.assertRaises(RottaNonValida):
            esegui_movimento(self.galassia, self.base, analizza_rotta("1 E"), radar=4, serbatoi=1)

    def test_nessun_avvistamento_fra_livelli_diversi(self):
        """I livelli distano 4 parsec: con 3 radar al massimo non si vede il livello vicino."""
        galassia = galassia_di_prova((0, 0, 0), (1, 0, 0))
        movimento = esegui_movimento(
            galassia, Posizione(0, 0, 0), analizza_rotta("1 E"), radar=3, serbatoi=1
        )
        self.assertNotIn("L2·A1", [a.pianeta_id for a in movimento.avvistamenti])


if __name__ == "__main__":
    unittest.main()
