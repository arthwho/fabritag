FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000

WORKDIR /app

COPY src/lib/server/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --disable-pip-version-check -r requirements.txt

COPY src/lib/server/ ./

RUN useradd --create-home --uid 10001 fabritag \
    && chown -R fabritag:fabritag /app

USER fabritag

EXPOSE 5000

# Uma única instância mantém compatibilidade com sessões e heartbeats em memória.
# Antes de escalar horizontalmente, esses estados devem migrar para Redis/PostgreSQL.
CMD ["gunicorn", "--bind=0.0.0.0:5000", "--workers=1", "--threads=8", "--timeout=60", "--access-logfile=-", "--error-logfile=-", "wsgi:app"]
