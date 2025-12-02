@echo off
REM SLD Processing Platform - Windows Installation Script
echo 🚀 SLD Processing Platform - Windows Installation
echo ================================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo ✅ Python is available

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed or not in PATH
    echo Please install Node.js 16+ from https://nodejs.org
    pause
    exit /b 1
)

echo ✅ Node.js is available

REM Run Python installation script
echo.
echo 📦 Running Python dependency installation...
python install.py

if errorlevel 1 (
    echo ❌ Python installation failed
    pause
    exit /b 1
)

REM Install frontend dependencies
echo.
echo 🌐 Installing frontend dependencies...
cd web_app\frontend

if not exist package.json (
    echo ❌ package.json not found in web_app/frontend
    pause
    exit /b 1
)

echo Installing Node.js packages...
call npm install

if errorlevel 1 (
    echo ❌ Frontend installation failed
    pause
    exit /b 1
)

cd ..\..

echo.
echo ================================================
echo 🎉 Installation completed successfully!
echo.
echo Next steps:
echo 1. Start the backend:
echo    cd web_app\backend
echo    python main.py
echo.
echo 2. In another terminal, start the frontend:
echo    cd web_app\frontend
echo    npm start
echo.
echo 3. Open http://localhost:3000 in your browser
echo.
echo 📚 Check README.md for more detailed instructions
echo ================================================
pause
