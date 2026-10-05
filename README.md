# C/AI Arena POC - Foundation

**FastAPI + PostgreSQL (Docker) Scaffold**

Baseline implementation for Phase 0 - Benchmarking Foundation (Weeks 3-5).

---

## Quick Start (5 minutes)

### Prerequisites
- Docker & Docker Compose installed
- Python 3.11+ (for local development)

### 1. Clone/Setup
```bash
# Copy .env.example to .env (or use defaults)
cp .env.example .env

# Start services with Docker Compose
docker-compose up -d

# Wait for PostgreSQL to be healthy (~5 seconds)
docker-compose ps
```

You should see:
```
arena_postgres   postgres:16-alpine     healthy
arena_api        C/AI Arena POC         running
```

### 2. Verify It Works
```bash
# Health check
curl http://localhost:8000/health

# Should return:
# {"status":"healthy","service":"arena-poc","environment":"development"}
```

### 3. Explore API
- **API Docs:** http://localhost:8000/docs (Swagger UI)
- **Alternative Docs:** http://localhost:8000/redoc (ReDoc)

---

## Project Structure

```
arena-poc/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Configuration management
│   ├── database.py          # Database connection
│   ├── logger.py            # Logging setup
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   └── api/
│       ├── __init__.py
│       └── benchmarks.py    # Benchmark CRUD endpoints
├── docker-compose.yml       # Docker services (PostgreSQL + app)
├── Dockerfile               # FastAPI container
├── requirements.txt         # Python dependencies
├── .env.example            # Example environment variables
└── README.md               # This file
```

---

## Database Schema

### Core Tables (POC Phase)

```
BenchmarkSuite (id, name, description, created_at)
  ↓ (one-to-many)
BenchmarkVersion (id, suite_id, version_number, status, published_at)
  ↓ (one-to-many)
Task (id, version_id, task_id, problem_statement, category, difficulty, public_tests)

Candidate (id, name, provider, description)
  ↓ (one-to-many)
CandidateVersion (id, candidate_id, version_number, model_id, config, status)

Experiment (id, benchmark_version_id, status, repetitions, budget_usd, spent_usd)
  ↓ (one-to-many)
Execution (id, experiment_id, task_id, candidate_version_id, status, metrics, score)
```

### Key Design Principles
- **Immutability:** Published versions cannot be edited
- **Versioning:** All changes create new versions
- **Audit Trail:** `created_at` on every table
- **Relationships:** Foreign keys enforce referential integrity

---

## API Endpoints (Phase 0)

### Benchmark Management

#### Create Benchmark
```bash
curl -X POST http://localhost:8000/api/v1/benchmarks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Java Programming Basics",
    "description": "Beginner-level Java tasks",
    "tasks": [
      {
        "task_id": "java-001",
        "problem_statement": "Write a function that returns the sum of two numbers.",
        "category": "basics",
        "difficulty": 1,
        "public_tests": [
          {"input": "add(2, 3)", "expected": "5"}
        ]
      }
    ]
  }'
```

#### List Benchmarks
```bash
curl http://localhost:8000/api/v1/benchmarks
```

#### Get Specific Benchmark
```bash
curl http://localhost:8000/api/v1/benchmarks/{benchmark_id}
```

#### Publish Benchmark Version
```bash
curl -X POST http://localhost:8000/api/v1/benchmarks/{benchmark_id}/versions/{version_id}/publish
```

#### List Benchmark Versions
```bash
curl http://localhost:8000/api/v1/benchmarks/{benchmark_id}/versions
```

#### Add Tasks to Draft Version
```bash
curl -X POST http://localhost:8000/api/v1/benchmarks/{benchmark_id}/versions/{version_id}/add-tasks \
  -H "Content-Type: application/json" \
  -d '{
    "tasks": [
      {
        "task_id": "java-002",
        "problem_statement": "...",
        "public_tests": []
      }
    ]
  }'
```

---

## Development Workflow

### Local Setup (Without Docker)
```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL with Docker (optional)
docker run -d \
  --name arena_postgres \
  -e POSTGRES_USER=arena_user \
  -e POSTGRES_PASSWORD=arena_password \
  -e POSTGRES_DB=arena_poc \
  -p 5432:5432 \
  postgres:16-alpine

# Set DATABASE_URL
export DATABASE_URL=postgresql://arena_user:arena_password@localhost:5432/arena_poc

# Run the app
uvicorn app.main:app --reload
```

### View API Documentation
Navigate to http://localhost:8000/docs for interactive Swagger UI.

### View Logs
```bash
# Docker logs
docker-compose logs -f arena_app

# Or view log file
tail -f logs/arena.log
```

### Access Database
```bash
# Connect to PostgreSQL
docker exec -it arena_postgres psql -U arena_user -d arena_poc

# List tables
\dt

# Sample query
SELECT id, name, created_at FROM benchmark_suites;
```

---

## Testing

### Run Tests
```bash
# With Docker
docker-compose exec arena_app pytest

# Locally
pytest tests/
```

### Basic Manual Test
```bash
# 1. Create a benchmark
BENCHMARK_ID=$(curl -s -X POST http://localhost:8000/api/v1/benchmarks \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Benchmark","tasks":[]}' \
  | jq -r '.id')

echo "Created benchmark: $BENCHMARK_ID"

# 2. List benchmarks
curl http://localhost:8000/api/v1/benchmarks | jq .

# 3. Get specific benchmark
curl http://localhost:8000/api/v1/benchmarks/$BENCHMARK_ID | jq .
```

---

## Configuration

Edit `.env` to customize:

```
ENVIRONMENT=development          # development or production
LOG_LEVEL=INFO                  # DEBUG, INFO, WARNING, ERROR
DATABASE_URL=postgresql://...   # PostgreSQL connection string
DATABASE_ECHO=True              # Log SQL queries
DEBUG=True                      # FastAPI debug mode
```

---

## Next Steps (Week 3-5 Tasks)

### Week 3: Foundation Complete ✓
- [x] FastAPI project scaffold
- [x] PostgreSQL schema + Alembic migrations
- [x] Benchmark registry API (CRUD)

### Week 4: Dataset & Candidate Registry
- [ ] Import 30 Java benchmark tasks
- [ ] Candidate registry API (model registration)
- [ ] Model adapters (OpenAI, Anthropic, Local/Mock)

### Week 5: Multi-Model Setup
- [ ] Health checks for models
- [ ] Cost estimation
- [ ] Model gateway abstraction

---

## Troubleshooting

### Port Already in Use
```bash
# Kill existing container
docker-compose down

# Or use different ports in docker-compose.yml
```

### Database Connection Error
```bash
# Check PostgreSQL is running
docker-compose logs postgres

# Wait for health check
docker-compose ps

# Verify DATABASE_URL
echo $DATABASE_URL
```

### Module Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Or in Docker
docker-compose rebuild
```

### Clear Everything & Start Fresh
```bash
# Stop and remove containers
docker-compose down -v

# Rebuild and start
docker-compose up -d
```

---

## Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Database Connections
```bash
# Inside PostgreSQL
SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname;
```

### Application Logs
```bash
docker-compose logs --tail=50 arena_app
```

---

## Architecture

### Layered Design
```
┌─────────────────────────────────────┐
│  FastAPI Application (Port 8000)    │
├─────────────────────────────────────┤
│  Routes (benchmarks, candidates)    │
│  Schemas (Pydantic validation)      │
│  Models (SQLAlchemy ORM)            │
│  Database Session Management        │
├─────────────────────────────────────┤
│  PostgreSQL (Port 5432)             │
│  • BenchmarkSuite, Version, Task    │
│  • Candidate, CandidateVersion      │
│  • Experiment, Execution            │
└─────────────────────────────────────┘
```

### Request Flow
```
Client Request
    ↓
FastAPI Router
    ↓
Validation (Pydantic Schema)
    ↓
Database Layer (SQLAlchemy)
    ↓
PostgreSQL
    ↓
Response (JSON)
```

---

## Key Files to Know

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI app initialization, route registration |
| `app/models.py` | Database schema (tables, relationships) |
| `app/schemas.py` | Request/response validation (Pydantic) |
| `app/api/benchmarks.py` | Benchmark CRUD endpoints |
| `app/database.py` | Database connection, session management |
| `docker-compose.yml` | PostgreSQL + app orchestration |

---

## What's Next (After Week 3)

Once foundation is solid, you'll add:

1. **Candidate Registry** (Week 4)
   - Register models (Claude, GPT-4, Llama)
   - API endpoints for candidate management
   - Health checks and cost estimation

2. **Experiment Orchestration** (Week 5-6)
   - Queue system (task queuing)
   - Worker pool (job execution)
   - Metrics collection (latency, tokens, cost)

3. **Java Evaluation** (Week 7-9)
   - Docker-based code execution
   - Compilation, testing, scoring
   - Resource limits enforcement

4. **POC Completion** (Week 10)
   - Results aggregation
   - Comparison reporting
   - Stakeholder demo

---

## Questions?

- **Architecture unclear?** See Phase 0 Week 2 Design docs
- **API questions?** Check Swagger UI at `/docs`
- **Database schema?** Review `app/models.py`
- **Docker issues?** Check `docker-compose.yml` and Docker logs

---

**Ready to start Week 3 implementation?** 🚀