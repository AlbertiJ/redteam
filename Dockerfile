# API-Eye Lab - Dockerfile
# Imagen basada en Python slim para mantener el tamaño chico

FROM python:3.11-slim

# Metadata
LABEL maintainer="API-Eye Lab"
LABEL description="Laboratorio de API Discovery y pentesting ético"
LABEL version="3.0.0"

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Crear usuario no-root para seguridad
RUN groupadd -r apieye && useradd -r -g apieye apieye

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias primero (mejor cache de Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY src/ ./src/
COPY auditoria/ ./auditoria/
COPY db/ ./db/
COPY export_json.py .

# Crear directorios de datos con permisos correctos
RUN mkdir -p /app/db/user_dbs && \
    chown -R apieye:apieye /app

# Cambiar a usuario no-root
USER apieye

# Exponer puerto
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/servidores')" || exit 1

# Comando por defecto
CMD ["python", "src/app.py"]
