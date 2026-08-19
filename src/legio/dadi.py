"""Dadi della C.S.C. — d6 e d10, con seme per riprodurre una partita.

Ogni tiro viene registrato: lo S.C. deve poter dimostrare di non aver commesso
errori (cfr. Regolamento, sez. A).
"""

from __future__ import annotations

import random
import secrets
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Tiro:
    """Un singolo lancio, con il motivo per cui e' stato effettuato."""

    dado: str
    esito: int
    motivo: str

    def __str__(self) -> str:
        return f"{self.dado} → {self.esito}"


@dataclass
class Dadiera:
    """Contenitore dei due dadi dello S.C. piu' il registro dei lanci."""

    seme: str
    _rng: random.Random = field(init=False, repr=False)
    registro: list[Tiro] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seme)

    @staticmethod
    def seme_casuale() -> str:
        """Seme leggibile a voce, nello stile delle matricole C.S.C."""
        gruppi = ("".join(secrets.choice("0123456789ABCDEFGHJKLMNPRSTVXZ") for _ in range(4)) for _ in range(3))
        return "-".join(gruppi)

    def tira(self, dado: str, motivo: str = "") -> Tiro:
        facce = FACCE.get(dado.lower())
        if facce is None:
            raise ValueError(f"dado non in dotazione alla C.S.C.: {dado!r}")
        tiro = Tiro(dado=dado.lower(), esito=self._rng.randint(1, facce), motivo=motivo)
        self.registro.append(tiro)
        return tiro

    def d6(self, motivo: str = "") -> Tiro:
        return self.tira("d6", motivo)

    def d10(self, motivo: str = "") -> Tiro:
        return self.tira("d10", motivo)

    def scegli(self, sequenza):
        """Estrazione a sorte (ordine di gioco, posizione dei pianeti, ...)."""
        return self._rng.choice(list(sequenza))

    def mescola(self, sequenza: list) -> None:
        self._rng.shuffle(sequenza)

    def campiona(self, popolazione, k: int) -> list:
        return self._rng.sample(list(popolazione), k)


FACCE = {"d6": 6, "d10": 10}
