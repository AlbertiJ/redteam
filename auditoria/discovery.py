"""
discovery.py — Recorre la API, compara con Swagger, detecta shadow APIs
y guarda todo en SQLite.

Uso:  python discovery.py
"""

import sys
import os
import json
import requests
from datetime import datetime

# Path hack para importar db desde el directorio db/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "db"))
from db import db

BASE = "http://127.0.0.1:8000"

# Diccionario de paths a probar (fuzzing controlado)
WORDLIST = [
    "/", "/docs", "/openapi.json", "/redoc",
    "/api/v1/servidores",
    "/api/v1/servidores/1", "/api/v1/servidores/999",
    "/api/v1/servidores/deprecados",
    "/api/v1/internal/health",
    "/api/v1/debug",
    "/api/v1/metadatos",
    "/api/v1/auth/admin",
    "/api/v1/internal/admin/panel",
    "/api/v1/test",
    "/api/v0/servidores",
    "/api/v1/auditoria/infraestructura",
    "/api/v2/servidores",
    "/admin", "/administrator", "/console",
    "/graphql", "/api/graphql",
    "/api/v1/users", "/api/v1/config",
    "/backup", "/api-docs", "/swagger",
    "/internal", "/test", "/dev", "/staging",
    "/api/v1/status", "/api/v1/logs",
    "/api/v1/internal", "/api/v1/internal/users",
    "/api/v1/secret", "/api/v1/.env",
    "/robots.txt", "/.well-known/openid-configuration",
]

PAYLOADS = [
    "SELECT * FROM users",
    "DROP TABLE servidores",
    "admin' OR 1=1 --",
    "'; DELETE FROM servidores; --",
    "<!DOCTYPE foo [<!ENTITY xxe SYSTEM \"file:///etc/passwd\">]>",
    "../../../etc/passwd",
    "; ls -la /",
    "'; cat /etc/shadow; echo '",
    "1' UNION SELECT username, password FROM users--",
]

def clasificar(status, body, headers):
    """Clasifica un hallazgo por severidad."""
    if status == 200:
        if "stack_trace" in str(body) or "query_revelada" in str(body):
            return ("VULNERABLE", "CRITICO", "Inyección ejecutada con stack trace filtrado")
        if "secret" in str(body).lower() or "password" in str(body).lower():
            return ("INFO_DISCLOSURE", "ALTO", "Credenciales o secretos expuestos")
        if "version" in str(body) or "framework" in str(body):
            return ("INFO_DISCLOSURE", "MEDIO", "Information disclosure de versiones/framework")
        return ("ENDPOINT_OK", "BAJO", "Endpoint funcional")
    if status == 404:
        return ("NO_ENCONTRADO", "INFO", "No existe")
    if status == 405:
        return ("METODO_NO_PERMITIDO", "BAJO", "Método no habilitado")
    if status == 500:
        return ("ERROR_INTERNO", "ALTO", "Posible fuga de stack trace")
    if status in (401, 403):
        return ("ACCESO_DENEGADO", "MEDIO", f"Status {status}")
    return ("OTRO", "INFO", f"Status {status}")

def obtener_swagger_oficial():
    """Descarga las rutas que SÍ están documentadas en /openapi.json."""
    try:
        r = requests.get(f"{BASE}/openapi.json", timeout=5)
        if r.status_code == 200:
            return set(r.json().get("paths", {}).keys())
    except Exception as e:
        print(f"[!] No pude leer Swagger: {e}")
    return set()

def fuzzing_rutas():
    """Recorre la wordlist y clasifica cada endpoint."""
    print(f"\n[+] Fuzzing de rutas contra {BASE} ...")
    swagger = obtener_swagger_oficial()
    print(f"[+] Swagger oficial lista {len(swagger)} rutas")

    for path in WORDLIST:
        try:
            r = requests.get(f"{BASE}{path}", timeout=5)
            en_swagger = path in swagger
            categoria, severidad, detalle = clasificar(r.status_code, r.text, r.headers)
            db.guardar_hallazgo(
                endpoint=path,
                metodo="GET",
                status_code=r.status_code,
                en_swagger=en_swagger,
                categoria=categoria,
                severidad=severidad,
                detalle=detalle,
                headers=json.dumps(dict(r.headers))
            )
            marcador = "📋" if en_swagger else "🕵️  SHADOW"
            print(f"  {marcador} {r.status_code} {path:45s} → {categoria}")
        except requests.exceptions.ConnectionError:
            print(f"  [✗] No se pudo conectar a {BASE}. ¿Levantaste mi_api_local.py ?")
            return False
    return True

def fuzzing_payloads():
    """Prueba payloads de inyección contra el endpoint de auditoría."""
    print(f"\n[+] Inyección de payloads contra /api/v1/auditoria/infraestructura ...")
    for p in PAYLOADS:
        try:
            r = requests.post(
                f"{BASE}/api/v1/auditoria/infraestructura",
                json={"comando": p},
                timeout=5
            )
            en_swagger = "/api/v1/auditoria/infraestructura" in obtener_swagger_oficial()
            categoria, severidad, detalle = clasificar(r.status_code, r.text, r.headers)
            db.guardar_hallazgo(
                endpoint="/api/v1/auditoria/infraestructura",
                metodo="POST",
                status_code=r.status_code,
                en_swagger=en_swagger,
                categoria=categoria,
                severidad=severidad,
                detalle=f"Payload: {p[:60]}",
                headers=json.dumps(dict(r.headers))
            )
            print(f"  {r.status_code} payload: {p[:50]:50s} → {categoria} ({severidad})")
        except Exception as e:
            print(f"  [✗] Error con payload {p}: {e}")

def reporte_consola():
    """Imprime el resumen final en consola."""
    hallazgos = db.listar_hallazgos()
    resumen = db.resumen_por_categoria()
    print(f"\n{'='*60}")
    print(f"  RESUMEN DE AUDITORÍA — {datetime.utcnow().isoformat()}")
    print(f"{'='*60}")
    print(f"  Total hallazgos: {len(hallazgos)}")
    shadow = [h for h in hallazgos if not h["en_swagger"]]
    print(f"  Shadow APIs detectadas: {len(shadow)}")
    criticos = [h for h in hallazgos if h["severidad"] == "CRITICO"]
    print(f"  Hallazgos CRÍTICOS: {len(criticos)}")
    print(f"\n  Por categoría:")
    for r in resumen:
        print(f"    {r['categoria']:25s} {r['severidad']:10s} x{r['total']}")

def main():
    print("="*60)
    print(" API-Eye v2.0 — Discovery & Shadow API Detection")
    print("="*60)
    db.init_db()
    db.limpiar()
    if fuzzing_rutas():
        fuzzing_payloads()
    reporte_consola()
    print(f"\n[+] Datos guardados en: db/hallazgos.db")
    print(f"[+] Ahora abrí el dashboard: dashboard.html\n")

if __name__ == "__main__":
    main()
