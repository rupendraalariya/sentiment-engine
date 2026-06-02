# syntax=docker/dockerfile:1

# ---- Stage 1: builder ----
FROM python:3.10-slim AS builder

WORKDIR /build

# System deps needed to build some wheels.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install all dependencies into an isolated prefix that we copy into runtime.
RUN pip install --upgrade pip \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- Stage 2: runtime ----
FROM python:3.10-slim AS runtime

WORKDIR /app

# curl is required by the HEALTHCHECK below.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Copy only the installed packages from the builder stage.
COPY --from=builder /install /usr/local

# Copy application code (model weights are mounted at runtime, not baked in).
COPY config.py app.py ./
COPY src ./src
COPY api ./api

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MODEL_DIR=/app/models

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
