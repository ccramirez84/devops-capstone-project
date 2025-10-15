# Dockerfile (raíz del repositorio)
FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencias del sistema que suelen necesitar paquetes Python (opcional pero útil)
RUN apt-get update -y && apt-get install -y --no-install-recommends \
    build-essential gcc curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Instala dependencias si existe requirements.txt
COPY requirements.txt /app/requirements.txt
RUN if [ -f requirements.txt ]; then \
      python -m pip install --upgrade pip wheel && \
      pip install --no-cache-dir -r requirements.txt; \
    else \
      echo "No requirements.txt found, continuing..."; \
    fi

# Copia el resto del código
COPY . /app

# (Opcional) Variables de entorno de la app
# ENV FLASK_APP=service:app
# ENV PORT=5000

# Exponer el puerto si tu app lo usa (ajusta si es 8080 u otro)
EXPOSE 5000

# Comando por defecto (ajústalo a tu app si ya la tienes)
# Ejemplos:
# CMD ["gunicorn", "--bind", "0.0.0.0:5000", "service:app"]
CMD ["python", "-m", "http.server", "5000"]
