/* RedTeam Lab v4 — Barra superior de Apariencia (topbar.js)
 * Renderiza una barra sticky arriba del header con todos los controles de apariencia.
 * Reemplaza el panel Apariencia que vivía dentro de la sidebar de Notas.
 * Depende de: theme.js (KEY_TEMA, KEY_MODO, setColorTema, setModo, aplicarTema).
 */
(function () {
  'use strict';

  // No duplicar
  if (document.getElementById('rt-topbar')) return;

  const COLORS = [
    { name: 'azul', hex: '#1877f2' },
    { name: 'verde', hex: '#16a34a' },
    { name: 'rojo', hex: '#dc2626' },
    { name: 'violeta', hex: '#9333ea' },
    { name: 'naranja', hex: '#ea580c' }
  ];

  // Lee de theme.js si está disponible
  const T = window.RedTeamTheme || {};
  const KEY_TEMA = 'redteam-tema';
  const KEY_MODO = 'redteam-modo';
  const KEY_FUENTE = 'rt_fuente';
  const KEY_BRILLO = 'rt_brillo';

  function getTema() {
    try { return localStorage.getItem(KEY_TEMA) || 'azul'; } catch (e) { return 'azul'; }
  }
  function getModo() {
    return 'claro';
  }
  function getFuente() {
    try { return localStorage.getItem(KEY_FUENTE) || 'A'; } catch (e) { return 'A'; }
  }
  function getBrillo() {
    try { return parseInt(localStorage.getItem(KEY_BRILLO) || '100'); } catch (e) { return 100; }
  }

  function aplicarColor(hex) {
    document.documentElement.style.setProperty('--accent', hex);
    document.documentElement.style.setProperty('--color-accent', hex);
  }

  function aplicarBrillo(val) {
    const v = Math.max(50, Math.min(100, val));
    // Atenuar toda la página con un overlay (no afecta la topbar)
    let overlay = document.getElementById('rt-brillo-overlay');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = 'rt-brillo-overlay';
      overlay.style.cssText = 'position:fixed;inset:0;background:black;pointer-events:none;z-index:9999;transition:opacity 0.2s;';
      document.body.appendChild(overlay);
    }
    // 100 = transparente, 50 = 50% negro
    overlay.style.opacity = (100 - v) / 100;
  }

  function aplicarFuente(size) {
    const sizes = { 'A-': '13px', 'A': '15px', 'A+': '17px', 'A++': '19px' };
    const px = sizes[size] || '15px';
    document.body.style.fontSize = px;
    document.documentElement.style.setProperty('--rt-font-size', px);
    document.documentElement.setAttribute('data-font-size', size);
  }

  function aplicarTipografia(tipo) {
    const fonts = {
      'sans': '-apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", sans-serif',
      'mono': '"JetBrains Mono", "SF Mono", Monaco, Consolas, monospace',
      'dyslexic': '"OpenDyslexic", "Comic Sans MS", sans-serif'
    };
    const f = fonts[tipo] || fonts.sans;
    document.body.style.fontFamily = f;
    document.documentElement.style.setProperty('--rt-font-family', f);
    document.documentElement.setAttribute('data-tipografia', tipo);
  }

  function buildBar() {
    const bar = document.createElement('div');
    bar.id = 'rt-topbar';
    bar.className = 'rt-topbar';

    const tema = getTema();
    const modo = getModo();
    const fuente = getFuente();
    const brillo = getBrillo();

    bar.innerHTML = `
      <div class="grp">
        <label>Color</label>
        <div class="color-row" id="rtTopbarColores">
          ${COLORS.map(c => `<div class="color-dot ${c.name === tema ? 'activo' : ''}" data-color="${c.name}" data-hex="${c.hex}" style="background:${c.hex}" title="${c.name}"></div>`).join('')}
        </div>
      </div>
      <div class="sep"></div>
      <div class="grp">
        <label>Fuente</label>
        <div class="toggle-grp" id="rtTopbarFuente">
          <button data-fuente="A-" class="${fuente === 'A-' ? 'activo' : ''}">A-</button>
          <button data-fuente="A" class="${fuente === 'A' ? 'activo' : ''}">A</button>
          <button data-fuente="A+" class="${fuente === 'A+' ? 'activo' : ''}">A+</button>
          <button data-fuente="A++" class="${fuente === 'A++' ? 'activo' : ''}">A++</button>
        </div>
      </div>
      <div class="sep"></div>
      <div class="grp">
        <label>Brillo</label>
        <input class="brightness" id="rtTopbarBrillo" type="range" min="50" max="100" value="${brillo}">
      </div>
      <div class="spacer"></div>
      <div class="grp">
        <label>Tipografía</label>
        <select id="rtTopbarTipografia">
          <option value="sans">Sans</option>
          <option value="mono">Mono</option>
          <option value="dyslexic">Dyslexic</option>
        </select>
      </div>
    `;
    return bar;
  }

  function mount() {
    if (document.getElementById('rt-topbar')) return;
    const bar = buildBar();
    // Insertar al principio del body (arriba de la navbar)
    document.body.insertBefore(bar, document.body.firstChild);

    // Aplicar valores guardados
    aplicarColor((COLORS.find(c => c.name === getTema()) || COLORS[0]).hex);
    aplicarBrillo(getBrillo());
    aplicarFuente(getFuente());
    aplicarTipografia(localStorage.getItem('rt_tipografia') || 'sans');

    // === Handlers ===
    // Modo oscuro desactivado: siempre claro
    document.documentElement.setAttribute('data-modo', 'claro');

    // Color
    document.querySelectorAll('#rtTopbarColores .color-dot').forEach(dot => {
      dot.onclick = () => {
        const name = dot.dataset.color;
        const hex = dot.dataset.hex;
        aplicarColor(hex);
        // No hay función directa en theme.js, guardamos y aplicamos
        localStorage.setItem(KEY_TEMA, name);
        // Si theme.js tiene un método para aplicar, lo usamos
        if (T.aplicarTemaColor) T.aplicarTemaColor(name);
        document.querySelectorAll('#rtTopbarColores .color-dot').forEach(d => d.classList.toggle('activo', d === dot));
      };
    });

    // Fuente
    document.querySelectorAll('#rtTopbarFuente button').forEach(btn => {
      btn.onclick = () => {
        const f = btn.dataset.fuente;
        aplicarFuente(f);
        localStorage.setItem(KEY_FUENTE, f);
        document.querySelectorAll('#rtTopbarFuente button').forEach(b => b.classList.toggle('activo', b === btn));
      };
    });

    // Brillo
    const brilloInput = document.getElementById('rtTopbarBrillo');
    brilloInput.oninput = () => {
      aplicarBrillo(parseInt(brilloInput.value));
      localStorage.setItem(KEY_BRILLO, brilloInput.value);
    };

    // Tipografía
    const tipoSelect = document.getElementById('rtTopbarTipografia');
    // Cargar valor guardado
    const tipoGuardado = localStorage.getItem('rt_tipografia') || 'sans';
    tipoSelect.value = tipoGuardado;
    aplicarTipografia(tipoGuardado);
    tipoSelect.onchange = () => {
      const t = tipoSelect.value;
      aplicarTipografia(t);
      localStorage.setItem('rt_tipografia', t);
    };
  }

  // Esperar a que theme.js monte
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => setTimeout(mount, 50));
  } else {
    setTimeout(mount, 50);
  }
})();
