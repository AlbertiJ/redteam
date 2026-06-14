"""Gestión de usuarios del RedTeam Lab.
- 1 archivo JSON por usuario en /usuarios/<nombre>.json
- Estructura: nombre, fecha_alta, tiempo_total_segundos, ultima_sesion, bugs_resueltos, dbs_custom
- Login: crea archivo si no existe, lee si existe, devuelve "hola" o "bienvenido"
- Logout: actualiza tiempo_total y ultima_sesion
- Sesión activa: cookie 'rt_usuario' con el nombre
"""
import os
import json
import time
from datetime import datetime
from pathlib import Path
from fastapi import HTTPException, Cookie
from typing import Optional

# Path: /usuarios/ en la raíz del proyecto (al lado de src/)
BASE_DIR = Path(__file__).parent.parent
USUARIOS_DIR = BASE_DIR / "usuarios"
USUARIOS_DIR.mkdir(exist_ok=True)

RANKING_FILE = USUARIOS_DIR / "_ranking.json"


def _archivo_usuario(nombre: str) -> Path:
    """Devuelve el path al archivo JSON de un usuario. Sanitiza el nombre."""
    # Solo letras, números, guiones y guión bajo
    safe = "".join(c for c in nombre if c.isalnum() or c in "-_").lower()
    if not safe:
        raise HTTPException(400, "Nombre inválido. Usá letras, números, guiones o guión bajo.")
    if safe != nombre.lower():
        # No bloqueamos pero advertimos
        pass
    return USUARIOS_DIR / f"{safe}.json"


def cargar_usuario(nombre: str) -> dict:
    """Lee el archivo de un usuario. Si no existe, lo crea."""
    archivo = _archivo_usuario(nombre)
    if not archivo.exists():
        # Crear nuevo
        return {
            "nombre": nombre,
            "fecha_alta": datetime.now().isoformat(),
            "tiempo_total_segundos": 0,
            "ultima_sesion": None,
            "bugs_resueltos": [],   # IDs de bugs del Detective resueltos
            "dbs_custom": [],        # nombres de DBs custom creadas
        }
    with open(archivo, "r", encoding="utf-8") as f:
        return json.load(f)


def guardar_usuario(nombre: str, data: dict):
    """Escribe el archivo JSON de un usuario."""
    archivo = _archivo_usuario(nombre)
    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def login(nombre: str) -> dict:
    """Loguea a un usuario. Si no existe, lo crea.
    Devuelve un dict con: nuevo (bool), data (dict), mensaje (str)."""
    nuevo = not _archivo_usuario(nombre).exists()
    data = cargar_usuario(nombre)
    if nuevo:
        guardar_usuario(nombre, data)
    return {
        "nuevo": nuevo,
        "data": data,
        "mensaje": f"Bienvenido a la plataforma, {nombre}." if nuevo else f"Bienvenido de nuevo, {nombre}."
    }


def logout(nombre: str, duracion_segundos: int) -> dict:
    """Cierra sesión, suma el tiempo activo al total."""
    data = cargar_usuario(nombre)
    data["tiempo_total_segundos"] = data.get("tiempo_total_segundos", 0) + int(duracion_segundos)
    data["ultima_sesion"] = datetime.now().isoformat()
    guardar_usuario(nombre, data)
    actualizar_ranking()
    return data


def sumar_tiempo(nombre: str, duracion_segundos: int):
    """Suma tiempo al total sin tocar ultima_sesion (para cron de actividad)."""
    data = cargar_usuario(nombre)
    data["tiempo_total_segundos"] = data.get("tiempo_total_segundos", 0) + int(duracion_segundos)
    guardar_usuario(nombre, data)


def registrar_bug_resuelto(nombre: str, bug_id: str):
    """Registra un bug como resuelto en el archivo del usuario."""
    data = cargar_usuario(nombre)
    bugs = data.get("bugs_resueltos", [])
    if bug_id not in bugs:
        bugs.append(bug_id)
        data["bugs_resueltos"] = bugs
        guardar_usuario(nombre, data)
    return data


def registrar_db_custom(nombre: str, db_nombre: str):
    """Registra una DB custom en el archivo del usuario."""
    data = cargar_usuario(nombre)
    dbs = data.get("dbs_custom", [])
    if db_nombre not in dbs:
        dbs.append(db_nombre)
        data["dbs_custom"] = dbs
        guardar_usuario(nombre, data)
    return data


def obtener_dashboard(nombre: str) -> dict:
    """Devuelve lo que ve el usuario cuando entra: tiempo, progreso, pendientes."""
    data = cargar_usuario(nombre)
    tiempo_total = data.get("tiempo_total_segundos", 0)
    bugs_resueltos = data.get("bugs_resueltos", [])
    dbs_custom = data.get("dbs_custom", [])

    # Progreso del Detective
    total_bugs = 10
    progreso_detective = f"{len(bugs_resueltos)}/{total_bugs}"

    # Pendientes: lo que falta
    todos_los_bugs = ["1a", "1b", "2a", "2b", "3a", "3b", "4a", "4b", "5a", "5b"]
    bugs_pendientes = [b for b in todos_los_bugs if b not in bugs_resueltos]

    return {
        "nombre": data["nombre"],
        "fecha_alta": data["fecha_alta"],
        "ultima_sesion": data.get("ultima_sesion"),
        "tiempo_total_segundos": tiempo_total,
        "tiempo_total_legible": _formatear_tiempo(tiempo_total),
        "bugs_resueltos": bugs_resueltos,
        "bugs_pendientes": bugs_pendientes,
        "progreso_detective": progreso_detective,
        "dbs_custom": dbs_custom,
        "total_dbs_custom": f"{len(dbs_custom)}/3"
    }


def _formatear_tiempo(segundos: int) -> str:
    """Convierte segundos a algo legible: '2h 14min 32s'."""
    if segundos < 60:
        return f"{segundos}s"
    if segundos < 3600:
        m = segundos // 60
        s = segundos % 60
        return f"{m}min {s}s"
    h = segundos // 3600
    m = (segundos % 3600) // 60
    s = segundos % 60
    return f"{h}h {m}min {s}s"


def actualizar_ranking():
    """Lee todos los usuarios y actualiza _ranking.json ordenado por tiempo."""
    usuarios = []
    for archivo in USUARIOS_DIR.glob("*.json"):
        if archivo.name == "_ranking.json":
            continue
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                data = json.load(f)
            usuarios.append({
                "nombre": data.get("nombre", archivo.stem),
                "tiempo_total_segundos": data.get("tiempo_total_segundos", 0),
                "bugs_resueltos_count": len(data.get("bugs_resueltos", [])),
                "dbs_custom_count": len(data.get("dbs_custom", [])),
            })
        except Exception:
            continue
    # Ordenar: mayor tiempo primero
    usuarios.sort(key=lambda u: u["tiempo_total_segundos"], reverse=True)
    # Score combinado: tiempo + bugs*60s + dbs*120s
    for u in usuarios:
        u["score"] = u["tiempo_total_segundos"] + u["bugs_resueltos_count"] * 60 + u["dbs_custom_count"] * 120
    usuarios.sort(key=lambda u: u["score"], reverse=True)
    with open(RANKING_FILE, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, indent=2, ensure_ascii=False)
    return usuarios


def obtener_ranking() -> list:
    """Devuelve el ranking actual. Si no existe, lo regenera."""
    if not RANKING_FILE.exists():
        return actualizar_ranking()
    with open(RANKING_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
