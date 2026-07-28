#!/bin/bash

echo "🔄 Creating migration files..."
python -m alembic revision --autogenerate -m "Initial migration"

echo "🔄 Running database migrations..."
python -m alembic upgrade head

echo "🚀 Starting Uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000