# C/AI Arena Optimization - API Specification

**Version:** 1.0.0  
**Base URL:** `http://localhost:8000/api/v1` (development)  
**Authentication:** Bearer token (JWT)

---

## Table of Contents

1. [Health & System](#health--system)
2. [Benchmarks](#benchmarks)
3. [Candidates](#candidates)
4. [Experiments](#experiments)
5. [Executions](#executions)
6. [Results](#results)
7. [Statistics](#statistics)
8. [Configuration](#configuration)
9. [Error Responses](#error-responses)

---

## Health & System

### Get Health Status

```
GET /health
```

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development",
  "timestamp": "2026-10-21T12:00:00Z"
}
```

---

### Get System Info

```
GET /info
```

**Response:** `200 OK`
```json
{
  "app_name": "C/AI Arena Optimization",
  "version": "1.0.0",
  "environment": "development",
  "database": "postgresql",
  "queue": "memory",
  "adapters": ["mock"],
  "uptime_seconds": 3600
}
```

---

## Benchmarks

### List Benchmarks

```
GET /benchmarks
```

**Query Parameters:**
- `skip` (int, default: 0)
- `limit` (int, default: 20, max: 100)
- `status` (string: "active", "archived")

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "bench-uuid-001",
      "name": "Math Reasoning Benchmark",
      "description": "Test mathematical problem solving",
      "status": "active",
      "version_count": 3,
      "task_count": 50,
      "created_at": "2026-10-01T10:00:00Z",
      "updated_at": "2026-10-21T12:00:00Z"
    }
  ],
  "total": 5,
  "skip": 0,
  "limit": 20
}
```

---

### Create Benchmark

```
POST /benchmarks
Content-Type: application/json
Authorization: Bearer {token}
```

**Request Body:**
```json
{
  "name": "Code Generation Benchmark",
  "description": "Test code generation capabilities",
  "language": "python",
  "difficulty": "advanced"
}
```

**Response:** `201 Created`
```json
{
  "id": "bench-uuid-002",
  "name": "Code Generation Benchmark",
  "description": "Test code generation capabilities",
  "status": "active",
  "version_count": 0,
  "task_count": 0,
  "created_at": "2026-10-21T12:00:00Z",
  "updated_at": "2026-10-21T12:00:00Z"
}
```

---

### Get Benchmark by ID

```
GET /benchmarks/{benchmark_id}
```

**Response:** `200 OK`
```json
{
  "id": "bench-uuid-001",
  "name": "Math Reasoning Benchmark",
  "description": "Test mathematical problem solving",
  "status": "active",
  "versions": [
    {
      "id": "v1",
      "version_number": 1,
      "task_count": 50,
      "created_at": "2026-10-01T10:00:00Z"
    }
  ],
  "tasks": [
    {
      "id": "task-001",
      "name": "Addition",
      "description": "Simple addition",
      "input": "2 + 2",
      "expected_output": "4"
    }
  ]
}
```

---

### Create Benchmark Version

```
POST /benchmarks/{benchmark_id}/versions
Content-Type: application/json
Authorization: Bearer {token}
```

**Request Body:**
```json
{
  "tasks": [
    {
      "name": "Problem 1",
      "description": "Solve this math problem",
      "input": "What is 15 + 27?",
      "expected_output": "42"
    },
    {
      "name": "Problem 2",
      "description": "Solve this math problem",
      "input": "What is 100 / 4?",
      "expected_output": "25"
    }
  ]
}
```

**Response:** `201 Created`
```json
{
  "id": "v2",
  "version_number": 2,
  "benchmark_id": "bench-uuid-001",
  "task_count": 2,
  "created_at": "2026-10-21T12:00:00Z"
}
```

---

## Candidates

### List Candidates

```
GET /candidates
```

**Query Parameters:**
- `skip` (int, default: 0)
- `limit` (int, default: 20)

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "cand-uuid-001",
      "name": "Claude Opus",
      "provider": "anthropic",
      "model": "claude-opus-4-6",
      "status": "active",
      "created_at": "2026-10-01T10:00:00Z"
    },
    {
      "id": "cand-uuid-002",
      "name": "GPT-4",
      "provider": "openai",
      "model": "gpt-4-turbo",
      "status": "active",
      "created_at": "2026-10-01T10:00:00Z"
    }
  ],
  "total": 10,
  "skip": 0,
  "limit": 20
}
```

---

### Create Candidate

```
POST /candidates
Content-Type: application/json
Authorization: Bearer {token}
```

**Request Body:**
```json
{
  "name": "Claude Sonnet",
  "provider": "anthropic",
  "model": "claude-sonnet-4-6",
  "config": {
    "temperature": 0.7,
    "max_tokens": 2048
  }
}
```

**Response:** `201 Created`
```json
{
  "id": "cand-uuid-003",
  "name": "Claude Sonnet",
  "provider": "anthropic",
  "model": "claude-sonnet-4-6",
  "status": "active",
  "created_at": "2026-10-21T12:00:00Z"
}
```

---

## Experiments

### List Experiments

```
GET /experiments
```

**Query Parameters:**
- `skip` (int, default: 0)
- `limit` (int, default: 20)
- `status` (string: "created", "queued", "running", "complete", "failed", "cancelled")
- `benchmark_id` (string, optional)

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "exp-uuid-001",
      "name": "Experiment 1: Opus vs GPT-4",
      "benchmark_id": "bench-uuid-001",
      "benchmark_version_id": "v1",
      "status": "running",
      "candidate_count": 2,
      "execution_count": 4,
      "execution_success": 3,
      "execution_failed": 1,
      "progress_percent": 75,
      "created_at": "2026-10-21T10:00:00Z",
      "started_at": "2026-10-21T10:05:00Z",
      "completed_at": null
    }
  ],
  "total": 15,
  "skip": 0,
  "limit": 20
}
```

---

### Create Experiment

```
POST /experiments
Content-Type: application/json
Authorization: Bearer {token}
```

**Request Body:**
```json
{
  "name": "Experiment: New Models",
  "description": "Compare new models on math benchmarks",
  "benchmark_id": "bench-uuid-001",
  "benchmark_version_id": "v1",
  "candidate_ids": ["cand-uuid-001", "cand-uuid-002"],
  "runs_per_candidate": 2
}
```

**Response:** `201 Created`
```json
{
  "id": "exp-uuid-002",
  "name": "Experiment: New Models",
  "description": "Compare new models on math benchmarks",
  "benchmark_id": "bench-uuid-001",
  "benchmark_version_id": "v1",
  "status": "created",
  "candidate_count": 2,
  "execution_count": 0,
  "execution_success": 0,
  "execution_failed": 0,
  "progress_percent": 0,
  "created_at": "2026-10-21T12:00:00Z",
  "started_at": null,
  "completed_at": null
}
```

---

### Get Experiment by ID

```
GET /experiments/{experiment_id}
```

**Response:** `200 OK`
```json
{
  "id": "exp-uuid-001",
  "name": "Experiment 1: Opus vs GPT-4",
  "benchmark_id": "bench-uuid-001",
  "status": "running",
  "executions": [
    {
      "id": "exec-001",
      "candidate_id": "cand-uuid-001",
      "candidate_name": "Claude Opus",
      "status": "complete",
      "score": 95.5,
      "execution_time_seconds": 2.34,
      "started_at": "2026-10-21T10:05:00Z",
      "completed_at": "2026-10-21T10:05:02Z"
    },
    {
      "id": "exec-002",
      "candidate_id": "cand-uuid-002",
      "candidate_name": "GPT-4",
      "status": "running",
      "score": null,
      "execution_time_seconds": null,
      "started_at": "2026-10-21T10:05:10Z",
      "completed_at": null
    }
  ]
}
```

---

### Queue Experiment

```
POST /experiments/{experiment_id}/queue
Authorization: Bearer {token}
```

**Response:** `200 OK`
```json
{
  "id": "exp-uuid-001",
  "status": "queued",
  "queued_at": "2026-10-21T12:00:00Z",
  "message": "Experiment queued for execution"
}
```

---

### Cancel Experiment

```
POST /experiments/{experiment_id}/cancel
Authorization: Bearer {token}
```

**Response:** `200 OK`
```json
{
  "id": "exp-uuid-001",
  "status": "cancelled",
  "cancelled_at": "2026-10-21T12:05:00Z",
  "message": "Experiment cancelled"
}
```

---

## Executions

### Get Execution by ID

```
GET /experiments/{experiment_id}/executions/{execution_id}
```

**Response:** `200 OK`
```json
{
  "id": "exec-001",
  "experiment_id": "exp-uuid-001",
  "candidate_id": "cand-uuid-001",
  "candidate_name": "Claude Opus",
  "status": "complete",
  "score": 95.5,
  "metrics": {
    "accuracy": 0.95,
    "precision": 0.94,
    "recall": 0.96,
    "f1_score": 0.95
  },
  "execution_time_seconds": 2.34,
  "error_message": null,
  "started_at": "2026-10-21T10:05:00Z",
  "completed_at": "2026-10-21T10:05:02Z"
}
```

---

### Stream Execution Logs

```
GET /experiments/{experiment_id}/executions/{execution_id}/logs
```

**Response:** `200 OK` (text/event-stream)
```
data: {"timestamp": "2026-10-21T10:05:00.123Z", "level": "INFO", "message": "Starting execution"}
data: {"timestamp": "2026-10-21T10:05:01.456Z", "level": "INFO", "message": "Task 1/50 complete"}
data: {"timestamp": "2026-10-21T10:05:02.789Z", "level": "INFO", "message": "Task 50/50 complete"}
```

---

## Results

### Get Experiment Results

```
GET /experiments/{experiment_id}/results
```

**Query Parameters:**
- `format` (string: "json", "csv")

**Response:** `200 OK`
```json
{
  "experiment_id": "exp-uuid-001",
  "benchmark_name": "Math Reasoning Benchmark",
  "results": {
    "Claude Opus": {
      "score": 95.5,
      "accuracy": 0.955,
      "execution_time_avg": 2.34,
      "execution_time_std": 0.12,
      "failures": 0
    },
    "GPT-4": {
      "score": 92.3,
      "accuracy": 0.923,
      "execution_time_avg": 3.21,
      "execution_time_std": 0.45,
      "failures": 1
    }
  },
  "generated_at": "2026-10-21T12:00:00Z"
}
```

---

### Export Results

```
GET /experiments/{experiment_id}/results/export
```

**Query Parameters:**
- `format` (string: "csv", "json", "xlsx")

**Response:** `200 OK` (application/octet-stream)
```
Attachment: experiment_exp-uuid-001_results.csv
```

---

## Statistics

### Get Leaderboard

```
GET /statistics/leaderboard
```

**Query Parameters:**
- `benchmark_id` (string, optional)
- `limit` (int, default: 10)

**Response:** `200 OK`
```json
{
  "benchmark_id": "bench-uuid-001",
  "benchmark_name": "Math Reasoning Benchmark",
  "leaderboard": [
    {
      "rank": 1,
      "candidate_id": "cand-uuid-001",
      "candidate_name": "Claude Opus",
      "average_score": 95.5,
      "experiment_count": 3,
      "win_count": 2,
      "tie_count": 1,
      "loss_count": 0,
      "confidence_interval": {
        "lower": 93.2,
        "upper": 97.8
      }
    },
    {
      "rank": 2,
      "candidate_id": "cand-uuid-002",
      "candidate_name": "GPT-4",
      "average_score": 92.3,
      "experiment_count": 3,
      "win_count": 0,
      "tie_count": 1,
      "loss_count": 2,
      "confidence_interval": {
        "lower": 89.1,
        "upper": 95.5
      }
    }
  ]
}
```

---

### Statistical Significance

```
GET /statistics/significance
```

**Query Parameters:**
- `candidate_a_id` (string)
- `candidate_b_id` (string)
- `benchmark_id` (string, optional)

**Response:** `200 OK`
```json
{
  "candidate_a_id": "cand-uuid-001",
  "candidate_a_name": "Claude Opus",
  "candidate_b_id": "cand-uuid-002",
  "candidate_b_name": "GPT-4",
  "benchmark_id": "bench-uuid-001",
  "difference": 3.2,
  "p_value": 0.0234,
  "significant_at_alpha_0_05": true,
  "effect_size": 0.45,
  "confidence_interval": {
    "lower": 0.5,
    "upper": 5.9
  }
}
```

---

## Configuration

### Get Configuration

```
GET /config
Authorization: Bearer {token}
```

**Response:** `200 OK`
```json
{
  "environment": "development",
  "database_url": "postgresql://...",
  "log_level": "DEBUG",
  "log_format": "text",
  "adapter_type": "mock",
  "queue_type": "memory",
  "max_concurrent_executions": 5
}
```

---

### Update Configuration

```
PATCH /config
Content-Type: application/json
Authorization: Bearer {token}
```

**Request Body:**
```json
{
  "log_level": "INFO",
  "max_concurrent_executions": 10
}
```

**Response:** `200 OK`
```json
{
  "environment": "development",
  "log_level": "INFO",
  "max_concurrent_executions": 10
}
```

---

## Error Responses

### Error Response Format

```json
{
  "error": "ValidationError",
  "message": "Invalid benchmark_id format",
  "status_code": 400,
  "timestamp": "2026-10-21T12:00:00Z"
}
```

---

### Common Status Codes

| Code | Error | Meaning |
|------|-------|---------|
| 200 | OK | Success |
| 201 | Created | Resource created |
| 400 | ValidationError | Invalid input |
| 401 | SecurityError | Unauthorized |
| 403 | SecurityError | Forbidden |
| 404 | NotFoundError | Resource not found |
| 409 | ConflictError | Resource conflict |
| 500 | SystemError | Server error |
| 503 | AdapterError | Service unavailable |

---

### Example Errors

**400 Bad Request**
```json
{
  "error": "ValidationError",
  "message": "Field 'name' is required",
  "status_code": 400
}
```

**404 Not Found**
```json
{
  "error": "BenchmarkNotFoundError",
  "message": "Benchmark 'bench-invalid' not found",
  "status_code": 404
}
```

**503 Service Unavailable**
```json
{
  "error": "AdapterError",
  "message": "Failed to connect to adapter: connection refused",
  "status_code": 503
}
```

---

## Authentication

### Bearer Token

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Tokens obtained from:
```
POST /auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## Rate Limiting

**Rate limit:** 100 requests per minute per token

**Headers returned:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1634846460
```

---

## Pagination

All list endpoints support pagination:

**Query Parameters:**
- `skip` (int, default: 0)
- `limit` (int, default: 20, max: 100)

**Response includes:**
```json
{
  "items": [...],
  "total": 150,
  "skip": 0,
  "limit": 20
}
```

---

**API v1 Complete | Ready for Frontend Integration**