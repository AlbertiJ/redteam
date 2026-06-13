/**
 * brightness.js — Control de brillo de pantalla desde el navegador
 * Usa un overlay semitransparente negro para atenuar sin permisos especiales.
 * No requiere APIs nativas (funciona en cualquier navegador).
 */

(function() {
  // Crea el overlay y el botón flotante
  const overlay = document.createElement('div');
  overlay.id = 'brightness-overlay';
  overlay.style.cssText = `
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0,0,0,0); pointer-events: none; z-index: 999998;
    transition: background 0.3s ease;
  `;
  document.body.appendChild(overlay);

  const panel = document.createElement('div');
  panel.id = 'brightness-panel';
  panel.style.cssText = `
    position: fixed; bottom: 20px; right: 20px; z-index: 999999;
    background: #161b22; border: 1px solid #30363d; border-radius: 10px;
    padding: 12px 16px; display: flex; gap: 8px; align-items: center;
    box-shadow: 0 4px 16px rgba(0,0,0,0.5); font-family: 'Segoe UI', system-ui, sans-serif;
  `;
  panel.innerHTML = `
    <span style="color:#79c0ff; font-size:13px; user-select:none;">🔅 Brillo</span>
    <input type="range" id="brightness-slider" min="0" max="80" value="0"
           style="width: 120px; cursor: pointer; accent-color: #58a6ff;">
    <span id="brightness-value" style="color:#8b949e; font-size:12px; min-width:32px; text-align:right;">0%</span>
    <button id="brightness-reset" title="Reset"
            style="background:#21262d; color:#c9d1d9; border:1px solid #30363d;
                   border-radius:4px; padding:4px 8px; cursor:pointer; font-size:12px;">↺</button>
  `;
  document.body.appendChild(panel);

  const slider = document.getElementById('brightness-slider');
  const valueLabel = document.getElementById('brightness-value');
  const resetBtn = document.getElementById('brightness-reset');

  // Persistir valor entre páginas
  const STORAGE_KEY = 'api-eye-brightness';
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved !== null) {
    slider.value = saved;
    applyBrightness(saved);
  }

  function applyBrightness(v) {
    overlay.style.background = `rgba(0,0,0,${v/100})`;
    valueLabel.textContent = v + '%';
    localStorage.setItem(STORAGE_KEY, v);
  }

  slider.addEventListener('input', e => applyBrightness(e.target.value));
  resetBtn.addEventListener('click', () => { slider.value = 0; applyBrightness(0); });
})();
