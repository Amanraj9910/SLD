#!/bin/bash
set -e

echo "=============================================="
echo "🚀 SLD Application - Azure Startup Script"
echo "=============================================="

# Set working directory
cd /home/site/wwwroot
export PORT=${PORT:-8000}

echo "📍 Working directory: $(pwd)"
echo "📦 Installing Python dependencies..."

# Upgrade pip first
python3 -m pip install --upgrade pip setuptools wheel --quiet 2>/dev/null || true

# Install from root requirements.txt
if [ -f "requirements.txt" ]; then
    echo "   → Installing from requirements.txt..."
    python3 -m pip install -r requirements.txt --quiet 2>/dev/null || python3 -m pip install -r requirements.txt
fi

# Install gunicorn and uvicorn (critical for running the app)
python3 -m pip install gunicorn uvicorn --quiet 2>/dev/null || python3 -m pip install gunicorn uvicorn

echo "✅ Dependencies installed"

# List installed packages for debugging
echo "📋 Key packages installed:"
python3 -m pip list | grep -E "(fastapi|uvicorn|gunicorn)" || true

# Change to backend directory
cd web_app/core/backend

echo "📍 Backend directory: $(pwd)"
echo "🌐 Starting FastAPI on port $PORT..."

# Start the application
exec gunicorn \
    --workers 1 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:$PORT \
    --timeout 600 \
    --graceful-timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    main:app
