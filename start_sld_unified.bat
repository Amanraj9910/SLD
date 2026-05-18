@echo off
title SLD Platform - Unified Startup
color 0A

echo.
echo =============================================
echo   SLD Platform - Unified Startup
echo =============================================
echo.
echo This unified script will:
echo - Check system requirements (Python, Node.js)
echo - Verify and install dependencies automatically
echo - Configure environment variables
echo - Create necessary directories
echo - Start backend and frontend servers
echo - Open the application in your browser
echo.

REM Set the base directory
set "BASE_DIR=%~dp0"
set "BACKEND_DIR=%BASE_DIR%web_app\core\backend"
set "FRONTEND_DIR=%BASE_DIR%web_app\core\frontend"

echo Step 1: System Requirements Check
echo ====================================

REM Check Python - try multiple locations
set PYTHON_CMD=

REM Try common installation paths first (most reliable)
if exist "C:\Users\admin\AppData\Local\Programs\Python\Python311\python.exe" (
    set PYTHON_CMD=C:\Users\admin\AppData\Local\Programs\Python\Python311\python.exe
    echo SUCCESS: Python found at local installation
    goto :python_found
)

if exist "C:\Python311\python.exe" (
    set PYTHON_CMD=C:\Python311\python.exe
    echo SUCCESS: Python found at system installation
    goto :python_found
)

REM Try standard python command
python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python
    echo SUCCESS: Python found via PATH
    goto :python_found
)

REM Try py launcher
py --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=py
    echo SUCCESS: Python found via py launcher
    goto :python_found
)

echo ERROR: Python not found!
echo Please install Python 3.8+ from https://python.org
echo Make sure to check "Add Python to PATH" during installation
start https://python.org/downloads/
pause
exit /b 1

:python_found
echo Python command set to: %PYTHON_CMD%

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found!
    echo.
    echo Please install Node.js 16+ from https://nodejs.org
    echo After installing Node.js, run this script again.
    echo.
    start https://nodejs.org/
    pause
    exit /b 1
) else (
    echo SUCCESS: Node.js found
)

echo.
echo Step 2: Installing Dependencies
echo ==================================

REM Install Python dependencies
echo Installing Python packages...
cd /d "%BACKEND_DIR%"

REM Debug: Show what Python command we're using
echo Using Python command: %PYTHON_CMD%

REM First upgrade pip
echo Upgrading pip...
"%PYTHON_CMD%" -m pip install --upgrade pip >nul 2>&1
if errorlevel 1 (
    echo WARNING: Failed to upgrade pip, continuing anyway...
)

REM Install required packages
echo Installing required packages...
"%PYTHON_CMD%" -m pip install -r "%BASE_DIR%requirements.txt" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Failed to install Python dependencies silently
    echo Trying alternative installation without silent mode...
    "%PYTHON_CMD%" -m pip install -r "%BASE_DIR%requirements.txt"
    if errorlevel 1 (
        echo ERROR: Failed to install Python dependencies
        echo.
        echo Please try manually running:
        echo "%PYTHON_CMD%" -m pip install -r "%BASE_DIR%requirements.txt"
        echo.
        pause
        exit /b 1
    )
)
echo SUCCESS: Python dependencies installed

REM Install Node.js dependencies
echo Installing Node.js packages...
cd /d "%FRONTEND_DIR%"
if not exist "node_modules" (
    echo.
    echo Installing frontend dependencies...
    echo This may take 3-5 minutes on first run. Please wait...
    echo.
    npm install
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to install Node.js dependencies
        echo Please check your internet connection and try again.
        pause
        exit /b 1
    )
    echo.
    echo SUCCESS: Node.js dependencies installed
) else (
    echo SUCCESS: Node.js dependencies already installed
)

echo.
echo Step 3: Environment Setup
echo =============================

cd /d "%BASE_DIR%"

REM Create necessary directories
if not exist "uploads" mkdir "uploads"
if not exist "logs" mkdir "logs"
if not exist "results" mkdir "results"
if not exist "annotation_projects" mkdir "annotation_projects"
if not exist "static" mkdir "static"
echo SUCCESS: Directories created

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
    echo SUCCESS: Environment file created
) else (
    echo SUCCESS: Environment file exists
)

echo.
echo Step 4: Cleanup Existing Processes
echo =====================================

REM Kill any existing processes on ports 8000 and 3000
echo Cleaning up existing processes...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000') do taskkill /f /pid %%a >nul 2>&1
echo SUCCESS: Ports cleared

echo.
echo Step 5: Starting Services
echo =============================

REM Start backend
echo Starting Backend Server...
echo Using Python: %PYTHON_CMD%
cd /d "%BACKEND_DIR%"

REM Create a temporary batch file to handle the Python command properly
echo @echo off > start_backend_temp.bat
echo title SLD Backend Server >> start_backend_temp.bat
echo echo ======================================== >> start_backend_temp.bat
echo echo   SLD Backend Server >> start_backend_temp.bat
echo echo ======================================== >> start_backend_temp.bat
echo echo Backend: http://localhost:8000 >> start_backend_temp.bat
echo echo API Docs: http://localhost:8000/docs >> start_backend_temp.bat
echo echo Health: http://localhost:8000/health >> start_backend_temp.bat
echo echo. >> start_backend_temp.bat
echo set "PYTHONPATH=%BASE_DIR%" >> start_backend_temp.bat
echo "%PYTHON_CMD%" main.py >> start_backend_temp.bat

start "SLD Backend Server" cmd /k start_backend_temp.bat

REM Wait for backend to start
echo Waiting for backend to initialize...
timeout /t 5 /nobreak >nul

REM Start frontend
echo Starting Frontend Server...
cd /d "%FRONTEND_DIR%"
start "SLD Frontend Server" cmd /k "title SLD Frontend Server && echo ======================================== && echo   SLD Frontend Server && echo ======================================== && echo Frontend: http://localhost:3000 && echo Backend: http://localhost:8000 && echo. && npm start"

echo.
echo Step 6: Opening Application
echo ==============================

echo Waiting for services to fully initialize...
timeout /t 10 /nobreak >nul

echo Opening SLD Platform in your browser...
start http://localhost:3000

echo.
echo =============================================
echo   SLD Platform Started Successfully!
echo =============================================
echo.
echo Your SLD Platform is now running:
echo.
echo   Main Application: http://localhost:3000
echo   Backend API:      http://localhost:8000
echo   API Documentation: http://localhost:8000/docs
echo   Health Check:     http://localhost:8000/health
echo.
echo What you can do now:
echo   - Upload SLD images for component detection
echo   - Extract text from documents using Azure OCR
echo   - Create manual annotations for training data
echo   - View API documentation and test endpoints
echo.
echo To stop the platform:
echo   - Run: scripts\stop_sld_platform.bat
echo   - Or close both server windows
echo.
echo To restart later:
echo   - Run: start_sld_unified.bat (this script)
echo   - Run: scripts\quick_start.bat (fastest)
echo   - Run: scripts\start_sld_platform.bat (standard)
echo.

pause
