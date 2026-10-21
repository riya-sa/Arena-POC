# Docker Build Guide - C/AI Arena Optimization

**Week 12 Documentation | Containerization & Supply Chain**

## Table of Contents

1. [Quick Start](#quick-start)
2. [Local Build](#local-build)
3. [Image Structure](#image-structure)
4. [Running Containers](#running-containers)
5. [Pushing to GHCR](#pushing-to-ghcr)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start

```bash
# Build locally
docker build -t arena:1.0.0 .

# Run container
docker run -d --name arena -p 8000:8000 arena:1.0.0

# Health check
curl http://localhost:8000/api/v1/health

# Expected output:
# {"status":"healthy","version":"1.0.0","environment":"development"}

# Stop & remove
docker stop arena
docker rm arena
```

---

## Local Build

### Prerequisites

- Docker 24.0+ installed
- 2GB free disk space
- `requirements.txt` in project root
- `Dockerfile` in project root
- `.dockerignore` in project root

### Build Command

```bash
# Standard build
docker build -t arena:1.0.0 .

# Build with no cache (fresh build)
docker build --no-cache -t arena:1.0.0 .

# Build with build args
docker build --build-arg PYTHON_VERSION=3.13 -t arena:1.0.0 .

# Show build progress
docker build --progress=plain -t arena:1.0.0 .
```

### Build Stages

The Dockerfile uses multi-stage build:

**Stage 1: Builder**
- Python 3.13-slim base
- Installs gcc (for compiled dependencies)
- Creates Python venv
- Installs requirements.txt

**Stage 2: Runtime**
- Python 3.13-slim base (smaller final image)
- Copies venv from builder
- Creates non-root `arena` user
- Exposes port 8000
- Health check configured
- Starts uvicorn on 0.0.0.0:8000

### Build Output

```
Successfully built sha256:abc123...
Successfully tagged arena:1.0.0
```

Image size: ~250MB (including all dependencies)

---

## Image Structure

```
arena:1.0.0 (Python 3.13-slim)
├── /app (working directory)
│   ├── app/ (source code)
│   ├── tests/ (test suite)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .dockerignore
├── /opt/venv (virtual environment)
├── /app/logs (log directory)
└── /app/data (data directory)

Non-root user: arena:arena
Entrypoint: uvicorn app.main:app --host 0.0.0.0 --port 8000
Health check: http://localhost:8000/api/v1/health (30s interval, 10s timeout)
```

### Environment Variables

```bash
PYTHONUNBUFFERED=1        # Real-time logging
PYTHONDONTWRITEBYTECODE=1 # No .pyc files
PATH="/opt/venv/bin:$PATH"
VIRTUAL_ENV="/opt/venv"
```

---

## Running Containers

### Development Mode

```bash
# Run with interactive logs
docker run -it --name arena-dev \
  -p 8000:8000 \
  -v $(pwd):/app \
  arena:1.0.0

# Expected output:
# ✅ Configuration loaded
# 2026-10-21 12:00:00 [INFO] app.main: Starting C/AI Arena Optimization v1.0.0
# INFO: Uvicorn running on http://0.0.0.0:8000
```

### Production Mode

```bash
# Run detached with restart policy
docker run -d \
  --name arena-prod \
  --restart unless-stopped \
  -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e LOG_FORMAT=json \
  -e LOG_LEVEL=INFO \
  arena:1.0.0
```

### With Database

```bash
# Run with PostgreSQL connection
docker run -d \
  --name arena \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql+asyncpg://user:pass@db.example.com/arena_db" \
  -e ENVIRONMENT=production \
  arena:1.0.0
```

### With Volume Mounts

```bash
# Mount logs directory
docker run -d \
  --name arena \
  -p 8000:8000 \
  -v /var/log/arena:/app/logs \
  arena:1.0.0

# Mount data directory
docker run -d \
  --name arena \
  -p 8000:8000 \
  -v /var/data/arena:/app/data \
  arena:1.0.0
```

### With Health Check

```bash
# View health status
docker ps
# NAMES    STATUS
# arena    Up 5 minutes (healthy)

# Check health directly
docker exec arena curl http://localhost:8000/api/v1/health

# View health events
docker events --filter type=container --filter container=arena
```

---

## Container Management

### View Logs

```bash
# Real-time logs
docker logs -f arena

# Last 100 lines
docker logs --tail 100 arena

# With timestamps
docker logs -t arena

# Since specific time
docker logs --since 2026-10-21T12:00:00 arena
```

### Inspect Container

```bash
# Full container info
docker inspect arena

# View IP address
docker inspect -f '{{.NetworkSettings.IPAddress}}' arena

# View environment variables
docker inspect arena | grep -A 20 "Env"
```

### Execute Commands

```bash
# Run health check
docker exec arena curl http://localhost:8000/api/v1/health

# Access Python shell
docker exec -it arena python

# View logs from inside
docker exec arena tail -f /app/logs/app.log
```

### Stop & Remove

```bash
# Stop container
docker stop arena
# Graceful 10s shutdown (configurable)

# Force stop
docker kill arena

# Remove container
docker rm arena

# Stop and remove all
docker stop $(docker ps -q) && docker rm $(docker ps -aq)
```

---

## Pushing to GHCR

### Prerequisites

```bash
# Generate token: https://github.com/settings/tokens
# Scopes: repo, write:packages, delete:packages

# Save token
export GITHUB_TOKEN="ghp_your_token_here"

# Or use gh CLI
gh auth login
```

### Login to GHCR

```bash
# Using GitHub token
echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin

# Using gh CLI
gh auth token | docker login ghcr.io -u YOUR_USERNAME --password-stdin

# Verify login
docker logout ghcr.io
```

### Tag Image

```bash
# Tag for GHCR
docker tag arena:1.0.0 ghcr.io/YOUR_USERNAME/arena-poc:1.0.0
docker tag arena:1.0.0 ghcr.io/YOUR_USERNAME/arena-poc:latest

# Verify tags
docker images | grep arena
```

### Push to Registry

```bash
# Push specific tag
docker push ghcr.io/YOUR_USERNAME/arena-poc:1.0.0

# Push with latest
docker push ghcr.io/YOUR_USERNAME/arena-poc:latest

# Push all tags
docker push ghcr.io/YOUR_USERNAME/arena-poc:1.0.0
docker push ghcr.io/YOUR_USERNAME/arena-poc:latest
```

### Pull from GHCR

```bash
# Pull image
docker pull ghcr.io/YOUR_USERNAME/arena-poc:latest

# Run from registry
docker run -d --name arena \
  -p 8000:8000 \
  ghcr.io/YOUR_USERNAME/arena-poc:latest
```

---

## Troubleshooting

### Build Fails: "failed to solve: failed to configure registry cache exporter"

**Issue:** Repository name has uppercase characters

**Fix:**
```bash
# Use lowercase in Dockerfile and build command
docker build -t ghcr.io/username/arena-poc:latest .
```

---

### Build Fails: "failed to create new connection: all attempts failed"

**Issue:** Cannot reach Docker registry (network/firewall)

**Fix:**
```bash
# Check network
docker run --rm alpine ping google.com

# Restart Docker daemon
sudo systemctl restart docker

# Rebuild
docker build -t arena:1.0.0 .
```

---

### Container Exits Immediately

**Check logs:**
```bash
docker logs arena
# Look for startup errors
```

**Common causes:**
- Database connection failed → Expected in dev (gracefully handled)
- Invalid config → Check env variables
- Port conflict → Use different port: `-p 8001:8000`

**Solution:**
```bash
# Run with interactive shell to debug
docker run -it arena:1.0.0 /bin/bash

# Inside container
python -m app.main
```

---

### Health Check Failing

**Issue:** Container marked as unhealthy

**Check status:**
```bash
docker ps
# STATUS: Up 5 minutes (unhealthy)

# View health check logs
docker inspect --format='{{json .State.Health}}' arena

# Manual health check
docker exec arena curl http://localhost:8000/api/v1/health
```

**Fix:** Wait longer for startup
```bash
docker run -d --name arena \
  -p 8000:8000 \
  --health-start-period=60s \
  arena:1.0.0
```

---

### Port Already in Use

**Issue:** Cannot bind port 8000

**Check:**
```bash
# Find process using port
lsof -i :8000
# or
netstat -tlnp | grep 8000
```

**Solution:**
```bash
# Use different port
docker run -d --name arena \
  -p 8001:8000 \
  arena:1.0.0

# Access on 8001
curl http://localhost:8001/api/v1/health
```

---

### Out of Disk Space

**Check:**
```bash
docker system df
```

**Cleanup:**
```bash
# Remove unused images
docker image prune -a

# Remove dangling layers
docker system prune -a

# Remove all images/containers/networks
docker system prune -a --volumes
```

---

## Performance Tips

### Image Size

Current: ~250MB

Optimization:
```bash
# Use smaller base
FROM python:3.13-slim-bookworm

# Remove build tools from runtime
# (Already done in multi-stage build)

# Check layer sizes
docker history arena:1.0.0
```

### Build Speed

```bash
# Use cache
docker build -t arena:1.0.0 .
# Second build uses cache: ~5s

# Cache busting
docker build --no-cache -t arena:1.0.0 .

# Parallel downloads
# (Docker 24.0+ automatic)
```

### Runtime Performance

```bash
# Use resource limits
docker run -d \
  --name arena \
  --memory=512m \
  --cpus=1.0 \
  -p 8000:8000 \
  arena:1.0.0
```

---

## Security Best Practices

✅ Non-root user (arena:arena)  
✅ Minimal base image (python:3.13-slim)  
✅ Multi-stage build (no build tools in runtime)  
✅ Health checks enabled  
✅ Restart policies (unless-stopped)  
✅ Environment variable isolation  
✅ Read-only filesystem support  

```bash
# Run as read-only
docker run -d \
  --name arena \
  --read-only \
  --tmpfs /tmp \
  -p 8000:8000 \
  arena:1.0.0
```

---

## References

- [Docker CLI Reference](https://docs.docker.com/engine/reference/commandline/)
- [Dockerfile Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [GHCR Documentation](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)

---

**Week 12 Day 11 Complete** ✅