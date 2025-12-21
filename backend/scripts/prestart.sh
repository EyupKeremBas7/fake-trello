#!/bin/bash

# Prestart script - runs before the application starts
# This ensures database is always set up correctly
set -e

echo "========================================"
echo "PRESTART SCRIPT - Database Setup"
echo "========================================"

# Wait for database to be ready
echo "[1/3] Waiting for database..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if python -c "from app.core.db import engine; engine.connect()" 2>/dev/null; then
        echo "Database is ready!"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Waiting for database... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "ERROR: Could not connect to database after $MAX_RETRIES attempts"
    exit 1
fi

# Run database migrations
echo "[2/3] Running database migrations..."
alembic upgrade head
echo "Migrations completed!"

# Initialize first superuser if needed
echo "[3/3] Initializing database (creating admin user if needed)..."
python app/initial_data.py

echo "========================================"
echo "PRESTART COMPLETED - Starting application"
echo "========================================"
