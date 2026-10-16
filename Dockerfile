# Multi-stage Dockerfile for C/AI Arena Optimization
# Week 12 Day 7: Containerization & Supply Chain

# Stage 1: Builder
FROM python:3.13-slim as builder

WORKDIR /build

# RUN apt-get update && apt-get install -y --no-install-recommends \
#     gcc \
#     && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip setuptools wheel && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.13-slim

LABEL maintainer="Arena Development Team"
LABEL version="1.0.0"
LABEL description="C/AI Arena Optimization - Production Container"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    VIRTUAL_ENV="/opt/venv"

WORKDIR /app

RUN groupadd -r arena && useradd -r -g arena arena

COPY --from=builder --chown=arena:arena /opt/venv /opt/venv

COPY --chown=arena:arena . .

RUN mkdir -p /app/logs /app/data && \
    chown -R arena:arena /app

USER arena

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health').read()" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]