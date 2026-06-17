/* RedTeam Lab v4 — Sidebar (izq) + Notas (der) + Panel Detective
 *
 * Sidebar izquierdo: Tu avance + lista de 10 bugs del Detective
 * Panel derecho: TUS NOTAS con auto-guardado + exportar a TXT/PDF
 * Las cards del Detective scrollean al bug correspondiente
 * Botón flotante del sidebar izq NUNCA tapa la nav (bottom: 70px)
 */
(function () {
  'use strict';

  const KEY_DETECTIVE = 'redteam-detective-resueltos';
  const KEY_CUSTOM_DBS = 'redteam-custom-dbs';
  const KEY_NOTAS = 'redteam-notas';

  const BUGS = [
    {id: '1a', nombre: '1A · URL duplicada', grupo: 'URLs'},
    {id: '1b', nombre: '1B · URL concatenada', grupo: 'URLs'},
    {id: '2a', nombre: '2A · Input vacío', grupo: 'Validación'},
    {id: '2b', nombre: '2B · Tipo incorrecto', grupo: 'Validación'},
    {id: '3a', nombre: '3A · SQLi SELECT', grupo: 'SQLi'},
    {id: '3b', nombre: '3B · SQLi INSERT', grupo: 'SQLi'},
    {id: '4a', nombre: '4A · Credenciales', grupo: 'Auth'},
    {id: '4b', nombre: '4B · Token sin exp', grupo: 'Auth'},
    {id: '5a', nombre: '5A · Stack trace', grupo: 'Info Discl.'},
    {id: '5b', nombre: '5B · Endpoint debug', grupo: 'Info Discl.'},
  ];

  // ==================== CSS ====================
  function inyectarCSS() {
    if (document.getElementById('sidebar-css')) return;
    const css = `
      /* === LAYOUT 2 COLUMNAS: cuerpo + notas (sidebar IZQ va abajo, franja) === */
      .rt-layout {
        display: grid;
        grid-template-columns: 1fr 300px;
        gap: 1rem;
        max-width: 1500px;
        margin: 1rem auto;
        padding: 0 1.5rem;
        align-items: start;
      }
      /* La sidebar IZQ ocupa todo el ancho, debajo del cuerpo y notas */
      .rt-layout > .sidebar {
        grid-column: 1 / -1;
        max-height: none;
        margin-top: 0.5rem;
      }
      .rt-layout > .notes-panel {
        width: 300px;
        min-width: 300px;
        transition: width 0.3s ease, min-width 0.3s ease, padding 0.3s ease, opacity 0.2s ease, border-color 0.3s ease;
        overflow: hidden;
        flex-shrink: 0;
      }
      .rt-layout > .notes-panel.collapsed,
      .rt-layout > .notes-panel.collapsed * {
        width: 0 !important;
        min-width: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
        border: none !important;
        opacity: 0 !important;
        overflow: hidden !important;
      }
      .rt-layout > main,
      .rt-layout > .cuerpo {
        min-width: 0;
        max-height: none;
        background: var(--bg-card, #ffffff);
        border: 1px solid var(--border-soft, #dadde1);
        border-radius: 10px;
        padding: 1.5rem 2rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
      }
      .rt-layout > main { position: relative; }
      .sidebar, .notes-panel {
        position: static;
        width: auto;
        max-height: none;
        overflow-y: visible;
        background: var(--bg-card, #ffffff);
        border: 1px solid var(--border-soft, #dadde1);
        border-radius: 10px;
        padding: 1rem 1.1rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        z-index: 1;
        font-family: var(--font-family-base, sans-serif);
        font-size: 0.88rem;
      }
      /* === Sidebar IZQ como franja horizontal ABAJO del cuerpo (layout 2 col) === */
      .sidebar {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        gap: 1.5rem;
        max-height: none;
        margin-top: 1rem;
      }
      .sidebar .sidebar-section { margin-bottom: 0; }
      .sidebar-section { margin-bottom: 1rem; padding-bottom: 0.8rem; border-bottom: 1px solid var(--border-soft, #f0f2f5); }
      .sidebar-section:last-child { border-bottom: none; margin-bottom: 0; }
      .sidebar h4 {
        color: var(--accent, #1877f2);
        font-size: 0.85rem;
        text-transform: uppercase;
        font-weight: 700;
        margin: 0 0 0.5rem 0;
        letter-spacing: 0.5px;
      }
      .sidebar-stat {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 0.3rem 0;
        color: var(--text-main, #1c1e21);
      }
      .sidebar-stat .label { color: var(--text-muted, #65676b); font-size: 0.85rem; }
      .sidebar-stat .value {
        background: var(--accent, #1877f2);
        color: white;
        font-size: 0.78rem;
        font-weight: 700;
        padding: 1px 8px;
        border-radius: 10px;
      }
      .sidebar-bugs { list-style: none; padding: 0; margin: 0; }
      .sidebar-bugs li {
        display: block;
        padding: 0.35rem 0.4rem;
        font-size: 0.82rem;
        color: var(--text-muted, #65676b);
        cursor: pointer;
        border-radius: 4px;
        transition: background 0.15s;
      }
      .sidebar-bugs li:hover {
        background: var(--accent-soft, #e7f3ff);
        color: var(--accent, #1877f2);
      }
      .sidebar-bugs li.resuelto {
        color: var(--color-exito, #10b981);
        text-decoration: line-through;
        opacity: 0.7;
      }
      .sidebar-bugs li .check { margin-right: 0.3rem; }

      /* Panel derecho de notas */
      .notes-panel {
        position: fixed;
        top: 80px;
        right: 16px;
        width: 280px;
        max-height: calc(100vh - 100px);
        background: var(--bg-card, #ffffff);
        border: 1px solid var(--border-soft, #dadde1);
        border-radius: 10px;
        padding: 0.9rem 1rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        z-index: 50;
        font-family: var(--font-family-base, sans-serif);
        font-size: 0.88rem;
        display: flex;
        flex-direction: column;
      }
      .notes-panel h4 {
        color: var(--accent, #1877f2);
        font-size: 0.85rem;
        text-transform: uppercase;
        font-weight: 700;
        margin: 0 0 0.5rem 0;
        letter-spacing: 0.5px;
        display: flex;
        align-items: center;
        justify-content: space-between;
      }
      .notes-panel h4 button {
        background: transparent;
        border: none;
        color: var(--text-muted, #65676b);
        font-size: 1.1rem;
        cursor: pointer;
        padding: 0 0.3rem;
      }
      .notes-panel h4 button:hover { color: var(--color-fallo, #b91c1c); }
      .notes-panel textarea {
        flex: 1;
        min-height: 200px;
        font-family: inherit;
        font-size: 0.85rem;
        padding: 0.5rem;
        border: 1px solid var(--border-soft, #dadde1);
        border-radius: 4px;
        resize: vertical;
        background: var(--bg-soft, #f7f8fa);
        color: var(--text-main, #1c1e21);
      }
      .notes-panel .save-status {
        color: var(--color-exito, #10b981);
        font-size: 0.78rem;
        margin-top: 0.2rem;
        height: 1em;
      }
      .notes-panel .acciones {
        display: flex;
        gap: 0.4rem;
        margin-top: 0.5rem;
      }
      .notes-panel .acciones button {
        flex: 1;
        padding: 0.4rem;
        border: 1px solid var(--border-soft, #dadde1);
        background: var(--bg-soft, #f7f8fa);
        color: var(--text-main, #1c1e21);
        border-radius: 4px;
        cursor: pointer;
        font-size: 0.78rem;
        font-family: inherit;
      }
      .notes-panel .acciones button:hover {
        background: var(--accent-soft, #e7f3ff);
        border-color: var(--accent, #1877f2);
        color: var(--accent, #1877f2);
      }

      /* Botón flotante del sidebar - ADENTRO del header (no tapa nada) */
      .sidebar-toggle {
        position: fixed;
        top: 100px;
        left: 16px;
        width: 38px;
        height: 38px;
        border-radius: 50%;
        background: var(--accent, #1877f2);
        color: white;
        border: none;
        font-size: 1rem;
        cursor: pointer;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
        z-index: 60;
        display: none;  /* Por defecto oculto, aparece cuando la sidebar está colapsada */
        align-items: center;
        justify-content: center;
        transition: transform 0.2s ease;
      }
      body.sidebar-collapsed-izq .sidebar-toggle {
        display: flex;
      }
      .sidebar-toggle:hover { transform: scale(1.1); }

      .notes-toggle {
        position: fixed;
        top: 100px;
        right: 16px;
        width: 38px;
        height: 38px;
        border-radius: 50%;
        background: var(--accent, #1877f2);
        color: white;
        border: none;
        font-size: 1rem;
        cursor: pointer;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
        z-index: 60;
        display: none;  /* Por defecto oculto */
        align-items: center;
        justify-content: center;
        transition: transform 0.2s ease;
      }
      body.sidebar-collapsed-der .notes-toggle {
        display: flex;
      }
      .notes-toggle:hover { transform: scale(1.1); }
      .notes-toggle:hover {
        background: var(--accent-soft, #e7f3ff);
        border-color: var(--accent, #1877f2);
        color: var(--accent, #1877f2);
      }

      /* Mover contenido principal cuando sidebars están visibles */
      @media (min-width: 1200px) {
        body.sidebar-on main { margin-left: 260px; transition: margin 0.2s; }
        body.notes-on main { margin-right: 300px; transition: margin 0.2s; }
      }
    `;
    const style = document.createElement('style');
    style.id = 'sidebar-css';
    style.textContent = css;
    document.head.appendChild(style);
  }

  // ==================== HELPERS ====================
  function getDetectiveResueltos() {
    try { return JSON.parse(localStorage.getItem(KEY_DETECTIVE) || '[]'); } catch (e) { return []; }
  }
  function getCustomDBs() {
    try { return JSON.parse(localStorage.getItem(KEY_CUSTOM_DBS) || '[]'); } catch (e) { return []; }
  }
  function getNota() {
    return localStorage.getItem(KEY_NOTAS) || '';
  }

  // ==================== EXPORTAR NOTAS ====================
  function exportarTXT() {
    const nota = getNota();
    const resueltos = getDetectiveResueltos();
    const customs = getCustomDBs();
    const txt = `=== Mis notas del RedTeam Lab ===

Fecha: ${new Date().toLocaleString('es-AR')}

--- Detective de Bugs (${resueltos.length}/10) ---
${BUGS.map(b => `  ${resueltos.includes(b.id) ? '[X]' : '[ ]'} ${b.nombre}`).join('\n')}

--- DBs custom (${customs.length}/3) ---
${customs.length === 0 ? '  (ninguna)' : customs.map(d => `  - ${d}`).join('\n')}

--- Mis notas ---

${nota || '(vacío)'}
`;
    const blob = new Blob([txt], {type: 'text/plain'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `notas-redteam-${new Date().toISOString().slice(0,10)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }

  // ==================== EXPORTAR PDF (HTML imprimible) ====================
  function exportarPDF() {
    const nota = getNota();
    const resueltos = getDetectiveResueltos();
    const customs = getCustomDBs();
    // Abrimos una ventana con un HTML imprimible
    const html = `<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Notas RedTeam Lab</title>
<style>
  body { font-family: -apple-system, sans-serif; max-width: 700px; margin: 2em auto; padding: 1em; color: #1c1e21; }
  h1 { color: #1877f2; border-bottom: 2px solid #1877f2; padding-bottom: 0.3em; }
  h2 { color: #1877f2; margin-top: 1.5em; }
  .stat { display: flex; justify-content: space-between; padding: 0.3em 0; border-bottom: 1px solid #e0e6ed; }
  .stat span { color: #65676b; }
  .stat strong { color: #1c1e21; }
  .notas { white-space: pre-wrap; background: #f7f8fa; padding: 1em; border-radius: 6px; border-left: 3px solid #1877f2; }
  .fecha { color: #65676b; font-size: 0.9em; }
  .check { color: #10b981; font-weight: 700; }
  .uncheck { color: #b91c1c; }
  @media print { .no-print { display: none; } }
</style></head>
<body>
  <h1>📓 Mis notas del RedTeam Lab v4</h1>
  <p class="fecha">Fecha: ${new Date().toLocaleString('es-AR')}</p>

  <h2>📊 Detective de Bugs (${resueltos.length}/10 resueltos)</h2>
  ${BUGS.map(b => `<div class="stat"><span>${b.nombre}</span><strong class="${resueltos.includes(b.id) ? 'check' : 'uncheck'}">${resueltos.includes(b.id) ? '✅' : '⬜'}</strong></div>`).join('')}

  <h2>💾 DBs custom (${customs.length}/3)</h2>
  ${customs.length === 0 ? '<p><em>(ninguna)</em></p>' : customs.map(d => `<div class="stat"><span>${d}</span></div>`).join('')}

  <h2>📝 Mis notas</h2>
  <div class="notas">${(nota || '(vacío)').replace(/</g, '&lt;')}</div>

  <div class="no-print" style="margin-top: 2em; text-align: center;">
    <button onclick="window.print()" style="background:#1877f2; color:white; border:none; padding:0.7em 1.5em; border-radius:6px; cursor:pointer; font-size:1em;">🖨️ Imprimir / Guardar como PDF</button>
  </div>
</body></html>`;
    const ventana = window.open('', '_blank', 'width=800,height=900');
    ventana.document.write(html);
    ventana.document.close();
  }

  // ==================== RENDERIZAR ====================
  function renderSidebarDOM(resueltos, customs) {
    // Si ya existe el sidebar, no duplicar
    if (document.getElementById('sidebar')) {
      return;
    }
    // === SIDEBAR IZQUIERDO: solo avance + Detective ===
    const sidebar = document.createElement('aside');
    sidebar.className = 'sidebar';
    sidebar.id = 'sidebar';
    sidebar.innerHTML = `
      <div class="sidebar-section sidebar-header" data-toggle="sidebar">
        <h4 class="sidebar-title">📊 Tu avance <span class="toggle-icon">◀</span></h4>
        <div class="sidebar-stat">
          <span class="label">🐛 Detective</span>
          <span class="value">${resueltos.length}/10</span>
        </div>
        <div class="sidebar-stat">
          <span class="label">💾 DBs custom</span>
          <span class="value">${customs.length}/3</span>
        </div>
        <div class="sidebar-stat">
          <span class="label">🧪 Tests</span>
          <span class="value">22 ✅</span>
        </div>
      </div>

      <div class="sidebar-section">
        <h4>🪲 Detective (click → bug)</h4>
        <ul class="sidebar-bugs">
          ${BUGS.map(b => `
            <li class="sidebar-bug-link ${resueltos.includes(b.id) ? 'resuelto' : ''}" data-bug="${b.id}">
              <span class="check">${resueltos.includes(b.id) ? '✅' : '⬜'}</span>
              ${b.nombre}
            </li>
          `).join('')}
        </ul>
      </div>

      <div class="sidebar-section">
        <h4>🔗 Atajos</h4>
        <div class="sidebar-stat"><a href="/static/practicas.html" style="color:var(--accent);text-decoration:none;">🎵 Práctica</a></div>
        <div class="sidebar-stat"><a href="/static/detective.html" style="color:var(--accent);text-decoration:none;">🪲 Detective</a></div>
        <div class="sidebar-stat"><a href="/static/dbbuilder.html" style="color:var(--accent);text-decoration:none;">🗄️ DB Builder</a></div>
        <div class="sidebar-stat"><a href="/static/wizard.html" style="color:var(--accent);text-decoration:none;">📋 Cargar DB</a></div>
      </div>
    `;
    document.body.classList.add('sidebar-on');
    // Insertar el sidebar IZQ como hermano del <main> (en el body).
    // notas.js lo va a mover adentro del .rt-layout cuando arme el grid.
    // Por ahora lo metemos al body para que exista en el DOM.
    document.body.appendChild(sidebar);

    // Hacer las cards del Detective scrolleables al bug
    sidebar.querySelectorAll('.sidebar-bug-link').forEach(li => {
      li.onclick = () => {
        const bugId = li.dataset.bug;
        irAlBug(bugId);
      };
    });

    // === TOGGLE del sidebar IZQ ===
    // 1) Click en el header h4 → colapsa/expande
    const headerIzq = sidebar.querySelector('[data-toggle="sidebar"]');
    const toggleIzqIcon = sidebar.querySelector('.toggle-icon');
    if (headerIzq) {
      headerIzq.style.cursor = 'pointer';
      headerIzq.onclick = () => {
        const collapsed = sidebar.classList.toggle('collapsed');
        document.body.classList.toggle('sidebar-collapsed-izq', collapsed);
        if (toggleIzqIcon) {
          toggleIzqIcon.textContent = collapsed ? '▶' : '◀';
        }
      };
    }
    // 2) Botón flotante 📊 que aparece cuando la sidebar está colapsada
    const toggleIzq = document.createElement('button');
    toggleIzq.className = 'sidebar-toggle';
    toggleIzq.id = 'sidebarToggle';
    toggleIzq.textContent = '📊';
    toggleIzq.title = 'Mostrar/ocultar panel izquierdo';
    toggleIzq.onclick = () => {
      const collapsed = sidebar.classList.toggle('collapsed');
      document.body.classList.toggle('sidebar-collapsed-izq', collapsed);
      if (toggleIzqIcon) {
        toggleIzqIcon.textContent = collapsed ? '▶' : '◀';
      }
    };
    document.body.appendChild(toggleIzq);

    // === PANEL DERECHO: NOTAS ===
    const notes = document.createElement('aside');
    notes.className = 'notes-panel';
    notes.id = 'notesPanel';
    notes.innerHTML = `
      <h4 class="sidebar-title notes-header" data-toggle="notes">
        📝 Tus notas <span class="toggle-icon">▶</span>
      </h4>
      <textarea id="sidebarNotas" placeholder="Anotá lo que quieras... se guarda solo. Exportá a PDF o TXT cuando termines.">${getNota().replace(/</g, '&lt;')}</textarea>
      <div class="save-status" id="notasStatus"></div>
      <div class="acciones">
        <button id="btnExportTXT">📄 TXT</button>
        <button id="btnExportPDF">🖨️ PDF</button>
        <button id="btnLimpiarNotas">🗑️ Limpiar</button>
      </div>
    `;
    document.body.appendChild(notes);
    document.body.classList.add('notes-on');

    // Auto-save de notas
    const ta = document.getElementById('sidebarNotas');
    const status = document.getElementById('notasStatus');
    let saveTimer;
    ta.addEventListener('input', () => {
      clearTimeout(saveTimer);
      status.textContent = 'Guardando...';
      saveTimer = setTimeout(() => {
        localStorage.setItem(KEY_NOTAS, ta.value);
        status.textContent = '✅ Guardado';
        setTimeout(() => { status.textContent = ''; }, 1500);
      }, 500);
    });

    // Botones de exportación
    document.getElementById('btnExportTXT').onclick = exportarTXT;
    document.getElementById('btnExportPDF').onclick = exportarPDF;
    document.getElementById('btnLimpiarNotas').onclick = () => {
      if (confirm('¿Borrar todas las notas?')) {
        ta.value = '';
        localStorage.setItem(KEY_NOTAS, '');
        status.textContent = '🗑️ Borrado';
        setTimeout(() => { status.textContent = ''; }, 1500);
      }
    };
    const notesPanelClose = document.getElementById('notesPanelClose');
    if (notesPanelClose) {
      notesPanelClose.onclick = () => {
        notes.classList.add('collapsed');
      };
    }

    // === TOGGLE del sidebar DER (notas) ===
    // 1) Click en el header h4 → colapsa/expande
    const headerDer = notes.querySelector('[data-toggle="notes"]');
    const toggleDerIcon = notes.querySelector('.toggle-icon');
    if (headerDer) {
      headerDer.style.cursor = 'pointer';
      // Capture phase: se ejecuta ANTES que cualquier otro handler
      headerDer.addEventListener('click', (e) => {
        const collapsed = notes.classList.toggle('collapsed');
        document.body.classList.toggle('sidebar-collapsed-der', collapsed);
        if (toggleDerIcon) {
          toggleDerIcon.textContent = collapsed ? '◀' : '▶';
        }
      });
    }
    // 2) Botón flotante 📝
    const notesToggle = document.createElement('button');
    notesToggle.className = 'notes-toggle';
    notesToggle.id = 'notesToggle';
    notesToggle.textContent = '📝';
    notesToggle.title = 'Mostrar/ocultar notas';
    notesToggle.onclick = () => {
      const collapsed = notes.classList.toggle('collapsed');
      document.body.classList.toggle('sidebar-collapsed-der', collapsed);
      if (toggleDerIcon) {
        toggleDerIcon.textContent = collapsed ? '◀' : '▶';
      }
    };
    document.body.appendChild(notesToggle);
  }

  // ==================== IR A UN BUG ====================
  function irAlBug(bugId) {
    // Si estamos en la página del Detective, scrollear al bug
    if (window.location.pathname.includes('detective')) {
      const card = document.querySelector(`.bug-card[data-bug="${bugId}"]`);
      if (card) {
        card.scrollIntoView({behavior: 'smooth', block: 'center'});
        // Resaltar
        card.style.transition = 'box-shadow 0.3s';
        card.style.boxShadow = '0 0 0 4px #1877f2, 0 0 0 8px rgba(24, 119, 242, 0.4)';
        setTimeout(() => { card.style.boxShadow = ''; }, 1500);
      }
    } else {
      // Si no estamos, ir al detective con un anchor
      window.location.href = `/static/detective.html#bug-${bugId}`;
    }
  }

  // ==================== INIT ====================
  function render() {
    const resueltos = getDetectiveResueltos();
    const customs = getCustomDBs();

    // Sincronizar con el server (si hay usuario logueado)
    if (!window.RedTeamAuth || !window.RedTeamAuth.usuario) {
      renderSidebarDOM(resueltos, customs);
      return;
    }
    fetch('/api/v1/auth/mi-dashboard').then(r => r.ok ? r.json() : null).then(serverData => {
      if (serverData) {
        const serverBugs = serverData.bugs_resueltos || [];
        const localBugs = JSON.parse(localStorage.getItem(KEY_DETECTIVE) || '[]');
        if (localBugs.length === 0 && serverBugs.length > 0) {
          localStorage.setItem(KEY_DETECTIVE, JSON.stringify(serverBugs));
        }
        const serverDBs = serverData.dbs_custom || [];
        const localDBs = JSON.parse(localStorage.getItem(KEY_CUSTOM_DBS) || '[]');
        if (localDBs.length === 0 && serverDBs.length > 0) {
          localStorage.setItem(KEY_CUSTOM_DBS, JSON.stringify(serverDBs));
        }
        renderSidebarDOM(getDetectiveResueltos(), getCustomDBs());
      } else {
        renderSidebarDOM(resueltos, customs);
      }
    }).catch(() => renderSidebarDOM(resueltos, customs));
  }

  function init() {
    inyectarCSS();
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', render);
    } else {
      render();
    }
  }

  init();
})();
