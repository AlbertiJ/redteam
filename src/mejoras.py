"""
mejoras.py — Endpoints para las 4 mejoras del lab:
  1. Modo Compañía (DBs compartidas entre usuarios)
  2. Detective de Stack Traces
  3. Generador de Shadow APIs por stack
  4. Modo Time-Travel (replay de auditoría)
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sqlite3
import time
import random
import json
from datetime import datetime, timedelta
from pathlib import Path

router = APIRouter()

DB_DIR = Path(__file__).parent / "db" / "user_dbs"
DB_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================================
# MEJORA 1: MODO COMPAÑÍA
# DBs compartidas entre varios usuarios sin ver los datos del otro
# =========================================================================

class CompanySessionCreate(BaseModel):
    db_name: str
    campos: List[str]
    creator_name: str

class CompanyRowAdd(BaseModel):
    session_id: str
    user_name: str
    row: Dict[str, Any]

@router.post("/company/create")
def company_create(req: CompanySessionCreate):
    """Crea una sesión compartida: DB vacía con campos definidos."""
    if len(req.campos) < 3 or len(req.campos) > 100:
        raise HTTPException(400, "Mín 3 campos, máx 100")
    if "id" not in req.campos:
        raise HTTPException(400, "Primer campo debe ser 'id'")

    session_id = f"company_{int(time.time())}_{random.randint(1000,9999)}"
    db_path = DB_DIR / f"{session_id}.db"
    conn = sqlite3.connect(db_path)

    cols = ", ".join([f'"{c}" TEXT' for c in req.campos])
    conn.execute(f'CREATE TABLE "{req.db_name}" ({cols})')

    # Metadata de la sesión
    conn.execute('CREATE TABLE IF NOT EXISTS "_meta" (key TEXT, value TEXT)')
    conn.execute('INSERT INTO "_meta" VALUES (?, ?)', ("db_name", req.db_name))
    conn.execute('INSERT INTO "_meta" VALUES (?, ?)', ("creator", req.creator_name))
    conn.execute('INSERT INTO "_meta" VALUES (?, ?)', ("created_at", datetime.utcnow().isoformat()))
    conn.execute('INSERT INTO "_meta" VALUES (?, ?)', ("status", "open"))  # open | closed
    conn.commit()
    conn.close()

    return {
        "session_id": session_id,
        "share_url": f"/company.html?session={session_id}",
        "db_name": req.db_name,
        "campos": req.campos,
        "invite_message": f"Compartí este session_id con tu compañero: {session_id}"
    }

@router.post("/company/add_row")
def company_add_row(req: CompanyRowAdd):
    """Cada usuario carga una fila a la DB compartida sin ver las del otro."""
    db_path = DB_DIR / f"{req.session_id}.db"
    if not db_path.exists():
        raise HTTPException(404, "Sesión no existe")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Verificar que la sesión esté abierta
    status = conn.execute('SELECT value FROM "_meta" WHERE key="status"').fetchone()
    if not status or status["value"] != "open":
        conn.close()
        raise HTTPException(400, "La sesión está cerrada. No se pueden agregar más filas.")

    # Obtener nombre de la DB
    db_name = conn.execute('SELECT value FROM "_meta" WHERE key="db_name"').fetchone()["value"]

    # Verificar campos
    cols_info = conn.execute(f'PRAGMA table_info("{db_name}")').fetchall()
    cols = [c["name"] for c in cols_info]

    # Insertar fila
    cols_quoted = ", ".join([f'"{c}"' for c in cols])
    placeholders = ", ".join(["?" for _ in cols])
    values = [str(req.row.get(c, "")) for c in cols]
    conn.execute(f'INSERT INTO "{db_name}" ({cols_quoted}) VALUES ({placeholders})', values)
    conn.commit()

    # Contar total y usuarios únicos
    total = conn.execute(f'SELECT COUNT(*) FROM "{db_name}"').fetchone()[0]
    conn.close()

    return {"ok": True, "total_rows": total, "by_user": req.user_name, "private": True}

@router.post("/company/close/{session_id}")
def company_close(session_id: str):
    """Cierra la sesión: ya no se cargan más filas. Ahora todos pueden ver todo."""
    db_path = DB_DIR / f"{session_id}.db"
    if not db_path.exists():
        raise HTTPException(404, "Sesión no existe")
    conn = sqlite3.connect(db_path)
    conn.execute('UPDATE "_meta" SET value="closed" WHERE key="status"')
    conn.commit()
    conn.close()
    return {"ok": True, "status": "closed"}

@router.get("/company/data/{session_id}")
def company_data(session_id: str):
    """Devuelve los datos — pero el modo 'consulta' los oculta hasta que el user pida."""
    db_path = DB_DIR / f"{session_id}.db"
    if not db_path.exists():
        raise HTTPException(404, "Sesión no existe")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    db_name = conn.execute('SELECT value FROM "_meta" WHERE key="db_name"').fetchone()["value"]
    status = conn.execute('SELECT value FROM "_meta" WHERE key="status"').fetchone()["value"]
    rows = conn.execute(f'SELECT * FROM "{db_name}"').fetchall()
    conn.close()

    return {
        "db_name": db_name,
        "status": status,
        "total": len(rows),
        "datos": [dict(r) for r in rows]
    }

@router.get("/company/list")
def company_list():
    """Lista todas las sesiones de compañía."""
    sessions = []
    for db_path in DB_DIR.glob("company_*.db"):
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            db_name = conn.execute('SELECT value FROM "_meta" WHERE key="db_name"').fetchone()["value"]
            status = conn.execute('SELECT value FROM "_meta" WHERE key="status"').fetchone()["value"]
            creator = conn.execute('SELECT value FROM "_meta" WHERE key="creator"').fetchone()["value"]
            total = conn.execute(f'SELECT COUNT(*) FROM "{db_name}"').fetchone()[0]
            sessions.append({
                "session_id": db_path.stem,
                "db_name": db_name,
                "status": status,
                "creator": creator,
                "rows": total
            })
        except Exception:
            pass
        conn.close()
    return sessions


# =========================================================================
# MEJORA 2: DETECTIVE DE STACK TRACES
# Galería de errores famosos para entrenar lectura
# =========================================================================

STACK_TRACES_FAMOSOS = [
    {
        "id": 1,
        "titulo": "Stack trace de Equifax (2017)",
        "status": 500,
        "contexto": "Apache Struts - OGNL injection",
        "stack": [
            "java.lang.RuntimeException: Cannot find FacesContext",
            "    at org.apache.myfaces.context.servlet.FacesContextImpl.getCurrentInstance(FacesContextImpl.java:91)",
            "    at org.apache.struts2.jsf.Struts2FacesContextFactory.getFacesContext(Struts2FacesContextFactory.java:35)",
            "    at com.opensymphony.xwork2.ognl.OgnlUtil.invokeMethod(OgnlUtil.java:189)",
            "    at com.opensymphony.xwork2.ognl.OgnlUtil.compile(OgnlUtil.java:158)",
            "    at com.opensymphony.xwork2.ognl.OgnlUtil.getValue(OgnlUtil.java:143)",
            "Caused by: org.apache.struts2.ServletActionRedirectResult:18 (Apache Struts 2.5.12)",
            "Server: Apache-Coyote/1.1, X-Powered-By: Servlet 4.0"
        ],
        "pistas_por_capa": [
            {"capa": 1, "revelar": "HTTP 500 + Apache Tomcat"},
            {"capa": 2, "revelar": "Apache Struts 2.5.12"},
            {"capa": 3, "revelar": "OGNL injection — vector de Remote Code Execution"},
            {"capa": 4, "revelar": "CVE-2017-5638 — 147 millones de usuarios comprometidos"}
        ],
        "lecciones": [
            "El stack trace revela la versión exacta del framework (Struts 2.5.12)",
            "La línea de OGNL indica un punto de inyección",
            "El server (Apache-Coyote) confirma que es Java + Tomcat",
            "Con Struts 2.5.12 + OGNL ya sabés que es vulnerable a CVE-2017-5638 sin probar nada"
        ]
    },
    {
        "id": 2,
        "titulo": "Stack trace de Parler (2020)",
        "status": 500,
        "contexto": "AWS S3 misconfiguration",
        "stack": [
            "AccessDenied: User: arn:aws:iam::123456789012:user/parler-data is not authorized to perform: s3:GetObject",
            "    at Object.handleError (/var/app/node_modules/aws-sdk/lib/services/s3.js:1234:25)",
            "    at Request.extractError (/var/app/node_modules/aws-sdk/lib/event_listeners.js:267:14)",
            "    at Request.callListeners (/var/app/node_modules/aws-sdk/lib/sequential_executor.js:106:20)",
            "    at Request.emit (/var/app/node_modules/aws-sdk/lib/sequential_executor.js:78:10)",
            "    at Request.emit (/var/app/node_modules/aws-sdk/lib/request.js:683:14)",
            "Bucket: parler-public-data, Region: us-east-1, AccountId: 123456789012"
        ],
        "pistas_por_capa": [
            {"capa": 1, "revelar": "AWS S3 AccessDenied"},
            {"capa": 2, "revelar": "ARN del usuario IAM: 123456789012"},
            {"capa": 3, "revelar": "Bucket name: parler-public-data"},
            {"capa": 4, "revelar": "Path del código: /var/app/ → server Linux en EC2"}
        ],
        "lecciones": [
            "El ARN delata el ID de cuenta AWS (123456789012)",
            "El path /var/app/ confirma EC2 con Linux (no Lambda, no Fargate)",
            "El nombre del bucket indica que se creía público",
            "Toda esta info se filtró con UN solo error 500"
        ]
    },
    {
        "id": 3,
        "titulo": "Stack trace genérico - SQLi",
        "status": 500,
        "contexto": "API en Python con SQLAlchemy mal usado",
        "stack": [
            "sqlalchemy.exc.ProgrammingError: (psycopg2.errors.SyntaxError) syntax error at or near \"'\"",
            "LINE 1: SELECT * FROM users WHERE username = ''' OR 1=1 --' AND password = 'x'",
            "                                        ^",
            "    File \"/app/api/v1/auth.py\", line 47, in authenticate",
            "  query = f\"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'\"",
            "  result = db.execute(query)",
            "psycopg2 version: 2.9.5, PostgreSQL 14.2"
        ],
        "pistas_por_capa": [
            {"capa": 1, "revelar": "Error SQL: syntax error cerca de comilla"},
            {"capa": 2, "revelar": "Query completa con la concatenación del input"},
            {"capa": 3, "revelar": "PostgreSQL 14.2 + psycopg2 2.9.5"},
            {"capa": 4, "revelar": "F-strings de Python usados en SQL — patrón de SQLi"}
        ],
        "lecciones": [
            "La query completa aparece LITERAL en el error — el pentester ve la concatenación",
            "La línea del código (/app/api/v1/auth.py) revela estructura interna",
            "Versión de PostgreSQL permite buscar CVEs específicos",
            "F-strings en queries = marcador inequívoco de SQLi en Python"
        ]
    },
    {
        "id": 4,
        "titulo": "Stack trace de Node.js - path traversal",
        "status": 500,
        "contexto": "Express.js mal configurado",
        "stack": [
            "Error: ENOENT: no such file or directory, open '/var/www/uploads/../../../etc/passwd'",
            "    at Object.openSync (fs.js:476:3)",
            "    at Object.readFileSync (fs.js:377:35)",
            "    at /app/routes/files.js:23:18",
            "    at Layer.handle [as handle_request] (/app/node_modules/express/lib/router/layer.js:95:5)",
            "    at next (/app/node_modules/express/lib/router/route.js:137:13)",
            "Node.js v18.12.0, Express 4.18.2, Ubuntu 22.04"
        ],
        "pistas_por_capa": [
            {"capa": 1, "revelar": "ENOENT: error de file system"},
            {"capa": 2, "revelar": "Path traversal: /var/www/uploads/../../../etc/passwd"},
            {"capa": 3, "revelar": "Node 18.12.0 + Express 4.18.2"},
            {"capa": 4, "revelar": "Sistema operativo: Ubuntu 22.04"}
        ],
        "lecciones": [
            "El path muestra la estructura: /var/www/uploads/ es webroot",
            "Los ../../../ son el payload de path traversal que el pentester metió",
            "Express 4.18.2 es vulnerable a varios CVEs de middleware",
            "La versión de Node puede estar desactualizada (18.12 vs 20.x LTS actual)"
        ]
    },
    {
        "id": 5,
        "titulo": "Stack trace Django - debug mode en producción",
        "status": 500,
        "contexto": "DEBUG=True activado en producción (error clásico)",
        "stack": [
            "Django Version: 4.1.7",
            "Python Version: 3.9.16",
            "Exception Type: KeyError",
            "Exception Value: 'user_id'",
            "Exception Location: /app/views.py, line 142, in get_user_data",
            "Python Executable: /usr/bin/python3",
            "Python Path: ['/app', '/usr/lib/python39.zip', ...]",
            "GET /api/users/profile/999",
            "Request information: GET, /api/users/profile/999, 192.168.1.50"
        ],
        "pistas_por_capa": [
            {"capa": 1, "revelar": "Django + Python 3.9.16"},
            {"capa": 2, "revelar": "DEBUG=True — modo desarrollo activo en producción"},
            {"capa": 3, "revelar": "Path: /app/views.py line 142"},
            {"capa": 4, "revelar": "IP del cliente: 192.168.1.50"}
        ],
        "lecciones": [
            "DEBUG=True en producción es una de las peores fugas de info",
            "Revela: versiones exactas, paths internos, IPs de los requesters",
            "En este caso, el endpoint es IDOR: /api/users/profile/999",
            "La IP 192.168.1.50 indica red interna corporativa"
        ]
    },
    {
        "id": 6,
        "titulo": "Stack trace Java Spring - Actuator exposed",
        "status": 500,
        "contexto": "Spring Boot Actuator sin proteger",
        "stack": [
            "java.lang.IllegalStateException: Could not find bean 'dataSource'",
            "    at org.springframework.beans.factory.support.DefaultListableBeanFactory.getBean(DefaultListableBeanFactory.java:343)",
            "    at org.springframework.boot.actuate.autoconfigure.jdbc.DataSourceHealthIndicator.getBean(DataSourceHealthIndicator.java:51)",
            "    at org.springframework.boot.actuate.health.HealthEndpoint.health(HealthEndpoint.java:88)",
            "    at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)",
            "Spring Boot 2.7.5, Hibernate 5.6.11.Final, MySQL Connector/J 8.0.31"
        ],
        "pistas_por_capa": [
            {"capa": 1, "revelar": "Spring Boot + Hibernate"},
            {"capa": 2, "revelar": "Spring Boot Actuator endpoint /health expuesto"},
            {"capa": 3, "revelar": "Versiones: Spring 2.7.5, Hibernate 5.6.11"},
            {"capa": 4, "revelar": "MySQL Connector/J 8.0.31 — buscar CVEs"}
        ],
        "lecciones": [
            "Spring Actuator por default expone /health, /env, /beans",
            "Si el endpoint /env responde, se filtran TODAS las variables de entorno",
            "El stack trace confirma que Actuator está activo",
            "Versión 2.7.5 es vulnerable a CVE-2023-20860 (Spring Expression DoS)"
        ]
    }
]

@router.get("/detective/list")
def detective_list():
    return [{"id": s["id"], "titulo": s["titulo"], "status": s["status"]} for s in STACK_TRACES_FAMOSOS]

@router.get("/detective/{trace_id}")
def detective_get(trace_id: int):
    for s in STACK_TRACES_FAMOSOS:
        if s["id"] == trace_id:
            return s
    raise HTTPException(404, "No existe")


# =========================================================================
# MEJORA 3: GENERADOR DE SHADOW APIs POR STACK
# Predice shadow APIs según la firma del servidor
# =========================================================================

STACK_PROFILES = {
    "fastapi": {
        "firma_headers": ["server: uvicorn", "x-powered-by: fastapi"],
        "framework": "FastAPI",
        "lenguaje": "Python",
        "shadow_apis_comunes": [
            {"path": "/docs", "descripcion": "Swagger UI"},
            {"path": "/redoc", "descripcion": "ReDoc UI"},
            {"path": "/openapi.json", "descripcion": "OpenAPI schema"},
            {"path": "/api/v1/_debug", "descripcion": "Debug endpoint (dev)"},
            {"path": "/api/v1/_health", "descripcion": "Health check interno"},
            {"path": "/api/v1/internal/", "descripcion": "Directorio de rutas internas"},
            {"path": "/admin", "descripcion": "Admin panel"},
            {"path": "/test", "descripcion": "Test endpoint olvidado"},
        ]
    },
    "express": {
        "firma_headers": ["x-powered-by: express", "server: node"],
        "framework": "Express.js",
        "lenguaje": "JavaScript (Node.js)",
        "shadow_apis_comunes": [
            {"path": "/api/v1/dev", "descripcion": "Dev mode endpoint"},
            {"path": "/api/v1/test", "descripcion": "Test endpoint"},
            {"path": "/api/v1/_debug", "descripcion": "Debug"},
            {"path": "/api/v1/_internal", "descripcion": "Internal routes"},
            {"path": "/graphql", "descripcion": "GraphQL endpoint (a veces)"},
            {"path": "/socket.io/", "descripcion": "Socket.IO"},
            {"path": "/healthz", "descripcion": "Health check (K8s)"},
            {"path": "/env", "descripcion": "ENV leak (debug mode)"},
        ]
    },
    "spring": {
        "firma_headers": ["x-application-context:", "server: apache-coyote"],
        "framework": "Spring Boot",
        "lenguaje": "Java",
        "shadow_apis_comunes": [
            {"path": "/actuator", "descripcion": "Spring Boot Actuator"},
            {"path": "/actuator/env", "descripcion": "ENV leak (CRÍTICO)"},
            {"path": "/actuator/health", "descripcion": "Health check"},
            {"path": "/actuator/beans", "descripcion": "Lista de beans"},
            {"path": "/actuator/mappings", "descripcion": "URL mappings"},
            {"path": "/actuator/heapdump", "descripcion": "Heap dump (CRÍTICO)"},
            {"path": "/swagger-ui.html", "descripcion": "Swagger UI"},
            {"path": "/v3/api-docs", "descripcion": "OpenAPI v3"},
        ]
    },
    "django": {
        "firma_headers": ["x-frame-options: deny", "server: gunicorn"],
        "framework": "Django / DRF",
        "lenguaje": "Python",
        "shadow_apis_comunes": [
            {"path": "/admin/", "descripcion": "Django admin"},
            {"path": "/api/v1/", "descripcion": "DRF root"},
            {"path": "/api/v1/_debug/", "descripcion": "Debug toolbar (si DEBUG=True)"},
            {"path": "/__debug__/", "descripcion": "Django Debug Toolbar"},
            {"path": "/api/schema/", "descripcion": "DRF schema"},
            {"path": "/api/docs/", "descripcion": "Swagger"},
            {"path": "/api/auth/", "descripcion": "Auth endpoints"},
        ]
    },
    "rails": {
        "firma_headers": ["x-request-id:", "x-runtime:", "server: puma"],
        "framework": "Ruby on Rails",
        "lenguaje": "Ruby",
        "shadow_apis_comunes": [
            {"path": "/rails/info", "descripcion": "Rails info page"},
            {"path": "/rails/console", "descripcion": "Rails console (si exposed)"},
            {"path": "/api/v1/internal/", "descripcion": "Internal routes"},
            {"path": "/sidekiq", "descripcion": "Sidekiq dashboard"},
            {"path": "/admin", "descripcion": "Admin panel"},
            {"path": "/api/graphql", "descripcion": "GraphQL endpoint"},
        ]
    },
    "laravel": {
        "firma_headers": ["x-powered-by: php", "server: nginx"],
        "framework": "Laravel",
        "lenguaje": "PHP",
        "shadow_apis_comunes": [
            {"path": "/api/v1/_debug", "descripcion": "Debug"},
            {"path": "/api/v1/test", "descripcion": "Test endpoint"},
            {"path": "/telescope", "descripcion": "Laravel Telescope (dev)"},
            {"path": "/horizon", "descripcion": "Laravel Horizon (queues)"},
            {"path": "/admin", "descripcion": "Admin panel"},
            {"path": "/_ignition/health-check", "descripcion": "Ignition error page"},
        ]
    }
}

@router.get("/stack/list")
def stack_list():
    return [{"id": k, "framework": v["framework"], "lenguaje": v["lenguaje"]} for k, v in STACK_PROFILES.items()]

@router.get("/stack/detect")
def stack_detect(headers: str = Query("", description="Headers HTTP separados por |")):
    """Detecta el stack probable según los headers del response."""
    headers_lower = headers.lower()
    matches = []
    for stack_id, profile in STACK_PROFILES.items():
        score = 0
        matched_headers = []
        for firma in profile["firma_headers"]:
            if firma.lower() in headers_lower:
                score += 1
                matched_headers.append(firma)
        if score > 0:
            matches.append({
                "stack_id": stack_id,
                "framework": profile["framework"],
                "score": score,
                "matched_headers": matched_headers
            })
    matches.sort(key=lambda x: x["score"], reverse=True)
    return {"matches": matches, "best_guess": matches[0] if matches else None}


@router.get("/stack/{stack_id}")
def stack_get(stack_id: str):
    if stack_id not in STACK_PROFILES:
        raise HTTPException(404, "Stack no reconocido")
    return STACK_PROFILES[stack_id]


# =========================================================================
# MEJORA 4: MODO TIME-TRAVEL
# Replay de auditoría: 30 min de tráfico simulado
# =========================================================================

TIME_TRAVEL_DB = Path(__file__).parent / "db" / "time_travel.db"
TIME_TRAVEL_DB.parent.mkdir(parents=True, exist_ok=True)

def init_time_travel_db():
    conn = sqlite3.connect(TIME_TRAVEL_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            ip TEXT NOT NULL,
            user TEXT,
            method TEXT NOT NULL,
            path TEXT NOT NULL,
            status_code INTEGER NOT NULL,
            user_agent TEXT,
            bytes_sent INTEGER,
            suspicious INTEGER DEFAULT 0,
            anomaly_type TEXT
        )
    """)
    conn.commit()
    conn.close()

init_time_travel_db()

# Patrones de tráfico "normal"
NORMAL_USERS = ["alice", "bob", "carlos", "maria", "diego", "ana", "juan", "sofia"]
NORMAL_PATHS = [
    "/", "/api/v1/servidores", "/api/v1/servidores/1", "/api/v1/servidores/2",
    "/api/v1/servidores/3", "/docs", "/api/v1/status",
    "/", "/", "/", "/api/v1/servidores",  # más repeticiones de paths comunes
]
NORMAL_IPS = ["192.168.1.10", "192.168.1.11", "192.168.1.12", "10.0.0.50", "10.0.0.51"]
NORMAL_UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) Firefox/91.0"
]

# Patrones de ataque
ATTACKER_IPS = ["45.33.32.156", "185.220.101.50", "203.0.113.42"]
ATTACK_PATTERNS = [
    {"path": "/api/v1/auth/admin", "status": 200, "anomaly": "shadow_api_access", "ua": "sqlmap/1.5"},
    {"path": "/api/v1/debug", "status": 200, "anomaly": "info_disclosure", "ua": "curl/7.68.0"},
    {"path": "/admin", "status": 404, "anomaly": "path_fuzzing", "ua": "python-requests/2.28.0"},
    {"path": "/api/v1/auditoria/infraestructura", "status": 500, "anomaly": "sqli_attempt", "ua": "sqlmap/1.5"},
    {"path": "/.env", "status": 404, "anomaly": "env_leak_attempt", "ua": "curl/7.68.0"},
    {"path": "/wp-admin", "status": 404, "anomaly": "wordpress_scan", "ua": "Nikto/2.5"},
    {"path": "/api/v1/internal/admin/panel", "status": 200, "anomaly": "admin_access", "ua": "python-requests/2.28.0"},
    {"path": "/api/v1/servidores/../../etc/passwd", "status": 500, "anomaly": "path_traversal", "ua": "Mozilla/5.0"},
]

@router.post("/timetravel/generate/{scenario_id}")
def timetravel_generate(scenario_id: int, minutes: int = 30):
    """Genera un escenario de auditoría simulada."""
    scenarios = {
        1: {"name": "Shadow API access", "injection_at": 12, "attack_pattern": 0},
        2: {"name": "SQLi en endpoint auditoría", "injection_at": 18, "attack_pattern": 3},
        3: {"name": "Info disclosure masivo", "injection_at": 5, "attack_pattern": 1},
        4: {"name": "Path traversal campaign", "injection_at": 22, "attack_pattern": 7},
    }
    if scenario_id not in scenarios:
        raise HTTPException(404, "Escenario no existe")
    scenario = scenarios[scenario_id]

    # Limpiar log previo
    conn = sqlite3.connect(TIME_TRAVEL_DB)
    conn.execute("DELETE FROM audit_log")
    conn.commit()
    conn.close()

    # Generar eventos
    start_time = datetime.utcnow() - timedelta(minutes=minutes)
    events = []

    for sec in range(minutes * 60):
        ts = start_time + timedelta(seconds=sec)

        # Tráfico normal: 0-3 requests por segundo
        for _ in range(random.randint(0, 3)):
            events.append({
                "timestamp": ts.isoformat(),
                "ip": random.choice(NORMAL_IPS),
                "user": random.choice(NORMAL_USERS),
                "method": "GET",
                "path": random.choice(NORMAL_PATHS),
                "status_code": random.choices([200, 304, 404], weights=[85, 10, 5])[0],
                "user_agent": random.choice(NORMAL_UAS),
                "bytes_sent": random.randint(200, 5000),
                "suspicious": 0,
                "anomaly_type": None
            })

        # Inyectar ataque en el minuto configurado
        attack_minute = scenario["injection_at"]
        if sec == attack_minute * 60:
            pattern = ATTACK_PATTERNS[scenario["attack_pattern"]]
            for i in range(random.randint(3, 8)):
                attack_ts = ts + timedelta(seconds=i * 30)
                events.append({
                    "timestamp": attack_ts.isoformat(),
                    "ip": random.choice(ATTACKER_IPS),
                    "user": None,
                    "method": "GET",
                    "path": pattern["path"],
                    "status_code": pattern["status"],
                    "user_agent": pattern["ua"],
                    "bytes_sent": random.randint(100, 8000),
                    "suspicious": 1,
                    "anomaly_type": pattern["anomaly"]
                })

    # Insertar todos
    conn = sqlite3.connect(TIME_TRAVEL_DB)
    for e in events:
        conn.execute("""
            INSERT INTO audit_log (timestamp, ip, user, method, path, status_code, user_agent, bytes_sent, suspicious, anomaly_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (e["timestamp"], e["ip"], e["user"], e["method"], e["path"], e["status_code"], e["user_agent"], e["bytes_sent"], e["suspicious"], e["anomaly_type"]))
    conn.commit()
    total = conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
    suspicious = conn.execute("SELECT COUNT(*) FROM audit_log WHERE suspicious=1").fetchone()[0]
    conn.close()

    return {
        "scenario": scenario["name"],
        "total_events": total,
        "suspicious_events": suspicious,
        "duration_minutes": minutes,
        "first_event": events[0]["timestamp"] if events else None,
        "tip": "Buscá el primer evento sospechoso con ?cursor=N"
    }

@router.get("/timetravel/log")
def timetravel_log(cursor: int = 0, limit: int = 50, only_suspicious: bool = False):
    """Devuelve eventos del log paginados."""
    conn = sqlite3.connect(TIME_TRAVEL_DB)
    conn.row_factory = sqlite3.Row
    if only_suspicious:
        rows = conn.execute("SELECT * FROM audit_log WHERE suspicious=1 ORDER BY id LIMIT ? OFFSET ?", (limit, cursor)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM audit_log ORDER BY id LIMIT ? OFFSET ?", (limit, cursor)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@router.get("/timetravel/replay/{event_id}")
def timetravel_replay(event_id: int):
    """Reproduce un evento específico: muestra el contexto antes y después."""
    conn = sqlite3.connect(TIME_TRAVEL_DB)
    conn.row_factory = sqlite3.Row
    target = conn.execute("SELECT * FROM audit_log WHERE id=?", (event_id,)).fetchone()
    if not target:
        conn.close()
        raise HTTPException(404, "Evento no existe")
    # 5 eventos antes y 5 después
    before = conn.execute("SELECT * FROM audit_log WHERE id < ? ORDER BY id DESC LIMIT 5", (event_id,)).fetchall()
    after = conn.execute("SELECT * FROM audit_log WHERE id > ? ORDER BY id LIMIT 5", (event_id,)).fetchall()
    conn.close()
    return {
        "event": dict(target),
        "before": [dict(r) for r in reversed(before)],
        "after": [dict(r) for r in after]
    }

@router.get("/timetravel/scenarios")
def timetravel_scenarios():
    return [
        {"id": 1, "name": "Shadow API access", "description": "Un atacante escanea y encuentra /api/v1/auth/admin"},
        {"id": 2, "name": "SQLi en endpoint auditoría", "description": "Inyección SQL desde sqlmap"},
        {"id": 3, "name": "Info disclosure masivo", "description": "Curl scrapeando /api/v1/debug"},
        {"id": 4, "name": "Path traversal campaign", "description": "Escaneo de /../../../etc/passwd"},
    ]
