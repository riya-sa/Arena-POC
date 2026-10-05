#!/bin/bash

# C/AI Arena POC - Quick Start Script

set -e

echo "🚀 C/AI Arena POC - Quick Start"
echo "================================"

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "✅ .env created. You can edit it if needed."
fi

# Create logs directory
mkdir -p logs

echo "🐳 Starting Docker services..."
docker-compose down 2>/dev/null || true  # Remove existing containers
docker-compose up -d

echo "⏳ Waiting for PostgreSQL to be ready (health check)..."
for i in {1..30}; do
    if docker-compose exec -T postgres pg_isready -U arena_user -d arena_poc &> /dev/null; then
        echo "✅ PostgreSQL is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ PostgreSQL failed to start. Check logs with: docker-compose logs postgres"
        exit 1
    fi
    echo -n "."
    sleep 1
done

echo ""
echo "⏳ Waiting for API to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health &> /dev/null; then
        echo "✅ API is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "⚠️  API didn't respond. Check logs with: docker-compose logs arena_app"
        exit 1
    fi
    echo -n "."
    sleep 1
done

echo ""
echo "================================"
echo "✅ All services are running!"
echo "================================"
echo ""
echo "📚 Next steps:"
echo "   • API Docs:   http://localhost:8000/docs"
echo "   • Health:     http://localhost:8000/health"
echo "   • Logs:       docker-compose logs -f"
echo "   • Stop:       docker-compose down"
echo ""
echo "🧪 Test the API:"
echo "   curl http://localhost:8000/health"
echo ""
echo "💾 Database access:"
echo "   docker exec -it arena_postgres psql -U arena_user -d arena_poc"
echo ""