#!/bin/bash
# App Service deployment script
# This ensures the Python backend is deployed correctly

set -e

echo "================================================"
echo "SLD Backend Deployment Script"
echo "================================================"

cd /home/site/wwwroot

# Step 1: Verify we have Python
echo "Checking Python installation..."
python --version
pip --version

# Step 2: Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip setuptools wheel 2>&1 | tail -5
pip install -r requirements.txt 2>&1 | tail -5

# Step 3: Verify FastAPI can be imported
echo "Verifying FastAPI installation..."
python -c "import fastapi; print(f'FastAPI version: {fastapi.__version__}')"

# Step 4: Test app import
echo "Testing app import..."
python -c "import sys; sys.path.insert(0, './web_app/core/backend'); from main import app; print(f'✅ App imported successfully')"

# Step 5: Start the application
echo "================================================"
echo "Starting FastAPI application..."
echo "================================================"
export PORT=${PORT:-8000}

cd /home/site/wwwroot
exec python app.py
