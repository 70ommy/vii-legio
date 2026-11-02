"""Regolamento avanzato, Parte II — validazione della galassia costruita a mano."""

import unittest

from legio.editor import valida_galassia
from legio.modello import Anomalia, Galassia, Pianeta, Posizione


def pianeti_livello(livello: int, quanti: int = 9) -> list[Pianeta]:
    """`quanti` pianeti ben distanziati (>= 4 parsec) su un livello, per non far
    scattare errori estranei alla regola sotto test."""
    passo = 4
    pianeti = []
    for indice in range(quanti):
        x, y = (indice % 3) * passo, (indice // 3) * passo
        pianeti.append(Pianeta(posizione=Posizione(livello, x, y)))
    pianeti[0].base = True
    return pianeti


def galassia_base(livello_completo: int = 0) -> Galassia:
    """Un solo livello popolato di 9 pianeti (col base) in un angolo, gli altri vuoti.

    Il lato e' abbondante (20) per lasciare spazio, nell'angolo opposto, a celle
    davvero lontane da ogni pianeta — necessario per i test "non e' un errore".
    """
    pianeti = pianeti_livello(livello_completo)
    galassia = Galassia(seme="PROVA", lato=20, pianeti=pianeti)
    galassia.reindicizza()
    return galassia


class TestPianetaBase(unittest.TestCase):
    def test_nessun_pianeta_base_e_errore(self):
        galassia = Galassia(seme="PROVA", lato=12, pianeti=[Pianeta(posizione=Posizione(0, 0, 0))])
        referto = valida_galassia(galassia)
        self.assertTrue(any(e["codice"] == "base-assente" for e in referto["errori"]))

    def test_due_basi_e_errore(self):
        galassia = Galassia(
            seme="PROVA", lato=12,
            pianeti=[Pianeta(posizione=Posizione(0, 0, 0), base=True), Pianeta(posizione=Posizione(0, 5, 5), base=True)],
        )
        referto = valida_galassia(galassia)
        self.assertTrue(any(e["codice"] == "base-multipla" for e in referto["errori"]))

    def test_una_base_non_e_errore(self):
        galassia = galassia_base()
        referto = valida_galassia(galassia)
        self.assertFalse(any(e["codice"] in ("base-assente", "base-multipla") for e in referto["errori"]))


class TestConteggiDerogabili(unittest.TestCase):
    def test_meno_di_nove_pianeti_e_solo_avviso(self):
        galassia = galassia_base()
        galassia.rimuovi_pianeta(galassia.pianeti[-1].posizione)
        referto = valida_galassia(galassia)
        self.assertFalse(referto["errori"])
        self.assertTrue(any(a["codice"] == "conteggio-pianeti" for a in referto["avvisi"]))

    def test_nessuna_rmg_e_solo_avviso(self):
        referto = valida_galassia(galassia_base())
        self.assertTrue(any(a["codice"] == "conteggio-rmg" and a["livello"] == 0 for a in referto["avvisi"]))

    def test_nessuna_dn_e_solo_avviso(self):
        referto = valida_galassia(galassia_base())
        self.assertTrue(any(a["codice"] == "conteggio-dn" and a["livello"] == 0 for a in referto["avvisi"]))


class TestSovrapposizione(unittest.TestCase):
    def test_due_pianeti_sulla_stessa_cella_e_errore(self):
        galassia = Galassia(
            seme="PROVA", lato=12,
            pianeti=[
                Pianeta(posizione=Posizione(0, 0, 0), base=True),
                Pianeta(posizione=Posizione(0, 5, 5)),
                Pianeta(posizione=Posizione(0, 5, 5)),
            ],
        )
        referto = valida_galassia(galassia)
        self.assertTrue(any(e["codice"] == "sovrapposizione-pianeti" for e in referto["errori"]))


class TestRmg(unittest.TestCase):
    def test_rmg_non_contigua_e_errore(self):
        galassia = galassia_base()
        galassia.aggiungi_anomalia(
            Anomalia(tipo="RMG", celle=[Posizione(0, 10, 10), Posizione(0, 1, 1), Posizione(0, 11, 11)])
        )
        referto = valida_galassia(galassia)
        self.assertTrue(any(e["codice"] == "rmg-non-contigua" for e in referto["errori"]))

    def test_rmg_troppo_vicina_a_un_pianeta_e_errore(self):
        galassia = galassia_base()
        # Il pianeta [0] e' in (0,0): due celle a distanza < 4 violano la regola.
        galassia.aggiungi_anomalia(
            Anomalia(tipo="RMG", celle=[Posizione(0, 1, 0), Posizione(0, 2, 0), Posizione(0, 2, 1)])
        )
        referto = valida_galassia(galassia)
        self.assertTrue(any(e["codice"] == "rmg-troppo-vicina" for e in referto["errori"]))

    def test_rmg_contigua_e_distante_non_e_errore(self):
        galassia = galassia_base()
        galassia.aggiungi_anomalia(
            Anomalia(tipo="RMG", celle=[Posizione(0, 18, 18), Posizione(0, 17, 18), Posizione(0, 17, 17)])
        )
        referto = valida_galassia(galassia)
        self.assertFalse([e for e in referto["errori"] if e["codice"].startswith("rmg-")])


class TestBucoNero(unittest.TestCase):
    def test_buco_nero_troppo_vicino_e_errore(self):
        galassia = galassia_base()
        galassia.aggiungi_anomalia(
            Anomalia(tipo="BN", celle=[Posizione(l, 1, 0) for l in range(4)], raggio_effetto=4)
        )
        referto = valida_galassia(galassia)
        self.assertTrue(any(e["codice"] == "bn-troppo-vicino" and e["livello"] == 0 for e in referto["errori"]))

    def test_buco_nero_abbastanza_distante_non_e_errore(self):
        galassia = galassia_base()
        galassia.aggiungi_anomalia(
            Anomalia(tipo="BN", celle=[Posizione(l, 18, 18) for l in range(4)], raggio_effetto=4)
        )
        referto = valida_galassia(galassia)
        self.assertFalse([e for e in referto["errori"] if e["codice"] == "bn-troppo-vicino"])


class TestInfo(unittest.TestCase):
    def test_totale_pianeti_sempre_presente(self):
        referto = valida_galassia(galassia_base())
        self.assertTrue(any(i["codice"] == "totale-pianeti" for i in referto["info"]))


if __name__ == "__main__":
    unittest.main()
