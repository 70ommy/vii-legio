"""Sez. C — la creazione della zona deve rispettare il regolamento alla lettera."""

import unittest

from legio.generatore import genera_galassia
from legio.modello import LIVELLI, PIANETI_PER_LIVELLO


class TestGenerazione(unittest.TestCase):
    def test_trentasei_sistemi_nove_per_livello(self):
        for distribuzione in ("libera", "bilanciata", "ammassata"):
            with self.subTest(distribuzione=distribuzione):
                galassia, _ = genera_galassia(seme="PROVA", distribuzione=distribuzione)
                self.assertEqual(len(galassia.pianeti), LIVELLI * PIANETI_PER_LIVELLO)
                for livello in range(LIVELLI):
                    self.assertEqual(len(galassia.del_livello(livello)), PIANETI_PER_LIVELLO)

    def test_nessuna_sovrapposizione_sullo_stesso_livello(self):
        galassia, _ = genera_galassia(seme="SOVRAPPOSTI", distribuzione="ammassata")
        posizioni = [p.posizione for p in galassia.pianeti]
        self.assertEqual(len(posizioni), len(set(posizioni)))

    def test_un_solo_pianeta_base(self):
        galassia, _ = genera_galassia(seme="BASE")
        self.assertEqual(sum(1 for p in galassia.pianeti if p.base), 1)
        self.assertEqual(galassia.base.etichetta, "B")

    def test_stesso_seme_stessa_zona(self):
        prima, _ = genera_galassia(seme="RIPETIBILE")
        seconda, _ = genera_galassia(seme="RIPETIBILE")
        self.assertEqual(
            [p.posizione for p in prima.pianeti], [p.posizione for p in seconda.pianeti]
        )
        self.assertEqual(prima.base.posizione, seconda.base.posizione)

    def test_semi_diversi_zone_diverse(self):
        prima, _ = genera_galassia(seme="ALFA")
        seconda, _ = genera_galassia(seme="BETA")
        self.assertNotEqual(
            [p.posizione for p in prima.pianeti], [p.posizione for p in seconda.pianeti]
        )

    def test_il_contenuto_non_viene_generato_in_anticipo(self):
        galassia, _ = genera_galassia(seme="VUOTI")
        for pianeta in galassia.pianeti:
            self.assertEqual(pianeta.informazioni, {})
            self.assertEqual(pianeta.livelli_noti, [])

    def test_lato_fuori_scala_respinto(self):
        with self.assertRaises(ValueError):
            genera_galassia(seme="X", lato=3)


if __name__ == "__main__":
    unittest.main()
