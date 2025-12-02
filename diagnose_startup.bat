@echo off
title SLD Platform - Startup Diagnostics
color 0E

echo.
echo =============================================
echo   SLD Platform - Startup Diagnostics
echo =============================================
echo.

REM Set the base directory
set BASE_DIR=%~dp0
set BACKEND_DIR=%BASE_DIR%web_app\core\backend
set FRONTEND_DIR=%BASE_DIR%web_app\core\frontend

echo 🔍 DIAGNOSTIC REPORT
echo ==================

echo.
echo 📁 Directory Check:
echo -------------------
echo Base directory: %BASE_DIR%
if exist "%BASE_DIR%" (
    echo ✅ Base directory exists
) else (
    echo ❌ Base directory missing
)

echo Backend directory: %BACKEND_DIR%
if exist "%BACKEND_DIR%" (
    echo ✅ Backend directory exists
) else (
    echo ❌ Backend directory missing
)

echo Frontend directory: %FRONTEND_DIR%
if exist "%FRONTEND_DIR%" (
    echo ✅ Frontend directory exists
) else (
    echo ❌ Frontend directory missing
)

echo.
echo 📄 Key Files Check:
echo -------------------
if exist "%BACKEND_DIR%\main.py" (
    echo ✅ Backend main.py exists
) else (
    echo ❌ Backend main.py missing
)

if exist "%FRONTEND_DIR%\package.json" (
    echo ✅ Frontend package.json exists
) else (
    echo ❌ Frontend package.json missing
)

if exist "%FRONTEND_DIR%\node_modules" (
    echo ✅ Frontend node_modules exists
) else (
    echo ⚠️  Frontend node_modules missing (run npm install)
)

echo.
echo 🐍 Python Detection:
echo --------------------

REM Test Python detection logic
set PYTHON_CMD=
set PYTHON_FOUND=0

echo Testing Python at: C:\Users\admin\AppData\Local\Programs\Python\Python311\python.exe
if exist "C:\Users\admin\AppData\Local\Programs\Python\Python311\python.exe" (
    set PYTHON_CMD=C:\Users\admin\AppData\Local\Programs\Python\Python311\python.exe
    set PYTHON_FOUND=1
    echo ✅ Found at local installation
    
    REM Test if it actually works
    "%PYTHON_CMD%" --version >nul 2>&1
    if not errorlevel 1 (
        echo ✅ Python executable works
        "%PYTHON_CMD%" --version
    ) else (
        echo ❌ Python executable fails to run
    )
) else (
    echo ❌ Not found at local installation
)

if %PYTHON_FOUND%==0 (
    echo Testing: python command
    python --version >nul 2>&1
    if not errorlevel 1 (
        set PYTHON_CMD=python
        set PYTHON_FOUND=1
        echo ✅ Found via PATH
        python --version
    ) else (
        echo ❌ python command not available
    )
)

if %PYTHON_FOUND%==0 (
    echo Testing: py launcher
    py --version >nul 2>&1
    if not errorlevel 1 (
        set PYTHON_CMD=py
        set PYTHON_FOUND=1
        echo ✅ Found via py launcher
        py --version
    ) else (
        echo ❌ py launcher not available
    )
)

if %PYTHON_FOUND%==0 (
    echo ❌ NO PYTHON FOUND!
    echo.
    echo 💡 Solutions:
    echo 1. Install Python from https://python.org
    echo 2. Make sure to check "Add Python to PATH"
    echo 3. Or use the full path to python.exe
) else (
    echo ✅ Python command: %PYTHON_CMD%
)

echo.
echo 📦 Node.js Detection:
echo ---------------------
node --version >nul 2>&1
if not errorlevel 1 (
    echo ✅ Node.js found
    node --version
    npm --version
) else (
    echo ❌ Node.js not found
    echo 💡 Install from: https://nodejs.org
)

echo.
echo 🌐 Port Check:
echo --------------
echo Checking port 8000 (Backend):
netstat -an | findstr :8000 >nul
if not errorlevel 1 (
    echo ⚠️  Port 8000 is in use
    echo Processes using port 8000:
    netstat -ano | findstr :8000
) else (
    echo ✅ Port 8000 is available
)

echo.
echo Checking port 3000 (Frontend):
netstat -an | findstr :3000 >nul
if not errorlevel 1 (
    echo ⚠️  Port 3000 is in use
    echo Processes using port 3000:
    netstat -ano | findstr :3000
) else (
    echo ✅ Port 3000 is available
)

echo.
echo 🔧 Python Dependencies Check:
echo -----------------------------
if %PYTHON_FOUND%==1 (
    echo Testing Python imports...
    
    "%PYTHON_CMD%" -c "import fastapi; print('✅ FastAPI available')" 2>nul || echo "❌ FastAPI missing"
    "%PYTHON_CMD%" -c "import uvicorn; print('✅ Uvicorn available')" 2>nul || echo "❌ Uvicorn missing"
    "%PYTHON_CMD%" -c "import pydantic; print('✅ Pydantic available')" 2>nul || echo "❌ Pydantic missing"
    
    echo.
    echo If any dependencies are missing, run:
    echo "%PYTHON_CMD%" -m pip install fastapi uvicorn pydantic-settings python-multipart
) else (
    echo ⚠️  Cannot check Python dependencies (Python not found)
)

echo.
echo 📊 System Information:
echo ----------------------
echo OS: %OS%
echo Processor: %PROCESSOR_ARCHITECTURE%
echo User: %USERNAME%
echo Current directory: %CD%

echo.
echo 🚀 Startup Recommendations:
echo ===========================

if %PYTHON_FOUND%==0 (
    echo ❌ CRITICAL: Install Python first
    echo    Download from: https://python.org/downloads/
    echo    Make sure to check "Add Python to PATH"
    echo.
)

node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ CRITICAL: Install Node.js first
    echo    Download from: https://nodejs.org
    echo.
)

if not exist "%FRONTEND_DIR%\node_modules" (
    echo ⚠️  RECOMMENDED: Install frontend dependencies
    echo    Run: cd web_app\core\frontend && npm install
    echo.
)

if %PYTHON_FOUND%==1 (
    node --version >nul 2>&1
    if not errorlevel 1 (
        echo ✅ READY: You can try starting the platform
        echo.
        echo 🎯 Recommended startup methods:
        echo 1. start_sld_simple.bat     (Most reliable)
        echo 2. start_sld_unified.bat    (Full featured)
        echo 3. start_sld_quick.bat      (Fast startup)
        echo.
        echo 🔧 Manual startup:
        echo Backend:  cd web_app\core\backend && "%PYTHON_CMD%" main.py
        echo Frontend: cd web_app\core\frontend && npm start
    )
)

echo.
echo =============================================
echo   Diagnostics Complete
echo =============================================
echo.

pause
