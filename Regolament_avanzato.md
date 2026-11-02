# Regolamento Civile — C.S.C. · Modalità Spazio Esterno (Avanzato)

**Sezione:** Viaggi di esplorazione in settori esterni incogniti
**Accesso:** S.C. Classe A · **Livello:** Avanzato Segretissimo

> **Nota generale.** Rimangono valide tutte le norme previste per lo spazio interno. Questo documento è **complementare** al regolamento base (`regolamento_csc.md`): aggiunge i rischi ambientali, la radioattività, gli atterraggi rischiosi e le navi aliene, e in coda fornisce la specifica per costruire l'**Editor Galassia** con Claude Code.

> **Uso come prompt.** La Parte I estende il manuale dello S.C. per la modalità difficile. La Parte II è una specifica tecnica da fornire a Claude Code per aggiungere all'interfaccia un editor con cui il master posiziona a mano pianeti e anomalie sulla TABULA SPATII.

---

## Sigle aggiuntive

Oltre a quelle del file base (S.C., U.C., S.N., S.N.A., G.I., TABULA SPATII, parsec, D.N.S.):

- **B.N.** — Buco Nero.
- **R.M.G.** — Rete Magneto-Gravitazionale.
- **D.N.** — Distorsione Nullius.
- **E.** — unità/membri d'equipaggio di una nave (i "fattori degli E." usati nelle missioni).
- **F.C.Att. / F.C.Dif.** — Fattore di Combattimento in Attacco / in Difesa.
- **Princeps Psi** — figura speciale a bordo che consente di percepire alcune anomalie altrimenti invisibili (vedi G.I.).
- **tuta BIMBER / tuta LEGGY** — tute anti-radiazione (vedi G.I.).
- **TAB. C / M / N / O / P / Q** — tabelle di risoluzione: danni (C), esiti attacco Legionario (M), esiti attacco alieno (N), massa/atterraggio (O), zone di atterraggio (P), navi aliene (Q).

---

# Parte I — Regole aggiuntive per lo spazio esterno

## A) Lo spazio esterno — Rischi

Se nella geografia dello spazio interno si trovano solo i pianeti, in quello esterno si possono incontrare anche **Buchi Neri**, **Reti Magneto-Gravitazionali** e **Distorsioni Nullius**. Nessuna di queste anomalie è rilevabile dai radar.

### Buco Nero (B.N.)

- Presente in numero di **uno per livello**, esattamente nello **stesso punto** su tutti i livelli.
- Va inserito sulla TABULA SPATII a **non meno di 5 parsec** dal pianeta più vicino.
- Entro un raggio di **4 parsec** ha effetti sulle navi che vi transitano vicino, secondo la formula:

  `DISTANZA − MASSA (livello della nave) − ESITO CASUALE (d6)`

  dove la distanza è calcolata dal parsec di rotta più vicino al nucleo del B.N.
- Il B.N. **non è visibile con i radar**.
- L'eventuale **numero negativo** ottenuto equivale al numero di danni subiti da quella nave, da controllare sulla **TAB. C** alla fine della rotta in questione, a cura dell'U.C.
- Gli effetti del B.N. vengono comunicati indicando il parsec in cui si sono subiti, **senza rivelare l'esatta posizione** del B.N.

### Reti Magneto-Gravitazionali (R.M.G.)

- Se ne trova **una su ogni livello**, non necessariamente in corrispondenza tra loro.
- Ognuna occupa **3 parsec² adiacenti**, disposti in qualsiasi modo tra loro.
- La rotta che ne attraversa anche **un solo elemento** vi si ferma, **senza** che ciò sia comunicato all'U.C. — salvo in presenza di **Princeps Psi** a bordo.
- In presenza di Psi occorre tuttavia controllare se la scoperta lo uccide (vedi G.I.).
- Ogni R.M.G. deve **distare** non meno di **4 parsec** dal pianeta più vicino.
- Il turno successivo all'incontro, la rotta di quella nave ripartirà dal parsec in cui è avvenuto l'incontro.
- Anche le R.M.G. **non sono visibili con i radar**.

### Distorsioni Nullius (D.N.)

- Presenti in numero di **3 su ogni livello**, non necessariamente adiacenti; ognuna occupa **1 parsec²**.
- La rotta che le attraversa **viene bloccata**, comunicandolo all'U.C.
- Ciò che l'U.C. **non sa** (salvo Princeps Psi a bordo) è **da dove ripartirà** la rotta successiva. Lo S.C. lo calcola **in segreto** con due esiti casuali:
  - **I esito (d6):** `1 = Nord · 2 = Est · 3 = Sud · 4 = Ovest · 5 = Alto · 6 = Basso`
  - **II esito (d6):** la distanza a cui si arriva è pari all'esito stesso.
- Se la distorsione portasse **fuori dalla TABULA SPATII**, il movimento di distorsione si ferma nell'ultimo parsec prima dell'uscita.
- Se la distorsione facesse finire **esattamente su un pianeta**, scatta l'**atterraggio immediato e obbligatorio**, secondo le norme generali.
- Anche le D.N. **non sono rilevate dai radar**.

## B) Radioattività media presente sui pianeti

Al primo livello di informazione, in un settore definito "spazio esterno", la Scheda Informazioni indica come stabilire — tramite il solito esito casuale — il **livello di radioattività** di un pianeta. Va comunicato all'U.C. insieme al **tipo di atmosfera** e riportato sulla TABULA SPATII accanto alla lettera che identifica il tipo di pianeta.

Livelli di radioattività:

- **0** = inesistente
- **α** = 1° livello
- **β** = 2° livello

Per proteggere gli E. sbarcati in presenza di radioattività esistono due tute anti-radio (vedi G.I.):

- **Tuta BIMBER** — protegge dai raggi di tipo **α**; impacciando limitatamente i movimenti, **abbassa di 1 punto** il F.C. di un E. (2 invece di 3).
- **Tuta LEGGY** — protegge dai raggi di tipo **β**; più ingombrante, **toglie 2 punti** rendendo il F.C. di un E. uguale a **1**.

> Esempio di conteggio punti: un E. a cui viene eliminato 1 membro vale 1 punto; se perde 2 membri vale 0 punti, e così via.

## C) Massa e rischi in atterraggio

Non tutti i pianeti hanno la stessa gravità: ogni atterraggio è soggetto a rischi variabili, proporzionali alla massa del pianeta.

Lo S.C. lo stabilisce con un esito casuale (**d6**) controllato sulla **TAB. O** nel momento dell'atterraggio. Se il lancio è uguale a uno dei numeri scritti nella riga della tabella corrispondente al pianeta, quel numero coincide con i **danni subiti** dalla nave in atterraggio, poi controllati sulla **TAB. C** come di norma.

## D) Zone di atterraggio

A differenza dei viaggi nelle zone interne — dove tutte le attività, atterraggi compresi, sono sotto controllo dell'U.C. — nelle zone esterne occorre considerare le diverse **zone di pianeta** in cui una nave può atterrare.

- La zona è stabilita dall'**U.C.** con un esito casuale (**d10**) controllato sulla **TAB. P**.
- La G.I. (Scheda Tecnica) indica le zone in cui le razze aliene sono **più forti** e quelle in cui sono **assenti**:
  - **Zona forte:** il F.C. di ogni Alieno è **maggiorato** del valore scritto sotto la voce **AMBIENTE PREFERITO**.
  - **Zona assente:** l'U.C. può usare solo i fattori degli E. per svolgere le missioni; in compenso la nave **non può subire danni** da attacchi alieni.
- L'U.C. insoddisfatto della zona può tentare un **nuovo atterraggio** dichiarando una rotta che decolli e riatterri. Ciò **non** definisce il pianeta come "noto". Il riatterraggio è ammesso **una sola volta** ed è eseguito nel modo normale (controllo sulla **TAB. P**).

## E) Le navi aliene

### Note generali

- Ultimo compito dello S.C. è lo **spostamento delle navi aliene**. Il movimento è **automatico**: si spostano sempre, lungo il **percorso più breve**, verso la nave repubblicana più vicina, in base a un proprio **fattore movimento**.
- Può esistere **una sola nave aliena per volta**, sostituibile solo quando viene distrutta.
- Il tipo di nave è calcolato dallo S.C. al momento dell'ingresso tramite la **TAB. Q**, che riporta anche **F.C.Att.**, **F.C.Dif.** e **fattore movimento**. Il **lato** di ingresso è dato dalla TAB. Q; il **parsec preciso** di quel lato è scelto dallo S.C.
- Il **livello di ingresso** è quello in cui sono presenti più nemici.
- **Attenzione:** le navi atterrate su un qualsiasi pianeta **non attirano** le navi aliene.
- La posizione della nave aliena è ricordata piazzando il **S.N. nero**.
- Il suo movimento avviene alla **fine di un turno generale** in cui tutti gli U.C. hanno agito.
- Se sul livello della nave aliena non ci sono più navi, anch'essa cambia livello, verso quello **più popolato**.
- Una nave aliena può essere **captata dai radar**, ma solo durante il movimento dell'U.C.

### Il combattimento

Quando la nave aliena entra in un parsec in cui si trova un Legionario, questi viene attaccato. Svolgimento:

1. **Turno alieno** — l'alieno arriva nel parsec del Legionario e lo attacca (lo S.C. controlla gli esiti sulla **TAB. N**; eventuali danni sono controllati dall'U.C. sulla **TAB. C**).
2. **Turno Legionario** — controlla un esito casuale (**d6**): con **5 o 6** può andarsene; altrimenti attacca la nave che lo aggancia, con esiti sulla **TAB. M** (`D = eliminata`, `R = F.C.Att. e Dif. al 50%`).

Il combattimento continua fino allo **sganciamento** del Legionario o alla **distruzione** dell'Alieno.

È ammesso unire **2 navi della Legio** contro un Alieno: i loro F.C.Att. sono usati nei singoli turni; anche i F.C.Dif. restano separati e l'Alieno ne attacca **una alla volta** (quale, è scelto liberamente dallo S.C.). **Nessun punto** è attribuito per l'eliminazione di navi aliene.

## F) Riassunto delle attività dello S.C. (spazio esterno)

1. Disegna la **TABULA SPATII**.
2. Sposta i **S.N.** degli U.C.
3. Segnala gli **avvistamenti**.
4. Dà **informazioni** tratte da Scheda Informazioni e G.I.
5. Svolge tutte le **attività degli Alieni**.
6. Sposta le **navi aliene** dopo averne controllato il tipo.
7. Controlla **presenza e nuovi arrivi** sui vari pianeti.
8. Attribuisce **punti e gradi**.

---

# Parte II — Editor Galassia (specifica per Claude Code)

## Obiettivo

Aggiungere all'interfaccia una modalità **Master / Editor Galassia** che consenta allo S.C. di **creare a mano** la TABULA SPATII: posizionare pianeti e anomalie cliccando sulle celle della griglia, assegnarne le proprietà, validare il tutto contro le regole del regolamento ed esportarlo/importarlo. La galassia è costruita **in segreto** dal master; i giocatori vedono solo ciò che è "di dominio pubblico".

## Contesto per Claude Code

> Questa sezione è pensata per essere incollata a Claude Code come specifica. Se esiste già un componente che disegna la TABULA SPATII, **estenderlo**; altrimenti crearlo. Non modificare le regole di gioco: implementare solo posizionamento manuale, proprietà e validazione. Le anomalie sono invisibili ai radar, quindi devono essere nascoste nella vista giocatori.
>
> Stack consigliato: single-page (React + Tailwind, oppure HTML/JS vanilla) coerente col resto del progetto. **Persistenza:** se il progetto gira in un repo reale (Claude Code), usare `localStorage` e/o file JSON su disco; se il target è un artifact di Claude.ai, **non** usare `localStorage` — tenere lo stato in memoria e persistere solo via **export/import di file JSON**.

## Modello dati

```json
{
  "mode": "external",                // "internal" | "external"
  "gridSize": { "cols": 12, "rows": 12 },
  "distanceMetric": "chebyshev",     // parsec = celle; 8 direzioni ⇒ Chebyshev
  "levels": [
    {
      "id": 0,                        // 0=alto-sx, 1=alto-dx, 2=basso-sx, 3=basso-dx
      "label": "Livello I (più alto)",
      "planets": [
        {
          "id": "p-0-1",
          "cell": { "x": 3, "y": 5 },
          "letter": "B",             // lettera/tipo mostrato sulla TABULA
          "isBase": true,
          "type": null,              // es. "A terrestre" (assegnabile in gioco)
          "radioactivity": "0",      // "0" | "alpha" | "beta"  (solo external)
          "atmosphere": null,
          "infoRef": null,           // riferimento G.I. (numero razza)
          "discovered": false,       // se true → visibile ai giocatori
          "cleared": false           // "noto", non più visitabile
        }
      ],
      "anomalies": [
        { "id": "bn-0", "type": "BN", "cell": { "x": 8, "y": 2 }, "effectRadius": 4, "hidden": true },
        { "id": "rmg-0", "type": "RMG", "cells": [ {"x":1,"y":9}, {"x":2,"y":9}, {"x":2,"y":10} ], "hidden": true },
        { "id": "dn-0-1", "type": "DN", "cell": { "x": 6, "y": 6 }, "hidden": true }
      ]
    }
    // ... 4 livelli in totale
  ]
}
```

Note di modello:
- `distanceMetric` di default **Chebyshev** (`max(|dx|,|dy|)`), coerente con rotte a 8 direzioni e "1 parsec = 1 quadretto". Renderlo configurabile.
- Il **Buco Nero** ha la stessa `cell` su tutti i livelli: memorizzare un unico `blackHole.cell` a livello di galassia e replicarlo, oppure validare che le 4 `BN.cell` coincidano.

## Layout della TABULA SPATII

- 4 livelli disposti in griglia **2×2**: livello 0 in alto a sinistra (il più alto), livello 3 in basso a destra (il più basso).
- Ogni livello è una griglia `cols × rows` (default 12×12, configurabile dal master).
- A fianco di ogni livello, mostrare **lettere e numeri** di riferimento per il cambio livello (come da regolamento base), in modo che un parsec `(x,y)` corrisponda allo stesso `(x,y)` sull'altro livello.

## Strumenti dell'editor (toolbar master)

Strumento selezionabile, poi si clicca sulla cella:

- **Pianeta** — piazza un pianeta; apre il pannello proprietà.
- **Pianeta Base (B)** — come sopra ma con `isBase = true` (unico in tutta la galassia).
- **Buco Nero (B.N.)** — piazza il B.N.; mostra in overlay l'area d'effetto (raggio 4 parsec). Piazzarne uno propaga lo stesso punto su tutti i livelli.
- **R.M.G.** — richiede la selezione di **3 celle contigue** (adiacenti anche in diagonale); evidenzia il footprint mentre si costruisce.
- **D.N.** — piazza una distorsione (1 cella); max 3 per livello.
- **Sposta / Modifica** — seleziona un elemento per spostarlo o editarne le proprietà.
- **Elimina** — rimuove l'elemento selezionato.

Pannello proprietà (a lato) per l'elemento selezionato:
- Pianeta: `letter`, `isBase`, `type`, `radioactivity` (0/α/β, solo external), `atmosphere`, `infoRef`, toggle `discovered`, toggle `cleared`.
- Anomalie: `type`, toggle `hidden` (default true), `effectRadius` (solo B.N.).

## Regole di validazione (mappate al regolamento)

Mostrare in tempo reale un pannello "Validazione" con violazioni bloccanti (❌) e avvisi (⚠️). Distanze in parsec = celle, metrica configurata.

Per ogni **livello**:
1. ❌ Esattamente **9 pianeti** per livello (⚠️ se il master vuole derogare, permetterlo ma segnalarlo).
2. ❌ **Nessuna sovrapposizione**: due pianeti non possono occupare la stessa cella dello stesso livello.
3. ❌ Esattamente **1 R.M.G.** per livello, con footprint di **3 celle contigue**; distanza dal pianeta più vicino **≥ 4 parsec**.
4. ❌ Esattamente **3 D.N.** per livello, ciascuna di 1 cella (nessun vincolo di adiacenza).
5. ❌ Esattamente **1 B.N.** per livello, con distanza dal pianeta più vicino **≥ 5 parsec**; `effectRadius = 4`.

Per l'intera **galassia**:
6. ❌ Esattamente **un solo pianeta base** (`isBase = true`) in tutti i 36 pianeti; contrassegnato **B**.
7. ❌ Il **B.N.** deve avere la **stessa cella** su tutti e 4 i livelli.
8. ⚠️ Totale pianeti = 36 (9 × 4).
9. ℹ️ Tutte le anomalie con `hidden = true` di default (invisibili ai radar).

Utility di calcolo: `distance(a, b)` secondo `distanceMetric`; `nearestPlanetDistance(cell, level)`; `areContiguous(cells)` per R.M.G.

## Viste: Master vs Giocatori

Toggle **Vista Master ↔ Vista Giocatori**:

- **Vista Master:** mostra tutto (pianeti, tipi, anomalie, aree d'effetto, note interne).
- **Vista Giocatori:** nasconde tutte le anomalie (`hidden`) e le proprietà non ancora rivelate; mostra i pianeti solo se `discovered = true`, con accanto solo le informazioni **di dominio pubblico** già date. I pianeti `cleared` sono mostrati **barrati** e non più visitabili.

## Import / Export

- **Export**: serializza la galassia in JSON (schema sopra) e scarica un file (es. `galassia_<data>.json`).
- **Import**: carica un JSON, valida lo schema, ripopola l'editor.
- (Opzionale, solo in repo reale) autosalvataggio in `localStorage` con chiave versionata.

## Aiuti opzionali (nice-to-have, non prioritari)

- Bottone **"Piazzamento assistito"**: genera in modo casuale ma **rispettando tutti i vincoli** (distanze minime, conteggi, non sovrapposizione), lasciando comunque al master la possibilità di ritoccare a mano. Il posizionamento manuale resta la modalità principale.
- **Righello parsec**: al passaggio del mouse mostra la distanza in parsec dalla cella selezionata (utile per verificare i ≥5 / ≥4).
- **Overlay direzioni**: piccola bussola N / NE / E … per interpretare le rotte.

## Criteri di accettazione

- Il master può creare da zero una galassia a 4 livelli, piazzando manualmente pianeti e anomalie con pochi clic.
- I vincoli 1–9 sono verificati in tempo reale; le violazioni bloccanti impediscono l'export "pulito" ma non l'uso in bozza.
- L'area d'effetto del B.N. (raggio 4) e il footprint della R.M.G. (3 celle) sono visualizzati.
- Il toggle Vista Giocatori nasconde correttamente tutte le anomalie e le informazioni non rivelate.
- Export → Import ricostruisce identicamente la galassia.

---

## Prompt pronto per Claude Code

```
Estendi l'interfaccia del gioco "Legio / C.S.C." con una modalità
"Master — Editor Galassia" che permetta al game master (S.C.) di creare
a mano la TABULA SPATII.

Implementa esattamente quanto descritto nella specifica
"Parte II — Editor Galassia" del file regolamento_csc_avanzato_e_editor.md:

- Modello dati JSON come da schema (galassia a 4 livelli in griglia 2×2,
  griglia per livello configurabile, metrica distanze Chebyshev).
- Toolbar per piazzare cliccando: Pianeta, Pianeta Base (B), Buco Nero,
  R.M.G. (3 celle contigue), Distorsione Nullius, più Sposta/Modifica ed Elimina.
- Pannello proprietà per l'elemento selezionato.
- Validazione in tempo reale delle regole 1–9 (conteggi, distanze minime
  B.N. ≥5 e R.M.G. ≥4 parsec dal pianeta più vicino, unico pianeta base,
  B.N. nella stessa cella su tutti i livelli, no sovrapposizioni).
- Overlay: area d'effetto B.N. (raggio 4) e footprint R.M.G.
- Toggle Vista Master ↔ Vista Giocatori (nasconde anomalie e info non rivelate;
  mostra i pianeti barrati se "cleared").
- Export/Import della galassia in JSON. Persistenza su localStorage solo se
  siamo in un repo reale; se è un artifact Claude.ai, niente localStorage:
  stato in memoria + export/import file.

Non cambiare le regole di gioco: implementa solo posizionamento manuale,
proprietà, validazione e viste. Mantieni lo stile/stack del resto del progetto.
```