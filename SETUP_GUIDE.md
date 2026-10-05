# Setup Guide: C/AI Arena POC Foundation

**Complete Phase 0 Foundation Implementation**  
FastAPI + PostgreSQL (Docker) working scaffold ready to extend.

---

## What You Have

A complete, working FastAPI application with:
- ✅ FastAPI web framework (Python)
- ✅ PostgreSQL database (in Docker)
- ✅ SQLAlchemy ORM (models, relationships)
- ✅ Pydantic schemas (request/response validation)
- ✅ Benchmark Registry API (CRUD endpoints)
- ✅ Database migrations ready (Alembic)
- ✅ Logging configured
- ✅ Docker Compose (one-command startup)
- ✅ Tests (basic API tests)

---

## Files Created (Complete Structure)

```
arena-poc/
├── docker-compose.yml           # PostgreSQL + app orchestration ⭐
├── Dockerfile                   # FastAPI container
├── requirements.txt             # Python dependencies
├── .env.example                 # Example environment variables
├── .gitignore                   # Git ignore rules
├── start.sh                     # Quick start (Linux/Mac)
├── start.bat                    # Quick start (Windows)
├── README.md                    # Detailed documentation
├── SETUP_GUIDE.md              # This file
│
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point ⭐
│   ├── config.py               # Configuration management ⭐
│   ├── database.py             # Database connection ⭐
│   ├── logger.py               # Logging setup
│   ├── models.py               # SQLAlchemy models (6 tables) ⭐⭐⭐
│   ├── schemas.py              # Pydantic schemas
│   └── api/
│       ├── __init__.py
│       └── benchmarks.py       # Benchmark CRUD endpoints ⭐⭐
│
└── tests/
    ├── __init__.py
    └── test_api.py            # API tests (9 test cases)
```

**⭐ = Critical files to understand**

---

## 60-Second Setup

### Option 1: Docker (Recommended)
```bash
# Go to project directory
cd arena-poc

# On Linux/Mac:
bash start.sh

# On Windows:
start.bat

# Wait 10 seconds...
# Then open: http://localhost:8000/docs
```

### Option 2: Manual
```bash
# Start PostgreSQL
docker-compose up -d postgres

# Install dependencies (Python 3.11+)
pip install -r requirements.txt

# Set database URL
export DATABASE_URL=postgresql://arena_user:arena_password@localhost:5432/arena_poc

# Run app
uvicorn app.main:app --reload

# Open: http://localhost:8000/docs
```

---

## Verify It Works

### Check 1: Health
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy",...}
```

### Check 2: Create Benchmark
```bash
curl -X POST http://localhost:8000/api/v1/benchmarks \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","tasks":[]}'
# Should return: {"id":"...","name":"Test",...}
```

### Check 3: List Benchmarks
```bash
curl http://localhost:8000/api/v1/benchmarks
# Should return: [{"id":"...","name":"Test",...}]
```

### Check 4: Database
```bash
docker exec -it arena_postgres psql -U arena_user -d arena_poc -c "SELECT * FROM benchmark_suites;"
# Should return: your benchmark
```

---

## How It Works

### Architecture
```
Client (curl, browser, app)
    ↓
FastAPI Router (/api/v1/benchmarks)
    ↓
Pydantic Schemas (validate input)
    ↓
SQLAlchemy Models (ORM)
    ↓
PostgreSQL Database
    ↓
Response (JSON)
```

### Database Schema (Simple Version)
```
BenchmarkSuite
├── name: "Java Programming"
├── created_at: 2024-01-01
└── versions[]
    └── BenchmarkVersion (v1.0, draft)
        ├── status: "draft"
        └── tasks[]
            └── Task
                ├── task_id: "java-001"
                ├── problem_statement: "Write code..."
                └── public_tests: [...]
```

### API Endpoints (Phase 0)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/benchmarks` | Create benchmark + tasks |
| GET | `/api/v1/benchmarks` | List all benchmarks |
| GET | `/api/v1/benchmarks/{id}` | Get specific benchmark |
| POST | `/api/v1/benchmarks/{id}/versions/{id}/publish` | Publish (make immutable) |
| GET | `/api/v1/benchmarks/{id}/versions` | List versions |
| POST | `/api/v1/benchmarks/{id}/versions/{id}/add-tasks` | Add tasks to draft |

---

## What's Ready vs What's Next

### ✅ Week 3 - Done (You Have This)
- FastAPI scaffold
- PostgreSQL schema
- Benchmark registry API
- Basic CRUD operations
- Tests framework

### ⏭️ Week 4 - Next (You'll Build)
- Import 30 Java benchmark tasks
- Candidate registry API (register models)
- Model adapter abstraction

### ⏭️ Week 5 - After (You'll Build)
- Model adapters (OpenAI, Anthropic, Mock)
- Health checks
- Cost estimation

---

## Key Code Locations

### Understand the Schema
**File:** `app/models.py`

```python
# This is what you're building on:
class BenchmarkSuite(Base):  # Parent table
    id = Column(UUID, primary_key=True)
    name = Column(String(255))
    versions = relationship("BenchmarkVersion")  # One-to-many

class BenchmarkVersion(Base):  # Versioned benchmark
    id = Column(UUID, primary_key=True)
    version_number = Column(String(20))  # v1.0, v1.1
    status = Column(String(50))  # draft or published
    tasks = relationship("Task")  # Tasks in this version

class Task(Base):  # Individual task
    id = Column(UUID, primary_key=True)
    task_id = Column(String(100))  # java-001
    problem_statement = Column(Text)
    public_tests = Column(JSON)
```

### Add an Endpoint
**File:** `app/api/benchmarks.py`

```python
@router.post("/api/v1/my-endpoint")
async def my_endpoint(request: MySchema, db: Session = Depends(get_db)):
    # request = validated input
    # db = database session (auto-closed after response)
    
    # Your code here
    return {"result": "..."}
```

### Change Configuration
**File:** `app/config.py`

```python
class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://..."
    LOG_LEVEL: str = "INFO"
    # Add your settings here
```

---

## Common Tasks

### Task 1: Create a New API Endpoint

1. **Add schema** in `app/schemas.py`:
```python
class MyInputSchema(BaseModel):
    field1: str
    field2: int

class MyOutputSchema(BaseModel):
    id: UUID
    field1: str
```

2. **Add endpoint** in `app/api/benchmarks.py`:
```python
@router.post("/my-endpoint")
async def my_endpoint(request: MyInputSchema, db: Session = Depends(get_db)):
    return MyOutputSchema(id=uuid.uuid4(), field1=request.field1)
```

3. **Test it**:
```bash
curl -X POST http://localhost:8000/api/v1/my-endpoint \
  -H "Content-Type: application/json" \
  -d '{"field1":"value","field2":42}'
```

### Task 2: Add a New Table

1. **Define model** in `app/models.py`:
```python
class MyTable(Base):
    __tablename__ = "my_tables"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
```

2. **Restart app** (tables auto-created on startup):
```bash
docker-compose restart arena_app
```

3. **Use in endpoints**:
```python
my_record = db.query(MyTable).filter(MyTable.id == some_id).first()
```

### Task 3: Run Tests

```bash
# With Docker
docker-compose exec arena_app pytest

# Locally
pytest tests/

# With verbose output
pytest tests/test_api.py -v

# Run specific test
pytest tests/test_api.py::TestBenchmarks::test_create_benchmark -v
```

### Task 4: View Database

```bash
# Interactive PostgreSQL shell
docker exec -it arena_postgres psql -U arena_user -d arena_poc

# In psql shell:
\dt              # List tables
SELECT * FROM benchmark_suites;  # Query table
\q              # Quit
```

### Task 5: View Logs

```bash
# App logs
docker-compose logs -f arena_app

# PostgreSQL logs
docker-compose logs -f postgres

# Specific lines
docker-compose logs --tail=50 arena_app
```

---

## Week 3 Checklist

You've completed Week 3 when:

- [x] **FastAPI project scaffold** ✓
  - Project structure created
  - Logging configured
  - Config management working
  
- [x] **PostgreSQL schema** ✓
  - 6 core tables created
  - Relationships defined
  - Immutability enforced (published versions)
  
- [x] **Benchmark registry API** ✓
  - POST /benchmarks (create)
  - GET /benchmarks (list)
  - GET /benchmarks/{id} (retrieve)
  - POST /.../publish (publish version)
  - POST /.../add-tasks (add tasks to draft)
  
- [x] **Docker setup** ✓
  - docker-compose.yml working
  - One-command startup
  - Health checks configured
  
- [x] **Tests** ✓
  - 9 test cases covering CRUD
  - Tests runnable with pytest
  
- [ ] **Can import 30 Java tasks** (Week 4)
- [ ] **Can register models** (Week 4)

---

## Week 4 Tasks (Preview)

Once Week 3 is solid:

1. **Get Java benchmark source** (LeetCode API or download)
2. **Create data import script**:
   ```python
   # Pseudo-code
   for task in json_file:
       db.add(Task(
           task_id=task["id"],
           problem_statement=task["description"],
           public_tests=task["tests"]
       ))
   ```
3. **Add Candidate registry** (similar to benchmarks)
4. **Create model adapters** (abstraction for Claude, GPT-4, etc.)

---

## Troubleshooting

### "Port 5432 already in use"
```bash
# Stop existing container
docker-compose down

# Or use different port in docker-compose.yml
```

### "DATABASE_URL not set"
```bash
# Set it
export DATABASE_URL=postgresql://arena_user:arena_password@localhost:5432/arena_poc

# Or use .env file
cp .env.example .env
```

### "ModuleNotFoundError: No module named 'app'"
```bash
# Install dependencies
pip install -r requirements.txt

# Or with Docker
docker-compose rebuild
```

### "Connection refused (PostgreSQL)"
```bash
# Check if postgres is running
docker-compose ps

# If not, start it
docker-compose up -d postgres

# Wait 5 seconds for health check
sleep 5

# Test connection
docker exec -it arena_postgres pg_isready
```

### "Test fails with 'database is locked'"
```bash
# Clear test database
rm test.db

# Rerun tests
pytest tests/
```

---

## Next Steps

1. **Verify setup works** (run health check, create benchmark)
2. **Explore API docs** (http://localhost:8000/docs)
3. **Read `app/models.py`** (understand the schema)
4. **Read `app/api/benchmarks.py`** (understand the endpoints)
5. **Week 4:** Add candidate registry and model adapters

---

## Questions?

- **API not starting?** Check: `docker-compose logs arena_app`
- **Database not connecting?** Check: `docker-compose logs postgres`
- **Schema unclear?** Read: `app/models.py`
- **Endpoints unclear?** Check: `app/api/benchmarks.py`
- **How to add something?** See "Common Tasks" section above

---

## Quick Reference

| Need | Command |
|------|---------|
| Start all | `docker-compose up -d` |
| Stop all | `docker-compose down` |
| View logs | `docker-compose logs -f` |
| Run tests | `pytest tests/` |
| API docs | http://localhost:8000/docs |
| Health | `curl http://localhost:8000/health` |
| Access DB | `docker exec -it arena_postgres psql ...` |
| Rebuild images | `docker-compose build` |
| Fresh start | `docker-compose down -v && docker-compose up -d` |

---

**You're ready for Week 3 implementation.** 🚀

Next: Import Java benchmarks (Week 4) and candidate registry (Week 4).