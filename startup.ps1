#!/usr/bin/env pwsh
# App Service startup script for SLD Backend (Windows)

# Set up environment
Set-Location -Path "/home/site/wwwroot"

# Export port from App Service environment variable or default to 8000
$Port = if ($env:PORT) { $env:PORT } else { "8000" }
$env:PORT = $Port

# Install Python dependencies if needed
if (-not (Test-Path "venv")) {
    Write-Host "Creating Python virtual environment..."
    python -m venv venv
}

# Activate virtual environment
& ".\venv\Scripts\Activate.ps1"

# Install/upgrade dependencies
Write-Host "Installing Python dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r config/requirements.txt
pip install -r web_app/core/backend/requirements.txt

# Navigate to backend directory
Set-Location -Path "web_app/core/backend"

# Run FastAPI backend with uvicorn
Write-Host "Starting SLD Backend on port $Port..."
uvicorn main:app --host 0.0.0.0 --port $Port --access-log
