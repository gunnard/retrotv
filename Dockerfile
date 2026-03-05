FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY retrotv/ ./retrotv/
COPY config.example.yaml ./config.yaml

RUN mkdir -p /app/data /app/exports /app/guides /app/filler

ENV RETROTV_DATA_DIR=/app/data
ENV RETROTV_DB_PATH=/app/data/retrotv.db

EXPOSE 8080

VOLUME ["/app/data", "/app/exports", "/app/guides"]

CMD ["python", "-m", "retrotv.main", "serve", "--host", "0.0.0.0", "--port", "8080"]
