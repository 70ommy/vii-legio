# Glossario di dominio — VII Legio

## Termini

**S.C. (Spazio Computer)** — il game master umano. Resta sempre un umano che orchestra
la partita (genera/edita la galassia, guarda i tiri, arbitra); le interfacce dei
giocatori si *affiancano* al suo ruolo, non lo sostituiscono.

**Consolle S.C.** — l'interfaccia web esistente (`src/legio/web/`), unica, usata dallo
S.C. per creare la zona, tracciare le rotte di ogni nave, leggere dossier e registro.

**Plancia U.C.** — il toggle già esistente sulla Consolle S.C. che nasconde i sistemi
non ancora avvistati: è un'anteprima di ciò che i giocatori dovrebbero vedere,
proiettata sullo stesso schermo condiviso. **Non** è l'interfaccia personale del
giocatore.

**Terminale di bordo** *(nuovo termine, non ancora implementato)* — la futura interfaccia
personale per singolo U.C., usabile dal proprio telefono: mostra e comanda solo la
propria nave (sostituisce il foglio di carta e penna del giocatore). Distinta dalla
Plancia U.C. per evitare ambiguità di nome.

**Spazio esterno** — modalità di gioco avanzata (già un flag `spazio_esterno` in
`Sessione`) in cui, oltre ai rischi dello spazio interno, si incontrano anomalie non
rilevabili dai radar (B.N., R.M.G., D.N.), radioattività sui pianeti e navi aliene.

**Radioattività** — livello ambientale di un pianeta in spazio esterno: `0` (assente),
`α` (protetta dalla tuta BIMBER), `β` (protetta dalla tuta LEGGY, più invalidante).
Sostituisce il precedente placeholder `NULLA`/`DEBOLE`/`LETALE`, che era un flavor
text ricostruito senza il testo del regolamento avanzato.

**E.** — unità d'equipaggio a bordo di una Nave Legio. Ha un F.C. (Fattore di
Combattimento) base di 3, ridotto dalle tute anti-radio (BIMBER: -1, LEGGY: -2) o
dalla perdita di membri. Numero di E. per nave: **assunzione, non confermata dal
manuale fisico** — vedi tabella "Assunzioni prese" nel README.

**Classe/massa della nave** — attributo scelto dall'U.C. alla creazione della propria
nave, usato nella formula del Buco Nero (`DISTANZA − MASSA − ESITO d6`). Valori:
**assunzione, non confermata dal manuale fisico** — vedi README.

**Princeps Psi** — presenza a bordo, opzionale, che permette a una Nave di percepire
R.M.G. e D.N. altrimenti invisibili. Scelta liberamente dall'U.C. alla creazione della
propria nave, come già avviene per radar/computer/serbatoi.

**Editor Galassia** — la modalità con cui il master costruisce a mano la TABULA invece
di generarla a seme. Non è una vista della Consolle S.C.: è l'altra strada per far
nascere una partita, e le due non si mescolano (vedi Decisioni prese).

**Bozza** — la galassia in costruzione dentro l'Editor, prima che diventi una partita.
Vive sul server, si valida di continuo, si esporta e si importa; all'avvio della partita
si trasforma in Sessione e smette di esistere. Una bozza *non* è una Sessione: non ha
navi, turni né registro.

## Decisioni prese

- **Ordine di lavoro sulle tre estensioni**: (1) regole avanzate spazio esterno →
  (2) editor manuale della galassia per il master → (3) Terminale di bordo per i
  giocatori. Ogni pacchetto si appoggia al precedente (l'editor piazza le anomalie
  del motore di regole; il Terminale di bordo mostra un gioco già completo).
- **Editor Galassia = modalità sostitutiva pura**: quando il master usa l'editor
  manuale, la galassia di quella partita **non** passa dalla generazione a seme
  (`generatore.py`): la crea a mano da zero, pianeti compresi. La generazione a seme
  resta disponibile come modalità alternativa per le partite rapide. Vedi
  `docs/adr/0001-editor-galassia-sostitutivo.md`.
