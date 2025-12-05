#!/bin/bash
set -e

echo "=============================================="
echo "🚀 Starting SLD Application Deployment"
echo "=============================================="

cd /home/site/wwwroot
export PORT=${PORT:-8000}

echo "📦 Installing Python dependencies..."
pip install --upgrade pip setuptools wheel --quiet

# Install from root requirements.txt (main deps)
if [ -f "requirements.txt" ]; then
    echo "   Installing from requirements.txt..."
    pip install -r requirements.txt --quiet
fi

# Install additional backend deps if exists
if [ -f "web_app/core/backend/requirements.txt" ]; then
    echo "   Installing from web_app/core/backend/requirements.txt..."
    pip install -r web_app/core/backend/requirements.txt --quiet
fi

# Ensure gunicorn and uvicorn are installed
pip install gunicorn uvicorn --quiet

echo "✅ Dependencies installed"

# Change to backend directory
cd web_app/core/backend

echo "📍 Working directory: $(pwd)"
echo "🌐 Starting FastAPI on port $PORT..."

# Start the application with gunicorn + uvicorn worker
exec gunicorn \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:$PORT \
    --timeout 600 \
    --graceful-timeout 120 \
    --keep-alive 5 \
    --access-logfile - \
    --error-logfile - \
    --capture-output \
    --log-level info \
    main:app
