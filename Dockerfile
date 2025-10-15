FROM python:3.9-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update -y && apt-get install -y --no-install-recommends \
    build-essential gcc curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN if [ -f requirements.txt ]; then \
      python -m pip install --upgrade pip wheel && \
      pip install --no-cache-dir -r requirements.txt; \
    else \
      echo "No requirements.txt found, continuing..."; \
    fi

COPY . /app
EXPOSE 5000
CMD ["python", "-m", "http.server", "5000"]
