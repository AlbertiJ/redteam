/* RedTeam Lab v4 — Tour Interactivo
 * Guía al usuario por la página actual. Como cuando entrás a Canvas.
 *
 * Uso:
 *   <button id="tourBtn">🎓 Tour</button>
 *   <script src="/static/tour.js"></script>
 *   <script>RedTeamTour.start('index')</script>  // arranca el tour del index
 *
 * El tour se define por página. Cada tour tiene varios "pasos" que apuntan
 * a un selector CSS y muestran un mensaje.
 */
(function () {
  'use strict';

  // ==================== DEFINICIÓN DE TOURS ====================

  const TOURS = {
    'index': {
      titulo: '🎓 Tour: Pantalla principal',
      pasos: [
        {
          selector: 'header',
          titulo: '¿Qué es RedTeam Lab?',
          texto: 'Es un laboratorio de pentesting ético. Acá vas a aprender a encontrar bugs en APIs.',
        },
        {
          selector: '.intro',
          titulo: 'Bienvenida',
          texto: 'Acá te dice el objetivo. Diseñado para cadetes (sin experiencia previa).',
        },
        {
          selector: '.bloque-grid',
          titulo: '3 formas de empezar',
          texto: 'DBs precargadas, cargar tu propia DB, o detective de bugs. Elegí la que te llame.',
        },
        {
          selector: '.bright-btn',
          titulo: 'Brillo y tema',
          texto: 'Click acá si te molesta el brillo. Y en el botón 🎨 Tema cambiás colores, fuentes y tamaño de letra.',
        },
      ],
    },

    'practicas': {
      titulo: '🎓 Tour: Práctica',
      pasos: [
        {
          selector: '.bloque',
          titulo: 'DBs precargadas',
          texto: 'Estas 7 DBs ya están listas. Hacé click en cualquier card para explorarla.',
        },
        {
          selector: '.bloque:nth-child(1) a',
          titulo: 'Click para explorar',
          texto: 'Apretá acá para ir al DB Builder con la DB filtrada. Probá con Música, Películas, etc.',
        },
        {
          selector: '.bright-btn',
          titulo: 'Si necesitás descansar la vista',
          texto: 'Click acá para bajar el brillo. Se aplica a todo el sitio.',
        },
      ],
    },

    'dbbuilder': {
      titulo: '🎓 Tour: DB Builder',
      pasos: [
        {
          selector: '.dbbuilder-section',
          titulo: 'Las 7 DBs precargadas',
          texto: 'Hacé click en cualquiera para abrir el visor.',
        },
        {
          selector: '#visorDB',
          titulo: 'Visor de la DB',
          texto: 'Acá ves los datos, los campos, y podés hacer consultas por URL. Las placeholders son contextuales a la DB que abriste.',
        },
        {
          selector: '#consFiltro',
          titulo: 'Filtro WHERE',
          texto: 'Probá filtros tipo "artista = \'Pink Floyd\'" o "anio = 1973". Pegale al endpoint directamente.',
        },
        {
          selector: '#seccionCustom',
          titulo: 'DBs custom',
          texto: 'Acá podés armar tu propia DB. 3 slots. Mín 3 campos, máx 100. El primero DEBE llamarse "id".',
        },
      ],
    },

    'wizard': {
      titulo: '🎓 Tour: Cargar DB',
      pasos: [
        {
          selector: '#btnEjemplo',
          titulo: 'Botón mágico',
          texto: 'Si no sabés cómo escribir el JSON, click acá. Te carga un ejemplo válido que podés modificar.',
        },
        {
          selector: '#jsonInput',
          titulo: 'Tu JSON',
          texto: 'Pegá acá un objeto JSON con: nombre (string), campos (array), datos (array de objetos). El primer campo debe ser "id".',
        },
        {
          selector: 'button[type="submit"]',
          titulo: 'Cargar DB',
          texto: 'Click para validar y crear. Si hay error, te dice exactamente qué línea y qué caracter está mal.',
        },
      ],
    },

    'detective': {
      titulo: '🎓 Tour: Detective de Bugs',
      pasos: [
        {
          selector: '.intro',
          titulo: 'Cómo funciona',
          texto: '10 bugs en 5 grupos. Cada bug tiene una pista, pasos accionables, código malo vs bueno. Tu progreso se guarda en este navegador.',
        },
        {
          selector: '.bug-card',
          titulo: 'Una card de bug',
          texto: 'Borde naranja = no resuelto. Click en "Marcar como resuelto" cuando lo arregles. Verde = resuelto.',
        },
        {
          selector: '.bug-pasos',
          titulo: 'Pasos concretos',
          texto: 'Cada bug te dice QUÉ archivo abrir, DÓNDE buscar, QUÉ cambiar. No más "mirá la concatenación" sin contexto.',
        },
        {
          selector: '#btnReset',
          titulo: 'Resetear progreso',
          texto: 'Si querés empezar de cero, click acá. Te pide confirmación.',
        },
      ],
    },

    'historial': {
      titulo: '🎓 Tour: Historial',
      pasos: [
        {
          selector: '.historial-grid',
          titulo: 'Bitácora honesta',
          texto: 'Acá cuento qué hice yo (Mavis) y qué corrigió Juan. Es un diario abierto del proyecto.',
        },
        {
          selector: '.resumen',
          titulo: 'Resumen del flujo',
          texto: 'Lo que funciona, lo que no, y la regla de oro: no subir nada que no ande.',
        },
      ],
    },
  };

  // ==================== MOTOR DEL TOUR ====================

  let overlay = null;
  let tooltip = null;
  let currentTour = null;
  let currentStep = 0;

  function inyectarCSS() {
    if (document.getElementById('tour-css')) return;
    const css = `
      .tour-overlay {
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(0, 0, 0, 0.55);
        z-index: 9998;
        animation: tour-fade 0.25s ease;
      }
      .tour-tooltip {
        position: absolute;
        background: #ffffff;
        border: 1px solid #1877f2;
        border-radius: 10px;
        padding: 1.2rem 1.4rem;
        max-width: 380px;
        z-index: 9999;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
        animation: tour-pop 0.3s ease;
        font-family: var(--font-family-base, sans-serif);
      }
      .tour-tooltip h4 {
        margin: 0 0 0.4rem 0;
        color: #1877f2;
        font-size: 1.05rem;
        display: flex;
        align-items: center;
        gap: 0.4rem;
      }
      .tour-tooltip p {
        margin: 0 0 0.8rem 0;
        color: #1c1e21;
        font-size: 0.95rem;
        line-height: 1.5;
      }
      .tour-tooltip .tour-controles {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 0.5rem;
      }
      .tour-tooltip .tour-paso-num {
        color: #65676b;
        font-size: 0.85rem;
      }
      .tour-tooltip button {
        background: #1877f2;
        color: white;
        border: none;
        padding: 0.4rem 0.8rem;
        border-radius: 5px;
        cursor: pointer;
        font-size: 0.88rem;
        font-family: inherit;
      }
      .tour-tooltip button:hover { background: #166fe5; }
      .tour-tooltip button.tour-saltar {
        background: transparent;
        color: #65676b;
        padding: 0.4rem 0.5rem;
      }
      .tour-tooltip button.tour-saltar:hover { color: #b91c1c; }
      .tour-tooltip button.tour-anterior { background: #f0f2f5; color: #1c1e21; }
      .tour-tooltip button.tour-anterior:hover { background: #e4e6e9; }
      .tour-highlight {
        position: relative;
        z-index: 9999;
        box-shadow: 0 0 0 4px #1877f2, 0 0 0 8px rgba(24, 119, 242, 0.3);
        border-radius: 6px;
        transition: all 0.2s;
      }
      @keyframes tour-fade { from {opacity: 0;} to {opacity: 1;} }
      @keyframes tour-pop {
        from {opacity: 0; transform: translateY(-8px);}
        to {opacity: 1; transform: translateY(0);}
      }
    `;
    const style = document.createElement('style');
    style.id = 'tour-css';
    style.textContent = css;
    document.head.appendChild(style);
  }

  function crearOverlay() {
    overlay = document.createElement('div');
    overlay.className = 'tour-overlay';
    document.body.appendChild(overlay);
  }

  function crearTooltip() {
    tooltip = document.createElement('div');
    tooltip.className = 'tour-tooltip';
    document.body.appendChild(tooltip);
  }

  function highlightElement(selector) {
    document.querySelectorAll('.tour-highlight').forEach(el => el.classList.remove('tour-highlight'));
    const el = document.querySelector(selector);
    if (!el) return null;
    el.classList.add('tour-highlight');
    el.scrollIntoView({behavior: 'smooth', block: 'center'});
    return el;
  }

  function posicionarTooltip(target) {
    if (!target || !tooltip) return;
    const rect = target.getBoundingClientRect();
    const tooltipRect = tooltip.getBoundingClientRect();
    // Posicionar debajo del elemento
    let top = rect.bottom + window.scrollY + 12;
    let left = rect.left + window.scrollX;
    // Si no entra abajo, poner arriba
    if (top + tooltipRect.height > window.scrollY + window.innerHeight) {
      top = rect.top + window.scrollY - tooltipRect.height - 12;
    }
    // Si se va a la derecha, ajustar
    if (left + tooltipRect.width > window.scrollX + window.innerWidth - 20) {
      left = window.scrollX + window.innerWidth - tooltipRect.width - 20;
    }
    tooltip.style.top = top + 'px';
    tooltip.style.left = Math.max(20, left) + 'px';
  }

  function mostrarPaso(idx) {
    if (!currentTour) return;
    const paso = currentTour.pasos[idx];
    if (!paso) {
      terminar();
      return;
    }
    currentStep = idx;
    const target = highlightElement(paso.selector);
    if (!target) {
      // Si no encuentra el elemento, salta al siguiente
      mostrarPaso(idx + 1);
      return;
    }
    tooltip.innerHTML = `
      <h4>${paso.titulo}</h4>
      <p>${paso.texto}</p>
      <div class="tour-controles">
        <button class="tour-saltar" data-accion="saltar">Salir del tour</button>
        <span class="tour-paso-num">${idx + 1} de ${currentTour.pasos.length}</span>
        <div style="display:flex; gap:0.3rem;">
          ${idx > 0 ? '<button class="tour-anterior" data-accion="anterior">← Atrás</button>' : ''}
          <button data-accion="siguiente">${idx === currentTour.pasos.length - 1 ? '✓ Terminé' : 'Siguiente →'}</button>
        </div>
      </div>
    `;
    // Bindear botones
    tooltip.querySelectorAll('button').forEach(btn => {
      btn.onclick = (e) => {
        e.stopPropagation();
        const accion = btn.dataset.accion;
        if (accion === 'siguiente') mostrarPaso(idx + 1);
        else if (accion === 'anterior') mostrarPaso(idx - 1);
        else if (accion === 'saltar') terminar();
      };
    });
    // Posicionar después de renderizar
    setTimeout(() => posicionarTooltip(target), 50);
  }

  function terminar() {
    if (overlay) overlay.remove();
    if (tooltip) tooltip.remove();
    document.querySelectorAll('.tour-highlight').forEach(el => el.classList.remove('tour-highlight'));
    overlay = null;
    tooltip = null;
    currentTour = null;
  }

  // ==================== API PÚBLICA ====================

  function start(pageKey) {
    // Si no se pasa key, intentar autodetectar
    if (!pageKey) {
      const path = window.location.pathname;
      if (path.includes('wizard')) pageKey = 'wizard';
      else if (path.includes('practicas')) pageKey = 'practicas';
      else if (path.includes('dbbuilder')) pageKey = 'dbbuilder';
      else if (path.includes('detective')) pageKey = 'detective';
      else if (path.includes('historial')) pageKey = 'historial';
      else pageKey = 'index';
    }
    const tour = TOURS[pageKey];
    if (!tour) {
      console.warn(`[tour] No hay tour definido para "${pageKey}"`);
      return;
    }
    // Si ya hay un tour activo, terminarlo
    if (currentTour) terminar();
    currentTour = tour;
    currentStep = 0;
    inyectarCSS();
    crearOverlay();
    crearTooltip();
    mostrarPaso(0);
  }

  // Exponer
  window.RedTeamTour = {
    start,
    stop: terminar,
    listar: () => Object.keys(TOURS),
  };

  // Inyectar botón "🎓 Tour" en la nav
  function inyectarBotonTour() {
    const nav = document.querySelector('header nav');
    if (!nav || document.getElementById('tourBtn')) return;
    const btn = document.createElement('button');
    btn.id = 'tourBtn';
    btn.className = 'bright-btn';
    btn.textContent = '🎓 Tour';
    btn.title = 'Tour guiado por esta página';
    btn.onclick = () => start();
    nav.appendChild(btn);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inyectarBotonTour);
  } else {
    inyectarBotonTour();
  }
})();
