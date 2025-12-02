@echo off
title SLD Platform - Complete Setup and Start
color 0E

echo.
echo =============================================
echo   SLD Platform - Complete Setup and Start
echo =============================================
echo.
echo This script will:
echo 1. Check system requirements
echo 2. Install missing dependencies
echo 3. Set up the environment
echo 4. Start both backend and frontend
echo 5. Open the application in your browser
echo.

set /p continue="Continue? (Y/N): "
if /i not "%continue%"=="Y" exit /b 0

echo.
echo 🔍 Step 1: System Requirements Check
echo =====================================

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    py --version >nul 2>&1
    if errorlevel 1 (
        echo ❌ Python not found!
        echo.
        echo Please install Python 3.8+ from https://python.org
        echo Make sure to check "Add Python to PATH" during installation
        echo.
        echo After installing Python, run this script again.
        echo.
        start https://python.org/downloads/
        pause
        exit /b 1
    ) else (
        set "PYTHON_CMD=py"
        echo ✅ Python found (using 'py' command)
    )
) else (
    set "PYTHON_CMD=python"
    echo ✅ Python found (using 'python' command)
)

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js not found!
    echo.
    echo Please install Node.js 16+ from https://nodejs.org
    echo After installing Node.js, run this script again.
    echo.
    start https://nodejs.org/
    pause
    exit /b 1
) else (
    echo ✅ Node.js found
)

echo.
echo 📦 Step 2: Installing Dependencies
echo ==================================

REM Install Python dependencies
echo Installing Python packages...
cd /d "%~dp0web_app\backend"
%PYTHON_CMD% -m pip install --upgrade pip
%PYTHON_CMD% -m pip install fastapi uvicorn pydantic-settings python-multipart python-dotenv
if errorlevel 1 (
    echo ❌ Failed to install Python dependencies
    pause
    exit /b 1
)
echo ✅ Python dependencies installed

REM Install Node.js dependencies
echo Installing Node.js packages...
cd /d "%~dp0web_app\frontend"
if not exist "node_modules" (
    npm install
    if errorlevel 1 (
        echo ❌ Failed to install Node.js dependencies
        pause
        exit /b 1
    )
)
echo ✅ Node.js dependencies installed

echo.
echo 🔧 Step 3: Environment Setup
echo =============================

cd /d "%~dp0"

REM Create directories
if not exist "uploads" mkdir "uploads"
if not exist "logs" mkdir "logs"
if not exist "results" mkdir "results"
if not exist "annotation_projects" mkdir "annotation_projects"
echo ✅ Directories created

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo Creating environment configuration...
    (
        echo # SLD Processing Platform Configuration
        echo DEBUG=true
        echo LOG_LEVEL=INFO
        echo API_HOST=0.0.0.0
        echo API_PORT=8000
        echo.
        echo # Azure Document Intelligence Configuration
        echo AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://sld.cognitiveservices.azure.com/
        echo AZURE_DOCUMENT_INTELLIGENCE_KEY=8n1hs7EHtYI7nKxRvktl9VhoRg3GnKQYYcd1xqMXne2t8avsu9pgJQQJ99BEACYeBjFXJ3w3AAAAACOGm7Iv
    ) > .env
    echo ✅ Environment file created
) else (
    echo ✅ Environment file exists
)

echo.
echo 🚀 Step 4: Starting Services
echo =============================

REM Clean up any existing processes
echo Cleaning up existing processes...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000') do taskkill /f /pid %%a >nul 2>&1

REM Start backend
echo 📡 Starting Backend Server...
start "SLD Backend" cmd /k "title SLD Backend Server && cd /d "%~dp0web_app\backend" && echo ======================================== && echo   SLD Backend Server Started && echo ======================================== && echo 📡 Backend: http://localhost:8000 && echo 📖 API Docs: http://localhost:8000/docs && echo ❤️ Health: http://localhost:8000/health && echo. && %PYTHON_CMD% main_fixed.py"

REM Wait for backend
echo ⏳ Waiting for backend to start...
timeout /t 5 /nobreak >nul

REM Start frontend
echo 🌐 Starting Frontend Server...
start "SLD Frontend" cmd /k "title SLD Frontend Server && cd /d "%~dp0web_app\frontend" && echo ======================================== && echo   SLD Frontend Server Started && echo ======================================== && echo 🌐 Frontend: http://localhost:3000 && echo 🔗 Backend: http://localhost:8000 && echo. && npm start"

echo.
echo 🌍 Step 5: Opening Application
echo ==============================

echo ⏳ Waiting for services to fully initialize...
timeout /t 10 /nobreak >nul

echo 🌍 Opening SLD Platform in your browser...
start http://localhost:3000

echo.
echo =============================================
echo   🎉 SLD Platform Setup Complete!
echo =============================================
echo.
echo 🌍 Your SLD Platform is now running:
echo.
echo   🌐 Main Application: http://localhost:3000
echo   📡 Backend API:      http://localhost:8000  
echo   📖 API Documentation: http://localhost:8000/docs
echo   ❤️  Health Check:    http://localhost:8000/health
echo.
echo 📋 What you can do now:
echo   ✅ Upload SLD images for component detection
echo   ✅ Extract text from documents using Azure OCR
echo   ✅ Create manual annotations for training data
echo   ✅ View API documentation and test endpoints
echo.
echo 🛑 To stop the platform:
echo   - Run: stop_sld_platform.bat
echo   - Or close both server windows
echo.
echo 🔄 To restart later:
echo   - Run: quick_start.bat (fastest)
echo   - Run: start_sld_platform.bat (standard)
echo   - Run: start_sld_advanced.bat (with health checks)
echo.

pause
