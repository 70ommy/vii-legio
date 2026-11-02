/* ══════════════════════════════════════════════════════════════════════════
   Terminale di bordo (/uc): la plancia personale di un U.C.

   Legge l'identita' salvata dall'ingresso (localStorage['legio.nave']), poi fa
   polling di GET /api/stato?vista=uc ogni 2 s. Mostra la propria nave in primo
   piano, la TABULA con la conoscenza della *flotta* (stessa vista dei Comandanti)
   ed evidenzia i sistemi che la propria nave ha avvistato di persona.

   Renderer dedicato, indipendente da app.js (la consolle dello S.C.): stessa
   convenzione — una fetch, si ridisegna dal risultato del server.
   ══════════════════════════════════════════════════════════════════════════ */

"use strict";

const NAVE_KEY = "legio.nave";       // condivisa con l'ingresso
const INTERVALLO_MS = 2000;

const CLASSI_MASSA = { 1: "Leggera", 2: "Media", 3: "Pesante" };
const ETICHETTE_INFO = {
  tipo: "Tipo", codice: "Codice", classe: "Classe", ambiente: "Ambiente",
  radioattivita: "Radioattività", nota_radio: "Nota radio", vita: "Vita",
  sapienza: "Sapienza", terminale: "Terminale", esito_finale: "Esito finale",
  razza: "Razza", rif_gi: "Rif. G.I.",
};

let mioNome = null;        // nome dell'U.C. di questo telefono (maiuscolo, come lo tiene lo S.C.)
let ultimoJson = null;     // per non ridisegnare (e non far saltare lo scroll) se nulla cambia
let selezione = null;      // id del sistema aperto nel dossier, conservato fra un refresh e l'altro

// Matita di pianificazione: appunti PRIVATI su questo telefono (localStorage), non stato di
// gioco. Aiutano a pianificare i turni; nessun altro li vede, non passano dal server.
let schizzoAttivo = false;
let strumentoSchizzo = "tappa";
let abbozzi = {};                       // chiave "liv:x:y" -> {tipo:"tappa"|"segno", ordine?}
let statoCorrente = null;               // ultimi dati disegnati: per ridisegnare la sola TABULA
let miaCorrente = null;                 //   dopo un abbozzo, senza aspettare il polling

function identita() {
  try {
    const grezzo = localStorage.getItem(NAVE_KEY);
    return grezzo ? JSON.parse(grezzo) : null;
  } catch (e) {
    return null;
  }
}

function testo(elemento, valore) {
  document.getElementById(elemento).textContent = valore;
}

// ── ciclo di aggiornamento ──────────────────────────────────────────────── //

async function aggiorna() {
  const linea = document.getElementById("linea-stato");
  try {
    const risposta = await fetch("/api/stato?vista=uc", { cache: "no-store" });
    if (!risposta.ok) throw new Error(`stato ${risposta.status}`);
    const stato = await risposta.json();

    const mia = (stato.navi || []).find((n) => n.nome === mioNome);
    if (!mia) {
      // La nave salvata non e' in questa partita (altri ufficiali, o partita non
      // ancora avviata): si torna a scegliere invece di mostrare una plancia vuota.
      location.replace("/");
      return;
    }

    linea.textContent = "";
    const impronta = JSON.stringify(stato);
    if (impronta === ultimoJson) return; // niente di nuovo: si lascia lo scroll dov'e'
    ultimoJson = impronta;
    disegna(stato, mia);
  } catch (e) {
    linea.textContent = "Nessun contatto con lo Spazio Computer. Nuovo tentativo…";
  }
}

function disegna(stato, mia) {
  statoCorrente = stato;
  miaCorrente = mia;
  document.getElementById("terminale").hidden = false;
  document.title = `${mia.nome} — Terminale di bordo`;
  document.documentElement.style.setProperty("--colore-nave", mia.colore || "");

  testo("mio-nome", mia.nome);
  testo("mio-turno", stato.turno);
  disegnaStatNave(stato, mia);
  disegnaOrdine(stato);
  disegnaTocca(stato);
  disegnaAttesa(mia);
  disegnaTabula(stato, mia);
  disegnaRegistro(stato);
  riapriDossier(stato, mia); // il sistema selezionato puo' essere cambiato di stato
}

// ── dichiarazione di rotta (3D) ─────────────────────────────────────────── //

function disegnaTocca(stato) {
  const p = document.getElementById("tocca");
  const di = stato.turno_di;
  p.classList.toggle("mio", di === mioNome);
  if (!di) p.textContent = "Tutti gli Ufficiali hanno mosso: si attende il prossimo turno.";
  else if (di === mioNome) p.textContent = "Tocca a te.";
  else p.textContent = `Ora tocca a ${di}. Puoi comunque dichiarare: sarà lo S.C. a decidere.`;
}

function disegnaAttesa(mia) {
  const box = document.getElementById("attesa-dichiarazione");
  const d = mia.dichiarazione_in_attesa;
  if (!d) { box.hidden = true; box.innerHTML = ""; return; }
  box.hidden = false;
  box.innerHTML = "";
  const testa = document.createElement("div");
  testa.innerHTML = `In attesa di esecuzione dallo S.C.: <span class="rotta-attesa">${d.rotta}</span>`
    + (d.atterraggio ? " · ATTERRAGGIO" : "");
  const annulla = document.createElement("button");
  annulla.className = "mini-bottone";
  annulla.type = "button";
  annulla.textContent = "Annulla dichiarazione";
  annulla.addEventListener("click", annullaDichiarazione);
  box.append(testa, annulla);
}

async function invia(percorso, corpo) {
  const r = await fetch(percorso, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(corpo),
  });
  const dati = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(dati.errore || `errore ${r.status}`);
  return dati;
}

function numero(id, predefinito) {
  const v = parseInt(document.getElementById(id).value, 10);
  return Number.isFinite(v) ? v : predefinito;
}

async function dichiara() {
  const linea = document.getElementById("linea-stato");
  const rotta = document.getElementById("c-rotta").value.trim();
  if (!rotta) { linea.textContent = "Scrivi una rotta prima di dichiarare."; return; }
  try {
    await invia("/api/dichiarazione", {
      nave: mioNome, vista: "uc", rotta,
      serbatoi: numero("c-serbatoi", 3),
      radar: numero("c-radar", 3),
      computer: numero("c-computer", 2),
      atterraggio: document.getElementById("c-atterraggio").checked,
    });
    linea.textContent = "";
    ultimoJson = null;   // forza il ridisegno: compare il riquadro d'attesa
    await aggiorna();
  } catch (e) {
    linea.textContent = e.message;
  }
}

async function annullaDichiarazione() {
  const linea = document.getElementById("linea-stato");
  try {
    await invia("/api/dichiarazione/annulla", { nave: mioNome, vista: "uc" });
    ultimoJson = null;
    await aggiorna();
  } catch (e) {
    linea.textContent = e.message;
  }
}

// ── quadro della propria nave ───────────────────────────────────────────── //

function disegnaStatNave(stato, mia) {
  const siglaBase = mappaIdSigla(stato.galassia);
  const aTerra = mia.a_terra ? `A terra · ${siglaBase[mia.a_terra] || mia.a_terra}` : "In volo";
  const voci = [
    ["Posizione", mia.posizione.riferimento, false],
    ["Stato", aTerra, true],
    ["Punti", mia.punti, false],
    ["Informazioni residue", mia.informazioni_residue, false],
    ["Serbatoi", mia.serbatoi, false],
    ["Radar", mia.radar, false],
    ["Computer", mia.computer, false],
  ];
  if (stato.spazio_esterno) {
    voci.push(["Classe/massa", CLASSI_MASSA[mia.classe_massa] || mia.classe_massa, true]);
    voci.push(["Princeps Psi", mia.princeps_psi ? "Sì" : "No", true]);
  }

  const dl = document.getElementById("mie-stat");
  dl.innerHTML = "";
  for (const [etichetta, valore, piccolo] of voci) {
    const blocco = document.createElement("div");
    blocco.className = "stat";
    const dt = document.createElement("dt");
    dt.textContent = etichetta;
    const dd = document.createElement("dd");
    dd.textContent = valore;
    if (piccolo) dd.classList.add("piccolo");
    blocco.append(dt, dd);
    dl.appendChild(blocco);
  }
}

function disegnaOrdine(stato) {
  const riga = document.getElementById("ordine-turno");
  const ordine = stato.ordine_turno || [];
  if (!ordine.length) { riga.textContent = ""; return; }
  riga.innerHTML = "Ordine di gioco: ";
  ordine.forEach((nome, i) => {
    const s = document.createElement("span");
    s.textContent = nome;
    if (nome === mioNome) s.className = "io";
    riga.appendChild(s);
    if (i < ordine.length - 1) riga.appendChild(document.createTextNode(" → "));
  });
}

// ── TABULA a settori ────────────────────────────────────────────────────── //

function mappaIdSigla(galassia) {
  const m = {};
  for (const p of galassia.pianeti) m[p.id] = p.sigla;
  return m;
}

function disegnaTabula(stato, mia) {
  const galassia = stato.galassia;
  const lato = galassia.lato;
  const lettere = galassia.lettere;

  // Sistemi noti e gettoni nave, indicizzati per cella.
  const perCella = {};
  for (const p of galassia.pianeti) perCella[`${p.livello}:${p.x}:${p.y}`] = p;
  const naviCella = {};
  for (const nave of stato.navi) {
    const pos = nave.posizione;
    const chiave = `${pos.livello}:${pos.x}:${pos.y}`;
    (naviCella[chiave] || (naviCella[chiave] = [])).push(nave);
  }

  const contenitore = document.getElementById("tabula");
  contenitore.innerHTML = "";

  for (let liv = 0; liv < galassia.livelli; liv++) {
    const settore = document.createElement("section");
    settore.className = "settore";
    const titolo = document.createElement("h3");
    titolo.textContent = `Settore ${galassia.nomi_livello[liv]}`;
    settore.appendChild(titolo);

    const scorri = document.createElement("div");
    scorri.className = "scorri-tabula";
    const griglia = document.createElement("div");
    griglia.className = "griglia-tabula";
    // prima colonna per i numeri di riga, poi una per parsec
    griglia.style.gridTemplateColumns = `auto repeat(${lato}, 26px)`;

    // intestazione: angolo vuoto + lettere di colonna
    griglia.appendChild(cellaAsse(""));
    for (let x = 0; x < lato; x++) griglia.appendChild(cellaAsse(lettere[x]));

    for (let y = 0; y < lato; y++) {
      griglia.appendChild(cellaAsse(String(y + 1)));
      for (let x = 0; x < lato; x++) {
        griglia.appendChild(cellaTabula(liv, x, y, perCella, naviCella, mia));
      }
    }
    scorri.appendChild(griglia);
    settore.appendChild(scorri);
    contenitore.appendChild(settore);
  }
}

function cellaAsse(testo) {
  const c = document.createElement("div");
  c.className = "cella cella-asse";
  c.textContent = testo;
  return c;
}

function cellaTabula(liv, x, y, perCella, naviCella, mia) {
  const cella = document.createElement("div");
  cella.className = "cella cella-giocabile";
  const pianeta = perCella[`${liv}:${x}:${y}`];

  if (pianeta) {
    cella.classList.add("cella-pianeta");
    if (pianeta.base) { cella.classList.add("pianeta-base"); cella.textContent = "B"; }
    else if (pianeta.livelli_noti && pianeta.livelli_noti.length) { cella.classList.add("pianeta-noto"); cella.textContent = "●"; }
    else if (pianeta.barrato) { cella.classList.add("pianeta-barrato"); cella.textContent = "╳"; }
    else { cella.classList.add("pianeta-noto"); cella.textContent = "○"; }

    if ((pianeta.avvistato_da || []).includes(mioNome)) cella.classList.add("mia-scoperta");
    if (pianeta.id === selezione) cella.classList.add("selezionata");
  }

  // Appunto personale (privato): un contrassegno d'angolo, sopra a qualunque pianeta.
  const ab = abbozzi[`${liv}:${x}:${y}`];
  if (ab) {
    const badge = document.createElement("span");
    badge.className = "abbozzo abbozzo-" + ab.tipo;
    badge.textContent = ab.tipo === "tappa" ? String(ab.ordine) : "⚑";
    cella.appendChild(badge);
  }

  const navi = naviCella[`${liv}:${x}:${y}`];
  if (navi && navi.length) {
    const gettoni = document.createElement("div");
    gettoni.className = "gettoni";
    for (const nave of navi) {
      const g = document.createElement("span");
      g.className = "gettone" + (nave.nome === mioNome ? " mio" : "");
      g.style.setProperty("--c", nave.colore || "");
      g.title = nave.nome;
      gettoni.appendChild(g);
    }
    cella.appendChild(gettoni);
  }

  // Un solo gestore: con la matita si abbozza, altrimenti si apre il dossier del pianeta.
  cella.addEventListener("click", () => {
    if (schizzoAttivo) { schizzaCella(liv, x, y); return; }
    if (pianeta) { selezione = pianeta.id; riapriDossierDa(pianeta); segnaSelezione(); cella.classList.add("selezionata"); }
  });
  return cella;
}

function segnaSelezione() {
  for (const c of document.querySelectorAll(".cella.selezionata")) c.classList.remove("selezionata");
  // la cella selezionata viene ridisegnata al prossimo refresh; qui basta il dossier
}

// ── matita di pianificazione (appunti privati sulla propria mappa) ───────── //

function chiaveAbbozzi() { return "legio.abbozzi." + mioNome; }

function caricaAbbozzi() {
  try { abbozzi = JSON.parse(localStorage.getItem(chiaveAbbozzi()) || "{}") || {}; }
  catch (e) { abbozzi = {}; }
}

function salvaAbbozzi() {
  try { localStorage.setItem(chiaveAbbozzi(), JSON.stringify(abbozzi)); }
  catch (e) { /* privato e non essenziale: se lo storage e' pieno o bloccato, pazienza */ }
}

function prossimoNumero() {
  let massimo = 0;
  for (const a of Object.values(abbozzi)) if (a.tipo === "tappa" && a.ordine > massimo) massimo = a.ordine;
  return massimo + 1;
}

function rinumeraTappe() {
  // Le tappe restano una sequenza contigua 1..n nell'ordine in cui erano numerate.
  Object.entries(abbozzi)
    .filter(([, a]) => a.tipo === "tappa")
    .sort((u, v) => u[1].ordine - v[1].ordine)
    .forEach(([k], i) => { abbozzi[k].ordine = i + 1; });
}

function schizzaCella(liv, x, y) {
  const k = `${liv}:${x}:${y}`;
  const esistente = abbozzi[k];
  if (strumentoSchizzo === "gomma") {
    if (esistente) { delete abbozzi[k]; if (esistente.tipo === "tappa") rinumeraTappe(); }
  } else if (strumentoSchizzo === "segno") {
    if (esistente && esistente.tipo === "segno") delete abbozzi[k];
    else { const eraTappa = esistente && esistente.tipo === "tappa"; abbozzi[k] = { tipo: "segno" }; if (eraTappa) rinumeraTappe(); }
  } else { // tappa
    if (esistente && esistente.tipo === "tappa") { delete abbozzi[k]; rinumeraTappe(); }
    else abbozzi[k] = { tipo: "tappa", ordine: prossimoNumero() };
  }
  salvaAbbozzi();
  if (statoCorrente) disegnaTabula(statoCorrente, miaCorrente);
}

function pulisciAbbozzi() {
  if (!Object.keys(abbozzi).length) return;
  abbozzi = {};
  salvaAbbozzi();
  if (statoCorrente) disegnaTabula(statoCorrente, miaCorrente);
}

// ── dossier del sistema selezionato ─────────────────────────────────────── //

function riapriDossier(stato) {
  if (!selezione) return;
  const pianeta = stato.galassia.pianeti.find((p) => p.id === selezione);
  if (pianeta) riapriDossierDa(pianeta);
  else { selezione = null; document.getElementById("dossier").hidden = true; }
}

function riapriDossierDa(pianeta) {
  const dossier = document.getElementById("dossier");
  const corpo = document.getElementById("dossier-corpo");
  corpo.innerHTML = "";

  const testa = document.createElement("div");
  testa.className = "intestazione-dossier";
  const sigla = document.createElement("span");
  sigla.className = "sigla-dossier";
  sigla.textContent = pianeta.sigla;
  testa.appendChild(sigla);
  if (pianeta.base) testa.appendChild(pastiglia("Base", "pastiglia-base"));
  if (pianeta.barrato) testa.appendChild(pastiglia("Barrato", "pastiglia-barrato"));
  if ((pianeta.avvistato_da || []).includes(mioNome)) testa.appendChild(pastiglia("Avvistato da te", "pastiglia-mia"));
  corpo.appendChild(testa);

  const dl = document.createElement("dl");
  const noti = pianeta.livelli_noti || [];
  if (noti.length) aggiungiRiga(dl, "Livelli noti", noti.join(" · "));
  for (const [chiave, etichetta] of Object.entries(ETICHETTE_INFO)) {
    if (chiave in pianeta.informazioni) {
      let v = pianeta.informazioni[chiave];
      if (typeof v === "boolean") v = v ? "Sì" : "No";
      aggiungiRiga(dl, etichetta, v);
    }
  }
  if (pianeta.alieni_presenti != null) aggiungiRiga(dl, "Alieni presenti", pianeta.alieni_presenti);

  if (!dl.children.length) {
    const vuoto = document.createElement("p");
    vuoto.className = "vuoto";
    vuoto.textContent = pianeta.base
      ? "Pianeta base della Legio: casa, sempre visitabile."
      : "Nessuna notizia raccolta su questo sistema.";
    corpo.appendChild(vuoto);
  } else {
    corpo.appendChild(dl);
  }
  dossier.hidden = false;
}

function aggiungiRiga(dl, etichetta, valore) {
  const riga = document.createElement("div");
  riga.className = "riga-info";
  const dt = document.createElement("dt");
  dt.textContent = etichetta;
  const dd = document.createElement("dd");
  dd.textContent = valore;
  riga.append(dt, dd);
  dl.appendChild(riga);
}

function pastiglia(testo, classe) {
  const s = document.createElement("span");
  s.className = "pastiglia " + classe;
  s.textContent = testo;
  return s;
}

// ── registro pubblico ───────────────────────────────────────────────────── //

function disegnaRegistro(stato) {
  const ol = document.getElementById("registro");
  ol.innerHTML = "";
  const voci = (stato.registro || []).slice(-50).reverse(); // le piu' recenti in alto
  if (!voci.length) {
    const vuoto = document.createElement("li");
    vuoto.className = "vuoto";
    vuoto.textContent = "Nessuna comunicazione dallo S.C.";
    ol.appendChild(vuoto);
    return;
  }
  for (const voce of voci) {
    const li = document.createElement("li");
    li.className = "tipo-" + (voce.tipo || "sistema");
    const attore = document.createElement("span");
    attore.className = "attore";
    attore.textContent = `T${voce.turno} · ${voce.attore}`;
    const corpo = document.createElement("div");
    corpo.textContent = voce.testo;
    li.append(attore, corpo);
    ol.appendChild(li);
  }
}

// ── avvio ───────────────────────────────────────────────────────────────── //

const io = identita();
if (!io || !io.nome) {
  location.replace("/");
} else {
  mioNome = io.nome;
  caricaAbbozzi();
  document.getElementById("chiudi-dossier").addEventListener("click", () => {
    selezione = null;
    document.getElementById("dossier").hidden = true;
  });
  document.getElementById("c-dichiara").addEventListener("click", dichiara);

  const bottoneModo = document.getElementById("modo-schizzo");
  bottoneModo.addEventListener("click", () => {
    schizzoAttivo = !schizzoAttivo;
    bottoneModo.classList.toggle("attivo", schizzoAttivo);
    bottoneModo.setAttribute("aria-pressed", String(schizzoAttivo));
    document.getElementById("tavolozza-schizzo").hidden = !schizzoAttivo;
    document.getElementById("nota-schizzo").hidden = !schizzoAttivo;
    document.getElementById("tabula").classList.toggle("schizzo", schizzoAttivo);
  });
  document.querySelectorAll("#tavolozza-schizzo [data-schizzo]").forEach((b) => {
    b.addEventListener("click", () => {
      strumentoSchizzo = b.dataset.schizzo;
      document.querySelectorAll("#tavolozza-schizzo [data-schizzo]").forEach((x) => x.classList.toggle("attivo", x === b));
    });
  });
  document.getElementById("pulisci-schizzo").addEventListener("click", pulisciAbbozzi);

  aggiorna();
  setInterval(aggiorna, INTERVALLO_MS);
}
