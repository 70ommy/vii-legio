# VII LEGIO — Terminale dello Spazio Computer

Sistema di supporto per la fase di esplorazione di **VII Legio**: genera la zona di
galassia tridimensionale, traccia le rotte dichiarate dagli Ufficiali Comandanti,
calcola gli avvistamenti radar e risolve informazioni e atterraggi tirando i dadi
sulle Schede Informazioni e sulla Guida Incontri.

Nessuna dipendenza esterna: solo libreria standard di Python (≥ 3.14).

> **Strumento non ufficiale.** Progetto di giocatori, senza alcun rapporto con gli
> autori o gli editori di VII Legio. Il testo del regolamento **non è incluso** in
> questo repository: serve la propria copia del gioco per usarlo al tavolo.

## Avvio

```powershell
uv sync
uv run legio                 # apre la consolle grafica su http://127.0.0.1:7734/
uv run legio genera          # stampa una zona di galassia sul terminale
uv run legio genera --seme MIA-ZONA-0001 --lato 14 --distribuzione libera
uv run python -m unittest discover -s tests -t .
```

## Che cosa fa

| Sezione del regolamento | Nel programma |
|---|---|
| **C** Creazione della zona | 4 settori (livelli), 9 sistemi ciascuno, 36 in tutto, 1 pianeta base **B**, nessuna sovrapposizione |
| **D** Rotte | dichiarazione tipo `10 N, +5 E`, non necessariamente rettilinea; fermata all'ultimo parsec utile se esce dalla zona; `SU`/`GIU` per cambiare livello (4 parsec a salto) |
| **E** Avvistamenti | gittata di 1 parsec per radar fino a 3; comunicazione di parsec, distanza e direzione nella dizione del manuale; fermata sul primo parsec di avvistamento se la rotta attraversa un sistema; atterraggio obbligatorio senza radar |
| **F** Informazioni | livelli I→IV a cascata, ogni informazione tiene presente le precedenti; una richiesta per computer di bordo; solo entro il raggio radar; D.N.S. che spreca la richiesta; notizie di pubblico dominio ripetute gratuitamente; pianeti barrati alla ripartenza |
| **G** Atterraggio | completamento delle informazioni mancanti, TAB. PRESENZE, attività degli Alieni con indicazione di chi tira il dado, TAB. ARRIVI, attribuzione dei punti |

### Il contenuto dei pianeti non esiste in anticipo

La generazione crea **solo la topografia**. Tipo di pianeta, forme di vita, grado di
sapienza e razza aliena vengono tirati ai dadi nel momento in cui una nave li
incontra: così «neanche lo Spazio Computer conosce con precisione in cosa si
imbatteranno le astronavi».

### Matricola della zona (seme)

Ogni zona ha una matricola. Rigenerando con la stessa matricola si riottiene la
stessa mappa e la stessa sequenza di dadi: utile per riprendere una partita o per
verificare che lo S.C. non abbia commesso errori.

## Consolle

- **Quattro settori** — la TABULA SPATII come sul tavolo: livello più alto in alto a
  sinistra, più basso in basso a destra, lettere e numeri a fianco di ogni livello.
- **Stereoscopio 3D** — i quattro livelli in proiezione isometrica, distanziati dei
  4 parsec di regolamento, con le rotte che passano da un livello all'altro.
- **Plancia U.C.** — occulta i sistemi non ancora avvistati: è la vista da proiettare
  ai giocatori senza rivelare la mappa.
- **Registro di cella** — ogni comunicazione e ogni tiro di dado, esportabile in JSON
  e stampabile.

## Tabelle

`src/legio/dati/scheda_informazioni.json` e `src/legio/dati/guida_incontri.json`
contengono la Scheda Informazioni e la Guida Incontri. **Sono una ricostruzione**:
il regolamento in nostro possesso descrive il meccanismo (livelli a cascata, dadi
indicati di volta in volta, D.N.S., riferimento alla G.I. dato dal IV livello) ma non
riporta le tabelle. Sono state ricostruite coerentemente — l'esempio del manuale
«vegetali non sapiens → d6 1-3 VELENOSI, 4-6 MOSTRI» è riprodotto esattamente — e
possono essere sostituite con quelle originali mantenendo il formato.

Formato di una tabella:

```json
{
  "quando": {"vita": ["MINERALI"]},   // condizioni sulle notizie già ottenute
  "dado": "d10",
  "esiti": [
    {"faccia": "1-3", "dati": {"sapienza": "SAPIENS"}},
    {"faccia": "10",  "dns": true}
  ]
}
```

La prima tabella le cui condizioni sono soddisfatte è quella che si legge; una
tabella con `"quando": {}` fa da ripiego.

## Assunzioni prese

Il regolamento non le fissa; sono tutte in un punto solo e modificabili.

| Assunzione | Valore | Perché |
|---|---|---|
| Lato di un settore | 12 parsec | compatibile con le rotte dell'esempio (`10 N, +5 E`); regolabile da 6 a 21 |
| Autonomia di un serbatoio | 5 parsec | dall'esempio della sez. E: 15 parsec dichiarati con 3 serbatoi |
| Costo di un cambio di livello | 4 parsec | è la distanza fra i livelli fissata dalla sez. C |
| Pianeta base | non viene barrato | è la casa della Legio: barrarlo alla prima ripartenza la renderebbe irraggiungibile |
| E. (unità d'equipaggio) per nave | 3 | il regolamento avanzato usa F.C. per singolo E. ma non ne fissa il numero per nave; valore in attesa di conferma dal manuale fisico |
| Classe/massa della nave (formula Buco Nero) | 3 classi, massa 1/2/3 | il regolamento avanzato usa "MASSA (livello della nave)" nella formula del B.N. senza definirla; scelta dall'U.C. alla creazione, in attesa di conferma dal manuale fisico |

Sono in [`src/legio/modello.py`](src/legio/modello.py) (`LATO_PREDEFINITO`,
`PARSEC_PER_SERBATOIO`, `PARSEC_FRA_LIVELLI`).

## Struttura

```
src/legio/
  dadi.py          d6 e d10 con seme e registro dei lanci
  modello.py       parsec, direzioni, pianeti, livelli, galassia
  generatore.py    sez. C — creazione della zona
  rotte.py         sez. D/E — tracciamento, avvistamenti, atterraggi
  schede.py        sez. F/G — Schede Informazioni e Guida Incontri
  sessione.py      stato della partita, navi, registro, punteggi
  server.py        terminale HTTP locale (solo stdlib)
  cli.py           riga di comando
  dati/            tabelle in JSON
  web/             consolle grafica
tests/             suite unittest
```
