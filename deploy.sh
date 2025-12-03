#!/bin/bash
# App Service deployment script
# This ensures the Python backend is deployed correctly with frontend

set -e

echo "================================================"
echo "SLD Backend + Frontend Deployment Script"
echo "================================================"

cd /home/site/wwwroot

# Step 1: Verify we have Python
echo "Checking Python installation..."
python --version
pip --version

# Step 2: Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip setuptools wheel 2>&1 | tail -5
pip install -r requirements.txt 2>&1 | tail -5

# Step 3: Build frontend if Node.js is available
echo "Checking for Node.js..."
if command -v node &> /dev/null; then
    echo "Node.js found: $(node --version)"
    echo "Building frontend..."
    cd web_app/core/frontend
    npm ci 2>&1 | tail -5 || npm install 2>&1 | tail -5
    npm run build 2>&1 | tail -5
    cd /home/site/wwwroot
    echo "✅ Frontend built successfully"
else
    echo "⚠️  Node.js not found, skipping frontend build"
    echo "   Frontend static files should already exist in build/"
fi

# Step 4: Verify FastAPI can be imported
echo "Verifying FastAPI installation..."
python -c "import fastapi; print(f'FastAPI version: {fastapi.__version__}')"

# Step 5: Test app import
echo "Testing app import..."
python -c "import sys; sys.path.insert(0, './web_app/core/backend'); from main import app; print(f'✅ App imported successfully')"

# Step 6: Start the application
echo "================================================"
echo "Starting FastAPI application..."
echo "================================================"
export PORT=${PORT:-8000}

cd /home/site/wwwroot
exec python app.py
