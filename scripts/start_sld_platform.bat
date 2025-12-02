@echo off
title SLD Processing Platform - Startup
color 0A

echo.
echo ========================================
echo   SLD Processing Platform - Startup
echo ========================================
echo.

REM Set the base directory
set "BASE_DIR=%~dp0"
set "BACKEND_DIR=%BASE_DIR%web_app\backend"
set "FRONTEND_DIR=%BASE_DIR%web_app\frontend"

echo 🔍 Checking system requirements...

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    py --version >nul 2>&1
    if errorlevel 1 (
        echo ❌ Python not found! Please install Python 3.8+ from https://python.org
        echo Make sure to check "Add Python to PATH" during installation
        pause
        exit /b 1
    ) else (
        set "PYTHON_CMD=py"
    )
) else (
    set "PYTHON_CMD=python"
)

REM Check if Node.js is available
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js not found! Please install Node.js 16+ from https://nodejs.org
    pause
    exit /b 1
)

echo ✅ Python: Available
echo ✅ Node.js: Available

REM Check if backend directory exists
if not exist "%BACKEND_DIR%" (
    echo ❌ Backend directory not found: %BACKEND_DIR%
    pause
    exit /b 1
)

REM Check if frontend directory exists
if not exist "%FRONTEND_DIR%" (
    echo ❌ Frontend directory not found: %FRONTEND_DIR%
    pause
    exit /b 1
)

echo.
echo 🚀 Starting SLD Processing Platform...
echo.

REM Create logs directory
if not exist "%BASE_DIR%logs" mkdir "%BASE_DIR%logs"

REM Start backend in a new window
echo 📡 Starting Backend Server...
start "SLD Backend" cmd /k "cd /d "%BACKEND_DIR%" && echo Starting SLD Backend Server... && echo. && %PYTHON_CMD% main_fixed.py"

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend in a new window
echo 🌐 Starting Frontend Server...
start "SLD Frontend" cmd /k "cd /d "%FRONTEND_DIR%" && echo Starting SLD Frontend Server... && echo. && npm start"

REM Wait a moment for frontend to start
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo   🎉 SLD Platform Starting Up!
echo ========================================
echo.
echo 📡 Backend:  http://localhost:8000
echo 🌐 Frontend: http://localhost:3000
echo 📖 API Docs: http://localhost:8000/docs
echo ❤️  Health:  http://localhost:8000/health
echo.
echo ⏳ Please wait 30-60 seconds for both servers to fully start...
echo.

REM Wait and then open browser
echo 🌍 Opening browser in 10 seconds...
timeout /t 10 /nobreak >nul

REM Try to open the frontend in default browser
start http://localhost:3000

echo.
echo ========================================
echo   Platform Status
echo ========================================
echo.
echo ✅ Backend window opened (check for any errors)
echo ✅ Frontend window opened (check for any errors)
echo ✅ Browser should open automatically
echo.
echo 📋 Next Steps:
echo 1. Check both terminal windows for any errors
echo 2. Wait for "Local:" message in frontend window
echo 3. Go to http://localhost:3000 in your browser
echo 4. Test upload functionality
echo.
echo 🛑 To stop: Close both terminal windows or press Ctrl+C in each
echo.

pause
