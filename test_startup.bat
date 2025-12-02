@echo off
title SLD Platform - Startup Test
color 0E

echo.
echo =============================================
echo   SLD Platform - Startup Diagnostics
echo =============================================
echo.

REM Set the base directory
set "BASE_DIR=%~dp0"
set "BACKEND_DIR=%BASE_DIR%web_app\core\backend"
set "FRONTEND_DIR=%BASE_DIR%web_app\core\frontend"

echo 🔍 Testing System Requirements...
echo.

REM Check Python
echo Testing Python...
python --version >nul 2>&1
if errorlevel 1 (
    py --version >nul 2>&1
    if errorlevel 1 (
        echo ❌ Python not found!
        echo Please install Python 3.8+ from https://python.org
        goto :end
    ) else (
        set "PYTHON_CMD=py"
        echo ✅ Python found (using 'py' command)
        py --version
    )
) else (
    set "PYTHON_CMD=python"
    echo ✅ Python found
    python --version
)

echo.

REM Check Node.js
echo Testing Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js not found!
    echo Please install Node.js 16+ from https://nodejs.org
    goto :end
) else (
    echo ✅ Node.js found
    node --version
    npm --version
)

echo.

REM Check directories
echo Testing directories...
if exist "%BACKEND_DIR%" (
    echo ✅ Backend directory exists: %BACKEND_DIR%
) else (
    echo ❌ Backend directory missing: %BACKEND_DIR%
    goto :end
)

if exist "%FRONTEND_DIR%" (
    echo ✅ Frontend directory exists: %FRONTEND_DIR%
) else (
    echo ❌ Frontend directory missing: %FRONTEND_DIR%
    goto :end
)

echo.

REM Check main files
echo Testing main files...
if exist "%BACKEND_DIR%\main.py" (
    echo ✅ Backend main.py exists
) else (
    echo ❌ Backend main.py missing
    echo Looking for files in backend directory:
    dir "%BACKEND_DIR%\*.py" /b
)

if exist "%FRONTEND_DIR%\package.json" (
    echo ✅ Frontend package.json exists
) else (
    echo ❌ Frontend package.json missing
)

echo.

REM Test Python imports
echo Testing Python dependencies...
cd /d "%BACKEND_DIR%"
%PYTHON_CMD% -c "import sys; print('Python path:', sys.executable)" 2>nul
if errorlevel 1 (
    echo ❌ Python execution failed
    goto :end
)

%PYTHON_CMD% -c "import fastapi; print('FastAPI version:', fastapi.__version__)" 2>nul
if errorlevel 1 (
    echo ⚠️  FastAPI not installed
    echo Installing FastAPI...
    %PYTHON_CMD% -m pip install fastapi uvicorn
) else (
    echo ✅ FastAPI available
)

echo.

REM Test Node.js dependencies
echo Testing Node.js dependencies...
cd /d "%FRONTEND_DIR%"
if exist "node_modules" (
    echo ✅ Node modules exist
) else (
    echo ⚠️  Node modules missing
    echo Installing dependencies...
    npm install
)

echo.

REM Test ports
echo Testing ports...
netstat -an | findstr :8000 >nul
if not errorlevel 1 (
    echo ⚠️  Port 8000 is in use
    echo Processes using port 8000:
    netstat -ano | findstr :8000
) else (
    echo ✅ Port 8000 is available
)

netstat -an | findstr :3000 >nul
if not errorlevel 1 (
    echo ⚠️  Port 3000 is in use
    echo Processes using port 3000:
    netstat -ano | findstr :3000
) else (
    echo ✅ Port 3000 is available
)

echo.
echo =============================================
echo   Diagnostics Complete
echo =============================================
echo.
echo If all checks passed, try running start_sld_unified.bat again.
echo If there are issues, please share the output above.
echo.

:end
pause
