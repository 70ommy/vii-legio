"""VII LEGIO — sistema di supporto per lo Spazio Computer (C.S.C.).

Genera la zona di galassia tridimensionale da esplorare, traccia le rotte
dichiarate dagli U.C., calcola gli avvistamenti radar e risolve informazioni e
atterraggi tirando i dadi sulle Schede Informazioni e sulla Guida Incontri.
"""

from __future__ import annotations

from .dadi import Dadiera
from .generatore import genera_galassia
from .modello import Galassia, Pianeta, Posizione
from .sessione import Sessione

__all__ = ["Dadiera", "Galassia", "Pianeta", "Posizione", "Sessione", "genera_galassia", "main"]
__version__ = "0.1.0"


def main(argomenti: list[str] | None = None) -> int:
    from .cli import main as _main

    return _main(argomenti)
