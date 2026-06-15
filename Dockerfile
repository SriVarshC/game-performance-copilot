# ── Base image ──────────────────────────────────────────────
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system build tools (needed by psutil, lightgbm)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# ── Dependencies ─────────────────────────────────────────────
# Copy requirements first — Docker layer caching
# Only re-installs if requirements.txt changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Application code ─────────────────────────────────────────
COPY src/ src/
COPY models/ models/

# Create data directory for SQLite (volume will mount here)
RUN mkdir -p data

# ── Runtime ──────────────────────────────────────────────────
EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]