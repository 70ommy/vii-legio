/* ══════════════════════════════════════════════════════════════════════════
   Pagina d'ingresso: il telefono chiede allo S.C. quali navi ci sono e lascia
   scegliere la propria. L'identita' vive in localStorage (nessun login: e' un
   tavolo di amici), e da qui si "atterra" sul terminale personale in /uc.

   Stessa convenzione del resto del progetto: niente framework, funzioni globali,
   ogni giro di stato passa da una fetch e ridisegna dal risultato del server.
   ══════════════════════════════════════════════════════════════════════════ */

"use strict";

// Chiave condivisa col terminale (/uc): la nave scelta qui e' quella che il
// terminale legge per sapere chi comanda. Un solo posto per non sfasarsi.
const NAVE_KEY = "legio.nave";
const INTERVALLO_MS = 2000;

let navi = [];            // ultimo elenco ricevuto dallo S.C.
let partitaAttiva = false;
let vuoleCambiare = false; // l'U.C. ha toccato "cambia nave": mostra l'elenco anche se gia' registrato

function naveSalvata() {
  try {
    const grezzo = localStorage.getItem(NAVE_KEY);
    return grezzo ? JSON.parse(grezzo) : null;
  } catch (e) {
    return null; // localStorage negato (finestra privata ecc.): si ricomincia dalla scelta
  }
}

function salvaNave(nave) {
  try {
    localStorage.setItem(NAVE_KEY, JSON.stringify({ nome: nave.nome, colore: nave.colore }));
  } catch (e) {
    /* senza storage l'identita' non sopravvive al redirect, ma la partita non si blocca */
  }
}

function prendiPosto(nave) {
  salvaNave(nave);
  location.href = "/uc";
}

// La nave registrata esiste ancora nella partita in corso? (Un nuovo avvio puo'
// avere ufficiali diversi: in quel caso il ricordo e' stantio e si riscegli.)
function naveAncoraInServizio(salvata) {
  return salvata && navi.some((n) => n.nome === salvata.nome);
}

function mostra(idSezione) {
  for (const id of ["sezione-ripresa", "sezione-scelta", "sezione-attesa"]) {
    document.getElementById(id).hidden = id !== idSezione;
  }
}

function disegna() {
  const salvata = naveSalvata();

  if (!partitaAttiva) {
    mostra("sezione-attesa");
    return;
  }
  if (naveAncoraInServizio(salvata) && !vuoleCambiare) {
    disegnaRipresa(salvata);
    mostra("sezione-ripresa");
    return;
  }
  disegnaElenco();
  mostra("sezione-scelta");
}

function disegnaRipresa(salvata) {
  const riquadro = document.getElementById("ripresa-nave");
  riquadro.style.setProperty("--colore-nave", salvata.colore || "");
  riquadro.innerHTML = "";
  const gemma = document.createElement("span");
  gemma.className = "gemma";
  const nome = document.createElement("span");
  nome.textContent = salvata.nome;
  riquadro.append(gemma, nome);
}

function disegnaElenco() {
  const elenco = document.getElementById("elenco-navi");
  elenco.innerHTML = "";
  for (const nave of navi) {
    const carta = document.createElement("button");
    carta.type = "button";
    carta.className = "carta-nave";
    carta.setAttribute("role", "listitem");
    carta.style.setProperty("--colore-nave", nave.colore || "");

    const gemma = document.createElement("span");
    gemma.className = "gemma";
    const nome = document.createElement("span");
    nome.className = "nome-nave";
    nome.textContent = nave.nome;
    const freccia = document.createElement("span");
    freccia.className = "freccia";
    freccia.textContent = "➤";

    carta.append(gemma, nome, freccia);
    carta.addEventListener("click", () => prendiPosto(nave));
    elenco.appendChild(carta);
  }
}

async function aggiorna() {
  const linea = document.getElementById("linea-stato");
  try {
    const risposta = await fetch("/api/navi", { cache: "no-store" });
    if (!risposta.ok) throw new Error(`stato ${risposta.status}`);
    const dati = await risposta.json();
    partitaAttiva = Boolean(dati.partita_attiva);
    navi = dati.navi || [];
    linea.textContent = "";
    disegna();
  } catch (e) {
    // Il master potrebbe aver spento la cella: non e' un errore fatale, si ritenta.
    linea.textContent = "Nessun contatto con lo Spazio Computer. Nuovo tentativo…";
  }
}

document.getElementById("bottone-entra").addEventListener("click", () => {
  location.href = "/uc";
});
document.getElementById("bottone-cambia").addEventListener("click", () => {
  vuoleCambiare = true;
  disegna();
});

aggiorna();
// Il giocatore apre spesso il telefono prima che il master avvii: si ricontrolla
// da soli finche' la partita compare, senza dover ricaricare la pagina a mano.
setInterval(aggiorna, INTERVALLO_MS);
