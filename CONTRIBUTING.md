# 🤝 Guía para contribuir

¡Gracias por tu interés en mejorar API-Eye Lab! Toda contribución es bienvenida.

## Formas de contribuir

- 🐛 **Reportar bugs** — Abrí un [Issue](https://github.com/TU_USUARIO/api-eye-lab/issues) con:
  - Pasos para reproducir
  - Comportamiento esperado vs real
  - Screenshots (si aplica)
  - Tu entorno (OS, versión de Python)

- 💡 **Proponer features** — Abrí un Issue con el tag `enhancement` describiendo:
  - El caso de uso
  - Cómo lo resolverías
  - Alternativas consideradas

- 📝 **Mejorar documentación** — Typos, ejemplos faltantes, traducciones

- 🧪 **Agregar tests** — Cobertura de pytest es bienvenida

- 🎨 **Mejorar el UI/UX** — Los HTMLs son editables directo

- 🌍 **Traducir** — Si querés hacer una versión en otro idioma

## Flujo de trabajo

1. **Fork** del repositorio
2. **Cloná** tu fork: `git clone https://github.com/TU_USUARIO/api-eye-lab.git`
3. **Creá una branch** desde `main`: `git checkout -b feature/mi-mejora`
4. **Desarrollá** tu cambio
5. **Probá** que todo siga funcionando: `python src/app.py`
6. **Commit** con mensaje descriptivo: `git commit -m "feat: agrego escenario de OAuth bypass"`
7. **Push** a tu fork: `git push origin feature/mi-mejora`
8. **Abrí un Pull Request** explicando qué cambia y por qué

## Estilo de código

### Python
- PEP 8
- Type hints cuando sea posible
- Docstrings en funciones públicas
- Nombres descriptivos

### HTML/CSS/JS
- HTML semántico
- CSS en `<style>` por archivo (no requiere build)
- JS vanilla (no frameworks)
- Comentarios en español

### Commits
Usamos [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — Nueva funcionalidad
- `fix:` — Bug fix
- `docs:` — Cambios en documentación
- `style:` — Cambios de formato (sin cambiar lógica)
- `refactor:` — Refactor de código
- `test:` — Agregar o modificar tests
- `chore:` — Tareas de mantenimiento

## Áreas donde faltan contribuciones

- 🧪 Tests con pytest
- 🌐 Soporte GraphQL (introspection, nested queries)
- 🌐 Soporte SOAP (WSDL, XXE)
- 📊 Más visualizaciones en el dashboard
- 🌍 Traducciones (i18n)
- 📚 Más escenarios resueltos
- 🎨 Mejoras de UI/UX

## Código de conducta

- Sé respetuoso
- Aceptá críticas constructivas
- Enfocate en el problema, no en la persona
- No tolere acoso de ningún tipo

## Licencia

Al contribuir, aceptás que tus aportes se publiquen bajo la misma licencia MIT del proyecto.
