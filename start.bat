@echo off
REM C/AI Arena POC - Quick Start Script for Windows

setlocal enabledelayedexpansion

echo.
echo 🚀 C/AI Arena POC - Quick Start (Windows)
echo =========================================
echo.

REM Check for Docker
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed. Please install Docker for Windows.
    pause
    exit /b 1
)

REM Check for docker-compose
where docker-compose >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Docker Compose is not installed.
    pause
    exit /b 1
)

REM Create .env if it doesn't exist
if not exist .env (
    echo 📝 Creating .env from .env.example...
    copy .env.example .env
    echo ✅ .env created.
)

REM Create logs directory
if not exist logs mkdir logs

echo.
echo 🐳 Starting Docker services...
docker-compose down
docker-compose up -d

echo.
echo ⏳ Waiting for PostgreSQL to be ready...
for /l %%i in (1,1,30) do (
    docker-compose exec -T postgres pg_isready -U arena_user -d arena_poc >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✅ PostgreSQL is ready!
        goto postgres_ready
    )
    echo -n "."
    timeout /t 1 /nobreak >nul 2>&1
)
echo ❌ PostgreSQL failed to start
docker-compose logs postgres
pause
exit /b 1

:postgres_ready
echo.
echo ⏳ Waiting for API to be ready...
for /l %%i in (1,1,30) do (
    curl -s http://localhost:8000/health >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✅ API is ready!
        goto api_ready
    )
    echo -n "."
    timeout /t 1 /nobreak >nul 2>&1
)
echo ⚠️  API didn't respond. Check logs.
goto continue

:api_ready
echo.
echo =========================================
echo ✅ All services are running!
echo =========================================
echo.

:continue
echo 📚 Next steps:
echo    * API Docs:   http://localhost:8000/docs
echo    * Health:     http://localhost:8000/health
echo    * Logs:       docker-compose logs -f
echo    * Stop:       docker-compose down
echo.
echo 🧪 Test the API:
echo    curl http://localhost:8000/health
echo.
echo 💾 Database access:
echo    docker exec -it arena_postgres psql -U arena_user -d arena_poc
echo.
pause