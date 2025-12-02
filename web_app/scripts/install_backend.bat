@echo off
echo 🚀 Installing SLD Backend Dependencies
echo =====================================

REM Try different Python commands
python --version >nul 2>&1
if not errorlevel 1 (
    echo ✅ Using 'python' command
    python install_backend.py
    goto :end
)

py --version >nul 2>&1
if not errorlevel 1 (
    echo ✅ Using 'py' command
    py install_backend.py
    goto :end
)

python3 --version >nul 2>&1
if not errorlevel 1 (
    echo ✅ Using 'python3' command
    python3 install_backend.py
    goto :end
)

echo ❌ Python not found in PATH
echo Please install Python from https://python.org
echo Make sure to check "Add Python to PATH" during installation
pause

:end
echo.
echo Installation script completed.
pause
