# ── Backend: FastAPI with SQLAlchemy async ──────────────────────────────────
FROM python:3.14-slim

WORKDIR /app

# System dependencies (pg_isready needs postgresql-client)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application
COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Default port
EXPOSE 8000

# Run migrations then start server
ENTRYPOINT ["./entrypoint.sh"]