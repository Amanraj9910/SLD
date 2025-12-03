#!/bin/bash
set -e

cd /home/site/wwwroot
export PORT=${PORT:-8000}

echo "Installing dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r config/requirements.txt 2>/dev/null || true
pip install -r web_app/core/backend/requirements.txt 2>/dev/null || true
pip install gunicorn uvicorn

echo "Starting FastAPI backend on port $PORT..."
cd web_app/core/backend
exec gunicorn --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --timeout 600 --access-logfile - main:app
