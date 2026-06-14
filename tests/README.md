# Tests de RedTeam Lab v4

Esta carpeta tiene **2 tipos de tests automáticos**:

## 1. Tests de humo y API (`tests/api/test_api_smoke.py`)

Verifican que los endpoints críticos no se rompan cuando alguien hace cambios al código.

```bash
# 1. Levantar el server
python src/app.py

# 2. En otra terminal, correr los tests
python -m pytest tests/api/ -v
```

**Cubre:**
- Index responde 200
- 8 páginas estáticas responden 200
- API de servidores (listar, por id, inexistente, deprecados)
- DB Builder (predefinidas, consultar, input inválido)
- Shadow APIs (que sigan existiendo como bug intencional)
- Health check

## 2. Tests del Detective de Bugs (`tests/step_defs/test_bugs.py` + `tests/features/`)

**10 features en español** que documentan los 10 bugs del Detective. Cada `.feature`
es un test legible por humanos que un cadete puede leer y entender.

```bash
# Asegurarse de tener pytest-bdd instalado
pip install pytest-bdd

# Correr la suite BDD
python -m pytest tests/step_defs/ -v
```

**Filosofía de los tests del Detective:**
- Detectan **patrones de bugs** en el código (no bugs específicos)
- Si el test **pasa**: el código está OK, no tiene ese bug
- Si el test **falla**: el bug está presente, el Detective lo cazó
- Algunos tests se **skipean** si el código no tiene el patrón a buscar
  (ej: si no hay función de token, no podemos testear bug de token)

## Archivos

```
tests/
├── README.md
├── api/
│   └── test_api_smoke.py          # Tests de humo + API
├── features/
│   ├── bug_01_url_duplicada.feature
│   ├── bug_02_url_concatenada.feature
│   ├── bug_03_input_vacio.feature
│   ├── bug_04_tipo_dato_incorrecto.feature
│   ├── bug_05_sql_injection_select.feature
│   ├── bug_06_sql_injection_insert.feature
│   ├── bug_07_credenciales_hardcoded.feature
│   ├── bug_08_token_sin_expiracion.feature
│   ├── bug_09_stack_trace_en_errores.feature
│   └── bug_10_debug_endpoint.feature
└── step_defs/
    └── test_bugs.py                # Steps en español para los .feature
```

## Cómo agregar un nuevo test

1. Para un test de API: agregar método a la clase correspondiente en `test_api_smoke.py`
2. Para un test de bug: crear `tests/features/bug_XX_nombre.feature` + agregar
   el step en `tests/step_defs/test_bugs.py` con el decorador `@when` o `@then`
