/* RedTeam Lab v4 — Detective: cronómetro por bug + check verde persistente
 *
 * Por cada bug-card:
 *   - Chip ⏱ HH:MM:SS que corre cuando la card está visible (auto-start)
 *   - Botones: ▶ Reanudar · ⏸ Pausar · ↻ Resetear
 *   - Cuando se marca como resuelto, se pinta verde + check grande
 *   - Se persiste en localStorage: 'redteam-detective-tiempos'
 *
 * También arma el resumen arriba: resueltos / tiempo total / promedio
 */
(function () {
  'use strict';

  const KEY_TIEMPOS = 'redteam-detective-tiempos';     // { [bugId]: { segundos: number, corriendo: bool, iniciadoEn: ts|null, terminadoEn: ts|null } }
  const KEY_RESUELTOS = 'detective-resueltos';  // misma key que usa detective.html (no duplicar)

  // ==================== HELPERS ====================
  function fmtTiempo(seg) {
    seg = Math.max(0, Math.floor(seg));
    const h = Math.floor(seg / 3600);
    const m = Math.floor((seg % 3600) / 60);
    const s = seg % 60;
    const pad = n => String(n).padStart(2, '0');
    return `${pad(h)}:${pad(m)}:${pad(s)}`;
  }

  function cargarTiempos() {
    try { return JSON.parse(localStorage.getItem(KEY_TIEMPOS) || '{}'); }
    catch (e) { return {}; }
  }

  function guardarTiempos(t) {
    localStorage.setItem(KEY_TIEMPOS, JSON.stringify(t));
  }

  function getTiempo(bugId) {
    const t = cargarTiempos();
    return t[bugId] || { segundos: 0, corriendo: true, iniciadoEn: null, terminadoEn: null };
  }

  function setTiempo(bugId, data) {
    const t = cargarTiempos();
    t[bugId] = data;
    guardarTiempos(t);
  }

  function getResueltos() {
    try { return JSON.parse(localStorage.getItem(KEY_RESUELTOS) || '[]'); }
    catch (e) { return []; }
  }

  // ==================== CSS ====================
  function inyectarCSS() {
    if (document.getElementById('det-tiempo-css')) return;
    const css = `
      .det-tiempo {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        background: var(--bg-card, #fff);
        border: 1px solid var(--border, #dadde1);
        border-radius: 5px;
        padding: 0.18rem 0.55rem;
        font-size: 0.74rem;
        color: var(--text-soft, #65676b);
        font-variant-numeric: tabular-nums;
        font-family: "JetBrains Mono", "Courier New", monospace;
        transition: background 0.15s, border-color 0.15s, color 0.15s;
      }
      .det-tiempo.corr {
        background: rgba(245, 158, 11, 0.10);
        border-color: #f59e0b;
        color: #92400e;
      }
      .det-tiempo.pausa {
        background: #f0f0f0;
        border-color: #d0d0d0;
        color: #8a8d91;
      }
      .det-tiempo.resuelto {
        background: rgba(16, 185, 129, 0.10);
        border-color: #10b981;
        color: #047857;
      }
      .det-tiempo .det-tiempo-icon { font-size: 0.85rem; }

      .det-tiempo-botones {
        display: inline-flex;
        gap: 0.25rem;
      }
      .det-tiempo-btn {
        background: var(--bg-card, #fff);
        border: 1px solid var(--border, #dadde1);
        color: var(--text-main, #1c1e21);
        padding: 0.2rem 0.55rem;
        border-radius: 5px;
        font-size: 0.74rem;
        cursor: pointer;
        font-weight: 500;
      }
      .det-tiempo-btn:hover { background: var(--bg-soft, #f7f8fa); }
      .det-tiempo-btn.primary {
        background: var(--accent, #1877f2);
        color: white;
        border-color: var(--accent, #1877f2);
      }
      .det-tiempo-btn.primary:hover { filter: brightness(0.95); }

      /* Check verde al lado del chip, no en esquina (el cuaderno fixed tapa la esquina) */
      .bug-card.resuelto {
        background: rgba(16, 185, 129, 0.06);
      }
      .bug-card.resuelto .bug-num {
        background: var(--color-exito, #10b981) !important;
      }
      .bug-card .det-check {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid #10b981;
        color: #047857;
        padding: 0.2rem 0.55rem;
        border-radius: 5px;
        font-size: 0.74rem;
        font-weight: 700;
      }

      /* Box resumen arriba */
      .det-resumen {
        background: rgba(16, 185, 129, 0.08);
        border: 1px solid #10b981;
        border-radius: 10px;
        padding: 0.7rem 1rem;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 1rem;
        flex-wrap: wrap;
        font-size: 0.88rem;
        color: #065f46;
      }
      .det-resumen .det-res-icon { font-size: 1.3rem; }
      .det-resumen .det-res-stat {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
      }
      .det-resumen b { color: #047857; }
    `;
    const style = document.createElement('style');
    style.id = 'det-tiempo-css';
    style.textContent = css;
    document.head.appendChild(style);
  }

  // ==================== TICK GLOBAL ====================
  // Refresca el display de TODOS los chips cada 1s
  let tickHandle = null;
  function iniciarTick() {
    if (tickHandle) return;
    tickHandle = setInterval(refrescarTodosLosChips, 1000);
  }
  function detenerTick() {
    if (tickHandle) { clearInterval(tickHandle); tickHandle = null; }
  }

  function refrescarTodosLosChips() {
    const tiempos = cargarTiempos();
    const resueltos = getResueltos();
    document.querySelectorAll('.det-tiempo').forEach(chip => {
      const bugId = chip.dataset.bugId;
      // Re-leer desde localStorage para tener el estado ACTUAL (no el de cuando se inyectó)
      const data = tiempos[bugId] || getTiempo(bugId);
      const seg = calcularSegundos(data);
      chip.querySelector('.det-tiempo-valor').textContent = fmtTiempo(seg);
      // Si está resuelto, pintar verde y parar contador visual
      if (resueltos.includes(bugId)) {
        chip.classList.add('resuelto');
        chip.classList.remove('corr', 'pausa');
      } else if (data.corriendo) {
        chip.classList.add('corr');
        chip.classList.remove('pausa', 'resuelto');
      } else {
        chip.classList.add('pausa');
        chip.classList.remove('corr', 'resuelto');
      }
    });
  }

  function calcularSegundos(data) {
    let seg = data.segundos || 0;
    if (data.corriendo && data.iniciadoEn) {
      seg += Math.floor((Date.now() - data.iniciadoEn) / 1000);
    }
    return seg;
  }

  // ==================== RESUMEN ====================
  function renderResumen() {
    let box = document.getElementById('det-resumen');
    if (!box) {
      // Crear el box y ponerlo arriba del primer grupo-card
      box = document.createElement('div');
      box.id = 'det-resumen';
      box.className = 'det-resumen';
      const mainCol = document.querySelector('.main-col, main, .cuerpo');
      if (!mainCol) return;
      const primerGrupo = mainCol.querySelector('.grupo-card, .grupo, h2');
      if (primerGrupo && primerGrupo.parentNode === mainCol) {
        mainCol.insertBefore(box, primerGrupo);
      } else {
        mainCol.prepend(box);
      }
    }
    const tiempos = cargarTiempos();
    const resueltos = getResueltos();
    let totalSeg = 0;
    let cantConTiempo = 0;
    resueltos.forEach(id => {
      const d = tiempos[id];
      if (d) { totalSeg += calcularSegundos(d); cantConTiempo++; }
    });
    const promSeg = cantConTiempo > 0 ? Math.floor(totalSeg / cantConTiempo) : 0;
    const totalCards = document.querySelectorAll('.bug-card').length;
    box.innerHTML = `
      <span class="det-res-icon">📊</span>
      <span class="det-res-stat">Avance: <b>${resueltos.length}/${totalCards} resueltos</b></span>
      <span class="det-res-stat">⏱ Tiempo total: <b>${fmtTiempo(totalSeg)}</b></span>
      <span class="det-res-stat">⏱ Promedio: <b>${fmtTiempo(promSeg)}</b></span>
    `;
  }

  // ==================== HANDLERS DE BOTONES ====================
  function togglePausar(bugId) {
    const data = getTiempo(bugId);
    const resueltos = getResueltos();
    if (resueltos.includes(bugId)) return; // No pausar si ya está resuelto
    if (data.corriendo) {
      // Estaba corriendo → pausar (acumular segundos y detener iniciadoEn)
      const ahora = Date.now();
      const segAcumulados = (data.segundos || 0) + Math.floor((ahora - (data.iniciadoEn || ahora)) / 1000);
      setTiempo(bugId, {
        segundos: segAcumulados,
        corriendo: false,
        iniciadoEn: null,
        terminadoEn: null
      });
    } else {
      // Estaba pausado → reanudar
      setTiempo(bugId, {
        segundos: data.segundos || 0,
        corriendo: true,
        iniciadoEn: Date.now(),
        terminadoEn: null
      });
    }
    refrescarTodosLosChips();
    renderBotones(bugId);
  }

  function resetear(bugId) {
    setTiempo(bugId, { segundos: 0, corriendo: true, iniciadoEn: Date.now(), terminadoEn: null });
    refrescarTodosLosChips();
    renderBotones(bugId);
  }

  function renderBotones(bugId) {
    const data = getTiempo(bugId);
    const resueltos = getResueltos();
    const cont = document.querySelector(`.det-tiempo-botones[data-bug-id="${bugId}"]`);
    if (!cont) return;
    if (resueltos.includes(bugId)) {
      // Resuelto: mostrar check verde en lugar de botones
      cont.innerHTML = `<span class="det-check">✅ Resuelto</span>`;
      return;
    }
    if (data.corriendo) {
      cont.innerHTML = `
        <button class="det-tiempo-btn primary" data-accion="pausar">⏸ Pausar</button>
        <button class="det-tiempo-btn" data-accion="resetear">↻ Resetear</button>
      `;
    } else {
      cont.innerHTML = `
        <button class="det-tiempo-btn primary" data-accion="reanudar">▶ Reanudar</button>
        <button class="det-tiempo-btn" data-accion="resetear">↻ Resetear</button>
      `;
    }
    cont.querySelectorAll('button').forEach(btn => {
      btn.onclick = () => {
        const acc = btn.dataset.accion;
        if (acc === 'pausar' || acc === 'reanudar') togglePausar(bugId);
        else if (acc === 'resetear') resetear(bugId);
      };
    });
  }

  // ==================== INYECTAR UI EN CADA BUG-CARD ====================
  function inyectarChipEnCards() {
    const cards = document.querySelectorAll('.bug-card');
    if (cards.length === 0) return;

    cards.forEach(card => {
      const bugId = card.dataset.bug;
      if (!bugId) return;
      // Evitar duplicar
      if (card.querySelector(`.det-tiempo[data-bug-id="${bugId}"]`)) return;

      // PASO 1: Asegurar que el bug tenga un tiempo inicializado (auto-start en la primera carga)
      const tiempos = cargarTiempos();
      if (!tiempos[bugId]) {
        tiempos[bugId] = { segundos: 0, corriendo: true, iniciadoEn: Date.now(), terminadoEn: null };
        guardarTiempos(tiempos);
      }
      // PASO 2: Ahora sí leer el estado (ya inicializado)

      // Encontrar el head (donde está bug-num, bug-dificultad)
      const head = card.querySelector('.bug-head') || card;
      // Si no hay .bug-head, creamos uno minimalista
      let headEl = card.querySelector('.bug-head');
      if (!headEl) {
        headEl = document.createElement('div');
        headEl.className = 'bug-head';
        headEl.style.cssText = 'display:flex;align-items:center;gap:0.4rem;flex-wrap:wrap;';
        // Mover bug-num y bug-dificultad al head si están sueltos
        const num = card.querySelector('.bug-num');
        const dif = card.querySelector('.bug-dificultad');
        if (num) headEl.appendChild(num);
        if (dif) headEl.appendChild(dif);
        card.insertBefore(headEl, card.firstChild);
      }

      // Crear chip
      const data = getTiempo(bugId);
      const seg = calcularSegundos(data);
      const resueltos = getResueltos();
      const chip = document.createElement('span');
      chip.className = 'det-tiempo ' + (resueltos.includes(bugId) ? 'resuelto' : (data.corriendo ? 'corr' : 'pausa'));
      chip.dataset.bugId = bugId;
      chip.innerHTML = `
        <span class="det-tiempo-icon">⏱</span>
        <span class="det-tiempo-valor">${fmtTiempo(seg)}</span>
      `;
      headEl.appendChild(chip);

      // Crear contenedor de botones (al lado del chip, no a la derecha del todo)
      const botones = document.createElement('span');
      botones.className = 'det-tiempo-botones';
      botones.dataset.bugId = bugId;
      botones.style.cssText = 'display:inline-flex;gap:0.25rem;margin-left:0.4rem;';
      headEl.appendChild(botones);

      renderBotones(bugId);
    });
  }

  // ==================== INIT ====================
  let inyeccionHecha = false;
  function init() {
    inyectarCSS();
    inyectarChipEnCards();
    renderResumen();
    refrescarTodosLosChips();  // Refrescar inmediatamente (no esperar 1s)
    iniciarTick();

    // Hook: cuando se marca/desmarca como resuelto, refrescar botones y resumen
    const observer = new MutationObserver((mutations) => {
      // Solo actuar si cambió la clase de una bug-card (no por nuestros propios inserts)
      const esCambioBug = mutations.some(m =>
        m.type === 'attributes' &&
        m.attributeName === 'class' &&
        m.target.classList && m.target.classList.contains('bug-card')
      );
      if (!esCambioBug) return;
      renderResumen();
      refrescarTodosLosChips();
      document.querySelectorAll('.bug-card').forEach(card => {
        renderBotones(card.dataset.bug);
      });
    });
    document.querySelectorAll('.bug-card').forEach(card => {
      observer.observe(card, { attributes: true, attributeFilter: ['class'] });
    });
  }

  // Exponer para tests
  window.RedTeamDetectiveTiempo = {
    fmtTiempo,
    cargarTiempos,
    getTiempo,
    getResueltos,
    renderResumen,
    refrescarTodosLosChips,
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();