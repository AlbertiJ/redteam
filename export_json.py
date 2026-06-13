"""
export_json.py — Exporta los hallazgos de SQLite a hallazgos.json
para que el dashboard.html los pueda leer sin servidor backend.
"""

import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "db"))
from db import db

def main():
    hallazgos = db.listar_hallazgos()
    resumen = db.resumen_por_categoria()

    # Convertir timestamps/headers a string
    for h in hallazgos:
        h["timestamp"] = str(h.get("timestamp", ""))
        h["headers"] = str(h.get("headers", ""))
        h["en_swagger"] = bool(h.get("en_swagger"))

    out = {
        "generated_at": datetime.utcnow().isoformat(),
        "total": len(hallazgos),
        "resumen": resumen,
        "hallazgos": hallazgos
    }

    out_path = os.path.join(os.path.dirname(__file__), "hallazgos.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"[+] Exportados {len(hallazgos)} hallazgos a {out_path}")

if __name__ == "__main__":
    main()
