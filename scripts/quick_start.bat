@echo off
title SLD Platform - Quick Start
color 0B

echo.
echo ================================
echo   SLD Platform - Quick Start
echo ================================
echo.

REM Set directories
set "BACKEND_DIR=%~dp0web_app\backend"
set "FRONTEND_DIR=%~dp0web_app\frontend"

REM Quick system check
python --version >nul 2>&1 || py --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Install from https://python.org
    pause & exit /b 1
)

node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js not found! Install from https://nodejs.org
    pause & exit /b 1
)

echo ✅ System requirements OK
echo.
echo 🚀 Starting servers...

REM Start backend
start "Backend" cmd /k "cd /d "%BACKEND_DIR%" && python main_fixed.py"

REM Wait and start frontend
timeout /t 3 /nobreak >nul
start "Frontend" cmd /k "cd /d "%FRONTEND_DIR%" && npm start"

REM Wait and open browser
timeout /t 8 /nobreak >nul
start http://localhost:3000

echo.
echo ✅ Platform started!
echo 📡 Backend: http://localhost:8000
echo 🌐 Frontend: http://localhost:3000
echo.
echo Browser opening automatically...
echo Close this window when done.
echo.

pause
