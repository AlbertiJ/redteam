# 🛰️ RedTeam Lab

> **Laboratorio interactivo de API Discovery, Shadow API Detection y Pentesting Ético**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](Dockerfile)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-success.svg)]()
[![Open Source](https://img.shields.io/badge/Open%20Source-Yes-brightgreen.svg)]()

RedTeam es un **laboratorio 100% local** para entrenar la detección de APIs ocultas (*shadow APIs*), filtraciones de información, y vulnerabilidades comunes en APIs REST modernas. Diseñado para practicar reconocimiento y auditoría de forma **ética, legal y reproducible** sobre un entorno controlado.

---

## 📋 Tabla de contenidos

- [¿Qué es?](#-qué-es)
- [Features](#-features)
- [Instalación](#-instalación)
- [Uso rápido](#-uso-rápido)
- [Arquitectura](#-arquitectura)
- [Módulos del lab](#-módulos-del-lab)
- [Shadow APIs escondidas](#-shadow-apis-escondidas)
- [Conceptos entrenados](#-conceptos-entrenados)
- [Aviso ético](#-aviso-ético)
- [Roadmap](#-roadmap)
- [Contribuir](#-contribuir)
- [Licencia](#-licencia)

---

## 🎯 ¿Qué es?

Cuando un desarrollador se va, se lleva código, deja endpoints sin documentar, o sube rutas a producción que nunca pasaron por el Swagger oficial. **RedTeam entrena la habilidad de encontrar esa API "huérfana"**: rutas, verbos, parámetros, información sensible filtrada.

**No es una herramienta de explotación.** Es un **campo de entrenamiento** para auditoría defensiva y reconocimiento pasivo/activo.

### Casos de uso

- 🧑‍🎓 **Aprender** fingerprinting de APIs REST, GraphQL, SOAP
- 🕵️ **Practicar** detección de shadow APIs y rutas abandonadas
- 🔍 **Entrenar** el ojo para detectar information disclosure
- 🧪 **Probar** payloads de SQLi, XXE, SSRF, Command Injection de forma segura
- 📚 **Enseñar** cómo se ven las vulnerabilidades reales (con su firma en logs)

---

## ✨ Features

### 🎯 Menú de práctica interactivo

- **3 niveles de dificultad** preconfigurados (básico, intermedio, avanzado)
- **6 vectores activables** desde la UI: SQLi, XXE, SSRF, CMDi, Shadow APIs, Info Disclosure
- Modificación de la URL en tiempo real: `?sqli=on&xxe=on&ssrf=on&cmdi=on`
- **6 escenarios resueltos** con lógica paso a paso oculta (botón "Revelar")
- Área de pruebas directa (GET/POST) con payloads editables

### 🗄️ DB Builder configurable

- **7 bases de datos precargadas** con datos reales:
  - 🎵 Música (álbumes clásicos)
  - 🎬 Películas (incluye cine argentino)
  - 🌍 Países (con códigos telefónicos)
  - 📚 Libros
  - ⚽ Deportes
  - 🍽️ Comidas típicas
  - 💻 Lenguajes de programación
- **3 slots custom** para que el usuario arme su propia DB
- Validación: mín 3 campos, máx 100, primer campo debe ser `id`
- Recomendaciones contextuales al diseñar (formato emails, códigos de área, etc.)
- **Consulta por URL** modificable (campo, filtro, límite)
- Detección automática de intentos de SQLi en filtros

### 🔍 API Visual Playground

- URL bar editable tipo navegador
- Botones rápidos para endpoints oficiales y shadow APIs
- Etiquetado automático: ¿es Swagger documentado o Shadow API?
- Historial de navegación con click para re-ejecutar
- Tracking automático de cada búsqueda

### 📚 Documentación por código de error

- 7 códigos HTTP documentados (200, 401, 403, 404, 405, 500, 503)
- Menú desplegable con: descripción, significado en pentest, ejemplo real del lab
- Buscador por palabra clave

### 📊 Tracking de actividad

- Registra clicks, búsquedas, navegaciones, escenarios revelados
- Persistencia en SQLite
- Endpoint para visualizar actividad reciente

### 🛡️ Modo seguro por defecto

- No ejecuta payloads reales
- Stack traces simulados (no son de una app real)
- DBs en `db/user_dbs/` aisladas del sistema
- Detección de SQLi devuelve 500 con alerta en vez de ejecutar la query

---

## 🚀 Instalación

### Opción 1: Docker (recomendado)

```bash
git clone https://github.com/AlbertiJ/redteam.git
cd redteam
docker compose up --build
```

El servidor queda disponible en `http://localhost:8000/`.

**Para correr en background**:
```bash
docker compose up -d
```

**Para ver los logs**:
```bash
docker compose logs -f
```

**Para parar el lab**:
```bash
docker compose down
```

### Opción 2: Python local

#### Requisitos

- Python 3.11+
- pip

#### Pasos

```bash
git clone https://github.com/AlbertiJ/redteam.git
cd redteam
pip install -r requirements.txt
python src/app.py
```

El servidor levanta en `http://127.0.0.1:8000/`.

### Primera visita

Abrí `http://127.0.0.1:8000/` en tu navegador. Vas a ver el menú principal con todos los módulos del lab.

---

## 🎮 Uso rápido

### 1. Menú de práctica

```
http://127.0.0.1:8000/static/practicas.html
```

Activá los vectores que querés entrenar, elegí un nivel de dificultad, y empezá a probar los escenarios. La idea es **no ver la resolución inmediatamente**: intentá primero, y solo revelá el paso a paso cuando lo necesites.

### 2. DB Builder

```
http://127.0.0.1:8000/static/dbbuilder.html
```

Explorá las 7 DBs precargadas (recomendado: empezá por `paises` o `peliculas`). Después armá tu propia DB en uno de los 3 slots custom y descubrí **qué información queda expuesta** cuando consultás por URL.

### 3. API Visual

```
http://127.0.0.1:8000/static/api_visual.html
```

Pegá URLs o usá los botones rápidos. El lab etiqueta automáticamente cada respuesta como `SWAGGER` (oficial) o `SHADOW` (escondida). El historial te deja volver a cualquier endpoint probado.

### 4. Discovery automatizado

```bash
python auditoria/discovery.py
```

Recorre la API, compara con Swagger, detecta shadow APIs, inyecta payloads, y guarda todo en `db/hallazgos.db`. Después corré `python export_json.py` y abrí `dashboard.html` para visualizar.

---

## 🏗️ Arquitectura

```
redteam/
├── src/
│   ├── app.py                 # API FastAPI principal
│   └── static/                # Frontend (HTMLs del lab)
│       ├── index.html         # Menú principal
│       ├── practicas.html     # Menú de práctica + escenarios
│       ├── dbbuilder.html     # Constructor de DBs
│       ├── api_visual.html    # Playground de URLs
│       ├── errores.html       # Doc de códigos HTTP
│       └── dashboard.html     # Dashboard de hallazgos
├── auditoria/
│   └── discovery.py           # Script de reconocimiento automatizado
├── db/
│   ├── db.py                  # Capa SQLite (init + CRUD)
│   ├── hallazgos.db           # Generado por discovery.py
│   ├── actividad.db           # Tracking de usuario
│   └── user_dbs/              # DBs custom creadas
├── docs/
│   └── GUIA.md                # Guía extendida de pentesting de APIs
├── export_json.py             # Exporta hallazgos a JSON
├── requirements.txt
├── Dockerfile                 # Imagen Docker
├── docker-compose.yml         # Orquestación
├── .dockerignore              # Exclusiones del build
├── .gitignore
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

---

## 📚 Módulos del lab

| Módulo | URL | Qué entrena |
|--------|-----|-------------|
| 🎯 Menú de práctica | `/static/practicas.html` | Activación de vectores, escenarios paso a paso |
| 🗄️ DB Builder | `/static/dbbuilder.html` | Information disclosure, IDOR, SQLi en filtros |
| 🔍 API Visual | `/static/api_visual.html` | Reconocimiento activo, comparación Swagger vs realidad |
| 📚 Doc de errores | `/static/errores.html` | Interpretación de códigos HTTP en pentesting |
| 📊 Dashboard | `/static/dashboard.html` | Visualización de hallazgos, severidad, categorías |
| 🛰️ Swagger oficial | `/docs` | El Swagger público (incompleto a propósito) |
| 🕵️ Shadow APIs | (escondidas) | Detección de rutas abandonadas |

---

## 🕵️ Shadow APIs escondidas

El lab tiene **7 APIs intencionalmente escondidas** del Swagger público. La idea es que las encuentres usando las herramientas del lab. No las listes explícitamente en tus reportes a clientes hasta que las descubras por tu cuenta 😉

**Pistas**:
- Los devs olvidan `/test`, `/debug`, `/internal/`
- Las versiones viejas (`/api/v0/`) suelen quedar activas
- Los endpoints de admin (`/auth/admin`, `/admin/panel`) son candidatos clásicos
- Los recursos deprecados no siempre se eliminan

---

## 🎓 Conceptos entrenados

| Concepto | Cómo se practica |
|----------|------------------|
| **API Fingerprinting** | Comparar `/docs` vs realidad, identificar framework, versiones |
| **Shadow API Detection** | Encontrar rutas no documentadas con fuzzing controlado |
| **Information Disclosure** | Analizar `/metadatos`, headers, stack traces |
| **SQL Injection** | Probar payloads en `/auditoria/infraestructura` |
| **XXE** | Activar módulo `xxe` y probar payloads XML |
| **SSRF** | Activar módulo `ssrf` y probar URLs internas |
| **Command Injection** | Activar módulo `cmdi` y probar payloads de OS |
| **IDOR / URL Manipulation** | Enumerar IDs en endpoints con path parameters |
| **Auth Bypass** | Probar SQLi en endpoints de autenticación |
| **Reconocimiento activo vs pasivo** | Diferenciar qué rompe el silencio y qué no |

---

## ⚖️ Aviso ético

**Este laboratorio es exclusivamente para uso educativo y de entrenamiento en entornos controlados.**

✅ **SÍ podés**:
- Usarlo en tu máquina local
- Adaptarlo para cursos, talleres, entrenamientos internos
- Practicar reconocimiento sobre él todo lo que quieras

❌ **NO está diseñado para**:
- Atacar sistemas reales sin autorización
- Pentestear APIs de terceros sin permiso escrito
- Usar las técnicas entrenadas con fines maliciosos

**Recordatorio legal**: Pentestear sistemas sin autorización escrita es un delito en la mayoría de las jurisdicciones. Este lab es un **campo de entrenamiento simulado**, no una herramienta de ataque. Las "vulnerabilidades" son intencionales pero contenidas: los payloads se evalúan, no se ejecutan contra sistemas reales.

---

## 🛣️ Roadmap

- [x] v1.0 — Fingerprinting básico y shadow APIs
- [x] v2.0 — DB Builder + tracking
- [x] v3.0 — Escenarios resueltos, menú de práctica por niveles
- [ ] v4.0 — Soporte para GraphQL (introspection, nested queries)
- [ ] v4.0 — Soporte para SOAP (WSDL enumeration, XXE)
- [ ] v5.0 — Modo "comandería" (C2 simulado en local)
- [ ] v5.0 — Tests automatizados con pytest
- [ ] v6.0 — Dashboard con export a PDF
- [ ] v6.0 — Internacionalización (i18n)

---

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Algunas ideas:

- 🐛 Reportar bugs o comportamiento inesperado
- 💡 Proponer nuevos escenarios
- 🌐 Agregar traducciones
- 📚 Mejorar la documentación
- 🧪 Agregar tests
- 🎨 Mejorar el UI/UX

### Cómo contribuir

1. Fork el proyecto
2. Crea una branch (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'feat: agrego X'`)
4. Push a la branch (`git push origin feature/nueva-funcionalidad`)
5. Abrí un Pull Request

---

## 📄 Licencia

Este proyecto está bajo la **Licencia MIT** — ver el archivo [LICENSE](LICENSE) para más detalles.

```
MIT License

Copyright (c) 2026 RedTeam Lab Contributors

Se concede permiso, sin cargo alguno, a cualquier persona que obtenga una copia
de este software y archivos de documentación asociados...
```

---

## 🙏 Agradecimientos

- A la comunidad de **OWASP API Security Top 10** por el marco de referencia
- A los proyectos de **PortSwigger Web Security Academy** por la inspiración
- A todos los que enseñan y aprenden seguridad ofensiva de forma ética

---

## 📞 Contacto

- 🐛 **Issues**: [GitHub Issues](https://github.com/AlbertiJ/redteam/issues)
- 💬 **Discusiones**: [GitHub Discussions](https://github.com/AlbertiJ/redteam/discussions)

---

<p align="center">
  <strong>Hecho con 🛰️ para la comunidad de pentesting ético</strong>
</p>
