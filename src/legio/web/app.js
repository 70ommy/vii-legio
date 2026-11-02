/* ═══════════════════════════════════════════════════════════════════════════
   Consolle dello Spazio Computer. Disegna la TABULA SPATII e parla col terminale.
   ═══════════════════════════════════════════════════════════════════════════ */

const $ = (selettore) => document.querySelector(selettore);
const esc = (testo) => String(testo ?? '').replace(/[&<>"]/g, (c) => (
  { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]
));

const stato = {
  dati: null,
  vistaMappa: 'settori',
  selezione: null,
  tabelle: null,
  modoCreazione: 'seme',
  editor: {
    attivo: false,
    strumento: null,
    rmgBuffer: [],
    bozza: null,
    validazione: null,
    selezione: null,
  },
};

const CELLA_SETTORI = 22;
const CELLA_STEREO = 20;
const ISO_X = 0.87;   // schiacciamento orizzontale della proiezione
const ISO_Y = 0.28;   // schiacciamento verticale: piani sottili, impilabili
const MARGINE_SX = 19;
const MARGINE_SU = 32;
const DIVARIO_SETTORI = 28;

/* ───────────────────────────── terminale ───────────────────────────── */

async function chiama(percorso, corpo) {
  const opzioni = corpo === undefined
    ? {}
    : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(corpo) };
  const risposta = await fetch(percorso, opzioni);
  const dati = await risposta.json();
  if (!risposta.ok) throw new Error(dati.errore || `guasto del terminale (${risposta.status})`);
  return dati;
}

let temporizzatoreAvviso = null;
function avvisa(testo, tipo = 'errore') {
  const nodo = $('#avviso');
  nodo.textContent = testo;
  nodo.classList.toggle('esito', tipo === 'esito');
  nodo.classList.add('visibile');
  clearTimeout(temporizzatoreAvviso);
  temporizzatoreAvviso = setTimeout(() => nodo.classList.remove('visibile'), tipo === 'esito' ? 4200 : 8000);
}

/* ───────────────────────────── frasario ───────────────────────────── */

const GRADI = ['I', 'I-bis', 'II', 'III', 'IV'];

function fraseInfo(livello, i) {
  switch (livello) {
    case 'I': return `Pianeta ${i.tipo} (${i.codice}) — ${i.classe}. ${i.ambiente}`;
    case 'I-bis': return `Radioattività ${i.radioattivita}. ${i.nota_radio}`;
    case 'II': return `Si dichiarano forme di vita ${i.vita}.`;
    case 'III': return i.terminale ? (i.esito_finale || 'Pianeta deserto.') : `Si dichiarano ${i.sapienza}.`;
    case 'IV': return `Razza: ${i.razza} — riferimento G.I. n. ${i.rif_gi}.`;
    default: return '';
  }
}

/* ───────────────────────────── disegno: quattro settori ───────────────────────────── */

function larghezzaSettore(lato) { return MARGINE_SX + lato * CELLA_SETTORI + 10; }
function altezzaSettore(lato) { return MARGINE_SU + lato * CELLA_SETTORI + 16; }

function originaSettore(livello, lato) {
  const colonna = livello % 2;
  const riga = Math.floor(livello / 2);
  return {
    ox: colonna * (larghezzaSettore(lato) + DIVARIO_SETTORI),
    oy: riga * (altezzaSettore(lato) + DIVARIO_SETTORI),
  };
}

function centroCella(livello, x, y, lato) {
  const { ox, oy } = originaSettore(livello, lato);
  return {
    cx: ox + MARGINE_SX + x * CELLA_SETTORI + CELLA_SETTORI / 2,
    cy: oy + MARGINE_SU + y * CELLA_SETTORI + CELLA_SETTORI / 2,
  };
}

function disegnaGrigliaLivelli(g) {
  const lato = g.lato;
  const pezzi = [];
  for (let livello = 0; livello < 4; livello += 1) {
    const { ox, oy } = originaSettore(livello, lato);
    const x0 = ox + MARGINE_SX;
    const y0 = oy + MARGINE_SU;
    const dim = lato * CELLA_SETTORI;

    pezzi.push(`<g>`);
    pezzi.push(`<rect class="fondo-settore" x="${x0}" y="${y0}" width="${dim}" height="${dim}"/>`);
    for (let k = 0; k <= lato; k += 1) {
      const forte = k % 4 === 0 ? ' reticolo-forte' : '';
      pezzi.push(`<line class="reticolo${forte}" x1="${x0 + k * CELLA_SETTORI}" y1="${y0}" x2="${x0 + k * CELLA_SETTORI}" y2="${y0 + dim}"/>`);
      pezzi.push(`<line class="reticolo${forte}" x1="${x0}" y1="${y0 + k * CELLA_SETTORI}" x2="${x0 + dim}" y2="${y0 + k * CELLA_SETTORI}"/>`);
    }
    pezzi.push(`<rect class="cornice-settore" x="${x0}" y="${y0}" width="${dim}" height="${dim}"/>`);
    pezzi.push(`<text class="etichetta-settore" x="${x0}" y="${oy + 12}">SETTORE ${esc(g.nomi_livello[livello])}</text>`);

    for (let x = 0; x < lato; x += 1) {
      pezzi.push(`<text class="coordinata" x="${x0 + x * CELLA_SETTORI + CELLA_SETTORI / 2}" y="${y0 - 5}" text-anchor="middle">${g.lettere[x]}</text>`);
    }
    for (let y = 0; y < lato; y += 1) {
      pezzi.push(`<text class="coordinata" x="${x0 - 4}" y="${y0 + y * CELLA_SETTORI + CELLA_SETTORI / 2 + 3}" text-anchor="end">${y + 1}</text>`);
    }
    pezzi.push(`</g>`);
  }
  return pezzi;
}

function disegnaSettori(dati) {
  const g = dati.galassia;
  const lato = g.lato;
  const largo = larghezzaSettore(lato) * 2 + DIVARIO_SETTORI;
  const alto = altezzaSettore(lato) * 2 + DIVARIO_SETTORI;
  const pezzi = disegnaGrigliaLivelli(g);

  pezzi.push(disegnaGittate(dati, lato));
  pezzi.push(disegnaRotte(dati, lato));
  pezzi.push(disegnaSistemi(dati, lato));
  pezzi.push(disegnaSegnalini(dati, lato));

  return `<svg viewBox="-6 -4 ${largo + 12} ${alto + 10}" role="img" aria-label="Tabula Spatii">${pezzi.join('')}</svg>`;
}

function disegnaSistemi(dati, lato) {
  return dati.galassia.pianeti.map((p) => {
    const { cx, cy } = centroCella(p.livello, p.x, p.y, lato);
    const scelto = stato.selezione === p.id;
    const parti = [`<g class="sistema" data-pianeta="${esc(p.id)}">`];
    parti.push(`<circle class="alone" cx="${cx}" cy="${cy}" r="10" fill="rgba(255,194,71,.18)"/>`);

    if (p.base) {
      parti.push(`<circle class="anello-base" cx="${cx}" cy="${cy}" r="8.5"/>`);
      parti.push(`<circle class="disco-base" cx="${cx}" cy="${cy}" r="5.2"/>`);
      parti.push(`<text class="lettera-base" x="${cx}" y="${cy + 2.6}" text-anchor="middle">B</text>`);
    } else if (p.noto) {
      parti.push(`<circle class="disco-noto" cx="${cx}" cy="${cy}" r="4.4"/>`);
      parti.push(`<circle cx="${cx}" cy="${cy}" r="7" fill="none" stroke="rgba(72,216,224,.35)" stroke-width=".8"/>`);
    } else {
      parti.push(`<circle class="disco-ignoto" cx="${cx}" cy="${cy}" r="4.2"/>`);
    }

    if (p.barrato) {
      parti.push(`<line class="croce-barrato" x1="${cx - 6}" y1="${cy - 6}" x2="${cx + 6}" y2="${cy + 6}"/>`);
      parti.push(`<line class="croce-barrato" x1="${cx + 6}" y1="${cy - 6}" x2="${cx - 6}" y2="${cy + 6}"/>`);
    }
    if (scelto) parti.push(`<circle class="selezionato" cx="${cx}" cy="${cy}" r="11"/>`);

    const nome = p.informazioni?.tipo ? `${p.informazioni.tipo} (${p.informazioni.codice})` : '';
    parti.push(`<text class="sigla-sistema" x="${cx}" y="${cy + 15}" text-anchor="middle">${esc(p.sigla)}</text>`);
    if (nome) parti.push(`<text class="nome-sistema" x="${cx}" y="${cy + 22.5}" text-anchor="middle">${esc(nome)}</text>`);
    parti.push(`<title>${esc(p.id)} — ${esc(p.base ? 'PIANETA BASE' : (p.informazioni?.razza || nome || 'nessuna notizia'))}</title>`);
    parti.push('</g>');
    return parti.join('');
  }).join('');
}

function disegnaGittate(dati, lato) {
  // La gittata e' un quadrato di raggio pari al numero di radar, ritagliato sul settore.
  return dati.navi.map((n) => {
    if (!n.radar) return '';
    const { ox, oy } = originaSettore(n.posizione.livello, lato);
    const x0 = ox + MARGINE_SX;
    const y0 = oy + MARGINE_SU;
    const sinistra = Math.max(0, n.posizione.x - n.radar);
    const sopra = Math.max(0, n.posizione.y - n.radar);
    const destra = Math.min(lato - 1, n.posizione.x + n.radar);
    const sotto = Math.min(lato - 1, n.posizione.y + n.radar);
    return `<rect class="gittata-radar"
      x="${x0 + sinistra * CELLA_SETTORI}" y="${y0 + sopra * CELLA_SETTORI}"
      width="${(destra - sinistra + 1) * CELLA_SETTORI}" height="${(sotto - sopra + 1) * CELLA_SETTORI}"/>`;
  }).join('');
}

function disegnaRotte(dati, lato) {
  return dati.navi.map((n) => {
    const traccia = n.ultimo_movimento?.traccia;
    if (!traccia || traccia.length < 2) return '';
    const gruppi = [];
    traccia.forEach((passo) => {
      const ultimo = gruppi[gruppi.length - 1];
      if (ultimo && ultimo[0].livello === passo.livello) ultimo.push(passo);
      else gruppi.push([passo]);
    });
    const pezzi = gruppi.map((gruppo) => {
      const punti = gruppo.map((p) => {
        const { cx, cy } = centroCella(p.livello, p.x, p.y, lato);
        return `${cx},${cy}`;
      }).join(' ');
      return `<polyline class="linea-rotta" points="${punti}" stroke="${esc(n.colore)}"/>`;
    });
    traccia.forEach((p) => {
      const { cx, cy } = centroCella(p.livello, p.x, p.y, lato);
      const raggio = p.cambio_livello ? 2.4 : 1.4;
      pezzi.push(`<circle class="punto-rotta" cx="${cx}" cy="${cy}" r="${raggio}" fill="${esc(n.colore)}"/>`);
    });
    return pezzi.join('');
  }).join('');
}

function segnalinoSvg(cx, cy, colore, pieno) {
  const punti = `${cx},${cy - 6} ${cx + 5},${cy + 4.5} ${cx - 5},${cy + 4.5}`;
  return pieno
    ? `<polygon class="segnalino" points="${punti}" fill="${esc(colore)}"/>`
    : `<polygon class="segnalino" points="${punti}" fill="none" stroke="${esc(colore)}" stroke-width="1.4"/>`;
}

function disegnaSegnalini(dati, lato) {
  // Piu' navi sullo stesso parsec (tipico alla partenza dalla base) vanno sfalsate.
  const affollamento = new Map();
  return dati.navi.map((n) => {
    const chiave = `${n.posizione.livello}:${n.posizione.x}:${n.posizione.y}`;
    const ordine = affollamento.get(chiave) || 0;
    affollamento.set(chiave, ordine + 1);
    const sfalsa = ordine * 7;

    const pezzi = [];
    const partenza = n.partenza_movimento;
    if (partenza && (partenza.x !== n.posizione.x || partenza.y !== n.posizione.y || partenza.livello !== n.posizione.livello)) {
      const a = centroCella(partenza.livello, partenza.x, partenza.y, lato);
      pezzi.push(segnalinoSvg(a.cx, a.cy - 2, n.colore, false));
    }
    const b = centroCella(n.posizione.livello, n.posizione.x, n.posizione.y, lato);
    pezzi.push(segnalinoSvg(b.cx + sfalsa, b.cy - 2, n.colore, true));
    pezzi.push(`<text class="nome-segnalino" x="${b.cx + sfalsa + 7}" y="${b.cy - 4}" fill="${esc(n.colore)}">${esc(n.nome.replace('LEGIONARIO ', 'L.'))}</text>`);
    return pezzi.join('');
  }).join('');
}

/* ───────────────────────────── disegno: editor galassia ───────────────────────────── */

function disegnaCelleEditor(g, lato) {
  // Una cella gia' occupata da un pianeta o da un'anomalia non e' piu' piazzabile:
  // il suo click deve arrivare all'elemento che c'e' sopra, non a un rettangolo vuoto.
  const occupate = new Set(g.pianeti.map((p) => `${p.livello}:${p.x}:${p.y}`));
  g.anomalie.forEach((a) => a.celle.forEach((c) => occupate.add(`${c.livello}:${c.x}:${c.y}`)));
  const pezzi = [];
  for (let livello = 0; livello < 4; livello += 1) {
    const { ox, oy } = originaSettore(livello, lato);
    const x0 = ox + MARGINE_SX;
    const y0 = oy + MARGINE_SU;
    for (let x = 0; x < lato; x += 1) {
      for (let y = 0; y < lato; y += 1) {
        if (occupate.has(`${livello}:${x}:${y}`)) continue;
        const scelta = stato.editor.rmgBuffer.some((c) => c.livello === livello && c.x === x && c.y === y);
        pezzi.push(`<rect class="editor-cella${scelta ? ' editor-cella-scelta' : ''}" data-editor-cella="1"
          x="${x0 + x * CELLA_SETTORI}" y="${y0 + y * CELLA_SETTORI}" width="${CELLA_SETTORI}" height="${CELLA_SETTORI}"
          data-livello="${livello}" data-x="${x}" data-y="${y}"/>`);
      }
    }
  }
  return pezzi.join('');
}

function disegnaAnomalieEditor(g, lato) {
  const pezzi = [];
  g.anomalie.forEach((a) => {
    a.celle.forEach((cella) => {
      const { cx, cy } = centroCella(cella.livello, cella.x, cella.y, lato);
      pezzi.push(`<g class="anomalia anomalia-${esc(a.tipo.toLowerCase())}" data-anomalia="${esc(a.id)}">`);
      if (a.tipo === 'BN' && a.raggio_effetto) {
        pezzi.push(`<circle class="anteprima-bn" cx="${cx}" cy="${cy}" r="${a.raggio_effetto * CELLA_SETTORI}"/>`);
      }
      // Bersaglio di click esteso a tutta la cella: il solo pittogramma da 6.5px
      // costringerebbe a centrare il colpo per selezionare o eliminare l'anomalia.
      pezzi.push(`<rect class="area-anomalia" x="${cx - CELLA_SETTORI / 2}" y="${cy - CELLA_SETTORI / 2}" width="${CELLA_SETTORI}" height="${CELLA_SETTORI}"/>`);
      pezzi.push(`<circle class="segno-anomalia" cx="${cx}" cy="${cy}" r="6.5"/>`);
      pezzi.push(`<text class="sigla-anomalia" x="${cx}" y="${cy + 3}" text-anchor="middle">${esc(a.tipo)}</text>`);
      pezzi.push(`<title>${esc(a.id)}</title>`);
      pezzi.push('</g>');
    });
    if (a.tipo === 'RMG' && a.celle.length > 1) {
      const punti = a.celle.map((c) => { const p = centroCella(c.livello, c.x, c.y, lato); return `${p.cx},${p.cy}`; }).join(' ');
      pezzi.push(`<polyline class="anteprima-rmg" points="${punti}"/>`);
    }
  });
  return pezzi.join('');
}

function disegnaPianetiEditor(g, lato) {
  return g.pianeti.map((p) => {
    const { cx, cy } = centroCella(p.livello, p.x, p.y, lato);
    const sel = stato.editor.selezione;
    const scelto = sel && sel.genere === 'pianeta' && sel.livello === p.livello && sel.x === p.x && sel.y === p.y;
    const pezzi = [`<g class="sistema" data-editor-pianeta="${p.livello}:${p.x}:${p.y}">`];
    pezzi.push(`<circle class="alone" cx="${cx}" cy="${cy}" r="10" fill="rgba(255,194,71,.18)"/>`);
    if (p.base) {
      pezzi.push(`<circle class="anello-base" cx="${cx}" cy="${cy}" r="8.5"/>`);
      pezzi.push(`<circle class="disco-base" cx="${cx}" cy="${cy}" r="5.2"/>`);
      pezzi.push(`<text class="lettera-base" x="${cx}" y="${cy + 2.6}" text-anchor="middle">B</text>`);
    } else {
      pezzi.push(`<circle class="disco-ignoto" cx="${cx}" cy="${cy}" r="4.2"/>`);
    }
    if (scelto) pezzi.push(`<circle class="selezionato" cx="${cx}" cy="${cy}" r="11"/>`);
    const nome = p.informazioni?.tipo ? `${p.informazioni.tipo} (${p.informazioni.codice || ''})` : '';
    pezzi.push(`<text class="sigla-sistema" x="${cx}" y="${cy + 15}" text-anchor="middle">${esc(p.sigla)}</text>`);
    if (nome) pezzi.push(`<text class="nome-sistema" x="${cx}" y="${cy + 22.5}" text-anchor="middle">${esc(nome)}</text>`);
    pezzi.push('</g>');
    return pezzi.join('');
  }).join('');
}

function anteprimaUc() {
  return $('#campo-vista-uc').checked;
}

function costruisciSvgEditor(g) {
  const lato = g.lato;
  const largo = larghezzaSettore(lato) * 2 + DIVARIO_SETTORI;
  const alto = altezzaSettore(lato) * 2 + DIVARIO_SETTORI;
  const pezzi = disegnaGrigliaLivelli(g);
  // Nell'anteprima della plancia U.C. non si piazza nulla: e' la vista dei giocatori,
  // non un piano di lavoro. Senza celle cliccabili l'errore diventa impossibile.
  if (!anteprimaUc()) pezzi.push(disegnaCelleEditor(g, lato));
  pezzi.push(disegnaAnomalieEditor(g, lato));
  pezzi.push(disegnaPianetiEditor(g, lato));
  return `<svg viewBox="-6 -4 ${largo + 12} ${alto + 10}" role="img" aria-label="Editor Tabula Spatii">${pezzi.join('')}</svg>`;
}

function disegnaEditorTela() {
  if (!stato.editor.bozza) {
    $('#tela').innerHTML = '';
  } else if (stato.vistaMappa === 'stereoscopio') {
    // Lo stereoscopio non ha una griglia di celle su cui piazzare: e' una verifica
    // a sola lettura di come i 4 livelli si impilano (utile soprattutto per il B.N.).
    $('#tela').innerHTML = disegnaStereoscopio({ galassia: stato.editor.bozza, navi: [] });
  } else {
    $('#tela').innerHTML = costruisciSvgEditor(stato.editor.bozza);
  }
  aggiornaValidazioneEditor(stato.editor.validazione);
  aggiornaIstruzioneEditor();
  // Il pannello proprieta' segue sempre la bozza: se il pianeta selezionato non
  // esiste piu' (eliminato, o bozza ricaricata) la scheda va chiusa, non lasciata li'.
  const sel = stato.editor.selezione;
  const pianeta = sel && stato.editor.bozza
    ? stato.editor.bozza.pianeti.find((p) => p.livello === sel.livello && p.x === sel.x && p.y === sel.y)
    : null;
  if (!pianeta) stato.editor.selezione = null;
  aggiornaProprietaEditor(pianeta);
}

function aggiornaValidazioneEditor(validazione) {
  const lista = $('#validazione-editor');
  if (!validazione) { lista.innerHTML = ''; return; }
  const voci = [
    ...validazione.errori.map((v) => ({ ...v, classe: 'validazione-errore', segno: '❌' })),
    ...validazione.avvisi.map((v) => ({ ...v, classe: 'validazione-avviso', segno: '⚠️' })),
    ...validazione.info.map((v) => ({ ...v, classe: 'validazione-info', segno: 'ℹ️' })),
  ];
  lista.innerHTML = voci.length
    ? voci.map((v) => `<li class="riga-validazione ${v.classe}">${v.segno} ${esc(v.messaggio)}</li>`).join('')
    : '<li class="vuoto">Nessuna bozza in costruzione.</li>';
}

function aggiornaIstruzioneEditor() {
  const testi = {
    pianeta: 'Clicca una cella libera per piazzare un pianeta.',
    base: 'Clicca una cella libera per piazzare il pianeta base (rimpiazza quella precedente).',
    bn: 'Clicca una cella: il Buco Nero viene propagato automaticamente sui 4 livelli.',
    rmg: `Clicca 3 celle contigue sullo stesso livello (selezionate finora: ${stato.editor.rmgBuffer.length}/3).`,
    dn: 'Clicca una cella per piazzare una Distorsione Nullius.',
    elimina: "Clicca un pianeta o un'anomalia per eliminarli.",
  };
  let testo;
  if (anteprimaUc()) {
    testo = 'Anteprima Plancia U.C.: ecco cosa vedranno i giocatori. Per modificare, togli la spunta.';
  } else if (stato.vistaMappa === 'stereoscopio') {
    testo = 'Lo stereoscopio è di sola lettura: torna a "Quattro settori" per piazzare.';
  } else {
    testo = stato.editor.strumento
      ? (testi[stato.editor.strumento] || '')
      : 'Seleziona uno strumento della barra qui sopra.';
  }
  $('#istruzione-editor').textContent = testo;
}

function aggiornaProprietaEditor(pianeta) {
  const nodo = $('#proprieta-editor');
  if (!pianeta) { nodo.hidden = true; nodo.innerHTML = ''; return; }
  nodo.hidden = false;
  nodo.innerHTML = `
    <p class="nota-pannello">Pianeta in ${esc(pianeta.sigla)}, livello ${pianeta.livello + 1}.</p>
    <label class="interruttore compatto">
      <input type="checkbox" id="editor-prop-base" ${pianeta.base ? 'checked' : ''}>
      <span class="leva"></span>
      <span class="etichetta-leva">Pianeta Base</span>
    </label>
    <label class="campo">
      <span>Tipo</span>
      <input id="editor-prop-tipo" type="text" value="${esc(pianeta.informazioni?.tipo || '')}">
    </label>
    <label class="campo">
      <span>Codice</span>
      <input id="editor-prop-codice" type="text" value="${esc(pianeta.informazioni?.codice || '')}">
    </label>
    <div class="fila-bottoni">
      <button id="editor-prop-salva" class="bottone bottone-piccolo">Salva</button>
      <button id="editor-prop-elimina" class="bottone bottone-piccolo">Elimina</button>
    </div>`;
  $('#editor-prop-salva').addEventListener('click', async () => {
    try {
      await chiama('/api/editor/pianeta', {
        livello: pianeta.livello, x: pianeta.x, y: pianeta.y,
        base: $('#editor-prop-base').checked,
        tipo: $('#editor-prop-tipo').value.trim(),
        codice: $('#editor-prop-codice').value.trim(),
      });
      await caricaBozzaEditor();
      avvisa('Proprietà del pianeta salvate.', 'esito');
    } catch (errore) { avvisa(errore.message); }
  });
  $('#editor-prop-elimina').addEventListener('click', async () => {
    try {
      await chiama('/api/editor/elimina', { genere: 'pianeta', livello: pianeta.livello, x: pianeta.x, y: pianeta.y });
      stato.editor.selezione = null;
      await caricaBozzaEditor();
    } catch (errore) { avvisa(errore.message); }
  });
}

function selezionaPianetaEditor(livello, x, y) {
  const pianeta = stato.editor.bozza?.pianeti.find((p) => p.livello === livello && p.x === x && p.y === y);
  if (!pianeta) return;
  stato.editor.selezione = { genere: 'pianeta', livello, x, y };
  disegnaEditorTela();
}

async function piazzaSuCella(strumento, livello, x, y) {
  if (!strumento) {
    avvisa('Seleziona prima uno strumento nella barra "Editor manuale".');
    return;
  }
  if (strumento === 'pianeta' || strumento === 'base') {
    await chiama('/api/editor/pianeta', { livello, x, y, base: strumento === 'base' });
    await caricaBozzaEditor();
    selezionaPianetaEditor(livello, x, y);
    return;
  }
  if (strumento === 'bn') {
    await chiama('/api/editor/anomalia', { tipo: 'BN', livello, x, y });
    await caricaBozzaEditor();
    return;
  }
  if (strumento === 'dn') {
    await chiama('/api/editor/anomalia', { tipo: 'DN', livello, x, y });
    await caricaBozzaEditor();
    return;
  }
  if (strumento === 'rmg') {
    stato.editor.rmgBuffer.push({ livello, x, y });
    if (stato.editor.rmgBuffer.length < 3) {
      disegnaEditorTela();
      return;
    }
    const celle = stato.editor.rmgBuffer;
    stato.editor.rmgBuffer = [];
    await chiama('/api/editor/anomalia', { tipo: 'RMG', celle });
    await caricaBozzaEditor();
  }
}

async function gestisciClickEditor(evento) {
  if (anteprimaUc() || stato.vistaMappa === 'stereoscopio') return;  // viste di sola lettura
  const nodoAnomalia = evento.target.closest('[data-anomalia]');
  const nodoPianeta = evento.target.closest('[data-editor-pianeta]');
  const nodoCella = evento.target.closest('[data-editor-cella]');
  const strumento = stato.editor.strumento;
  try {
    if (nodoAnomalia) {
      if (strumento === 'elimina') {
        await chiama('/api/editor/elimina', { genere: 'anomalia', id: nodoAnomalia.dataset.anomalia });
        await caricaBozzaEditor();
      }
      return;
    }
    if (nodoPianeta) {
      const [livello, x, y] = nodoPianeta.dataset.editorPianeta.split(':').map(Number);
      if (strumento === 'elimina') {
        await chiama('/api/editor/elimina', { genere: 'pianeta', livello, x, y });
        stato.editor.selezione = null;
        await caricaBozzaEditor();
      } else {
        selezionaPianetaEditor(livello, x, y);
      }
      return;
    }
    if (nodoCella) {
      await piazzaSuCella(strumento, Number(nodoCella.dataset.livello), Number(nodoCella.dataset.x), Number(nodoCella.dataset.y));
    }
  } catch (errore) { avvisa(errore.message); }
}

async function caricaBozzaEditor() {
  const vista = anteprimaUc() ? 'uc' : 'sc';
  const risposta = await chiama(`/api/editor/stato?vista=${vista}`);
  stato.editor.bozza = risposta.bozza;
  stato.editor.validazione = risposta.validazione;
  disegnaEditorTela();
}

async function nuovaBozza() {
  try {
    await chiama('/api/editor/nuova', { lato: Number($('#campo-editor-lato').value) });
    stato.editor.selezione = null;
    stato.editor.rmgBuffer = [];
    await caricaBozzaEditor();
  } catch (errore) { avvisa(errore.message); }
}

async function esportaBozza() {
  try {
    const dati = await chiama('/api/editor/esporta');
    const url = URL.createObjectURL(new Blob([JSON.stringify(dati, null, 2)], { type: 'application/json' }));
    const collegamento = document.createElement('a');
    collegamento.href = url;
    collegamento.download = `galassia-${dati.seme}.json`;
    collegamento.click();
    URL.revokeObjectURL(url);
  } catch (errore) { avvisa(errore.message); }
}

async function importaBozza(file) {
  try {
    const testo = await file.text();
    await chiama('/api/editor/importa', JSON.parse(testo));
    stato.editor.selezione = null;
    stato.editor.rmgBuffer = [];
    await caricaBozzaEditor();
    avvisa('Bozza importata.', 'esito');
  } catch (errore) { avvisa(errore.message); }
}

function impostaModoCreazione(modo) {
  document.querySelectorAll('[data-modo-creazione]').forEach((b) => {
    b.classList.toggle('attiva', b.dataset.modoCreazione === modo);
  });
  stato.modoCreazione = modo;
  stato.editor.attivo = modo === 'editor';
  $('#campi-seme').hidden = modo !== 'seme';
  $('#pannello-editor').hidden = modo !== 'editor';
  $('#bottone-genera').innerHTML = modo === 'editor'
    ? '<span class="pittogramma">◈</span> Avvia partita con questa galassia'
    : '<span class="pittogramma">◈</span> Genera la zona di galassia';
  if (modo === 'editor') {
    if (!stato.editor.bozza) caricaBozzaEditor();
    else disegnaEditorTela();
  } else {
    aggiornaProprietaEditor(null);
    disegna();  // tornando al seme la tela deve rimostrare la partita in corso
  }
}

/* ───────────────────────────── disegno: stereoscopio ───────────────────────────── */

function profonditaPiano(lato) { return 2 * (lato - 1) * ISO_Y * CELLA_STEREO; }

function distanzaFraPiani(lato) {
  // I 4 parsec di regolamento, piu' quel tanto che basta perche' i piani non si confondano.
  return 4 * CELLA_STEREO + profonditaPiano(lato) * 0.35;
}

function proiettaStereo(livello, x, y, lato) {
  return {
    px: (x - y) * ISO_X * CELLA_STEREO,
    py: (x + y) * ISO_Y * CELLA_STEREO + livello * distanzaFraPiani(lato),
  };
}

function sistemaStereo(p, lato) {
  const { px, py } = proiettaStereo(p.livello, p.x, p.y, lato);
  const alzata = 9;
  const pezzi = [`<g class="sistema" data-pianeta="${esc(p.id)}">`];
  pezzi.push(`<circle class="alone" cx="${px}" cy="${py - alzata}" r="11" fill="rgba(255,194,71,.18)"/>`);
  pezzi.push(`<ellipse cx="${px}" cy="${py}" rx="3.6" ry="1.6" fill="rgba(0,0,0,.6)"/>`);
  pezzi.push(`<line class="colonna-stereo" x1="${px}" y1="${py}" x2="${px}" y2="${py - alzata}"/>`);
  if (p.base) {
    pezzi.push(`<circle class="anello-base" cx="${px}" cy="${py - alzata}" r="8"/>`);
    pezzi.push(`<circle class="disco-base" cx="${px}" cy="${py - alzata}" r="5"/>`);
    pezzi.push(`<text class="lettera-base" x="${px}" y="${py - alzata + 2.6}" text-anchor="middle">B</text>`);
  } else if (p.noto) {
    pezzi.push(`<circle class="disco-noto" cx="${px}" cy="${py - alzata}" r="4.4"/>`);
  } else {
    pezzi.push(`<circle class="disco-ignoto" cx="${px}" cy="${py - alzata}" r="4"/>`);
  }
  if (p.barrato) {
    pezzi.push(`<line class="croce-barrato" x1="${px - 5.5}" y1="${py - alzata - 5.5}" x2="${px + 5.5}" y2="${py - alzata + 5.5}"/>`);
    pezzi.push(`<line class="croce-barrato" x1="${px + 5.5}" y1="${py - alzata - 5.5}" x2="${px - 5.5}" y2="${py - alzata + 5.5}"/>`);
  }
  if (stato.selezione === p.id) pezzi.push(`<circle class="selezionato" cx="${px}" cy="${py - alzata}" r="12"/>`);
  pezzi.push(`<text class="sigla-sistema" x="${px}" y="${py + 11}" text-anchor="middle">${esc(p.sigla)}</text>`);
  pezzi.push(`<title>${esc(p.id)}</title></g>`);
  return pezzi.join('');
}

function disegnaStereoscopio(dati) {
  const g = dati.galassia;
  const lato = g.lato;
  const pezzi = [];

  // Si disegna un livello per volta, dal piu' alto al piu' basso: cosi' ogni piano
  // copre quello che gli sta dietro e la pila si legge davvero come tridimensionale.
  for (let livello = 0; livello < 4; livello += 1) {
    const angoli = [[0, 0], [lato - 1, 0], [lato - 1, lato - 1], [0, lato - 1]]
      .map(([x, y]) => proiettaStereo(livello, x, y, lato));
    pezzi.push(`<polygon class="piano-stereo" points="${angoli.map((a) => `${a.px},${a.py}`).join(' ')}"/>`);

    for (let k = 0; k < lato; k += 3) {
      const a = proiettaStereo(livello, k, 0, lato); const b = proiettaStereo(livello, k, lato - 1, lato);
      const c = proiettaStereo(livello, 0, k, lato); const d = proiettaStereo(livello, lato - 1, k, lato);
      pezzi.push(`<line class="reticolo" x1="${a.px}" y1="${a.py}" x2="${b.px}" y2="${b.py}"/>`);
      pezzi.push(`<line class="reticolo" x1="${c.px}" y1="${c.py}" x2="${d.px}" y2="${d.py}"/>`);
    }

    const sinistra = proiettaStereo(livello, 0, lato - 1, lato);
    const nome = String(g.nomi_livello[livello]).split('—')[0].trim();
    pezzi.push(`<text class="etichetta-settore" x="${sinistra.px - 16}" y="${sinistra.py + 4}" text-anchor="end">LIVELLO ${esc(nome)}</text>`);

    // tratti di rotta percorsi su questo livello
    dati.navi.forEach((n) => {
      const traccia = n.ultimo_movimento?.traccia;
      if (!traccia || traccia.length < 2) return;
      const punti = traccia.filter((p) => p.livello === livello)
        .map((p) => { const q = proiettaStereo(p.livello, p.x, p.y, lato); return `${q.px},${q.py - 9}`; });
      if (punti.length > 1) {
        pezzi.push(`<polyline class="linea-rotta" points="${punti.join(' ')}" stroke="${esc(n.colore)}"/>`);
      }
    });

    // Le anomalie compaiono solo dove esistono (bozza dell'editor, mai in vista U.C.).
    (g.anomalie || []).forEach((a) => {
      a.celle.filter((c) => c.livello === livello).forEach((c) => {
        const q = proiettaStereo(livello, c.x, c.y, lato);
        pezzi.push(`<g class="anomalia anomalia-${esc(a.tipo.toLowerCase())}">`);
        pezzi.push(`<circle class="segno-anomalia" cx="${q.px}" cy="${q.py - 5}" r="6"/>`);
        pezzi.push(`<text class="sigla-anomalia" x="${q.px}" y="${q.py - 2.6}" text-anchor="middle">${esc(a.tipo)}</text>`);
        pezzi.push(`<title>${esc(a.id)}</title></g>`);
      });
    });

    g.pianeti.filter((p) => p.livello === livello).forEach((p) => pezzi.push(sistemaStereo(p, lato)));

    dati.navi.filter((n) => n.posizione.livello === livello).forEach((n, indice) => {
      const q = proiettaStereo(livello, n.posizione.x, n.posizione.y, lato);
      pezzi.push(segnalinoSvg(q.px + indice * 8, q.py - 15, n.colore, true));
    });
  }

  // I cambi di livello si vedono come segmenti verticali fra un piano e l'altro.
  dati.navi.forEach((n) => {
    const traccia = n.ultimo_movimento?.traccia || [];
    for (let k = 1; k < traccia.length; k += 1) {
      if (!traccia[k].cambio_livello) continue;
      const a = proiettaStereo(traccia[k - 1].livello, traccia[k - 1].x, traccia[k - 1].y, lato);
      const b = proiettaStereo(traccia[k].livello, traccia[k].x, traccia[k].y, lato);
      pezzi.push(`<line class="salto-livello" x1="${a.px}" y1="${a.py - 9}" x2="${b.px}" y2="${b.py - 9}" stroke="${esc(n.colore)}"/>`);
    }
  });

  const meta = (lato - 1) * ISO_X * CELLA_STEREO;
  const alto = 3 * distanzaFraPiani(lato) + profonditaPiano(lato);
  return `<svg viewBox="${-meta - 160} -30 ${2 * meta + 200} ${alto + 60}" role="img" aria-label="Stereoscopio tridimensionale">${pezzi.join('')}</svg>`;
}

/* ───────────────────────────── pannelli ───────────────────────────── */

function aggiornaTesta(dati) {
  $('#lettura-matricola').textContent = dati.galassia.seme;
  $('#lettura-turno').textContent = dati.turno;
  $('#lettura-tiri').textContent = dati.tiri;
}

function aggiornaNavi(dati) {
  const contenitore = $('#elenco-navi');
  const attiva = $('#campo-nave').value;
  contenitore.innerHTML = dati.navi.map((n) => `
    <div class="scheda-nave ${n.nome === attiva ? 'attiva' : ''}" data-nave="${esc(n.nome)}">
      <div class="bandiera-nave" style="background:${esc(n.colore)};color:${esc(n.colore)}"></div>
      <div>
        <div class="nome-nave">${esc(n.nome)}</div>
        <div class="dati-nave">
          S.N. in <b>${esc(n.posizione.riferimento)}</b>${n.a_terra ? ' · <b>al suolo</b>' : ''}<br>
          ${n.serbatoi} serbatoi · ${n.radar} radar · ${n.computer} computer<br>
          informazioni residue: <b>${n.informazioni_residue}</b>
        </div>
      </div>
      <div class="punti-nave">${n.punti}<small>punti</small></div>
    </div>`).join('');

  const selettore = $('#campo-nave');
  const precedente = selettore.value;
  selettore.innerHTML = dati.navi.map((n) => `<option value="${esc(n.nome)}">${esc(n.nome)}</option>`).join('');
  if (dati.navi.some((n) => n.nome === precedente)) selettore.value = precedente;
  $('#nota-ordine').textContent = `Ordine di gioco estratto a sorte: ${dati.ordine_turno.join(' → ')}.`;
}

function aggiornaRegistro(dati) {
  const lista = $('#registro');
  if (!dati.registro.length) {
    lista.innerHTML = '<li class="vuoto">Registro vuoto.</li>';
    return;
  }
  lista.innerHTML = dati.registro.map((v) => `
    <li class="tipo-${esc(v.tipo)}">
      <span class="indice">${v.n}</span>
      <span class="voce"><span class="attore">${esc(v.attore)}:</span> ${esc(v.testo)}</span>
    </li>`).join('');
  lista.scrollTop = lista.scrollHeight;
}

function aggiornaAutonomia() {
  const serbatoi = Number($('#campo-serbatoi').value || 0);
  const per = stato.dati?.parsec_per_serbatoio ?? 5;
  $('#lettura-autonomia').textContent = `${serbatoi * per} parsec`;
}

function aggiornaDossier() {
  const nodo = $('#dossier');
  const pianeta = stato.dati?.galassia.pianeti.find((p) => p.id === stato.selezione);
  if (!pianeta) {
    nodo.innerHTML = '<p class="vuoto">Seleziona un sistema sulla Tabula per aprirne la scheda.</p>';
    return;
  }
  const i = pianeta.informazioni || {};
  const pezzi = [`
    <div class="testata-dossier">
      <h3>${esc(pianeta.base ? 'PIANETA BASE' : (i.tipo ? `${i.tipo} (${i.codice})` : 'SISTEMA IGNOTO'))}</h3>
      <span class="riferimento">${esc(pianeta.id)}</span>
    </div>`];

  if (pianeta.barrato) {
    pezzi.push('<p class="nota-pannello" style="color:var(--corallo)">Barrato sulla Tabula: ormai noto, non più visitabile da nessuno.</p>');
  }

  const righe = (pianeta.livelli_noti || []).map((livello) => `
    <li><span class="grado">${esc(livello)}</span><span>${esc(fraseInfo(livello, i))}</span></li>`);
  if (righe.length) pezzi.push(`<ul class="righe-info">${righe.join('')}</ul>`);
  else if (!pianeta.base) pezzi.push('<p class="nota-pannello">Nessuna notizia negli archivi. Occorre una richiesta di informazione da parte di un U.C. entro il raggio dei radar.</p>');

  if (pianeta.alieni_presenti != null) {
    pezzi.push(`<p class="nota-pannello">TAB. PRESENZE: <strong style="color:var(--ambra)">${pianeta.alieni_presenti}</strong> Alieni rilevati.</p>`);
  }

  const voce = i.rif_gi ? stato.tabelle?.guida?.voci?.[String(i.rif_gi)] : null;
  if (voce) pezzi.push(bloccoGi(voce, i.rif_gi));

  const nave = $('#campo-nave').value;
  const naveDati = stato.dati.navi.find((n) => n.nome === nave);
  const stessoParsec = naveDati && naveDati.posizione.livello === pianeta.livello
    && naveDati.posizione.x === pianeta.x && naveDati.posizione.y === pianeta.y;
  pezzi.push(`
    <div class="fila-azioni">
      <button class="bottone bottone-piccolo" data-azione="informa">Richiedi informazione</button>
      ${stessoParsec ? '<button class="bottone bottone-piccolo" data-azione="atterra">Atterra qui</button>' : ''}
    </div>`);
  nodo.innerHTML = pezzi.join('');
}

function bloccoGi(voce, riferimento) {
  const scheda = voce.scheda || {};
  const tabella = (nome, tab) => {
    if (!tab) return '';
    const celle = Object.entries(tab.esiti).map(([faccia, valore]) => `<tr><td>${esc(faccia)}</td><td>${esc(valore)}</td></tr>`).join('');
    return `<table class="tabella-gi"><tr><th colspan="2">${esc(nome)} — ${esc(tab.dado)}</th></tr>${celle}</table>`;
  };
  const attivita = (scheda.attivita || []).map((a) => `
    <table class="tabella-gi">
      <tr><th colspan="2">${esc(a.nome)} — ${esc(a.dado)}, controllo ${esc(a.controllo)}</th></tr>
      ${Object.entries(a.esiti).map(([faccia, riga]) => `<tr><td>${esc(faccia)}</td><td>${esc(riga.testo)} <em style="color:var(--ambra)">(${riga.punti > 0 ? '+' : ''}${riga.punti})</em></td></tr>`).join('')}
    </table>`).join('');
  return `
    <div class="blocco-gi">
      <span class="genere">G.I. n. ${esc(riferimento)} · ${esc(voce.genere)}</span>
      <h4>${esc(voce.nome)}</h4>
      <p>${esc(voce.descrizione)}</p>
      <p style="color:var(--cromo-cupo)"><strong>Atteggiamento:</strong> ${esc(scheda.atteggiamento || '—')}</p>
      ${tabella('TAB. PRESENZE', scheda.presenze)}
      ${tabella('TAB. ARRIVI', scheda.arrivi)}
      ${attivita}
      <p style="color:var(--cromo-cupo)"><strong>Combattimento:</strong> forza ${esc(scheda.combattimento?.forza)} · resistenza ${esc(scheda.combattimento?.resistenza)} — ${esc(scheda.combattimento?.nota || '')}</p>
    </div>`;
}

function aggiornaDichiarazioni(dati) {
  const tocca = $('#sc-tocca');
  tocca.textContent = dati.turno_di
    ? `Ordine di turno (morbido): ora toccherebbe a ${dati.turno_di}.`
    : 'In questo turno hanno mosso tutti.';
  const lista = $('#dichiarazioni-attesa');
  const inAttesa = (dati.navi || []).filter((n) => n.dichiarazione_in_attesa);
  if (!inAttesa.length) {
    lista.innerHTML = '<li class="vuoto">Nessuna dichiarazione in attesa dai Terminali.</li>';
    return;
  }
  lista.innerHTML = inAttesa.map((n) => {
    const d = n.dichiarazione_in_attesa;
    return `
      <li class="dichiarazione" data-nave="${esc(n.nome)}">
        <div class="cap-dichiarazione">
          <span class="bandiera-nave" style="background:${esc(n.colore)}"></span>
          <b>${esc(n.nome)}</b>
        </div>
        <div class="corpo-dichiarazione">
          <span class="rotta-dich">${esc(d.rotta)}</span>${d.atterraggio ? ' · <b>ATTERRAGGIO</b>' : ''}
          <small>${d.serbatoi} serbatoi · ${d.radar} radar · ${d.computer ?? '—'} computer</small>
        </div>
        <div class="azioni-dichiarazione">
          <button class="bottone bottone-piccolo" data-risolvi="${esc(n.nome)}">Risolvi</button>
          <button class="bottone bottone-piccolo" data-annulla-dich="${esc(n.nome)}">Annulla</button>
        </div>
      </li>`;
  }).join('');
}

function disegna() {
  if (!stato.dati) return;
  aggiornaTesta(stato.dati);
  // In modo editor la tela appartiene alla bozza: un aggiornamento della partita
  // (per esempio il toggle Plancia U.C.) non deve cancellare la galassia in costruzione.
  if (stato.editor.attivo) {
    disegnaEditorTela();
  } else {
    $('#tela').innerHTML = stato.vistaMappa === 'stereoscopio'
      ? disegnaStereoscopio(stato.dati)
      : disegnaSettori(stato.dati);
  }
  aggiornaNavi(stato.dati);
  aggiornaDichiarazioni(stato.dati);
  aggiornaRegistro(stato.dati);
  aggiornaDossier();
  aggiornaAutonomia();
}

/* ───────────────────────────── comandi ───────────────────────────── */

let ultimaImpronta = null;   // per il polling: si ridisegna solo quando lo stato cambia davvero

async function caricaStato() {
  const vista = $('#campo-vista-uc').checked ? 'uc' : 'sc';
  stato.dati = await chiama(`/api/stato?vista=${vista}`);
  ultimaImpronta = JSON.stringify(stato.dati);
  disegna();
}

async function sincronizza() {
  // Battito leggero: fa comparire da sé le dichiarazioni dai Terminali e le mosse
  // altrui, senza toccare i moduli che il master sta compilando. Non ridisegna se
  // nulla è cambiato (niente sfarfallio) e sta ferma mentre si costruisce una galassia.
  if (stato.editor.attivo || document.hidden) return;
  try {
    const vista = $('#campo-vista-uc').checked ? 'uc' : 'sc';
    const dati = await chiama(`/api/stato?vista=${vista}`);
    const impronta = JSON.stringify(dati);
    if (impronta === ultimaImpronta) return;
    ultimaImpronta = impronta;
    stato.dati = dati;
    disegna();
  } catch (errore) {
    // silenzioso: la consolle non deve urlare a ogni battito perso
  }
}

async function risolviDichiarazione(nave) {
  try {
    const risposta = await chiama('/api/dichiarazione/risolvi', { nave });
    await caricaStato();
    const comunicazioni = risposta.esito.movimento?.comunicazioni || [];
    avvisa(comunicazioni.join('  ·  ') || `Rotta di ${nave} eseguita.`, 'esito');
  } catch (errore) { avvisa(errore.message); }
}

async function annullaDichiarazioneSC(nave) {
  try {
    await chiama('/api/dichiarazione/annulla', { nave });
    await caricaStato();
    avvisa(`Dichiarazione di ${nave} annullata.`, 'esito');
  } catch (errore) { avvisa(errore.message); }
}

function aggiornaDettagliNavi() {
  const contenitore = $('#dettagli-navi-esterno');
  const esterno = $('#campo-esterno').checked;
  const nomi = $('#campo-ufficiali').value.split(',').map((s) => s.trim().toUpperCase()).filter(Boolean);
  contenitore.hidden = !esterno || !nomi.length;
  if (contenitore.hidden) return;
  const precedenti = stato.dettagliNavi || {};
  $('#righe-dettagli-navi').innerHTML = nomi.map((nome) => {
    const classe = precedenti[nome]?.classe_massa ?? 2;
    const psi = precedenti[nome]?.princeps_psi ?? false;
    return `
      <div class="riga-dettaglio-nave" data-nome="${esc(nome)}">
        <span class="nome-nave-dettaglio">${esc(nome)}</span>
        <label class="campo">
          <span>Classe/massa</span>
          <select class="campo-classe-massa">
            <option value="1" ${classe === 1 ? 'selected' : ''}>1 · leggera</option>
            <option value="2" ${classe === 2 ? 'selected' : ''}>2 · media</option>
            <option value="3" ${classe === 3 ? 'selected' : ''}>3 · pesante</option>
          </select>
        </label>
        <label class="interruttore compatto">
          <input type="checkbox" class="campo-princeps-psi" ${psi ? 'checked' : ''}>
          <span class="leva"></span>
          <span class="etichetta-leva">Princeps Psi</span>
        </label>
      </div>`;
  }).join('');
}

function leggiDettagliNavi() {
  const dettagli = {};
  document.querySelectorAll('#righe-dettagli-navi .riga-dettaglio-nave').forEach((riga) => {
    dettagli[riga.dataset.nome] = {
      classe_massa: Number(riga.querySelector('.campo-classe-massa').value),
      princeps_psi: riga.querySelector('.campo-princeps-psi').checked,
    };
  });
  stato.dettagliNavi = dettagli;
  return dettagli;
}

async function generaZona() {
  const ufficiali = $('#campo-ufficiali').value.split(',').map((s) => s.trim()).filter(Boolean);
  const spazioEsterno = $('#campo-esterno').checked;
  const dettagliNavi = spazioEsterno ? leggiDettagliNavi() : undefined;
  try {
    if (stato.modoCreazione === 'editor') {
      await chiama('/api/editor/avvia', { ufficiali, spazio_esterno: spazioEsterno, dettagli_navi: dettagliNavi });
      stato.editor.bozza = null;
      stato.editor.validazione = null;
      stato.editor.selezione = null;
      impostaModoCreazione('seme');
    } else {
      await chiama('/api/nuova', {
        seme: $('#campo-seme').value,
        lato: Number($('#campo-lato').value),
        distribuzione: $('#campo-distribuzione').value,
        ufficiali,
        spazio_esterno: spazioEsterno,
        dettagli_navi: dettagliNavi,
      });
    }
    stato.selezione = null;
    await caricaStato();
    avvisa(`Zona creata. Matricola ${stato.dati.galassia.seme}. Gli U.C. non ne sono al corrente.`, 'esito');
  } catch (errore) { avvisa(errore.message); }
}

async function eseguiRotta() {
  try {
    const risposta = await chiama('/api/rotta', {
      nave: $('#campo-nave').value,
      rotta: $('#campo-rotta').value,
      serbatoi: Number($('#campo-serbatoi').value),
      radar: Number($('#campo-radar').value),
      computer: Number($('#campo-computer').value),
      atterraggio: $('#campo-atterraggio').checked,
    });
    await caricaStato();
    const comunicazioni = risposta.esito.movimento.comunicazioni || [];
    avvisa(comunicazioni.join('  ·  ') || 'Rotta eseguita.', 'esito');
    $('#campo-atterraggio').checked = false;
  } catch (errore) { avvisa(errore.message); }
}

async function richiediInformazione() {
  try {
    const risposta = await chiama('/api/informazione', {
      nave: $('#campo-nave').value,
      pianeta: stato.selezione,
    });
    await caricaStato();
    const e = risposta.esito;
    const dado = e.dado ? `${e.dado} → ${e.esito} · ` : '';
    avvisa(`${e.livello} livello · ${dado}${e.testo}`, e.dns ? 'errore' : 'esito');
  } catch (errore) { avvisa(errore.message); }
}

async function atterra() {
  try {
    const risposta = await chiama('/api/atterraggio', { nave: $('#campo-nave').value, pianeta: stato.selezione });
    await caricaStato();
    const e = risposta.esito;
    avvisa(`Atterraggio su ${e.sigla}. Punti attribuiti: ${e.punti ?? 0}.`, 'esito');
  } catch (errore) { avvisa(errore.message); }
}

async function chiudiTurno() {
  try {
    await chiama('/api/turno', {});
    await caricaStato();
    avvisa(`Turno ${stato.dati.turno}. Informazioni di bordo ripristinate.`, 'esito');
  } catch (errore) { avvisa(errore.message); }
}

async function esporta() {
  try {
    const dati = await chiama('/api/esporta');
    const url = URL.createObjectURL(new Blob([JSON.stringify(dati, null, 2)], { type: 'application/json' }));
    const collegamento = document.createElement('a');
    collegamento.href = url;
    collegamento.download = `vii-legio-${dati.stato.galassia.seme}.json`;
    collegamento.click();
    URL.revokeObjectURL(url);
  } catch (errore) { avvisa(errore.message); }
}

/* ───────────────────────────── avvio ───────────────────────────── */

function collega() {
  $('#bottone-genera').addEventListener('click', generaZona);
  $('#bottone-rotta').addEventListener('click', eseguiRotta);
  $('#bottone-turno').addEventListener('click', chiudiTurno);
  $('#bottone-esporta').addEventListener('click', esporta);
  $('#bottone-stampa').addEventListener('click', () => window.print());
  $('#campo-serbatoi').addEventListener('input', aggiornaAutonomia);
  $('#campo-vista-uc').addEventListener('change', async () => {
    // In modo editor la plancia filtra la bozza, che vive sul server: va richiesta di nuovo.
    if (stato.editor.attivo) await caricaBozzaEditor();
    await caricaStato();
  });
  $('#campo-esterno').addEventListener('change', aggiornaDettagliNavi);
  $('#campo-ufficiali').addEventListener('input', aggiornaDettagliNavi);
  $('#campo-nave').addEventListener('change', () => { aggiornaNavi(stato.dati); aggiornaDossier(); });
  $('#campo-rotta').addEventListener('keydown', (evento) => { if (evento.key === 'Enter') eseguiRotta(); });

  const scegliVista = (nome) => {
    document.querySelectorAll('[data-vista-mappa]').forEach((b) => {
      b.classList.toggle('attiva', b.dataset.vistaMappa === nome);
    });
    stato.vistaMappa = nome;
    location.hash = nome;
    disegna();
  };
  document.querySelectorAll('[data-vista-mappa]').forEach((bottone) => {
    bottone.addEventListener('click', () => scegliVista(bottone.dataset.vistaMappa));
  });
  if (location.hash.slice(1) === 'stereoscopio') scegliVista('stereoscopio');

  document.querySelectorAll('[data-modo-creazione]').forEach((bottone) => {
    bottone.addEventListener('click', () => impostaModoCreazione(bottone.dataset.modoCreazione));
  });
  document.querySelectorAll('#strumenti-editor [data-strumento]').forEach((bottone) => {
    bottone.addEventListener('click', () => {
      document.querySelectorAll('#strumenti-editor [data-strumento]').forEach((b) => b.classList.toggle('attiva', b === bottone));
      stato.editor.strumento = bottone.dataset.strumento;
      stato.editor.rmgBuffer = [];
      aggiornaIstruzioneEditor();
    });
  });
  $('#bottone-editor-nuovo').addEventListener('click', nuovaBozza);
  $('#bottone-editor-esporta').addEventListener('click', esportaBozza);
  $('#bottone-editor-importa').addEventListener('click', () => $('#campo-editor-importa').click());
  $('#campo-editor-importa').addEventListener('change', (evento) => {
    const file = evento.target.files[0];
    evento.target.value = '';
    if (file) importaBozza(file);
  });

  $('#tela').addEventListener('click', (evento) => {
    if (stato.editor.attivo) { gestisciClickEditor(evento); return; }
    const sistema = evento.target.closest('[data-pianeta]');
    if (!sistema) return;
    stato.selezione = sistema.dataset.pianeta;
    disegna();
  });

  $('#elenco-navi').addEventListener('click', (evento) => {
    const scheda = evento.target.closest('[data-nave]');
    if (!scheda) return;
    $('#campo-nave').value = scheda.dataset.nave;
    aggiornaNavi(stato.dati);
    aggiornaDossier();
  });

  $('#dichiarazioni-attesa').addEventListener('click', (evento) => {
    const risolvi = evento.target.closest('[data-risolvi]');
    const annulla = evento.target.closest('[data-annulla-dich]');
    if (risolvi) risolviDichiarazione(risolvi.dataset.risolvi);
    else if (annulla) annullaDichiarazioneSC(annulla.dataset.annullaDich);
  });

  $('#dossier').addEventListener('click', (evento) => {
    const azione = evento.target.closest('[data-azione]')?.dataset.azione;
    if (azione === 'informa') richiediInformazione();
    if (azione === 'atterra') atterra();
  });
}

(async function avvia() {
  collega();
  aggiornaDettagliNavi();
  try {
    stato.tabelle = await chiama('/api/tabelle');
    await caricaStato();
  } catch (errore) {
    avvisa(`Terminale non raggiungibile: ${errore.message}`);
  }
  setInterval(sincronizza, 2000);  // battito: le dichiarazioni dai Terminali compaiono da sé
}());
