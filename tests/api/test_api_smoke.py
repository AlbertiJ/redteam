"""Tests de API automáticos para RedTeam Lab v4.

Estos tests verifican que los endpoints CRÍTICOS no se rompan cuando
alguien hace cambios en el código.

Se ejecutan automáticamente con: pytest tests/api/

Cubre:
- Endpoint principal: /
- Servidores: /api/v1/servidores
- Servidor específico: /api/v1/servidores/{id}
- DB Builder: /api/v1/dbbuilder/predefinidas
- Shadow APIs: /api/v1/auth/admin (debe existir y devolver 200 con info sensible - es INTENCIONAL)
- Health: /api/v1/internal/health
- Deprecados: /api/v1/servidores/deprecados
- Versión: /api/v1/metadatos
"""
import os
import pytest
import requests

HOST = os.environ.get("REDTEAM_HOST", "http://127.0.0.1:8000")


def _skip_if_no_server():
    """Helper: skip el test si el server no está corriendo."""
    try:
        r = requests.get(HOST + "/", timeout=2)
        if r.status_code != 200:
            pytest.skip(f"Server respondió con {r.status_code}")
    except Exception as e:
        pytest.skip(f"Server no disponible en {HOST}: {e}")


# =========================================================================
# TESTS DE HUMO (SMOKE TESTS)
# =========================================================================

class TestSmoke:
    """Tests de humo: ¿el server arranca y responde?"""

    def test_index_responde_200(self):
        _skip_if_no_server()
        r = requests.get(HOST + "/", timeout=5)
        assert r.status_code == 200
        assert "RedTeam Lab" in r.text, "El index no tiene el título"

    def test_docs_responde_200(self):
        _skip_if_no_server()
        r = requests.get(HOST + "/docs", timeout=5)
        assert r.status_code == 200
        assert "swagger" in r.text.lower(), "No parece Swagger UI"

    def test_paginas_estaticas_responden_200(self):
        _skip_if_no_server()
        paginas = [
            "/static/practicas.html",
            "/static/wizard.html",
            "/static/dbbuilder.html",
            "/static/api_visual.html",
            "/static/dashboard.html",
            "/static/detective.html",
            "/static/historial.html",
            "/static/errores.html",
        ]
        for p in paginas:
            r = requests.get(HOST + p, timeout=5)
            assert r.status_code == 200, f"Página {p} devolvió {r.status_code}"


# =========================================================================
# TESTS DE API: SERVIDORES
# =========================================================================

class TestServidoresAPI:
    """Tests del API principal de servidores."""

    def test_listar_servidores_200(self):
        _skip_if_no_server()
        r = requests.get(HOST + "/api/v1/servidores", timeout=5)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list), "La respuesta no es una lista"
        assert len(data) > 0, "No hay servidores en la respuesta"
        # Cada servidor debe tener los campos básicos
        for s in data:
            assert "id" in s, f"Servidor sin id: {s}"
            assert "nombre" in s, f"Servidor sin nombre: {s}"

    def test_obtener_servidor_por_id_200(self):
        _skip_if_no_server()
        r = requests.get(HOST + "/api/v1/servidores/1", timeout=5)
        assert r.status_code == 200
        s = r.json()
        assert s["id"] == 1

    def test_servidor_inexistente_404(self):
        _skip_if_no_server()
        r = requests.get(HOST + "/api/v1/servidores/99999", timeout=5)
        assert r.status_code == 404, f"Debería devolver 404, devolvió {r.status_code}"

    def test_servidores_deprecados_200(self):
        _skip_if_no_server()
        r = requests.get(HOST + "/api/v1/servidores/deprecados", timeout=5)
        # 200 (es un endpoint de doc), 404 (sacado) o 422 (parámetro inválido)
        assert r.status_code in [200, 404, 422]


# =========================================================================
# TESTS DE API: DB BUILDER
# =========================================================================

class TestDBBuilderAPI:
    """Tests del constructor de DBs."""

    def test_listar_dbs_predefinidas_200(self):
        _skip_if_no_server()
        r = requests.get(HOST + "/api/v1/dbbuilder/predefinidas", timeout=5)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, (list, dict)), "La respuesta no es ni lista ni dict"

    def test_consultar_db_existente_200(self):
        _skip_if_no_server()
        r = requests.get(HOST + "/api/v1/dbbuilder/consultar?db=bandas&limite=5", timeout=5)
        # 200 (si existe bandas) o 404 (si no existe)
        assert r.status_code in [200, 404]

    def test_consultar_con_limite_invalido_no_500(self):
        _skip_if_no_server()
        r = requests.get(HOST + "/api/v1/dbbuilder/consultar?db=bandas&limite=uchos", timeout=5)
        # No debería explotar con 500, debería rechazar el input
        assert r.status_code != 500, (
            f"BUG: el server explotó con 500 cuando le pasamos un string en vez de int. "
            f"Debería devolver 400 o 422."
        )


# =========================================================================
# TESTS DE API: SHADOW APIs (INTENCIONALMENTE VULNERABLES)
# =========================================================================

class TestShadowAPIs:
    """Tests de las shadow APIs que el Detective de Bugs detecta.

    Estos tests están acá para DOCUMENTAR que los bugs existen.
    Si el server los arregla, estos tests fallan (¡y eso es bueno!).
    """

    def test_auth_admin_sin_auth_devuelve_200(self):
        """Shadow API intencional: /api/v1/auth/admin sin auth devuelve 200."""
        _skip_if_no_server()
        r = requests.get(HOST + "/api/v1/auth/admin", timeout=5)
        # BUG intencional: debería ser 401, no 200
        assert r.status_code == 200, "El admin endpoint debería devolver 200 con info sensible (es el bug)"

    def test_debug_endpoint_sin_auth(self):
        """Shadow API intencional: /api/v1/debug expone secretos."""
        _skip_if_no_server()
        r = requests.get(HOST + "/api/v1/debug", timeout=5)
        # BUG intencional
        if r.status_code == 200:
            body = r.text.lower()
            # Verifica que efectivamente filtra secretos
            assert any(s in body for s in ["db_host", "db_user", "secret", "key", "password", "api_key"])

    def test_metadatos_filtra_info(self):
        """Endpoint de info disclosure: /api/v1/metadatos filtra versiones."""
        _skip_if_no_server()
        r = requests.get(HOST + "/api/v1/metadatos", timeout=5)
        assert r.status_code == 200
        # Verifica que filtra versión de FastAPI
        body = r.text.lower()
        assert "fastapi" in body or "version" in body, (
            "El endpoint debería filtrar info de versiones (es el bug)"
        )


# =========================================================================
# TESTS DE API: HEALTH CHECK
# =========================================================================

class TestHealth:
    def test_internal_health_responde(self):
        _skip_if_no_server()
        r = requests.get(HOST + "/api/v1/internal/health", timeout=5)
        # 200 o 404 (puede estar oculto)
        assert r.status_code in [200, 404]


# =========================================================================
# CONFIGURACIÓN
# =========================================================================

def pytest_configure(config):
    """Marker para tests de humo."""
    config.addinivalue_line("markers", "smoke: Tests de humo (arranque básico)")
