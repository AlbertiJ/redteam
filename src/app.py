#!/usr/bin/env python3
"""
RedTeam Lab v4.0 — Laboratorio de API Discovery + DB Builder + Detective de Bugs + Tracking
Microservicio FastAPI con:
  • Shadow APIs escondidas
  • Information disclosure
  • Menú de práctica por URL (?nivel=X&sqli=on&xxe=on&ssrf=off...)
  • Tracking de actividad (clicks/búsquedas del usuario)
  • Builder de DBs (7 precargadas + 3 custom)
  • Endpoint de escenarios resueltos con reveal
  • Documentación inline por código de error

Levanta con:  python mi_api_local.py
"""

from fastapi import FastAPI, HTTPException, Request, Query, Cookie, Response
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
from mejoras import router as mejoras_router
from usuarios import login as usuario_login, logout as usuario_logout, cargar_usuario, guardar_usuario, obtener_dashboard, registrar_bug_resuelto, registrar_db_custom, sumar_tiempo, obtener_ranking
import json
import os
import time
import sqlite3
import logging
from datetime import datetime
from pathlib import Path

# === LOGGING ===
LOG_FILE = BASE_DIR / "redteam.log" if (BASE_DIR := Path(__file__).parent.parent).exists() else Path("redteam.log")
logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger("redteam")

# =========================================================================
# CONFIGURACIÓN
# =========================================================================

BASE_DIR = Path(__file__).parent
DB_DIR = BASE_DIR / "db" / "user_dbs"
DB_DIR.mkdir(parents=True, exist_ok=True)
TRACKER_DB = BASE_DIR / "db" / "actividad.db"

# Inicializar app
app = FastAPI(
    title="RedTeam - Lab de Pentesting de Gestión de Infraestructura",
    description="RedTeam - Laboratorio de pentesting ético de la Provincia de Buenos Aires.",
    version="3.0.0",
)

# Montar archivos estáticos (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Montar router de las 4 mejoras
app.include_router(mejoras_router, prefix="/api/v1")

# =========================================================================
# DB DE TRACKING — clicks y búsquedas del usuario
# =========================================================================

def init_tracker_db():
    conn = sqlite3.connect(TRACKER_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS actividad (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            tipo TEXT NOT NULL,
            target TEXT,
            contexto TEXT,
            session_id TEXT
        )
    """)
    conn.commit()
    conn.close()

init_tracker_db()

# =========================================================================
# DATOS CORE DE LA API
# =========================================================================

BASE_DATOS_SERVIDORES = {
    1: {"id": 1, "nombre": "srv-delta-linux",   "ip": "10.20.30.40",  "so": "Ubuntu 22.04 LTS",   "estado": "activo"},
    2: {"id": 2, "nombre": "ad-windows-pba",     "ip": "10.20.30.41",  "so": "Windows Server 2022","estado": "activo"},
    3: {"id": 3, "nombre": "fw-perimetral-gob",  "ip": "10.20.30.1",   "so": "pfSense 2.7",        "estado": "activo"},
    4: {"id": 4, "nombre": "bd-sensible-minint", "ip": "10.20.40.50",  "so": "PostgreSQL 14",       "estado": "restringido"},
    5: {"id": 5, "nombre": "srv-legacy-2019",    "ip": "10.20.30.99",  "so": "Debian 9",            "estado": "deprecado"},
}

class Servidor(BaseModel):
    id: int
    nombre: str
    ip: str
    so: str
    estado: str

class PayloadAuditoria(BaseModel):
    comando: str

class TrackEvent(BaseModel):
    tipo: str  # "click", "busqueda", "navegacion", "escenario"
    target: str
    contexto: Optional[str] = ""
    session_id: Optional[str] = "anon"

# =========================================================================
# ENDPOINTS OFICIALES
# =========================================================================

@app.get("/", response_class=HTMLResponse, tags=["Raíz"])
def raiz():
    return HTMLResponse(content=leer_html("index.html"), status_code=200)

# HTMLs del lab - rutas explícitas
HTMLS_LAB = [
    "practicas.html", "dbbuilder.html", "api_visual.html",
    "dashboard.html", "errores.html", "mejoras.html",
    "detective.html", "wizard.html", "historial.html",
    "resumen-visual.html", "ranking.html"
]

@app.get("/{nombre_html}", response_class=HTMLResponse, tags=["HTMLs"])
def servir_html(nombre_html: str):
    # Solo servir HTMLs conocidos (whitelist para no chocar con /api/...)
    if nombre_html in HTMLS_LAB:
        return HTMLResponse(content=leer_html(nombre_html), status_code=200)
    # Si no es un HTML conocido, 404 (deja que el routing normal se encargue)
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="Página no encontrada")

@app.get("/api/v1/servidores", response_model=List[Servidor], tags=["Infraestructura"])
def listar_servidores():
    return [s for s in BASE_DATOS_SERVIDORES.values() if s["estado"] != "deprecado"]

@app.get("/api/v1/servidores/{sid}", response_model=Servidor, tags=["Infraestructura"])
def obtener_servidor(sid: int):
    if sid not in BASE_DATOS_SERVIDORES:
        raise HTTPException(status_code=404, detail="Servidor no indexado")
    return BASE_DATOS_SERVIDORES[sid]

# =========================================================================
# SHADOW APIs
# =========================================================================

@app.get("/api/v1/internal/health", include_in_schema=False)
def shadow_health():
    return {
        "status": "ok",
        "uptime_sec": int(time.time()) % 86400,
        "version_interna": "3.0.0-build.2026-06-10",
        "deployado_por": "deploy-bot@mininterior.gob.ar"
    }

@app.get("/api/v1/debug", include_in_schema=False)
def shadow_debug():
    return {
        "debug": True, "env": "production",
        "db_host": "10.20.40.50", "db_user": "api_gba_ro",
        "ultima_deployment": "2026-06-10T14:00:00Z",
        "developer_email": "juan.perez@mininterior.gob.ar (ya no trabaja acá)"
    }

@app.get("/api/v0/servidores", include_in_schema=False)
def shadow_v0_legacy():
    return {
        "version": "v0", "estado": "DEPRECADO",
        "data": list(BASE_DATOS_SERVIDORES.values()),
        "advertencia": "Este endpoint no debería estar en producción"
    }

@app.get("/api/v1/servidores/deprecados", include_in_schema=False)
def shadow_deprecados():
    return [s for s in BASE_DATOS_SERVIDORES.values() if s["estado"] == "deprecado"]

@app.get("/api/v1/auth/admin", include_in_schema=False)
def shadow_admin_no_doc():
    return {
        "status": "Acceso denegado",
        "motivo": "Falta Bearer token",
        "endpoint_real_admin": "/api/v1/internal/admin/panel"
    }

@app.get("/api/v1/internal/admin/panel", include_in_schema=False)
def shadow_admin_panel():
    return {
        "panel_admin": "configuracion_interna",
        "usuarios_admin": ["root", "deploy-bot"],
        "recomendacion": "BLOQUEAR EN PRODUCCIÓN"
    }

@app.get("/api/v1/test", include_in_schema=False)
def shadow_test():
    return {"test": "ok", "message": "Shadow API detectada"}

@app.get("/api/v1/metadatos", include_in_schema=False)
def information_disclosure():
    return {
        "framework": "FastAPI 0.110.0",
        "asgi_server": "uvicorn 0.27.1",
        "python_version": "3.11.6",
        "hostname": "api-gba-prod-01",
        "rutas_registradas_count": 11,
        "headers_expuestos": ["Server", "X-Powered-By"]
    }

# =========================================================================
# AUDITORÍA — comportamiento según nivel/módulos activos
# =========================================================================

@app.post("/api/v1/auditoria/infraestructura", tags=["Auditoria"])
def evaluar_payload(
    payload: PayloadAuditoria,
    request: Request,
    sqli: bool = Query(False, description="Activa detección de SQLi"),
    xxe: bool = Query(False, description="Activa detección de XXE"),
    ssrf: bool = Query(False, description="Activa detección de SSRF"),
    cmdi: bool = Query(False, description="Activa Command Injection"),
):
    """
    Endpoint de auditoría configurable.
    Activá los vectores con: ?sqli=on&xxe=on&ssrf=on&cmdi=on
    """
    entrada = payload.comando.lower()
    detecciones = []

    if sqli and any(f in entrada for f in ["drop", "or 1=1", "delete", "union select", "xp_cmdshell"]):
        detecciones.append(("SQLi", "CRITICO", "Inyección SQL detectada"))
    if xxe and ("<!entity" in entrada or "system \"file:///" in entrada or "<!doctype" in entrada):
        detecciones.append(("XXE", "CRITICO", "XML External Entity detectada"))
    if ssrf and any(f in entrada for f in ["http://169.254.169.254", "file:///", "localhost", "127.0.0.1", "metadata.google"]):
        detecciones.append(("SSRF", "ALTO", "Server-Side Request Forgery detectado"))
    if cmdi and any(f in entrada for f in ["; ls", "; cat", "| nc", "$(", "`"]):
        detecciones.append(("CMDi", "CRITICO", "Command Injection detectado"))

    if detecciones:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detecciones": [{"tipo": d[0], "severidad": d[1], "msg": d[2]} for d in detecciones],
                "stack_trace": [
                    f"File \"/app/api/v1/auditoria.py\", line 47",
                    f"  query = f\"SELECT * FROM servidores WHERE nombre = '{payload.comando}'\"",
                    f"psycopg2.errors.SyntaxError cerca de \"{entrada[:20]}\""
                ],
                "modulos_activos": {"sqli": sqli, "xxe": xxe, "ssrf": ssrf, "cmdi": cmdi},
                "recomendacion": "Usar ORM con prepared statements. Validar inputs con allowlist."
            }
        )

    return {
        "status": "limpio",
        "modulos_activos": {"sqli": sqli, "xxe": xxe, "ssrf": ssrf, "cmdi": cmdi},
        "resultado": f"Procesado: {payload.comando}"
    }

# =========================================================================
# TRACKING — registra actividad del usuario
# =========================================================================

@app.post("/api/v1/track", include_in_schema=False)
def track_event(event: TrackEvent):
    conn = sqlite3.connect(TRACKER_DB)
    conn.execute(
        "INSERT INTO actividad (timestamp, tipo, target, contexto, session_id) VALUES (?, ?, ?, ?, ?)",
        (datetime.utcnow().isoformat(), event.tipo, event.target, event.contexto, event.session_id)
    )
    conn.commit()
    conn.close()
    return {"ok": True}

@app.get("/api/v1/track/recientes", include_in_schema=False)
def track_recientes(limit: int = 50):
    conn = sqlite3.connect(TRACKER_DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM actividad ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# =========================================================================
# DB BUILDER — 7 precargadas + 3 custom
# =========================================================================

DB_PREDEFINIDAS = {
    "musica": {
        "descripcion": "Catálogo de artistas y álbumes",
        "sugerencia_campos": "nombre, artista, anio, genero, duracion_seg",
        "datos": [
            {"id": 1, "nombre": "Dark Side of the Moon", "artista": "Pink Floyd",       "anio": 1973, "genero": "Rock Progresivo", "duracion_seg": 2583},
            {"id": 2, "nombre": "Thriller",              "artista": "Michael Jackson",  "anio": 1982, "genero": "Pop",             "duracion_seg": 2542},
            {"id": 3, "nombre": "Rumours",               "artista": "Fleetwood Mac",    "anio": 1977, "genero": "Rock",            "duracion_seg": 2580},
            {"id": 4, "nombre": "Back in Black",         "artista": "AC/DC",            "anio": 1980, "genero": "Hard Rock",       "duracion_seg": 2541},
            {"id": 5, "nombre": "The Wall",              "artista": "Pink Floyd",       "anio": 1979, "genero": "Rock Progresivo", "duracion_seg": 4860},
            {"id": 6, "nombre": "Led Zeppelin IV",       "artista": "Led Zeppelin",     "anio": 1971, "genero": "Hard Rock",       "duracion_seg": 2551},
            {"id": 7, "nombre": "Abbey Road",            "artista": "The Beatles",      "anio": 1969, "genero": "Rock",            "duracion_seg": 2843},
            {"id": 8, "nombre": "Nevermind",             "artista": "Nirvana",          "anio": 1991, "genero": "Grunge",          "duracion_seg": 2904},
        ]
    },
    "peliculas": {
        "descripcion": "Películas icónicas del cine",
        "sugerencia_campos": "titulo, director, anio, genero, duracion_min, rating",
        "datos": [
            {"id": 1, "titulo": "The Godfather",    "director": "Francis Ford Coppola", "anio": 1972, "genero": "Drama",      "duracion_min": 175, "rating": 9.2},
            {"id": 2, "titulo": "Pulp Fiction",    "director": "Quentin Tarantino",   "anio": 1994, "genero": "Crimen",     "duracion_min": 154, "rating": 8.9},
            {"id": 3, "titulo": "The Dark Knight",  "director": "Christopher Nolan",    "anio": 2008, "genero": "Acción",     "duracion_min": 152, "rating": 9.0},
            {"id": 4, "titulo": "Forrest Gump",     "director": "Robert Zemeckis",      "anio": 1994, "genero": "Drama",      "duracion_min": 142, "rating": 8.8},
            {"id": 5, "titulo": "Inception",        "director": "Christopher Nolan",    "anio": 2010, "genero": "Sci-Fi",     "duracion_min": 148, "rating": 8.8},
            {"id": 6, "titulo": "Matrix",           "director": "Wachowski Sisters",    "anio": 1999, "genero": "Sci-Fi",     "duracion_min": 136, "rating": 8.7},
            {"id": 7, "titulo": "El Secreto de sus Ojos", "director": "Juan José Campanella", "anio": 2009, "genero": "Drama", "duracion_min": 129, "rating": 8.2},
        ]
    },
    "paises": {
        "descripcion": "Información de países del mundo",
        "sugerencia_campos": "nombre, capital, poblacion, continente, idioma_oficial, codigo_tel",
        "datos": [
            {"id": 1, "nombre": "Argentina",    "capital": "Buenos Aires",     "poblacion": 46044703,  "continente": "América",   "idioma_oficial": "Español",      "codigo_tel": "+54"},
            {"id": 2, "nombre": "Brasil",       "capital": "Brasilia",         "poblacion": 215313498, "continente": "América",   "idioma_oficial": "Portugués",    "codigo_tel": "+55"},
            {"id": 3, "nombre": "Japón",        "capital": "Tokio",            "poblacion": 125709000, "continente": "Asia",      "idioma_oficial": "Japonés",      "codigo_tel": "+81"},
            {"id": 4, "nombre": "Alemania",     "capital": "Berlín",           "poblacion": 83149300,  "continente": "Europa",    "idioma_oficial": "Alemán",       "codigo_tel": "+49"},
            {"id": 5, "nombre": "Australia",    "capital": "Canberra",         "poblacion": 25788215,  "continente": "Oceanía",   "idioma_oficial": "Inglés",       "codigo_tel": "+61"},
            {"id": 6, "nombre": "Egipto",       "capital": "El Cairo",         "poblacion": 104258327, "continente": "África",    "idioma_oficial": "Árabe",        "codigo_tel": "+20"},
            {"id": 7, "nombre": "Canadá",       "capital": "Ottawa",           "poblacion": 38929902,  "continente": "América",   "idioma_oficial": "Inglés/Francés","codigo_tel": "+1"},
        ]
    },
    "libros": {
        "descripcion": "Libros clásicos de la literatura",
        "sugerencia_campos": "titulo, autor, anio, genero, paginas, isbn",
        "datos": [
            {"id": 1, "titulo": "Cien Años de Soledad",  "autor": "Gabriel García Márquez",  "anio": 1967, "genero": "Realismo Mágico", "paginas": 471, "isbn": "978-0307474728"},
            {"id": 2, "titulo": "1984",                  "autor": "George Orwell",          "anio": 1949, "genero": "Distopía",        "paginas": 326, "isbn": "978-0451524935"},
            {"id": 3, "titulo": "Don Quijote",           "autor": "Miguel de Cervantes",    "anio": 1605, "genero": "Novela",          "paginas": 863, "isbn": "978-8424116057"},
            {"id": 4, "titulo": "El Principito",         "autor": "Antoine de Saint-Exupéry","anio": 1943,"genero": "Fábula",          "paginas": 96,  "isbn": "978-0156012195"},
            {"id": 5, "titulo": "Rayuela",               "autor": "Julio Cortázar",         "anio": 1963, "genero": "Novela",          "paginas": 736, "isbn": "978-0394752846"},
        ]
    },
    "deportes": {
        "descripcion": "Deportes y eventos olímpicos",
        "sugerencia_campos": "nombre, jugadores, origen, tipo, primer_anio",
        "datos": [
            {"id": 1, "nombre": "Fútbol",     "jugadores": 11,   "origen": "Inglaterra",  "tipo": "Equipo",   "primer_anio": 1863},
            {"id": 2, "nombre": "Básquet",    "jugadores": 5,    "origen": "EE.UU.",      "tipo": "Equipo",   "primer_anio": 1891},
            {"id": 3, "nombre": "Tenis",      "jugadores": 1,    "origen": "Francia",     "tipo": "Individual","primer_anio": 1873},
            {"id": 4, "nombre": "Rugby",      "jugadores": 15,   "origen": "Inglaterra",  "tipo": "Equipo",   "primer_anio": 1823},
            {"id": 5, "nombre": "Ajedrez",    "jugadores": 1,    "origen": "India",       "tipo": "Individual","primer_anio": 1500},
        ]
    },
    "comidas": {
        "descripcion": "Platos típicos del mundo",
        "sugerencia_campos": "nombre, pais_origen, ingredientes_principales, tipo, picante",
        "datos": [
            {"id": 1, "nombre": "Asado",          "pais_origen": "Argentina",  "ingredientes_principales": "carne de res, sal, chimichurri", "tipo": "Plato principal", "picante": False},
            {"id": 2, "nombre": "Sushi",          "pais_origen": "Japón",     "ingredientes_principales": "arroz, pescado crudo, alga",      "tipo": "Plato principal", "picante": False},
            {"id": 3, "nombre": "Tacos",          "pais_origen": "México",    "ingredientes_principales": "tortilla, carne, salsa",         "tipo": "Plato principal", "picante": True},
            {"id": 4, "nombre": "Pizza",          "pais_origen": "Italia",    "ingredientes_principales": "masa, tomate, queso",            "tipo": "Plato principal", "picante": False},
            {"id": 5, "nombre": "Paella",         "pais_origen": "España",    "ingredientes_principales": "arroz, mariscos, azafrán",       "tipo": "Plato principal", "picante": False},
            {"id": 6, "nombre": "Empanadas",      "pais_origen": "Argentina",  "ingredientes_principales": "masa, carne, cebolla",           "tipo": "Entrada",         "picante": False},
        ]
    },
    "tecnologia": {
        "descripcion": "Lenguajes de programación y frameworks",
        "sugerencia_campos": "nombre, creador, anio_creacion, paradigma, tipado, uso_principal",
        "datos": [
            {"id": 1, "nombre": "Python",      "creador": "Guido van Rossum",  "anio_creacion": 1991, "paradigma": "Multiparadigma", "tipado": "Dinámico",  "uso_principal": "Backend, Data Science, IA"},
            {"id": 2, "nombre": "JavaScript",  "creador": "Brendan Eich",      "anio_creacion": 1995, "paradigma": "Multiparadigma", "tipado": "Dinámico",  "uso_principal": "Frontend, Backend (Node)"},
            {"id": 3, "nombre": "Rust",        "creador": "Graydon Hoare",     "anio_creacion": 2010, "paradigma": "Funcional/Imperativo","tipado": "Estático", "uso_principal": "Sistemas, Performance"},
            {"id": 4, "nombre": "Go",          "creador": "Google (Rob Pike)", "anio_creacion": 2009, "paradigma": "Imperativo",    "tipado": "Estático",  "uso_principal": "Cloud, Microservicios"},
            {"id": 5, "nombre": "TypeScript",  "creador": "Microsoft",         "anio_creacion": 2012, "paradigma": "Orientado a Objetos", "tipado": "Estático", "uso_principal": "Frontend escalable"},
        ]
    },
}

@app.get("/api/v1/dbbuilder/predefinidas", include_in_schema=False)
def listar_dbs_predefinidas():
    return [
        {"nombre": k, "descripcion": v["descripcion"], "sugerencia_campos": v["sugerencia_campos"], "registros": len(v["datos"])}
        for k, v in DB_PREDEFINIDAS.items()
    ]

@app.get("/api/v1/dbbuilder/datos/{nombre}", include_in_schema=False)
def obtener_datos_db(nombre: str):
    """Obtiene los datos de una DB predefinida."""
    if nombre not in DB_PREDEFINIDAS:
        raise HTTPException(404, f"DB '{nombre}' no existe")
    return {
        "nombre": nombre,
        "descripcion": DB_PREDEFINIDAS[nombre]["descripcion"],
        "sugerencia_campos": DB_PREDEFINIDAS[nombre]["sugerencia_campos"],
        "datos": DB_PREDEFINIDAS[nombre]["datos"]
    }

class DBCustomCreate(BaseModel):
    nombre: str
    campos: List[str]  # ej: ["id", "nombre", "email"]
    datos: List[Dict[str, Any]]  # ej: [{"id": 1, "nombre": "Juan", "email": "..."}]

@app.post("/api/v1/dbbuilder/crear", include_in_schema=False)
def crear_db_custom(db_def: DBCustomCreate):
    """Crea una DB custom con 3-100 campos, validado."""
    if len(db_def.campos) < 3 or len(db_def.campos) > 100:
        raise HTTPException(400, "La DB debe tener entre 3 y 100 campos")
    if "id" not in db_def.campos:
        raise HTTPException(400, "La DB debe tener un campo 'id'")
    if len(db_def.datos) > 10000:
        raise HTTPException(400, "Máximo 10.000 registros")

    db_path = DB_DIR / f"{db_def.nombre}.db"
    conn = sqlite3.connect(db_path)
    cols = ", ".join([f'"{c}" TEXT' for c in db_def.campos])
    conn.execute(f'CREATE TABLE IF NOT EXISTS "{db_def.nombre}" ({cols})')

    cols_quoted = ", ".join([f'"{c}"' for c in db_def.campos])
    for row in db_def.datos:
        placeholders = ", ".join(["?" for _ in db_def.campos])
        values = [str(row.get(c, "")) for c in db_def.campos]
        conn.execute(
            f'INSERT INTO "{db_def.nombre}" ({cols_quoted}) VALUES ({placeholders})',
            values
        )
    conn.commit()
    conn.close()
    return {"ok": True, "path": str(db_path), "registros": len(db_def.datos)}

@app.get("/api/v1/dbbuilder/custom", include_in_schema=False)
def listar_dbs_custom():
    """Lista las DBs custom creadas por el usuario."""
    return [{"nombre": p.stem, "path": p.name} for p in DB_DIR.glob("*.db")]

@app.get("/api/v1/dbbuilder/consultar", include_in_schema=False)
def consultar_db(
    db: str = Query(..., description="Nombre de la DB"),
    campo: Optional[str] = Query(None, description="Campo a proyectar"),
    filtro: Optional[str] = Query(None, description="Filtro tipo SQL WHERE"),
    limite: int = Query(100, description="Límite de resultados"),
):
    """
    Consulta una DB (predefinida o custom).
    ⚠️ Acepta 'filtro' como string — esto es INTENCIONAL para entrenar
    la detección de SQLi en el lab.
    """
    # DBs predefinidas
    if db in DB_PREDEFINIDAS:
        data = DB_PREDEFINIDAS[db]["datos"]
        if filtro:
            try:
                filtrados = []
                for row in data:
                    eval_globals = {"__builtins__": {}}
                    eval_locals = {c: row.get(c) for c in row.keys()}
                    if eval(filtro, eval_globals, eval_locals):
                        filtrados.append(row)
                data = filtrados
            except Exception as e:
                return {"error": f"Filtro inválido: {e}", "datos": []}
        if campo:
            data = [{c: r.get(c) for c in (campo.split(",") if "," in campo else [campo])} for r in data]
        return {"fuente": "predefinida", "total": len(data), "datos": data[:limite]}

    # DBs custom
    db_path = DB_DIR / f"{db}.db"
    if not db_path.exists():
        raise HTTPException(404, f"DB '{db}' no existe")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        if filtro and (";" in filtro or "--" in filtro or "union" in filtro.lower() or "drop" in filtro.lower()):
            return JSONResponse(status_code=500, content={
                "error": "Posible SQLi detectado en filtro",
                "alerta": "CRITICO",
                "recomendacion": "Sanitizar inputs del usuario. Usar prepared statements."
            })

        if filtro:
            sql = f'SELECT * FROM "{db}" WHERE {filtro} LIMIT ?'
            rows = conn.execute(sql, (limite,)).fetchall()
        else:
            sql = f'SELECT * FROM "{db}" LIMIT ?'
            rows = conn.execute(sql, (limite,)).fetchall()
        return {"fuente": "custom", "total": len(rows), "datos": [dict(r) for r in rows]}
    finally:
        conn.close()

# =========================================================================
# ESCENARIOS RESUELTOS — lógica paso a paso
# =========================================================================

ESCENARIOS = [
    {
        "id": 1,
        "titulo": "Shadow API en producción",
        "categoria": "API Discovery",
        "vector": "API no documentada en Swagger",
        "descripcion": "Un desarrollador deployó un endpoint de health check interno que quedó accesible públicamente.",
        "logs_originales": [
            "GET /api/v1/internal/health → 200 OK",
            "Response: {status: ok, version_interna: '2.4.1', deployado_por: 'deploy-bot@mininterior.gob.ar'}"
        ],
        "paso_a_paso": [
            "1. Hacer reconocimiento pasivo: leer /openapi.json de la API oficial",
            "2. Comparar rutas documentadas vs rutas que responden",
            "3. Probar paths típicos: /internal/, /debug/, /test/, /admin/",
            "4. Detectar /api/v1/internal/health que NO está en Swagger",
            "5. La ruta devuelve metadatos internos (versión, deployer email) → information disclosure",
            "6. Clasificar como Shadow API con severidad ALTO"
        ],
        "mitigacion": [
            "Eliminar endpoints innecesarios antes de producción",
            "Usar routers separados para admin/internal vs público",
            "Implementar allowlist de IPs para rutas internas",
            "Auditoría periódica con descubrimiento de rutas (como este lab)"
        ]
    },
    {
        "id": 2,
        "titulo": "SQL Injection en endpoint de búsqueda",
        "categoria": "Inyección",
        "vector": "SQLi clásico con OR 1=1",
        "descripcion": "El endpoint de auditoría concatena input del usuario en una query SQL sin sanitizar.",
        "logs_originales": [
            "POST /api/v1/auditoria/infraestructura",
            "Body: {comando: \"' OR 1=1 --\"}",
            "Response: 500 Internal Server Error + stack trace con query expuesta"
        ],
        "paso_a_paso": [
            "1. Identificar endpoints que aceptan strings y los procesan",
            "2. Probar caracteres especiales: comillas, paréntesis, comentarios",
            "3. Inyectar ' OR 1=1 -- que cierra la query y agrega condición verdadera",
            "4. El backend responde 500 con stack trace revelando la query real",
            "5. Confirmar SQLi: la query concatenada aparece en el error",
            "6. Intentar UNION SELECT para exfiltrar otras tablas"
        ],
        "mitigacion": [
            "Usar ORM con prepared statements (SQLAlchemy, Django ORM)",
            "Validar input con allowlist (solo letras/números)",
            "NUNCA concatenar strings en queries SQL",
            "Implementar WAF (ModSecurity, Cloudflare) en el borde",
            "Deshabilitar stack traces en producción (DEBUG=False)"
        ]
    },
    {
        "id": 3,
        "titulo": "Information Disclosure en /metadatos",
        "categoria": "Information Disclosure",
        "vector": "Endpoint de debug que revela versiones y rutas",
        "descripcion": "El endpoint /api/v1/metadatos expone versiones exactas del stack, hostname y conteo de rutas.",
        "logs_originales": [
            "GET /api/v1/metadatos → 200 OK",
            "Response: {framework: 'FastAPI 0.110.0', python_version: '3.11.6', hostname: 'api-gba-prod-01'}"
        ],
        "paso_a_paso": [
            "1. Buscar endpoints comunes: /metadatos, /info, /status, /version",
            "2. Encontrar /api/v1/metadatos que responde con info del servidor",
            "3. La versión exacta de FastAPI (0.110.0) permite buscar CVEs específicos",
            "4. El hostname interno (api-gba-prod-01) ayuda a mapear la infraestructura",
            "5. El conteo de rutas (11) es una pista: hay más rutas que las que muestra Swagger"
        ],
        "mitigacion": [
            "Eliminar endpoints de debug en producción",
            "Si se necesitan, proteger con autenticación Bearer",
            "Ofuscar versiones (mostrar solo major version)",
            "Configurar headers HTTP para NO exponer framework (X-Powered-By, Server)"
        ]
    },
    {
        "id": 4,
        "titulo": "Acceso a datos por modificación de URL",
        "categoria": "IDOR / URL Manipulation",
        "vector": "Inferencia de recursos por enumeración",
        "descripcion": "El endpoint /api/v1/servidores/{id} no valida autorización: cualquier usuario autenticado puede ver cualquier servidor.",
        "logs_originales": [
            "GET /api/v1/servidores/1 → 200 OK (servidor propio)",
            "GET /api/v1/servidores/4 → 200 OK (servidor restringido de otra área)"
        ],
        "paso_a_paso": [
            "1. Identificar endpoints con path parameters numéricos (IDOR candidates)",
            "2. Probar IDs secuenciales: 1, 2, 3, 4, 5",
            "3. Detectar que /api/v1/servidores/4 responde 200 sin chequeo de permisos",
            "4. El servidor 4 es 'restringido' (en metadata) pero igual responde",
            "5. Confirmar IDOR: se accede a datos que el usuario no debería ver"
        ],
        "mitigacion": [
            "Implementar RBAC: validar que el usuario tiene permiso sobre el recurso",
            "Usar UUIDs en vez de IDs secuenciales (más difíciles de enumerar)",
            "Rate limiting por usuario en endpoints sensibles",
            "Logging de accesos cross-tenant para detección"
        ]
    },
    {
        "id": 5,
        "titulo": "XXE en endpoint que procesa XML",
        "categoria": "Inyección",
        "vector": "XML External Entity",
        "descripcion": "El endpoint procesa XML sin deshabilitar entidades externas, permitiendo leer archivos del servidor.",
        "logs_originales": [
            "POST /api/v1/auditoria (Content-Type: application/xml)",
            "Body: <!DOCTYPE foo [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]>",
            "Response: 500 con contenido de /etc/passwd en el error"
        ],
        "paso_a_paso": [
            "1. Buscar endpoints que acepten Content-Type: application/xml",
            "2. Inyectar payload XXE estándar con declaración DOCTYPE",
            "3. La entidad externa 'xxe' intenta leer /etc/passwd",
            "4. El parser XML resuelve la entidad y el contenido aparece en la respuesta",
            "5. Escalar: leer archivos de configuración, hacer SSRF via XXE"
        ],
        "mitigacion": [
            "Deshabilitar DTD processing en el parser XML",
            "Usar defusedxml en Python, o similar en otros lenguajes",
            "Validar input con XSD estricto cuando sea posible",
            "No procesar XML si podés usar JSON"
        ]
    },
    {
        "id": 6,
        "titulo": "Bypass de autenticación por SQLi en login",
        "categoria": "Auth Bypass",
        "vector": "SQLi en endpoint de login",
        "descripcion": "El endpoint /api/v1/auth/admin valida el token contra una query SQL vulnerable.",
        "logs_originales": [
            "POST /api/v1/auth/admin",
            "Body: {token: \"' OR '1'='1\"}",
            "Response: 200 OK con permisos de administrador"
        ],
        "paso_a_paso": [
            "1. Probar caracteres especiales en el campo token",
            "2. Inyectar ' OR '1'='1 que convierte WHERE en condición siempre verdadera",
            "3. La query retorna el primer usuario (admin) → bypass de auth",
            "4. El endpoint devuelve permisos administrativos sin token válido",
            "5. Confirmar: hay acceso total con un payload simple"
        ],
        "mitigacion": [
            "Prepared statements SIEMPRE",
            "Hashing de tokens (comparar hash, no string plano)",
            "Rate limiting agresivo en login",
            "MFA (Multi-Factor Authentication) para endpoints críticos",
            "Logging de intentos de bypass para alertas"
        ]
    },
]

@app.get("/api/v1/escenarios", include_in_schema=False)
def listar_escenarios():
    return [
        {"id": e["id"], "titulo": e["titulo"], "categoria": e["categoria"], "vector": e["vector"]}
        for e in ESCENARIOS
    ]

@app.get("/api/v1/escenarios/{eid}", include_in_schema=False)
def obtener_escenario(eid: int):
    for e in ESCENARIOS:
        if e["id"] == eid:
            return e
    raise HTTPException(404, "Escenario no existe")

# =========================================================================
# DOCUMENTACIÓN DE CÓDIGOS DE ERROR
# =========================================================================

DOC_ERRORES = {
    200: {
        "titulo": "200 OK",
        "descripcion": "Petición exitosa. El servidor devolvió el recurso solicitado.",
        "en_pentest": "Útil para confirmar endpoints activos, pero no es un hallazgo por sí mismo.",
        "ejemplo_real": "GET /api/v1/servidores → 200 con JSON de servidores"
    },
    401: {
        "titulo": "401 Unauthorized",
        "descripcion": "Falta autenticación o el token es inválido.",
        "en_pentest": "Confirma que el endpoint EXISTE. Es medio hallazgo: hay recurso detrás.",
        "ejemplo_real": "GET /api/v1/admin/panel sin Bearer token → 401"
    },
    403: {
        "titulo": "403 Forbidden",
        "descripcion": "Autenticado pero sin permisos para el recurso.",
        "en_pentest": "ACL denegó acceso. Indica que el recurso existe y requiere más privilegios.",
        "ejemplo_real": "GET /api/v1/internal/admin/panel con token de usuario normal → 403"
    },
    404: {
        "titulo": "404 Not Found",
        "descripcion": "El recurso no existe.",
        "en_pentest": "404 ≠ 'no existe el endpoint'. A veces es un mensaje genérico para no revelar info.",
        "ejemplo_real": "GET /api/v1/servidores/999 → 404 Servidor no indexado"
    },
    405: {
        "titulo": "405 Method Not Allowed",
        "descripcion": "El verbo HTTP no está habilitado para esa ruta.",
        "en_pentest": "Confirma que la ruta existe. Probá con otros verbos: PUT, DELETE, PATCH.",
        "ejemplo_real": "DELETE /api/v1/servidores/1 → 405 (solo GET habilitado)"
    },
    500: {
        "titulo": "500 Internal Server Error",
        "descripcion": "Error interno del servidor. Frecuentemente filtra stack traces.",
        "en_pentest": "HALLAZGO CRÍTICO. Los stack traces revelan queries, paths internos, versiones.",
        "ejemplo_real": "POST /auditoria con SQLi → 500 con query completa en el error"
    },
    503: {
        "titulo": "503 Service Unavailable",
        "descripcion": "El servicio está caído o en mantenimiento.",
        "en_pentest": "Útil para mapear infraestructura: confirma que el servicio existe y está en otra red.",
        "ejemplo_real": "GET /api/v2/servidores → 503 (migración en curso)"
    },
}

@app.get("/api/v1/doc/error/{codigo}", include_in_schema=False)
def doc_error(codigo: int):
    if codigo not in DOC_ERRORES:
        raise HTTPException(404, f"No hay doc para código {codigo}")
    return DOC_ERRORES[codigo]

@app.get("/api/v1/doc/errores", include_in_schema=False)
def listar_docs_errores():
    return [
        {"codigo": c, "titulo": d["titulo"]}
        for c, d in DOC_ERRORES.items()
    ]

# =========================================================================
# HELPER — leer HTMLs
# =========================================================================

def leer_html(nombre: str) -> str:
    # Buscar primero en src/static/ (donde están los HTMLs)
    path = BASE_DIR / "static" / nombre
    if path.exists():
        return path.read_text(encoding="utf-8")
    # Fallback: buscar en src/ directo
    path = BASE_DIR / nombre
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"<h1>404 - {nombre} no encontrado</h1>"

# =========================================================================
# ENTRYPOINT
# =========================================================================

# =========================================================================
# AUTH (LOGIN/LOGOUT SIMPLE — sin password, didáctico)
# =========================================================================

class LoginBody(BaseModel):
    nombre: str

class LogoutBody(BaseModel):
    nombre: str
    duracion_segundos: int = 0

class BugResueltoBody(BaseModel):
    nombre: str
    bug_id: str

class DBCustomBody(BaseModel):
    nombre: str
    db_nombre: str

@app.post("/api/v1/auth/login", tags=["Auth"])
def auth_login(body: LoginBody, response: Response):
    """Loguea al usuario. Crea el archivo JSON si no existe.
    Setea cookie 'rt_usuario' con el nombre."""
    if not body.nombre or len(body.nombre) < 2 or len(body.nombre) > 30:
        raise HTTPException(400, "El nombre tiene que tener entre 2 y 30 caracteres.")
    res = usuario_login(body.nombre)
    response.set_cookie(key="rt_usuario", value=body.nombre.lower(), max_age=86400 * 30, httponly=True, samesite="lax")
    log.info(f"LOGIN: {body.nombre} (nuevo={res['nuevo']})")
    return {
        "ok": True,
        "nuevo": res["nuevo"],
        "mensaje": res["mensaje"],
        "nombre": body.nombre.lower(),
    }

@app.post("/api/v1/auth/logout", tags=["Auth"])
def auth_logout(body: LogoutBody, response: Response):
    """Cierra sesión: suma el tiempo activo al total, actualiza ultima_sesion."""
    data = usuario_logout(body.nombre, body.duracion_segundos)
    response.delete_cookie("rt_usuario")
    log.info(f"LOGOUT: {body.nombre} (sumó {body.duracion_segundos}s)")
    return {
        "ok": True,
        "tiempo_total_legible": data["tiempo_total_segundos"] // 60 if data["tiempo_total_segundos"] >= 60 else f"{data['tiempo_total_segundos']}s",
        "tiempo_total_segundos": data["tiempo_total_segundos"],
        "ultima_sesion": data["ultima_sesion"],
    }

@app.get("/api/v1/auth/quien-soy", tags=["Auth"])
def auth_quien_soy(rt_usuario: Optional[str] = Cookie(default=None)):
    """Dice quién está logueado (lee cookie). Si no, devuelve null."""
    if not rt_usuario:
        return {"logueado": False, "nombre": None}
    return {"logueado": True, "nombre": rt_usuario}

@app.post("/api/v1/auth/sumar-tiempo", tags=["Auth"])
def auth_sumar_tiempo(body: LogoutBody):
    """Suma tiempo sin cerrar sesión (para cron de actividad)."""
    sumar_tiempo(body.nombre, body.duracion_segundos)
    return {"ok": True}

@app.get("/api/v1/auth/mi-dashboard", tags=["Auth"])
def auth_dashboard(rt_usuario: Optional[str] = Cookie(default=None)):
    """Devuelve tiempo total, progreso del Detective, pendientes, dbs custom."""
    if not rt_usuario:
        raise HTTPException(401, "No estás logueado. Hacé click en 'Hola, soy ___' arriba a la derecha.")
    return obtener_dashboard(rt_usuario)

@app.post("/api/v1/auth/bug-resuelto", tags=["Auth"])
def auth_bug_resuelto(body: BugResueltoBody, rt_usuario: Optional[str] = Cookie(default=None)):
    """Registra un bug como resuelto en el archivo del usuario."""
    if not rt_usuario or rt_usuario != body.nombre.lower():
        raise HTTPException(401, "No estás logueado con ese nombre.")
    data = registrar_bug_resuelto(body.nombre, body.bug_id)
    return {"ok": True, "bugs_resueltos": data["bugs_resueltos"]}

@app.post("/api/v1/auth/db-custom", tags=["Auth"])
def auth_db_custom(body: DBCustomBody, rt_usuario: Optional[str] = Cookie(default=None)):
    """Registra una DB custom creada."""
    if not rt_usuario or rt_usuario != body.nombre.lower():
        raise HTTPException(401, "No estás logueado con ese nombre.")
    data = registrar_db_custom(body.nombre, body.db_nombre)
    return {"ok": True, "dbs_custom": data["dbs_custom"]}

@app.get("/api/v1/auth/ranking", tags=["Auth"])
def auth_ranking():
    """Devuelve el ranking de usuarios ordenado por score (tiempo + bugs + dbs)."""
    usuarios = obtener_ranking()
    return {
        "total_usuarios": len(usuarios),
        "usuarios": usuarios
    }

if __name__ == "__main__":
    print("=" * 60)
    print("RedTeam Lab v4.0 — Lab completo")
    print("=" * 60)
    print("URLs principales:")
    print("  http://127.0.0.1:8000/              → índice")
    print("  http://127.0.0.1:8000/docs          → Swagger oficial")
    print("")
    print("HTMLs del lab:")
    print("  /static/practicas.html  → menú de práctica + escenarios")
    print("  /static/wizard.html     → cargar tu propia DB en 1 paso")
    print("  /static/dbbuilder.html  → constructor de DBs")
    print("  /static/api_visual.html → playground de inyección por URL")
    print("  /static/dashboard.html  → dashboard de hallazgos")
    print("  /static/detective.html  → Detective de Bugs (10 bugs)")
    print("  /static/historial.html  → bitácora honesta del proyecto")
    print("  /static/errores.html    → documentación por código de error")
    print("  /static/resumen-visual.html → mapa visual del lab (entregable A)")
    print("=" * 60)
    uvicorn.run(app, host="127.0.0.1", port=8000)
