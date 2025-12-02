@echo off
title SLD Platform - Quick Start
color 0A

echo.
echo =============================================
echo   SLD Platform - Quick Start
echo =============================================
echo.
echo This script will start the SLD platform quickly
echo by skipping dependency installation if already present.
echo.

REM Set the base directory
set "BASE_DIR=%~dp0"
set "BACKEND_DIR=%BASE_DIR%web_app\core\backend"
set "FRONTEND_DIR=%BASE_DIR%web_app\core\frontend"

echo Step 1: System Check
echo ====================

REM Check Python - try multiple locations
set "PYTHON_CMD="

REM Try standard python command
python --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    echo SUCCESS: Python found (python command)
    goto :python_found
)

REM Try py launcher
py --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py"
    echo SUCCESS: Python found (py launcher)
    goto :python_found
)

REM Try common installation paths
if exist "C:\Users\admin\AppData\Local\Programs\Python\Python311\python.exe" (
    set "PYTHON_CMD=C:\Users\admin\AppData\Local\Programs\Python\Python311\python.exe"
    echo SUCCESS: Python found (local installation)
    goto :python_found
)

if exist "C:\Python311\python.exe" (
    set "PYTHON_CMD=C:\Python311\python.exe"
    echo SUCCESS: Python found (system installation)
    goto :python_found
)

echo ERROR: Python not found! Please install Python first.
echo Checked locations:
echo - python command
echo - py launcher
echo - C:\Users\admin\AppData\Local\Programs\Python\Python311\python.exe
echo - C:\Python311\python.exe
pause
exit /b 1

:python_found

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found! Please install Node.js first.
    pause
    exit /b 1
) else (
    echo SUCCESS: Node.js found
)

echo.
echo Step 2: Quick Setup
echo ===================

cd /d "%BASE_DIR%"

REM Create basic directories
if not exist "uploads" mkdir "uploads"
if not exist "logs" mkdir "logs"
if not exist "results" mkdir "results"
echo SUCCESS: Directories ready

REM Check if frontend dependencies exist
cd /d "%FRONTEND_DIR%"
if not exist "node_modules" (
    echo.
    echo WARNING: Frontend dependencies not found!
    echo You need to run 'npm install' in the frontend directory first.
    echo.
    echo Options:
    echo 1. Run: start_sld_unified.bat (full setup with dependencies)
    echo 2. Manually run: cd web_app\core\frontend && npm install
    echo 3. Continue anyway (backend only)
    echo.
    set /p choice="Enter choice (1/2/3): "
    if "%choice%"=="1" (
        echo Running full setup script...
        cd /d "%BASE_DIR%"
        start_sld_unified.bat
        exit /b 0
    )
    if "%choice%"=="2" (
        echo Please run: cd web_app\core\frontend && npm install
        echo Then run this script again.
        pause
        exit /b 0
    )
    echo Continuing with backend only...
)

echo.
echo Step 3: Starting Services
echo =========================

REM Kill existing processes
echo Cleaning up existing processes...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000') do taskkill /f /pid %%a >nul 2>&1

REM Start backend
echo Starting Backend Server...
cd /d "%BACKEND_DIR%"
start "SLD Backend Server" cmd /k "title SLD Backend && echo ======================================== && echo   SLD Backend Server && echo ======================================== && echo Backend: http://localhost:8000 && echo API Docs: http://localhost:8000/docs && echo. && \"%PYTHON_CMD%\" main.py"

REM Wait a moment
timeout /t 3 /nobreak >nul

REM Start frontend if dependencies exist
cd /d "%FRONTEND_DIR%"
if exist "node_modules" (
    echo Starting Frontend Server...
    start "SLD Frontend Server" cmd /k "title SLD Frontend && echo ======================================== && echo   SLD Frontend Server && echo ======================================== && echo Frontend: http://localhost:3000 && echo Backend: http://localhost:8000 && echo. && npm start"
    
    REM Wait and open browser
    timeout /t 8 /nobreak >nul
    echo Opening browser...
    start http://localhost:3000
) else (
    echo Frontend not started (dependencies missing)
    echo Backend only mode - API available at http://localhost:8000
    timeout /t 3 /nobreak >nul
    start http://localhost:8000/docs
)

echo.
echo =============================================
echo   SLD Platform Started!
echo =============================================
echo.
echo Services running:
echo   Backend API: http://localhost:8000
echo   API Docs:    http://localhost:8000/docs
if exist "%FRONTEND_DIR%\node_modules" (
    echo   Frontend:    http://localhost:3000
)
echo.
echo To stop: Close the terminal windows or run scripts\stop_sld_platform.bat
echo.

pause
