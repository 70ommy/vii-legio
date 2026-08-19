"""Interfaccia a riga di comando della cella S.C."""

from __future__ import annotations

import argparse

from .generatore import DISTRIBUZIONI, genera_galassia
from .modello import LATO_PREDEFINITO, LETTERE, LIVELLI, NOMI_LIVELLO, Galassia, Posizione


def _tabula_ascii(galassia: Galassia) -> str:
    """Stampa la TABULA SPATII: livello piu' alto in alto a sinistra (sez. C)."""
    righe: list[str] = []
    lato = galassia.lato
    for livello in range(LIVELLI):
        titolo = f"─ SETTORE {NOMI_LIVELLO[livello]} "
        larghezza = max(2 * lato + 2, len(titolo))
        righe.append("")
        righe.append("  ┌" + titolo + "─" * (larghezza - len(titolo)) + "┐")
        righe.append("  │   " + " ".join(LETTERE[:lato]).ljust(larghezza - 3) + "│")
        for y in range(lato):
            celle = []
            for x in range(lato):
                pianeta = galassia.a(Posizione(livello, x, y))
                celle.append("·" if pianeta is None else ("B" if pianeta.base else "●"))
            corpo = f"{y + 1:>2} " + " ".join(celle)
            righe.append("  │" + corpo.ljust(larghezza) + "│")
        righe.append("  └" + "─" * larghezza + "┘")
    return "\n".join(righe)


def comando_genera(argomenti: argparse.Namespace) -> int:
    galassia, _ = genera_galassia(
        seme=argomenti.seme, lato=argomenti.lato, distribuzione=argomenti.distribuzione
    )
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  C.S.C. — CREAZIONE DELLA ZONA DI GALASSIA DA ESPLORARE     ║")
    print("║  Classifica: S.C. Classe B · Livello Basico Segreto         ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"  Matricola zona : {galassia.seme}")
    print(f"  TABULA SPATII  : {galassia.lato}×{galassia.lato} parsec per settore, 4 settori")
    print(f"  Sistemi        : {len(galassia.pianeti)} (9 per livello)")
    print(f"  Pianeta base B : {galassia.base.posizione.riferimento}")
    print(f"  Disposizione   : {argomenti.distribuzione} — {DISTRIBUZIONI[argomenti.distribuzione]}")
    print(_tabula_ascii(galassia))
    print("\n  Elenco riservato dei sistemi:")
    for livello in range(LIVELLI):
        sigle = " ".join(
            ("B:" if p.base else "") + p.posizione.sigla
            for p in sorted(galassia.del_livello(livello), key=lambda p: p.posizione)
        )
        print(f"    Livello {livello + 1}: {sigle}")
    print("\n  Il contenuto dei sistemi non e' stato generato: si tira ai dadi all'incontro.")
    return 0


def comando_consolle(argomenti: argparse.Namespace) -> int:
    from .server import avvia

    avvia(porta=argomenti.porta, apri_browser=not argomenti.senza_browser)
    return 0


def costruisci_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="legio",
        description="VII LEGIO — sistema di supporto dello Spazio Computer (C.S.C.).",
    )
    sotto = parser.add_subparsers(dest="comando")

    consolle = sotto.add_parser("consolle", help="avvia la consolle grafica dello S.C. (predefinito)")
    consolle.add_argument("--porta", type=int, default=7734)
    consolle.add_argument("--senza-browser", action="store_true", dest="senza_browser")
    consolle.set_defaults(funzione=comando_consolle)

    genera = sotto.add_parser("genera", help="genera una zona di galassia e stampala sul terminale")
    genera.add_argument("--seme", default=None, help="matricola della zona, per riprodurla identica")
    genera.add_argument("--lato", type=int, default=LATO_PREDEFINITO, help="parsec per lato di ogni settore")
    genera.add_argument(
        "--distribuzione", default="bilanciata", choices=sorted(DISTRIBUZIONI), help="disposizione dei sistemi"
    )
    genera.set_defaults(funzione=comando_genera)

    parser.set_defaults(funzione=comando_consolle, porta=7734, senza_browser=False)
    return parser


def _terminale_in_utf8() -> None:
    """Le console Windows partono spesso in cp1252 e non reggono i caratteri di cornice."""
    import sys

    for flusso in (sys.stdout, sys.stderr):
        riconfigura = getattr(flusso, "reconfigure", None)
        if riconfigura is not None:
            try:
                riconfigura(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass


def main(argomenti: list[str] | None = None) -> int:
    _terminale_in_utf8()
    parser = costruisci_parser()
    analizzati = parser.parse_args(argomenti)
    return analizzati.funzione(analizzati)
