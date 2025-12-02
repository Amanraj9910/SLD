@echo off
title SLD Processing Platform - Advanced Startup
color 0A

echo.
echo ================================================
echo   SLD Processing Platform - Advanced Startup
echo ================================================
echo.

REM Set the base directory
set "BASE_DIR=%~dp0"
set "BACKEND_DIR=%BASE_DIR%web_app\backend"
set "FRONTEND_DIR=%BASE_DIR%web_app\frontend"
set "LOG_FILE=%BASE_DIR%logs\startup.log"

REM Create logs directory
if not exist "%BASE_DIR%logs" mkdir "%BASE_DIR%logs"

REM Initialize log file
echo [%date% %time%] SLD Platform Startup Started > "%LOG_FILE%"

echo 🔍 Performing system checks...

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
        pause
        exit /b 1
    ) else (
        set "PYTHON_CMD=py"
        for /f "tokens=*" %%i in ('py --version') do set "PYTHON_VERSION=%%i"
    )
) else (
    set "PYTHON_CMD=python"
    for /f "tokens=*" %%i in ('python --version') do set "PYTHON_VERSION=%%i"
)

echo ✅ %PYTHON_VERSION%

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js not found!
    echo.
    echo Please install Node.js 16+ from https://nodejs.org
    echo After installing Node.js, run this script again.
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('node --version') do set "NODE_VERSION=%%i"
    echo ✅ Node.js %NODE_VERSION%
)

REM Check npm
npm --version >nul 2>&1
if errorlevel 1 (
    echo ❌ npm not found!
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('npm --version') do set "NPM_VERSION=%%i"
    echo ✅ npm %NPM_VERSION%
)

echo.
echo 📦 Checking dependencies...

REM Check if Python dependencies are installed
cd /d "%BACKEND_DIR%"
%PYTHON_CMD% -c "import fastapi, uvicorn" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Python dependencies missing. Installing...
    %PYTHON_CMD% -m pip install fastapi uvicorn pydantic-settings python-multipart
    if errorlevel 1 (
        echo ❌ Failed to install Python dependencies
        pause
        exit /b 1
    )
    echo ✅ Python dependencies installed
) else (
    echo ✅ Python dependencies available
)

REM Check if Node.js dependencies are installed
cd /d "%FRONTEND_DIR%"
if not exist "node_modules" (
    echo ⚠️  Node.js dependencies missing. Installing...
    npm install
    if errorlevel 1 (
        echo ❌ Failed to install Node.js dependencies
        pause
        exit /b 1
    )
    echo ✅ Node.js dependencies installed
) else (
    echo ✅ Node.js dependencies available
)

echo.
echo 🔧 Preparing environment...

REM Create necessary directories
cd /d "%BASE_DIR%"
if not exist "uploads" mkdir "uploads"
if not exist "results" mkdir "results"
if not exist "annotation_projects" mkdir "annotation_projects"

echo ✅ Directories created

REM Check if .env file exists
if not exist ".env" (
    echo ⚠️  Environment file missing. Creating basic .env...
    echo # SLD Processing Platform Configuration > .env
    echo DEBUG=true >> .env
    echo LOG_LEVEL=INFO >> .env
    echo API_HOST=0.0.0.0 >> .env
    echo API_PORT=8000 >> .env
    echo. >> .env
    echo # Azure Document Intelligence Configuration >> .env
    echo AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://sld.cognitiveservices.azure.com/ >> .env
    echo AZURE_DOCUMENT_INTELLIGENCE_KEY=8n1hs7EHtYI7nKxRvktl9VhoRg3GnKQYYcd1xqMXne2t8avsu9pgJQQJ99BEACYeBjFXJ3w3AAAAACOGm7Iv >> .env
    echo ✅ Environment file created
) else (
    echo ✅ Environment file exists
)

echo.
echo 🚀 Starting services...

REM Kill any existing processes on ports 8000 and 3000
echo 🧹 Cleaning up existing processes...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000') do taskkill /f /pid %%a >nul 2>&1

REM Start backend
echo 📡 Starting Backend Server...
cd /d "%BACKEND_DIR%"
start "SLD Backend Server" cmd /k "title SLD Backend && echo ========================================= && echo   SLD Backend Server && echo ========================================= && echo. && echo 📡 Starting on http://localhost:8000 && echo 📖 API Docs: http://localhost:8000/docs && echo ❤️  Health: http://localhost:8000/health && echo. && %PYTHON_CMD% main_fixed.py"

REM Wait for backend to start
echo ⏳ Waiting for backend to initialize...
timeout /t 5 /nobreak >nul

REM Test backend health
echo 🔍 Testing backend connection...
for /l %%i in (1,1,10) do (
    curl -s http://localhost:8000/health >nul 2>&1
    if not errorlevel 1 (
        echo ✅ Backend is responding
        goto backend_ready
    )
    timeout /t 2 /nobreak >nul
)
echo ⚠️  Backend may still be starting...

:backend_ready

REM Start frontend
echo 🌐 Starting Frontend Server...
cd /d "%FRONTEND_DIR%"
start "SLD Frontend Server" cmd /k "title SLD Frontend && echo ========================================= && echo   SLD Frontend Server && echo ========================================= && echo. && echo 🌐 Starting on http://localhost:3000 && echo 🔗 Backend: http://localhost:8000 && echo. && npm start"

REM Wait for frontend to start
echo ⏳ Waiting for frontend to initialize...
timeout /t 10 /nobreak >nul

echo.
echo ================================================
echo   🎉 SLD Platform Started Successfully!
echo ================================================
echo.
echo 🌍 Services:
echo   📡 Backend:  http://localhost:8000
echo   🌐 Frontend: http://localhost:3000
echo   📖 API Docs: http://localhost:8000/docs
echo   ❤️  Health:  http://localhost:8000/health
echo.
echo 📋 What's Running:
echo   ✅ Backend server (Python/FastAPI)
echo   ✅ Frontend server (React/Node.js)
echo   ✅ Mock AI services (Component Detection, Text Extraction)
echo.
echo 🌍 Opening browser...
timeout /t 3 /nobreak >nul
start http://localhost:3000

echo.
echo ================================================
echo   Platform Ready!
echo ================================================
echo.
echo 🎯 Next Steps:
echo 1. Browser should open automatically to http://localhost:3000
echo 2. Try uploading an SLD image for component detection
echo 3. Test text extraction with a PDF or image
echo 4. Check the debug panel in bottom-right corner
echo.
echo 🛑 To Stop Platform:
echo   - Close both terminal windows, or
echo   - Press Ctrl+C in each terminal window
echo.
echo 📝 Logs saved to: %LOG_FILE%
echo.

echo [%date% %time%] SLD Platform Startup Completed >> "%LOG_FILE%"

pause
