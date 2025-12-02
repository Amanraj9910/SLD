@echo off
title SLD Platform - Simple Startup
color 0A

echo.
echo =============================================
echo   SLD Platform - Simple Startup
echo =============================================
echo.

REM Set the base directory
set BASE_DIR=%~dp0
set BACKEND_DIR=%BASE_DIR%web_app\core\backend
set FRONTEND_DIR=%BASE_DIR%web_app\core\frontend

echo Checking directories...
if not exist "%BACKEND_DIR%" (
    echo ERROR: Backend directory not found: %BACKEND_DIR%
    pause
    exit /b 1
)

if not exist "%FRONTEND_DIR%" (
    echo ERROR: Frontend directory not found: %FRONTEND_DIR%
    pause
    exit /b 1
)

echo SUCCESS: Directories found

echo.
echo Finding Python...

REM Set Python command directly to known location
set PYTHON_CMD=C:\Users\admin\AppData\Local\Programs\Python\Python311\python.exe

REM Verify Python exists
if not exist "%PYTHON_CMD%" (
    echo ERROR: Python not found at expected location: %PYTHON_CMD%
    echo.
    echo Trying alternative methods...
    
    REM Try py launcher
    py --version >nul 2>&1
    if not errorlevel 1 (
        set PYTHON_CMD=py
        echo SUCCESS: Using py launcher
        goto :python_ok
    )
    
    REM Try python command
    python --version >nul 2>&1
    if not errorlevel 1 (
        set PYTHON_CMD=python
        echo SUCCESS: Using python command
        goto :python_ok
    )
    
    echo ERROR: No Python installation found!
    echo Please install Python from https://python.org
    pause
    exit /b 1
) else (
    echo SUCCESS: Python found at %PYTHON_CMD%
)

:python_ok

echo.
echo Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found!
    echo Please install Node.js from https://nodejs.org
    pause
    exit /b 1
) else (
    echo SUCCESS: Node.js found
)

echo.
echo Cleaning up existing processes...
REM Kill any existing processes on ports 8000 and 3000
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000') do taskkill /f /pid %%a >nul 2>&1
echo SUCCESS: Ports cleared

echo.
echo Creating necessary directories...
cd /d "%BASE_DIR%"
if not exist "uploads" mkdir "uploads"
if not exist "logs" mkdir "logs"
if not exist "results" mkdir "results"
if not exist "static" mkdir "static"
echo SUCCESS: Directories ready

echo.
echo Starting Backend Server...
cd /d "%BACKEND_DIR%"

REM Create a simple batch file for backend startup
echo @echo off > temp_start_backend.bat
echo title SLD Backend Server >> temp_start_backend.bat
echo echo ======================================== >> temp_start_backend.bat
echo echo   SLD Backend Server >> temp_start_backend.bat
echo echo ======================================== >> temp_start_backend.bat
echo echo Backend: http://localhost:8000 >> temp_start_backend.bat
echo echo API Docs: http://localhost:8000/docs >> temp_start_backend.bat
echo echo Health: http://localhost:8000/health >> temp_start_backend.bat
echo echo. >> temp_start_backend.bat
echo echo Starting with Python: %PYTHON_CMD% >> temp_start_backend.bat
echo echo. >> temp_start_backend.bat

REM Add the Python command based on type
if "%PYTHON_CMD%"=="py" (
    echo py main.py >> temp_start_backend.bat
) else if "%PYTHON_CMD%"=="python" (
    echo python main.py >> temp_start_backend.bat
) else (
    echo "%PYTHON_CMD%" main.py >> temp_start_backend.bat
)

echo pause >> temp_start_backend.bat

REM Start backend in new window
start "SLD Backend" cmd /k temp_start_backend.bat

echo Backend starting...
timeout /t 3 /nobreak >nul

echo.
echo Starting Frontend Server...
cd /d "%FRONTEND_DIR%"

REM Check if node_modules exists
if not exist "node_modules" (
    echo WARNING: node_modules not found. Installing dependencies...
    echo This may take a few minutes...
    npm install
    if errorlevel 1 (
        echo ERROR: Failed to install frontend dependencies
        echo Please run: cd web_app\core\frontend && npm install
        pause
        exit /b 1
    )
    echo SUCCESS: Dependencies installed
)

REM Start frontend in new window
start "SLD Frontend" cmd /k "title SLD Frontend Server && echo ======================================== && echo   SLD Frontend Server && echo ======================================== && echo Frontend: http://localhost:3000 && echo Backend: http://localhost:8000 && echo. && npm start"

echo Frontend starting...
timeout /t 8 /nobreak >nul

echo.
echo =============================================
echo   SLD Platform Started!
echo =============================================
echo.
echo Services:
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:3000
echo   API Docs: http://localhost:8000/docs
echo   Health:   http://localhost:8000/health
echo.
echo Opening browser...
start http://localhost:3000

echo.
echo Platform is starting up...
echo Please wait 30-60 seconds for both servers to fully initialize.
echo.
echo To stop the platform:
echo - Close both terminal windows
echo - Or run: scripts\stop_sld_platform.bat
echo.

pause
