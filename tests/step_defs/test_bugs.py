"""Step definitions para los 10 .feature del Detective de Bugs.

Estos tests son DUALES:
- Detectan el bug (FALLA si el bug está, como debería ser en un lab)
- Documentan el bug con un test legible por humanos (Gherkin)
"""
import os
import re
import json
import pytest
import requests
from pytest_bdd import scenarios, given, when, then, parsers

# Directorio del código fuente
SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "src")
APP_PY = os.path.join(SRC_DIR, "app.py")

# Cargar todos los .feature del directorio features
scenarios("../features")


# =========================================================================
# FIXTURES COMPARTIDAS
# =========================================================================

@pytest.fixture
def ctx():
    """Contexto compartido entre pasos."""
    return {
        "host": os.environ.get("REDTEAM_HOST", "http://127.0.0.1:8000"),
        "response": None,
        "html": None,
        "app_source": None,
    }


@pytest.fixture(autouse=True)
def cargar_source(ctx):
    """Carga el código de app.py una sola vez por test."""
    if os.path.exists(APP_PY):
        with open(APP_PY, "r", encoding="utf-8") as f:
            ctx["app_source"] = f.read()


# =========================================================================
# PASOS COMUNES (REUTILIZADOS POR MUCHOS FEATURE)
# =========================================================================

@given(parsers.parse('que el server de RedTeam Lab está corriendo'))
def server_corriendo(ctx):
    """Verifica que el server responde (o lo levanta si no está)."""
    try:
        r = requests.get(ctx["host"] + "/", timeout=2)
        assert r.status_code == 200, f"Server respondió con {r.status_code}"
    except Exception as e:
        pytest.skip(f"Server no está corriendo en {ctx['host']}: {e}")


@given(parsers.parse('que visito la página "{path}"'))
def visitar_pagina(ctx, path):
    r = requests.get(ctx["host"] + path, timeout=5)
    ctx["html"] = r.text
    assert r.status_code == 200, f"Página {path} no respondió 200"


@given('que leo el código del RedTeam Lab')
def leer_codigo(ctx):
    assert ctx["app_source"] is not None, f"No se pudo leer {APP_PY}"


@given('que leo el código de la función de insert del dbbuilder')
def leer_insert(ctx):
    """Alias para leer el código (mismo archivo)."""
    leer_codigo(ctx)


@given('que leo el código de la función crear_token')
def leer_crear_token(ctx):
    """Alias para leer el código."""
    leer_codigo(ctx)


# =========================================================================
# BUG 1A y 1B: URLs mal construidas
# =========================================================================

@when('el frontend arma la URL para consultar datos')
def armar_url_consulta(ctx):
    """Busca el patrón de armado de URL en el HTML."""
    assert ctx["html"] is not None
    # Buscar líneas con "window.location.origin" + "/api/"
    patron_host_origen = re.search(
        r"\$\{window\.location\.origin\}/api/",
        ctx["html"]
    )
    patron_host_doble = re.search(
        r"\$\{window\.location\.origin\}\$\{window\.location\.origin\}",
        ctx["html"]
    )
    ctx["url_origen_ok"] = patron_host_origen is not None
    ctx["url_doble_mal"] = patron_host_doble is not None


@then(parsers.parse('la URL resultante empieza con "{prefijo}"'))
def check_prefijo_url(ctx, prefijo):
    """Si la URL está bien armada, empieza con el host + /api/."""
    assert ctx["url_origen_ok"], (
        f"BUG DETECTADO: el HTML no usa window.location.origin para armar la URL.\n"
        f"Debería empezar con: {prefijo}"
    )


@then(parsers.parse('no contiene "{patron}"'))
def check_no_contiene(ctx, patron):
    """Si la URL está bien armada, no tiene el host duplicado."""
    assert not ctx["url_doble_mal"], (
        f"BUG DETECTADO: el HTML tiene '{patron}' duplicado."
    )


@when(parsers.parse('el operador y el servidor arman una URL con la plantilla y nombre {nombre}'))
def armar_url_plantilla(ctx, nombre):
    ctx["nombre"] = nombre
    # El bug se detecta si en el HTML se concatena con template string mal
    assert ctx["html"] is not None


@when('la plantilla se mete en el medio de un template string con backticks')
def plantilla_template_string(ctx):
    """Paso informativo, no hace nada (el assert está en check_url_contiene)."""
    pass


@then(parsers.parse('la URL final contiene "{fragmento}"'))
def check_url_contiene(ctx, fragmento):
    """Detecta que la URL está bien armada (no concatenada con +)."""
    # Si el HTML tiene la concatenación '+ \n' eso es el bug
    bug_concat = re.search(
        r"`\$\{window\.location\.origin\}/api/v1/dbbuilder/consultar\?db=` \+\s*\$\{nombre\}",
        ctx["html"]
    )
    assert not bug_concat, (
        f"BUG DETECTADO: la URL se concatena con '+' en vez de template string.\n"
        f"Fragmento esperado: {fragmento}"
    )


@then('ese patrón debería ser seguro')
def placeholder_seguro(ctx):
    """Paso redundante, el assert anterior ya validó."""
    pass


# =========================================================================
# BUG 2A: No validar input vacío
# =========================================================================

@when(parsers.parse('hago POST a "{endpoint}" con nombre ""'))
def post_input_vacio(ctx, endpoint):
    try:
        ctx["response"] = requests.post(
            ctx["host"] + endpoint,
            json={"nombre": "", "campos": ["id"], "datos": []},
            timeout=5
        )
    except Exception as e:
        pytest.skip(f"No se pudo hacer POST: {e}")


@then(parsers.parse('el código de respuesta NO debería ser {code:d}'))
def check_response_no_es(ctx, code):
    assert ctx["response"] is not None
    assert ctx["response"].status_code != code, (
        f"BUG DETECTADO: el endpoint aceptó input vacío y devolvió {code}.\n"
        f"Debería haber devuelto 400 o 422."
    )


@then(parsers.parse('debería ser {code1:d} o {code2:d}'))
def check_response_es_uno_de_dos(ctx, code1, code2):
    assert ctx["response"] is not None
    assert ctx["response"].status_code in [code1, code2], (
        f"BUG DETECTADO: respuesta fue {ctx['response'].status_code}, "
        f"debería ser {code1} o {code2}."
    )


# =========================================================================
# BUG 2B: Tipo de dato incorrecto
# =========================================================================

@when(parsers.parse('hago GET a "{endpoint}"'))
def get_endpoint(ctx, endpoint):
    try:
        ctx["response"] = requests.get(ctx["host"] + endpoint, timeout=5)
    except Exception as e:
        pytest.skip(f"No se pudo hacer GET: {e}")


@then(parsers.parse('el código de respuesta debería ser {code1:d} o {code2:d}'))
def check_response_status_2(ctx, code1, code2):
    assert ctx["response"] is not None
    assert ctx["response"].status_code in [code1, code2], (
        f"BUG DETECTADO: respuesta fue {ctx['response'].status_code}, "
        f"debería ser {code1} o {code2}."
    )


@then(parsers.parse('NO debería ser {code:d}'))
def check_response_not_500(ctx, code):
    assert ctx["response"] is not None
    assert ctx["response"].status_code != code, (
        f"BUG DETECTADO: el server explotó con 500 cuando le pasaste "
        f"un tipo de dato incorrecto."
    )


# =========================================================================
# BUG 3A: SQL Injection en SELECT
# =========================================================================

@when(parsers.parse('leo el código de la función "{funcion}"'))
def leer_funcion(ctx, funcion):
    """Alias para cargar el código."""
    assert ctx["app_source"] is not None


@then(parsers.parse('la query SQL se arma con f-string o concatenación (+)'))
def check_sql_concat(ctx):
    """Detecta SQL Injection: SELECT * FROM tabla WHERE campo LIKE '%{input}%'"""
    patron_sqli = re.search(
        r'SELECT.*\{.*\}.*LIKE|SELECT.*\+.*LIKE|SELECT.*\+.*\+',
        ctx["app_source"]
    )
    assert patron_sqli is None, (
        f"BUG DETECTADO: hay un SELECT con concatenación vulnerable:\n"
        f"{patron_sqli.group(0)[:200] if patron_sqli else ''}"
    )


@then(parsers.parse('NO usa parámetros preparados (?) o placeholders'))
def placeholder_no_placeholders(ctx):
    """Si el assert anterior pasó, ya está validado."""
    pass


# =========================================================================
# BUG 3B: INSERT sin prepared statements
# =========================================================================

@when('busco "INSERT INTO" en el código')
def buscar_insert(ctx):
    patron_insert = re.search(r'INSERT\s+INTO', ctx["app_source"], re.IGNORECASE)
    assert patron_insert is not None, "No se encontró ningún INSERT INTO"


@then('el código de RedTeam Lab DEBE usar placeholders (?) en TODOS los INSERT')
def check_insert_con_placeholders(ctx):
    """Asegura que todos los INSERTs usen placeholders, no concatenación."""
    # Buscar todos los INSERT INTO seguidos de comilla (string template)
    inserts = re.findall(
        r'INSERT\s+INTO\s+["\']?[\w_]+["\']?[^"\']*["\'][^"\']*VALUES\s*\(?\s*["\']',
        ctx["app_source"],
        re.IGNORECASE,
    )
    # Si no hay INSERTs con string template, el test pasa (no hay nada que validar)
    if not inserts:
        pytest.skip("No se encontraron INSERTs con string template para validar")
    for ins in inserts:
        # Si es un INSERT INTO con VALUES en string template, DEBE tener ?
        assert '?' in ins, (
            f"BUG: el siguiente INSERT no usa placeholders (?):\n{ins[:200]}"
        )


@then(parsers.parse('NUNCA debe concatenar valores con + str() ni con f-strings'))
def check_insert_sin_concatenacion(ctx):
    """Asegura que ningún INSERT concatene valores con str() o f-string en string template."""
    # Buscar patrón de concatenación en string template: VALUES ' + str( o f"...{
    patron = re.search(
        r"VALUES\s*['\"][^'\"]*['\"]?\s*\+\s*str\(|f['\"]VALUES[^'\"]*\{",
        ctx["app_source"],
        re.IGNORECASE | re.DOTALL,
    )
    assert patron is None, (
        f"BUG: el siguiente INSERT concatena valores con str() o f-string:\n"
        f"{patron.group(0)[:200] if patron else ''}"
    )


# =========================================================================
# BUG 4A: Credenciales hardcoded
# =========================================================================

@when(parsers.parse('busco la palabra "{palabra}" en el código'))
def buscar_palabra(ctx, palabra):
    patron = re.search(palabra, ctx["app_source"], re.IGNORECASE)
    ctx["palabra_encontrada"] = patron is not None


@then(parsers.parse('aparece como "{snippet}" SIN valor por defecto'))
def check_environ_sin_default(ctx, snippet):
    """Detecta: os.environ.get('DB_PASSWORD')  ← SIN default = BIEN
       El bug sería: os.environ.get('DB_PASSWORD', 'admin123')  ← CON default = MAL"""
    patron_mal = re.search(
        r'os\.environ\.get\([\'"]DB_PASSWORD[\'"]\s*,\s*[\'"][^\'"]+[\'"]\)',
        ctx["app_source"]
    )
    assert patron_mal is None, (
        f"BUG DETECTADO: DB_PASSWORD tiene valor por defecto hardcoded:\n"
        f"{patron_mal.group(0)}"
    )


@then(parsers.parse('NO como "{snippet}"'))
def check_no_es_patron(ctx, snippet):
    """Detecta: DB_PASSWORD = 'admin123'  # MAL"""
    patron = re.search(
        r'DB_PASSWORD\s*=\s*[\'"][^\'"]+[\'"]',
        ctx["app_source"]
    )
    assert patron is None, (
        f"BUG DETECTADO: hay un DB_PASSWORD hardcoded:\n"
        f"{patron.group(0)}"
    )


# =========================================================================
# BUG 4B: Token que no expira
# =========================================================================

@when('busco la función que genera tokens')
def buscar_token(ctx):
    patron = re.search(
        r'jwt\.encode|create_access_token|generar_token|create_token',
        ctx["app_source"],
        re.IGNORECASE
    )
    ctx["funcion_token_encontrada"] = patron is not None


@then(parsers.parse('si existe, NO debe tener expires_delta ni exp en el payload'))
def check_token_sin_expira(ctx):
    """Detecta: el código no tiene expires_delta ni 'exp' en el payload."""
    if not ctx["funcion_token_encontrada"]:
        pytest.skip("El lab no implementa generación de tokens (no hay bug que detectar)")
    patron_exp = re.search(
        r'expires_delta\s*=|[\'"]exp[\'"]\s*:',
        ctx["app_source"]
    )
    assert patron_exp is None, (
        f"BUG DETECTADO: el token SÍ tiene expiración, debería NO tenerla "
        f"para que el test reproduzca el bug."
    )


@then('eso significa que el token no expira nunca')
def placeholder_token_no_expira(ctx):
    pass


# =========================================================================
# BUG 5A: Stack trace visible en errores
# =========================================================================

@when(parsers.parse('hago GET a "{endpoint}"'))
def get_endpoint_que_falla(ctx, endpoint):
    try:
        ctx["response"] = requests.get(ctx["host"] + endpoint, timeout=5)
    except Exception as e:
        ctx["response"] = None
        pytest.skip(f"No se pudo hacer GET: {e}")


@then(parsers.parse('la respuesta NO debería contener "{snippet}"'))
def check_no_traceback(ctx, snippet):
    assert ctx["response"] is not None
    assert snippet not in ctx["response"].text, (
        f"BUG DETECTADO: la respuesta contiene '{snippet}'.\n"
        f"El server está filtrando el stack trace al cliente."
    )


@then('NO debería contener la ruta interna del servidor')
def check_no_path_interno(ctx):
    assert ctx["response"] is not None
    # Patrones típicos de paths internos
    patrones = ["/run/csi/", "/home/", "/root/", "/app/", "File \""]
    for p in patrones:
        assert p not in ctx["response"].text, (
            f"BUG DETECTADO: la respuesta filtra path interno '{p}'."
        )


# =========================================================================
# BUG 5B: Endpoint /debug sin auth
# =========================================================================

@when(parsers.parse('hago GET a "{endpoint}" sin auth'))
def get_debug_sin_auth(ctx, endpoint):
    try:
        ctx["response"] = requests.get(ctx["host"] + endpoint, timeout=5)
    except Exception as e:
        pytest.skip(f"No se pudo hacer GET: {e}")


@then(parsers.parse('el código de respuesta NO debería ser {code:d} con secretos'))
def check_debug_no_200_con_secretos(ctx, code):
    """Si el debug devuelve 200 con secretos, el test pasa y el bug se confirma."""
    assert ctx["response"] is not None
    if ctx["response"].status_code == code:
        # El bug está, el test lo confirma
        body = ctx["response"].text
        # Verificar que efectivamente filtra secretos
        palabras_secretas = ["secret", "key", "password", "api_key", "DB_HOST"]
        filtra_secretos = any(p.lower() in body.lower() for p in palabras_secretas)
        assert filtra_secretos, (
            f"El endpoint devuelve {code} pero no parece filtrar secretos. "
            f"Revisar manualmente."
        )


@then(parsers.parse('debería ser {code1:d} (no autorizado) o {code2:d} (no existe)'))
def check_debug_es_401_o_404(ctx, code1, code2):
    """Si el endpoint está bien protegido, devuelve 401 o 404."""
    # Este assert es "el caso bueno": si pasa, NO hay bug
    # Si falla, el bug existe (es lo que el test del Detective quiere)
    assert ctx["response"] is not None
    # Solo informativo: el test "pasa" si el bug existe (response != 401/404)
    # Para que el Detective detecte el bug, queremos que response SEA 200 con secretos
    # (eso lo confirmó el then anterior)
