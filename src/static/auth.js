/* RedTeam Lab v4 — Sistema de Auth + Tracking
 * Inyecta en la nav:
 * - Si NO hay cookie: input "Hola, soy ___" con botón "Entrar"
 * - Si HAY cookie: muestra "👤 juan" + botón "📊 Mi panel" + botón "🚪 Cerrar sesión"
 *
 * Trackea tiempo activo: cada 60s manda sumar-tiempo al server.
 * Al cerrar sesión: POST /logout con la duración total.
 */
(function () {
  'use strict';

  const COOKIE_NAME = 'rt_usuario';
  let usuario = null;
  let sesionInicio = null;
  let cronInterval = null;
  let ultimoSumado = 0;

  // ==================== HELPERS ====================

  function getCookie(name) {
    const m = document.cookie.match(new RegExp('(^|; )' + name + '=([^;]*)'));
    return m ? decodeURIComponent(m[2]) : null;
  }

  // Persistencia adicional en sessionStorage (porque la cookie rt_usuario es httponly
  // y el JS no puede leerla directamente). Lo sincronizamos cuando el server responde.
  const SESSION_KEY = 'rt_session_usuario';
  function getSessionUsuario() {
    // Prioridad: sessionStorage > cookie si está disponible
    return sessionStorage.getItem(SESSION_KEY) || getCookie('rt_usuario_legible');
  }

  function borrarCookie(name) {
    document.cookie = name + '=; Path=/; Max-Age=0';
  }

  function formatearTiempo(seg) {
    if (seg < 60) return seg + 's';
    if (seg < 3600) return Math.floor(seg / 60) + 'min ' + (seg % 60) + 's';
    return Math.floor(seg / 3600) + 'h ' + Math.floor((seg % 3600) / 60) + 'min';
  }

  // ==================== AUTH ====================

  async function login(nombre) {
    const r = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({nombre})
    });
    if (!r.ok) {
      const err = await r.json();
      throw new Error(err.detail || 'Error al loguear');
    }
    return r.json();
  }

  async function logout() {
    if (!usuario) return;
    const duracion = Math.floor((Date.now() - sesionInicio) / 1000) + ultimoSumado;
    try {
      await fetch('/api/v1/auth/logout', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({nombre: usuario, duracion_segundos: duracion})
      });
    } catch (e) {
      console.warn('Error al cerrar sesión:', e);
    }
    borrarCookie(COOKIE_NAME);
    usuario = null;
    sesionInicio = null;
    ultimoSumado = 0;
    if (cronInterval) clearInterval(cronInterval);
    renderNav();
  }

  async function fetchDashboard() {
    const r = await fetch('/api/v1/auth/mi-dashboard');
    if (!r.ok) return null;
    return r.json();
  }

  // ==================== UI ====================

  function inyectarCSS() {
    if (document.getElementById('auth-css')) return;
    const css = `
      .auth-widget {
        display: flex;
        align-items: center;
        gap: 0.4rem;
        font-family: var(--font-family-base, sans-serif);
      }
      .auth-widget input.nombre {
        padding: 0.3rem 0.6rem;
        border: 1px solid var(--border-soft, #dadde1);
        border-radius: 4px;
        font-size: 0.88rem;
        background: var(--bg-input, #fff);
        color: var(--text-main, #1c1e21);
        width: 130px;
        font-family: inherit;
      }
      .auth-widget input.nombre:focus {
        outline: none;
        border-color: var(--accent, #1877f2);
      }
      .auth-widget button {
        padding: 0.3rem 0.6rem;
        border-radius: 4px;
        font-size: 0.82rem;
        cursor: pointer;
        border: 1px solid var(--border-soft, #dadde1);
        background: var(--accent, #1877f2);
        color: white;
        font-family: inherit;
      }
      .auth-widget button.entrar { background: var(--accent, #1877f2); }
      .auth-widget button.entrar:hover { background: var(--accent-hover, #166fe5); }
      .auth-widget button.panel { background: transparent; color: var(--accent, #1877f2); }
      .auth-widget button.panel:hover { background: var(--accent-soft, #e7f3ff); }
      .auth-widget button.logout { background: transparent; color: var(--color-fallo, #b91c1c); border-color: var(--color-fallo, #b91c1c); }
      .auth-widget button.logout:hover { background: #fee2e2; }
      .auth-widget .hola { color: var(--text-muted, #65676b); font-size: 0.88rem; }
      .auth-widget .usuario {
        font-weight: 700;
        color: var(--accent, #1877f2);
        font-size: 0.92rem;
      }
      .auth-modal-bg {
        position: fixed; top:0; left:0; right:0; bottom:0;
        background: rgba(0,0,0,0.5);
        z-index: 10000;
        display: flex; align-items: center; justify-content: center;
        animation: auth-fade 0.2s;
      }
      .auth-modal {
        background: var(--bg-card, #fff);
        border-radius: 12px;
        padding: 1.5rem 1.8rem;
        max-width: 460px;
        width: 90%;
        box-shadow: 0 12px 48px rgba(0,0,0,0.25);
        animation: auth-pop 0.25s;
      }
      .auth-modal h3 { margin: 0 0 0.6rem 0; color: var(--accent, #1877f2); }
      .auth-modal .stat-row { display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid var(--border-soft, #f0f2f5); }
      .auth-modal .stat-row strong { color: var(--text-main); }
      .auth-modal .stat-row span { color: var(--text-muted, #65676b); }
      .auth-modal .pendientes { background: #fffbeb; border-radius: 6px; padding: 0.6rem 0.8rem; margin-top: 0.8rem; }
      .auth-modal .pendientes strong { color: #92400e; }
      .auth-modal .acciones { display: flex; gap: 0.4rem; margin-top: 1rem; justify-content: flex-end; }
      .auth-modal .err { color: var(--color-fallo, #b91c1c); font-size: 0.88rem; margin-top: 0.4rem; }
      @keyframes auth-fade { from {opacity:0;} to {opacity:1;} }
      @keyframes auth-pop { from {opacity:0; transform: translateY(-10px);} to {opacity:1; transform: translateY(0);} }
    `;
    const style = document.createElement('style');
    style.id = 'auth-css';
    style.textContent = css;
    document.head.appendChild(style);
  }

  function renderNav() {
    const cont = document.getElementById('auth-widget-mount');
    if (!cont) return;
    if (usuario) {
      cont.innerHTML = `
        <div class="auth-widget">
          <span class="hola">👤</span>
          <span class="usuario">${usuario}</span>
          <button class="panel" id="authPanelBtn">📊 Mi panel</button>
          <button class="logout" id="authLogoutBtn">🚪 Cerrar sesión</button>
        </div>
      `;
      document.getElementById('authPanelBtn').onclick = abrirPanel;
      document.getElementById('authLogoutBtn').onclick = () => {
        if (confirm('¿Cerrar sesión? Tu tiempo y progreso se guardan.')) {
          logout();
        }
      };
    } else {
      cont.innerHTML = `
        <div class="auth-widget">
          <span class="hola">Hola, soy</span>
          <input class="nombre" id="authNombreInput" placeholder="tu nombre" maxlength="30" />
          <button class="entrar" id="authLoginBtn">Entrar</button>
        </div>
      `;
      const input = document.getElementById('authNombreInput');
      const btn = document.getElementById('authLoginBtn');
      const doLogin = async () => {
        const nombre = input.value.trim();
        if (!nombre) { input.focus(); return; }
        try {
          const res = await login(nombre);
          usuario = res.nombre;
          // Persistir en sessionStorage (sobrevive a refresh y a abrir otras pestañas)
          sessionStorage.setItem(SESSION_KEY, res.nombre);
          sesionInicio = Date.now();
          ultimoSumado = 0;
          iniciarCron();
          renderNav();
        } catch (e) {
          alert('Error: ' + e.message);
        }
      };
      btn.onclick = doLogin;
      input.onkeypress = (e) => { if (e.key === 'Enter') doLogin(); };
    }
  }

  function inyectarMount() {
    // Inyectar un mount point en la nav (al final de header nav)
    const nav = document.querySelector('header nav');
    if (!nav) return;
    if (document.getElementById('auth-widget-mount')) return;
    const li = document.createElement('div');
    li.id = 'auth-widget-mount';
    li.style.marginLeft = 'auto';
    nav.appendChild(li);
  }

  async function abrirPanel() {
    // Cerrar si ya hay uno
    document.querySelectorAll('.auth-modal-bg').forEach(el => el.remove());

    const data = await fetchDashboard();
    if (!data) {
      alert('No se pudo obtener tu dashboard. Hacé login de nuevo.');
      return;
    }

    const modal = document.createElement('div');
    modal.className = 'auth-modal-bg';
    modal.onclick = (e) => { if (e.target === modal) modal.remove(); };
    modal.innerHTML = `
      <div class="auth-modal" onclick="event.stopPropagation()">
        <h3>📊 Tu panel — ${data.nombre}</h3>
        <div class="stat-row"><span>⏱️ Tiempo total en plataforma</span><strong>${data.tiempo_total_legible}</strong></div>
        <div class="stat-row"><span>🪲 Detective de Bugs</span><strong>${data.progreso_detective} resueltos</strong></div>
        <div class="stat-row"><span>💾 DBs custom creadas</span><strong>${data.total_dbs_custom}</strong></div>
        <div class="stat-row"><span>📅 Dado de alta</span><strong>${data.fecha_alta.split('T')[0]}</strong></div>
        <div class="stat-row"><span>🕐 Última sesión</span><strong>${data.ultima_sesion ? data.ultima_sesion.split('T')[0] : 'nunca'}</strong></div>
        <div class="pendientes">
          <strong>📋 Pendientes:</strong>
          ${data.bugs_pendientes.length === 0
            ? '<div>🎉 ¡No tenés bugs pendientes! Ya resolviste todo el Detective.</div>'
            : '<div>Bugs que faltan: ' + data.bugs_pendientes.join(', ') + '</div>'}
        </div>
        <div class="acciones">
          <button class="panel" id="authCerrarPanel">Cerrar</button>
          <button class="logout" id="authCerrarSesion">🚪 Cerrar sesión</button>
        </div>
      </div>
    `;
    document.body.appendChild(modal);
    document.getElementById('authCerrarPanel').onclick = () => modal.remove();
    document.getElementById('authCerrarSesion').onclick = () => {
      if (confirm('¿Cerrar sesión? Tu tiempo y progreso se guardan.')) {
        modal.remove();
        logout();
      }
    };
  }

  // ==================== CRON DE ACTIVIDAD ====================

  function iniciarCron() {
    if (cronInterval) clearInterval(cronInterval);
    cronInterval = setInterval(async () => {
      if (!usuario) return;
      // Sumar 60 segundos al contador local
      ultimoSumado += 60;
      try {
        await fetch('/api/v1/auth/sumar-tiempo', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({nombre: usuario, duracion_segundos: 60})
        });
      } catch (e) { /* silencioso */ }
    }, 60000);
  }

  // ==================== INIT ====================

  function init() {
    inyectarCSS();
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => {
        inyectarMount();
        renderNav();
      });
    } else {
      inyectarMount();
      renderNav();
    }
  }

  // Auto-recuperar sesión: sessionStorage (persistente) > cookie legible > cookie httponly
  const sesionGuardada = getSessionUsuario();
  if (sesionGuardada) {
    usuario = sesionGuardada;
    sesionInicio = Date.now();
    ultimoSumado = 0;
    iniciarCron();
    // También guardamos en sessionStorage por las dudas
    sessionStorage.setItem(SESSION_KEY, sesionGuardada);
  }

  init();

  // Exponer para que otros scripts puedan saber
  window.RedTeamAuth = {
    get usuario() { return usuario; },
    formatearTiempo,
    abrirPanel,
    logout,
  };
})();
