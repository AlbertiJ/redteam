/* RedTeam Lab v4 — Sidebar de Progreso
 * Muestra en el lateral izquierdo:
 * - Progreso del Detective de Bugs
 * - DBs custom del usuario
 * - Tests pasados
 * - Tareas del usuario
 *
 * Se inyecta automáticamente si la página tiene header.
 */
(function () {
  'use strict';

  const KEY_DETECTIVE = 'redteam-detective-resueltos';
  const KEY_CUSTOM_DBS = 'redteam-custom-dbs';
  const KEY_NOTAS = 'redteam-notas';

  function inyectarCSS() {
    if (document.getElementById('sidebar-css')) return;
    const css = `
      .sidebar {
        position: fixed;
        top: 80px;
        left: 16px;
        width: 240px;
        max-height: calc(100vh - 100px);
        overflow-y: auto;
        background: var(--bg-card, #ffffff);
        border: 1px solid var(--border-soft, #dadde1);
        border-radius: 10px;
        padding: 1rem 1.1rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        z-index: 100;
        font-family: var(--font-family-base, sans-serif);
        font-size: 0.88rem;
      }
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
      .sidebar-bugs {
        list-style: none;
        padding: 0;
        margin: 0;
      }
      .sidebar-bugs li {
        display: flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.25rem 0;
        font-size: 0.82rem;
        color: var(--text-muted, #65676b);
      }
      .sidebar-bugs li.resuelto { color: var(--color-exito, #10b981); }
      .sidebar-bugs li .check { width: 14px; display: inline-block; }
      .sidebar-notas textarea {
        width: 100%;
        min-height: 70px;
        font-family: inherit;
        font-size: 0.85rem;
        padding: 0.4rem;
        border: 1px solid var(--border-soft, #dadde1);
        border-radius: 4px;
        resize: vertical;
        background: var(--bg-soft, #f7f8fa);
        color: var(--text-main, #1c1e21);
      }
      .sidebar-notas .save-status {
        color: var(--color-exito, #10b981);
        font-size: 0.78rem;
        margin-top: 0.2rem;
        height: 1em;
      }
      .sidebar-toggle {
        position: fixed;
        bottom: 16px;
        left: 16px;
        background: var(--accent, #1877f2);
        color: white;
        border: none;
        border-radius: 50%;
        width: 44px;
        height: 44px;
        font-size: 1.2rem;
        cursor: pointer;
        z-index: 101;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      }
      .sidebar-toggle:hover { transform: scale(1.05); }
      .sidebar.collapsed { display: none; }
      /* Mover contenido principal cuando sidebar está visible */
      @media (min-width: 1100px) {
        body.sidebar-on main { margin-left: 270px; transition: margin 0.2s; }
      }
    `;
    const style = document.createElement('style');
    style.id = 'sidebar-css';
    style.textContent = css;
    document.head.appendChild(style);
  }

  function getDetectiveResueltos() {
    try {
      return JSON.parse(localStorage.getItem(KEY_DETECTIVE) || '[]');
    } catch (e) { return []; }
  }

  function getCustomDBs() {
    try {
      return JSON.parse(localStorage.getItem(KEY_CUSTOM_DBS) || '[]');
    } catch (e) { return []; }
  }

  function renderSidebar() {
    const resueltos = getDetectiveResueltos();
    const customs = getCustomDBs();
    const nota = localStorage.getItem(KEY_NOTAS) || '';

    // Sincronizar con el server (si hay cookie de sesión)
    // Usamos un flag para no hacer fetch en cada render
    if (!window.RedTeamAuth || !window.RedTeamAuth.usuario) {
      renderSidebarDOM(resueltos, customs, nota);
      return;
    }
    // Traer dashboard del server para mantener sincronía
    fetch('/api/v1/auth/mi-dashboard').then(r => r.ok ? r.json() : null).then(serverData => {
      if (serverData) {
        // Si el server tiene datos, usar esos como fuente de verdad
        // pero solo si el localStorage está vacío (primera vez)
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
        // Re-leer del localStorage
        renderSidebarDOM(
          getDetectiveResueltos(),
          getCustomDBs(),
          nota
        );
      } else {
        renderSidebarDOM(resueltos, customs, nota);
      }
    }).catch(() => renderSidebarDOM(resueltos, customs, nota));
  }

  function renderSidebarDOM(resueltos, customs, nota) {

    const bugs = [
      {id: '1a', nombre: '1A · URL duplicada'},
      {id: '1b', nombre: '1B · URL concatenada'},
      {id: '2a', nombre: '2A · Input vacío'},
      {id: '2b', nombre: '2B · Tipo incorrecto'},
      {id: '3a', nombre: '3A · SQLi SELECT'},
      {id: '3b', nombre: '3B · SQLi INSERT'},
      {id: '4a', nombre: '4A · Credenciales'},
      {id: '4b', nombre: '4B · Token sin exp'},
      {id: '5a', nombre: '5A · Stack trace'},
      {id: '5b', nombre: '5B · Endpoint debug'},
    ];

    const sidebar = document.createElement('aside');
    sidebar.className = 'sidebar';
    sidebar.id = 'sidebar';
    sidebar.innerHTML = `
      <div class="sidebar-section">
        <h4>📊 Tu avance</h4>
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
        <h4>🪲 Detective de Bugs</h4>
        <ul class="sidebar-bugs">
          ${bugs.map(b => `
            <li class="${resueltos.includes(b.id) ? 'resuelto' : ''}">
              <span class="check">${resueltos.includes(b.id) ? '✅' : '⬜'}</span>
              ${b.nombre}
            </li>
          `).join('')}
        </ul>
      </div>

      <div class="sidebar-section sidebar-notas">
        <h4>📝 Tus notas</h4>
        <textarea id="sidebarNotas" placeholder="Anotá lo que quieras... se guarda solo.">${nota}</textarea>
        <div class="save-status" id="notasStatus"></div>
      </div>

      <div class="sidebar-section">
        <h4>🔗 Atajos</h4>
        <div class="sidebar-stat"><a href="/static/practicas.html" style="color:var(--accent);text-decoration:none;">🎵 Práctica</a></div>
        <div class="sidebar-stat"><a href="/static/detective.html" style="color:var(--accent);text-decoration:none;">🪲 Detective</a></div>
        <div class="sidebar-stat"><a href="/static/dbbuilder.html" style="color:var(--accent);text-decoration:none;">🗄️ DB Builder</a></div>
        <div class="sidebar-stat"><a href="/static/wizard.html" style="color:var(--accent);text-decoration:none;">📋 Cargar DB</a></div>
      </div>
    `;

    document.body.appendChild(sidebar);
    document.body.classList.add('sidebar-on');

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

    // Toggle button
    const toggle = document.createElement('button');
    toggle.className = 'sidebar-toggle';
    toggle.id = 'sidebarToggle';
    toggle.textContent = '📊';
    toggle.title = 'Mostrar/ocultar panel';
    toggle.onclick = () => {
      sidebar.classList.toggle('collapsed');
    };
    document.body.appendChild(toggle);
  }

  function init() {
    inyectarCSS();
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', renderSidebar);
    } else {
      renderSidebar();
    }
  }

  init();
})();
