"""
db.py — Capa de persistencia para API-Eye
Crea la tabla de hallazgos y expone funciones para guardar/consultar.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "hallazgos.db")

def init_db():
    """Crea la tabla si no existe."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS hallazgos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            metodo TEXT NOT NULL,
            status_code INTEGER NOT NULL,
            en_swagger INTEGER NOT NULL,
            categoria TEXT NOT NULL,
            severidad TEXT NOT NULL,
            detalle TEXT,
            headers TEXT
        )
    """)
    conn.commit()
    conn.close()

def guardar_hallazgo(endpoint, metodo, status_code, en_swagger, categoria, severidad, detalle="", headers=""):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO hallazgos (timestamp, endpoint, metodo, status_code, en_swagger, categoria, severidad, detalle, headers)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.utcnow().isoformat(),
        endpoint,
        metodo,
        status_code,
        1 if en_swagger else 0,
        categoria,
        severidad,
        detalle,
        headers
    ))
    conn.commit()
    conn.close()

def listar_hallazgos():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM hallazgos ORDER BY id DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def resumen_por_categoria():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT categoria, severidad, COUNT(*) as total
        FROM hallazgos
        GROUP BY categoria, severidad
        ORDER BY total DESC
    """)
    rows = [{"categoria": r[0], "severidad": r[1], "total": r[2]} for r in cur.fetchall()]
    conn.close()
    return rows

def limpiar():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM hallazgos")
    conn.commit()
    conn.close()
