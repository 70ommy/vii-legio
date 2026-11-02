"""Modello dati della TABULA SPATII: pianeti, anomalie, galassia."""

import unittest

from legio.modello import Anomalia, Galassia, Pianeta, Posizione, occulta_per_uc


def galassia_di_prova() -> Galassia:
    pianeti = [
        Pianeta(posizione=Posizione(0, 0, 0), base=True, informazioni={"tipo": "TERRA", "codice": "A"}),
        Pianeta(posizione=Posizione(0, 5, 5)),
    ]
    anomalie = [
        Anomalia(tipo="DN", celle=[Posizione(0, 3, 3)]),
        Anomalia(tipo="BN", celle=[Posizione(l, 8, 8) for l in range(4)], raggio_effetto=4),
    ]
    galassia = Galassia(seme="PROVA", lato=12, pianeti=pianeti, anomalie=anomalie)
    galassia.reindicizza()
    return galassia


class TestRimozione(unittest.TestCase):
    def test_rimuovi_pianeta(self):
        galassia = galassia_di_prova()
        galassia.rimuovi_pianeta(Posizione(0, 5, 5))
        self.assertEqual(len(galassia.pianeti), 1)
        self.assertIsNone(galassia.a(Posizione(0, 5, 5)))

    def test_rimuovi_anomalia(self):
        galassia = galassia_di_prova()
        [dn] = [a for a in galassia.anomalie if a.tipo == "DN"]
        galassia.rimuovi_anomalia(dn.id)
        self.assertEqual(len(galassia.anomalie), 1)
        self.assertIsNone(galassia.anomalia_a(Posizione(0, 3, 3)))

    def test_rimuovi_anomalia_inesistente_non_fa_nulla(self):
        galassia = galassia_di_prova()
        galassia.rimuovi_anomalia("BN-inesistente")
        self.assertEqual(len(galassia.anomalie), 2)


class TestRicostruzione(unittest.TestCase):
    def test_da_dict_ricostruisce_una_galassia_equivalente(self):
        originale = galassia_di_prova()
        ricostruita = Galassia.da_dict(originale.in_chiaro())
        self.assertEqual(ricostruita.seme, originale.seme)
        self.assertEqual(ricostruita.lato, originale.lato)
        self.assertEqual(ricostruita.in_chiaro(), originale.in_chiaro())

    def test_da_dict_ripopola_gli_indici(self):
        ricostruita = Galassia.da_dict(galassia_di_prova().in_chiaro())
        self.assertTrue(ricostruita.base.base)
        self.assertIsNotNone(ricostruita.anomalia_a(Posizione(0, 3, 3)))
        self.assertIsNotNone(ricostruita.anomalia_a(Posizione(2, 8, 8)))


class TestAvvistatoDa(unittest.TestCase):
    """Il Terminale di bordo evidenzia i sistemi avvistati dalla *propria* nave:
    il campo deve essere esposto da in_chiaro e sopravvivere alla vista U.C."""

    def test_in_chiaro_espone_gli_avvistatori(self):
        pianeta = Pianeta(posizione=Posizione(0, 5, 5), livelli_noti=["I"], avvistato_da=["ALFA"])
        self.assertEqual(pianeta.in_chiaro()["avvistato_da"], ["ALFA"])

    def test_sopravvive_alla_vista_uc(self):
        galassia = galassia_di_prova()
        [ignoto] = [p for p in galassia.pianeti if not p.base]
        ignoto.livelli_noti = ["I"]
        ignoto.avvistato_da = ["ALFA", "BETA"]
        filtrata = occulta_per_uc(galassia.in_chiaro())
        avvistato = next(p for p in filtrata["pianeti"] if p["id"] == ignoto.id)
        self.assertEqual(avvistato["avvistato_da"], ["ALFA", "BETA"])

    def test_round_trip_preserva_gli_avvistatori(self):
        galassia = galassia_di_prova()
        galassia.pianeti[1].avvistato_da = ["ALFA"]
        ricostruita = Galassia.da_dict(galassia.in_chiaro())
        self.assertEqual(ricostruita.in_chiaro(), galassia.in_chiaro())


class TestOccultamentoUc(unittest.TestCase):
    """Regola condivisa fra la partita in corso e l'anteprima dell'editor."""

    def test_le_anomalie_non_sono_mai_visibili(self):
        filtrata = occulta_per_uc(galassia_di_prova().in_chiaro())
        self.assertEqual(filtrata["anomalie"], [])

    def test_restano_solo_base_noti_e_barrati(self):
        galassia = galassia_di_prova()
        galassia.pianeti.append(Pianeta(posizione=Posizione(1, 2, 2), livelli_noti=["I"]))
        galassia.pianeti.append(Pianeta(posizione=Posizione(1, 4, 4), barrato=True))
        filtrata = occulta_per_uc(galassia.in_chiaro())
        self.assertEqual(
            sorted(p["id"] for p in filtrata["pianeti"]),
            ["L1·A1", "L2·C3", "L2·E5"],  # base, avvistato, barrato — non il sistema ignoto
        )

    def test_la_matricola_resta_riservata(self):
        filtrata = occulta_per_uc(galassia_di_prova().in_chiaro())
        self.assertNotIn("PROVA", filtrata["seme"])

    def test_non_altera_la_galassia_di_partenza(self):
        galassia = galassia_di_prova()
        in_chiaro = galassia.in_chiaro()
        occulta_per_uc(in_chiaro)
        self.assertEqual(len(in_chiaro["anomalie"]), 2)
        self.assertEqual(len(in_chiaro["pianeti"]), 2)


if __name__ == "__main__":
    unittest.main()
