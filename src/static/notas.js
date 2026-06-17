/* RedTeam Lab v4 — Menú de Notas + Panel Apariencia
 *
 * Se integra DENTRO de la sidebar de Notas (que ya renderiza sidebar.js).
 * sidebar.js crea un <aside class="notes-panel"> con un <h4> y un textarea.
 * Este script ENGANCHA ese panel y le agrega:
 *   - Panel Apariencia (claro/oscuro, color, fuente, tipo) en la parte de arriba
 *   - Menú de 5 opciones (Notas rápidas, Historial, Favoritas, Exportar, Papelera)
 *   - Click en cada opción del menú expande una sección en el cuerpo
 *   - Reemplaza el textarea único original por el sistema de secciones
 *
 * Reutiliza el sistema de localStorage del theme.js (KEY_TEMA, etc).
 */
(function () {
  'use strict';

  // ==================== HELPERS ====================
  const $ = (sel, root) => (root || document).querySelector(sel);
  const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));

  // ==================== DATOS DE LAS SECCIONES ====================
  const SECCIONES = {
    rapidas: {
      icono: '📝',
      titulo: 'Notas rápidas',
      html: function () {
        // El editor real vive en la sidebar del cuaderno. Acá mostramos una vista
        // resumen + atajo para abrir la sección del cuerpo si lo necesita.
        const ta = document.getElementById('sidebarNotas');
        const texto = ta ? ta.value : localStorage.getItem('redteam-notas') || '';
        const preview = texto.slice(0, 300) || 'Sin notas todavía. Escribí en la sidebar de la derecha.';
        return `
          <div class="nota-vista-rapida">
            <p>✏️ <b>El editor de notas está en la sidebar derecha</b> (botón 📝 Cuaderno). Escribí ahí y se guarda solo.</p>
            <div class="nota-preview">
              <h4>Vista previa de lo que tenés:</h4>
              <pre>${preview.replace(/</g, '&lt;')}${texto.length > 300 ? '...' : ''}</pre>
            </div>
            <p class="nota-ayuda">💡 Tip: usá los botones <b>💾 Guardar</b>, <b>⭐ Favorita</b> y <b>🗑️ Limpiar</b> de la sidebar para gestionar tus notas.</p>
          </div>
        `;
      },
      onMount: function () {
        // Nada que montar; el editor está en la sidebar
      },
    },
    historial: {
      icono: '📚',
      titulo: 'Historial de notas',
      html: function () {
        let items = [];
        try { items = JSON.parse(localStorage.getItem('redteam-notas-historial') || '[]'); } catch (e) { items = []; }
        if (items.length === 0) {
          return '<div class="nota-vacio">📭 Sin historial todavía. Hacé click en 💾 Guardar o ⭐ Favorita en el cuaderno.</div>';
        }
        return `
          <div class="nota-lista">
            ${items.map((item, i) => `
              <div class="nota-item" data-historial-idx="${i}">
                <div class="nota-item-fecha">${new Date(item.fecha).toLocaleString('es-AR')}</div>
                <div class="nota-item-texto">${item.texto.slice(0, 200).replace(/</g, '&lt;')}${item.texto.length > 200 ? '...' : ''}</div>
                <button class="nota-item-restaurar" data-idx="${i}">↩ Restaurar</button>
              </div>
            `).join('')}
          </div>
        `;
      },
      onMount: function () {
        document.querySelectorAll('.nota-item-restaurar').forEach(btn => {
          btn.onclick = () => {
            const idx = parseInt(btn.dataset.idx);
            let items = [];
            try { items = JSON.parse(localStorage.getItem('redteam-notas-historial') || '[]'); } catch (e) { items = []; }
            if (items[idx]) {
              const ta = document.getElementById('sidebarNotas');
              if (ta) {
                ta.value = items[idx].texto;
                localStorage.setItem('redteam-notas', items[idx].texto);
                ta.dispatchEvent(new Event('input'));
              }
              if (typeof cerrarSeccion === 'function') cerrarSeccion();
            }
          };
        });
      }
    },
    favoritas: {
      icono: '⭐',
      titulo: 'Favoritas',
      html: function () {
        let items = [];
        try { items = JSON.parse(localStorage.getItem('redteam-notas-favoritas') || '[]'); } catch (e) { items = []; }
        if (items.length === 0) {
          return '<div class="nota-vacio">⭐ Sin favoritas todavía. Escribí en el cuaderno y hacé click en ⭐ Favorita.</div>';
        }
        return `
          <div class="nota-lista">
            ${items.map((item, i) => `
              <div class="nota-item" data-fav-idx="${i}">
                <div class="nota-item-fecha">${new Date(item.fecha).toLocaleString('es-AR')}</div>
                <div class="nota-item-texto">${item.texto.slice(0, 200).replace(/</g, '&lt;')}${item.texto.length > 200 ? '...' : ''}</div>
                <div class="nota-item-acciones">
                  <button class="nota-item-restaurar" data-fav-idx="${i}">↩ Restaurar</button>
                  <button class="nota-item-borrar" data-fav-idx="${i}">🗑️ Borrar</button>
                </div>
              </div>
            `).join('')}
          </div>
        `;
      },
      onMount: function () {
        document.querySelectorAll('.nota-item[data-fav-idx] .nota-item-restaurar').forEach(btn => {
          btn.onclick = () => {
            const idx = parseInt(btn.dataset.favIdx);
            let items = [];
            try { items = JSON.parse(localStorage.getItem('redteam-notas-favoritas') || '[]'); } catch (e) { items = []; }
            if (items[idx]) {
              const ta = document.getElementById('sidebarNotas');
              if (ta) {
                ta.value = items[idx].texto;
                localStorage.setItem('redteam-notas', items[idx].texto);
                ta.dispatchEvent(new Event('input'));
              }
              if (typeof cerrarSeccion === 'function') cerrarSeccion();
            }
          };
        });
        document.querySelectorAll('.nota-item[data-fav-idx] .nota-item-borrar').forEach(btn => {
          btn.onclick = () => {
            const idx = parseInt(btn.dataset.favIdx);
            let items = [];
            try { items = JSON.parse(localStorage.getItem('redteam-notas-favoritas') || '[]'); } catch (e) { items = []; }
            items.splice(idx, 1);
            localStorage.setItem('redteam-notas-favoritas', JSON.stringify(items));
            // Re-render
            const cont = document.getElementById('nota-seccion-cuerpo');
            if (cont && typeof abrirSeccion === 'function') abrirSeccion('favoritas', null);
          };
        });
      }
    },
    exportar: {
      icono: '📤',
      titulo: 'Exportar notas',
      html: function () {
        return `
          <div class="exportar-grid">
            <button class="exportar-btn" data-formato="txt">
              <div class="exportar-icono">📄</div>
              <div class="exportar-label">TXT</div>
              <small>texto plano</small>
            </button>
            <button class="exportar-btn" data-formato="pdf">
              <div class="exportar-icono">🖨️</div>
              <div class="exportar-label">PDF</div>
              <small>para imprimir</small>
            </button>
            <button class="exportar-btn" data-formato="md">
              <div class="exportar-icono">📝</div>
              <div class="exportar-label">Markdown</div>
              <small>editable</small>
            </button>
            <button class="exportar-btn" data-formato="json">
              <div class="exportar-icono">📋</div>
              <div class="exportar-label">JSON</div>
              <small>para backup</small>
            </button>
          </div>
          <p class="nota-ayuda">Elegí el formato para bajar todas tus notas.</p>
        `;
      },
      onMount: function () {
        $$('.exportar-btn').forEach(btn => {
          btn.onclick = () => {
            const formato = btn.dataset.formato;
            const nota = localStorage.getItem('redteam-notas') || '';
            const nombre = `redteam-notas-${new Date().toISOString().slice(0, 10)}.${formato}`;
            let contenido = nota;
            let mime = 'text/plain';
            if (formato === 'json') {
              contenido = JSON.stringify({notas: nota, fecha: new Date().toISOString()}, null, 2);
              mime = 'application/json';
            } else if (formato === 'md') {
              contenido = `# Notas RedTeam Lab\n\n${nota}`;
              mime = 'text/markdown';
            }
            const blob = new Blob([contenido], {type: mime});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = nombre;
            a.click();
            URL.revokeObjectURL(url);
          };
        });
      },
    },
    papelera: {
      icono: '🗑️',
      titulo: 'Papelera',
      html: function () {
        return `
          <p class="nota-ayuda">Las notas borradas aparecerán acá para que las puedas recuperar. (Próximamente)</p>
        `;
      },
    },
  };

  function getNota() {
    return localStorage.getItem('redteam-notas') || '';
  }

  // ==================== PANEL APARIENCIA ====================
  function renderPanelApariencia(host) {
    const KEY_TEMA = 'redteam-tema';
    const KEY_FONTSIZE = 'redteam-fontsize';
    const KEY_FONT = 'redteam-font';
    const KEY_MODO = 'redteam-modo';

    const temaActual = localStorage.getItem(KEY_TEMA) || 'azul';
    const fontsizeActual = localStorage.getItem(KEY_FONTSIZE) || 'normal';
    const fontActual = localStorage.getItem(KEY_FONT) || 'system';
    const modoActual = localStorage.getItem(KEY_MODO) || 'claro';

    const TEMAS = [
      {id: 'azul', label: 'Azul', color: '#1877f2'},
      {id: 'verde', label: 'Verde', color: '#16a34a'},
      {id: 'rojo', label: 'Rojo', color: '#dc2626'},
      {id: 'violeta', label: 'Violeta', color: '#9333ea'},
      {id: 'naranja', label: 'Naranja', color: '#ea580c'},
    ];
    const FONT_SIZES = [
      {id: 'chico', label: 'A-', px: 14},
      {id: 'normal', label: 'A', px: 16},
      {id: 'grande', label: 'A+', px: 18},
      {id: 'xl', label: 'A++', px: 20},
    ];
    const FONT_FAMILIES = [
      {id: 'system', label: 'Sans', family: 'system-ui, sans-serif'},
      {id: 'mono', label: 'Mono', family: 'monospace'},
      {id: 'serif', label: 'Serif', family: 'Georgia, serif'},
      {id: 'dyslexic', label: 'Dislexia', family: 'OpenDyslexic, Comic Sans MS, cursive'},
    ];

    const panel = document.createElement('div');
    panel.className = 'panel-apariencia';
    panel.innerHTML = `
      <h5 class="apariencia-titulo">🎨 Apariencia</h5>

      <div class="apariencia-row">
        <div class="toggle-modo">
          <button class="modo-btn ${modoActual === 'claro' ? 'activo' : ''}" data-modo="claro">☀️</button>
          <button class="modo-btn ${modoActual === 'oscuro' ? 'activo' : ''}" data-modo="oscuro">🌙</button>
        </div>
      </div>

      <div class="apariencia-row">
        <label class="apariencia-label">Color</label>
        <div class="colores-row">
          ${TEMAS.map(t => `
            <button class="color-dot ${t.id === temaActual ? 'activo' : ''}"
                    data-tema="${t.id}" title="${t.label}"
                    style="background:${t.color}"></button>
          `).join('')}
        </div>
      </div>

      <div class="apariencia-row">
        <label class="apariencia-label">Fuente</label>
        <div class="fontsize-row">
          ${FONT_SIZES.map(f => `
            <button class="fontsize-btn ${f.id === fontsizeActual ? 'activo' : ''}"
                    data-fontsize="${f.id}" style="font-size:${f.px}px">${f.label}</button>
          `).join('')}
        </div>
      </div>

      <div class="apariencia-row">
        <label class="apariencia-label">Tipo</label>
        <select class="font-select" data-font>
          ${FONT_FAMILIES.map(f => `
            <option value="${f.id}" ${f.id === fontActual ? 'selected' : ''}>${f.label}</option>
          `).join('')}
        </select>
      </div>
    `;

    // === EVENTOS ===
    panel.querySelectorAll('.modo-btn').forEach(btn => {
      btn.onclick = () => {
        const modo = btn.dataset.modo;
        localStorage.setItem(KEY_MODO, modo);
        document.documentElement.setAttribute('data-modo', modo);
        panel.querySelectorAll('.modo-btn').forEach(b => b.classList.toggle('activo', b === btn));
      };
    });

    panel.querySelectorAll('.color-dot').forEach(btn => {
      btn.onclick = () => {
        const t = btn.dataset.tema;
        localStorage.setItem(KEY_TEMA, t);
        document.documentElement.setAttribute('data-tema', t);
        panel.querySelectorAll('.color-dot').forEach(b => b.classList.toggle('activo', b === btn));
      };
    });

    panel.querySelectorAll('.fontsize-btn').forEach(btn => {
      btn.onclick = () => {
        const fs = btn.dataset.fontsize;
        localStorage.setItem(KEY_FONTSIZE, fs);
        document.documentElement.setAttribute('data-fontsize', fs);
        panel.querySelectorAll('.fontsize-btn').forEach(b => b.classList.toggle('activo', b === btn));
      };
    });

    panel.querySelector('.font-select').onchange = (e) => {
      const f = e.target.value;
      localStorage.setItem(KEY_FONT, f);
      document.documentElement.setAttribute('data-font', f);
    };

    host.appendChild(panel);
  }

  // ==================== MENÚ DE NOTAS ====================
  function renderMenuNotas(host) {
    const menu = document.createElement('ul');
    menu.className = 'menu-notas';
    menu.innerHTML = `
      <li><button class="menu-nota-item activo" data-seccion="rapidas">
        <span class="menu-nota-icono">📝</span>
        <span class="menu-nota-label">Notas rápidas</span>
      </button></li>
      <li><button class="menu-nota-item" data-seccion="historial">
        <span class="menu-nota-icono">📚</span>
        <span class="menu-nota-label">Historial</span>
        <span class="menu-nota-badge">4</span>
      </button></li>
      <li><button class="menu-nota-item" data-seccion="favoritas">
        <span class="menu-nota-icono">⭐</span>
        <span class="menu-nota-label">Favoritas</span>
      </button></li>
      <li><button class="menu-nota-item" data-seccion="exportar">
        <span class="menu-nota-icono">📤</span>
        <span class="menu-nota-label">Exportar</span>
      </button></li>
      <li><button class="menu-nota-item" data-seccion="papelera">
        <span class="menu-nota-icono">🗑️</span>
        <span class="menu-nota-label">Papelera</span>
      </button></li>
    `;
    host.appendChild(menu);

    menu.querySelectorAll('.menu-nota-item').forEach(btn => {
      btn.onclick = () => abrirSeccion(btn.dataset.seccion, btn);
    });
  }

  // ==================== SECCIÓN EN EL CUERPO ====================
  // Renderiza la sección seleccionada (Historial, Favoritas, etc.) en un contenedor
  // que va DESPUÉS del .rt-layout, no adentro del main. Esto evita que los bug-cards
  // del Detective crezcan cuando se abre una sección.
  function ensureContenedorCuerpo() {
    let cont = document.getElementById('nota-seccion-cuerpo');
    if (cont) return cont;
    cont = document.createElement('div');
    cont.id = 'nota-seccion-cuerpo';
    cont.className = 'nota-seccion-cuerpo';
    const layout = document.querySelector('.rt-layout');
    if (layout && layout.parentNode) {
      layout.parentNode.insertBefore(cont, layout.nextSibling);
    } else {
      document.body.appendChild(cont);
    }
    return cont;
  }

  function abrirSeccion(seccionId, btn) {
    const data = SECCIONES[seccionId];
    if (!data) return;

    // Marcar botón activo
    document.querySelectorAll('.menu-nota-item').forEach(b => b.classList.remove('activo'));
    if (btn) btn.classList.add('activo');

    // Renderizar contenido
    const cont = ensureContenedorCuerpo();
    cont.innerHTML = `
      <div class="nota-seccion-header">
        <span class="nota-seccion-icono">${data.icono}</span>
        <span class="nota-seccion-titulo">${data.titulo}</span>
        <button class="nota-seccion-cerrar" aria-label="cerrar">×</button>
      </div>
      <div class="nota-seccion-contenido">${data.html()}</div>
    `;
    cont.classList.remove('oculto');

    cont.querySelector('.nota-seccion-cerrar').onclick = cerrarSeccion;

    if (data.onMount) data.onMount();

    // Scroll suave
    cont.scrollIntoView({behavior: 'smooth', block: 'nearest'});
  }

  function cerrarSeccion() {
    const cont = document.getElementById('nota-seccion-cuerpo');
    if (cont) cont.classList.add('oculto');
    document.querySelectorAll('.menu-nota-item').forEach(b => b.classList.remove('activo'));
  }

  // ==================== INIT ====================
  function init() {
    // Buscar el panel de notas (que sidebar.js ya creó)
    const notesPanel = document.querySelector('.notes-panel');
    const sidebarIzq = document.querySelector('.sidebar');
    const main = document.querySelector('main');
    if (!notesPanel || !main) {
      // Si sidebar.js no creó los elementos, reintentar en 500ms
      setTimeout(init, 500);
      return;
    }

    // === CREAR WRAPPER DE 2 COLUMNAS (cuerpo + notas; sidebar IZQ abajo como franja) ===
    if (!document.querySelector('.rt-layout')) {
      // Crear wrapper
      const wrapper = document.createElement('div');
      wrapper.className = 'rt-layout';
      // 1. Mover el main adentro (cuerpo)
      main.remove();
      wrapper.appendChild(main);
      // 2. Mover la sidebar DER (notas)
      notesPanel.remove();
      wrapper.appendChild(notesPanel);
      // 3. La sidebar IZQ va al FINAL, ocupa todo el ancho (span 2)
      if (sidebarIzq) {
        sidebarIzq.remove();
        wrapper.appendChild(sidebarIzq);
      }
      // Insertar el wrapper después de la navbar
      const navbar = document.querySelector('header') || document.querySelector('nav');
      if (navbar && navbar.parentNode) {
        navbar.parentNode.insertBefore(wrapper, navbar.nextSibling);
      } else {
        document.body.appendChild(wrapper);
      }
    }

    // El textarea y los botones del cuaderno (sidebar.js) se renderizan en la sidebar.
    // Acá solo agregamos el menú de navegación (Historial, Favoritas, etc.) DESPUÉS del h4.
    const h4 = notesPanel.querySelector('h4');
    if (h4 && h4.parentNode) {

      // Crear contenedor arriba de todo
      const wrap = document.createElement('div');
      wrap.className = 'notas-contenedor';
      // Mover el h4 + textarea + acciones adentro del wrap
      while (notesPanel.firstChild) wrap.appendChild(notesPanel.firstChild);
      // NOTA: Panel Apariencia ahora vive en la topbar (topbar.js). No se renderiza aquí.
      // Agregar separador y menú de notas DESPUÉS del h4
      const sep = document.createElement('hr');
      sep.className = 'notas-separador';
      h4.after(sep);
      const menuWrap = document.createElement('div');
      menuWrap.className = 'menu-notas-wrap';
      renderMenuNotas(menuWrap);
      sep.after(menuWrap);
      // Volver a poner el wrap dentro del notesPanel
      notesPanel.appendChild(wrap);
    }

    // Abrir sección default: notas rápidas
    setTimeout(() => {
      const defaultBtn = document.querySelector('.menu-nota-item[data-seccion="rapidas"]');
      if (defaultBtn) abrirSeccion('rapidas', defaultBtn);
    }, 200);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    setTimeout(init, 100);  // esperar a que sidebar.js termine
  }
})();
