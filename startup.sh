#!/bin/bash

# App Service startup script for SLD Backend

# Set up environment
cd /home/site/wwwroot

# Export port from App Service environment variable or default to 8000
export PORT=${PORT:-8000}

# Install Python dependencies if needed
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/upgrade dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r config/requirements.txt
pip install -r web_app/core/backend/requirements.txt

# Navigate to backend directory
cd web_app/core/backend

# Run FastAPI backend with uvicorn
echo "Starting SLD Backend on port $PORT..."
uvicorn main:app --host 0.0.0.0 --port $PORT --access-log
