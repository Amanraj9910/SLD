@echo off
title SLD Platform - Stop Services
color 0C

echo.
echo ================================
echo   SLD Platform - Stop Services
echo ================================
echo.

echo 🛑 Stopping SLD Platform services...

REM Kill processes on port 8000 (Backend)
echo 📡 Stopping Backend (port 8000)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do (
    echo   Killing process %%a
    taskkill /f /pid %%a >nul 2>&1
)

REM Kill processes on port 3000 (Frontend)
echo 🌐 Stopping Frontend (port 3000)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000') do (
    echo   Killing process %%a
    taskkill /f /pid %%a >nul 2>&1
)

REM Kill Node.js processes
echo 🔄 Stopping Node.js processes...
taskkill /f /im node.exe >nul 2>&1

REM Kill Python processes (be careful with this)
echo 🐍 Stopping Python web processes...
for /f "tokens=2" %%a in ('tasklist /fi "imagename eq python.exe" /fo csv ^| findstr uvicorn') do (
    taskkill /f /pid %%a >nul 2>&1
)

echo.
echo ✅ SLD Platform services stopped
echo.
echo 📋 Ports freed:
echo   📡 Port 8000 (Backend)
echo   🌐 Port 3000 (Frontend)
echo.
echo You can now restart the platform with:
echo   - start_sld_platform.bat
echo   - start_sld_advanced.bat  
echo   - quick_start.bat
echo.

pause
