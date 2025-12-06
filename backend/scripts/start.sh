#!/bin/bash
# Startup script for AI RPG backend

set -e

echo "🚀 Starting AI RPG Backend..."

# Wait for database to be ready
echo "⏳ Waiting for database..."
while ! pg_isready -h postgres -p 5432 -U postgres > /dev/null 2>&1; do
    sleep 1
done
echo "✅ Database is ready"

# Run database migrations
echo "📦 Running database migrations..."
alembic upgrade head

# Start the application
echo "🎮 Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
